import re
import urllib.parse
from datetime import datetime

import requests

TIMEOUT = 6

# List of phrases that a real entity would NEVER include in a legitimate offer
SCAM_CONTRADICTION_PHRASES = [
    r'\bregistration fee\b', 
    r'\bsecurity deposit\b', 
    r'\bprocessing fee\b', 
    r'\bsend money\b', 
    r'\bpayment required\b',
    r'\bpay now\b'
]

def contains_scam_phrase(text, phrases):
    """Checks if any scam phrase exists with word boundaries and no negation."""
    text = text.lower()
    for pattern in phrases:
        # Check if pattern exists in text
        if re.search(pattern, text):
            # Check for negation (e.g., "no registration fee")
            # We look for "no", "not", "without", "never" within 3 words before the match
            match = re.search(pattern, text)
            start = match.start()
            prefix = text[max(0, start-30):start]
            if any(neg in prefix for neg in ['no ', 'not ', 'without ', 'never ']):
                continue
            return True, re.findall(pattern, text)[0]
    return False, None

# Keywords that appear in legitimate Wikipedia company articles
WIKI_LEGIT_SIGNALS = [
    'founded', 'headquartered', 'employees', 'revenue', 'listed', 'nasdaq',
    'bse', 'nse', 'fortune', 'inc.', 'ltd', 'corporation', 'company',
    'subsidiary', 'acquired', 'merger', 'products', 'services', 'stock',
]

class AgentLog:
    def __init__(self):
        self.entries = []

    def add(self, message, level='info'):
        ts = datetime.now().strftime('%H:%M:%S')
        self.entries.append({'time': ts, 'message': message, 'level': level})

    def to_list(self):
        return self.entries

def url_is_alive(url):
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        r = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        try:
            r = requests.get(url, timeout=TIMEOUT)
            return r.status_code < 400
        except Exception:
            return False

def check_wikipedia_presence(company_name, offer_text, log):
    """Search Wikipedia for the company, then cross-check snippet against the offer text."""
    log.add(f'Querying global knowledge base for "{company_name}"')

    if not company_name or len(company_name.strip()) < 2:
        return {'found': False, 'score': 0.45, 'detail': 'No company name to verify.'}

    endpoint = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": company_name.strip(),
        "srlimit": 5,
        "utf8": "",
        "format": "json"
    }

    try:
        resp = requests.get(endpoint, params=params, timeout=TIMEOUT, headers={'User-Agent': 'VeriInternBot/1.0'})
        if resp.status_code != 200:
            log.add('Knowledge base returned non-200 response', 'warn')
            return {'found': False, 'score': 0.50, 'detail': 'Web verification currently unavailable.'}

        results = resp.json().get("query", {}).get("search", [])

        if not results:
            log.add(f'"{company_name}" has no public online presence — likely fabricated', 'warn')
            return {
                'found': False,
                'score': 0.25,  # Penalize — unknown companies are suspicious
                'detail': f'No public information found for "{company_name}". May not be a real company.'
            }

        offer_lower = offer_text.lower()
        company_lower = company_name.lower()

        for r in results[:5]:
            title = r.get('title', '').lower()
            snippet = re.sub(r'<[^>]+>', '', r.get('snippet', '')).lower()  # strip HTML tags

            # STRICT MATCHING: The entity must be an exact match to be "found"
            is_exact_match = (company_lower == title)
            
            if not is_exact_match:
                if company_lower in title or title in company_lower:
                    log.add(f'Impersonation Risk: "{company_name}" closely resembles real entity "{r["title"]}"', 'danger')
                continue

            # Check if this Wikipedia entry is actually an organization/company
            legit_signals_in_wiki = sum(1 for kw in WIKI_LEGIT_SIGNALS if kw in snippet)
            is_likely_org = (legit_signals_in_wiki >= 2)
            
            # Check for scam behavior using the new strict matching logic
            is_scam, detected_phrase = contains_scam_phrase(offer_lower, SCAM_CONTRADICTION_PHRASES)

            if is_scam:
                # If they claim to be a real org but ask for money, it's 100% fraud
                msg = f'SCAM DETECTED: Real entities NEVER ask for {detected_phrase}.'
                log.add(msg, 'danger')
                return {
                    'found': True,
                    'score': 0.01,  # Near-zero trust when payment is demanded
                    'detail': f'This offer uses the name of a real entity ("{r["title"]}") but demands payment ("{detected_phrase}"). Real companies do not charge fees.'
                }

            if is_likely_org:
                log.add(f'Verified: "{r["title"]}" is a documented global organization', 'success')
                return {
                    'found': True,
                    'score': 0.95,
                    'detail': f'"{r["title"]}" is a verified, established organization with global records.'
                }
            else:
                log.add(f'Entity "{r["title"]}" found, but it does not appear to be a company/employer', 'warn')
                return {
                    'found': True,
                    'score': 0.40,
                    'detail': f'"{r["title"]}" exists as a public entity, but we found no records of them being an internship provider or company.'
                }

        # If no result was an EXACT match
        log.add(f'Verification Failed: "{company_name}" is not a recognized company', 'warn')
        return {
            'found': False,
            'score': 0.20,
            'detail': f'No company records found for "{company_name}". This entity appears to be fabricated or illegitimate.'
        }

    except Exception as e:
        log.add(f'Knowledge base query failed: {str(e)}', 'warn')

    return {'found': False, 'score': 0.50, 'detail': 'Web verification currently unavailable.'}


