import os
import re
import joblib
import numpy as np
import difflib
import xml.etree.ElementTree as ET
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# ------------------------------
# FastAPI App
# ------------------------------
app = FastAPI(
    title="Medi AI",
    description="AI-powered medical symptom analyzer — predicts diseases, provides home remedies via Gemini & MedlinePlus",
    version="2.0.0"
)

# ------------------------------
# OpenAI client → Gemini OpenAI-compatible endpoint
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
REMEDY_CACHE = {}

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
    """Fetch a verified disease summary from MedlinePlus API. Results are cached."""
    if disease_name in REMEDY_CACHE:
        print(f"[CACHE HIT] Remedy for '{disease_name}' served from cache.")
        return REMEDY_CACHE[disease_name]
    params = {"db": "healthTopics", "term": disease_name, "rettype": "brief"}
    try:
        import requests as _req
        res = _req.get(MEDLINEPLUS_BASE_URL, params=params, timeout=4)
        if res.status_code == 200:
            root = ET.fromstring(res.text)
            for doc in root.iter("document"):
                for content in doc.iter("content"):
                    if content.get("name") == "FullSummary" and content.text:
                        clean = re.sub(r'<[^>]+>', '', content.text)
                        clean = re.sub(r'\s+', ' ', clean).strip()
                        sentences = re.split(r'(?<=[.!?])\s+', clean)
                        summary = ' '.join(sentences[:2])
                        REMEDY_CACHE[disease_name] = summary
                        print(f"[CACHE SET] MedlinePlus remedy cached for '{disease_name}'.")
                        return summary
    except Exception as e:
        print(f"[WARNING] MedlinePlus fetch failed for '{disease_name}': {e}")
    local = DISEASE_REMEDIES.get(disease_name)
    if local:
        REMEDY_CACHE[disease_name] = local
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
# Symptom Features & Synonyms
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

SYNONYMS = {
    "tired": "fatigue", "exhausted": "fatigue",
    "stomach pain": "abdominal_pain", "belly pain": "abdominal_pain",
    "stomach ache": "abdominal_pain", "throat pain": "sore_throat",
    "sore throat": "sore_throat", "running nose": "runny_nose",
    "muscle ache": "muscle_pain", "body ache": "muscle_pain",
    "joint ache": "joint_pain", "skin rash": "rash",
    "itchy": "itching", "itchiness": "itching",
    "vomit": "vomiting", "vomitting": "vomiting",
    "nauseous": "nausea", "nauseated": "nausea",
    "lost appetite": "loss_of_appetite", "loss of appetite": "loss_of_appetite",
    "night sweat": "night_sweats", "yellow skin": "jaundice",
    "yellow eyes": "jaundice", "lymph nodes": "swollen_glands",
    "swollen lymph nodes": "swollen_glands", "lesions": "skin_lesions",
    "blister": "blisters", "ulcer": "ulcers",
    "paralyzed": "paralysis", "bite": "bite_exposure"
}

GREETING_RE = re.compile(r"^\s*(hi+l*o*|hello+|hey+|yo+|hlo+|helo+|hy+|hola|good\s+(morning|afternoon|evening))\b", re.I)
BYE_RE = re.compile(r"^\s*(bye|goodbye|see you|see ya|take care|farewell)\b", re.I)

MEDICAL_KEYWORDS = [
    "dengue", "malaria", "fever", "cough", "flu", "cold", "pain", "infection",
    "headache", "virus", "disease", "treatment", "doctor", "medicine", "pill",
    "symptom", "vomit", "nausea", "rash", "itch", "diarrhea", "sick", "health",
    "hospital", "care", "prevent", "vaccine", "contagious", "infectious"
]

# ------------------------------
# Pydantic Request/Response Models
# ------------------------------
class ChatRequest(BaseModel):
    message: str = ""
    symptoms: list[str] = []
    history: list[dict] = []

class ChatResponse(BaseModel):
    response: str
    symptoms: list[str]
    predictions: list[dict] | None = None

# ------------------------------
# Core Logic Functions
# ------------------------------
def detect_symptoms(text: str) -> set:
    """Return canonical symptoms detected in free text with fuzzy matching."""
    text = text.lower()
    found = set()
    for f in FEATURES:
        if f in text.replace(" ", "_") or f.replace("_", " ") in text:
            found.add(f)
    for phrase, canonical in SYNONYMS.items():
        if phrase in text:
            found.add(canonical)
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text)
    for word in words:
        close = difflib.get_close_matches(word, FEATURES, n=1, cutoff=0.8)
        if close:
            found.add(close[0])
        close_syn = difflib.get_close_matches(word, list(SYNONYMS.keys()), n=1, cutoff=0.8)
        if close_syn:
            found.add(SYNONYMS[close_syn[0]])
    return found


