package com.medibot.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.medibot.dto.MlServiceResponse;
import com.medibot.dto.PredictionItem;
import jakarta.annotation.PostConstruct;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.util.*;

/**
 * Enterprise Native Java Machine Learning Inference Engine.
 * Executes Bayesian probability classification for 45 infectious diseases across 30 symptoms
 * in pure Java (sub-millisecond latency, zero external process dependencies).
 */
@Service
public class MlClientService {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final List<String> features = new ArrayList<>();
    private final Map<String, Map<String, Double>> diseaseSymptomProbs = new HashMap<>();

    @PostConstruct
    public void init() {
        try (InputStream is = new ClassPathResource("disease_model.json").getInputStream()) {
            JsonNode root = objectMapper.readTree(is);

            // 1. Load canonical features list
            JsonNode featuresNode = root.get("features");
            if (featuresNode != null && featuresNode.isArray()) {
                for (JsonNode f : featuresNode) {
                    features.add(f.asText());
                }
            }

            // 2. Load disease conditional probability profiles
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
                    diseaseSymptomProbs.put(diseaseName, probs);
                }
            }
            System.out.println("✅ Native Java ML Engine initialized: " + features.size() + " symptoms, " + diseaseSymptomProbs.size() + " diseases.");
        } catch (Exception e) {
            System.err.println("❌ Failed to load disease_model.json: " + e.getMessage());
        }
    }

    public List<String> getFeatures() {
        return Collections.unmodifiableList(features);
    }

    public MlServiceResponse predict(List<String> symptoms) {
        if (symptoms == null || symptoms.isEmpty()) {
            throw new IllegalArgumentException("Symptoms list cannot be empty.");
        }

        // Normalize input symptoms
        Set<String> activeSymptoms = new HashSet<>();
        for (String s : symptoms) {
            if (s != null && !s.trim().isEmpty()) {
                activeSymptoms.add(s.trim().toLowerCase().replace(" ", "_"));
            }
        }

        // Calculate log-likelihood for each disease
        Map<String, Double> logScores = new HashMap<>();
        double maxLog = -Double.MAX_VALUE;

        for (Map.Entry<String, Map<String, Double>> entry : diseaseSymptomProbs.entrySet()) {
            String disease = entry.getKey();
            Map<String, Double> probs = entry.getValue();

            double logScore = 0.0;
            for (String f : features) {
                double p = probs.getOrDefault(f, 0.01);
                // Clamp probabilities to avoid log(0)
                p = Math.max(0.001, Math.min(0.999, p));

                if (activeSymptoms.contains(f)) {
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

        // Numerically stable softmax to convert log-scores to probabilities
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

        // Sort descending by confidence
        rankedList.sort((a, b) -> Double.compare(b.getConfidence(), a.getConfidence()));

        // Extract top 3 candidates
        List<PredictionItem> top3 = rankedList.subList(0, Math.min(3, rankedList.size()));
        PredictionItem winner = top3.get(0);

        MlServiceResponse response = new MlServiceResponse();
        response.setTopDisease(winner.getDisease());
        response.setConfidence(winner.getConfidence());
        response.setPredictions(top3);

        return response;
    }
}