def verify_offer_url(url, company_name, log):
    """Check if the offer URL is reachable and plausibly linked to the company."""
    if not url:
        return None

    log.add(f'Verifying live state of domain: {url}')
    alive = url_is_alive(url)

    if not alive:
        log.add('URL is completely unreachable', 'danger')
        return {
            'reachable': False,
            'domain_match': False,
            'score': 0.05,
            'detail': 'The provided URL is broken or inactive.'
        }

    log.add('Domain is live and responsive', 'success')

    try:
        domain = urllib.parse.urlparse(url if url.startswith('http') else 'https://' + url).netloc.lower()
        name_parts = [w for w in re.split(r'\W+', company_name.lower()) if len(w) > 2]
        domain_match = any(part in domain for part in name_parts)
    except Exception:
        domain_match = False

    if domain_match:
        log.add('URL domain structure correlates with company name', 'success')
        return {
            'reachable': True,
            'domain_match': True,
            'score': 0.85,
            'detail': 'Live domain strictly matches the company identity.'
        }

    log.add('Domain live but does not directly correspond to company name', 'warn')
    return {
        'reachable': True,
        'domain_match': False,
        'score': 0.40,
        'detail': 'URL works but the domain name is unrelated to the company name.'
    }

def run_agent(company_name, offer_text='', url=''):
    """
    Web verification agent: Wikipedia lookup + URL liveness + contradictions check.
    Returns a legitimacy score from 0.0 (definite fraud) to 1.0 (definitely legitimate).
    """
    log = AgentLog()
    log.add('Initializing web verification agent')

    if not company_name or not company_name.strip():
        log.add('No company name provided — skipping web checks', 'warn')
        return {
            'score': 0.45,
            'findings': [],
            'agent_log': log.to_list(),
            'summary': 'No company name — web verification skipped.',
            'stats': {'positive': 0, 'negative': 0, 'neutral': 1}
        }

    findings = []
    scores = []   # list of (score, weight)

    # ── Step 1: Wikipedia presence + contradiction check (highest weight)
    wiki = check_wikipedia_presence(company_name, offer_text, log)
    is_wiki_positive = wiki['found'] and wiki['score'] >= 0.85
    is_wiki_negative = wiki['score'] <= 0.30
    findings.append({
        'label': 'Public Entity Footprint',
        'detail': wiki['detail'],
        'positive': is_wiki_positive,
        'neutral': not is_wiki_positive and not is_wiki_negative,
    })
    scores.append((wiki['score'], 4.0))   # 4x weight — most important signal

    # ── Step 2: URL liveness + domain correlation
    if url:
        offer_url_result = verify_offer_url(url, company_name, log)
        if offer_url_result:
            url_positive = offer_url_result['reachable'] and offer_url_result['domain_match']
            url_neutral  = offer_url_result['reachable'] and not offer_url_result['domain_match']
            findings.append({
                'label': 'Domain Correlation',
                'detail': offer_url_result['detail'],
                'positive': url_positive,
                'neutral': url_neutral,
            })
            scores.append((offer_url_result['score'], 2.5))  # 2.5x weight
    else:
        log.add('No URL provided — URL verification skipped', 'info')

    # ── Compute weighted final score
    total_weight = sum(w for _, w in scores)
    if total_weight > 0:
        weighted_score = sum(s * w for s, w in scores) / total_weight
    else:
        weighted_score = 0.45

    final_score = round(min(1.0, max(0.0, weighted_score)), 4)

    positive = sum(1 for f in findings if f.get('positive') is True)
    neutral  = sum(1 for f in findings if not f.get('positive') and f.get('neutral'))
    negative = sum(1 for f in findings if not f.get('positive') and not f.get('neutral'))

    log.add(f'Agent completed — legitimacy score: {final_score:.2f}')

    if final_score <= 0.35:
        summary = 'Web verification raised serious concerns. High fraud risk detected.'
    elif final_score >= 0.80:
        summary = 'Web verification confirmed legitimate company presence online.'
    else:
        summary = 'Web verification returned mixed signals. Other factors also considered.'

    return {
        'score': final_score,
        'findings': findings,
        'agent_log': log.to_list(),
        'summary': summary,
        'stats': {'positive': positive, 'negative': negative, 'neutral': neutral}
    }
