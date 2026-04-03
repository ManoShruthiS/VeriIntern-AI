import pandas as pd
import random

random.seed(42)

# ─── Fraud Patterns ────────────────────────────────────────────────────────────
fraud_templates = [
    "Congratulations! You have been selected for an internship at {company}. No interview required. Pay a registration fee of ₹{amount} to confirm your seat.",
    "Exciting internship opportunity at {company}! Earn ₹{salary}/month working from home. Send ₹{amount} as security deposit to start immediately.",
    "We are hiring interns for {company}. Get a certificate and ₹{salary} stipend. No experience needed. Pay ₹{amount} processing fee today.",
    "URGENT! {company} is looking for remote interns. Salary: ₹{salary}/month. No interview. Pay ₹{amount} to unlock your offer letter.",
    "Dear student, you are shortlisted for {company} internship. Please transfer ₹{amount} registration charges within 24 hours.",
    "Work from home internship at {company}. ₹{salary}/month guaranteed. Limited seats. Pay ₹{amount} now before the offer expires.",
    "Get certified internship at {company} — no skills needed. Pay ₹{amount} to enroll now and receive your offer letter instantly.",
    "Internship at {company}: earn ₹{salary}/month online. 100% placement guaranteed. Submit ₹{amount} refundable deposit to apply.",
    "You won an internship at {company}! Claim your ₹{salary}/month stipend. Hurry — pay ₹{amount} to confirm before midnight.",
    "Top MNC {company} offers part-time internship ₹{salary}/month. No experience. No interview. Just pay ₹{amount} admin fee.",
    "Internship with daily payment at {company}. ₹{salary}/day guaranteed! Registration open — pay ₹{amount} now.",
    "Shortlisted! {company} remote internship. Certificate + ₹{salary} stipend. Hurry — only 5 seats left. Pay ₹{amount} fee.",
    "Internship at top startup {company}. 100% work from home. No rounds required. Pay ₹{amount} to get started today.",
    "Congratulations, you are selected for {company} internship! No resume needed. Pay ₹{amount} joining fee to activate your account.",
    "Earn ₹{salary}/month from home with {company}! Guaranteed certificate. Pay ₹{amount} to lock your spot now.",
]

# ─── Legitimate Patterns ───────────────────────────────────────────────────────
legit_templates = [
    "{company} is hiring {role} interns for Summer {year}. Apply at careers.{domain}. Stipend: ₹{salary}/month. Resume required.",
    "We are accepting applications for the {role} Internship at {company}. Duration: {duration} months. Apply through our official portal.",
    "{company} {role} Internship Program {year}: Work with our engineering team on real projects. Stipend provided. No fee required.",
    "Apply now for {company}'s {year} {role} Internship. Interview process includes technical round and HR discussion. Stipend: ₹{salary}/month.",
    "{company} is offering a {duration}-month paid internship in {role}. Applications close {date}. Visit {domain} to apply.",
    "Summer Internship at {company} — {role} track. Competitive stipend. Interview required. Apply via LinkedIn or our careers page.",
    "{company} {role} Intern | {year} Batch | ₹{salary}/month stipend | On-site, {city} | Deadline: {date}",
    "Join {company} as a {role} intern this summer. Our program includes mentorship, real-world projects, and a performance-based stipend.",
    "Internship Notice: {company} is recruiting {role} interns. Candidates will go through a screening process. No registration fees.",
    "{company} announces its annual internship drive for {year}. Roles: {role}. Duration: {duration} months. Official link: {domain}",
    "We at {company} are excited to open applications for our {role} internship program. Eligible candidates will be interviewed.",
    "{company} {role} Internship — Work on live projects with our team. Paid opportunity. Apply with your resume at {domain}.",
    "Internship at {company}: {role} | Duration: {duration} months | Stipend ₹{salary}/month | Merit-based selection process.",
    "{company} is conducting interviews for {year} internship cohort in {role}. Registration is free. Apply by {date}.",
    "Official Internship Opening at {company}. Role: {role}. Selection via assessment + interview. Stipend ₹{salary}/month.",
]

fake_companies = ["TechGrow Solutions", "DigiWorks India", "SkillBoost Hub", "EarnFast Corp",
                  "QuickHire Pro", "CertifyNow", "GlobalTech Fake", "WorkFromHome Inc"]

real_companies = ["Google", "Microsoft", "Amazon", "Infosys", "TCS", "Wipro",
                  "Zoho", "Flipkart", "Razorpay", "CRED", "Swiggy", "IBM", "Deloitte", "Accenture"]

roles = ["Software Development", "Data Science", "UI/UX Design", "Machine Learning",
         "Cybersecurity", "Cloud Computing", "Product Management", "DevOps"]

cities = ["Bangalore", "Chennai", "Hyderabad", "Pune", "Mumbai", "Delhi"]
domains = ["google.com", "microsoft.com", "tcs.com", "infosys.com", "wipro.com",
           "zoho.com", "careers.amazon.in", "flipkart.com"]

rows = []

# Generate fraud samples
for _ in range(400):
    template = random.choice(fraud_templates)
    text = template.format(
        company=random.choice(fake_companies),
        amount=random.choice([499, 999, 1499, 199, 299, 2000]),
        salary=random.choice([5000, 8000, 10000, 15000, 20000])
    )
    rows.append({"text": text, "label": 1})

# Generate legitimate samples
for _ in range(400):
    template = random.choice(legit_templates)
    text = template.format(
        company=random.choice(real_companies),
        role=random.choice(roles),
        year=random.choice([2024, 2025]),
        salary=random.choice([10000, 15000, 20000, 25000, 30000]),
        duration=random.choice([2, 3, 6]),
        city=random.choice(cities),
        domain=random.choice(domains),
        date=random.choice(["March 31", "April 15", "May 1", "June 30"])
    )
    rows.append({"text": text, "label": 0})

df = pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)
df.to_csv("/home/claude/veriintern-ai/data/internship_dataset.csv", index=False)
print(f"Dataset created: {len(df)} samples ({df['label'].sum()} fraud, {(df['label']==0).sum()} legit)")
