package com.medibot.service;

import com.medibot.dto.MlServiceResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Enterprise Service for communicating with the Python ML microservice.
 * Demonstrates Spring Boot 3 RestClient usage and microservices integration.
 */
@Service
public class MlClientService {

    private final RestClient restClient;
    private final String mlServiceUrl;

    public MlClientService(@Value("${ml.service.url:http://127.0.0.1:5001}") String mlServiceUrl) {
        this.mlServiceUrl = mlServiceUrl;
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(5000);
        this.restClient = RestClient.builder()
                .requestFactory(factory)
                .baseUrl(mlServiceUrl)
                .build();
    }

    public MlServiceResponse predict(List<String> symptoms) {
        try {
            Map<String, Object> payload = Map.of("symptoms", symptoms);
            return restClient.post()
                    .uri("/predict")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(payload)
                    .retrieve()
                    .body(MlServiceResponse.class);
        } catch (Exception e) {
            System.err.println("❌ ML Microservice call failed: " + e.getMessage());
            throw new RuntimeException("Unable to reach the Machine Learning service. Please ensure ml_service.py is running on " + mlServiceUrl, e);
        }
    }

    @SuppressWarnings("unchecked")
    public List<String> getFeatures() {
        try {
            Map<String, Object> res = restClient.get()
                    .uri("/features")
                    .retrieve()
                    .body(Map.class);
            if (res != null && res.containsKey("features")) {
                return (List<String>) res.get("features");
            }
        } catch (Exception e) {
            System.err.println("⚠️ Could not fetch features from ML service: " + e.getMessage());
        }
        return Collections.emptyList();
    }
}
