import os
import re
import joblib
import numpy as np
import requests
import difflib
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

# ------------------------------
# Load Disease Prediction Model
# ------------------------------
model = None
label_encoder = None
try:
    loaded = joblib.load("disease_predictor.pkl")
    if isinstance(loaded, tuple) and len(loaded) >= 2:
        model, label_encoder = loaded[0], loaded[1]
    else:
        model = loaded
    print("[INFO] Disease model loaded. Has label encoder:", label_encoder is not None)
except Exception as e:
    print(f"[ERROR] Failed to load disease_predictor.pkl: {e}")

# ------------------------------
# Symptom features (must match training order)
# ------------------------------
FEATURES = [
    "fever","cough","sore_throat","runny_nose","sneezing",
    "headache","fatigue","chills","muscle_pain","joint_pain",
    "rash","abdominal_pain","diarrhea","vomiting","nausea",
    "loss_of_appetite","night_sweats","weight_loss","jaundice",
    "dark_urine","bloody_stool","confusion","stiff_neck",
    "swollen_glands","skin_lesions","itching","blisters",
    "ulcers","paralysis","bite_exposure"
]

# Common synonyms/phrases -> canonical feature
SYNONYMS = {
    "tired": "fatigue",
    "exhausted": "fatigue",
    "stomach pain": "abdominal_pain",
    "belly pain": "abdominal_pain",
    "stomach ache": "abdominal_pain",
    "throat pain": "sore_throat",
    "sore throat": "sore_throat",
    "running nose": "runny_nose",
    "muscle ache": "muscle_pain",
    "body ache": "muscle_pain",
    "joint ache": "joint_paint",
    "skin rash": "rash",
    "itchy": "itching",
    "itchiness": "itching",
    "vomit": "vomiting",
    "vomitting": "vomiting",
    "nauseous": "nausea",
    "nauseated": "nausea",
    "lost appetite": "loss_of_appetite",
    "loss of appetite": "loss_of_appetite",
    "night sweat": "night_sweats",
    "yellow skin": "jaundice",
    "yellow eyes": "jaundice",
    "lymph nodes": "swollen_glands",
    "swollen lymph nodes": "swollen_glands",
    "lesions": "skin_lesions",
    "blister": "blisters",
    "ulcer": "ulcers",
    "paralyzed": "paralysis",
    "bite": "bite_exposure"
}

# Greeting and bye detection (expanded to catch letters trailing like hii, heyy, helloo, hloo)
GREETING_RE = re.compile(r"^\s*(hi+l*o*|hello+|hey+|yo+|hlo+|helo+|hy+|hola|good\s+(morning|afternoon|evening))\b", re.I)
BYE_RE = re.compile(r"^\s*(bye|goodbye|see you|see ya|take care|farewell)\b", re.I)

# Read API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ------------------------------
# Helper functions
# ------------------------------
def detect_symptoms(text: str):
    """Return a set of canonical FEATURES detected in free text, with fuzzy matching for typos."""
    text = text.lower()
    found = set()

    # 1. Exact matches
    for f in FEATURES:
        if f in text.replace(" ", "_"):
            found.add(f)
        if f.replace("_", " ") in text:
            found.add(f)

    for phrase, canonical in SYNONYMS.items():
        if phrase in text:
            found.add(canonical)

    # 2. Fuzzy matches for typos (e.g., "headche", "fevr")
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text)  # Only fuzzy check words of length >= 4
    for word in words:
        close_features = difflib.get_close_matches(word, FEATURES, n=1, cutoff=0.8)
        if close_features:
            found.add(close_features[0])

        close_synonyms = difflib.get_close_matches(word, list(SYNONYMS.keys()), n=1, cutoff=0.8)
        if close_synonyms:
            found.add(SYNONYMS[close_synonyms[0]])

    return found


