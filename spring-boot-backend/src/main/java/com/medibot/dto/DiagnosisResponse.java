package com.medibot.dto;

import java.util.List;

public class DiagnosisResponse {

    private String predictedDisease;
    private Double confidence;
    private String specialistToConsult;
    private String severityLevel;
    private String homeRemedies;
    private String precautions;
    private boolean emergency;
    private List<PredictionItem> allPredictions;

    public DiagnosisResponse() {}

    public DiagnosisResponse(String predictedDisease, Double confidence, String specialistToConsult,
                             String severityLevel, String homeRemedies, String precautions,
                             boolean emergency, List<PredictionItem> allPredictions) {
        this.predictedDisease = predictedDisease;
        this.confidence = confidence;
        this.specialistToConsult = specialistToConsult;
        this.severityLevel = severityLevel;
        this.homeRemedies = homeRemedies;
        this.precautions = precautions;
        this.emergency = emergency;
        this.allPredictions = allPredictions;
    }

    public String getPredictedDisease() {
        return predictedDisease;
    }

    public void setPredictedDisease(String predictedDisease) {
        this.predictedDisease = predictedDisease;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public String getSpecialistToConsult() {
        return specialistToConsult;
    }

    public void setSpecialistToConsult(String specialistToConsult) {
        this.specialistToConsult = specialistToConsult;
    }

    public String getSeverityLevel() {
        return severityLevel;
    }

    public void setSeverityLevel(String severityLevel) {
        this.severityLevel = severityLevel;
    }

    public String getHomeRemedies() {
        return homeRemedies;
    }

    public void setHomeRemedies(String homeRemedies) {
        this.homeRemedies = homeRemedies;
    }

    public String getPrecautions() {
        return precautions;
    }

    public void setPrecautions(String precautions) {
        this.precautions = precautions;
    }

    public boolean isEmergency() {
        return emergency;
    }

    public void setEmergency(boolean emergency) {
        this.emergency = emergency;
    }

    public List<PredictionItem> getAllPredictions() {
        return allPredictions;
    }

    public void setAllPredictions(List<PredictionItem> allPredictions) {
        this.allPredictions = allPredictions;
    }
}
