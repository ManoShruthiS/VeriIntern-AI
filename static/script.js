/* VeriIntern-AI — Frontend Logic */

const FRAUD_SAMPLE = `Congratulations! You have been selected for a remote internship at TechGrow Solutions. No interview required. You will earn ₹15,000/month working from home. 

To confirm your seat and receive your offer letter, please pay a registration fee of ₹999 within 24 hours. 

Transfer to: UPI ID - techgrowjobs@upi
Limited seats only — offer expires tonight!

Visit: http://techgrow-internship.xyz/register`;

const LEGIT_SAMPLE = `Google is hiring Software Development interns for Summer 2025!

Join our engineering team in Bangalore and work on real-world projects alongside experienced engineers.

Details:
- Role: Software Development Intern
- Duration: 3 months (May–July 2025)
- Stipend: ₹25,000/month
- Location: Bangalore, India
- Selection: Resume screening + 2 technical rounds + HR discussion

No registration fee. Apply through our official portal only.
Deadline: April 15, 2025

Apply at: https://careers.google.com/jobs/results/internship-2025`;

// ─── Sample loader ─────────────────────────────────────────────────────────
function loadSample(type) {
  document.getElementById('offerText').value = type === 'fraud' ? FRAUD_SAMPLE : LEGIT_SAMPLE;
  document.getElementById('companyName').value = type === 'fraud' ? 'TechGrow Solutions' : 'Google';
  document.getElementById('urlInput').value = type === 'fraud'
    ? 'http://techgrow-internship.xyz/register'
    : 'https://careers.google.com/jobs/results/internship-2025';
  updateCharCount();
  // Hide previous results
  document.getElementById('resultsSection').classList.add('hidden');
}

// ─── Character counter ────────────────────────────────────────────────────
function updateCharCount() {
  const len = document.getElementById('offerText').value.length;
  document.getElementById('charCount').textContent = len.toLocaleString();
}
document.getElementById('offerText').addEventListener('input', updateCharCount);

// ─── Main analysis function ───────────────────────────────────────────────
async function analyzeOffer() {
  const offerText   = document.getElementById('offerText').value.trim();
  const companyName = document.getElementById('companyName').value.trim();
  const url         = document.getElementById('urlInput').value.trim();

  if (!offerText) {
    shakeElement('offerText');
    return;
  }

  setLoading(true);

  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ offer_text: offerText, company_name: companyName, url: url })
    });

    if (!response.ok) throw new Error(`Server error: ${response.status}`);

    const data = await response.json();
    if (data.error) throw new Error(data.error);

    displayResults(data);
  } catch (err) {
    showError(err.message || 'Analysis failed. Make sure the Flask server is running.');
  } finally {
    setLoading(false);
  }
}

