package com.medibot.dto;

public class PredictionItem {
    private String disease;
    private Double confidence;

    public PredictionItem() {}

    public PredictionItem(String disease, Double confidence) {
        this.disease = disease;
        this.confidence = confidence;
    }

    public String getDisease() {
        return disease;
    }

    public void setDisease(String disease) {
        this.disease = disease;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }
}
