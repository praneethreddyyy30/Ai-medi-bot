const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const resetBtn = document.getElementById("reset-btn");
const toggleBtn = document.getElementById("symptoms-toggle");
const symptomsContainer = document.getElementById("symptoms-list-container");
const pillGrid = document.getElementById("symptoms-pill-grid");
const activeSymptomsSection = document.getElementById("active-symptoms-section");
const activeSymptomsList = document.getElementById("active-symptoms-list");
const predictionPanel = document.getElementById("prediction-panel");
const predictionsList = document.getElementById("predictions-list");

// Supported symptoms list matching app.py exactly
const FEATURES = [
  "fever", "cough", "sore_throat", "runny_nose", "sneezing",
  "headache", "fatigue", "chills", "muscle_pain", "joint_pain",
  "rash", "abdominal_pain", "diarrhea", "vomiting", "nausea",
  "loss_of_appetite", "night_sweats", "weight_loss", "jaundice",
  "dark_urine", "bloody_stool", "confusion", "stiff_neck",
  "swollen_glands", "skin_lesions", "itching", "blisters",
  "ulcers", "paralysis", "bite_exposure"
];

let activeSymptoms = [];
let chatHistory = [];

// Initialize Symptom Selection Tags
function initSymptomTags() {
  pillGrid.innerHTML = "";
  FEATURES.forEach(symptom => {
    const btn = document.createElement("button");
    btn.className = "symptom-tag";
    btn.dataset.symptom = symptom;
    btn.textContent = symptom.replace(/_/g, " ");
    btn.addEventListener("click", () => toggleSymptom(symptom));
    pillGrid.appendChild(btn);
  });
}

// Toggle symptom selection
function toggleSymptom(symptom) {
  const index = activeSymptoms.indexOf(symptom);
  const symptomName = symptom.replace(/_/g, " ");
  
  if (index === -1) {
    activeSymptoms.push(symptom);
    // Append to input box if not already present
    let currentVal = userInput.value.trim();
    if (currentVal) {
      if (!currentVal.toLowerCase().includes(symptomName.toLowerCase())) {
        userInput.value = currentVal.endsWith(",") ? `${currentVal} ${symptomName}` : `${currentVal}, ${symptomName}`;
      }
    } else {
      userInput.value = symptomName;
    }
  } else {
    activeSymptoms.splice(index, 1);
    // Remove from input box
    let currentVal = userInput.value;
    const regex = new RegExp(`\\b${symptomName}\\b,?\\s*|\\s*,?\\s*\\b${symptomName}\\b`, 'gi');
    userInput.value = currentVal.replace(regex, '').trim().replace(/^,|,$/g, '').trim();
  }
  updateSymptomUI();
}

// Remove symptom directly (accessible globally)
window.removeSymptom = function(symptom) {
  const index = activeSymptoms.indexOf(symptom);
  if (index !== -1) {
    activeSymptoms.splice(index, 1);
    
    // Remove from input box
    const symptomName = symptom.replace(/_/g, " ");
    let currentVal = userInput.value;
    const regex = new RegExp(`\\b${symptomName}\\b,?\\s*|\\s*,?\\s*\\b${symptomName}\\b`, 'gi');
    userInput.value = currentVal.replace(regex, '').trim().replace(/^,|,$/g, '').trim();
    
    updateSymptomUI();
  }
}

// Sync selection to UI tags and active pills box
function updateSymptomUI() {
  // Update available tags in grid
  document.querySelectorAll(".symptom-tag").forEach(tag => {
    const symptom = tag.dataset.symptom;
    if (activeSymptoms.includes(symptom)) {
      tag.classList.add("selected");
    } else {
      tag.classList.remove("selected");
    }
  });

  // Render active pills box
  activeSymptomsList.innerHTML = "";
  if (activeSymptoms.length > 0) {
    activeSymptomsSection.classList.remove("hidden");
    activeSymptoms.forEach(symptom => {
      const pill = document.createElement("div");
      pill.className = "active-pill";
      pill.innerHTML = `
        <span>${symptom.replace(/_/g, " ")}</span>
        <button onclick="removeSymptom('${symptom}')" title="Remove">&times;</button>
      `;
      activeSymptomsList.appendChild(pill);
    });
  } else {
    activeSymptomsSection.classList.add("hidden");
  }
}

