"""Quick test of the improved scoring engine."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding='utf-8')

from utils.company_check import verify_company, normalize_homoglyphs
from app import ml_predict, keyword_present

print("=" * 70)
print("HOMOGLYPH IMPERSONATION DETECTION TESTS")
print("=" * 70)

tests = [
    ("rnicrosoft",          "homoglyph rn->m"),
    ("g00gle",              "homoglyph 0->o"),
    ("vvipro",              "homoglyph vv->w"),
    ("1nfosys",             "homoglyph 1->l"),
    ("micro$oft",           "homoglyph $->s"),
    ("d3loitte",            "homoglyph 3->e"),
    ("@mazon",              "homoglyph @->a"),
    ("Gogle",               "typo/fuzzy match"),
    ("Microsft",            "typo/fuzzy match"),
    ("Microsoft",           "real company"),
    ("Google",              "real company"),
    ("Infosys",             "real company"),
    ("TechGrow Solutions",  "fabricated name"),
    ("ABC Corp",            "unknown company"),
]

for name, desc in tests:
    r = verify_company(name)
    import re
    norm = re.sub(r"[^a-z\s]", "", name.lower().strip())
    canonical = normalize_homoglyphs(name)
    tag = "[IMPERSONATION]" if r["status"] == "impersonation" else ("[SUSPICIOUS]" if r["status"] == "suspicious" else ("[VERIFIED]" if r["status"] == "verified" else "[UNKNOWN]"))
    print(f"\n{tag} {name} ({desc})")
    print(f"   Status: {r['status']}, Score: {r['score']}")
    if canonical != norm:
        print(f"   Canonical: '{canonical}' (normalized from '{name}')")
    print(f"   Reason: {r['reason']}")


print("\n" + "=" * 70)
print("NEGATION-AWARE KEYWORD DETECTION TESTS")
print("=" * 70)

negation_tests = [
    ("Pay a registration fee of Rs.999",         "registration fee", True),
    ("No registration fee required",              "registration fee", False),
    ("We charge no registration fee",             "registration fee", False),
    ("Send money via UPI",                        "send money",       True),
    ("Don't send money to anyone",                "send money",       False),
    ("No interview required",                     "no interview required", True),
    ("There is an interview process",             "no interview required", False),
]

for text, keyword, expected in negation_tests:
    result = keyword_present(text.lower(), keyword)
    tag = "[PASS]" if result == expected else "[FAIL]"
    print(f"\n{tag} Text: \"{text}\"")
    print(f"   Keyword: \"{keyword}\" -> Present: {result} (expected: {expected})")


print("\n" + "=" * 70)
print("ML SCORING TESTS")
print("=" * 70)

scoring_tests = [
    ("Pay registration fee of Rs.999. Send money now via UPI. No interview required.", "Fraud: payment + no interview"),
    ("No registration fee. Apply through official portal. Resume screening, technical round, HR discussion.", "Legit: proper process"),
    ("Guaranteed certificate. Limited seats. Offer expires tonight.", "Medium fraud: pressure only"),
    ("Google internship. Technical round. HR round. Coding assessment. Apply at careers.google.com.", "Legit: all legit signals"),
]

for text, desc in scoring_tests:
    prob, method = ml_predict(text)
    tag = "[FRAUD]" if prob >= 0.5 else "[LEGIT]"
    print(f"\n{tag} {desc}")
    print(f"   Fraud probability: {prob:.2f} ({method})")

print("\n" + "=" * 70)
print("ALL TESTS COMPLETE")
print("=" * 70)