def extract_symptoms_with_llm(text: str):
    """Use Gemini to extract symptoms from free-form text as a fallback."""
    if not GEMINI_API_KEY:
        return set()

    prompt = (
        f"You are a medical helper. Given a user's message, identify which of these symptoms are present. "
        f"Only return a comma-separated list of EXACT symptoms from this list, or 'none' if none are present:\n"
        f"{', '.join(FEATURES)}\n\n"
        f"User message: \"{text}\"\n"
        f"Symptoms present:"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 60
        }
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=3)
        if response.status_code == 200:
            res_json = response.json()
            raw_output = res_json['candidates'][0]['content']['parts'][0]['text'].lower().strip()
            found = set()
            for s in FEATURES:
                if s in raw_output:
                    found.add(s)
            return found
    except Exception as e:
        print(f"[WARNING] LLM symptom extraction failed: {e}")
    return set()


def predict_diseases(symptoms_list):
    """Build feature vector from active symptoms and return top 3 predictions with confidence."""
    if model is None:
        return None, "Model not loaded. Please ensure disease_predictor.pkl is present."

    if not symptoms_list:
        return None, "no_symptoms"

    vector = [1 if f in symptoms_list else 0 for f in FEATURES]
    try:
        # Get probability estimates for all classes
        probs = model.predict_proba([vector])[0]
        # Sort indices by probability descending
        top_indices = np.argsort(probs)[::-1][:3]

        predictions = []
        for idx in top_indices:
            conf = float(probs[idx])
            if conf >= 0.01:  # only include if >= 1% confidence
                if label_encoder is not None:
                    disease = label_encoder.inverse_transform([idx])[0]
                else:
                    disease = f"Class {idx}"
                predictions.append({
                    "disease": disease,
                    "confidence": round(conf * 100, 1)
                })
        return predictions, None
    except Exception as e:
        return None, f"prediction_error: {e}"


def process_chat_message(msg: str, client_symptoms: list):
    """Extract symptoms locally, then via LLM if needed, merge and predict."""
    # 1. Local extraction
    detected = detect_symptoms(msg)

    # 2. LLM extraction if nothing found locally and text is a full phrase
    if not detected and len(msg.split()) > 3:
        detected = extract_symptoms_with_llm(msg)

    # 3. Merge with frontend symptoms
    all_symptoms = set(client_symptoms) | detected
    all_symptoms = sorted(list(all_symptoms))

    # 4. Predict
    predictions, err = predict_diseases(all_symptoms)
    return {
        "symptoms": all_symptoms,
        "predictions": predictions,
        "newly_detected": sorted(list(detected))
    }, err


# Keywords to identify medical topics in fallback mode
MEDICAL_KEYWORDS = [
    "dengue", "malaria", "fever", "cough", "flu", "cold", "pain", "infection", 
    "headache", "virus", "disease", "treatment", "doctor", "medicine", "pill", 
    "symptom", "vomit", "nausea", "rash", "itch", "diarrhea", "sick", "health",
    "hospital", "care", "prevent", "vaccine", "contagious", "infectious"
]


def get_fallback_reply(user_message: str) -> str:
    """Fallback conversation system when Gemini API is not configured or rate-limited."""
    msg = user_message.lower()

    if GREETING_RE.match(user_message):
        return "Hello! I'm Medi AI. Please select or describe your symptoms below, and I'll suggest a likely condition."

    if BYE_RE.match(user_message):
        return "Goodbye! Take care of yourself. Let me know if you need anything else."

    if "symptom" in msg or "help" in msg or "what can you do" in msg:
        return "I can predict likely health conditions based on symptoms like fever, cough, and headache. Select symptoms using the tags below or type them."

    # Check if the user message contains any medical keywords
    has_medical_keyword = any(kw in msg for kw in MEDICAL_KEYWORDS)
    if has_medical_keyword:
        return "I am currently offline or experiencing rate limits. While I cannot answer general medical questions right now, please select or enter your symptoms to get a classifier suggestion."

    return "I am a medical assistant and can only help with health-related queries or symptom analysis."


