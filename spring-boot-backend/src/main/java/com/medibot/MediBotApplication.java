package com.medibot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class MediBotApplication {

    public static void main(String[] args) {
        SpringApplication.run(MediBotApplication.class, args);
        System.out.println("=================================================");
        System.out.println("🚀 AI Medi Bot Enterprise Backend is LIVE on Port 8080");
        System.out.println("📊 H2 Database Console: http://localhost:8080/h2-console");
        System.out.println("🩺 API Endpoint: http://localhost:8080/api/diagnose");
        System.out.println("=================================================");
    }
}
