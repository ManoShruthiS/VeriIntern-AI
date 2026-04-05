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


def extract_text_signals(text):
    lower = text.lower()
    return {
        'fraud_keywords': [kw for kw in FRAUD_KEYWORDS if kw in lower],
        'legit_signals': [s for s in LEGIT_SIGNALS if s in lower],
    }


def ml_predict(text):
    if pipeline:
        prob = float(pipeline.predict_proba([text])[0][1])
        return prob, 'ml_pipeline'

    lower = text.lower()
    hits = sum(1 for kw in FRAUD_KEYWORDS if kw in lower)
    prob = min(0.95, hits * 0.15)
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


def fuse_scores(ml_fraud_prob, company_score, url_score, agent_score):
    """
    Weights:
      ML text model   40%
      Web scraping    30%
      Company DB      15%
      URL check       15%
    """
    combined = (
        0.40 * ml_fraud_prob +
        0.30 * (1.0 - agent_score) +
        0.15 * (1.0 - company_score) +
        0.15 * (1.0 - url_score)
    )

    is_fraud = combined >= 0.5
    confidence = round(combined * 100 if is_fraud else (1.0 - combined) * 100, 1)

    return {
        'verdict': 'FRAUD' if is_fraud else 'LEGITIMATE',
        'combined_fraud_probability': round(combined, 4),
        'confidence_percent': confidence,
        'is_fraud': is_fraud,
        'component_scores': {
            'ml_fraud_probability': round(ml_fraud_prob, 4),
            'agent_legitimacy': round(agent_score, 4),
            'company_legitimacy': round(company_score, 4),
            'url_safety': round(url_score, 4),
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
    url_result = check_url(url) if url else {
        'status': 'unknown', 'score': 0.5, 'reason': 'No URL found in the offer text.'
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
        agent_result['score']
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