def gemini_reply(user_message: str, active_symptoms: list = None, conversation_history: list = None) -> str:
    """Get a response from the serverless Gemini API."""
    if not GEMINI_API_KEY:
        return get_fallback_reply(user_message)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"
    
    system_instruction = (
        "You are Medi AI, a helpful, friendly, and concise medical AI assistant. "
        "Keep your answers short (typically 1-2 sentences). "
        "You ONLY answer questions related to health, symptoms, medicine, first-aid, wellness, or biology. "
        "Do not diagnose the user directly since that is handled by our classifier, but guide them to describe their symptoms. "
        "CRITICAL RULE: If the user asks anything unrelated to health, medicine, or symptoms (such as general knowledge, "
        "celebrities, movies, politics, programming, jokes, or translation requests), you MUST politely refuse to answer. "
        "Your refusal MUST say: 'I am a medical assistant and can only help with health-related queries or symptom analysis.'"
    )

    # Build context message internally if we have active symptoms
    context_msg = user_message
    if active_symptoms:
        symptoms_str = ", ".join([s.replace("_", " ") for s in active_symptoms])
        context_msg = f"[Context: The user currently has these selected symptoms: {symptoms_str}]\nUser message: {user_message}"

    contents = []
    if conversation_history:
        # Include last 4 turns for context
        for turn in conversation_history[-4:]:
            contents.append({
                "role": "user" if turn.get("role") == "user" else "model",
                "parts": [{"text": turn.get("content", "")}]
            })

    contents.append({
        "role": "user",
        "parts": [{"text": context_msg}]
    })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 100
        }
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
        if response.status_code == 200:
            res_json = response.json()
            reply = res_json['candidates'][0]['content']['parts'][0]['text']
            return reply.strip()
        else:
            print(f"[WARNING] Gemini API returned status {response.status_code}: {response.text}")
            return get_fallback_reply(user_message)
    except Exception as e:
        print(f"[ERROR] Failed to query Gemini API: {e}")
        return get_fallback_reply(user_message)


