import re
import difflib

# ─────────────────────────────────────────────────────────────────────────────
# Company Verification Database
# Source: Indian MCA registered, NSE/BSE listed, Fortune 500, unicorns.
#
# PURPOSE:
#   1. Confirm known companies as "verified" (trust boost)
#   2. Detect impersonation via fuzzy matching (e.g. "Gogle" vs "Google")
#   3. Detect homoglyph impersonation (e.g. "rnicrosoft" vs "microsoft")
#
#   Unknown companies are NOT penalized — Wikipedia scraping decides their fate.
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_LEGIT_COMPANIES = {
    # Global Tech
    "google", "alphabet", "microsoft", "amazon", "apple", "meta", "facebook",
    "netflix", "twitter", "linkedin", "adobe", "oracle", "salesforce",
    "ibm", "intel", "amd", "nvidia", "qualcomm", "broadcom",
    "cisco", "vmware", "sap", "siemens", "ericsson", "nokia", "sony",
    "samsung", "lg", "huawei", "xiaomi", "oppo", "vivo", "oneplus",
    "hp", "dell", "lenovo", "asus", "acer",
    "paypal", "stripe", "shopify", "ebay", "alibaba", "tencent",
    "baidu", "bytedance", "tiktok", "zoom", "slack", "dropbox",
    "spotify", "uber", "lyft", "airbnb",
    "palo alto networks", "crowdstrike", "fortinet", "zscaler", "okta",
    "splunk", "servicenow", "workday", "zendesk", "hubspot",
    "mongodb", "snowflake", "palantir", "datadog", "atlassian", "github", "gitlab",
    # Indian IT
    "tcs", "tata consultancy services", "infosys", "wipro",
    "hcl technologies", "hcl tech", "hcl",
    "tech mahindra", "mphasis", "hexaware", "cognizant",
    "persistent systems", "cyient", "mastek", "mindtree",
    "happiest minds", "tata elxsi", "coforge", "birlasoft",
    "sonata software", "datamatics", "newgen software",
    "quick heal technologies", "tata technologies",
    # Consulting & BPO
    "accenture", "capgemini", "deloitte", "kpmg", "pwc", "pricewaterhousecoopers",
    "ey", "ernst young", "bain", "mckinsey", "bcg", "boston consulting group",
    "gartner", "wns global services", "exl service", "firstsource solutions",
    # Indian Banks & Finance
    "hdfc bank", "hdfc", "icici bank", "icici",
    "state bank of india", "sbi", "axis bank", "kotak mahindra bank", "kotak",
    "yes bank", "punjab national bank", "pnb",
    "bank of baroda", "canara bank", "federal bank", "indusind bank",
    "idfc first bank", "rbl bank", "bandhan bank",
    "bajaj finance", "bajaj finserv", "muthoot finance", "shriram finance",
    "tata capital", "groww", "zerodha", "upstox", "angel one",
    "motilal oswal", "iifl", "sharekhan", "paytm money",
    # Indian Startups & Unicorns
    "flipkart", "razorpay", "paytm", "one97 communications",
    "swiggy", "zomato", "ola", "cred",
    "byju", "byjus", "unacademy", "freshworks", "chargebee", "browserstack",
    "meesho", "nykaa", "boat", "zepto", "dunzo", "blinkit", "grofers",
    "big basket", "urban company", "urban clap",
    "vedantu", "toppr", "physics wallah", "pw",
    "simplilearn", "upgrad", "great learning", "scaler", "coding ninjas",
    "internshala", "naukri", "info edge", "iimjobs",
    "darwinbox", "keka", "zoho",
    "practo", "policybazaar", "acko", "digit insurance",
    "oyo", "makemytrip", "cleartrip", "ease my trip", "goibibo", "ixigo",
    "rapido", "delhivery", "bluedart", "xpressbees", "shiprocket",
    "udaan", "moglix", "zetwerk",
    "sharechat", "dailyhunt",
    "hotstar", "disney hotstar", "sony liv", "jio cinema", "zee5",
    "dream11", "mpl", "nazara technologies",
    "phonepe", "mobikwik", "cashfree",
    # Manufacturing & Conglomerates
    "tata motors", "tata steel", "tata power", "tata communications",
    "reliance industries", "reliance", "jio", "reliance jio", "reliance retail",
    "adani enterprises", "adani ports", "adani green",
    "mahindra", "bajaj auto", "hero motocorp", "tvs motor",
    "royal enfield", "eicher motors", "maruti suzuki",
    "bosch india", "motherson", "bharat forge",
    "havells", "voltas", "blue star", "godrej", "polycab",
    # Pharma & Healthcare
    "sun pharma", "dr reddys", "cipla", "lupin", "aurobindo pharma",
    "zydus lifesciences", "torrent pharmaceuticals", "glenmark pharmaceuticals",
    "biocon", "abbott india", "pfizer india", "gsk india",
    "apollo hospitals", "fortis healthcare", "max healthcare", "manipal hospitals",
    "medanta", "metropolis healthcare", "dr lal pathlabs",
    # FMCG & Retail
    "hindustan unilever", "hul", "nestle india", "itc",
    "britannia industries", "marico", "dabur india", "emami",
    "amul", "gcmmf", "jubilant foodworks", "rebel foods",
    # Telecom
    "airtel", "bharti airtel", "vodafone idea", "vi", "bsnl",
    # Energy
    "ongc", "indian oil corporation", "ioc", "bpcl", "hpcl",
    "gail india", "ntpc", "nhpc", "powergrid", "bhel",
    # Government PSUs & Regulatory
    "isro", "drdo", "hal", "hindustan aeronautics", "bel",
    "bharat electronics", "beml", "nasscom", "sebi", "rbi",
    # Global Finance
    "goldman sachs", "jpmorgan", "jp morgan", "morgan stanley", "blackrock",
    "citigroup", "citi", "wells fargo", "bank of america",
    "barclays", "ubs", "deutsche bank", "bnp paribas", "standard chartered", "hsbc",
}

