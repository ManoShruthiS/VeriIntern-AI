import os
import re
import pickle
from flask import Flask, request, jsonify, render_template

# Import our custom utilities
import sys
sys.path.insert(0, os.path.dirname(__file__))
from utils.company_check import verify_company
from utils.url_check import check_url

app = Flask(__name__)

# ─── Load ML Model ─────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model", "pipeline.pkl")
pipeline = None

def load_model():
    global pipeline
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            pipeline = pickle.load(f)
        print("✅ ML Model loaded successfully.")
    else:
        print("⚠️  Model not found. Run model/train_model.py first.")

load_model()

# ─── Fraud keyword signals ─────────────────────────────────────────────────────
FRAUD_KEYWORDS = [
    "registration fee", "pay now", "security deposit", "transfer money",
    "no interview", "no experience required", "instant offer", "100% placement",
    "pay ₹", "send ₹", "guaranteed certificate", "refundable deposit",
    "limited seats", "offer expires", "work from home guaranteed", "daily payment",
    "joining fee", "admin fee", "processing fee", "unlock your offer",
]

LEGIT_SIGNALS = [
    "apply at", "visit our", "careers page", "deadline:", "resume required",
    "interview process", "technical round", "hr discussion", "merit-based",
    "screening process", "official portal", "no registration fee",
]

def extract_text_signals(text: str) -> dict:
    text_lower = text.lower()
    found_fraud = [kw for kw in FRAUD_KEYWORDS if kw in text_lower]
    found_legit = [kw for kw in LEGIT_SIGNALS if kw in text_lower]
    return {"fraud_keywords": found_fraud, "legit_signals": found_legit}

def extract_company_from_text(text: str) -> str:
    """Try to extract company name from offer text using simple heuristics."""
    patterns = [
        r"(?:at|with|for|by|from)\s+([A-Z][a-zA-Z\s&]{2,30})(?:\s+is|\s+are|\s+offers?|\s+internship|\.|,)",
        r"internship\s+(?:at|with|for)\s+([A-Z][a-zA-Z\s&]{2,30})",
        r"([A-Z][a-zA-Z\s&]{2,25})\s+(?:is hiring|announces|is offering|is recruiting)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""

def extract_url_from_text(text: str) -> str:
    """Extract first URL from text."""
    pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
    match = re.search(pattern, text)
    return match.group(0) if match else ""

# ─── Score Fusion ──────────────────────────────────────────────────────────────
def fuse_scores(ml_fraud_prob: float, company_score: float, url_score: float) -> dict:
    """
    Weights:
      ML Model     → 50%
      Company Check → 25%
      URL Check    → 25%

    All scores are in [0,1] where:
      ml_fraud_prob : probability of being FRAUD (higher = more fraudulent)
      company_score : legitimacy score (higher = more legitimate)
      url_score     : safety score (higher = safer)

    We convert company and url scores to "fraud probability" equivalents.
    """
    company_fraud_prob = 1.0 - company_score
    url_fraud_prob = 1.0 - url_score

    combined_fraud_prob = (
        0.50 * ml_fraud_prob +
        0.25 * company_fraud_prob +
        0.25 * url_fraud_prob
    )

    is_fraud = combined_fraud_prob >= 0.5
    confidence = round(combined_fraud_prob * 100 if is_fraud else (1 - combined_fraud_prob) * 100, 1)

    return {
        "verdict": "FRAUD" if is_fraud else "LEGITIMATE",
        "combined_fraud_probability": round(combined_fraud_prob, 4),
        "confidence_percent": confidence,
        "component_scores": {
            "ml_fraud_probability": round(ml_fraud_prob, 4),
            "company_legitimacy": round(company_score, 4),
            "url_safety": round(url_score, 4),
        }
    }

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    offer_text = data.get("offer_text", "").strip()
    company_name = data.get("company_name", "").strip()
    url = data.get("url", "").strip()

    if not offer_text:
        return jsonify({"error": "Offer text is required"}), 400

    # ── Auto-extract company & URL if not provided ──────────────────────────
    if not company_name:
        company_name = extract_company_from_text(offer_text)
    if not url:
        url = extract_url_from_text(offer_text)

    # ── 1. ML Analysis ───────────────────────────────────────────────────────
    if pipeline:
        ml_fraud_prob = float(pipeline.predict_proba([offer_text])[0][1])
    else:
        # Fallback: keyword scoring
        text_lower = offer_text.lower()
        fraud_hits = sum(1 for kw in FRAUD_KEYWORDS if kw in text_lower)
        ml_fraud_prob = min(0.95, fraud_hits * 0.15)

    # ── 2. Text Signal Extraction ────────────────────────────────────────────
    text_signals = extract_text_signals(offer_text)

    # ── 3. Company Verification ──────────────────────────────────────────────
    company_result = verify_company(company_name)

    # ── 4. URL Safety Check ──────────────────────────────────────────────────
    url_result = check_url(url) if url else {"status": "unknown", "score": 0.5, "reason": "No URL found in the offer."}

    # ── 5. Score Fusion ──────────────────────────────────────────────────────
    fusion = fuse_scores(ml_fraud_prob, company_result["score"], url_result["score"])

    # ── 6. Build Explanation ─────────────────────────────────────────────────
    explanations = []
    if text_signals["fraud_keywords"]:
        explanations.append(f"⚠️ Suspicious phrases detected: {', '.join(f'\"{k}\"' for k in text_signals['fraud_keywords'][:4])}")
    if text_signals["legit_signals"]:
        explanations.append(f"✅ Legitimate signals found: {', '.join(f'\"{k}\"' for k in text_signals['legit_signals'][:3])}")
    explanations.append(f"🏢 Company: {company_result['reason']}")
    explanations.append(f"🌐 URL: {url_result['reason']}")

    return jsonify({
        "verdict": fusion["verdict"],
        "confidence_percent": fusion["confidence_percent"],
        "combined_fraud_probability": fusion["combined_fraud_probability"],
        "component_scores": fusion["component_scores"],
        "company": {
            "name": company_name or "Not detected",
            "status": company_result["status"],
            "score": company_result["score"],
            "reason": company_result["reason"]
        },
        "url": {
            "value": url or "Not found",
            "status": url_result["status"],
            "score": url_result["score"],
            "reason": url_result["reason"]
        },
        "text_signals": text_signals,
        "explanations": explanations,
        "model_used": "ML Pipeline" if pipeline else "Keyword Fallback"
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": pipeline is not None})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
