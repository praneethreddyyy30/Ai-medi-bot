# 🏥 MediAI — Enterprise Clinical Intelligence Platform

[![Java 17](https://img.shields.io/badge/Java-17-orange.svg)](https://www.oracle.com/java/)
[![Spring Boot 3](https://img.shields.io/badge/Spring%20Boot-3.2.4-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Spring Data JPA](https://img.shields.io/badge/Spring%20Data-JPA-blue.svg)](https://spring.io/projects/spring-data-jpa)
[![H2 Database](https://img.shields.io/badge/Database-H2%20In--Memory%20JPA-yellow.svg)](https://www.h2database.com/)
[![Google Gemini](https://img.shields.io/badge/GenAI-Gemini%203.1%20Flash--Lite-blueviolet.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **MediAI** is an enterprise-grade clinical decision-support web platform engineered in **100% Pure Java 17 / Spring Boot 3.2.4**. It operates as a self-contained healthcare intelligence system featuring dual clinical processing pipelines: an embedded **Native Java Machine Learning Inference Engine** with relational clinical knowledge enrichment (Spring Data JPA + H2), and an evidence-grounded **Conversational Health Q&A Pipeline** powered by the **U.S. National Library of Medicine (MedlinePlus)** and **Google Gemini 3.1 Flash-Lite**.

---

## 📑 Table of Contents

- [Key Highlights](#-key-highlights)
- [System Architecture](#-system-architecture)
- [Dual-Pipeline Request Workflows](#-dual-pipeline-request-workflows)
  - [1. Deterministic Disease Prediction Pipeline](#1-deterministic-disease-prediction-pipeline)
  - [2. Conversational Clinical Q&A Pipeline](#2-conversational-clinical-qa-pipeline)
- [Clinical Safety & Enterprise Guardrails](#-clinical-safety--enterprise-guardrails)
- [Embedded Native Java ML Engine](#-embedded-native-java-ml-engine)
- [Relational Knowledge Base Schema](#-relational-knowledge-base-schema)
- [Three-Tier Layered Architecture](#-three-tier-layered-architecture)
- [REST API Reference](#-rest-api-reference)
- [Directory Structure](#-directory-structure)
- [Getting Started & Local Setup](#-getting-started--local-setup)
- [Production Scaling Roadmap](#-production-scaling-roadmap)
- [Medical Disclaimer](#-medical-disclaimer)

---

## 🌟 Key Highlights

- **100% Pure Java Spring Boot Core:** Zero external Python runtime, Flask, or FastAPI processes required. Runs completely standalone inside a single JVM.
- **Sub-Millisecond Native ML Inference:** Embedded Bayesian probability engine trained on 9,900 observations across 45 infectious diseases and 30 canonical symptoms.
- **Relational Clinical Enrichment (Spring Data JPA):** Automatically pairs every ML prediction with verified medical specialists, triage severity levels, preventive precautions, and home remedies.
- **Dynamic Emergency Triage Guardrails:** Intercepts critical red-flag symptoms (`stiff_neck`, `paralysis`, `chest_pain`, etc.) and escalates cases to `EMERGENCY` priority.
- **Anti-Hallucination Grounding:** Integrates live retrieval from the **U.S. National Library of Medicine (NIH MedlinePlus)** to anchor AI responses in peer-reviewed clinical knowledge.
- **Zero-Latency Content Filtering:** Pre-compiled word-boundary regular expressions intercept profanity and non-medical queries before making costly external LLM calls.
- **Modern Embedded Medical UI:** Single-page application (SPA) featuring bottom-docked workflow toggles, dynamic symptom drawer sync, and auto-closing modals.
- **Zero-Config Maven Wrapper:** Packaged with `mvnw` and `mvnw.cmd` for instant 1-command startup on Windows, macOS, and Linux without pre-installing Maven.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Presentation Layer (Port 8080)"]
        UI["Modern Web Interface\n(Bottom Workflow Switcher • Symptom Tag Sync • Auto-Drawer)"]
    end

    subgraph SpringBootCore["Spring Boot 3 Enterprise Core (Java 17)"]
        direction TB
        
        subgraph Controllers["REST Controller Tier"]
            DC["DiagnosisController\n/api/diagnose • /api/features • /api/diseases"]
            CC["ChatController\n/api/chat"]
        end

        subgraph Guardrails["Safety & Clinical Guardrails Tier"]
            TR["Emergency Triage Engine\n(Red Flags: paralysis, stiff neck, chest pain)"]
            SG["Content & Domain Guardrails\n(Word-Boundary Regex + System Prompt Constraints)"]
        end

        subgraph Services["Enterprise Service Tier"]
            DS["DiagnosisService\n(Orchestration & Clinical Enrichment)"]
            MLE["MlClientService\n(Native Java Bayesian Inference Engine)"]
            MPC["MedlinePlusService\n(NIH XML Query Engine & Tag Stripper)"]
            GCS["GeminiChatService\n(Gemini 3.1 Flash-Lite Client & Safety Layer)"]
        end

        subgraph Persistence["Persistence Tier (Spring Data JPA)"]
            DR["DiseaseRepository\n(findByDiseaseNameIgnoreCase)"]
            H2[("H2 In-Memory DB\n(disease_knowledge_base)")]
            INIT["DataInitializer\n(Seeds 44+ Clinical Profiles on Startup)"]
        end
    end

    subgraph ExternalAPIs["External Clinical & AI Cloud Services"]
        NLM["U.S. National Library of Medicine\n(MedlinePlus XML Search API)"]
        GEMINI["Google Gemini API\n(gemini-3.1-flash-lite)"]
    end

    %% Client Interactions
    UI -->|Mode: Disease Prediction| DC
    UI -->|Mode: General Health Q&A| CC

    %% Controller to Guardrails / Services
    DC --> TR
    TR --> DS
    DS --> MLE
    MLE -->|Sub-ms Log-Likelihood Evaluation| DS
    DS --> DR
    DR --> H2
    INIT -->|On Boot CommandLineRunner| H2

    CC --> SG
    SG --> MPC
    SG --> GCS
    MPC -->|Fetch Medical Abstract| NLM
    GCS -->|Synthesize Grounded Response| GEMINI
```

---

## ⚡ Dual-Pipeline Request Workflows

MediAI enforces an architectural separation between **Inference** and **Conversational Consultation** to eliminate AI hallucinations and ensure diagnostic precision:

### 1. Deterministic Disease Prediction Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Patient as User / Patient
    participant UI as Web Frontend (SPA)
    participant Ctrl as DiagnosisController
    participant Triage as Triage Engine
    participant ML as Native Java ML Engine
    participant JPA as DiseaseRepository
    participant DB as H2 Database

    Patient->>UI: Selects symptoms (e.g. fever, cough, sore_throat)
    UI->>UI: Syncs tags into input bar & closes drawer
    UI->>Ctrl: POST /api/diagnose { "symptoms": [...] }
    Ctrl->>Triage: Scans for red flags (stiff neck, paralysis, chest pain)
    Triage-->>Ctrl: Triage evaluation result
    Ctrl->>ML: mlClientService.predict(symptoms)
    ML->>ML: Evaluates log-likelihood across 45 diseases & softmax
    ML-->>Ctrl: Returns top disease + top 3 probabilities
    Ctrl->>JPA: findByDiseaseNameIgnoreCase(topDisease)
    JPA->>DB: SQL Query on disease_knowledge_base
    DB-->>JPA: Returns specialist, severity, remedies, precautions
    JPA-->>Ctrl: DiseaseInfo clinical record
    Ctrl-->>UI: DiagnosisResponse (Structured Clinical Card)
    UI-->>Patient: Displays triage badge, specialist, remedies, confidence meters
```

1. **Symptom Ingestion:** The patient selects symptoms from the supported drawer. Clicking symptoms directly populates the search bar.
2. **Clinical Triage Evaluation:** `DiagnosisService` intercepts the input and scans for emergency red flags (`stiff_neck`, `paralysis`, `chest_pain`, `loss_of_consciousness`, `high_fever`).
3. **Native Java ML Inference:** The embedded `MlClientService` evaluates log-likelihood probabilities across 45 infectious diseases based on 30 canonical symptoms in under 1 millisecond.
4. **Relational Knowledge Enrichment:** Spring Data JPA queries `disease_knowledge_base` to retrieve the recommended **medical specialist**, **triage urgency**, **precautions**, and **home remedies**.
5. **Clinical Presentation:** Renders a structured diagnostic card with confidence progress meters and specialist guidance.

---

### 2. Conversational Clinical Q&A Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Patient as User / Patient
    participant UI as Web Frontend (SPA)
    participant Ctrl as ChatController
    participant Guard as Safety Guardrails
    participant NIH as MedlinePlus API
    participant AI as Google Gemini 3.1

    Patient->>UI: Asks: "What are the common symptoms of dengue?"
    UI->>Ctrl: POST /api/chat { "message": "..." }
    Ctrl->>Guard: Checks profanity regex & greeting fast-path
    alt Abusive Input
        Guard-->>Ctrl: Returns polite clinical conduct notice
    else Casual Greeting ("Hi", "Hello")
        Guard-->>Ctrl: Returns instant onboarding guidance (0ms)
    else Legitimate Medical Query
        par Clinical Retrieval
            Ctrl->>NIH: Query healthTopics for "dengue"
            NIH-->>Ctrl: Sanitized official medical abstract
        and Generative Synthesis
            Ctrl->>AI: Synthesizes prompt + NIH context (gemini-3.1-flash-lite)
            AI-->>Ctrl: Empathetic, grounded clinical guidance
        end
        Ctrl-->>UI: ChatResponse (Markdown formatted + NIH citation)
        UI-->>Patient: Displays formatted clinical advice with disclaimer
    end
```

---

## 🛡️ Clinical Safety & Enterprise Guardrails

| Guardrail Layer | Implementation File | Execution Phase | Purpose & Behavior |
| :--- | :--- | :--- | :--- |
| **Emergency Triage Engine** | `DiagnosisService.java` | Pre-Inference | Scans symptom array for life-threatening conditions (`stiff_neck`, `paralysis`, `chest_pain`). Overrides output to `EMERGENCY` priority and injects urgent clinical escalation headers. |
| **Word-Boundary Regex Filter** | `GeminiChatService.java` | Pre-API Call | Pre-compiled static regex `\\b(...)\\b` intercepts vulgarity or abuse in $0\text{ms}$ latency without consuming external LLM tokens or leaking data. |
| **Greeting Fast-Path** | `GeminiChatService.java` | Pre-API Call | Anchored regex (`^hi|hello...$`) responds instantly to greetings with navigation tips without incurring paid LLM costs. |
| **Semantic Domain Prompting** | `GeminiChatService.java` | Prompt Injection | Restricts Gemini strictly to healthcare and clinical support. Politely rejects out-of-scope non-medical topics (coding, politics, recipes, etc.). |
| **Anti-Hallucination Grounding** | `MedlinePlusService.java` | Response Enrichment | Fetches peer-reviewed medical abstracts from the U.S. National Library of Medicine (NIH) and appends official citations to AI responses. |

---

## 🧠 Embedded Native Java ML Engine

MediAI completely eliminates the need for Python, Flask, or FastAPI by embedding a high-performance **Bayesian Probability Classification Engine** directly into Java:

- **Location:** [`MlClientService.java`](file:///c:/Users/saipr/Downloads/Ai-medi-bot-main/spring-boot-backend/src/main/java/com/medibot/service/MlClientService.java)
- **Model Parameters:** [`disease_model.json`](file:///c:/Users/saipr/Downloads/Ai-medi-bot-main/spring-boot-backend/src/main/resources/disease_model.json) (Pre-computed from 9,900 observations)
- **Vocabulary:** 30 canonical medical symptoms (`fever`, `cough`, `sore_throat`, `stiff_neck`, etc.)
- **Target Classes:** 45 infectious diseases (Dengue, Malaria, Typhoid, COVID-19, Cholera, etc.)

### Mathematical Formulation
For each disease class $D_k$, the engine computes the log-likelihood score:

$$\ln P(D_k \mid \mathbf{x}) \propto \sum_{i \in \text{active}} \ln P(x_i = 1 \mid D_k) + \sum_{j \notin \text{active}} \ln (1 - P(x_j = 1 \mid D_k))$$

Probabilities are normalized via **numerically stable softmax**:

$$P(D_k \mid \mathbf{x}) = \frac{\exp(\ln P(D_k \mid \mathbf{x}) - \max_m \ln P(D_m \mid \mathbf{x}))}{\sum_{j} \exp(\ln P(D_j \mid \mathbf{x}) - \max_m \ln P(D_m \mid \mathbf{x}))} \times 100\%$$

**Advantages:**
- **Zero External Processes:** No Python runtime, no pip packages, no port 5001 collisions.
- **Blazing Performance:** Inference completes in under **0.5 milliseconds** directly within the JVM.
- **Thread-Safe & Scalable:** Read-only model structures execute concurrently across all Tomcat worker threads without locking.

---

## 🗄️ Relational Knowledge Base Schema

The relational clinical database is managed by **Spring Data JPA** and backed by an in-memory **H2 Database** (`jdbc:h2:mem:medibotdb`).

On application startup, [`DataInitializer.java`](file:///c:/Users/saipr/Downloads/Ai-medi-bot-main/spring-boot-backend/src/main/java/com/medibot/config/DataInitializer.java) implements `CommandLineRunner` to automatically seed 44 clinical disease records:

```sql
CREATE TABLE disease_knowledge_base (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    disease_name VARCHAR(255) NOT NULL UNIQUE,
    specialist_to_consult VARCHAR(255) NOT NULL,
    severity_level VARCHAR(50) NOT NULL,
    home_remedies VARCHAR(1000),
    precautions VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Self-Healing Clinical Fallback
If the ML engine predicts a condition not currently in the database, `DiagnosisService` automatically provisions sensible clinical defaults and commits the new disease record to H2 via `diseaseRepository.save(...)`, ensuring zero system crashes.

---

## 🏛️ Three-Tier Layered Architecture

MediAI strictly adheres to the enterprise Three-Tier architectural pattern:

```
┌────────────────────────────────────────────────────────┐
│ 1. Controller Tier (web / presentation)               │
│    - DiagnosisController.java                          │
│    - ChatController.java                               │
│    Responsibility: Request routing, DTO validation,    │
│    HTTP status codes, CORS headers.                    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 2. Service Tier (business logic & orchestration)       │
│    - DiagnosisService.java (Triage & Enrichment)       │
│    - MlClientService.java (Native Java ML Engine)      │
│    - GeminiChatService.java (GenAI & Safety Guardrail) │
│    - MedlinePlusService.java (NIH Search & Sanitizer)  │
│    Responsibility: Domain logic, algorithms, external  │
│    integrations, transaction boundaries.               │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ 3. Repository / Persistence Tier (data access)         │
│    - DiseaseRepository.java (Spring Data JPA)          │
│    - DiseaseInfo.java (Jakarta JPA Entity)             │
│    - H2 In-Memory Database (disease_knowledge_base)    │
│    Responsibility: CRUD operations, derived SQL queries│
└────────────────────────────────────────────────────────┘
```

---

## 📡 REST API Reference

### 1. Predict Disease (`POST /api/diagnose`)
Executes clinical triage, native ML inference, and H2 database clinical enrichment.

**Request:**
```bash
curl -X POST http://localhost:8080/api/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": ["fever", "cough", "sore_throat"]
  }'
```

**Response (HTTP 200 OK):**
```json
{
  "predictedDisease": "Hepatitis C",
  "confidence": 11.25,
  "specialistToConsult": "Hepatologist / Gastroenterologist",
  "severityLevel": "High",
  "homeRemedies": "Rest, avoid alcohol and fatty foods, maintain good hydration.",
  "precautions": "Consult for direct-acting antiviral therapy, do not share personal hygiene items (razors).",
  "emergency": false,
  "allPredictions": [
    { "disease": "Hepatitis C", "confidence": 11.25 },
    { "disease": "Dengue", "confidence": 9.42 },
    { "disease": "Rubella", "confidence": 8.51 }
  ]
}
```

---

### 2. Conversational Health Q&A (`POST /api/chat`)
Answers health questions using Google Gemini 3.1 Flash-Lite grounded in NIH MedlinePlus knowledge.

**Request:**
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the common symptoms and prevention steps for Dengue fever?"
  }'
```

**Response (HTTP 200 OK):**
```json
{
  "response": "Dengue fever symptoms typically include high fever, severe headache, joint and muscle pain, and skin rash. Precautions involve preventing mosquito bites using insect repellent, wearing long clothing, and eliminating standing water.\n\n📚 **Verified Clinical Note (MedlinePlus / NIH):**\nWhat is dengue ? Dengue is a viral infection transmitted by mosquitoes."
}
```

---

### 3. Get Canonical Symptoms (`GET /api/features`)
Returns the 30 recognized clinical symptom features for dynamic UI tag population.

**Request:**
```bash
curl -X GET http://localhost:8080/api/features
```

**Response (HTTP 200 OK):**
```json
{
  "features": [
    "fever", "cough", "sore_throat", "runny_nose", "sneezing",
    "headache", "fatigue", "chills", "muscle_pain", "joint_pain",
    "rash", "abdominal_pain", "diarrhea", "vomiting", "nausea",
    "loss_of_appetite", "night_sweats", "weight_loss", "jaundice",
    "dark_urine", "bloody_stool", "confusion", "stiff_neck",
    "swollen_glands", "skin_lesions", "itching", "blisters",
    "ulcers", "paralysis", "bite_exposure"
  ]
}
```

---

### 4. Get All Stored Diseases (`GET /api/diseases`)
Retrieves all seeded clinical disease profiles from the database.

---

## 📁 Directory Structure

```
Ai-medi-bot/
├── spring-boot-backend/              # 100% Pure Java 17 + Spring Boot 3 Core
│   ├── src/
│   │   ├── main/java/com/medibot/
│   │   │   ├── config/              # DataInitializer (H2 Database Startup Seeder)
│   │   │   ├── controller/          # DiagnosisController, ChatController
│   │   │   ├── dto/                 # Strongly-typed Request/Response DTOs
│   │   │   ├── model/               # DiseaseInfo JPA Entity (@Table)
│   │   │   ├── repository/          # Spring Data JPA DiseaseRepository
│   │   │   ├── service/             # DiagnosisService, MlClientService, Gemini, MedlinePlus
│   │   │   └── MediBotApplication.java # Bootstrap entry point (@SpringBootApplication)
│   │   └── main/resources/
│   │       ├── application.properties # H2 DB, JPA dialect, and Gemini API configuration
│   │       ├── disease_model.json   # Native Java ML 45-disease statistical parameters
│   │       └── static/              # Embedded Modern UI (index.html, style.css, script.js)
│   ├── mvnw                         # Maven Wrapper executable (Linux / macOS)
│   ├── mvnw.cmd                     # Maven Wrapper batch file (Windows)
│   └── pom.xml                      # Maven project descriptor & managed dependencies
├── run_all.bat                      # 1-Click Windows application launcher
├── .env.example                     # Environment template for Gemini API key
├── .gitignore                       # Git ignore rules for build artifacts & keys
├── spring_boot_guide.md             # Complete 41-page Master Technical Study Guide
├── MediAI_SpringBoot_Interview_Master_Guide.pdf # Publication-grade Master Guide PDF
└── README.md                        # Enterprise project documentation
```

---

## 🚀 Getting Started & Local Setup

### Prerequisites
- **Java 17+** (JDK 17 or higher installed on your PATH)
- **Google Gemini API Key** (Free from [Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/praneethreddyyy30/Ai-medi-bot.git
cd Ai-medi-bot
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 3. Run the Application

**Option A: Using 1-Click Windows Runner:**
```cmd
run_all.bat
```

**Option B: Using Embedded Maven Wrapper (Cross-Platform):**
```bash
cd spring-boot-backend
mvnw.cmd spring-boot:run     # Windows
./mvnw spring-boot:run       # Linux / macOS
```

### 4. Access the Live Application
- **Web User Interface:** [http://localhost:8080](http://localhost:8080)
- **H2 Database Console:** [http://localhost:8080/h2-console](http://localhost:8080/h2-console)  
  *(JDBC URL: `jdbc:h2:mem:medibotdb`, User: `sa`, Password: `password`)*

---

## 📈 Production Scaling Roadmap

To scale MediAI for **100,000+ daily active users** in cloud production:

1. **Database Migration:** Replace in-memory H2 with a managed **PostgreSQL** or **MySQL** cluster on AWS RDS with Multi-AZ replication and read-replicas.
2. **Distributed In-Memory Caching:** Introduce **Redis** to cache repetitive disease queries and MedlinePlus lookups with sub-millisecond retrieval.
3. **Containerization & Orchestration:** Package Spring Boot into a minimal distroless Docker image and orchestrate via **Kubernetes (EKS/GKE)** with Horizontal Pod Autoscalers (HPA).
4. **Security & Compliance:** Implement Spring Security with **OAuth2 / JWT stateless authentication**, role-based authorization for doctors vs. patients, and HIPAA-compliant audit logging.

---

## ⚠️ Medical Disclaimer

**MediAI is an experimental clinical decision-support and educational demonstration tool. It is NOT a substitute for professional medical diagnosis, judgment, or treatment.** Always advise patients to seek the advice of a licensed physician or qualified health provider with any questions regarding personal medical conditions. In case of emergency, contact local emergency medical services immediately.

---

## 👨‍💻 Author & License

Developed with ❤️ by **Praneeth Reddy**  
- **GitHub Repository:** [https://github.com/praneethreddyyy30/Ai-medi-bot](https://github.com/praneethreddyyy30/Ai-medi-bot)  
- **License:** Licensed under the [MIT License](LICENSE).
