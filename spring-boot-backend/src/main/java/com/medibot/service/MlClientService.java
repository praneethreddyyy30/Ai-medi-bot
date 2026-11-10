package com.medibot.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.medibot.dto.MlServiceResponse;
import com.medibot.dto.PredictionItem;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.io.InputStream;
import java.util.*;

/**
 * Enterprise Service for Machine Learning Inference.
 * Communicates with the Python FastAPI XGBoost ML microservice on Port 5001 via Spring 6 RestClient,
 * and maintains an embedded fault-tolerant fallback engine if the microservice is offline.
 */
@Service
public class MlClientService {

    private final RestClient restClient;
    private final String mlServiceUrl;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // Fallback embedded model data
    private final List<String> fallbackFeatures = new ArrayList<>();
    private final Map<String, Map<String, Double>> fallbackProbs = new HashMap<>();

    public MlClientService(@Value("${ml.service.url:http://127.0.0.1:5001}") String mlServiceUrl) {
        this.mlServiceUrl = mlServiceUrl;
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(4000);
        factory.setReadTimeout(5000);
        this.restClient = RestClient.builder()
                .requestFactory(factory)
                .baseUrl(mlServiceUrl)
                .build();
    }

    @PostConstruct
    public void initFallback() {
        try (InputStream is = new ClassPathResource("disease_model.json").getInputStream()) {
            JsonNode root = objectMapper.readTree(is);
            JsonNode featuresNode = root.get("features");
            if (featuresNode != null && featuresNode.isArray()) {
                for (JsonNode f : featuresNode) {
                    fallbackFeatures.add(f.asText());
                }
            }

            JsonNode diseasesNode = root.get("diseases");
            if (diseasesNode != null && diseasesNode.isObject()) {
                Iterator<Map.Entry<String, JsonNode>> fields = diseasesNode.fields();
                while (fields.hasNext()) {
                    Map.Entry<String, JsonNode> entry = fields.next();
                    String diseaseName = entry.getKey();
                    JsonNode probsNode = entry.getValue().get("symptom_probs");
                    Map<String, Double> probs = new HashMap<>();
                    if (probsNode != null && probsNode.isObject()) {
                        Iterator<Map.Entry<String, JsonNode>> pFields = probsNode.fields();
                        while (pFields.hasNext()) {
                            Map.Entry<String, JsonNode> pEntry = pFields.next();
                            probs.put(pEntry.getKey(), pEntry.getValue().asDouble());
                        }
                    }
                    fallbackProbs.put(diseaseName, probs);
                }
            }
        } catch (Exception e) {
            System.err.println("ℹ️ Note: Fallback model not loaded (" + e.getMessage() + ")");
        }
    }

    public MlServiceResponse predict(List<String> symptoms) {
        if (symptoms == null || symptoms.isEmpty()) {
            throw new IllegalArgumentException("Symptoms list cannot be empty.");
        }

        // 1. Primary: Call Python FastAPI XGBoost ML microservice on port 5001
        try {
            Map<String, Object> payload = Map.of("symptoms", symptoms);
            MlServiceResponse response = restClient.post()
                    .uri("/predict")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(payload)
                    .retrieve()
                    .body(MlServiceResponse.class);

            if (response != null && response.getTopDisease() != null) {
                return response;
            }
        } catch (Exception e) {
            System.out.println("⚠️ Python ML Microservice call failed (" + e.getMessage() + "). Switching to embedded model fallback...");
        }

        // 2. Fallback: Internal model evaluation if Python microservice is offline
        return predictFallback(symptoms);
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
            // Fallback to embedded canonical features list
        }
        return Collections.unmodifiableList(fallbackFeatures);
    }

    private MlServiceResponse predictFallback(List<String> symptoms) {
        Set<String> active = new HashSet<>();
        for (String s : symptoms) {
            if (s != null && !s.trim().isEmpty()) {
                active.add(s.trim().toLowerCase().replace(" ", "_"));
            }
        }

        Map<String, Double> logScores = new HashMap<>();
        double maxLog = -Double.MAX_VALUE;

        for (Map.Entry<String, Map<String, Double>> entry : fallbackProbs.entrySet()) {
            String disease = entry.getKey();
            Map<String, Double> probs = entry.getValue();

            double logScore = 0.0;
            for (String f : fallbackFeatures) {
                double p = probs.getOrDefault(f, 0.01);
                p = Math.max(0.001, Math.min(0.999, p));
                if (active.contains(f)) {
                    logScore += Math.log(p);
                } else {
                    logScore += Math.log(1.0 - p);
                }
            }
            logScores.put(disease, logScore);
            if (logScore > maxLog) {
                maxLog = logScore;
            }
        }

        double sumExp = 0.0;
        Map<String, Double> expScores = new HashMap<>();
        for (Map.Entry<String, Double> entry : logScores.entrySet()) {
            double exp = Math.exp(entry.getValue() - maxLog);
            expScores.put(entry.getKey(), exp);
            sumExp += exp;
        }

        List<PredictionItem> rankedList = new ArrayList<>();
        for (Map.Entry<String, Double> entry : expScores.entrySet()) {
            double percentage = (entry.getValue() / sumExp) * 100.0;
            double rounded = Math.round(percentage * 100.0) / 100.0;
            rankedList.add(new PredictionItem(entry.getKey(), rounded));
        }

        rankedList.sort((a, b) -> Double.compare(b.getConfidence(), a.getConfidence()));
        List<PredictionItem> top3 = rankedList.subList(0, Math.min(3, rankedList.size()));
        PredictionItem winner = top3.get(0);

        MlServiceResponse response = new MlServiceResponse();
        response.setTopDisease(winner.getDisease());
        response.setConfidence(winner.getConfidence());
        response.setPredictions(top3);

        return response;
    }
}
