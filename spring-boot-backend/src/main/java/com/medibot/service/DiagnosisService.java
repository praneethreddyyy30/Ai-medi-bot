package com.medibot.service;

import com.medibot.dto.DiagnosisResponse;
import com.medibot.dto.MlServiceResponse;
import com.medibot.dto.PredictionItem;
import com.medibot.model.DiseaseInfo;
import com.medibot.repository.DiseaseRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.Set;

/**
 * Core Orchestration Service:
 * 1. Performs clinical triage / emergency checks.
 * 2. Calls Python ML microservice for XGBoost inference.
 * 3. Enriches prediction with clinical data from the Spring Data JPA Repository.
 */
@Service
public class DiagnosisService {

    private final MlClientService mlClientService;
    private final DiseaseRepository diseaseRepository;

    // High-risk symptoms that warrant emergency clinical triage
    private static final Set<String> EMERGENCY_SYMPTOMS = Set.of(
            "paralysis", "bloody_stool", "stiff_neck", "bite_exposure", "confusion"
    );

    public DiagnosisService(MlClientService mlClientService, DiseaseRepository diseaseRepository) {
        this.mlClientService = mlClientService;
        this.diseaseRepository = diseaseRepository;
    }

    public DiagnosisResponse diagnose(List<String> symptoms) {
        // 1. Check for clinical emergency triage
        boolean isEmergency = symptoms.stream()
                .map(s -> s.trim().toLowerCase().replace(" ", "_"))
                .anyMatch(EMERGENCY_SYMPTOMS::contains);

        // 2. Call ML microservice for inference
        MlServiceResponse mlResponse = mlClientService.predict(symptoms);
        String topDisease = mlResponse.getTopDisease();
        Double confidence = mlResponse.getConfidence();
        List<PredictionItem> allPredictions = mlResponse.getPredictions();

        // 3. Query Database (Spring Data JPA) for clinical knowledge
        Optional<DiseaseInfo> diseaseOpt = diseaseRepository.findByDiseaseNameIgnoreCase(topDisease);

        String specialist;
        String severity;
        String remedies;
        String precautions;

        if (diseaseOpt.isPresent()) {
            DiseaseInfo info = diseaseOpt.get();
            specialist = info.getSpecialistToConsult();
            severity = isEmergency ? "EMERGENCY" : info.getSeverityLevel();
            remedies = info.getHomeRemedies();
            precautions = info.getPrecautions();
        } else {
            // Fallback default and persist into DB for future requests
            specialist = isEmergency ? "Emergency Medicine Specialist" : "General Physician";
            severity = isEmergency ? "EMERGENCY" : "Moderate";
            remedies = "Get plenty of rest, maintain hydration with warm fluids or ORS, and monitor symptoms.";
            precautions = "Seek medical evaluation immediately if symptoms worsen or high fever persists.";

            DiseaseInfo newEntry = new DiseaseInfo(topDisease, specialist, severity, remedies, precautions);
            diseaseRepository.save(newEntry);
        }

        return new DiagnosisResponse(
                topDisease,
                confidence,
                specialist,
                severity,
                remedies,
                precautions,
                isEmergency,
                allPredictions
        );
    }
}
