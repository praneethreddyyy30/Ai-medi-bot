package com.medibot.controller;

import com.medibot.dto.ChatRequest;
import com.medibot.dto.ChatResponse;
import com.medibot.service.GeminiChatService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST Controller for conversational healthcare chat queries via Google Gemini API.
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ChatController {

    private final GeminiChatService geminiChatService;

    public ChatController(GeminiChatService geminiChatService) {
        this.geminiChatService = geminiChatService;
    }

    @PostMapping("/chat")
    public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest request) {
        String message = request.getMessage() != null ? request.getMessage().trim() : "";
        if (message.isEmpty()) {
            return ResponseEntity.ok(new ChatResponse("Please ask a medical question or select symptoms for diagnosis."));
        }

        String reply = geminiChatService.getConversationalReply(message, request.getCurrentDisease());
        return ResponseEntity.ok(new ChatResponse(reply));
    }
}
