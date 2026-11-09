package com.medibot.controller;

import com.medibot.dto.DiagnoseRequest;
import com.medibot.dto.DiagnosisResponse;
import com.medibot.model.DiseaseInfo;
import com.medibot.repository.DiseaseRepository;
import com.medibot.service.DiagnosisService;
import com.medibot.service.MlClientService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST Controller exposing clinical diagnosis and symptom feature endpoints.
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class DiagnosisController {

    private final DiagnosisService diagnosisService;
    private final MlClientService mlClientService;
    private final DiseaseRepository diseaseRepository;

    public DiagnosisController(DiagnosisService diagnosisService,
                               MlClientService mlClientService,
                               DiseaseRepository diseaseRepository) {
        this.diagnosisService = diagnosisService;
        this.mlClientService = mlClientService;
        this.diseaseRepository = diseaseRepository;
    }

    /**
     * Returns the 30 canonical medical symptom tags.
     */
    @GetMapping("/features")
    public ResponseEntity<Map<String, List<String>>> getFeatures() {
        List<String> features = mlClientService.getFeatures();
        return ResponseEntity.ok(Map.of("features", features));
    }

    /**
     * Primary Diagnosis Endpoint:
     * Receives symptom list, performs clinical triage, executes ML inference,
     * enriches with Spring Data JPA database, and returns diagnostic response.
     */
    @PostMapping("/diagnose")
    public ResponseEntity<DiagnosisResponse> diagnose(@Valid @RequestBody DiagnoseRequest request) {
        DiagnosisResponse response = diagnosisService.diagnose(request.getSymptoms());
        return ResponseEntity.ok(response);
    }

    /**
     * Returns all diseases stored in the knowledge base.
     */
    @GetMapping("/diseases")
    public ResponseEntity<List<DiseaseInfo>> getAllDiseases() {
        return ResponseEntity.ok(diseaseRepository.findAll());
    }

    /**
     * Retrieves clinical details for a specific disease.
     */
    @GetMapping("/diseases/{name}")
    public ResponseEntity<DiseaseInfo> getDiseaseByName(@PathVariable String name) {
        return diseaseRepository.findByDiseaseNameIgnoreCase(name)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
