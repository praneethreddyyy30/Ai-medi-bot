import os
import re
import joblib
import numpy as np
import difflib
import xml.etree.ElementTree as ET
from openai import OpenAI
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')

# ------------------------------
# OpenAI client pointed at Gemini's OpenAI-compatible endpoint
# ------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    print("[INFO] Gemini client initialized via OpenAI-compatible API.")
else:
    print("[WARNING] GEMINI_API_KEY not set. Falling back to offline replies.")

# ------------------------------
# MedlinePlus Remedy Cache + Fetcher
# ------------------------------
# In-memory cache: disease name -> remedy summary string
REMEDY_CACHE = {}

# Comprehensive local fallback for all 45 diseases (used when API is unavailable)
DISEASE_REMEDIES = {
    "Common Cold": "Rest, stay hydrated with warm teas and water, use saline nasal spray or steam inhalation to relieve congestion.",
    "Influenza": "Get bed rest, drink warm broths and fluids, use a humidifier, and take fever-reducing medicine if needed.",
    "COVID-19": "Rest, isolate, monitor oxygen levels, stay hydrated, and practice breathing exercises. Seek care if symptoms worsen.",
    "Dengue": "Drink plenty of fluids (water, ORS, coconut water) to prevent dehydration. Rest and monitor platelet count closely.",
    "Malaria": "Seek medical attention immediately. Rest in a cool room, stay hydrated with electrolyte fluids, and use mosquito nets.",
    "Typhoid Fever": "Drink boiled or bottled water and ORS, eat soft and easily digestible meals (khichdi, bananas), and rest well.",
    "Cholera": "Begin Oral Rehydration Salts (ORS) immediately in large quantities. Seek medical care for severe dehydration.",
    "Chickenpox": "Avoid scratching blisters, take cool oatmeal baths, use calamine lotion, wear loose clothing, and rest.",
    "Measles": "Rest in a dim room if eyes are sensitive, drink warm fluids, isolate from others, and keep skin clean.",
    "Rubella": "Rest, drink warm fluids, maintain hygiene, and isolate to prevent spreading the virus to others.",
    "Tetanus": "Seek emergency medical care immediately. Keep all wounds clean and seek a booster shot if needed.",
    "Rabies": "Seek emergency medical care immediately after any animal bite. Clean the wound with soap and water for 15 minutes.",
    "Hepatitis A": "Rest well, eat a bland low-fat diet, avoid alcohol completely, stay hydrated, and maintain good hand hygiene.",
    "Hepatitis B": "Rest, avoid alcohol, eat nutritious low-fat meals, stay hydrated, and follow prescribed antiviral treatment.",
    "Hepatitis C": "Rest, avoid alcohol and fatty foods, stay hydrated, and follow medical treatment for antiviral therapy.",
    "Tuberculosis": "Take all prescribed TB medications consistently without skipping doses. Rest, eat nutritious food, and improve ventilation.",
    "Dysentery": "Stay hydrated with ORS, eat a bland BRAT diet (bananas, rice, applesauce, toast), and rest.",
    "Salmonella Infection": "Drink plenty of fluids, take ORS, eat a bland diet, and rest. Seek care if symptoms persist beyond 2 days.",
    "Ebola": "Seek emergency isolation and medical care immediately. This is a medical emergency requiring hospital treatment.",
    "Plague": "Seek emergency medical attention immediately. Plague requires urgent antibiotic treatment in a clinical setting.",
    "Chikungunya": "Rest, stay hydrated, use cold compresses on swollen joints, and take paracetamol for fever and pain.",
    "Zika": "Rest, drink plenty of fluids, use paracetamol for fever. Pregnant women must consult a doctor immediately.",
    "SARS": "Seek immediate medical care. Isolate, rest, and stay hydrated while following medical protocols.",
    "MERS": "Seek immediate medical care. Isolate and rest. This requires urgent hospital treatment.",
    "West Nile Fever": "Rest, stay hydrated, and use over-the-counter pain relievers for headache and body aches.",
    "Yellow Fever": "Rest in a cool place, stay hydrated, avoid aspirin. Seek immediate medical care for severe symptoms.",
    "Leptospirosis": "Stay hydrated, rest, and seek medical care promptly. Avoid contact with potentially contaminated water.",
    "Brucellosis": "Rest, eat nutritious food, stay hydrated, and take all prescribed antibiotics as directed.",
    "Anthrax": "Seek emergency medical care immediately. Requires urgent antibiotic treatment in a clinical setting.",
    "Botulism": "Seek emergency medical care immediately. This requires urgent hospital treatment.",
    "Meningitis": "Seek emergency medical care immediately. Rest in a quiet dark room and stay hydrated while awaiting treatment.",
    "Encephalitis": "Seek emergency medical care immediately. Keep cool, rest, and stay hydrated while awaiting treatment.",
    "Diphtheria": "Seek medical care immediately for antitoxin treatment. Rest, stay hydrated, and isolate from others.",
    "Whooping Cough": "Rest, stay hydrated, use a humidifier, and eat small frequent meals. Cough drops may soothe the throat.",
    "Mumps": "Rest, apply warm or cold packs to swollen glands, eat soft foods, stay hydrated, and isolate.",
    "Polio": "Seek medical care immediately. Rest is critical; use warm compresses on painful muscles for relief.",
    "Typhus": "Rest, stay well hydrated, and seek medical care promptly for antibiotic treatment.",
    "Rocky Mountain Spotted Fever": "Seek immediate medical care for antibiotic treatment. Rest and stay hydrated.",
    "Lyme Disease": "Rest, stay hydrated, and seek medical care promptly for antibiotic treatment to prevent complications.",
    "Leishmaniasis": "Seek medical care for treatment. Rest, stay hydrated, and use insect repellent to prevent re-infection.",
    "Schistosomiasis": "Seek medical care for antiparasitic treatment. Stay hydrated and avoid contact with contaminated water.",
    "Filariasis": "Seek medical treatment. Keep affected limbs elevated, maintain hygiene, and exercise the limb gently.",
    "Toxoplasmosis": "Rest, stay hydrated, and eat well. Seek medical care especially if pregnant or immunocompromised.",
    "Cryptosporidiosis": "Stay hydrated with ORS, eat a bland diet, rest, and avoid spreading infection through proper hand washing.",
}