def extract_symptoms_with_llm(text: str) -> set:
    """Use Gemini to extract symptoms from free-form text."""
    if not gemini_client:
        return set()
    prompt = (
        f"You are a medical helper. Given a user's message, identify which of these symptoms are present. "
        f"Only return a comma-separated list of EXACT symptoms from this list, or 'none' if none are present:\n"
        f"{', '.join(FEATURES)}\n\nUser message: \"{text}\"\nSymptoms present:"
    )
    try:
        response = gemini_client.chat.completions.create(
            model="gemini-3.1-flash-lite",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, max_tokens=60
        )
        raw = response.choices[0].message.content.lower().strip()
        return {s for s in FEATURES if s in raw}
    except Exception as e:
        print(f"[WARNING] LLM symptom extraction failed: {e}")
    return set()


def predict_diseases(symptoms_list: list) -> tuple:
    """Return top 3 disease predictions with confidence scores."""
    if model is None:
        return None, "Model not loaded."
    if not symptoms_list:
        return None, "no_symptoms"
    vector = [1 if f in symptoms_list else 0 for f in FEATURES]
    try:
        probs = model.predict_proba([vector])[0]
        top_indices = np.argsort(probs)[::-1][:3]
        predictions = []
        for idx in top_indices:
            conf = float(probs[idx])
            if conf >= 0.01:
                disease = label_encoder.inverse_transform([idx])[0] if label_encoder else f"Class {idx}"
                predictions.append({"disease": disease, "confidence": round(conf * 100, 1)})
        return predictions, None
    except Exception as e:
        return None, f"prediction_error: {e}"


def get_fallback_reply(user_message: str) -> str:
    """Fallback when Gemini is rate-limited — uses MedlinePlus for medical queries."""
    msg = user_message.lower()
    if GREETING_RE.match(user_message):
        return "Hello! I'm Medi AI. Please select or describe your symptoms below, and I'll suggest a likely condition."
    if BYE_RE.match(user_message):
        return "Goodbye! Take care of yourself. Let me know if you need anything else."
    if "symptom" in msg or "help" in msg or "what can you do" in msg:
        return "I can predict health conditions based on symptoms like fever, cough, and headache. Type or select symptoms to begin."
    what_is_match = re.search(r"what\s+is\s+(?:a\s+|an\s+|the\s+)?([a-z\s\-]+?)[\?\.\!]?$", msg.strip())
    if what_is_match:
        term = what_is_match.group(1).strip()
        answer = fetch_medlineplus_remedy(term)
        if answer:
            return f"📚 *From MedlinePlus (NLM):* {answer}\n\n⚠️ For personalised advice, please describe your symptoms below."
    if any(kw in msg for kw in MEDICAL_KEYWORDS):
        for kw in MEDICAL_KEYWORDS:
            if kw in msg:
                answer = fetch_medlineplus_remedy(kw)
                if answer:
                    return f"📚 *From MedlinePlus (NLM):* {answer}\n\n⚠️ For personalised advice, describe your symptoms below."
        return "I am currently experiencing rate limits. Please select or enter your symptoms below."
    return "I am a medical assistant and can only help with health-related queries or symptom analysis."


