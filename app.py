import os
import re
import pickle
import logging
import sys

from flask import Flask, request, jsonify, render_template

sys.path.insert(0, os.path.dirname(__file__))
from utils.company_check import verify_company
from utils.url_check import check_url
from utils.scraping_agent import run_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model', 'pipeline.pkl')
pipeline = None


def load_model():
    global pipeline
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            pipeline = pickle.load(f)
        logger.info("ML model loaded successfully")
    else:
        logger.warning("model/pipeline.pkl not found — falling back to keyword scoring")


load_model()


# ─── Keyword Lists for Text Signal Detection ─────────────────────────────────
# Used for the "Text Signals" display in the UI
FRAUD_KEYWORDS = [
    'registration fee', 'pay now', 'security deposit', 'transfer money',
    'pay registration', 'send money', 'no interview', 'no interview required',
    '100% placement', 'pay rs', 'pay inr', 'pay rupees', 'send rs',
    'guaranteed certificate', 'refundable deposit', 'limited seats',
    'offer expires', 'joining fee', 'admin fee', 'processing fee',
    'unlock your offer', 'confirm your seat', 'daily payment',
    'earn from home', 'work from home guaranteed', 'instant offer letter',
]

LEGIT_SIGNALS = [
    'apply at', 'visit our', 'careers page', 'deadline', 'resume required',
    'interview process', 'technical round', 'hr round', 'merit-based',
    'screening process', 'official portal', 'no registration fee',
    'shortlisting', 'assessment', 'aptitude test', 'coding round',
]


# ─── Tiered Fraud Keywords for ML Scoring ─────────────────────────────────────
# Critical: direct monetary demands — strongest fraud indicators
CRITICAL_FRAUD_KW = [
    'registration fee', 'security deposit', 'pay registration',
    'joining fee', 'processing fee', 'pay now', 'transfer money',
    'send money', 'admin fee', 'pay rs', 'pay inr', 'pay rupees', 'send rs',
]

# High: process red flags — strong fraud indicators
HIGH_FRAUD_KW = [
    'no interview required', 'no interview', '100% placement',
    'instant offer letter', 'refundable deposit',
    'earn from home', 'work from home guaranteed',
]

# Medium: pressure tactics and suspicious promises
MEDIUM_FRAUD_KW = [
    'guaranteed certificate', 'limited seats', 'offer expires',
    'daily payment', 'unlock your offer', 'confirm your seat',
]


# ─── Negation-Aware Keyword Detection ─────────────────────────────────────────
NEGATION_PREFIXES = [
    'no ', 'not ', 'without ', 'zero ', 'nil ', "don't ",
    "doesn't ", "never ", "free from ", "exempt from ",
]


def keyword_present(text_lower, keyword):
    """
    Check if keyword is meaningfully present in text.
    Handles negation context: 'no registration fee' won't trigger 'registration fee'.
    Keywords that inherently contain negation (like 'no interview') are matched literally.
    """
    # Keywords that start with negation words → match literally, no negation check
    if keyword.startswith(('no ', 'not ')):
        return keyword in text_lower
    # For payment/demand keywords, check they aren't negated
    idx = text_lower.find(keyword)
    while idx != -1:
        start = max(0, idx - 25)
        prefix = text_lower[start:idx]
        if not any(neg in prefix for neg in NEGATION_PREFIXES):
            return True  # Found without negation
        idx = text_lower.find(keyword, idx + len(keyword))
    return False  # Not found, or all occurrences negated


def extract_text_signals(text):
    lower = text.lower()
    return {
        'fraud_keywords': [kw for kw in FRAUD_KEYWORDS if keyword_present(lower, kw)],
        'legit_signals': [s for s in LEGIT_SIGNALS if s in lower],
    }


