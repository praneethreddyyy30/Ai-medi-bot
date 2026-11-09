package com.medibot.dto;

import java.util.List;

public class ChatRequest {
    private String message;
    private List<String> symptoms;
    private String currentDisease;

    public ChatRequest() {}

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public List<String> getSymptoms() {
        return symptoms;
    }

    public void setSymptoms(List<String> symptoms) {
        this.symptoms = symptoms;
    }

    public String getCurrentDisease() {
        return currentDisease;
    }

    public void setCurrentDisease(String currentDisease) {
        this.currentDisease = currentDisease;
    }
}