def gemini_reply(user_message: str, active_symptoms: list = None, conversation_history: list = None) -> str:
    """Get a conversational response from Gemini via the OpenAI-compatible client."""
    if not gemini_client:
        return get_fallback_reply(user_message)
    system_instruction = (
        "You are Medi AI, a helpful, friendly, and concise medical AI assistant. "
        "Keep your answers short (1-2 sentences). "
        "You ONLY answer questions related to health, symptoms, medicine, first-aid, wellness, or biology. "
        "CRITICAL RULE: If the user asks anything unrelated to health, you MUST say: "
        "'I am a medical assistant and can only help with health-related queries or symptom analysis.'"
    )
    context_msg = user_message
    if active_symptoms:
        symptoms_str = ", ".join([s.replace("_", " ") for s in active_symptoms])
        context_msg = f"[Context: user has symptoms: {symptoms_str}]\nUser message: {user_message}"
    messages = [{"role": "system", "content": system_instruction}]
    if conversation_history:
        for turn in conversation_history[-4:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
    messages.append({"role": "user", "content": context_msg})
    try:
        response = gemini_client.chat.completions.create(
            model="gemini-3.1-flash-lite", messages=messages, temperature=0.7, max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] Gemini API error: {e}")
        return get_fallback_reply(user_message)


# ------------------------------
# FastAPI Routes
# ------------------------------
@app.get("/", include_in_schema=False)
async def index():
    """Serve the main UI."""
    return FileResponse("index.html")


@app.get("/health", tags=["System"], summary="Live API health check")
async def health():
    """Check if the Gemini client is configured and responsive."""
    key_exists = gemini_client is not None
    test_status, test_response = None, None
    if key_exists:
        try:
            r = gemini_client.chat.completions.create(
                model="gemini-3.1-flash-lite",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            test_status = 200
            test_response = r.choices[0].message.content.strip()
        except Exception as e:
            test_status = "error"
            test_response = str(e)[:200]
    return {
        "status": "healthy",
        "gemini_client_configured": key_exists,
        "test_api_status": test_status,
        "test_api_response": test_response
    }


@app.get("/features", tags=["System"], summary="Get symptom features list")
async def features():
    """Return the canonical symptom features list — frontend loads this dynamically."""
    return {"features": FEATURES}


@app.post("/chat", response_model=ChatResponse, tags=["Chat"], summary="Main chatbot endpoint")
async def chat(body: ChatRequest):
    """
    Main chatbot endpoint.
    - Detects symptoms from message (exact + fuzzy + LLM)
    - Predicts top 3 diseases using XGBoost
    - Returns Gemini advice or MedlinePlus remedy as fallback
    """
    msg = body.message.strip()
    client_symptoms = body.symptoms
    history = body.history

    if not msg and not client_symptoms:
        return ChatResponse(
            response="Please type a message or select a symptom.",
            symptoms=client_symptoms,
            predictions=[]
        )

    if BYE_RE.match(msg):
        return ChatResponse(
            response="Goodbye! Take care of yourself. If you have symptoms later, feel free to come back.",
            symptoms=client_symptoms,
            predictions=[]
        )

    # Detect symptoms from message
    detected = detect_symptoms(msg)
    if not detected and len(msg.split()) > 3:
        detected = extract_symptoms_with_llm(msg)

    all_symptoms = sorted(list(set(client_symptoms) | detected))
    greeting_match = GREETING_RE.match(msg)
    is_prediction_request = len(detected) > 0 or (msg == "" and len(all_symptoms) > 0)

    if is_prediction_request:
        predictions, err = predict_diseases(all_symptoms)
        if not err and predictions:
            symptoms_str = ", ".join([s.replace("_", " ") for s in all_symptoms])
            top_pred = predictions[0]["disease"]
            if greeting_match:
                greet_text = greeting_match.group(0).strip().capitalize()
                reply = (f"{greet_text}! Based on the symptoms ({symptoms_str}), the classifier suggests "
                         f"**{top_pred}** as the most likely match. See the detailed breakdown below.")
            else:
                reply = (f"Based on the symptoms ({symptoms_str}), the classifier suggests "
                         f"**{top_pred}** as the most likely match. See the detailed breakdown below.")

            # Tier 1: Gemini personalised advice
            advice_text = None
            if gemini_client:
                advice_prompt = (
                    f"The user has symptoms: {symptoms_str}. Classifier predicted: {top_pred}. "
                    f"Write a very short (2-sentence) friendly suggestion with safe home remedies "
                    f"and include advice to consult a doctor."
                )
                try:
                    res = gemini_client.chat.completions.create(
                        model="gemini-3.1-flash-lite",
                        messages=[{"role": "user", "content": advice_prompt}],
                        temperature=0.5, max_tokens=100
                    )
                    advice_text = res.choices[0].message.content.strip()
                except Exception:
                    pass

            if advice_text:
                reply += f"\n\n*Medi AI Support:* {advice_text}"
            else:
                # Tier 2 & 3: MedlinePlus (cached) → local dict
                remedy = fetch_medlineplus_remedy(top_pred) or "Get plenty of rest, stay hydrated, and monitor your symptoms closely."
                reply += (f"\n\n*Medi AI Support:* 🌱 **Home Care Tips:** {remedy}\n\n"
                          f"⚠️ **Note:** Please consult a doctor for proper diagnosis and treatment.")

            return ChatResponse(response=reply, symptoms=all_symptoms, predictions=predictions)

    # Conversational flow
    bot_response = gemini_reply(msg, all_symptoms, history)
    return ChatResponse(response=bot_response, symptoms=client_symptoms, predictions=None)


# Serve static files (CSS, JS) via catch-all
@app.get("/{filename:path}", include_in_schema=False)
async def static_files(filename: str):
    filepath = os.path.join(".", filename)
    if os.path.isfile(filepath):
        return FileResponse(filepath)
    return JSONResponse(status_code=404, content={"error": "Not found"})


# ------------------------------
# Run
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