# ------------------------------
# Routes
# ------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    key_exists = GEMINI_API_KEY is not None and len(GEMINI_API_KEY.strip()) > 0
    key_prefix = GEMINI_API_KEY[:6] if key_exists else "None"
    
    test_api_status = None
    test_api_response = None
    
    if key_exists:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"
            payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
            res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=4)
            test_api_status = res.status_code
            test_api_response = res.text[:200]  # Show first 200 chars
        except Exception as e:
            test_api_status = "error"
            test_api_response = str(e)
            
    return jsonify({
        "status": "healthy",
        "gemini_api_key_configured": key_exists,
        "key_prefix": key_prefix,
        "test_api_status": test_api_status,
        "test_api_response": test_api_response
    })


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    msg = data.get("message", "").strip()
    client_symptoms = data.get("symptoms", [])
    history = data.get("history", [])

    if not msg and not client_symptoms:
        return jsonify({
            "response": "Please type a message or select a symptom.",
            "symptoms": client_symptoms,
            "predictions": []
        })

    greeting_match = GREETING_RE.match(msg)
    bye_match = BYE_RE.match(msg)

    # 1. Handle goodbye
    if bye_match:
        return jsonify({
            "response": "Goodbye! Take care of yourself. If you have symptoms later, feel free to come back.",
            "symptoms": client_symptoms,
            "predictions": []
        })

    # Detect if any new symptoms are in the message
    detected = detect_symptoms(msg)
    if not detected and len(msg.split()) > 3:
        detected = extract_symptoms_with_llm(msg)

    # Combine all symptoms
    all_symptoms = sorted(list(set(client_symptoms) | detected))

    # Determine if this is a prediction request or conversational query.
    # It is a prediction request if:
    # - User sent new symptoms in their message (detected is not empty)
    # - OR user clicked/toggled a tag (msg is empty, but we have active symptoms)
    is_prediction_request = len(detected) > 0 or (msg == "" and len(all_symptoms) > 0)

    if is_prediction_request:
        predictions, err = predict_diseases(all_symptoms)
        if not err and predictions:
            symptoms_str = ", ".join([s.replace("_", " ") for s in all_symptoms])
            top_pred = predictions[0]["disease"]

            if greeting_match:
                greet_text = greeting_match.group(0).strip().capitalize()
                reply = (f"{greet_text}! Based on the symptoms ({symptoms_str}), the classifier suggests **{top_pred}** as the most likely match. "
                         f"See the detailed breakdown below.")
            else:
                reply = (f"Based on the symptoms ({symptoms_str}), the classifier suggests **{top_pred}** as the most likely match. "
                         f"See the detailed breakdown below.")

            # Remedies lookup dictionary for offline fallback
            DISEASE_REMEDIES = {
                "Common Cold": "Rest, stay hydrated (water, warm teas), and use saline nasal sprays or steam inhalation.",
                "Influenza": "Get plenty of bed rest, drink warm broths, and use a humidifier to ease congestion.",
                "COVID-19": "Rest, monitor oxygen levels, isolate, stay hydrated, and practice breathing exercises.",
                "Dengue": "Drink plenty of fluids (water, ORS) to prevent dehydration, rest, and monitor platelet count.",
                "Malaria": "Seek immediate medical attention. Rest in a cool room and stay hydrated with electrolyte fluids.",
                "Typhoid Fever": "Drink boiled water or ORS, eat light/easily digestible meals, and rest.",
                "Tetanus": "Seek emergency medical care immediately. Keep wounds clean.",
                "Rubella": "Rest, drink warm fluids, keep skin clean, and avoid contact with others to prevent spread.",
                "Measles": "Rest, keep the room dim if eyes are sensitive to light, drink warm fluids, and isolate.",
                "Chickenpox": "Avoid scratching rashes, take cool oatmeal baths, wear loose clothing, and rest.",
                "Cholera": "Immediately start taking Oral Rehydration Salts (ORS) in large quantities to prevent severe dehydration.",
                "Dysentery": "Stay hydrated with ORS, eat a bland diet (bananas, rice), and rest.",
                "Salmonella Infection": "Drink fluids to replace lost electrolytes, rest, and eat simple bland foods."
            }

            # Optional Gemini advice
            advice_text = None
            if GEMINI_API_KEY:
                advice_prompt = (
                    f"The user has the following symptoms: {symptoms_str}. "
                    f"The classifier predicted: {top_pred}. "
                    f"Write a very short (2-sentence) friendly medical suggestion. "
                    f"Provide safe non-side-effect home remedies (like rest, hydration, steam), "
                    f"and include a suggestion to consult a doctor for a proper diagnosis."
                )
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"
                    payload = {
                        "contents": [{"parts": [{"text": advice_prompt}]}],
                        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 100}
                    }
                    res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=4)
                    if res.status_code == 200:
                        advice_text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                except Exception:
                    pass

            if advice_text:
                reply += f"\n\n*Medi AI Support:* {advice_text}"
            else:
                remedy = DISEASE_REMEDIES.get(top_pred, "Get plenty of rest, stay hydrated, and monitor your symptoms closely.")
                reply += (f"\n\n*Medi AI Support:* 🌱 **Home Care Tips:** {remedy}\n\n"
                          f"⚠️ **Note:** Please consult a doctor or healthcare professional for proper diagnosis and treatment.")

            return jsonify({
                "response": reply,
                "symptoms": all_symptoms,
                "predictions": predictions
            })

    # Conversational response flow (for greetings, general chat, follow-up questions)
    bot_response = gemini_reply(msg, all_symptoms, history)
    
    return jsonify({
        "response": bot_response,
        "symptoms": client_symptoms,  # keep existing symptoms intact
        "predictions": None  # return None so the frontend keeps showing the previous prediction
    })


# ------------------------------
# Run
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)
