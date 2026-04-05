// VeriIntern AI — Frontend Logic
// handles UI state, API calls, and rendering results

const SAMPLES = {
  fraud: {
    text: `Congratulations! You have been selected for a remote internship at TechGrow Solutions. No interview required. You will earn Rs.15,000/month working from home.

To confirm your seat and receive your offer letter, please pay a registration fee of Rs.999 within 24 hours. Transfer to UPI ID: techgrowjobs@upi

Limited seats only — offer expires tonight. Visit http://techgrow-internship.xyz/register to complete payment.`,
    company: 'TechGrow Solutions',
    url: 'http://techgrow-internship.xyz/register'
  },
  legit: {
    text: `Google is hiring Software Development interns for Summer 2025.

Join our engineering team in Bangalore and work on real-world projects alongside experienced engineers.

Role: Software Development Intern
Duration: 3 months (May to July 2025)
Stipend: Rs.25,000 per month
Location: Bangalore, India
Selection process: Resume screening, two technical rounds, and an HR discussion

No registration fee. Apply through the official portal only.
Application deadline: April 15, 2025
Apply at: https://careers.google.com/jobs/results/internship-2025`,
    company: 'Google',
    url: 'https://careers.google.com/jobs/results/internship-2025'
  }
};

let analysisInProgress = false;

// update character count as user types
document.getElementById('offerText').addEventListener('input', function() {
  const len = this.value.length;
  document.getElementById('charCount').textContent = len.toLocaleString() + ' characters';
});

function loadSample(type) {
  const s = SAMPLES[type];
  document.getElementById('offerText').value = s.text;
  document.getElementById('companyName').value = s.company;
  document.getElementById('urlInput').value = s.url;

  // update char count
  document.getElementById('charCount').textContent = s.text.length.toLocaleString() + ' characters';

  // reset results
  showState('empty');
}

async function analyzeOffer() {
  if (analysisInProgress) return;

  const offerText   = document.getElementById('offerText').value.trim();
  const companyName = document.getElementById('companyName').value.trim();
  const url         = document.getElementById('urlInput').value.trim();
  const skipScraping = document.getElementById('skipScraping').checked;

  if (!offerText) {
    const textarea = document.getElementById('offerText');
    textarea.style.borderColor = 'var(--danger)';
    textarea.style.animation = 'fieldShake 0.4s ease';
    setTimeout(() => {
      textarea.style.borderColor = '';
      textarea.style.animation = '';
    }, 700);
    return;
  }

  setLoading(true);
  showState('loading');
  animateLoadingSteps(skipScraping);

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        offer_text: offerText,
        company_name: companyName,
        url: url,
        skip_scraping: skipScraping
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      throw new Error(err.error || `Server returned ${res.status}`);
    }

    const data = await res.json();
    if (data.error) throw new Error(data.error);

    renderResults(data);
    showState('results');

  } catch (err) {
    showState('empty');
    alert('Analysis failed: ' + (err.message || 'Unknown error. Is the Flask server running?'));
  } finally {
    setLoading(false);
  }
}