# ─── Homoglyph / Visual Impersonation Detection ──────────────────────────────
# Fraudsters use visually similar characters to impersonate known companies:
#   "rnicrosoft" (rn → m), "g00gle" (0 → o), "vvipro" (vv → w)
#
# These tricks exploit how human eyes read — "rn" looks like "m" in most fonts,
# "0" (zero) looks like "o", etc. Our detector normalises these back to their
# canonical Latin form and then compares against the known company database.
#
# Multi-character substitutions (applied before single-char, order matters):
HOMOGLYPH_MULTI = [
    ('rn', 'm'),   # rnicrosoft → microsoft  (the classic trick)
    ('vv', 'w'),   # vvipro → wipro
    ('cl', 'd'),   # cleep → deep
]

# Single-character visual lookalikes:
HOMOGLYPH_SINGLE = {
    '0': 'o',   # g00gle → google
    '1': 'l',   # 1inkedin → linkedin
    '!': 'i',   # !nfosys → infosys
    '|': 'l',   # |inkedin → linkedin
    '$': 's',   # micro$oft → microsoft
    '@': 'a',   # @mazon → amazon
    '3': 'e',   # d3loitte → deloitte
    '5': 's',   # 5amsung → samsung
    '8': 'b',   # 8osch → bosch
}

# ─── Red-Flag Company Name Patterns ───────────────────────────────────────────
SUSPICIOUS_COMPANY_PATTERNS = [
    r"\bfake\b", r"\bscam\b", r"\bearn\s?fast\b", r"\bquick\s?hire\b",
    r"\bcertify\s?now\b", r"\bskill\s?boost\b", r"\bdigiwork\b", r"\btechgrow\b",
    r"\bworkfromhome\s?inc\b", r"\bearnnow\b",
    r"\binstant\s?jobs?\b", r"\bfree\s?cert\b", r"\bjob\s?guaranteed\b",
]


def normalize(name: str) -> str:
    """Basic normalization: lowercase, strip non-alpha except spaces."""
    return re.sub(r"[^a-z\s]", "", name.lower().strip())


def normalize_homoglyphs(name: str) -> str:
    """
    Normalize visual lookalike characters to their canonical Latin form.
    Converts tricks like 'rn' → 'm', '0' → 'o', etc.
    Returns a cleaned, canonical version of the name.
    """
    result = name.lower().strip()
    # Multi-character substitutions FIRST (order matters)
    for fake, real in HOMOGLYPH_MULTI:
        result = result.replace(fake, real)
    # Single-character substitutions
    for fake, real in HOMOGLYPH_SINGLE.items():
        result = result.replace(fake, real)
    # Final cleanup: strip non-alpha except spaces
    return re.sub(r"[^a-z\s]", "", result)