// ─── Display results ──────────────────────────────────────────────────────
function displayResults(data) {
  const isFraud = data.verdict === 'FRAUD';
  const conf = data.confidence_percent;

  // Show section
  const section = document.getElementById('resultsSection');
  section.classList.remove('hidden');

  // ── Verdict banner ──
  const banner = document.getElementById('verdictBanner');
  banner.className = `verdict-banner ${isFraud ? 'fraud' : 'legit'}`;

  document.getElementById('verdictIcon').textContent = isFraud ? '🚨' : '✅';
  document.getElementById('verdictLabel').textContent = isFraud ? 'FRAUD DETECTED' : 'LOOKS LEGITIMATE';
  document.getElementById('verdictConfidence').textContent =
    `${conf}% confidence · Score: ${(data.combined_fraud_probability * 100).toFixed(1)}% fraud probability`;

  // Confidence ring animation
  const ringFill = document.getElementById('ringFill');
  const circumference = 201;
  const offset = circumference - (conf / 100) * circumference;
  setTimeout(() => { ringFill.style.strokeDashoffset = offset; }, 100);
  animateCounter('ringPct', 0, conf, '%', 1000);

  // ── Score bars ──
  const scores = data.component_scores;
  const mlFraud = +(scores.ml_fraud_probability * 100).toFixed(1);
  const compLegit = +(scores.company_legitimacy * 100).toFixed(1);
  const urlSafe = +(scores.url_safety * 100).toFixed(1);

  setBar('mlBar',      mlFraud,   true,  'mlValue',      mlFraud + '% fraud prob');
  setBar('companyBar', compLegit, false, 'companyValue', compLegit + '% legit');
  setBar('urlBar',     urlSafe,   false, 'urlValue',     urlSafe + '% safe');

  // ── Company card ──
  document.getElementById('companyName2').textContent = data.company.name || 'Not detected';
  document.getElementById('companyReason').textContent = data.company.reason;
  document.getElementById('companyBadge').textContent = data.company.status;
  document.getElementById('companyBadge').className = `detail-badge badge-${data.company.status}`;

  // ── URL card ──
  document.getElementById('urlName').textContent = data.url.value || 'Not found';
  document.getElementById('urlReason').textContent = data.url.reason;
  document.getElementById('urlBadge').textContent = data.url.status;
  document.getElementById('urlBadge').className = `detail-badge badge-${data.url.status}`;

  // ── Explanations ──
  const list = document.getElementById('explanationsList');
  list.innerHTML = '';
  (data.explanations || []).forEach(exp => {
    const div = document.createElement('div');
    div.className = 'explanation-item';
    div.textContent = exp;
    list.appendChild(div);
  });

  // ── Text signals ──
  const fraudKws = data.text_signals?.fraud_keywords || [];
  const legitSigs = data.text_signals?.legit_signals || [];

  const fraudSection = document.getElementById('fraudKeywordsSection');
  const legitSection = document.getElementById('legitSignalsSection');

  if (fraudKws.length > 0) {
    fraudSection.classList.remove('hidden');
    document.getElementById('fraudKeywordsList').innerHTML =
      fraudKws.map(k => `<span class="keyword-tag fraud-tag">${k}</span>`).join('');
  } else {
    fraudSection.classList.add('hidden');
  }

  if (legitSigs.length > 0) {
    legitSection.classList.remove('hidden');
    document.getElementById('legitSignalsList').innerHTML =
      legitSigs.map(k => `<span class="keyword-tag legit-tag">${k}</span>`).join('');
  } else {
    legitSection.classList.add('hidden');
  }

  // Scroll to results
  setTimeout(() => section.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
}

// ─── Helpers ──────────────────────────────────────────────────────────────
function setBar(barId, pct, isFraud, valueId, label) {
  const bar = document.getElementById(barId);
  bar.className = `score-bar ${isFraud ? 'fraud-bar' : 'safe-bar'}`;
  setTimeout(() => { bar.style.width = Math.min(100, pct) + '%'; }, 200);
  document.getElementById(valueId).textContent = label;
}

function animateCounter(id, from, to, suffix, duration) {
  const el = document.getElementById(id);
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    const ease = t < 0.5 ? 2*t*t : -1 + (4-2*t)*t;
    el.textContent = Math.round(from + (to - from) * ease) + suffix;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function setLoading(active) {
  const btn = document.getElementById('analyzeBtn');
  const loader = document.getElementById('btnLoader');
  const dot = document.getElementById('statusDot');
  btn.disabled = active;
  loader.classList.toggle('visible', active);
  dot.classList.toggle('active', active);
  document.getElementById('btnLoader').style.display = active ? 'block' : 'none';
  document.querySelector('.btn-text').textContent = active ? 'Analyzing...' : 'Analyze Offer';
}

function shakeElement(id) {
  const el = document.getElementById(id);
  el.style.animation = 'none';
  el.offsetHeight; // reflow
  el.style.animation = 'shake 0.4s ease';
  el.style.borderColor = 'var(--danger)';
  setTimeout(() => { el.style.borderColor = ''; el.style.animation = ''; }, 800);
}

function showError(msg) {
  alert('❌ Error: ' + msg);
}

function resetForm() {
  document.getElementById('offerText').value = '';
  document.getElementById('companyName').value = '';
  document.getElementById('urlInput').value = '';
  document.getElementById('charCount').textContent = '0';
  document.getElementById('resultsSection').classList.add('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Shake animation
const style = document.createElement('style');
style.textContent = `@keyframes shake {
  0%,100%{transform:translateX(0)}
  20%{transform:translateX(-8px)}
  40%{transform:translateX(8px)}
  60%{transform:translateX(-5px)}
  80%{transform:translateX(5px)}
}`;
document.head.appendChild(style);
