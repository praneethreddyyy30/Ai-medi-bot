"""
Medi AI - Python ML Inference Microservice
Port: 5001
Exposes a lightweight REST endpoint to serve the XGBoost disease classification model.
"""
import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')
import joblib
import numpy as np
import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Disease Prediction ML Microservice", version="1.0.0")

# 1. Load canonical features
FEATURES_PATH = os.path.join(os.path.dirname(__file__), "features.json")
with open(FEATURES_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
    FEATURES = data if isinstance(data, list) else data.get("features", [])

FEATURE_INDEX = {feat: idx for idx, feat in enumerate(FEATURES)}

# 2. Load trained XGBoost model and LabelEncoder
MODEL_PATH = os.path.join(os.path.dirname(__file__), "disease_predictor.pkl")
try:
    loaded = joblib.load(MODEL_PATH)
    if isinstance(loaded, tuple) and len(loaded) >= 2:
        model, label_encoder = loaded[0], loaded[1]
    else:
        model, label_encoder = loaded, None
    print(f"✅ XGBoost model loaded successfully. Features count: {len(FEATURES)}")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    model, label_encoder = None, None


class PredictRequest(BaseModel):
    symptoms: list[str]


class DiseaseProbability(BaseModel):
    disease: str
    confidence: float


class PredictResponse(BaseModel):
    top_disease: str
    confidence: float
    predictions: list[DiseaseProbability]


@app.get("/health")
def health_check():
    return {
        "status": "UP",
        "service": "disease-ml-microservice",
        "model_loaded": model is not None,
        "features_count": len(FEATURES)
    }


@app.get("/features")
def get_features():
    return {"features": FEATURES}


@app.post("/predict")
async def predict(request: Request):
    if not model:
        raise HTTPException(status_code=500, detail="ML model is not loaded.")
    
    try:
        raw = await request.body()
        print(f"[DEBUG] Received raw body: {raw}")
        body = await request.json()
    except Exception as e:
        print(f"[DEBUG] JSON parse error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")

    symptoms = body.get("symptoms", [])
    if not symptoms:
        raise HTTPException(status_code=400, detail="At least one symptom is required.")

    # Convert symptoms list to binary feature vector
    input_vector = np.zeros(len(FEATURES), dtype=np.float32)
    matched_any = False

    for s in symptoms:
        normalized = s.strip().lower().replace(" ", "_")
        if normalized in FEATURE_INDEX:
            input_vector[FEATURE_INDEX[normalized]] = 1.0
            matched_any = True

    if not matched_any:
        raise HTTPException(status_code=400, detail="None of the provided symptoms matched the feature vocabulary.")

    # Predict probabilities
    input_arr = input_vector.reshape(1, -1)
    
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(input_arr)[0]
    else:
        # Fallback if predict_proba is not direct
        preds = model.predict(input_arr)
        top_name = label_encoder.inverse_transform(preds)[0] if label_encoder else str(preds[0])
        return PredictResponse(
            top_disease=top_name,
            confidence=100.0,
            predictions=[DiseaseProbability(disease=top_name, confidence=100.0)]
        )

    # Get top 3 predicted classes
    top_indices = np.argsort(probs)[::-1][:3]
    predictions = []
    
    for idx in top_indices:
        conf = float(probs[idx]) * 100.0
        disease_name = label_encoder.inverse_transform([idx])[0] if label_encoder else f"Class_{idx}"
        predictions.append(DiseaseProbability(disease=disease_name, confidence=round(conf, 2)))

    return PredictResponse(
        top_disease=predictions[0].disease,
        confidence=predictions[0].confidence,
        predictions=predictions
    )


if __name__ == "__main__":
    uvicorn.run("ml_service:app", host="127.0.0.1", port=5001, reload=False)
