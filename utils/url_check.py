import re
import urllib.parse
from datetime import datetime

try:
    import whois as python_whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

# ─── Trusted domains ───────────────────────────────────────────────────────────
TRUSTED_DOMAINS = {
    "google.com", "microsoft.com", "amazon.com", "amazon.in", "linkedin.com",
    "tcs.com", "infosys.com", "wipro.com", "hcl.com", "zoho.com",
    "flipkart.com", "razorpay.com", "freshworks.com", "swiggy.in", "zomato.com",
    "cred.club", "groww.in", "zerodha.com", "accenture.com", "deloitte.com",
    "ibm.com", "nvidia.com", "adobe.com", "salesforce.com", "oracle.com",
    "cognizant.com", "capgemini.com", "github.com", "hackerrank.com",
    "unstop.com", "internshala.com", "naukri.com",
}

# ─── Suspicious TLDs / patterns ───────────────────────────────────────────────
SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".gq", ".ml", ".cf", ".tk", ".buzz", ".info", ".biz"}
SUSPICIOUS_PATTERNS = [
    r"bit\.ly", r"tinyurl", r"goo\.gl", r"t\.co", r"ow\.ly",   # URL shorteners
    r"free.*job", r"earn.*fast", r"certif.*free", r"job.*guaranteed",
    r"\d{4,}",           # Long number strings in domain
    r"[a-z0-9]{20,}",   # Gibberish long hostnames
]

def extract_domain(url: str) -> str | None:
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower().lstrip("www.")
    except Exception:
        return None

def check_domain_age(domain: str) -> dict:
    """Try WHOIS lookup to get domain age."""
    if not WHOIS_AVAILABLE:
        return {"age_days": None, "note": "WHOIS not available"}
    try:
        w = python_whois.whois(domain)
        created = w.creation_date
        if isinstance(created, list):
            created = created[0]
        if created:
            age = (datetime.now() - created).days
            return {"age_days": age, "note": f"Domain registered {age} days ago"}
    except Exception:
        pass
    return {"age_days": None, "note": "Could not retrieve WHOIS data"}

def check_url(url: str) -> dict:
    """
    Returns:
        status: 'safe' | 'suspicious' | 'unknown'
        score: 0.0 – 1.0 (1.0 = fully safe)
        reason: explanation
    """
    if not url or not url.strip():
        return {"status": "unknown", "score": 0.5, "reason": "No URL provided."}

    domain = extract_domain(url)
    if not domain:
        return {"status": "suspicious", "score": 0.1, "reason": "Could not parse the URL."}

    # Trusted domain
    for trusted in TRUSTED_DOMAINS:
        if domain == trusted or domain.endswith("." + trusted):
            return {"status": "safe", "score": 1.0, "reason": f"'{domain}' is a verified, trusted domain."}

    warnings = []
    score = 0.6

    # Suspicious TLD
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            warnings.append(f"Suspicious TLD: {tld}")
            score -= 0.25
            break

    # Suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, domain):
            warnings.append(f"Suspicious domain pattern detected")
            score -= 0.2
            break

    # Hyphen heavy domain (often phishing)
    if domain.count("-") >= 2:
        warnings.append("Domain contains multiple hyphens (phishing risk)")
        score -= 0.15

    # HTTP (no HTTPS)
    if url.strip().startswith("http://"):
        warnings.append("Non-HTTPS URL (insecure)")
        score -= 0.1

    # Subdomain depth
    parts = domain.split(".")
    if len(parts) > 4:
        warnings.append("Excessive subdomain depth")
        score -= 0.1

    # Domain age check
    age_info = check_domain_age(domain)
    if age_info["age_days"] is not None:
        if age_info["age_days"] < 90:
            warnings.append(f"Very new domain: only {age_info['age_days']} days old")
            score -= 0.2

    score = max(0.0, min(1.0, score))
    status = "safe" if score >= 0.7 else ("suspicious" if score < 0.4 else "unknown")
    reason = f"Domain '{domain}' is not in the verified list."
    if warnings:
        reason += " Issues: " + "; ".join(warnings) + "."

    return {"status": status, "score": round(score, 2), "reason": reason}