MEDLINEPLUS_BASE_URL = "https://wsearch.nlm.nih.gov/ws/query"

def fetch_medlineplus_remedy(disease_name: str) -> str | None:
    """
    Fetch a verified disease summary from MedlinePlus API.
    Results are cached in REMEDY_CACHE to avoid redundant API calls.
    """
    # 1. Check in-memory cache first
    if disease_name in REMEDY_CACHE:
        print(f"[CACHE HIT] Remedy for '{disease_name}' served from cache.")
        return REMEDY_CACHE[disease_name]

    # 2. Try MedlinePlus API
    params = {"db": "healthTopics", "term": disease_name, "rettype": "brief"}
    try:
        import requests as _req
        res = _req.get(MEDLINEPLUS_BASE_URL, params=params, timeout=4)
        if res.status_code == 200:
            root = ET.fromstring(res.text)
            for doc in root.iter("document"):
                for content in doc.iter("content"):
                    if content.get("name") == "FullSummary" and content.text:
                        # Strip HTML tags and clean whitespace
                        clean = re.sub(r'<[^>]+>', '', content.text)
                        clean = re.sub(r'\s+', ' ', clean).strip()
                        # Take first 2 sentences only
                        sentences = re.split(r'(?<=[.!?])\s+', clean)
                        summary = ' '.join(sentences[:2])
                        # Store in cache
                        REMEDY_CACHE[disease_name] = summary
                        print(f"[CACHE SET] MedlinePlus remedy cached for '{disease_name}'.")
                        return summary
    except Exception as e:
        print(f"[WARNING] MedlinePlus fetch failed for '{disease_name}': {e}")

    # 3. Fall back to local DISEASE_REMEDIES dict
    local = DISEASE_REMEDIES.get(disease_name)
    if local:
        REMEDY_CACHE[disease_name] = local   # Also cache the local fallback
        return local

    return None

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
    """Use Gemini (via OpenAI-compatible client) to extract symptoms from free-form text."""
    if not gemini_client:
        return set()

    prompt = (
        f"You are a medical helper. Given a user's message, identify which of these symptoms are present. "
        f"Only return a comma-separated list of EXACT symptoms from this list, or 'none' if none are present:\n"
        f"{', '.join(FEATURES)}\n\n"
        f"User message: \"{text}\"\n"
        f"Symptoms present:"
    )

    try:
        response = gemini_client.chat.completions.create(
            model="gemini-3.1-flash-lite",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=60
        )
        raw_output = response.choices[0].message.content.lower().strip()
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
    """Get a response from Gemini via the OpenAI-compatible client."""
    if not gemini_client:
        return get_fallback_reply(user_message)

    system_instruction = (
        "You are Medi AI, a helpful, friendly, and concise medical AI assistant. "
        "Keep your answers short (typically 1-2 sentences). "
        "You ONLY answer questions related to health, symptoms, medicine, first-aid, wellness, or biology. "
        "Do not diagnose the user directly since that is handled by our classifier, but guide them to describe their symptoms. "
        "CRITICAL RULE: If the user asks anything unrelated to health, medicine, or symptoms (such as general knowledge, "
        "celebrities, movies, politics, programming, jokes, or translation requests), you MUST politely refuse to answer. "
        "Your refusal MUST say: 'I am a medical assistant and can only help with health-related queries or symptom analysis.'"
    )

    # Build context message
    context_msg = user_message
    if active_symptoms:
        symptoms_str = ", ".join([s.replace("_", " ") for s in active_symptoms])
        context_msg = f"[Context: The user currently has these selected symptoms: {symptoms_str}]\nUser message: {user_message}"

    # Build messages list in OpenAI format
    messages = [{"role": "system", "content": system_instruction}]
    if conversation_history:
        for turn in conversation_history[-4:]:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", "")
            })
    messages.append({"role": "user", "content": context_msg})

    try:
        response = gemini_client.chat.completions.create(
            model="gemini-3.1-flash-lite",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
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
    key_exists = gemini_client is not None

    test_api_status = None
    test_api_response = None

    if key_exists:
        try:
            response = gemini_client.chat.completions.create(
                model="gemini-3.1-flash-lite",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            test_api_status = 200
            test_api_response = response.choices[0].message.content.strip()
        except Exception as e:
            test_api_status = "error"
            test_api_response = str(e)[:200]

    return jsonify({
        "status": "healthy",
        "gemini_client_configured": key_exists,
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

            # ── Tier 1: Try Gemini API for personalised advice ─────────────────
            advice_text = None
            if gemini_client:
                advice_prompt = (
                    f"The user has the following symptoms: {symptoms_str}. "
                    f"The classifier predicted: {top_pred}. "
                    f"Write a very short (2-sentence) friendly medical suggestion. "
                    f"Provide safe non-side-effect home remedies (like rest, hydration, steam), "
                    f"and include a suggestion to consult a doctor for a proper diagnosis."
                )
                try:
                    res = gemini_client.chat.completions.create(
                        model="gemini-3.1-flash-lite",
                        messages=[{"role": "user", "content": advice_prompt}],
                        temperature=0.5,
                        max_tokens=100
                    )
                    advice_text = res.choices[0].message.content.strip()
                except Exception:
                    pass

            if advice_text:
                # Gemini succeeded
                reply += f"\n\n*Medi AI Support:* {advice_text}"
            else:
                # ── Tier 2 & 3: MedlinePlus API (cached) → local dict ──────────
                remedy = fetch_medlineplus_remedy(top_pred) or "Get plenty of rest, stay hydrated, and monitor your symptoms closely."
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
