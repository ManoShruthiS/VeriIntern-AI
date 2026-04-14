# 🛡️ VeriIntern AI — Internship Fraud Detection System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-3.0.0-000000?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/Status-Stable-brightgreen?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Architecture-4--Layer%20Fusion-blue?style=for-the-badge"/>
</p>

---

## 📌 Project Overview
**VeriIntern AI** is a professional-grade cybersecurity tool designed to protect students from sophisticated internship fraud. Using a multi-layered **Intelligent Fusion Engine**, it analyzes offer text, verifies company identities, and cross-references global knowledge bases to identify scams with high precision.

---

## 🏗️ System Architecture & Flow

### 1. High-Level User Journey
How a student interacts with the system:

```mermaid
graph LR
    User([Student]) --> Input[Paste Internship Text]
    Input --> Analysis[Intelligent Analysis]
    Analysis --> Verdict{Verdict}
    Verdict --> Legit[✅ Legitimate: Safe to Apply]
    Verdict --> Fraud[🚨 FRAUD: DO NOT PAY]
```

### 2. The 4-Layer Verification Pipeline
Our "Defense-in-Depth" strategy for analyzing every internship offer:

```mermaid
graph TD
    A[Start: Offer Data Received] --> B{Layer 1: Text Signals}
    B -->|Check| B1[Tiered Keywords]
    B -->|Check| B2[Negation-Aware Scan]
    
    A --> C{Layer 2: Entity Check}
    C -->|Normalise| C1[Homoglyph Normalizer]
    C -->|Compare| C2[Verified DB Match]
    
    A --> D{Layer 3: URL Analysis}
    D -->|Evaluate| D1[Domain Age & TLD]
    D -->|Check| D2[Link Activity Status]
    
    A --> E{Layer 4: Global Agent}
    E -->|Query| E1[Wikipedia Research]
    E -->|Process| E2[Contradiction Guard]
    
    B & C & D & E --> F[Weighted Fusion Engine]
    F --> G[Final Confidence Verdict]
```

---

## 🔬 Core Technologies & Logic

### 1️⃣ Homoglyph Impersonation Guard
We detect "visual typos" that human eyes often miss but scammers use to mimic giants like Google or Microsoft.

```mermaid
flowchart LR
    In[Input: 'rnicrosoft'] --> Norm[Visual Normalizer]
    Norm --> Out[Canonical: 'microsoft']
    Out --> Verify{Verified ID?}
    Verify -- Yes --> Alert[🚨 IMPERSONATION ALERT]
```

| Type | Fake | Detected As |
|------|------|-------------|
| **rn → m** | `rnicrosoft` | **microsoft** |
| **0 → o** | `g00gle` | **google** |
| **vv → w** | `vvipro` | **wipro** |

### 2️⃣ Weighted Fusion Engine
Scores are combined using a dynamic weighting system that prioritizes **Global Presence (Web Agent)** over simple text matching.

| Component | Weight | Purpose |
|-----------|--------|---------|
| **Web Agent** | **55%** | Verifies global entity footprint. |
| **Company Check** | **25%** | Detects name trickery/impersonation. |
| **Text Analysis** | **20%** | Analyzes language and payment red flags. |

> [!IMPORTANT]
> **Scam Override**: If the "Global Agent" detects a "Registration Fee" demand, the fraud score is automatically forced to **99%**, even if the company name looks real.

---

## 🤖 Web Research Agent Logic
The agent doesn't just look for "real" entities—it checks for **Contextual Consistency**.

```mermaid
flowchart TD
    Start[Agent Start] --> Search[Wikipedia Search]
    Search --> Found{Entity Found?}
    
    Found -- No --> F3[Score: 0.20 - Unknown Entity]
    
    Found -- Yes --> Exact{Exact Match?}
    Exact -- No --> F2[Score: 0.35 - Typo Risk]
    
    Exact -- Yes --> Signals{Is it a Company?}
    Signals -- No --> F4[Score: 0.40 - Place/Object]
    
    Signals -- Yes --> Checks[Check for 'Registration Fee']
    Checks -- Detected --> F1[Score: 0.01 - SCAM OVERRIDE]
    Checks -- Clean --> F5[Score: 0.95 - Verified Org]
```

---

## 📁 Project Structure

```text
VeriIntern-AI/
├── app.py                 # Core API & Fusion Scoring Engine
├── utils/
│   ├── company_check.py   # Homoglyph & Database Logic
│   ├── url_check.py       # Phishing Detection Logic
│   └── scraping_agent.py  # Wikipedia Research Agent
├── static/
│   ├── style.css          # Premium Dark Theme Styles
│   └── script.js          # Result Rendering & Auto-Detection
├── templates/
│   └── index.html         # User Dashboard UI
└── test_scoring.py        # Automated Test Suite
```

---

## 🚀 Installation & Usage

1.  **Clone Repository**:
    ```bash
    git clone https://github.com/manoshruthis/VeriIntern-AI.git
    ```
2.  **Activate Environment**:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
3.  **Install & Run**:
    ```bash
    pip install -r requirements.txt
    python app.py
    ```

---

<p align="center">
  Developed with focus on Student Safety<br/>
  <strong>Team VeriIntern</strong>
</p>
