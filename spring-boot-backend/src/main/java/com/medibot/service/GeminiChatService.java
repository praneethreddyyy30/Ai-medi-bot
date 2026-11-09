package com.medibot.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * Service to communicate with Google Gemini API for conversational medical support.
 */
@Service
public class GeminiChatService {

    private final RestClient restClient;
    private final String apiKey;
    private final MedlinePlusService medlinePlusService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public GeminiChatService(@Value("${gemini.api.key:}") String apiKey, MedlinePlusService medlinePlusService) {
        this.apiKey = apiKey;
        this.medlinePlusService = medlinePlusService;
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(8000);
        factory.setReadTimeout(10000);
        this.restClient = RestClient.builder()
                .requestFactory(factory)
                .baseUrl("https://generativelanguage.googleapis.com/v1beta/openai")
                .build();
    }

    private static final Pattern INAPPROPRIATE_PATTERN = Pattern.compile(
            "\\b(fuck|shit|bitch|asshole|bastard|dick|pussy|porn|sex|sexy|nude|kill you|die|hate you)\\b",
            Pattern.CASE_INSENSITIVE
    );

    @SuppressWarnings("unchecked")
    public String getConversationalReply(String userMessage, String currentDisease) {
        String trimmed = userMessage.trim().toLowerCase();

        // 1. Guardrail 1: Inappropriate / Abusive Input Filter
        if (INAPPROPRIATE_PATTERN.matcher(trimmed).find()) {
            return "⚠️ Please keep our conversation respectful and focused on healthcare. I am **MediAI**, your clinical assistant. How can I assist you with your health today?";
        }

        // 2. Guardrail 2: Friendly Casual Greeting Filter
        if (trimmed.matches("^(hi|hello|hey|hlo|good morning|good evening|good afternoon|namaste|sup|yo)[!., ]*?$")) {
            return "👋 Hello! I am **MediAI**, your healthcare assistant. You can select symptoms from **Supported Symptoms** below for an AI diagnosis, or ask me any general health questions!";
        }

        if (apiKey == null || apiKey.trim().isEmpty() || apiKey.startsWith("your_")) {
            return "🌱 **Medi AI Advice:** Stay well-hydrated, get adequate rest, and please consult a healthcare professional for specific questions regarding " + (currentDisease != null ? currentDisease : "your health") + ".";
        }

        String systemPrompt = "You are MediAI, an enterprise medical decision-support assistant. " +
                "STRICT DOMAIN RULE: You only answer medical, clinical, and health-related questions. " +
                "If the user asks about completely unrelated non-medical topics (e.g., coding, celebrities, politics, recipes), " +
                "politely state that you are specialized exclusively in health and medical guidance. " +
                "Provide safe, accurate, concise answers in 2-3 sentences. Always advise consulting a licensed physician. " +
                "Context disease: " + (currentDisease != null ? currentDisease : "None specified") + ".";

        Map<String, Object> requestBody = Map.of(
                "model", "gemini-3.1-flash-lite",
                "messages", List.of(
                        Map.of("role", "system", "content", systemPrompt),
                        Map.of("role", "user", "content", userMessage)
                ),
                "temperature", 0.6,
                "max_tokens", 200
        );

        String reply = null;
        try {
            byte[] bytes = restClient.post()
                    .uri("/chat/completions")
                    .header("Authorization", "Bearer " + apiKey)
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON, MediaType.ALL)
                    .body(requestBody)
                    .retrieve()
                    .body(byte[].class);

            if (bytes != null && bytes.length > 0) {
                String rawJson = new String(bytes, java.nio.charset.StandardCharsets.UTF_8);
                Map<String, Object> response = objectMapper.readValue(rawJson, Map.class);
                if (response != null && response.containsKey("choices")) {
                    List<Map<String, Object>> choices = (List<Map<String, Object>>) response.get("choices");
                    if (!choices.isEmpty()) {
                        Map<String, Object> firstChoice = choices.get(0);
                        Map<String, Object> message = (Map<String, Object>) firstChoice.get("message");
                        reply = (String) message.get("content");
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("⚠️ Gemini API chat failed: " + e.getMessage());
        }

        // Optional MedlinePlus enrichment: ONLY if the user specifically mentions a known disease in their question
        String medlineSummary = null;
        String[] medicalKeywords = {"malaria", "dengue", "typhoid", "covid", "influenza", "flu", "chickenpox", "tuberculosis", "cholera", "measles", "tetanus", "rabies"};
        for (String mk : medicalKeywords) {
            if (trimmed.contains(mk)) {
                medlineSummary = medlinePlusService.fetchSummary(mk);
                break;
            }
        }

        if (reply != null) {
            if (medlineSummary != null && !reply.toLowerCase().contains("medline")) {
                reply += "\n\n📚 **Verified Clinical Note (MedlinePlus / NIH):**\n" + medlineSummary;
            }
            return reply;
        }

        if (medlineSummary != null) {
            return "📚 **MedlinePlus Clinical Overview:**\n" + medlineSummary + "\n\n⚠️ Please consult a licensed doctor for personalized medical evaluation.";
        }

        return "🌱 **Care Guidance:** Ensure adequate rest, maintain hydration, and consult a doctor if your symptoms persist.";
    }
}
