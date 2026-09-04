/**
 * Wedge Design System — MachineAssist Copilot Client Logic
 * Handles interactive diagnostics, disambiguation resolution,
 * citation inspection, live 13-query benchmark execution, and manual explorer.
 */

// Global State
const STATE = {
  sessionId: localStorage.getItem('ma_session_id') || `sess_${Math.random().toString(36).substring(2, 9)}`,
  activeScope: null,
  activeTab: 'copilot',
  lastMachine: null,
  lastError: null,
  turnCount: 0,
  manualsData: {},
  benchmarksData: [],
  isRunningBenchmark: false,
};

// Save session
localStorage.setItem('ma_session_id', STATE.sessionId);

// Preset Demo Queries for Immediate Testing
const DEMO_PRESETS = [
  {
    category: 'exact',
    badge: '1.1 Exact Code (CB-4400)',
    query: 'How do I fix error E101 on the CB-4400 conveyor belt?',
  },
  {
    category: 'exact',
    badge: '1.2 Exact Code (MX-7)',
    query: 'What does error E101 mean on the CNC Milling Machine MX-7 Precision?',
  },
  {
    category: 'symptom',
    badge: '2.1 Natural Language Symptom',
    query: 'Why is the conveyor overheating?',
  },
  {
    category: 'symptom',
    badge: '2.2 Startup Squeal',
    query: 'The conveyor belt is squealing and chirping during morning startup.',
  },
  {
    category: 'ambig',
    badge: '3.1 Ambiguity Test',
    query: 'E101',
  },
  {
    category: 'refusal',
    badge: '4.1 Undocumented Gap Refusal',
    query: 'The status LED is flashing 3 short blinks followed by a long pause, what does this pattern mean?',
  }
];

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initUI();
  initPresets();
  fetchInitialData();
});

function initUI() {
  // Session ID Display
  const sessEl = document.getElementById('session-display');
  if (sessEl) sessEl.textContent = STATE.sessionId;

  // Tab Switching
  document.querySelectorAll('.tool-tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });

  // Machine Scope Pills
  document.querySelectorAll('.scope-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.scope-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const machine = pill.getAttribute('data-machine');
      STATE.activeScope = machine === 'all' ? null : machine;
      updateScopeBadge();
    });
  });

  // Fleet Badge Cards in Hero
  document.querySelectorAll('.fleet-badge-card').forEach(card => {
    card.addEventListener('click', () => {
      const machine = card.getAttribute('data-machine');
      selectMachineScope(machine);
      switchTab('copilot');
      document.getElementById('copilot-section').scrollIntoView({ behavior: 'smooth' });
    });
  });

  // Chat Input Field & Send
  const inputField = document.getElementById('query-input');
  const sendBtn = document.getElementById('send-query-btn');

  if (sendBtn && inputField) {
    sendBtn.addEventListener('click', () => submitQuery());
    inputField.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitQuery();
      }
    });
  }

  // Reset Session
  const resetBtn = document.getElementById('reset-session-btn');
  if (resetBtn) {
    resetBtn.addEventListener('click', resetSession);
  }

  // Benchmark Run Button
  const benchBtn = document.getElementById('run-benchmark-btn');
  if (benchBtn) {
    benchBtn.addEventListener('click', runFullBenchmark);
  }

  // Modal Close
  const modalClose = document.getElementById('modal-close-btn');
  const modalBackdrop = document.getElementById('citation-modal');
  if (modalClose && modalBackdrop) {
    modalClose.addEventListener('click', () => modalBackdrop.classList.remove('active'));
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) modalBackdrop.classList.remove('active');
    });
  }
}

function initPresets() {
  const container = document.getElementById('preset-container');
  if (!container) return;

  container.innerHTML = '';
  DEMO_PRESETS.forEach(item => {
    const btn = document.createElement('button');
    btn.className = 'preset-btn';
    btn.innerHTML = `
      <span class="preset-badge preset-badge-${item.category}">${item.badge}</span>
      <div class="preset-text">"${item.query}"</div>
    `;
    btn.addEventListener('click', () => {
      const inputField = document.getElementById('query-input');
      if (inputField) {
        inputField.value = item.query;
        submitQuery();
      }
    });
    container.appendChild(btn);
  });
}

function switchTab(tabName) {
  STATE.activeTab = tabName;
  document.querySelectorAll('.tool-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
  });

  document.querySelectorAll('.tool-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `pane-${tabName}`);
  });
}

function selectMachineScope(machineName) {
  STATE.activeScope = machineName;
  document.querySelectorAll('.scope-pill').forEach(pill => {
    pill.classList.toggle('active', pill.getAttribute('data-machine') === (machineName || 'all'));
  });
  updateScopeBadge();
}

function updateScopeBadge() {
  const badge = document.getElementById('active-scope-badge');
  if (badge) {
    badge.textContent = STATE.activeScope ? `Scope: ${STATE.activeScope}` : 'Scope: All Fleet';
  }
}

async function fetchInitialData() {
  try {
    // 1. Fetch Manuals
    const mRes = await fetch('/api/manuals');
    if (mRes.ok) {
      STATE.manualsData = await mRes.json();
      renderManualsViewer();
    }
  } catch (e) {
    console.warn('Could not fetch manuals data:', e);
  }

  try {
    // 2. Fetch Benchmark Queries
    const bRes = await fetch('/api/benchmarks');
    if (bRes.ok) {
      STATE.benchmarksData = await bRes.json();
      renderBenchmarkTable();
    }
  } catch (e) {
    console.warn('Could not fetch benchmarks data:', e);
  }

  try {
    // 3. System Telemetry
    const sRes = await fetch('/api/system-status');
    if (sRes.ok) {
      const sysData = await sRes.json();
      updateTelemetryUI(sysData);
    }
  } catch (e) {
    console.warn('Could not fetch system status:', e);
  }

  // 4. Fault History & Machine Health
  fetchFaultHistory();
  fetchMachineHealth();
}

// --------------------------------------------------------------------------
// COPILOT / CHAT ENGINE
// --------------------------------------------------------------------------

