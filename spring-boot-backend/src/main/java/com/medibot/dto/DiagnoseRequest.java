package com.medibot.dto;

import jakarta.validation.constraints.NotEmpty;
import java.util.List;

public class DiagnoseRequest {

    @NotEmpty(message = "Symptoms list cannot be empty.")
    private List<String> symptoms;

    public DiagnoseRequest() {}

    public DiagnoseRequest(List<String> symptoms) {
        this.symptoms = symptoms;
    }

    public List<String> getSymptoms() {
        return symptoms;
    }

    public void setSymptoms(List<String> symptoms) {
        this.symptoms = symptoms;
    }
}
