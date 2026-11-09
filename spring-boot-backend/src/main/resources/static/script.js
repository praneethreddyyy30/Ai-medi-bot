const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const resetBtn = document.getElementById("reset-btn");
const toggleBtn = document.getElementById("symptoms-toggle");
const symptomsContainer = document.getElementById("symptoms-list-container");
const pillGrid = document.getElementById("symptoms-pill-grid");
const predictionPanel = document.getElementById("prediction-panel");
const predictionsList = document.getElementById("predictions-list");
const modeTabPredict = document.getElementById("mode-tab-predict");
const modeTabChat = document.getElementById("mode-tab-chat");

let currentMode = "predict"; // "predict" or "chat"
let FEATURES = [];
let lastDiagnosedDisease = null;

// Synonyms dictionary for natural language symptom recognition
const SYNONYMS = {
  "tired": "fatigue", "exhausted": "fatigue",
  "stomach pain": "abdominal_pain", "belly pain": "abdominal_pain",
  "stomach ache": "abdominal_pain", "throat pain": "sore_throat",
  "running nose": "runny_nose", "body ache": "muscle_pain",
  "joint ache": "joint_pain", "skin rash": "rash",
  "itchy": "itching", "shivering": "chills",
  "throwing up": "vomiting", "puking": "vomiting",
  "high fever": "fever"
};

// 1. Fetch canonical symptoms from Spring Boot backend
async function initSymptomTags() {
  try {
    const res = await fetch("/api/features");
    const data = await res.json();
    FEATURES = data.features || [];
  } catch (e) {
    console.warn("Could not fetch features from /api/features", e);
    FEATURES = [];
  }

  pillGrid.innerHTML = "";
  FEATURES.forEach(symptom => {
    const btn = document.createElement("button");
    btn.className = "symptom-tag";
    btn.dataset.symptom = symptom;
    btn.textContent = symptom.replace(/_/g, " ");
    btn.addEventListener("click", () => toggleSymptomIntoInput(symptom));
    pillGrid.appendChild(btn);
  });
}

