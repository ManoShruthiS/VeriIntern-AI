import pandas as pd
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

# ─── Load dataset ──────────────────────────────────────────────────────────────
df = pd.read_csv("/home/claude/veriintern-ai/data/internship_dataset.csv")
X = df["text"]
y = df["label"]

# ─── Train/Test split ──────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# ─── Pipeline: TF-IDF + Logistic Regression ────────────────────────────────────
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        stop_words="english",
        sublinear_tf=True
    )),
    ("clf", LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    ))
])

pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)

print("=== VeriIntern-AI Model Evaluation ===")
print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
print(classification_report(y_test, y_pred, target_names=["Legitimate", "Fraud"]))

# ─── Save model ────────────────────────────────────────────────────────────────
os.makedirs("/home/claude/veriintern-ai/model", exist_ok=True)
with open("/home/claude/veriintern-ai/model/pipeline.pkl", "wb") as f:
    pickle.dump(pipeline, f)

print("Model saved to model/pipeline.pkl")