function renderResults(data) {
  const isFraud = data.is_fraud;
  const conf = data.confidence_percent;
  const fraudPct = (data.combined_fraud_probability * 100).toFixed(1) + '%';
  const scores = data.component_scores;

  // verdict bar
  const verdictBar = document.getElementById('verdictBar');
  verdictBar.className = 'verdict-bar ' + (isFraud ? 'fraud' : 'legit');
  document.getElementById('verdictStatus').textContent = isFraud ? 'FRAUD DETECTED' : 'LOOKS LEGITIMATE';
  document.getElementById('verdictSub').textContent = conf + '% confidence in this verdict';
  document.getElementById('verdictScore').textContent = fraudPct;

  // score cards
  renderScoreBar('ml', scores.ml_fraud_probability, true);
  renderScoreBar('agent', 1 - scores.agent_legitimacy, true);   // invert: legitimacy -> fraud risk
  renderScoreBar('company', 1 - scores.company_legitimacy, true);
  renderScoreBar('url', 1 - scores.url_safety, true);

  // agent log
  const terminal = document.getElementById('agentTerminal');
  const logs = data.agent?.agent_log || [];

  if (logs.length > 0) {
    terminal.innerHTML = logs.map(entry => {
      const level = entry.level || 'info';
      return `<div class="log-line ${level}">
        <span class="log-time">[${entry.time}]</span>
        <span class="log-msg">${escHtml(entry.message)}</span>
      </div>`;
    }).join('');
    // scroll to bottom
    terminal.scrollTop = terminal.scrollHeight;
  } else {
    terminal.innerHTML = '<div class="terminal-placeholder">Web agent was not run (fast mode).</div>';
  }

  // agent stats
  const stats = data.agent?.stats || {};
  if (stats.positive !== undefined) {
    document.getElementById('agentStats').textContent =
      `+${stats.positive} positive  -${stats.negative} negative  ~${stats.neutral} neutral`;
  }

  // agent findings
  const findingsList = document.getElementById('findingsList');
  const findings = data.agent?.findings || [];
  if (findings.length > 0) {
    findingsList.innerHTML = findings.map(f => {
      let badgeClass, badgeText;
      if (f.positive === true) {
        badgeClass = 'badge-positive';
        badgeText = 'Pass';
      } else if (f.positive === false && !f.neutral) {
        badgeClass = 'badge-negative';
        badgeText = 'Fail';
      } else {
        badgeClass = 'badge-neutral';
        badgeText = 'Neutral';
      }
      return `<div class="finding-row">
        <span class="finding-label">${escHtml(f.label)}</span>
        <span class="finding-detail">${escHtml(f.detail)}</span>
        <span class="finding-badge ${badgeClass}">${badgeText}</span>
      </div>`;
    }).join('');
  } else {
    findingsList.innerHTML = '';
  }

  // company detail
  const comp = data.company;
  document.getElementById('d-company-name').textContent = comp.name || 'Not detected';
  document.getElementById('d-company-reason').textContent = comp.reason;
  const compChip = document.getElementById('d-company-chip');
  compChip.textContent = comp.status;
  compChip.className = 'status-chip chip-' + comp.status;

  // url detail
  const urlData = data.url;
  document.getElementById('d-url-name').textContent = urlData.value || 'Not found';
  document.getElementById('d-url-reason').textContent = urlData.reason;
  const urlChip = document.getElementById('d-url-chip');
  urlChip.textContent = urlData.status;
  urlChip.className = 'status-chip chip-' + urlData.status;

  // reasoning
  const reasoningList = document.getElementById('reasoningList');
  reasoningList.innerHTML = (data.explanations || []).map(e =>
    `<div class="reasoning-item">${escHtml(e)}</div>`
  ).join('');

  // text signals
  const fraudKws = data.text_signals?.fraud_keywords || [];
  const legitSigs = data.text_signals?.legit_signals || [];

  const fraudBlock = document.getElementById('fraudSignalsBlock');
  const legitBlock = document.getElementById('legitSignalsBlock');

  if (fraudKws.length > 0) {
    fraudBlock.classList.remove('hidden');
    document.getElementById('fraudTags').innerHTML =
      fraudKws.map(k => `<span class="signal-tag tag-fraud">${escHtml(k)}</span>`).join('');
  } else {
    fraudBlock.classList.add('hidden');
  }

  if (legitSigs.length > 0) {
    legitBlock.classList.remove('hidden');
    document.getElementById('legitTags').innerHTML =
      legitSigs.map(k => `<span class="signal-tag tag-legit">${escHtml(k)}</span>`).join('');
  } else {
    legitBlock.classList.add('hidden');
  }
}

function renderScoreBar(key, fraudRisk, animate) {
  const pct = Math.round(fraudRisk * 100);
  const bar = document.getElementById('bar-' + key);
  const val = document.getElementById('val-' + key);

  let colorClass;
  if (fraudRisk >= 0.65) colorClass = 'bar-danger';
  else if (fraudRisk >= 0.4) colorClass = 'bar-warn';
  else colorClass = 'bar-success';

  bar.className = 'sc-bar ' + colorClass;
  val.textContent = pct + '%';
  val.style.color = fraudRisk >= 0.5 ? 'var(--danger)' : 'var(--success)';

  if (animate) {
    setTimeout(() => { bar.style.width = pct + '%'; }, 150);
  } else {
    bar.style.width = pct + '%';
  }
}

function showState(state) {
  document.getElementById('emptyState').classList.toggle('hidden', state !== 'empty');
  document.getElementById('loadingState').classList.toggle('hidden', state !== 'loading');
  document.getElementById('resultsContainer').classList.toggle('hidden', state !== 'results');
}

function setLoading(active) {
  analysisInProgress = active;
  const btn = document.getElementById('analyzeBtn');
  const loader = document.getElementById('btnLoader');
  btn.disabled = active;
  loader.classList.toggle('show', active);
  document.querySelector('.run-btn-text').textContent = active ? 'Analyzing...' : 'Run Analysis';
}

function animateLoadingSteps(skipScraping) {
  const steps = ['step-ml', 'step-company', 'step-url', 'step-agent'];
  const delays = [0, 600, 1100, 1600];

  steps.forEach(id => {
    const el = document.getElementById(id);
    el.className = 'load-step';
  });

  steps.forEach((id, i) => {
    if (skipScraping && id === 'step-agent') {
      setTimeout(() => {
        document.getElementById(id).className = 'load-step';
      }, delays[i]);
      return;
    }
    setTimeout(() => {
      // mark previous as done
      if (i > 0) {
        document.getElementById(steps[i - 1]).className = 'load-step done';
      }
      document.getElementById(id).className = 'load-step active';
    }, delays[i]);
  });
}

function resetUI() {
  document.getElementById('offerText').value = '';
  document.getElementById('companyName').value = '';
  document.getElementById('urlInput').value = '';
  document.getElementById('charCount').textContent = '0 characters';
  showState('empty');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