// 2. Insert or remove symptom directly into user input box (USER REQUESTED)
function toggleSymptomIntoInput(symptom) {
  const symptomName = symptom.replace(/_/g, " ");
  let currentVal = userInput.value.trim();

  // Check if symptom is already in the text box
  const escaped = symptomName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(^|[,\\s]+)${escaped}([,\\s]+|$)`, 'i');

  if (regex.test(currentVal)) {
    // Remove it from input box
    let updated = currentVal.replace(new RegExp(`\\b${escaped}\\b`, 'gi'), '');
    updated = updated.replace(/,\s*,/g, ',').replace(/^,\s*|,\s*$/g, '').trim();
    userInput.value = updated;
  } else {
    // Append to input box directly
    if (currentVal.length > 0) {
      userInput.value = currentVal.endsWith(",") ? `${currentVal} ${symptomName}` : `${currentVal}, ${symptomName}`;
    } else {
      userInput.value = symptomName;
    }
  }

  syncTagsWithInput();
  userInput.focus();
}

// Sync tag highlights with what is currently typed in the input box
function syncTagsWithInput() {
  const text = (userInput.value || "").toLowerCase();
  document.querySelectorAll(".symptom-tag").forEach(tag => {
    const sName = tag.dataset.symptom.replace(/_/g, " ").toLowerCase();
    const regex = new RegExp(`\\b${sName}\\b`, 'i');
    if (regex.test(text)) {
      tag.classList.add("selected");
    } else {
      tag.classList.remove("selected");
    }
  });
}

userInput.addEventListener("input", syncTagsWithInput);

// Mode Switch Handler (Bottom Tabs)
function switchMode(newMode) {
  currentMode = newMode;
  if (currentMode === "predict") {
    modeTabPredict.classList.add("active");
    modeTabChat.classList.remove("active");
    userInput.placeholder = "Describe symptoms e.g. fever, headache, chills or select from supported symptoms...";
    appendBotMessage("🩺 **Switched to Disease Prediction Mode (XGBoost + Database)**\nSelect symptoms below or type how you feel and hit Send to analyze!");
  } else {
    modeTabChat.classList.add("active");
    modeTabPredict.classList.remove("active");
    if (symptomsContainer && !symptomsContainer.classList.contains("hidden")) {
      symptomsContainer.classList.add("hidden");
      if (toggleBtn) toggleBtn.classList.remove("active");
    }
    userInput.placeholder = "Ask general health questions, remedies, diet, or say hi (Gemini & MedlinePlus)...";
    appendBotMessage("💬 **Switched to Health Q&A Mode (Gemini AI + MedlinePlus)**\nAsk any medical question regarding diseases, symptoms, nutrition, or home care without running a prediction model!");
  }
}

modeTabPredict.addEventListener("click", () => switchMode("predict"));
modeTabChat.addEventListener("click", () => switchMode("chat"));

// Render Top 3 Confidence Progress Bars
function renderPredictions(predictions) {
  predictionsList.innerHTML = "";
  if (predictions && predictions.length > 0) {
    predictionPanel.classList.remove("hidden");
    predictions.forEach(p => {
      const item = document.createElement("div");
      item.className = "prediction-item";
      item.innerHTML = `
        <div class="disease-name">${p.disease}</div>
        <div class="prog-bar-bg">
          <div class="prog-bar-fill" style="width: 0%"></div>
        </div>
        <div class="prog-pct">${p.confidence}%</div>
      `;
      predictionsList.appendChild(item);
      setTimeout(() => {
        const bar = item.querySelector(".prog-bar-fill");
        if (bar) bar.style.width = `${p.confidence}%`;
      }, 50);
    });
  } else {
    predictionPanel.classList.add("hidden");
  }
}

// Append User Message
function appendUserMessage(text) {
  const row = document.createElement("div");
  row.className = "chat-row user-row";
  row.innerHTML = `
    <div class="message-card">${formatText(text)}</div>
    <div class="row-avatar user">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
      </svg>
    </div>
  `;
  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Append Bot Message
function appendBotMessage(text, htmlExtra = "") {
  const row = document.createElement("div");
  row.className = "chat-row bot-row";
  row.innerHTML = `
    <div class="row-avatar bot">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <path d="M9 12h2l1-2 2 4 1-2h2"/>
      </svg>
    </div>
    <div class="message-card">
      <div>${formatText(text)}</div>
      ${htmlExtra}
    </div>
  `;
  chatBox.appendChild(row);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function formatText(text) {
  let f = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  f = f.replace(/\n/g, "<br>");
  return f;
}

// Typing Indicator
let typingIndicatorElem = null;
function showTypingIndicator() {
  if (typingIndicatorElem) return;
  typingIndicatorElem = document.createElement("div");
  typingIndicatorElem.className = "chat-row bot-row";
  typingIndicatorElem.innerHTML = `
    <div class="row-avatar bot">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    </div>
    <div class="message-card typing-dots">
      <span></span><span></span><span></span>
    </div>
  `;
  chatBox.appendChild(typingIndicatorElem);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
  if (typingIndicatorElem) {
    typingIndicatorElem.remove();
    typingIndicatorElem = null;
  }
}

// Extract symptoms from text
function extractSymptomsFromText(text) {
  const lower = text.toLowerCase();
  const matched = [];

  for (const [phrase, canon] of Object.entries(SYNONYMS)) {
    if (lower.includes(phrase) && !matched.includes(canon)) {
      matched.push(canon);
    }
  }

  FEATURES.forEach(f => {
    const spaceForm = f.replace(/_/g, " ");
    const regex = new RegExp(`\\b${spaceForm}\\b`, 'i');
    if (regex.test(lower) && !matched.includes(f)) {
      matched.push(f);
    }
  });

  return matched;
}

// Execute AI Diagnosis Flow
async function executeDiagnosis(symptoms) {
  sendBtn.disabled = true;
  showTypingIndicator();

  try {
    const res = await fetch("/api/diagnose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symptoms: symptoms })
    });

    const data = await res.json();
    removeTypingIndicator();
    sendBtn.disabled = false;

    if (!res.ok) {
      appendBotMessage("⚠️ Diagnosis failed: " + (data.message || "Unknown error"));
      return;
    }

    lastDiagnosedDisease = data.predictedDisease;

    const reportHtml = `
      <div class="clinical-card">
        <div class="clinical-card-header">
          <div class="diag-title-area">
            <span class="diag-badge">Top Diagnostic Match</span>
            <h3>${data.predictedDisease}</h3>
          </div>
          <span class="conf-badge">${data.confidence}% Match</span>
        </div>

        ${data.emergency ? `
          <div class="emergency-alert">
            🚨 <strong>EMERGENCY TRIAGE:</strong> High-risk symptoms detected. Please report to an emergency clinical room immediately.
          </div>
        ` : ''}

        <div class="clinical-grid">
          <div class="grid-cell">
            <div class="grid-cell-label">👨‍⚕️ Recommended Specialist</div>
            <div class="grid-cell-val">${data.specialistToConsult}</div>
          </div>
          <div class="grid-cell">
            <div class="grid-cell-label">⚠️ Severity Level</div>
            <div class="grid-cell-val" style="color: ${data.severityLevel === 'Emergency' ? '#dc2626' : data.severityLevel === 'High' ? '#d97706' : '#16a34a'}">${data.severityLevel}</div>
          </div>
        </div>

        ${data.homeRemedies ? `
          <div class="remedies-box">
            <strong>🌱 Safe Home Care Tips:</strong><br>
            ${data.homeRemedies}
          </div>
        ` : ''}

        ${data.precautions ? `
          <div class="precautions-box">
            <strong>🛡️ Precautions:</strong><br>
            ${data.precautions}
          </div>
        ` : ''}
      </div>
    `;

    appendBotMessage(`Analysis completed based on: **${symptoms.join(", ").replace(/_/g, " ")}**`, reportHtml);
    renderPredictions(data.allPredictions);

  } catch (err) {
    removeTypingIndicator();
    sendBtn.disabled = false;
    appendBotMessage("⚠️ Error connecting to Spring Boot backend: " + err.message);
  }
}

// Handle User Input Submission
async function handleUserInput() {
  const msg = (userInput.value || "").trim();
  if (!msg) return;

  // Automatically close the symptoms drawer upon sending (USER REQUESTED)
  if (symptomsContainer && !symptomsContainer.classList.contains("hidden")) {
    symptomsContainer.classList.add("hidden");
    if (toggleBtn) toggleBtn.classList.remove("active");
  }

  // Append user message to chat immediately
  appendUserMessage(msg);
  userInput.value = "";
  syncTagsWithInput();

  // 1. Health Q&A Mode: Always queries Gemini AI & MedlinePlus
  if (currentMode === "chat") {
    predictionPanel.classList.add("hidden");
    sendBtn.disabled = true;
    showTypingIndicator();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });

      const data = await res.json();
      removeTypingIndicator();
      sendBtn.disabled = false;

      appendBotMessage(data.response || "I am here to help with your medical queries.");
    } catch (err) {
      removeTypingIndicator();
      sendBtn.disabled = false;
      appendBotMessage("⚠️ Chat connection error: " + err.message);
    }
    return;
  }

  // 2. Disease Prediction Mode: Always executes ML model on symptoms
  const extracted = extractSymptomsFromText(msg);
  if (extracted.length > 0) {
    executeDiagnosis(extracted);
  } else {
    appendBotMessage("ℹ️ Please select symptoms from **Supported Symptoms** or type symptoms (e.g. *fever, chills, headache*) to run Disease Prediction, or switch to **Health Q&A mode** at the bottom for general questions.");
  }
}

// Reset App State
function resetApp() {
  lastDiagnosedDisease = null;
  userInput.value = "";
  syncTagsWithInput();
  predictionPanel.classList.add("hidden");
  chatBox.innerHTML = "";
  appendBotMessage("Hello! I am **MediAI**, your clinical diagnostic assistant.\n\nSelect symptoms from **Supported Symptoms** below or describe how you feel in the box to run an analysis. You can also switch to **Health Q&A mode** at the bottom to ask medical questions!");
}

// Event Listeners
sendBtn.addEventListener("click", handleUserInput);
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleUserInput();
});

toggleBtn.addEventListener("click", () => {
  symptomsContainer.classList.toggle("hidden");
  toggleBtn.classList.toggle("active");
});

resetBtn.addEventListener("click", resetApp);

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
  initSymptomTags();
  resetApp();
});