// Render prediction list with progress bars
function renderPredictions(predictions) {
  predictionsList.innerHTML = "";
  if (predictions && predictions.length > 0) {
    predictionPanel.classList.remove("hidden");
    predictions.forEach(p => {
      const item = document.createElement("div");
      item.className = "prediction-item";
      item.innerHTML = `
        <div class="disease-label">${p.disease}</div>
        <div class="progress-container">
          <div class="progress-bar" style="width: 0%"></div>
        </div>
        <div class="percentage-label">${p.confidence}%</div>
      `;
      predictionsList.appendChild(item);
      
      // Animate progress bar fill
      setTimeout(() => {
        const bar = item.querySelector(".progress-bar");
        if (bar) bar.style.width = `${p.confidence}%`;
      }, 50);
    });
  } else {
    predictionPanel.classList.add("hidden");
  }
}

// Append Chat Message HTML
function appendMessage(text, who = "bot") {
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  
  // Format markdown bold
  let formattedText = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  
  // Format lines
  formattedText = formattedText.replace(/\n/g, "<br>");
  
  div.innerHTML = formattedText;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Show/Hide Typing Indicator
let typingIndicatorElem = null;
function showTypingIndicator() {
  if (typingIndicatorElem) return;
  typingIndicatorElem = document.createElement("div");
  typingIndicatorElem.className = "msg bot typing-indicator";
  typingIndicatorElem.innerHTML = "<span></span><span></span><span></span>";
  chatBox.appendChild(typingIndicatorElem);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
  if (typingIndicatorElem) {
    typingIndicatorElem.remove();
    typingIndicatorElem = null;
  }
}

// Send Message Flow
async function sendMessage() {
  const msg = (userInput.value || "").trim();
  if (!msg && activeSymptoms.length === 0) return;
  
  if (msg) {
    appendMessage(msg, "user");
    chatHistory.push({ role: "user", content: msg });
    userInput.value = "";
  }
  
  sendBtn.disabled = true;
  userInput.disabled = true;
  showTypingIndicator();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: msg,
        symptoms: activeSymptoms,
        history: chatHistory
      })
    });
    
    const data = await res.json();
    removeTypingIndicator();
    
    let reply = data.response || "⚠️ No response.";
    appendMessage(reply, "bot");
    chatHistory.push({ role: "model", content: reply });
    
    // Sync symptoms list returned from backend (merged local + LLM detections)
    if (data.symptoms && data.symptoms.length > 0) {
      activeSymptoms = data.symptoms;
      updateSymptomUI();
    }
    
    // Render the suggestions panel
    if (data.predictions !== undefined && data.predictions !== null) {
      renderPredictions(data.predictions);
    }
    
  } catch (err) {
    removeTypingIndicator();
    appendMessage("⚠️ Connection error. Please try again.", "bot");
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    userInput.disabled = false;
    userInput.focus();
  }
}

// Reset App State
function resetApp() {
  chatBox.innerHTML = "";
  activeSymptoms = [];
  chatHistory = [];
  predictionsList.innerHTML = "";
  predictionPanel.classList.add("hidden");
  userInput.value = "";
  updateSymptomUI();
  appendMessage("Hi! I’m <strong>Medi AI</strong>. Select your symptoms using the tags or describe how you feel in the chat, and I'll analyze likely conditions for you.", "bot");
}

// Listeners
toggleBtn.addEventListener("click", () => {
  const isHidden = symptomsContainer.classList.contains("hidden");
  symptomsContainer.classList.toggle("hidden");
  toggleBtn.textContent = isHidden ? "Hide symptoms selector (-)" : "Select supported symptoms (+)";
});

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

resetBtn.addEventListener("click", resetApp);

// Initialize UI
initSymptomTags();
resetApp();