def detect_homoglyph_tricks(original: str) -> list:
    """Identify which specific visual tricks were used in the name."""
    tricks = []
    lower = original.lower()
    for fake, real in HOMOGLYPH_MULTI:
        if fake in lower:
            tricks.append(f"'{fake}' mimicking '{real}'")
    for fake, real in HOMOGLYPH_SINGLE.items():
        if fake in lower:
            tricks.append(f"'{fake}' mimicking '{real}'")
    return tricks


def verify_company(company_name: str) -> dict:
    # Role: Flag confirmed impersonations, suspicious names, and homoglyph tricks.
    # Unknown companies get lean-legitimate score. Wikipedia decides the rest.
    if not company_name or not company_name.strip():
        return {
            "status": "unknown",
            "score": 0.45,
            "reason": "No company name provided - relying on web verification."
        }

    norm = normalize(company_name)

    # Step 1: Direct match in trusted curated list
    if norm in KNOWN_LEGIT_COMPANIES:
        return {
            "status": "verified",
            "score": 1.0,
            "reason": f"'{company_name}' is a recognised, verified company."
        }

    # Multi-word name partial match
    for known in KNOWN_LEGIT_COMPANIES:
        if " " in known and known in norm:
            return {
                "status": "verified",
                "score": 1.0,
                "reason": f"'{company_name}' is a recognised, verified company."
            }

    # Step 2: Homoglyph impersonation detection (e.g. "rnicrosoft" → "microsoft")
    # This catches visual tricks that simple fuzzy matching can miss.
    canonical = normalize_homoglyphs(company_name)
    if canonical != norm:  # Homoglyph normalization actually changed the name
        tricks = detect_homoglyph_tricks(company_name)
        trick_str = ", ".join(tricks) if tricks else "visual character substitution"

        # Exact match after homoglyph normalization = confirmed impersonation
        if canonical in KNOWN_LEGIT_COMPANIES:
            return {
                "status": "impersonation",
                "score": 0.02,
                "reason": (
                    f"'{company_name}' is impersonating '{canonical}' "
                    f"using visual tricks ({trick_str}). "
                    f"This is a common fraud technique."
                )
            }

        # Multi-word partial match on canonical form
        for known in KNOWN_LEGIT_COMPANIES:
            if " " in known and known in canonical:
                return {
                    "status": "impersonation",
                    "score": 0.02,
                    "reason": (
                        f"'{company_name}' is impersonating '{known}' "
                        f"using visual tricks ({trick_str}). "
                        f"This is a common fraud technique."
                    )
                }

        # Fuzzy match on homoglyph-normalised form (catches combined tricks)
        for known in KNOWN_LEGIT_COMPANIES:
            if abs(len(canonical) - len(known)) > 3:
                continue
            ratio = difflib.SequenceMatcher(None, canonical, known).ratio()
            if ratio >= 0.82 and len(canonical) > 3:
                return {
                    "status": "impersonation",
                    "score": 0.03,
                    "reason": (
                        f"'{company_name}' uses visual tricks ({trick_str}) "
                        f"and closely resembles '{known}' — likely impersonation."
                    )
                }

    # Step 3: Fuzzy impersonation detection (e.g. "Gogle" vs "Google")
    for known in KNOWN_LEGIT_COMPANIES:
        if abs(len(norm) - len(known)) > 4:
            continue
        ratio = difflib.SequenceMatcher(None, norm, known).ratio()
        if 0.80 <= ratio < 1.0 and norm != known and len(norm) > 3:
            return {
                "status": "suspicious",
                "score": 0.05,
                "reason": f"'{company_name}' strongly resembles '{known}' - likely impersonation."
            }

    # Step 4: Explicitly suspicious fabricated name patterns
    for pattern in SUSPICIOUS_COMPANY_PATTERNS:
        if re.search(pattern, norm):
            return {
                "status": "suspicious",
                "score": 0.05,
                "reason": f"'{company_name}' matches known fraudulent company name patterns."
            }

    # Step 5: Unknown company - lean legitimate, let web agent (Wikipedia) decide
    # Real MCA-registered companies not in our list get benefit of the doubt here.
    return {
        "status": "unknown",
        "score": 0.65,
        "reason": f"'{company_name}' not in verified list - web verification will determine legitimacy."
    }