def ml_predict(text):
    """
    Predict fraud probability using ML model or keyword-based fallback.

    Keyword fallback uses tiered scoring with negation awareness:
      - Critical (payment demands): strongest signal
      - High (process red flags): strong signal
      - Medium (pressure tactics): moderate signal
    Legitimate signals reduce the score with diminishing effect.
    """
    if pipeline:
        prob = float(pipeline.predict_proba([text])[0][1])
        return prob, 'ml_pipeline'

    lower = text.lower()

    # Count fraud keywords per tier (negation-aware)
    critical = sum(1 for kw in CRITICAL_FRAUD_KW if keyword_present(lower, kw))
    high = sum(1 for kw in HIGH_FRAUD_KW if keyword_present(lower, kw))
    medium = sum(1 for kw in MEDIUM_FRAUD_KW if keyword_present(lower, kw))

    # ── Tiered scoring with diminishing returns ───────────────────
    score = 0.0

    # Critical keywords (payment demands) — strongest signal
    if critical >= 3:   score += 0.90
    elif critical >= 2: score += 0.75
    elif critical >= 1: score += 0.50

    # High-risk keywords (process red flags)
    if high >= 2:   score += 0.30
    elif high >= 1: score += 0.20

    # Medium keywords (pressure tactics)
    if medium >= 3:   score += 0.20
    elif medium >= 2: score += 0.12
    elif medium >= 1: score += 0.06

    # ── Legitimate signals reduce fraud score ─────────────────────
    legit_count = sum(1 for s in LEGIT_SIGNALS if s in lower)
    if critical == 0:
        # No critical fraud → legit signals have full effect
        if legit_count >= 3:   score *= 0.40
        elif legit_count >= 2: score *= 0.60
        elif legit_count >= 1: score *= 0.80
    else:
        # Critical fraud keywords present — legit signals have diminished effect
        # (a scam can still mention "interview process" to seem legit)
        if legit_count >= 3: score *= 0.80
        elif legit_count >= 1: score *= 0.90

    prob = min(0.95, max(0.0, score))
    return prob, 'keyword_fallback'