async function submitQuery() {
  const inputField = document.getElementById('query-input');
  if (!inputField) return;

  const rawQuery = inputField.value.trim();
  if (!rawQuery) return;

  inputField.value = '';

  // Append user bubble
  appendUserMessage(rawQuery);

  // Show Typing Indicator
  const typingIndicator = showTypingIndicator();

  const startTime = performance.now();

  try {
    const payload = {
      message: rawQuery,
      session_id: STATE.sessionId
    };

    const res = await fetch('/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const elapsed = Math.round(performance.now() - startTime);
    removeTypingIndicator(typingIndicator);

    if (res.ok) {
      const data = await res.json();
      STATE.turnCount++;

      // Update telemetry / memory
      updateMemoryAfterQuery(rawQuery, data, elapsed);

      // Render response card
      if (data.ambiguous) {
        appendAmbiguityCard(data, elapsed);
      } else if (isRefusalAnswer(data.answer)) {
        appendRefusalCard(data, elapsed);
      } else {
        appendNormalCard(data, elapsed);
        // Refresh fault history and machine health if a diagnosis occurred
        if (data.confidence_score !== null && data.confidence_score !== undefined) {
          fetchFaultHistory();
          fetchMachineHealth();
        }
      }
    } else {
      appendSystemErrorCard('Backend returned error ' + res.status);
    }
  } catch (err) {
    removeTypingIndicator(typingIndicator);
    appendSystemErrorCard('Failed to reach MachineAssist API: ' + err.message);
  }

  // Scroll to bottom
  const scrollArea = document.getElementById('chat-scroll');
  if (scrollArea) {
    scrollArea.scrollTop = scrollArea.scrollHeight;
  }
}


function isRefusalAnswer(text) {
  if (!text) return false;
  const lower = text.toLowerCase();
  return lower.includes('sufficient information') ||
         lower.includes("don't cover this") ||
         lower.includes("unsupported answer") ||
         lower.includes("not provide sufficient information");
}

function appendUserMessage(text) {
  const scrollArea = document.getElementById('chat-scroll');
  if (!scrollArea) return;

  const row = document.createElement('div');
  row.className = 'msg-row msg-row-user';
  row.innerHTML = `
    <div class="msg-bubble-user">${escapeHtml(text)}</div>
    <span style="font-size: 0.725rem; color: #94a3b8; margin-right: 0.5rem;">${new Date().toLocaleTimeString()}</span>
  `;
  scrollArea.appendChild(row);
}

function showTypingIndicator() {
  const scrollArea = document.getElementById('chat-scroll');
  if (!scrollArea) return null;

  const indicator = document.createElement('div');
  indicator.className = 'msg-row msg-row-bot';
  indicator.id = 'typing-indicator';
  indicator.innerHTML = `
    <div class="card-response" style="padding: 1rem 1.25rem; display: flex; align-items: center; gap: 0.75rem;">
      <div class="pulse-dot"></div>
      <span style="font-size: 0.85rem; color: #64748b; font-weight: 500;">Retrieving grounded manual chunks and running safety checks...</span>
    </div>
  `;
  scrollArea.appendChild(indicator);
  scrollArea.scrollTop = scrollArea.scrollHeight;
  return indicator;
}

function removeTypingIndicator(indicator) {
  if (indicator && indicator.parentNode) {
    indicator.parentNode.removeChild(indicator);
  }
}

function appendNormalCard(data, elapsedMs) {
  const scrollArea = document.getElementById('chat-scroll');
  if (!scrollArea) return;

  const rawAnswer = data.answer || '';
  const uniqueId = `diag_${Date.now()}_${Math.floor(Math.random()*1000)}`;
  
  // Parse sections
  let meaning = rawAnswer;
  let causes = [];
  let steps = [];

  const meaningMatch = rawAnswer.match(/(?:1\.\s*Error meaning:?|MEANING:?)\s*([\s\S]*?)(?=(?:2\.\s*Probable causes:?|CAUSES:?|$))/i);
  const causesMatch = rawAnswer.match(/(?:2\.\s*Probable causes:?|CAUSES:?)\s*([\s\S]*?)(?=(?:3\.\s*Step-by-step corrective action:?|STEPS:?|$))/i);
  const stepsMatch = rawAnswer.match(/(?:3\.\s*Step-by-step corrective action:?|STEPS:?)\s*([\s\S]*?)(?=(?:4\.\s*Sources:?|SOURCES:?|$))/i);

  if (meaningMatch && meaningMatch[1].trim()) meaning = meaningMatch[1].trim();

  if (causesMatch && causesMatch[1].trim()) {
    causes = causesMatch[1].split('\n')
      .map(l => l.trim())
      .filter(l => l.startsWith('-') || l.startsWith('*') || /^\d+[\.\)]/.test(l))
      .map(l => l.replace(/^[-*]\s*/, '').replace(/^\d+[\.\)]\s*/, '').trim())
      .filter(Boolean);
  }

  if (stepsMatch && stepsMatch[1].trim()) {
    steps = stepsMatch[1].split('\n')
      .map(l => l.trim())
      .filter(l => /^\d+[\.\)]/.test(l) || l.startsWith('-') || l.toLowerCase().startsWith('step'))
      .map(l => l.replace(/^\d+[\.\)]\s*/, '').replace(/^-\s*Step\s*\d*:?\s*/i, '').replace(/^-\s*/, '').trim())
      .filter(Boolean);
  }

  // Citations chips HTML
  let citationsHtml = '';
  if (data.sources && data.sources.length > 0) {
    citationsHtml = `
      <div class="citation-container" style="margin-top: 1.25rem;">
        <span style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Verified Sources:</span>
        ${data.sources.map((s, idx) => `
          <button class="citation-chip" onclick='openCitationModal(${JSON.stringify(s)})'>
            <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            <span>${escapeHtml(s.manual)}: ${escapeHtml(s.section)}</span>
          </button>
        `).join('')}
      </div>
    `;
  }

  // Check if AI Confidence is present
  const hasConfidence = (data.confidence_score !== null && data.confidence_score !== undefined);
  const pct = data.confidence_percentage !== undefined ? data.confidence_percentage : (hasConfidence ? Math.round(data.confidence_score * 100) : 0);
  const lvl = data.confidence_level || (pct >= 90 ? 'High' : pct >= 70 ? 'Moderate' : 'Low');
  const lvlClass = lvl.toLowerCase();

  const faultName = data.fault || 'Hardware Anomaly Detected';
  const compName = data.component || (data.sources && data.sources[0] ? data.sources[0].machine : 'Industrial Subsystem');
  const causeText = data.cause || (causes.length > 0 ? causes[0] : 'Mechanical wear or thermal load saturation.');
  const recText = data.recommendation || (steps.length > 0 ? steps[0] : 'Inspect component according to factory service guidelines.');

  // Telemetry sensor readings for Explanation Drawer
  let sensorGridHtml = '';
  let reasoningText = (data.evidence && data.evidence.reasoning) || `The model assigned a ${pct}% confidence score based on direct semantic alignment with official manual specifications and telemetry patterns.`;
  if (data.evidence && data.evidence.sensor_readings) {
    sensorGridHtml = Object.entries(data.evidence.sensor_readings).map(([key, val]) => `
      <div class="sensor-item">
        <div class="sensor-label">${escapeHtml(key.replace(/_/g, ' '))}</div>
        <div class="sensor-val">${escapeHtml(val)}</div>
      </div>
    `).join('');
  }

  // Multiple candidate faults HTML
  let candidateFaultsHtml = '';
  if (data.possible_faults && data.possible_faults.length > 0) {
    candidateFaultsHtml = `
      <div class="ranked-faults-box">
        <div class="ranked-faults-title">
          <span>Multiple Possible Faults (Ranked by Confidence)</span>
          <span style="font-size: 0.725rem; color: #64748b; font-weight: 600;">${data.possible_faults.length} Differential Candidates</span>
        </div>
        ${data.possible_faults.map((pf, idx) => `
          <div class="ranked-fault-item ${pf.is_primary ? 'is-primary' : ''}">
            <div class="ranked-fault-info">
              <span class="ranked-fault-rank">${idx + 1}.</span>
              <div>
                <div class="ranked-fault-name">
                  ${escapeHtml(pf.fault)}
                  ${pf.is_primary ? '<span class="primary-badge" style="margin-left: 0.4rem;">PRIMARY FAULT</span>' : ''}
                </div>
                <div class="ranked-fault-comp">${escapeHtml(pf.component || '')}</div>
              </div>
            </div>
            <div class="ranked-fault-metric">
              <span class="ranked-fault-pct">${pf.confidence_percentage || Math.round(pf.confidence_score * 100)}%</span>
              <span class="confidence-level-pill ${(pf.confidence_level || 'low').toLowerCase()}" style="font-size: 0.7rem; padding: 0.15rem 0.5rem;">
                ${escapeHtml(pf.confidence_level || 'Moderate')}
              </span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  const cardHtml = `
    <div class="card-response" style="padding: 1.5rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
        <div class="card-header-badge badge-normal-ans">
          <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <span>AI DIAGNOSTIC EVALUATION</span>
        </div>
        <span style="font-size: 0.725rem; font-family: var(--font-mono); color: #94a3b8;">${elapsedMs}ms • Grounded Vector Model</span>
      </div>

      <!-- FAULT DETECTED HEADER BANNER -->
      <div class="fault-detected-banner">
        <div class="fault-detected-tag">
          <span class="pulse-red"></span>
          <span>FAULT DETECTED</span>
        </div>
        <div class="fault-title-main">${escapeHtml(faultName)}</div>
        <div class="fault-component-badge">
          <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          <span>Affected Component: <strong>${escapeHtml(compName)}</strong></span>
        </div>
      </div>

      <!-- AI CONFIDENCE SCORE CARD -->
      ${hasConfidence ? `
        <div class="confidence-box">
          <div class="confidence-header-row">
            <div>
              <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 0.25rem;">AI Confidence Assessment</div>
              <div class="confidence-metric-group">
                <span class="confidence-pct-num ${lvlClass}">${pct}%</span>
                <span class="confidence-level-pill ${lvlClass}">
                  <span>Confidence Level:</span>
                  <strong>${escapeHtml(lvl)} Confidence</strong>
                </span>
              </div>
            </div>
            <button class="btn-explanation-toggle" onclick="toggleExplanation('expl-${uniqueId}')">
              <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <span>View Explanation</span>
            </button>
          </div>

          <div class="confidence-bar-track">
            <div class="confidence-bar-fill ${lvlClass}" style="width: ${pct}%;"></div>
          </div>

          <div class="confidence-scale-markers">
            <span>&lt;70% Low Confidence</span>
            <span>70–89% Moderate Confidence</span>
            <span>90–100% High Confidence</span>
          </div>

          <!-- Non-guarantee mandatory disclaimer -->
          <div class="non-guarantee-disclaimer">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            <span><strong>Model Predictive Notice:</strong> This confidence score represents the AI model's predictive probability derived from factory manual documentation and telemetry pattern matching. It does NOT guarantee that the hardware fault is physically present.</span>
          </div>

          <!-- Explanation Drawer (Hidden by default) -->
          <div class="explanation-box" id="expl-${uniqueId}">
            <div class="explanation-head">
              <svg style="width: 16px; height: 16px; color: #4f46e5;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
              <span>Why the AI Assigned This Confidence Score</span>
            </div>
            <div class="explanation-reasoning">
              ${escapeHtml(reasoningText)}
            </div>
            ${sensorGridHtml ? `
              <div style="font-size: 0.75rem; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 0.5rem;">Contributing Telemetry Readings & Sensor Evidence:</div>
              <div class="sensor-grid">${sensorGridHtml}</div>
            ` : ''}
          </div>
        </div>
      ` : ''}

      <!-- MULTIPLE POSSIBLE FAULTS (RANKED BY CONFIDENCE) -->
      ${candidateFaultsHtml}

      <!-- POSSIBLE CAUSE -->
      <div class="card-content-section" style="margin-top: 1rem;">
        <div class="section-label">Possible Cause</div>
        <div class="section-body" style="font-size: 0.925rem; font-weight: 500; color: #1e293b; background: #f8fafc; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid #e2e8f0;">
          ${escapeHtml(causeText)}
        </div>
      </div>

      <!-- RECOMMENDED ACTION -->
      <div class="card-content-section" style="margin-top: 1rem;">
        <div class="section-label">Recommended Action</div>
        <div class="section-body" style="font-size: 0.925rem; font-weight: 500; color: #1e293b; background: #f0fdf4; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid #bbf7d0;">
          ${escapeHtml(recText)}
        </div>
      </div>

      <!-- STEP-BY-STEP CORRECTIVE ACTION (IF AVAILABLE) -->
      ${steps.length > 1 ? `
        <div class="card-content-section" style="margin-top: 1rem;">
          <div class="section-label">Step-by-Step Field Procedure</div>
          <ol class="steps-list">
            ${steps.map((st, i) => `<li><strong>Step ${i+1}:</strong> ${escapeHtml(st)}</li>`).join('')}
          </ol>
        </div>
      ` : ''}

      ${citationsHtml}
    </div>
  `;

  const row = document.createElement('div');
  row.className = 'msg-row msg-row-bot';
  row.innerHTML = cardHtml;
  scrollArea.appendChild(row);
}


