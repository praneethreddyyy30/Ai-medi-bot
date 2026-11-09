package com.medibot.service;

import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Service to fetch official verified clinical summaries from US National Library of Medicine (MedlinePlus).
 * Includes thread-safe in-memory caching.
 */
@Service
public class MedlinePlusService {

    private final RestClient restClient;
    private final Map<String, String> cache = new ConcurrentHashMap<>();
    private static final Pattern SUMMARY_PATTERN = Pattern.compile("<content name=\"FullSummary\">([\\s\\S]*?)</content>", Pattern.CASE_INSENSITIVE);
    private static final Pattern HTML_TAGS = Pattern.compile("<[^>]+>");

    public MedlinePlusService() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(4000);
        factory.setReadTimeout(5000);
        this.restClient = RestClient.builder()
                .requestFactory(factory)
                .baseUrl("https://wsearch.nlm.nih.gov/ws")
                .build();
    }

    public String fetchSummary(String diseaseName) {
        String key = diseaseName.trim().toLowerCase();
        if (cache.containsKey(key)) {
            return cache.get(key);
        }

        try {
            String xml = restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/query")
                            .queryParam("db", "healthTopics")
                            .queryParam("term", diseaseName)
                            .queryParam("rettype", "brief")
                            .build())
                    .retrieve()
                    .body(String.class);

            if (xml != null) {
                Matcher matcher = SUMMARY_PATTERN.matcher(xml);
                if (matcher.find()) {
                    String raw = matcher.group(1);
                    // Strip all HTML/XML tags whether raw (<...>) or escaped (&lt;...&gt;)
                    String clean = raw.replaceAll("&lt;.*?&gt;|<.*?>", " ")
                                      .replaceAll("&[a-zA-Z0-9#]+;", " ")
                                      .replaceAll("\\s+", " ")
                                      .trim();
                    String[] sentences = clean.split("(?<=[.!?])\\s+");
                    String summary = sentences.length > 1 ? sentences[0] + " " + sentences[1] : clean;
                    if (!summary.isEmpty()) {
                        cache.put(key, summary);
                        return summary;
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("⚠️ MedlinePlus fetch failed for " + diseaseName + ": " + e.getMessage());
        }

        return null;
    }
}