def extract_company_from_text(text):
    patterns = [
        r'(?:at|with|for|by|from)\s+([A-Z][a-zA-Z\s&]{2,30})(?:\s+is|\s+are|\s+offers?|\s+internship|\.|,)',
        r'internship\s+(?:at|with|for)\s+([A-Z][a-zA-Z\s&]{2,30})',
        r'([A-Z][a-zA-Z\s&]{2,25})\s+(?:is hiring|announces|is offering|is recruiting)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return ''


def extract_url_from_text(text):
    m = re.search(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+', text)
    return m.group(0) if m else ''


def fuse_scores(ml_fraud_prob, company_score, url_score, agent_score, has_url=True):
    """
    Score fusion where web scraping agent is the PRIMARY signal.

    Legitimacy scores (company_score, url_score, agent_score) → higher = more legit
    Fraud score (ml_fraud_prob) → higher = more fraudulent

    Convert everything to fraud probability, then combine:
      agent_fraud   = 1 - agent_score
      company_fraud = 1 - company_score
      url_fraud     = 1 - url_score
    """

    agent_fraud   = 1.0 - agent_score
    company_fraud = 1.0 - company_score
    url_fraud     = 1.0 - url_score

    # ── Override rules ──────────────────────────────────────────────
    # 1a. Confirmed homoglyph impersonation (score ≤ 0.05):
    #     This is intentional visual deception — force maximum fraud signal.
    #     Even if Wikipedia somehow finds something, the name trick is undeniable.
    if company_score <= 0.05:
        ml_fraud_prob = max(ml_fraud_prob, 0.85)
        agent_score   = min(agent_score, 0.10)
        agent_fraud   = 1.0 - agent_score

    # 1b. General impersonation / misspelled company (score ≤ 0.10):
    elif company_score <= 0.10:
        ml_fraud_prob = max(ml_fraud_prob, 0.75)
        agent_score   = min(agent_score, 0.25)
        agent_fraud   = 1.0 - agent_score

    # 2. Scammer using REAL company name but demanding fees:
    #    Web agent may have confirmed "Google is real" — but we override because
    #    a real company NEVER asks students to pay any fee.
    if ml_fraud_prob >= 0.75:
        agent_fraud   = max(agent_fraud, 0.70)
        company_fraud = max(company_fraud, 0.70)

    # ── Weighted fusion — WEB AGENT IS PRIMARY DRIVER ──────────────
    if has_url:
        combined = (
            0.50 * agent_fraud    +   # web scraping = primary signal
            0.20 * company_fraud  +   # company name check
            0.15 * url_fraud      +   # URL safety
            0.15 * ml_fraud_prob      # keyword text analysis
        )
    else:
        # No URL provided: redistribute URL weight to agent & company
        combined = (
            0.55 * agent_fraud    +
            0.25 * company_fraud  +
            0.20 * ml_fraud_prob
        )

    combined = round(min(1.0, max(0.0, combined)), 4)
    is_fraud  = combined >= 0.5
    confidence = round(combined * 100 if is_fraud else (1.0 - combined) * 100, 1)

    return {
        'verdict': 'FRAUD' if is_fraud else 'LEGITIMATE',
        'combined_fraud_probability': combined,
        'confidence_percent': confidence,
        'is_fraud': is_fraud,
        'component_scores': {
            'ml_fraud_probability': round(ml_fraud_prob, 4),
            'agent_legitimacy':     round(agent_score,   4),
            'company_legitimacy':   round(company_score, 4),
            'url_safety':           round(url_score,     4),
        }
    }


def build_explanations(fusion, company_result, url_result, text_signals, agent_result):
    explanations = []
    ml_pct = round(fusion['component_scores']['ml_fraud_probability'] * 100, 1)

    if ml_pct >= 70:
        explanations.append(f'ML model flagged this text as {ml_pct}% likely fraudulent based on language patterns.')
    elif ml_pct <= 30:
        explanations.append(f'ML model found language consistent with legitimate offers ({ml_pct}% fraud probability).')
    else:
        explanations.append(f'ML model is uncertain — text has mixed signals ({ml_pct}% fraud probability).')

    # Highlight impersonation detection prominently
    if company_result['status'] == 'impersonation':
        explanations.append(f'IMPERSONATION DETECTED — {company_result["reason"]}')
    else:
        explanations.append(f'Company check: {company_result["reason"]}')

    explanations.append(f'URL check: {url_result["reason"]}')

    if agent_result:
        explanations.append(f'Web agent: {agent_result["summary"]}')

    if text_signals['fraud_keywords']:
        kws = ', '.join(f'"{k}"' for k in text_signals['fraud_keywords'][:4])
        explanations.append(f'Suspicious payment-related phrases found: {kws}.')

    if text_signals['legit_signals']:
        sigs = ', '.join(f'"{s}"' for s in text_signals['legit_signals'][:3])
        explanations.append(f'Legitimate process signals found: {sigs}.')

    return explanations


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    offer_text = data.get('offer_text', '').strip()
    company_name = data.get('company_name', '').strip()
    url = data.get('url', '').strip()
    skip_scraping = data.get('skip_scraping', False)

    if not offer_text:
        return jsonify({'error': 'offer_text is required'}), 400

    if not company_name:
        company_name = extract_company_from_text(offer_text)
    if not url:
        url = extract_url_from_text(offer_text)

    ml_fraud_prob, model_used = ml_predict(offer_text)
    text_signals = extract_text_signals(offer_text)
    company_result = verify_company(company_name)
    has_url = bool(url)
    url_result = check_url(url) if has_url else {
        'status': 'unknown', 'score': 0.5, 'reason': 'No URL provided to check.'
    }

    if not skip_scraping:
        agent_result = run_agent(company_name, offer_text, url)
    else:
        agent_result = {
            'score': 0.5, 'findings': [], 'agent_log': [],
            'summary': 'Web verification skipped.', 'stats': {}
        }

    fusion = fuse_scores(
        ml_fraud_prob,
        company_result['score'],
        url_result['score'],
        agent_result['score'],
        has_url=has_url
    )

    explanations = build_explanations(fusion, company_result, url_result, text_signals, agent_result)

    return jsonify({
        'verdict': fusion['verdict'],
        'is_fraud': fusion['is_fraud'],
        'confidence_percent': fusion['confidence_percent'],
        'combined_fraud_probability': fusion['combined_fraud_probability'],
        'component_scores': fusion['component_scores'],
        'company': {
            'name': company_name or 'Not detected',
            'status': company_result['status'],
            'score': company_result['score'],
            'reason': company_result['reason'],
        },
        'url': {
            'value': url or 'Not found',
            'status': url_result['status'],
            'score': url_result['score'],
            'reason': url_result['reason'],
        },
        'agent': {
            'score': agent_result['score'],
            'findings': agent_result['findings'],
            'agent_log': agent_result['agent_log'],
            'summary': agent_result['summary'],
            'stats': agent_result.get('stats', {}),
        },
        'text_signals': text_signals,
        'explanations': explanations,
        'model_used': model_used,
    })


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model_loaded': pipeline is not None})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
