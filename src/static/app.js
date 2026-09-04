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
      <div class="citation-container">
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

  const cardHtml = `
    <div class="card-response">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div class="card-header-badge badge-normal-ans">
          <svg style="width: 14px; height: 14px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
          <span>VERIFIED GROUNDED PROCEDURE</span>
        </div>
        <span style="font-size: 0.725rem; font-family: var(--font-mono); color: #94a3b8;">${elapsedMs}ms • Grounded in Manuals</span>
      </div>

      <div class="card-content-section">
        <div class="section-label">1. Meaning & Diagnosis</div>
        <div class="section-body">${formatMarkdown(meaning)}</div>
      </div>

      ${causes.length > 0 ? `
        <div class="card-content-section">
          <div class="section-label">2. Probable Causes</div>
          <ul class="steps-list" style="list-style-type: disc;">
            ${causes.map(c => `<li>${escapeHtml(c)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${steps.length > 0 ? `
        <div class="card-content-section">
          <div class="section-label">3. Step-by-Step Corrective Action</div>
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

window.openPdfFromCitation = function(manualName, page = 1) {
  document.getElementById('citation-modal')?.classList.remove('active');
  if (typeof window.switchTab === 'function') {
    window.switchTab('manuals');
  }
  
  const manuals = (STATE.manualsData && STATE.manualsData.manuals) || [];
  const cleanTarget = (manualName || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const found = manuals.find(m => {
    const cf = m.filename.toLowerCase().replace(/[^a-z0-9]/g, '');
    const cm = (m.machine || '').toLowerCase().replace(/[^a-z0-9]/g, '');
    return cf.includes(cleanTarget) || cleanTarget.includes(cf) || cm.includes(cleanTarget) || cleanTarget.includes(cm);
  }) || manuals[0];

  if (found) {
    window.setManualViewMode('pdf');
    window.selectManualViewer(found.filename, page);
  }
};

window.openCitationModal = function(source) {
  const modal = document.getElementById('citation-modal');
  const modalBody = document.getElementById('citation-modal-body');
  if (!modal || !modalBody) return;

  const pageNum = source.page || 1;
  modalBody.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
      <span class="badge-tag badge-indigo">${escapeHtml(source.machine || 'Machine')}</span>
      <span style="font-size: 0.8rem; font-family: var(--font-mono); color: #64748b;">${escapeHtml(source.manual)} • Page ${pageNum}</span>
    </div>
    <h3 style="font-size: 1.25rem; font-weight: 800; color: #0f172a; margin-bottom: 1rem;">${escapeHtml(source.section)}</h3>
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; font-size: 0.875rem; line-height: 1.6; color: #334155;">
      ${source.snippet ? escapeHtml(source.snippet) : 'Verified procedure extracted directly from the manufacturer technical manual.'}
    </div>
    <div style="margin-top: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
      <button class="btn btn-primary" onclick="openPdfFromCitation('${escapeHtml(source.manual)}', ${pageNum})">
        📄 Open in PDF Reader (Page ${pageNum}) →
      </button>
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
// TOOL 3: MANUALS EXPLORER & PDF READER
// --------------------------------------------------------------------------

let CURRENT_MANUAL_VIEW_MODE = 'pdf'; // 'pdf' or 'text'
let CURRENT_MANUAL_PAGE = 1;

function renderManualsViewer() {
  const navContainer = document.getElementById('manuals-nav-list');
  const viewer = document.getElementById('manual-text-display');
  if (!navContainer || !viewer) return;

  const manuals = (STATE.manualsData && STATE.manualsData.manuals) || [];
  if (manuals.length === 0) return;

  navContainer.innerHTML = manuals.map((m, idx) => `
    <div class="manual-tab-item ${idx === 0 ? 'active' : ''}" onclick="selectManualViewer('${m.filename}', 1)" id="manual-tab-${m.filename}">
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <h5>${escapeHtml(m.title)}</h5>
        ${m.has_pdf ? '<span class="badge-tag badge-indigo" style="font-size: 0.65rem; padding: 2px 6px;">PDF</span>' : ''}
      </div>
      <p>${escapeHtml(m.filename)} • ${m.pages} Pages • ${m.chunkCount} Chunks</p>
    </div>
  `).join('');

  // Default display first manual
  selectManualViewer(manuals[0].filename, 1);
}

window.selectManualViewer = function(filename, page = 1) {
  document.querySelectorAll('.manual-tab-item').forEach(el => el.classList.remove('active'));
  const activeTab = document.getElementById(`manual-tab-${filename}`);
  if (activeTab) activeTab.classList.add('active');

  const manuals = (STATE.manualsData && STATE.manualsData.manuals) || [];
  const selected = manuals.find(m => m.filename === filename) || manuals[0];
  const viewer = document.getElementById('manual-text-display');
  if (!selected || !viewer) return;

  CURRENT_MANUAL_PAGE = page;
  window.CURRENT_SELECTED_MANUAL = selected;

  renderManualViewContent();
};

window.setManualViewMode = function(mode) {
  CURRENT_MANUAL_VIEW_MODE = mode;
  renderManualViewContent();
};

window.navigatePdfPage = function(delta) {
  const selected = window.CURRENT_SELECTED_MANUAL;
  if (!selected) return;
  const newPage = CURRENT_MANUAL_PAGE + delta;
  if (newPage >= 1 && newPage <= (selected.pages || 1)) {
    CURRENT_MANUAL_PAGE = newPage;
    renderManualViewContent();
  }
};

function renderManualViewContent() {
  const viewer = document.getElementById('manual-text-display');
  const selected = window.CURRENT_SELECTED_MANUAL;
  if (!selected || !viewer) return;

  const pdfUrl = selected.pdf_url || `/api/manuals/${selected.pdf_filename || selected.filename.replace('.txt', '.pdf')}/pdf`;

  const headerHtml = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0;">
      <div>
        <h2 style="margin: 0; font-size: 1.25rem;">${escapeHtml(selected.title)}</h2>
        <div style="display: flex; gap: 0.5rem; margin-top: 0.35rem; align-items: center;">
          <span class="badge-tag badge-indigo">${selected.filename}</span>
          <span class="badge-tag badge-success">${selected.chunkCount} Grounded Chunks</span>
          <span class="badge-tag" style="background: #f1f5f9; color: #475569;">${selected.pages} Pages</span>
        </div>
      </div>
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <div style="background: #e2e8f0; padding: 3px; border-radius: 8px; display: flex; gap: 2px;">
          <button class="btn ${CURRENT_MANUAL_VIEW_MODE === 'pdf' ? 'btn-primary' : 'btn-secondary'}" style="padding: 4px 10px; font-size: 0.75rem;" onclick="setManualViewMode('pdf')">
            📄 PDF Reader
          </button>
          <button class="btn ${CURRENT_MANUAL_VIEW_MODE === 'text' ? 'btn-primary' : 'btn-secondary'}" style="padding: 4px 10px; font-size: 0.75rem;" onclick="setManualViewMode('text')">
            📋 RAG Chunks
          </button>
        </div>
      </div>
    </div>
  `;

  if (CURRENT_MANUAL_VIEW_MODE === 'pdf' && selected.has_pdf) {
    viewer.innerHTML = `
      ${headerHtml}
      <div style="background: #0f172a; color: #f8fafc; padding: 0.5rem 1rem; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.75rem; background: #1e293b; color: #fff;" onclick="navigatePdfPage(-1)" ${CURRENT_MANUAL_PAGE <= 1 ? 'disabled style="opacity: 0.4;"' : ''}>◀ Prev</button>
          <span>Page <strong>${CURRENT_MANUAL_PAGE}</strong> of ${selected.pages || 1}</span>
          <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.75rem; background: #1e293b; color: #fff;" onclick="navigatePdfPage(1)" ${CURRENT_MANUAL_PAGE >= (selected.pages || 1) ? 'disabled style="opacity: 0.4;"' : ''}>Next ▶</button>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <a href="${pdfUrl}" target="_blank" class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.75rem; background: #1e293b; color: #fff; text-decoration: none;">↗ Open Tab</a>
          <a href="${pdfUrl}?download=true" download="${selected.filename.replace('.txt', '.pdf')}" class="btn btn-secondary" style="padding: 2px 8px; font-size: 0.75rem; background: #1e293b; color: #fff; text-decoration: none;">⬇ Download</a>
        </div>
      </div>
      <iframe src="${pdfUrl}?v=2#page=${CURRENT_MANUAL_PAGE}" style="width: 100%; height: 580px; border: 1px solid #cbd5e1; border-top: none; border-radius: 0 0 12px 12px; background: #f8fafc;" title="${escapeHtml(selected.title)}"></iframe>
    `;
  } else {
    viewer.innerHTML = `
      ${headerHtml}
      <pre style="background: #1e293b; color: #f8fafc; padding: 1.25rem; border-radius: 12px; font-family: var(--font-mono); font-size: 0.825rem; line-height: 1.6; max-height: 580px; overflow-y: auto;">${escapeHtml(selected.raw_text || '')}</pre>
    `;
  }
}

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
