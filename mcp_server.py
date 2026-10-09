"""
Medi AI — FastMCP Server
Exposes disease prediction, remedy lookup, and symptom extraction as MCP tools.
Run: python mcp_server.py
"""
from fastmcp import FastMCP
from app import detect_symptoms, predict_diseases, fetch_medlineplus_remedy, extract_symptoms_with_llm

mcp = FastMCP(
    name="Medi AI MCP Server",
    instructions=(
        "You are a medical AI assistant. Use these tools to predict diseases from symptoms, "
        "fetch verified home remedies, and extract symptoms from natural language text."
    )
)


@mcp.tool()
def predict_disease(symptoms: list[str]) -> dict:
    """
    Predict the top 3 most likely diseases given a list of symptoms.

    Args:
        symptoms: List of canonical symptom names e.g. ['fever', 'cough', 'headache']

    Returns:
        Dictionary with top 3 disease predictions and confidence percentages.
    """
    predictions, err = predict_diseases(symptoms)
    if err or not predictions:
        return {"error": err or "No predictions available. Check that symptoms are valid."}
    return {"predictions": predictions}


@mcp.tool()
def get_remedy(disease: str) -> str:
    """
    Fetch verified home care tips and remedies for a given disease.
    Checks in-memory cache first, then queries MedlinePlus NLM API,
    then falls back to local knowledge base.

    Args:
        disease: Disease name e.g. 'Dengue', 'Common Cold', 'Malaria'

    Returns:
        A short string with safe home remedy tips from MedlinePlus or local data.
    """
    remedy = fetch_medlineplus_remedy(disease)
    return remedy or "Please consult a qualified doctor or healthcare professional for advice on this condition."


@mcp.tool()
def extract_symptoms(text: str) -> list[str]:
    """
    Extract known medical symptoms from free-form natural language text.
    Uses exact matching, synonym mapping, fuzzy typo correction, and Gemini LLM as fallback.

    Args:
        text: Free-form user text e.g. 'I have a bad headche and I feel tired with high fevr'

    Returns:
        Sorted list of canonical symptom names detected in the text.
    """
    found = detect_symptoms(text)
    if not found and len(text.split()) > 3:
        found = extract_symptoms_with_llm(text)
    return sorted(list(found))


if __name__ == "__main__":
    mcp.run()
