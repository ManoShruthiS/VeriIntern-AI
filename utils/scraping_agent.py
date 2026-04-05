import re
import time
import logging
import urllib.parse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 8
DELAY = 0.6  # polite delay between requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
}

# trusted platforms where legit internships are posted
TRUSTED_JOB_BOARDS = {
    'internshala.com', 'linkedin.com', 'naukri.com', 'glassdoor.com',
    'indeed.com', 'unstop.com', 'foundit.in', 'shine.com', 'ambitionbox.com',
    'monster.com', 'iimjobs.com', 'letsintern.com', 'hirist.com',
}

# sites that commonly report scams
SCAM_REPORT_SITES = {
    'reddit.com', 'quora.com', 'scamadviser.com',
    'consumer.ftc.gov', 'complaintsboard.com', 'mouthshut.com',
}


class AgentLog:
    def __init__(self):
        self.entries = []

    def add(self, message, level='info'):
        ts = datetime.now().strftime('%H:%M:%S')
        self.entries.append({'time': ts, 'message': message, 'level': level})
        logger.debug(f"[agent][{ts}] {message}")

    def to_list(self):
        return self.entries


def ddg_search(query, max_results=8):
    """
    Scrapes DuckDuckGo HTML endpoint. No API key, completely free.
    Works well for programmatic use unlike Google which blocks immediately.
    """
    endpoint = 'https://html.duckduckgo.com/html/'
    try:
        resp = requests.get(
            endpoint,
            params={'q': query, 'kl': 'in-en'},
            headers=HEADERS,
            timeout=TIMEOUT
        )
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []

        for item in soup.select('.result__body')[:max_results]:
            title_tag = item.select_one('.result__a')
            snippet_tag = item.select_one('.result__snippet')
            url_tag = item.select_one('.result__url')

            if not title_tag:
                continue

            results.append({
                'title': title_tag.get_text(strip=True),
                'url': url_tag.get_text(strip=True) if url_tag else '',
                'snippet': snippet_tag.get_text(strip=True) if snippet_tag else '',
            })

        return results

    except requests.exceptions.Timeout:
        logger.warning("DuckDuckGo search timed out")
        return []
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {e}")
        return []


def get_domain(raw_url):
    url = raw_url.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        return urllib.parse.urlparse(url).netloc.lower().lstrip('www.')
    except Exception:
        return ''


