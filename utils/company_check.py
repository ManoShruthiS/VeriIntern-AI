import re

# ─── Known Legitimate Companies Database ──────────────────────────────────────
KNOWN_LEGIT_COMPANIES = {
    # Tech Giants
    "google", "microsoft", "amazon", "apple", "meta", "facebook", "netflix",
    "twitter", "linkedin", "adobe", "oracle", "salesforce", "ibm", "intel",
    # Indian IT
    "tcs", "tata consultancy services", "infosys", "wipro", "hcl", "tech mahindra",
    "mphasis", "hexaware", "cognizant", "accenture", "capgemini", "deloitte",
    # Indian Startups / Unicorns
    "zoho", "flipkart", "razorpay", "paytm", "swiggy", "zomato", "ola", "cred",
    "byju", "unacademy", "freshworks", "chargebee", "browserstack", "druva",
    "meesho", "nykaa", "boat", "zepto", "dunzo", "groww", "zerodha", "upstox",
    # Research / Finance
    "isro", "drdo", "niti aayog", "goldman sachs", "jpmorgan", "morgan stanley",
    "blackrock", "mckinsey", "bcg", "bain", "kpmg", "pwc", "ey", "ernst young",
    # Others
    "siemens", "bosch", "samsung", "lg", "sony", "nvidia", "amd", "qualcomm",
    "cisco", "vmware", "palo alto", "crowdstrike", "splunk", "snowflake",
}

# ─── Red-Flag Company Name Patterns ───────────────────────────────────────────
SUSPICIOUS_COMPANY_PATTERNS = [
    r"\bfake\b", r"\bscam\b", r"\bearn\s?fast\b", r"\bquick\s?hire\b",
    r"\bcertify\s?now\b", r"\bskill\s?boost\b", r"\bdigiwork\b", r"\btechgrow\b",
    r"\bworkfromhome\s?inc\b", r"\bglobaltechfake\b", r"\bearnnow\b",
    r"\binstant\s?jobs?\b", r"\bfree\s?cert\b", r"\bjob\s?guaranteed\b",
]

def normalize(name: str) -> str:
    return re.sub(r"[^a-z\s]", "", name.lower().strip())

def verify_company(company_name: str) -> dict:
    """
    Returns:
        status: 'verified' | 'suspicious' | 'unknown'
        score: 0.0 – 1.0  (1.0 = fully trusted)
        reason: human-readable explanation
    """
    if not company_name or not company_name.strip():
        return {"status": "unknown", "score": 0.3, "reason": "No company name provided."}

    norm = normalize(company_name)

    # Direct match in trusted list
    for known in KNOWN_LEGIT_COMPANIES:
        if known in norm or norm in known:
            return {
                "status": "verified",
                "score": 1.0,
                "reason": f"'{company_name}' is a recognised, legitimate company."
            }

    # Check suspicious patterns
    for pattern in SUSPICIOUS_COMPANY_PATTERNS:
        if re.search(pattern, norm):
            return {
                "status": "suspicious",
                "score": 0.0,
                "reason": f"'{company_name}' matches known fraudulent company name patterns."
            }

    # Heuristic checks
    warnings = []
    score = 0.5

    if len(norm.split()) < 1:
        warnings.append("Very short company name")
        score -= 0.1

    generic_words = ["solutions", "services", "hub", "pro", "corp", "technologies", "global"]
    overlap = [w for w in generic_words if w in norm]
    if len(overlap) >= 2:
        warnings.append("Name uses multiple generic business keywords")
        score -= 0.15

    if re.search(r"\d", norm):
        warnings.append("Company name contains numbers (unusual)")
        score -= 0.1

    score = max(0.1, min(0.6, score))
    reason = "Company not found in verified database."
    if warnings:
        reason += " Concerns: " + "; ".join(warnings) + "."

    return {"status": "unknown", "score": score, "reason": reason}
