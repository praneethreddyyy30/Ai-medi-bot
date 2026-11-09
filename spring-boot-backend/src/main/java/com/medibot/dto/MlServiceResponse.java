package com.medibot.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class MlServiceResponse {

    @JsonProperty("top_disease")
    private String topDisease;

    private Double confidence;
    private List<PredictionItem> predictions;

    public MlServiceResponse() {}

    public String getTopDisease() {
        return topDisease;
    }

    public void setTopDisease(String topDisease) {
        this.topDisease = topDisease;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public List<PredictionItem> getPredictions() {
        return predictions;
    }

    public void setPredictions(List<PredictionItem> predictions) {
        this.predictions = predictions;
    }
}