def url_is_alive(url):
    if not url.startswith('http'):
        url = 'https://' + url
    try:
        r = requests.head(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        # try GET as fallback, some servers reject HEAD
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            return r.status_code < 400
        except Exception:
            return False


def check_general_web_presence(company_name, log):
    """Search web for company, see if it shows up on job boards or credible sites."""
    log.add(f'Searching web: "{company_name} company India internship"')
    time.sleep(DELAY)

    results = ddg_search(f'{company_name} company India internship')
    if not results:
        log.add('No search results returned', 'warn')
        return {
            'found': False,
            'job_board_hits': [],
            'result_count': 0,
            'score': 0.05,
            'detail': 'No web presence found for this company.'
        }

    log.add(f'Got {len(results)} results from web search')
    job_board_hits = []

    for r in results:
        domain = get_domain(r['url'])
        for board in TRUSTED_JOB_BOARDS:
            if board in domain and board not in job_board_hits:
                job_board_hits.append(board)

    if job_board_hits:
        log.add(f'Found on trusted platforms: {", ".join(job_board_hits)}', 'success')
        return {
            'found': True,
            'job_board_hits': job_board_hits,
            'result_count': len(results),
            'score': 0.9,
            'detail': f'Company found on: {", ".join(job_board_hits)}'
        }

    # has web presence but not on job boards — ambiguous
    log.add('Has general web presence but not on known job boards', 'warn')
    return {
        'found': True,
        'job_board_hits': [],
        'result_count': len(results),
        'score': 0.35,
        'detail': f'{len(results)} web results found, but none from recognized job platforms.'
    }


def check_linkedin_presence(company_name, log):
    """
    LinkedIn blocks direct scraping aggressively.
    Workaround: search DDG for site:linkedin.com/company/<name>
    This uses LinkedIn's already-indexed pages through DDG.
    """
    log.add(f'Verifying LinkedIn presence via indexed search')
    time.sleep(DELAY)

    results = ddg_search(f'site:linkedin.com/company "{company_name}"', max_results=4)
    linkedin_hits = [r for r in results if 'linkedin.com' in get_domain(r['url'])]

    if linkedin_hits:
        page_url = linkedin_hits[0]['url']
        log.add(f'LinkedIn company page found: {page_url}', 'success')
        return {
            'found': True,
            'url': page_url,
            'score': 0.95,
            'detail': f'LinkedIn company page indexed and found.'
        }

    log.add('No LinkedIn company page found in search index', 'warn')
    return {
        'found': False,
        'url': None,
        'score': 0.08,
        'detail': 'No LinkedIn company page found. Legitimate companies typically have one.'
    }


def check_internshala(company_name, log):
    """Check Internshala specifically — biggest Indian internship platform."""
    log.add(f'Checking Internshala for "{company_name}"')
    time.sleep(DELAY)

    results = ddg_search(f'site:internshala.com "{company_name}"', max_results=4)
    hits = [r for r in results if 'internshala.com' in get_domain(r['url'])]

    if hits:
        log.add('Found on Internshala', 'success')
        return {
            'found': True,
            'score': 0.88,
            'detail': f'Company posts internships on Internshala.'
        }

    log.add('Not listed on Internshala')
    # not being on internshala isn't necessarily bad (large MNCs often aren't)
    return {
        'found': False,
        'score': 0.45,
        'detail': 'Not found on Internshala — neutral for large companies.'
    }


def check_scam_reports(company_name, log):
    """Search for any existing fraud/scam reports about this company."""
    log.add(f'Scanning for fraud reports: "{company_name} scam fake fraud"')
    time.sleep(DELAY)

    results = ddg_search(f'"{company_name}" scam fake fraud internship complaint', max_results=6)
    reports = []

    for r in results:
        domain = get_domain(r['url'])
        for scam_site in SCAM_REPORT_SITES:
            if scam_site in domain:
                reports.append({'source': scam_site, 'title': r['title']})
                break

        # also catch titles that scream scam even from other sources
        title_lower = r['title'].lower()
        if any(word in title_lower for word in ['scam', 'fraud', 'fake', 'cheated', 'beware']):
            if r not in reports:
                reports.append({'source': get_domain(r['url']), 'title': r['title']})

    if reports:
        log.add(f'Scam/fraud reports found: {len(reports)} result(s)', 'danger')
        return {
            'found': True,
            'reports': reports,
            'score': 0.0,
            'detail': f'{len(reports)} scam report(s) found online for this company name.'
        }

    log.add('No scam reports found', 'success')
    return {
        'found': False,
        'reports': [],
        'score': 0.7,
        'detail': 'No scam or fraud reports found in web search results.'
    }


def verify_offer_url(url, company_name, log):
    """Check if the offer URL is reachable and plausibly linked to the company."""
    if not url:
        return None

    log.add(f'Verifying offer URL: {url}')
    alive = url_is_alive(url)

    if not alive:
        log.add('URL is unreachable', 'danger')
        return {
            'reachable': False,
            'domain_match': False,
            'score': 0.05,
            'detail': 'The URL in the offer is unreachable or returns an error.'
        }

    log.add('URL is reachable', 'success')

    # see if the company name appears somewhere in the domain
    try:
        domain = urllib.parse.urlparse(url if url.startswith('http') else 'https://' + url).netloc.lower()
        name_parts = [w for w in re.split(r'\W+', company_name.lower()) if len(w) > 2]
        domain_match = any(part in domain for part in name_parts)
    except Exception:
        domain_match = False

    if domain_match:
        log.add('URL domain aligns with company name', 'success')
        return {
            'reachable': True,
            'domain_match': True,
            'score': 0.85,
            'detail': 'URL is live and the domain matches the company name.'
        }

    log.add('URL live but domain does not match company name', 'warn')
    return {
        'reachable': True,
        'domain_match': False,
        'score': 0.35,
        'detail': 'URL is reachable but domain does not correspond to the company name.'
    }


def run_agent(company_name, offer_text='', url=''):
    """
    Orchestrates all checks. Returns everything the frontend needs.
    Weights are intentionally skewed toward LinkedIn + job board presence
    because those are the hardest signals for scammers to fake.
    """
    log = AgentLog()
    log.add('Agent initialized — beginning multi-source verification')

    if not company_name or not company_name.strip():
        log.add('No company name — skipping all web checks', 'warn')
        return {
            'score': 0.5,
            'findings': [],
            'agent_log': log.to_list(),
            'summary': 'No company name provided for web verification.',
            'stats': {'positive': 0, 'negative': 0, 'neutral': 0}
        }

    findings = []
    scores = []

    # run all checks
    web = check_general_web_presence(company_name, log)
    li = check_linkedin_presence(company_name, log)
    internshala = check_internshala(company_name, log)
    scam = check_scam_reports(company_name, log)
    offer_url_result = verify_offer_url(url, company_name, log) if url else None

    # general web presence
    findings.append({
        'label': 'Web Presence',
        'detail': web['detail'],
        'positive': web['found'] and len(web['job_board_hits']) > 0,
        'neutral': web['found'] and len(web['job_board_hits']) == 0,
    })
    scores.append((web['score'], 2.0))  # (score, weight)

    # linkedin — high weight, very strong signal
    findings.append({
        'label': 'LinkedIn Company Page',
        'detail': li['detail'],
        'positive': li['found'],
        'neutral': False,
    })
    scores.append((li['score'], 3.0))

    # internshala
    findings.append({
        'label': 'Internshala Listing',
        'detail': internshala['detail'],
        'positive': internshala['found'],
        'neutral': not internshala['found'],  # absence is neutral, not negative
    })
    scores.append((internshala['score'], 1.5))

    # scam reports — high weight in negative direction
    findings.append({
        'label': 'Fraud/Scam Reports',
        'detail': scam['detail'],
        'positive': not scam['found'],
        'neutral': False,
    })
    scores.append((scam['score'], 2.5))

    # offer URL
    if offer_url_result:
        findings.append({
            'label': 'Offer URL Verification',
            'detail': offer_url_result['detail'],
            'positive': offer_url_result['reachable'] and offer_url_result['domain_match'],
            'neutral': offer_url_result['reachable'] and not offer_url_result['domain_match'],
        })
        scores.append((offer_url_result['score'], 1.5))

    # weighted average
    total_weight = sum(w for _, w in scores)
    weighted_score = sum(s * w for s, w in scores) / total_weight if total_weight > 0 else 0.5
    final_score = round(min(1.0, max(0.0, weighted_score)), 4)

    positive = sum(1 for f in findings if f.get('positive') is True)
    negative = sum(1 for f in findings if f.get('positive') is False)
    neutral = sum(1 for f in findings if f.get('neutral') is True)

    log.add(f'Verification complete — score: {final_score:.2f} | +{positive} -{negative} ~{neutral}')

    if negative > positive:
        summary = f'Web verification found {negative} negative signal(s) against {positive} positive — treat with caution.'
    elif positive > negative:
        summary = f'Web verification found {positive} positive signal(s) — company appears to have legitimate digital footprint.'
    else:
        summary = 'Web verification was inconclusive — insufficient data to confirm legitimacy.'

    return {
        'score': final_score,
        'findings': findings,
        'agent_log': log.to_list(),
        'summary': summary,
        'stats': {'positive': positive, 'negative': negative, 'neutral': neutral}
    }