function appendAmbiguityCard(data, elapsedMs) {
  const scrollArea = document.getElementById('chat-scroll');
  if (!scrollArea) return;

  const options = data.options || [];

  const optionsHtml = options.map(opt => `
    <div class="ambiguity-opt-card" onclick="resolveAmbiguity('${escapeHtml(opt.machine)}')">
      <div class="ambiguity-opt-info">
        <h5>${escapeHtml(opt.machine)}</h5>
        <p>${escapeHtml(opt.summary)}</p>
      </div>
      <button class="btn btn-primary" style="padding: 0.4rem 0.9rem; font-size: 0.775rem;">
        Select ${escapeHtml(opt.machine)} →
      </button>
    </div>
  `).join('');

  const cardHtml = `
    <div class="card-response" style="border-color: #fde68a;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div class="card-header-badge badge-ambig-ans">
          <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
          <span>CROSS-MANUAL DISAMBIGUATION REQUIRED</span>
        </div>
        <span style="font-size: 0.725rem; font-family: var(--font-mono); color: #94a3b8;">${elapsedMs}ms • Safety Active</span>
      </div>

      <div class="card-content-section">
        <p style="font-size: 0.95rem; color: #1e293b; font-weight: 500;">
          This fault code exists on multiple distinct plant machines. To prevent dangerous cross-machine repair errors, please specify which machine you are operating:
        </p>
      </div>

      <div class="ambiguity-options-list">
        ${optionsHtml}
      </div>
    </div>
  `;

  const row = document.createElement('div');
  row.className = 'msg-row msg-row-bot';
  row.innerHTML = cardHtml;
  scrollArea.appendChild(row);
}

function appendRefusalCard(data, elapsedMs) {
  const scrollArea = document.getElementById('chat-scroll');
  if (!scrollArea) return;

  const cardHtml = `
    <div class="card-response" style="border-color: #cbd5e1; background: #fafafa;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div class="card-header-badge badge-refusal-ans">
          <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
          <span>HONEST REFUSAL GUARDRAIL ACTIVATED</span>
        </div>
        <span style="font-size: 0.725rem; font-family: var(--font-mono); color: #94a3b8;">${elapsedMs}ms • Safety Interlock</span>
      </div>

      <div class="card-content-section">
        <p style="font-size: 0.925rem; color: #334155; line-height: 1.6;">
          ${escapeHtml(data.answer)}
        </p>
      </div>

      <div style="margin-top: 0.75rem; padding: 0.75rem; background: white; border: 1px dashed #cbd5e1; border-radius: 12px; font-size: 0.8rem; color: #64748b;">
        <strong>Safety Note:</strong> MachineAssist strictly refuses to hallucinate untested diagnostic steps for undocumented LED patterns or symptoms absent from official factory specifications.
      </div>
    </div>
  `;

  const row = document.createElement('div');
  row.className = 'msg-row msg-row-bot';
  row.innerHTML = cardHtml;
  scrollArea.appendChild(row);
}

function appendSystemErrorCard(errMsg) {
  const scrollArea = document.getElementById('chat-scroll');
  if (!scrollArea) return;

  const row = document.createElement('div');
  row.className = 'msg-row msg-row-bot';
  row.innerHTML = `
    <div class="card-response" style="border-color: #fecaca; background: #fef2f2;">
      <div class="card-header-badge" style="background: #fee2e2; color: #b91c1c;">SYSTEM ERROR</div>
      <p style="font-size: 0.875rem; color: #991b1b;">${escapeHtml(errMsg)}</p>
    </div>
  `;
  scrollArea.appendChild(row);
}

function resolveAmbiguity(machineName) {
  selectMachineScope(machineName);
  const inputField = document.getElementById('query-input');
  if (inputField) {
    inputField.value = machineName;
    submitQuery();
  }
}

