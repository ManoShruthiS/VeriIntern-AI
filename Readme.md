# 🛡️ VeriIntern-AI — Intelligent Fraud Detection System

A multi-layer AI-powered system to detect fraudulent internship offers using NLP, company verification, and URL safety analysis.

---

## 👩‍💻 Team Members
- Mano Shruthi S
- Bala Sowndarya
- Kowsalya V
- Kaviya Varshini S

---

## 📁 Project Structure

```
veriintern-ai/
├── app.py                      ← Flask backend (main server)
├── requirements.txt            ← Python dependencies
├── data/
│   ├── generate_dataset.py     ← Generates synthetic training data
│   └── internship_dataset.csv  ← Generated dataset (800 samples)
├── model/
│   ├── train_model.py          ← Trains TF-IDF + Logistic Regression
│   └── pipeline.pkl            ← Saved trained model
├── utils/
│   ├── company_check.py        ← Company legitimacy verifier
│   └── url_check.py            ← URL safety checker
├── templates/
│   └── index.html              ← Frontend HTML
└── static/
    ├── style.css               ← Dark cybersecurity UI styles
    └── script.js               ← Frontend JavaScript
```

---

## 🚀 How to Run

### Step 1 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Generate Dataset (already done, skip if csv exists)
```bash
python data/generate_dataset.py
```

### Step 3 — Train the ML Model (already done, skip if pipeline.pkl exists)
```bash
python model/train_model.py
```

### Step 4 — Start the Flask Server
```bash
python app.py
```

### Step 5 — Open in Browser
```
http://localhost:5000
```

---

## 🧠 How It Works

### Layer 1 — ML Text Analysis (50% weight)
- TF-IDF vectorization (unigrams + bigrams, 5000 features)
- Logistic Regression classifier
- Detects patterns like: "pay registration fee", "no interview required", "guaranteed certificate"

### Layer 2 — Company Verification (25% weight)
- Checks against a database of 80+ verified legitimate companies
- Detects suspicious company name patterns (e.g., TechGrow, EarnFast, DigiWorks)
- Heuristic scoring based on name structure

### Layer 3 — URL Safety Check (25% weight)
- Trusted domain whitelist (50+ verified domains)
- Suspicious TLD detection (.xyz, .top, .click, .tk etc.)
- URL shortener detection
- Domain pattern analysis
- Optional WHOIS domain age check

### Score Fusion Formula
```
Fraud Score = (ML × 0.50) + (Company Risk × 0.25) + (URL Risk × 0.25)
```
If Fraud Score ≥ 0.5 → FRAUD, else LEGITIMATE

---

## 📊 Model Performance (Synthetic Dataset)

| Metric     | Score  |
|-----------|--------|
| Accuracy  | 100%   |
| Precision | 1.00   |
| Recall    | 1.00   |
| F1-Score  | 1.00   |

> Note: 100% accuracy is expected on the synthetic dataset as it uses clearly patterned data.
> Real-world performance will vary. Collect more diverse training data to improve generalization.

---

## 🔌 API Endpoint

**POST /analyze**

Request body:
```json
{
  "offer_text": "Paste full internship offer text here",
  "company_name": "Optional company name",
  "url": "Optional URL"
}
```

Response:
```json
{
  "verdict": "FRAUD",
  "confidence_percent": 87.4,
  "combined_fraud_probability": 0.874,
  "component_scores": {
    "ml_fraud_probability": 0.95,
    "company_legitimacy": 0.0,
    "url_safety": 0.1
  },
  "company": { "name": "...", "status": "suspicious", "reason": "..." },
  "url": { "value": "...", "status": "suspicious", "reason": "..." },
  "text_signals": {
    "fraud_keywords": ["pay registration fee", "no interview"],
    "legit_signals": []
  },
  "explanations": ["..."]
}
```

---

## 💡 Future Enhancements
- BERT/transformer-based text classification
- Real-time VirusTotal API for URL scanning
- LinkedIn/Glassdoor company verification API
- Browser extension for job boards
- Email fraud detection
- Multilingual support (Tamil)
