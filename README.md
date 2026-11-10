# 🏥 MediAI — Enterprise Clinical Intelligence Platform

[![Java 17](https://img.shields.io/badge/Java-17-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot 3](https://img.shields.io/badge/Spring%20Boot-3.2.4-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Spring Data JPA](https://img.shields.io/badge/Spring%20Data-JPA-blue.svg)](https://spring.io/projects/spring-data-jpa)
[![H2 Database](https://img.shields.io/badge/Database-H2%20In--Memory%20JPA-yellow.svg)](https://www.h2database.com/)
[![Google Gemini](https://img.shields.io/badge/GenAI-Gemini%203.1%20Flash--Lite-blueviolet.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **MediAI** is an enterprise-grade clinical decision-support platform built on a pure **Java 17 / Spring Boot 3.2.4** enterprise architecture. It features dual clinical pipelines: a high-performance **Native Java Machine Learning Inference Engine** with relational knowledge enrichment (Spring Data JPA + H2), and an evidence-grounded **Conversational Health Q&A Pipeline** powered by the **U.S. National Library of Medicine (MedlinePlus)** and **Google Gemini 3.1**.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client["Presentation Layer (Port 8080)"]
        UI["Modern Web Interface\n(Bottom Mode Switcher + Dynamic Symptom Sync)"]
    end

    subgraph SpringBoot["Enterprise Core (Spring Boot 3 + Java 17)"]
        direction TB
        subgraph Controllers["REST Controllers"]
            DC["DiagnosisController\n/api/diagnose"]
            CC["ChatController\n/api/chat"]
        end

        subgraph Guardrails["Security & Clinical Guardrails"]
            TR["Emergency Triage Engine\n(Flags Stiff Neck, Paralysis, Chest Pain)"]
            SG["Safety Guardrails\n(Profanity & Domain Boundary Filter)"]
        end

        subgraph Services["Enterprise Service Layer"]
            DS["DiagnosisService\n(Clinical Enrichment & Orchestration)"]
            MLE["MlClientService\n(Native Java ML Bayesian Inference Engine)"]
            MPC["MedlinePlusService\n(NIH Medical Search API)"]
            GCS["GeminiChatService\n(Gemini 3.1 Flash-Lite Engine)"]
        end

        subgraph DataLayer["Persistence Layer (Spring Data JPA)"]
            DR["DiseaseRepository"]
            H2[("H2 Database\ndisease_knowledge_base")]
            INIT["DataInitializer\n(44+ Seeded Diseases)"]
        end
    end

    subgraph ExternalServices["External Medical & AI APIs"]
        NLM["U.S. National Library of Medicine\n(MedlinePlus XML Search)"]
        GEMINI["Google Gemini API\n(gemini-3.1-flash-lite)"]
    end

    %% Routing
    UI -->|Mode: Disease Prediction| DC
    UI -->|Mode: General Health Q&A| CC

    DC --> TR
    TR --> DS
    DS --> MLE
    MLE -->|Native Java Sub-ms Inference\n(30 Features -> 45 Diseases)| DS
    DS --> DR
    DR --> H2
    INIT --> H2

    CC --> SG
    SG --> MPC
    SG --> GCS
    MPC --> NLM
    GCS --> GEMINI
```

---

## ⚡ Dual Execution Pipelines

### 1. Disease Prediction Pipeline (Deterministic & Auditable Native ML)
1. **Symptom Ingestion:** The user selects or types symptoms. Clicking symptom tags directly populates the search bar.
2. **Clinical Triage Evaluation:** `DiagnosisService` intercepts the input and scans for emergency red flags (`stiff_neck`, `paralysis`, `chest_pain`, `loss_of_consciousness`, `high_fever`).
3. **Native Java ML Inference:** The embedded `MlClientService` evaluates log-likelihood probabilities across 45 infectious diseases based on 30 canonical symptoms in under 1 millisecond.
4. **Relational Knowledge Enrichment:** Spring Data JPA queries `disease_knowledge_base` to retrieve the recommended **medical specialist**, **triage urgency**, **precautions**, and **home remedies**.
5. **Clinical Presentation:** Renders a structured diagnostic card with confidence progress meters and specialist guidance.

### 2. Conversational Health Q&A Pipeline (Evidence-Grounded)
1. **Safety & Domain Guardrails:** The query passes through pre-compiled regex word-boundary filters and domain boundary assertions, rejecting profanity and irrelevant non-medical topics.
2. **Authoritative Grounding:** `MedlinePlusService` fetches verified health summaries from the **U.S. National Library of Medicine (NIH)** REST API, sanitizing escaped XML tags.
3. **Generative Clinical Reasoning:** `GeminiChatService` passes the user prompt along with grounding context to Google's **Gemini 3.1 Flash-Lite** under strict medical guardrail system prompts.
4. **Verified Delivery:** Responses are returned formatted in Markdown with official clinical citations.

---

## 🛡️ Clinical Safety & Enterprise Guardrails

| Guardrail Layer | Implementation | Purpose |
| :--- | :--- | :--- |
| **Emergency Triage Engine** | `DiagnosisService.java` | Detects life-threatening symptoms and immediately overrides triage state to `EMERGENCY`. |
| **Profanity & Content Filter** | Pre-compiled regex (`\\b...\\b`) | Intercepts vulgarity with $0\text{ms}$ latency without consuming external API tokens. |
| **Greeting Fast-Path** | Anchored regex (`^...$`) | Provides instant navigation without incurring LLM latency or cost. |
| **LLM Domain Boundary** | System prompt instructions | Restricts the generative AI exclusively to healthcare questions, politely rejecting out-of-scope topics. |
| **Anti-Hallucination Grounding** | `MedlinePlusService.java` | Synthesizes answers against live NIH clinical databases to guarantee scientific accuracy. |

---

## 🛠️ Tech Stack & Enterprise Design Patterns

- **Language & Runtime:** Java 17
- **Framework:** Spring Boot 3.2.4
- **Architecture:** Controller-Service-Repository pattern with strongly-typed DTOs
- **Database:** Spring Data JPA + H2 In-Memory Database (`jdbc:h2:mem:medibotdb`)
- **Machine Learning:** Embedded Native Java Bayesian Inference Engine (`disease_model.json`, 45 diseases, 30 symptoms)
- **External Integration:** Spring 6 `RestClient` for NIH MedlinePlus & Google Gemini 3.1
- **Build System:** Apache Maven with embedded Maven Wrapper (`./mvnw`)
- **Frontend:** Modern healthcare UI (Vanilla HTML5 / CSS3 / ES6 JavaScript) embedded in Spring Boot static resources

---

## 🚀 Getting Started

### Prerequisites
- **Java 17+** (JDK 17 or higher)
- **Google Gemini API Key** (Free from [Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/praneethreddyyy30/Ai-medi-bot.git
cd Ai-medi-bot
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run the Application (Pure Java — Single Command!)

**Using Windows 1-Click Runner:**
```cmd
run_all.bat
```

**Or using Maven Wrapper directly:**
```bash
cd spring-boot-backend
./mvnw spring-boot:run        # Linux / macOS
mvnw.cmd spring-boot:run      # Windows
```

Visit **[http://localhost:8080](http://localhost:8080)** in your browser.

---

## 🌐 Application Endpoints

| Resource | URL | Description |
| :--- | :--- | :--- |
| **Web Application** | [http://localhost:8080](http://localhost:8080) | Interactive MediAI Web Application |
| **H2 Database Console** | [http://localhost:8080/h2-console](http://localhost:8080/h2-console) | Database browser (JDBC URL: `jdbc:h2:mem:medibotdb`, User: `sa`, Password: `password`) |
| **Diagnosis API** | `POST http://localhost:8080/api/diagnose` | Predicts disease with embedded ML & enriches with H2 clinical knowledge |
| **Chat API** | `POST http://localhost:8080/api/chat` | Conversational medical advice grounded in MedlinePlus & Gemini |
| **Supported Symptoms API** | `GET http://localhost:8080/api/features` | Returns canonical list of 30 clinical symptoms |

---

## 📁 Repository Directory Structure

```
Ai-medi-bot/
├── spring-boot-backend/              # 100% Pure Java 17 + Spring Boot 3 Core
│   ├── src/
│   │   ├── main/java/com/medibot/
│   │   │   ├── config/              # DataInitializer (H2 Database Seed)
│   │   │   ├── controller/          # DiagnosisController, ChatController
│   │   │   ├── dto/                 # Strongly-typed Request/Response DTOs
│   │   │   ├── model/               # DiseaseInfo JPA Entity
│   │   │   ├── repository/          # Spring Data JPA DiseaseRepository
│   │   │   └── service/             # DiagnosisService, MlClientService (Native ML), Gemini, MedlinePlus
│   │   └── main/resources/
│   │       ├── application.properties
│   │       ├── disease_model.json   # Precomputed 45-disease statistical model
│   │       └── static/              # Modern UI (index.html, style.css, script.js)
│   ├── mvnw                         # Maven Wrapper (Unix)
│   ├── mvnw.cmd                     # Maven Wrapper (Windows)
│   └── pom.xml                      # Maven Build & Dependencies Configuration
├── run_all.bat                      # 1-Click application launcher
├── .env.example                     # Environment template for Gemini API key
├── .gitignore                       # Git ignore rules for build artifacts & keys
├── spring_boot_guide.md             # Complete 41-page Master Technical Guide
├── MediAI_SpringBoot_Interview_Master_Guide.pdf # Publication-grade PDF Guide
└── README.md                        # Enterprise project documentation
```

---

## ⚠️ Medical Disclaimer

**MediAI is a clinical decision-support demonstration tool and is NOT a substitute for professional medical judgment, diagnosis, or treatment.** Always advise patients and users to consult a qualified, licensed healthcare professional for personal medical conditions. In case of emergency, contact local emergency medical services immediately.

---

## 👨‍💻 Author & License

Developed by **Praneeth Reddy**  
Repository: [https://github.com/praneethreddyyy30/Ai-medi-bot](https://github.com/praneethreddyyy30/Ai-medi-bot)  
Licensed under the [MIT License](LICENSE).