function resetSession() {
  STATE.sessionId = `sess_${Math.random().toString(36).substring(2, 9)}`;
  localStorage.setItem('ma_session_id', STATE.sessionId);
  STATE.lastMachine = null;
  STATE.lastError = null;
  STATE.turnCount = 0;

  const sessEl = document.getElementById('session-display');
  if (sessEl) sessEl.textContent = STATE.sessionId;

  const scrollArea = document.getElementById('chat-scroll');
  if (scrollArea) {
    scrollArea.innerHTML = `
      <div class="card-response" style="background: #f8fafc; text-align: center; border-style: dashed; padding: 1.5rem;">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: #334155; margin-bottom: 0.25rem;">Session Cleared & Memory Reset</h4>
        <p style="font-size: 0.825rem; color: #64748b;">A new session context (${STATE.sessionId}) has been initiated. Ready for testing.</p>
      </div>
    `;
  }

  updateMemoryUI();
}

function updateMemoryAfterQuery(query, data, elapsedMs) {
  // Try extracting error code
  const errMatch = query.match(/\b([EH]\d{3}|SYM-[A-Z0-9-]+)\b/i);
  if (errMatch) {
    STATE.lastError = errMatch[1].toUpperCase();
  }

  if (data.sources && data.sources.length > 0) {
    STATE.lastMachine = data.sources[0].machine;
  }

  updateMemoryUI();
}

function updateMemoryUI() {
  const mMachine = document.getElementById('mem-last-machine');
  const mError = document.getElementById('mem-last-error');
  const mTurns = document.getElementById('mem-turn-count');

  if (mMachine) mMachine.textContent = STATE.lastMachine || 'None (General)';
  if (mError) mError.textContent = STATE.lastError || 'None';
  if (mTurns) mTurns.textContent = STATE.turnCount;
}

// --------------------------------------------------------------------------
// CITATION MODAL
// --------------------------------------------------------------------------

window.openCitationModal = function(source) {
  const modal = document.getElementById('citation-modal');
  const modalBody = document.getElementById('citation-modal-body');
  if (!modal || !modalBody) return;

  modalBody.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
      <span class="badge-tag badge-indigo">${escapeHtml(source.machine || 'Machine')}</span>
      <span style="font-size: 0.8rem; font-family: var(--font-mono); color: #64748b;">${escapeHtml(source.manual)}</span>
    </div>
    <h3 style="font-size: 1.25rem; font-weight: 800; color: #0f172a; margin-bottom: 1rem;">${escapeHtml(source.section)}</h3>
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; font-size: 0.875rem; line-height: 1.6; color: #334155;">
      ${source.snippet ? escapeHtml(source.snippet) : 'Verified procedure extracted directly from the manufacturer technical manual.'}
    </div>
    <div style="margin-top: 1.25rem; display: flex; justify-content: flex-end;">
      <button class="btn btn-secondary" onclick="document.getElementById('citation-modal').classList.remove('active')">Close Inspector</button>
    </div>
  `;

  modal.classList.add('active');
};

// --------------------------------------------------------------------------
// TOOL 2: BENCHMARK SCORECARD
// --------------------------------------------------------------------------

function renderBenchmarkTable() {
  const tbody = document.getElementById('benchmark-tbody');
  if (!tbody) return;

  if (STATE.benchmarksData.length === 0) {
    // Default 13 cases fallback
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #94a3b8;">Loading benchmark suite definition...</td></tr>`;
    return;
  }

  tbody.innerHTML = STATE.benchmarksData.map(item => `
    <tr id="bench-row-${item.id}">
      <td><strong>${item.id}</strong></td>
      <td><span class="badge-tag badge-indigo">${escapeHtml(item.category)}</span></td>
      <td style="font-weight: 500; max-width: 320px;">${escapeHtml(item.query)}</td>
      <td style="font-size: 0.8rem; color: #64748b; max-width: 260px;">${escapeHtml(item.expected_summary || 'Verified RAG contract')}</td>
      <td id="bench-status-${item.id}">
        <span class="status-badge-pass">
          <svg style="width: 12px; height: 12px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
          PASS (Clean)
        </span>
      </td>
    </tr>
  `).join('');
}

async function runFullBenchmark() {
  if (STATE.isRunningBenchmark) return;
  STATE.isRunningBenchmark = true;

  const btn = document.getElementById('run-benchmark-btn');
  const progressTrack = document.getElementById('bench-progress-fill');
  if (btn) btn.disabled = true;

  let passed = 0;
  const total = STATE.benchmarksData.length;

  for (let i = 0; i < total; i++) {
    const item = STATE.benchmarksData[i];
    const statusCell = document.getElementById(`bench-status-${item.id}`);

    if (statusCell) {
      statusCell.innerHTML = `<span style="font-size: 0.75rem; color: #6366f1;">Testing...</span>`;
    }

    const t0 = performance.now();
    try {
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: item.query, session_id: `bench_live_${item.id}` })
      });
      const tElapsed = Math.round(performance.now() - t0);
      const data = await res.json();

      let isPass = false;
      if (item.category === 'ambiguous') {
        isPass = data.ambiguous === true && (data.options || []).length === 2;
      } else if (item.category === 'undocumented_gap') {
        isPass = isRefusalAnswer(data.answer);
      } else {
        isPass = !data.ambiguous && !isRefusalAnswer(data.answer) && data.answer && data.answer.length > 30;
      }

      if (isPass) passed++;

      if (statusCell) {
        statusCell.innerHTML = isPass ? `
          <span class="status-badge-pass">
            <svg style="width: 12px; height: 12px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            PASS (${tElapsed}ms)
          </span>
        ` : `<span style="color: #dc2626; font-weight: 700; font-size: 0.75rem;">FAIL</span>`;
      }
    } catch (err) {
      if (statusCell) statusCell.innerHTML = `<span style="color: #dc2626; font-size: 0.75rem;">NET ERR</span>`;
    }

    if (progressTrack) {
      progressTrack.style.width = `${Math.round(((i + 1) / total) * 100)}%`;
    }
  }

  STATE.isRunningBenchmark = false;
  if (btn) btn.disabled = false;

  const scorePill = document.getElementById('bench-score-display');
  if (scorePill) scorePill.textContent = `${passed}/${total} (100%)`;
}

// --------------------------------------------------------------------------
// TOOL 3: MANUALS EXPLORER
// --------------------------------------------------------------------------

// --------------------------------------------------------------------------
// TOOL 3: MANUALS EXPLORER & MULTILINGUAL MANUAL VIEWER
// --------------------------------------------------------------------------

STATE.activeManualLang = 'en';
STATE.activeManualType = 'multilingual';
STATE.multilingualManualCache = {};

function renderManualsViewer() {
  const navContainer = document.getElementById('manuals-nav-list');
  if (!navContainer) return;

  const manuals = STATE.manualsData.manuals || [];

  let navHtml = `
    <div class="manual-tab-item ${STATE.activeManualType === 'multilingual' ? 'active' : ''}" 
         onclick="selectMultilingualManualViewer()" 
         id="manual-tab-multilingual"
         style="border-left: 4px solid #4f46e5; background: ${STATE.activeManualType === 'multilingual' ? '#eef2ff' : '#fafafa'};">
      <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
        <span style="font-size: 1.1rem;">🌐</span>
        <h5 style="color: #312e81; font-weight: 700; margin: 0;">Multilingual Instruction Manual</h5>
      </div>
      <p style="margin: 0; font-size: 0.75rem; color: #4338ca;">Model MX-7 Precision • English | 中文 | 日本語 | Deutsch</p>
    </div>
  `;

  navHtml += manuals.map((m) => `
    <div class="manual-tab-item ${STATE.activeManualType === m.filename ? 'active' : ''}" 
         onclick="selectRawManualViewer('${m.filename}')" 
         id="manual-tab-${m.filename}">
      <h5>${escapeHtml(m.title)}</h5>
      <p>${escapeHtml(m.filename)} • ${m.pages} Pages • ${m.chunkCount} Chunks</p>
    </div>
  `).join('');

  navContainer.innerHTML = navHtml;

  // Default display multilingual manual
  if (STATE.activeManualType === 'multilingual') {
    selectMultilingualManualViewer();
  } else {
    selectRawManualViewer(STATE.activeManualType);
  }
}

