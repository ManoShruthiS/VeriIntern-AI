<div align="center">

# VeriIntern AI

### Intelligent Authenticity Detection System for Internship Offers

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-Academic-blue?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge)]()

A multi-layer AI-powered system that protects students from deceptive internship offers by combining NLP text analysis, corporate identity verification, URL safety checks, and real-time web intelligence.

</div>

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Objective](#objective)
- [System Architecture](#system-architecture)
- [Core Detection Layers](#core-detection-layers)
- [Weighted Decision Fusion](#weighted-decision-fusion)
- [System Workflow](#system-workflow)
- [Detection Scenarios](#detection-scenarios)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [Installation and Usage](#installation-and-usage)
- [Testing and Validation](#testing-and-validation)
- [Team](#team)
- [Conclusion](#conclusion)

---

## Problem Statement

Students frequently encounter illegitimate internship solicitations that involve:

- **Unauthorized payment requests** — "registration fees", "security deposits", "processing fees"
- **Deceptive company identities** — visual character tricks like `rnicrosoft` mimicking `microsoft`
- **Suspicious or phishing URLs** — domains with risky TLDs, URL shorteners, gibberish hostnames
- **Pressure tactics** — "offer expires tonight", "limited seats", "confirm your seat now"

Standard detection methods rely solely on keyword matching, which fails against sophisticated impersonation. VeriIntern AI addresses this gap with a multi-layer fusion approach that cross-references global knowledge bases and security markers.

**Distribution of Illegitimate Internship Tactics (Observed Patterns):**

| Tactic | Frequency |
|:---|:---|
| Payment Demands | 35% |
| Fake Company Names | 25% |
| Phishing URLs | 20% |
| Pressure Tactics | 12% |
| False Guarantees | 8% |

---

## Objective

- Develop a multi-source analytical framework for internship authenticity detection
- Integrate ML-based linguistic predictions with external intelligence checks
- Implement homoglyph and impersonation neutralization for visual character tricks
- Provide a clear verdict, confidence score, and detailed explanation report
- Deliver a production-ready web application with a premium analytical dashboard

---

## System Architecture

The system follows a 4-layer parallel analysis pipeline that feeds into a weighted fusion engine:

```
                    +----------------------------------+
                    |   Student Submits Offer Details   |
                    +----------------+-----------------+
                                     |
                          +----------v-----------+
                          | Text and URL Extraction |
                          +----------+-----------+
                                     |
              +----------------------+----------------------+
              |              |               |               |
     +--------v-------+ +---v----------+ +--v-----------+ +-v--------------+
     | Layer 1:        | | Layer 2:     | | Layer 3:     | | Layer 4:       |
     | Semantic        | | Identity     | | Network      | | Web            |
     | Analysis        | | Verification | | Validation   | | Intelligence   |
     | (NLP + ML)      | | (Homoglyph)  | | (URL+WHOIS)  | | (Wikipedia)    |
     +--------+-------+ +---+----------+ +--+-----------+ +-+--------------+
              |              |               |               |
              +----------+---+------+--------+-------+-------+
                         |          |                 |
                +--------v----------v-----------------v--------+
                |          Weighted Fusion Engine               |
                |          with Override Logic                  |
                +--------+-------------+--------------+--------+
                         |             |              |
                   +-----v-----+ +----v------+ +-----v-----------+
                   | Verdict:  | | Confidence| | Reasoning       |
                   | SCAM or   | | Percentage| | Report          |
                   | LEGITIMATE| |           | |                 |
                   +-----------+ +-----------+ +-----------------+
```

---

## Core Detection Layers

### Layer 1: Linguistic Signal Analysis (NLP/ML)

The text analysis engine uses a tiered keyword scoring system with negation-aware detection to evaluate offer language. When a trained ML model (`pipeline.pkl`) is available, it uses TF-IDF vectorization for prediction. Otherwise, it falls back to the keyword-based tiered scoring system.

**Detection Flow:**

```
Input Text --> Negation-Aware Parser --> Keyword Tier Classification
                                              |
                    +-----------+-------------+-------------+
                    |           |             |             |
               Critical     High          Medium       Legit Signals
               (payment)   (red flags)   (pressure)   (reduces score)
                    |           |             |             |
                    +-----+-----+------+------+------+-----+
                          |            |             |
                          v            v             v
                    Tiered Score Computation --> Inauthenticity Probability
```

**Keyword Tier Scoring:**

| Tier | Count | Score Impact | Examples |
|:---|:---|:---|:---|
| Critical (payment demands) | 13 phrases | +0.50 to +0.90 | `registration fee`, `pay now`, `send money` |
| High (process red flags) | 7 phrases | +0.20 to +0.30 | `no interview required`, `instant offer letter` |
| Medium (pressure tactics) | 6 phrases | +0.06 to +0.20 | `limited seats`, `offer expires`, `guaranteed certificate` |
| Legit Signals (legitimate indicators) | 16 phrases | -20% to -60% | `interview process`, `coding round`, `screening process` |

**Negation Awareness:** The system distinguishes between `"Pay registration fee"` (scam) and `"No registration fee"` (legitimate) by scanning a 25-character prefix window for negation words like `no`, `not`, `without`, `never`, `don't`.

---

### Layer 2: Identity Verification

Multi-stage corporate identity validation protecting against impersonation attacks. The system maintains a curated database of 200+ verified companies spanning global tech, Indian IT, consulting, banking, startups, pharma, FMCG, telecom, and government PSUs.

**Verification Pipeline:**

```
Company Name Input
      |
      v
Basic Normalization (lowercase, strip symbols)
      |
      v
Direct Match in 200+ Verified Companies? ---YES--> VERIFIED (Score: 1.0)
      |NO
      v
Homoglyph Normalization (rn->m, 0->o, vv->w, etc.)
      |
      v
Matches Known Company After Normalization? ---YES--> IMPERSONATION (Score: 0.02)
      |NO
      v
Fuzzy Match (SequenceMatcher, threshold >= 80%)
      |
      v
Similarity >= 80%? ---YES--> SUSPICIOUS (Score: 0.05)
      |NO
      v
Matches Red-Flag Name Patterns? ---YES--> SUSPICIOUS (Score: 0.05)
      |NO
      v
UNVERIFIED (Score: 0.45) -- relies on web agent
```

**Homoglyph Detection Map:**

| Visual Trick | Fake | Real | Example |
|:---|:---|:---|:---|
| `rn` to `m` | rn | m | `rnicrosoft` becomes `microsoft` |
| `vv` to `w` | vv | w | `vvipro` becomes `wipro` |
| `0` to `o` | 0 (zero) | o | `g00gle` becomes `google` |
| `1` to `l` | 1 (one) | l | `1inkedin` becomes `linkedin` |
| `$` to `s` | $ | s | `micro$oft` becomes `microsoft` |
| `@` to `a` | @ | a | `@mazon` becomes `amazon` |
| `3` to `e` | 3 | e | `d3loitte` becomes `deloitte` |
| `!` to `i` | ! | i | `!nfosys` becomes `infosys` |

---

### Layer 3: Infrastructure and URL Safety

Automated domain analysis with multi-signal risk assessment. Checks against a curated list of 30+ trusted domains and evaluates multiple risk factors.

**Risk Factor Analysis:**

| Risk Factor | Score Penalty | Indicator |
|:---|:---|:---|
| Suspicious TLD (`.xyz`, `.tk`, `.gq`, `.ml`) | -0.25 | Free/spam-associated domains |
| Suspicious Pattern (shorteners, gibberish) | -0.20 | URL obfuscation attempt |
| Multiple Hyphens (2 or more) | -0.15 | Phishing domain structure |
| No HTTPS | -0.10 | Missing encryption |
| Excessive Subdomains (more than 4 levels) | -0.10 | Complex redirect chains |
| Very New Domain (less than 90 days) | -0.20 | Recently registered via WHOIS |

---

### Layer 4: Web Intelligence Agent

Real-time web verification using Wikipedia's MediaWiki API with contradiction detection. The agent queries the global knowledge base, validates whether the entity is actually an organization, and cross-checks the offer text for scam contradictions.

**Agent Decision Flow:**

```
Company Name --> Wikipedia API Search (top 5 results)
                        |
                  Results Found?
                   /         \
                 NO           YES
                 |             |
          No Public         Exact Title
          Presence          Match Filter
          (Score: 0.25)        |
                          Is Organization?
                          (founded, revenue,
                           employees, etc.)
                           /         \
                         NO           YES
                         |             |
                    Not a Company   Scam Phrase
                    (Score: 0.40)  Contradiction Check
                                    /         \
                              Demands         Clean Offer
                              Payment
                              |                    |
                         SCAM DETECTED        VERIFIED ORG
                         (Score: 0.01)        (Score: 0.95)
```

**Scam Contradiction Logic:** If an offer uses the name of a real, verified organization but simultaneously demands payment (e.g., "Google internship - pay Rs.999 registration fee"), the agent flags it as a scam. Real companies never charge students for internship placements.

---

## Weighted Decision Fusion

The fusion engine combines all four layers using a priority-weighted system where the Web Intelligence Agent serves as the primary signal driver.

**Component Weights:**

| Component | Weight | Role |
|:---|:---|:---|
| Web Intelligence Agent | **50%** | Primary signal — validates global corporate footprint |
| Identity Verification | **20%** | Detects impersonation, homoglyphs, and name tricks |
| Network Safety | **15%** | Evaluates URL, domain, TLD, and WHOIS data |
| ML Text Classification | **15%** | Identifies linguistic scam patterns in offer text |

```
Weight Distribution:

Web Intelligence Agent  [##########__________]  50%
Identity Verification   [####________________]  20%
Network Safety          [###_________________]  15%
ML Text Classification  [###_________________]  15%
```

### Override Rules

The system includes critical override logic for high-confidence scenarios:

| Rule | Trigger Condition | Action |
|:---|:---|:---|
| Homoglyph Impersonation | Company score <= 0.05 | Force ML >= 0.85, Cap agent <= 0.10 |
| Misspelled Company | Company score <= 0.10 | Force ML >= 0.75, Cap agent <= 0.25 |
| Payment with Real Name | ML scam score >= 0.75 | Force agent scam >= 0.70, Force company scam >= 0.70 |

These overrides ensure that even when individual layers disagree (e.g., Wikipedia confirms "Google" exists, but the offer demands payment), the final verdict correctly reflects the deception.

---

## System Workflow

```
Submit Offer --> Preprocessing --> [ML Scan]      --> Weighted Score --> Final Output
                 and Extraction    [Identity Check]    Fusion           with Explanations
                                   [Network Analysis]
                                   [Web Research]
```

**Step-by-step process:**

1. User submits offer text, optional company name, and optional URL
2. System auto-extracts company name and URL from text if not provided
3. All four analysis layers run in sequence
4. Scores are converted to inauthenticity probabilities and fused with weights
5. Override rules are applied for high-confidence edge cases
6. Final verdict (SCAM/LEGITIMATE), confidence percentage, and reasoning report are returned

---

## Detection Scenarios

Example scenarios demonstrating the system's detection capabilities:

| Scenario | ML Score | Company | URL | Agent | Verdict |
|:---|:---|:---|:---|:---|:---|
| Real company, legitimate offer | 0.00 | Verified (1.0) | Safe (1.0) | Confirmed (0.95) | **LEGITIMATE** |
| Fake company, payment demands | 0.90 | Unknown (0.45) | Risky (0.35) | Not found (0.25) | **INAUTHENTIC** |
| Real name + payment demand | 0.75 | Verified (1.0) | Safe (1.0) | Override (0.01) | **INAUTHENTIC** |
| Homoglyph impersonation (`rnicrosoft`) | 0.85+ | Impersonation (0.02) | Unknown (0.60) | Override (0.10) | **INAUTHENTIC** |
| Unknown company, clean language | 0.00 | Unverified (0.45) | No URL | Mixed (0.50) | **LEGITIMATE** |

---

## Tech Stack

| Layer | Technology |
|:---|:---|
| Language | Python 3.10+ |
| ML / NLP | Scikit-learn 1.4, TF-IDF Vectorization |
| Data Processing | Pandas 2.2, NumPy 1.26 |
| Backend Framework | Flask 3.0, Gunicorn |
| Frontend | HTML5, CSS3, ES6 JavaScript |
| Intelligence Source | MediaWiki API (Wikipedia) |
| Web Scraping | BeautifulSoup4, Requests |
| Network Analysis | python-whois, urllib |
| Deployment | Render (via Procfile) |

---

## Project Structure

```
VeriIntern-AI/
|
|-- app.py                    # Core API server, fusion engine, ML scoring logic
|-- test_scoring.py           # Automated test suite for scoring validation
|-- requirements.txt          # Python dependency manifest (28 packages)
|-- Procfile                  # Deployment config for Gunicorn
|-- runtime.txt               # Python runtime specification
|-- .gitignore                # Git exclusion rules
|
|-- utils/                    # Specialized analysis modules
|   |-- __init__.py           # Package initializer
|   |-- company_check.py      # Identity engine: 200+ companies, homoglyph detection
|   |-- scraping_agent.py     # Web intelligence agent: Wikipedia + URL liveness
|   |-- url_check.py          # URL safety: TLD, WHOIS, pattern analysis
|
|-- templates/
|   |-- index.html            # Premium analytical dashboard (IBM Plex typography)
|
|-- static/
    |-- style.css             # Glassmorphism dark-mode design system
    |-- script.js             # Client-side orchestration and API bridge
    |-- favicon.svg           # Brand identity mark (shield icon)
```

---

## Features

- **4-Layer Prioritized Detection** — ML, identity, network, and web intelligence working in parallel
- **ML Pipeline with TF-IDF** — Scikit-learn powered text classification with keyword fallback
- **Homoglyph Impersonation Detection** — Catches tricks like `rnicrosoft`, `g00gle`, `vvipro`, and more
- **Negation-Aware Keyword Matching** — Distinguishes "pay fee" from "no fee" using prefix scanning
- **Real-Time Web Intelligence** — Live Wikipedia verification via MediaWiki API
- **URL and Domain Risk Analysis** — TLD checks, WHOIS age, pattern detection, subdomain analysis
- **Weighted Fusion with Override Logic** — Priority-based scoring with hard overrides for edge cases
- **Premium Analytical Dashboard** — Dark glassmorphism UI with IBM Plex typography
- **Detailed Reasoning Reports** — Full transparency on every detection decision
- **Comprehensive Test Suite** — Automated validation for homoglyphs, negation, and scoring

---

## Installation and Usage

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/ManoShruthiS/VeriIntern-AI.git
cd VeriIntern-AI

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will be available at `http://localhost:5000`

### API Endpoint

```
POST /analyze
Content-Type: application/json

{
    "offer_text": "Congratulations! Pay Rs.999 registration fee for Google internship.",
    "company_name": "Google",
    "url": "https://example.com",
    "skip_scraping": false
}
```

**Response:**
```json
{
    "verdict": "INAUTHENTIC",
    "is_scam": true,
    "confidence_percent": 92.5,
    "component_scores": {
        "ml_scam_probability": 0.75,
        "agent_legitimacy": 0.01,
        "company_legitimacy": 1.0,
        "url_safety": 0.6
    },
    "explanations": ["..."]
}
```

---

## Testing and Validation

Run the automated test suite:

```bash
python test_scoring.py
```

The test suite validates:

| Test Category | Cases | What It Validates |
|:---|:---|:---|
| Homoglyph Detection | 7 | `rnicrosoft`, `g00gle`, `vvipro`, `1nfosys`, `micro$oft`, `d3loitte`, `@mazon` |
| Fuzzy Impersonation | 2 | Typo-based impersonation (`Gogle`, `Microsft`) |
| Verified Companies | 3 | Correct recognition of real companies |
| Negation Awareness | 7 | Distinguishing scam keywords vs. negated keywords |
| ML Scoring | 4 | End-to-end inauthenticity probability computation |

---

## Team

| Role | Name | Responsibility |
|:---|:---|:---|
| **Team Leader and Tester** | **Bala Sowndarya B** | Project guidance, team coordination, testing and quality assurance, problem solving, ideation, and development support |
| **Developer** | **Mano Shruthi S** | Full-stack development, ML pipeline, backend architecture, and system implementation |
| **Presenter and Data Collector** | **Kowsalya V** | Project presentation, data collection, and documentation |
| **Presenter and Data Collector** | **Kaviya Varshini S** | Project presentation, data collection, and documentation |

---

## Conclusion

VeriIntern AI provides a comprehensive and scalable analytical solution for neutralizing the threat of illegitimate internship offers. By fusing linguistic patterns with real-world web intelligence across four specialized detection layers, the system achieves high detection accuracy while minimizing false positives. The weighted fusion engine with override logic ensures that even sophisticated attacks — including homoglyph impersonation and payment-demanding scams using real company names — are reliably detected.

This system creates a reliable and trustworthy environment for students navigating online career opportunities.

---

<div align="center">

**VeriIntern AI** — Internship Authenticity Detection System

&copy; 2026 | Academic Project Submission

</div>