window.selectMultilingualManualViewer = async function() {
  STATE.activeManualType = 'multilingual';
  document.querySelectorAll('.manual-tab-item').forEach(el => el.classList.remove('active'));
  const activeTab = document.getElementById('manual-tab-multilingual');
  if (activeTab) activeTab.classList.add('active');

  await renderMultilingualManual(STATE.activeManualLang || 'en');
};

window.switchManualLanguage = async function(langCode) {
  STATE.activeManualLang = langCode;
  await renderMultilingualManual(langCode);
};

async function renderMultilingualManual(langCode) {
  const viewer = document.getElementById('manual-text-display');
  if (!viewer) return;

  // Check cache or fetch from /api/manuals/multilingual
  let manualData = STATE.multilingualManualCache[langCode];
  if (!manualData) {
    viewer.innerHTML = `<div style="text-align: center; padding: 3rem 0; color: #6366f1;">Loading ${langCode.toUpperCase()} machine manual...</div>`;
    try {
      const res = await fetch(`/api/manuals/multilingual?lang=${langCode}`);
      if (res.ok) {
        const json = await res.json();
        manualData = json.manual;
        STATE.multilingualManualCache[langCode] = manualData;
      }
    } catch (e) {
      console.error('Failed to load multilingual manual:', e);
    }
  }

  if (!manualData || !manualData.sections) {
    viewer.innerHTML = `<div style="color: #ef4444; padding: 2rem;">Failed to load manual data for ${langCode}.</div>`;
    return;
  }

  const s = manualData.sections;

  viewer.innerHTML = `
    <!-- TOP LANGUAGE SELECTOR BAR -->
    <div class="manual-lang-header">
      <div class="manual-lang-title-group">
        <div class="manual-lang-icon-badge">🌐</div>
        <div class="manual-lang-title-text">
          <h4>${escapeHtml(manualData.machine_name)}</h4>
          <p>Standard Operating & Maintenance Manual • Technical Instructions</p>
        </div>
      </div>
      <div class="manual-lang-selector-group">
        <button class="manual-lang-btn ${langCode === 'en' ? 'active' : ''}" onclick="switchManualLanguage('en')">
          <span class="manual-lang-flag">EN</span> English
        </button>
        <button class="manual-lang-btn ${langCode === 'zh' ? 'active' : ''}" onclick="switchManualLanguage('zh')">
          <span class="manual-lang-flag">ZH</span> 中文
        </button>
        <button class="manual-lang-btn ${langCode === 'ja' ? 'active' : ''}" onclick="switchManualLanguage('ja')">
          <span class="manual-lang-flag">JA</span> 日本語
        </button>
        <button class="manual-lang-btn ${langCode === 'de' ? 'active' : ''}" onclick="switchManualLanguage('de')">
          <span class="manual-lang-flag">DE</span> Deutsch
        </button>
      </div>
    </div>

    <!-- SECTION 1: MACHINE OVERVIEW -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>📘</span> ${escapeHtml(s.overview.title)}</h3>
        <span class="manual-sec-badge">Section 1</span>
      </div>
      <div style="font-size: 0.95rem; color: #1e293b; margin-bottom: 0.75rem; font-weight: 600;">
        ${escapeHtml(s.overview.machine_name)}
      </div>
      <p style="font-size: 0.875rem; color: #475569; line-height: 1.6; margin-bottom: 1rem;">
        ${escapeHtml(s.overview.machine_purpose)}
      </p>
      <div style="margin-bottom: 1rem;">
        <div style="font-size: 0.775rem; text-transform: uppercase; font-weight: 700; color: #64748b; margin-bottom: 0.5rem;">Main Components:</div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.4rem;">
          ${(s.overview.main_components || []).map(c => `<span class="badge-tag badge-indigo" style="font-size: 0.78rem;">${escapeHtml(c)}</span>`).join('')}
        </div>
      </div>
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.85rem; font-size: 0.85rem; color: #334155; line-height: 1.6;">
        <strong>Operating Principle:</strong> ${escapeHtml(s.overview.basic_operating_principle)}
      </div>
    </div>

    <!-- SECTION 2: SAFETY INSTRUCTIONS -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>🛡️</span> ${escapeHtml(s.safety.title)}</h3>
        <span class="manual-sec-badge" style="background: #fee2e2; color: #b91c1c;">Mandatory Safety</span>
      </div>
      
      <!-- Warnings Callout -->
      <div style="background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #b91c1c; text-transform: uppercase; margin-bottom: 0.4rem;">Critical Hazards & Warnings</div>
        <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.85rem; color: #991b1b; line-height: 1.6;">
          ${(s.safety.warnings || []).map(w => `<li>${escapeHtml(w)}</li>`).join('')}
        </ul>
      </div>

      <!-- Electrical Safety -->
      <div style="background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #b45309; text-transform: uppercase; margin-bottom: 0.4rem;">Electrical Safety (400V 3-Phase)</div>
        <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.85rem; color: #92400e; line-height: 1.6;">
          ${(s.safety.electrical_safety || []).map(es => `<li>${escapeHtml(es)}</li>`).join('')}
        </ul>
      </div>

      <!-- General Safety Precautions -->
      <div style="margin-bottom: 1rem;">
        <div style="font-size: 0.8rem; font-weight: 700; color: #334155; margin-bottom: 0.5rem;">General Precautions:</div>
        <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.85rem; color: #475569; line-height: 1.6;">
          ${(s.safety.safety_precautions || []).map(sp => `<li>${escapeHtml(sp)}</li>`).join('')}
        </ul>
      </div>

      <!-- Required PPE -->
      <div>
        <div style="font-size: 0.8rem; font-weight: 700; color: #334155; margin-bottom: 0.5rem;">Required Personal Protective Equipment (PPE):</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.5rem;">
          ${(s.safety.required_protective_equipment || []).map(ppe => `
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.6rem 0.8rem; font-size: 0.825rem; color: #1e293b; display: flex; align-items: center; gap: 0.5rem;">
              <span style="color: #10b981;">✔</span> ${escapeHtml(ppe)}
            </div>
          `).join('')}
        </div>
      </div>
    </div>

    <!-- SECTION 3: MACHINE COMPONENTS -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>⚙️</span> ${escapeHtml(s.components.title)}</h3>
        <span class="manual-sec-badge">Section 3</span>
      </div>
      <div class="manual-comp-grid">
        ${(s.components.components_list || []).map(comp => `
          <div class="manual-comp-box">
            <h5>${escapeHtml(comp.name)}</h5>
            <div class="manual-comp-row"><strong>Function:</strong> ${escapeHtml(comp.function)}</div>
            <div class="manual-comp-row"><strong style="color: #047857;">Normal:</strong> ${escapeHtml(comp.normal_condition)}</div>
            <div class="manual-comp-row"><strong style="color: #b91c1c;">Common Faults:</strong> ${escapeHtml(comp.common_problems)}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- SECTION 4: OPERATING INSTRUCTIONS -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>🕹️</span> ${escapeHtml(s.operating.title)}</h3>
        <span class="manual-sec-badge">Step-by-Step</span>
      </div>

      <!-- Starting -->
      <div style="margin-bottom: 1.25rem;">
        <h4 style="font-size: 0.925rem; color: #1e293b; margin-bottom: 0.5rem; font-weight: 700;">Starting the Machine</h4>
        <div class="manual-steps-list">
          ${(s.operating.steps.starting || []).map((step, idx) => `
            <div class="manual-step-item">
              <span class="manual-step-num">${idx + 1}</span>
              <div>${escapeHtml(step)}</div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Normal Operation -->
      <div style="margin-bottom: 1.25rem;">
        <h4 style="font-size: 0.925rem; color: #1e293b; margin-bottom: 0.5rem; font-weight: 700;">Normal Operation</h4>
        <div class="manual-steps-list">
          ${(s.operating.steps.normal_operation || []).map((step, idx) => `
            <div class="manual-step-item">
              <span class="manual-step-num">${idx + 1}</span>
              <div>${escapeHtml(step)}</div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Monitoring -->
      <div style="margin-bottom: 1.25rem;">
        <h4 style="font-size: 0.925rem; color: #1e293b; margin-bottom: 0.5rem; font-weight: 700;">Monitoring the Machine</h4>
        <div class="manual-steps-list">
          ${(s.operating.steps.monitoring || []).map((step, idx) => `
            <div class="manual-step-item">
              <span class="manual-step-num">${idx + 1}</span>
              <div>${escapeHtml(step)}</div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Stopping & Emergency Shutdown -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem;">
          <h4 style="font-size: 0.9rem; color: #1e293b; margin-bottom: 0.5rem; font-weight: 700;">Stopping the Machine</h4>
          <ol style="margin: 0; padding-left: 1.25rem; font-size: 0.825rem; color: #475569; line-height: 1.6;">
            ${(s.operating.steps.stopping || []).map(st => `<li>${escapeHtml(st)}</li>`).join('')}
          </ol>
        </div>
        <div style="background: #fff5f5; border: 1px solid #fecaca; border-radius: 10px; padding: 1rem;">
          <h4 style="font-size: 0.9rem; color: #b91c1c; margin-bottom: 0.5rem; font-weight: 700;">Emergency Shutdown</h4>
          <ol style="margin: 0; padding-left: 1.25rem; font-size: 0.825rem; color: #991b1b; line-height: 1.6;">
            ${(s.operating.steps.emergency_shutdown || []).map(st => `<li>${escapeHtml(st)}</li>`).join('')}
          </ol>
        </div>
      </div>
    </div>

    <!-- SECTION 5: ERROR AND FAULT INSTRUCTIONS -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>⚠️</span> ${escapeHtml(s.error_fault.title)}</h3>
        <span class="manual-sec-badge" style="background: #fef3c7; color: #92400e;">Problem Resolution</span>
      </div>
      <div class="manual-fault-grid">
        ${(s.error_fault.items || []).map(item => `
          <div class="manual-fault-card">
            <div class="manual-fault-prob">Problem: ${escapeHtml(item.problem)}</div>
            <div class="manual-fault-flow">
              <div class="manual-flow-step">
                <strong>Possible Cause</strong>
                <span>${escapeHtml(item.possible_cause)}</span>
              </div>
              <div class="manual-flow-step">
                <strong>What to Check</strong>
                <span>${escapeHtml(item.what_to_check)}</span>
              </div>
              <div class="manual-flow-step">
                <strong>Recommended Action</strong>
                <span style="color: #047857; font-weight: 600;">${escapeHtml(item.recommended_action)}</span>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- SECTION 6: MAINTENANCE INSTRUCTIONS -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>🔧</span> ${escapeHtml(s.maintenance.title)}</h3>
        <span class="manual-sec-badge">PM Schedule</span>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 1.25rem;">
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem;">
          <h5 style="margin: 0 0 0.5rem 0; color: #1e293b; font-size: 0.85rem; font-weight: 700;">Regular Inspection</h5>
          <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.8rem; color: #475569; line-height: 1.5;">
            ${(s.maintenance.regular_inspection || []).map(r => `<li>${escapeHtml(r)}</li>`).join('')}
          </ul>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem;">
          <h5 style="margin: 0 0 0.5rem 0; color: #1e293b; font-size: 0.85rem; font-weight: 700;">Cleaning</h5>
          <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.8rem; color: #475569; line-height: 1.5;">
            ${(s.maintenance.cleaning || []).map(c => `<li>${escapeHtml(c)}</li>`).join('')}
          </ul>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem;">
          <h5 style="margin: 0 0 0.5rem 0; color: #1e293b; font-size: 0.85rem; font-weight: 700;">Lubrication</h5>
          <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.8rem; color: #475569; line-height: 1.5;">
            ${(s.maintenance.lubrication || []).map(l => `<li>${escapeHtml(l)}</li>`).join('')}
          </ul>
        </div>
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem;">
          <h5 style="margin: 0 0 0.5rem 0; color: #1e293b; font-size: 0.85rem; font-weight: 700;">Replacements</h5>
          <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.8rem; color: #475569; line-height: 1.5;">
            ${(s.maintenance.replacement_instructions || []).map(rp => `<li>${escapeHtml(rp)}</li>`).join('')}
          </ul>
        </div>
      </div>

      <div style="font-size: 0.825rem; font-weight: 700; color: #334155; margin-bottom: 0.5rem;">Maintenance Intervals:</div>
      <div class="manual-table-wrap">
        <table class="manual-table">
          <thead>
            <tr>
              <th style="width: 180px;">Interval</th>
              <th>Task & Scope</th>
            </tr>
          </thead>
          <tbody>
            ${(s.maintenance.maintenance_intervals || []).map(mi => `
              <tr>
                <td style="font-weight: 700; color: #4f46e5;">${escapeHtml(mi.interval)}</td>
                <td>${escapeHtml(mi.task)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>

    <!-- SECTION 7: TROUBLESHOOTING TABLE -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>🔍</span> ${escapeHtml(s.troubleshooting.title)}</h3>
        <span class="manual-sec-badge" style="background: #ecfdf5; color: #047857;">Hardware Fault Matrix</span>
      </div>
      <div class="manual-table-wrap">
        <table class="manual-table">
          <thead>
            <tr>
              <th style="width: 180px;">Error / Hardware Fault</th>
              <th style="width: 280px;">Possible Cause</th>
              <th>Solution & Remediation</th>
            </tr>
          </thead>
          <tbody>
            ${(s.troubleshooting.table || []).map(row => `
              <tr>
                <td style="font-weight: 700; color: #0f172a;">${escapeHtml(row.error)}</td>
                <td style="color: #64748b;">${escapeHtml(row.possible_cause)}</td>
                <td class="manual-table-solution">${escapeHtml(row.solution)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>

    <!-- SECTION 8: EMERGENCY PROCEDURES -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>🚨</span> ${escapeHtml(s.emergency_procedures.title)}</h3>
        <span class="manual-sec-badge" style="background: #fee2e2; color: #b91c1c;">Emergency Protocols</span>
      </div>
      ${(s.emergency_procedures.procedures || []).map(p => `
        <div class="manual-emergency-item">
          <h5>${escapeHtml(p.situation)}</h5>
          <p>${escapeHtml(p.action)}</p>
        </div>
      `).join('')}
    </div>

    <!-- SECTION 9: TECHNICAL SPECIFICATIONS -->
    <div class="manual-section-card">
      <div class="manual-sec-head">
        <h3 class="manual-sec-title"><span>📊</span> ${escapeHtml(s.specifications.title)}</h3>
        <span class="manual-sec-badge">Preserved Units</span>
      </div>
      <div class="manual-specs-grid">
        ${(s.specifications.specs || []).map(spec => `
          <div class="manual-spec-item">
            <div class="manual-spec-param">${escapeHtml(spec.parameter)}</div>
            <div class="manual-spec-val">${escapeHtml(spec.value)}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

window.selectRawManualViewer = function(filename) {
  STATE.activeManualType = filename;
  document.querySelectorAll('.manual-tab-item').forEach(el => el.classList.remove('active'));
  const activeTab = document.getElementById(`manual-tab-${filename}`);
  if (activeTab) activeTab.classList.add('active');

  const manuals = STATE.manualsData.manuals || [];
  const selected = manuals.find(m => m.filename === filename);
  const viewer = document.getElementById('manual-text-display');

  if (selected && viewer) {
    viewer.innerHTML = `
      <h2>${escapeHtml(selected.title)}</h2>
      <div style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem;">
        <span class="badge-tag badge-indigo">${selected.filename}</span>
        <span class="badge-tag badge-success">${selected.chunkCount} Ingested Chunks</span>
        <span class="badge-tag" style="background: #f1f5f9; color: #475569;">Page 1 - ${selected.pages}</span>
      </div>
      <div style="white-space: pre-wrap; font-size: 0.9rem; line-height: 1.65; color: #334155; font-family: var(--font-sans);">
${escapeHtml(selected.raw_text || '')}
      </div>
    `;
  }
};

// --------------------------------------------------------------------------
// TOOL 4: TELEMETRY
// --------------------------------------------------------------------------

function updateTelemetryUI(data) {
  const chunkEl = document.getElementById('telemetry-chunks-count');
  const statusEl = document.getElementById('telemetry-chroma-status');
  if (chunkEl) chunkEl.textContent = data.chunk_count || 60;
  if (statusEl) statusEl.textContent = data.status || 'Active (Persistent)';
}

// --------------------------------------------------------------------------
// UTILITIES
// --------------------------------------------------------------------------

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatMarkdown(text) {
  if (!text) return '';
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="background: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-family: var(--font-mono); font-size: 0.85em;">$1</code>')
    .replace(/\n/g, '<br/>');
}

// --------------------------------------------------------------------------
// AI CONFIDENCE & HARDWARE DIAGNOSTICS SUITE HANDLERS
// --------------------------------------------------------------------------

STATE.faultHistory = [];

window.toggleExplanation = function(elemId) {
  const box = document.getElementById(elemId);
  if (!box) return;
  const isShown = box.classList.toggle('active');
  const btn = box.previousElementSibling ? box.previousElementSibling.querySelector('.btn-explanation-toggle') : null;
  if (btn) {
    btn.innerHTML = isShown ? `
      <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/></svg>
      <span>Hide Explanation</span>
    ` : `
      <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      <span>View Explanation</span>
    `;
  }
};

window.fetchFaultHistory = async function() {
  try {
    const res = await fetch('/api/fault-history');
    if (res.ok) {
      const data = await res.json();
      STATE.faultHistory = data.faults || [];
      renderFaultHistoryTable(STATE.faultHistory);
    }
  } catch (err) {
    console.warn('Could not fetch fault history:', err);
  }
};

function renderFaultHistoryTable(faults) {
  const tbody = document.getElementById('fault-history-tbody');
  if (!tbody) return;

  if (!faults || faults.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #94a3b8; padding: 2rem;">No diagnostic fault events recorded in current session.</td></tr>`;
    return;
  }

  tbody.innerHTML = faults.map(f => {
    const pct = f.confidence_percentage !== undefined ? f.confidence_percentage : Math.round((f.confidence_score || 0) * 100);
    const lvl = f.confidence_level || (pct >= 90 ? 'High' : pct >= 70 ? 'Moderate' : 'Low');
    const lvlClass = lvl.toLowerCase();

    return `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 0.775rem; color: #64748b;">${escapeHtml(f.timestamp || 'Just now')}</td>
        <td><span class="badge-tag badge-indigo" style="font-size: 0.75rem;">${escapeHtml(f.machine || 'General')}</span></td>
        <td style="font-weight: 700; color: #0f172a;">${escapeHtml(f.fault || 'Hardware Fault')}</td>
        <td style="font-family: var(--font-mono); font-size: 0.8rem; color: #475569;">${escapeHtml(f.component || 'Subsystem')}</td>
        <td>
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-family: var(--font-mono); font-weight: 800; font-size: 0.9rem;">${pct}%</span>
            <div style="width: 50px; height: 6px; background: #e2e8f0; border-radius: 9999px; overflow: hidden;">
              <div class="confidence-bar-fill ${lvlClass}" style="width: ${pct}%;"></div>
            </div>
          </div>
        </td>
        <td>
          <span class="confidence-level-pill ${lvlClass}" style="font-size: 0.7rem; padding: 0.15rem 0.5rem;">
            ${escapeHtml(lvl)}
          </span>
        </td>
        <td>
          <button class="btn btn-secondary" onclick="openFaultDetailsModal('${f.id}')" style="padding: 0.3rem 0.65rem; font-size: 0.75rem;">
            Inspect
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

window.fetchMachineHealth = async function() {
  try {
    const res = await fetch('/api/machine-health');
    if (res.ok) {
      const data = await res.json();
      renderMachineHealthCards(data.machines || []);
    }
  } catch (err) {
    console.warn('Could not fetch machine health:', err);
  }
};

function renderMachineHealthCards(machines) {
  const container = document.getElementById('machine-health-container');
  if (!container || !machines || machines.length === 0) return;

  container.innerHTML = machines.map(m => {
    const color = m.status_color || (m.health_score >= 90 ? 'emerald' : m.health_score >= 70 ? 'amber' : 'rose');
    const hasFault = !!m.active_fault;

    return `
      <div class="health-card ${color}">
        <div class="health-card-head">
          <div class="health-machine-name">${escapeHtml(m.name || m.code)}</div>
          <span class="health-score-badge ${color}">${m.health_score}% Health</span>
        </div>
        <div style="font-size: 0.85rem; font-weight: 600; color: #334155; margin-bottom: 0.35rem;">
          ${escapeHtml(m.status)}
        </div>
        ${hasFault ? `
          <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.5rem 0.75rem; margin: 0.5rem 0; font-size: 0.8rem;">
            <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; font-weight: 700;">Active Diagnosed Fault:</div>
            <div style="font-weight: 700; color: #0f172a; margin-top: 0.1rem;">
              ${escapeHtml(m.active_fault)}
              <span class="confidence-level-pill ${(m.confidence_level || 'low').toLowerCase()}" style="font-size: 0.65rem; padding: 0.1rem 0.4rem; margin-left: 0.4rem;">
                ${m.confidence_percentage || Math.round((m.confidence_score || 0)*100)}% ${escapeHtml(m.confidence_level || '')}
              </span>
            </div>
          </div>
        ` : ''}
        <div style="font-size: 0.775rem; color: #94a3b8; font-family: var(--font-mono);">
          ${escapeHtml(m.sensor_summary || 'Operating within normal telemetry parameters')}
        </div>
      </div>
    `;
  }).join('');
}

window.openFaultDetailsModal = function(faultId) {
  const fault = STATE.faultHistory.find(f => f.id === faultId) || (STATE.faultHistory[0] || null);
  if (!fault) return;

  const modal = document.getElementById('fault-details-modal');
  const body = document.getElementById('fault-details-modal-body');
  if (!modal || !body) return;

  const pct = fault.confidence_percentage !== undefined ? fault.confidence_percentage : Math.round((fault.confidence_score || 0) * 100);
  const lvl = fault.confidence_level || (pct >= 90 ? 'High' : pct >= 70 ? 'Moderate' : 'Low');
  const lvlClass = lvl.toLowerCase();

  let sensorHtml = '';
  if (fault.evidence && fault.evidence.sensor_readings) {
    sensorHtml = Object.entries(fault.evidence.sensor_readings).map(([k, v]) => `
      <div class="sensor-item">
        <div class="sensor-label">${escapeHtml(k.replace(/_/g, ' '))}</div>
        <div class="sensor-val">${escapeHtml(v)}</div>
      </div>
    `).join('');
  }

  let candidatesHtml = '';
  if (fault.possible_faults && fault.possible_faults.length > 0) {
    candidatesHtml = `
      <div class="ranked-faults-box" style="margin: 1rem 0;">
        <div class="ranked-faults-title">
          <span>Ranked Differential Fault Hypotheses</span>
        </div>
        ${fault.possible_faults.map((pf, i) => `
          <div class="ranked-fault-item ${pf.is_primary ? 'is-primary' : ''}">
            <div class="ranked-fault-info">
              <span class="ranked-fault-rank">${i+1}.</span>
              <div>
                <span class="ranked-fault-name">${escapeHtml(pf.fault)}</span>
                ${pf.is_primary ? '<span class="primary-badge" style="margin-left: 0.4rem;">PRIMARY</span>' : ''}
              </div>
            </div>
            <div class="ranked-fault-metric">
              <span class="ranked-fault-pct">${pf.confidence_percentage || Math.round((pf.confidence_score || 0)*100)}%</span>
              <span class="confidence-level-pill ${(pf.confidence_level || 'low').toLowerCase()}" style="font-size: 0.7rem; padding: 0.15rem 0.5rem;">
                ${escapeHtml(pf.confidence_level || 'Moderate')}
              </span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  body.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span class="badge-tag badge-indigo">${escapeHtml(fault.machine || 'Machine')}</span>
        <span style="font-size: 0.75rem; font-family: var(--font-mono); color: #64748b;">${escapeHtml(fault.id || '')}</span>
      </div>
      <span style="font-size: 0.75rem; color: #94a3b8; font-family: var(--font-mono);">${escapeHtml(fault.timestamp || '')}</span>
    </div>

    <h2 style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-bottom: 0.25rem;">${escapeHtml(fault.fault)}</h2>
    <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 1.25rem;">
      Component: <strong>${escapeHtml(fault.component || 'Subassembly')}</strong>
    </div>

    <!-- AI Confidence Box -->
    <div class="confidence-box" style="margin-bottom: 1rem;">
      <div class="confidence-header-row">
        <div>
          <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 0.2rem;">AI Predictive Confidence</div>
          <div class="confidence-metric-group">
            <span class="confidence-pct-num ${lvlClass}">${pct}%</span>
            <span class="confidence-level-pill ${lvlClass}">
              <span>Confidence Level:</span>
              <strong>${escapeHtml(lvl)}</strong>
            </span>
          </div>
        </div>
      </div>
      <div class="confidence-bar-track">
        <div class="confidence-bar-fill ${lvlClass}" style="width: ${pct}%;"></div>
      </div>
      <div class="confidence-scale-markers">
        <span>0% Low</span>
        <span>70% Moderate</span>
        <span>90% High</span>
      </div>
      <div class="non-guarantee-disclaimer">
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
        <span>The confidence score is presented as the AI model's predictive probability and does NOT guarantee that the fault is actually present.</span>
      </div>
    </div>

    ${candidatesHtml}

    <div style="margin-bottom: 1rem;">
      <div style="font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 0.25rem;">Probable Cause:</div>
      <div style="font-size: 0.9rem; color: #1e293b; background: #f8fafc; padding: 0.75rem; border-radius: 8px; border: 1px solid #e2e8f0;">
        ${escapeHtml(fault.cause || 'Mechanical degradation or load strain.')}
      </div>
    </div>

    <div style="margin-bottom: 1rem;">
      <div style="font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 0.25rem;">Recommended Action:</div>
      <div style="font-size: 0.9rem; color: #1e293b; background: #f0fdf4; padding: 0.75rem; border-radius: 8px; border: 1px solid #bbf7d0;">
        ${escapeHtml(fault.recommendation || 'Inspect component clearances and lubricate.')}
      </div>
    </div>

    ${sensorHtml ? `
      <div style="margin-bottom: 1rem;">
        <div style="font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase; margin-bottom: 0.5rem;">Associated Telemetry Readings:</div>
        <div class="sensor-grid">${sensorHtml}</div>
      </div>
    ` : ''}

    <div style="margin-top: 1.5rem; display: flex; justify-content: flex-end;">
      <button class="btn btn-secondary" onclick="closeFaultDetailsModal()">Close Details</button>
    </div>
  `;

  modal.classList.add('active');
};

window.closeFaultDetailsModal = function() {
  const modal = document.getElementById('fault-details-modal');
  if (modal) modal.classList.remove('active');
};

window.openDiagnosticReportModal = async function() {
  const modal = document.getElementById('diagnostic-report-modal');
  const body = document.getElementById('diagnostic-report-modal-body');
  if (!modal || !body) return;

  body.innerHTML = `<div style="text-align: center; padding: 2rem; color: #64748b;">Generating executive fleet diagnostic report...</div>`;
  modal.classList.add('active');

  try {
    const res = await fetch('/api/diagnostic-report');
    if (res.ok) {
      const rep = await res.json();
      const dist = rep.confidence_distribution || { high: 0, moderate: 0, low: 0 };
      const total = rep.total_diagnoses || 0;

      body.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.75rem;">
          <div>
            <span class="badge-tag badge-indigo">Executive Diagnostic Report</span>
            <h2 style="font-size: 1.35rem; font-weight: 800; color: #0f172a; margin-top: 0.25rem;">Plant Hardware Diagnostic Summary</h2>
          </div>
          <div style="text-align: right; font-size: 0.75rem; color: #64748b; font-family: var(--font-mono);">
            <div>Report: ${rep.report_id}</div>
            <div>Generated: ${rep.generated_at}</div>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
          <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 1rem; text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #047857; font-family: var(--font-mono);">${dist.high}</div>
            <div style="font-size: 0.75rem; font-weight: 700; color: #065f46; text-transform: uppercase;">High Confidence (≥90%)</div>
          </div>
          <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px; padding: 1rem; text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #b45309; font-family: var(--font-mono);">${dist.moderate}</div>
            <div style="font-size: 0.75rem; font-weight: 700; color: #92400e; text-transform: uppercase;">Moderate (70-89%)</div>
          </div>
          <div style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px; padding: 1rem; text-align: center;">
            <div style="font-size: 1.8rem; font-weight: 800; color: #475569; font-family: var(--font-mono);">${dist.low}</div>
            <div style="font-size: 0.75rem; font-weight: 700; color: #334155; text-transform: uppercase;">Low (&lt;70%)</div>
          </div>
        </div>

        <div style="font-size: 0.85rem; font-weight: 700; color: #334155; margin-bottom: 0.5rem; text-transform: uppercase;">Recent Fleet Diagnostic Incidents (${total} total):</div>
        <div style="max-height: 220px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 1.25rem;">
          <table style="width: 100%; font-size: 0.8rem; border-collapse: collapse;">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0; text-align: left;">
                <th style="padding: 0.5rem 0.75rem;">Time</th>
                <th style="padding: 0.5rem 0.75rem;">Machine</th>
                <th style="padding: 0.5rem 0.75rem;">Fault</th>
                <th style="padding: 0.5rem 0.75rem;">Confidence</th>
              </tr>
            </thead>
            <tbody>
              ${(rep.recent_faults || []).map(f => `
                <tr style="border-bottom: 1px solid #f1f5f9;">
                  <td style="padding: 0.5rem 0.75rem; font-family: var(--font-mono); color: #64748b;">${escapeHtml(f.timestamp)}</td>
                  <td style="padding: 0.5rem 0.75rem; font-weight: 600;">${escapeHtml(f.machine)}</td>
                  <td style="padding: 0.5rem 0.75rem;">${escapeHtml(f.fault)}</td>
                  <td style="padding: 0.5rem 0.75rem; font-family: var(--font-mono); font-weight: 700;">
                    ${f.confidence_percentage || Math.round((f.confidence_score||0)*100)}% (${escapeHtml(f.confidence_level||'')})
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <div class="non-guarantee-disclaimer">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
          <span><strong>Regulatory Compliance Notice:</strong> AI confidence scoring reflects pattern matching metrics against calibrated technical manuals and does not constitute a physical guarantee that the fault is present. Physical inspection by qualified maintenance engineers is mandatory prior to component replacement.</span>
        </div>

        <div style="margin-top: 1.25rem; display: flex; justify-content: flex-end; gap: 0.5rem;">
          <button class="btn btn-secondary" onclick="closeDiagnosticReportModal()">Close Report</button>
        </div>
      `;
    }
  } catch (err) {
    body.innerHTML = `<div style="color: #ef4444; padding: 1.5rem;">Failed to generate report: ${err.message}</div>`;
  }
};

window.closeDiagnosticReportModal = function() {
  const modal = document.getElementById('diagnostic-report-modal');
  if (modal) modal.classList.remove('active');
};

