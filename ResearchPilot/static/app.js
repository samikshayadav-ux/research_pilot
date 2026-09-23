/* ============================================================
   ResearchPilot AI — Frontend Application
   All 7 pages: Dashboard, Papers, Chat, Compare, Gaps, Map, Review
   ============================================================ */
'use strict';

/* ── State ──────────────────────────────────────────────────────────────── */
const State = { papers: [], currentPage: 'dashboard' };

/* ── API helpers ─────────────────────────────────────────────────────────── */
const API = {
  async get(path) {
    const r = await fetch(path);
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.error || r.statusText); }
    return r.json();
  },
  async post(path, body) {
    const r = await fetch(path, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.error || r.statusText); }
    return r.json();
  },
  async upload(path, formData) {
    const r = await fetch(path, { method:'POST', body:formData });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.error || r.statusText); }
    return r.json();
  },
  async del(path) {
    const r = await fetch(path, { method:'DELETE' });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.error || r.statusText); }
    return r.json();
  },
};

/* ── Toast ───────────────────────────────────────────────────────────────── */
function toast(msg, type = '') {
  const el  = document.getElementById('toast');
  const ico = document.getElementById('toastIcon');
  const txt = document.getElementById('toastMsg');
  ico.textContent = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  txt.textContent = msg;
  el.className = `toast ${type}`;
  el.classList.remove('hidden');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add('hidden'), 3800);
}

/* ── DOM helpers ─────────────────────────────────────────────────────────── */
function esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
function spinner(txt='') { return `<span class="loading-spin"></span>${txt ? ' ' + esc(txt) : ''}`; }
function renderMarkdown(text) { try { return marked.parse(text); } catch { return `<p>${esc(text)}</p>`; } }
function tagsHtml(items, cls) { return (items || []).map(t => `<span class="tag ${cls}">${esc(t)}</span>`).join(''); }
function formatDimLabel(k) { return k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()); }

/* ── Navigation ──────────────────────────────────────────────────────────── */
function navigate(page) {
  State.currentPage = page;
  document.querySelectorAll('.nav-item').forEach(a => a.classList.toggle('active', a.dataset.page === page));
  document.querySelectorAll('.page').forEach(s => s.classList.toggle('active', s.id === `page-${page}`));
  if (page === 'dashboard')  loadDashboard();
  if (page === 'papers')     loadPapers();
  if (page === 'chat')       initChat();
  if (page === 'compare')    loadCompareList();
  if (page === 'gaps')       loadGapsAuto();
  if (page === 'landscape')  loadLandscape();
  if (page === 'review')     loadReviewList();
}

document.querySelectorAll('.nav-item').forEach(a =>
  a.addEventListener('click', e => { e.preventDefault(); navigate(a.dataset.page); })
);

/* ── Status check ────────────────────────────────────────────────────────── */
async function checkStatus() {
  try {
    const s   = await API.get('/api/status');
    const dot = document.getElementById('statusDot');
    const badge  = document.getElementById('statusBadge');
    const detail = document.getElementById('statusDetail');
    if (s.watsonx_available) {
      dot.className   = 'status-dot ok';
      badge.textContent = 'IBM Granite';
      detail.textContent = `Model active · ${s.embeddings_available ? 'FAISS' : 'keyword'} search`;
    } else {
      dot.className   = 'status-dot demo';
      badge.textContent = 'Demo Mode';
      detail.textContent = 'Add WATSONX_API_KEY + WATSONX_PROJECT_ID to .env to enable AI generation';
    }
  } catch {
    document.getElementById('statusDot').className   = 'status-dot error';
    document.getElementById('statusBadge').textContent = 'Offline';
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   DASHBOARD
═══════════════════════════════════════════════════════════════════════════ */
async function loadDashboard() {
  try {
    const d = await API.get('/api/dashboard');

    document.getElementById('statPapers').textContent   = d.papers_count;
    document.getElementById('statTopics').textContent   = d.topics_count;
    document.getElementById('statMethods').textContent  = d.methods_count;
    document.getElementById('statDatasets').textContent = d.datasets_count;
    document.getElementById('statGaps').textContent     = d.gaps_count;

    renderBarChart('chartTopics',   d.topic_distribution,   'topic');
    renderBarChart('chartMethods',  d.method_distribution,  'method');
    renderBarChart('chartDatasets', d.dataset_distribution, 'dataset');

    const cnt   = document.getElementById('dashPaperCount');
    if (cnt) cnt.textContent = d.papers_count + ' papers';

    const tbody = document.querySelector('#dashPapersTable tbody');
    tbody.innerHTML = (d.papers || []).map(p => `
      <tr>
        <td style="font-weight:600">${esc(p.title)}</td>
        <td style="white-space:nowrap">${esc(p.year)}</td>
        <td>${tagsHtml(p.topics,  'tag-topic')}</td>
        <td>${tagsHtml(p.methods, 'tag-method')}</td>
        <td>${p.demo
          ? '<span class="tag tag-demo">Demo</span>'
          : '<span class="tag tag-real">Uploaded</span>'}</td>
      </tr>`).join('');
  } catch (err) {
    toast('Dashboard failed to load: ' + err.message, 'error');
  }
}

function renderBarChart(id, data, type = 'topic') {
  const el = document.getElementById(id);
  if (!data || !data.length) {
    el.innerHTML = '<div style="color:var(--faint);font-size:.72rem;padding:.5rem">No data yet</div>';
    return;
  }
  const max = Math.max(...data.map(d => d.value), 1);
  el.innerHTML = data.slice(0, 7).map(d => `
    <div class="bar-row">
      <div class="bar-label" title="${esc(d.name)}">${esc(d.name)}</div>
      <div class="bar-track">
        <div class="bar-fill bar-fill-${type}" style="width:${Math.max(4, (d.value/max)*100)}%"></div>
      </div>
      <div class="bar-count">${d.value}</div>
    </div>`).join('');
}

/* ═══════════════════════════════════════════════════════════════════════════
   PAPERS LIBRARY
═══════════════════════════════════════════════════════════════════════════ */
async function loadPapers() {
  try {
    State.papers = await API.get('/api/papers');
    renderPapersGrid();
  } catch (err) {
    toast('Papers load failed: ' + err.message, 'error');
  }
}

function renderPapersGrid() {
  const grid = document.getElementById('papersGrid');
  const cnt  = document.getElementById('libraryCount');
  if (cnt) cnt.textContent = State.papers.length + ' papers';

  if (!State.papers.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1">
      <div class="empty-state-icon">📄</div>
      <div>No papers yet. Upload a PDF to get started.</div>
    </div>`;
    return;
  }

  grid.innerHTML = State.papers.map(p => `
    <div class="paper-card" id="card-${p.paper_id}">
      <div class="paper-card-title">${esc(p.title)}</div>
      <div class="paper-card-meta">
        ${esc((p.authors||[]).slice(0,2).join(', '))}
        ${p.authors&&p.authors.length>2 ? `<span style="color:var(--faint)"> +${p.authors.length-2} more</span>` : ''}
        &nbsp;·&nbsp; ${esc(p.year||'?')}
        &nbsp;·&nbsp; ${p.page_count||'?'} pages
      </div>
      <div class="paper-card-abstract">${esc(p.abstract||'No abstract available.')}</div>
      <div class="paper-card-tags">
        ${tagsHtml((p.topics||[]).slice(0,3),  'tag-topic')}
        ${tagsHtml((p.methods||[]).slice(0,2), 'tag-method')}
      </div>
      <div class="paper-card-actions">
        <button class="btn-xs primary" onclick="openPaperModal('${p.paper_id}')">Open</button>
        ${p.demo
          ? '<span class="tag tag-demo" style="padding:.2rem .5rem;margin:0">Demo</span>'
          : `<button class="btn-xs danger" onclick="deletePaper('${p.paper_id}')">Delete</button>`}
      </div>
    </div>`).join('');
}

async function deletePaper(pid) {
  if (!confirm('Delete this paper from your library?')) return;
  try {
    await API.del(`/api/papers/${pid}`);
    State.papers = State.papers.filter(p => p.paper_id !== pid);
    renderPapersGrid();
    toast('Paper deleted', 'success');
  } catch (err) {
    toast('Delete failed: ' + err.message, 'error');
  }
}

/* ── Paper modal ─────────────────────────────────────────────────────────── */
async function openPaperModal(pid) {
  const paper = State.papers.find(p => p.paper_id === pid)
    || await API.get(`/api/papers/${pid}`).catch(() => null);
  if (!paper) { toast('Paper not found', 'error'); return; }

  document.getElementById('modalTitle').textContent = paper.title;
  const tagEl = document.getElementById('modalTag');
  tagEl.textContent = paper.demo ? 'Demo Paper' : 'Uploaded';
  tagEl.className   = `modal-tag ${paper.demo ? 'demo' : 'real'}`;

  document.getElementById('modalBody').innerHTML = `
    <div class="paper-detail-grid">
      <div>
        <div class="detail-label">Authors</div>
        <div class="detail-val">${esc((paper.authors||[]).join(', ')||'Unknown')}</div>
      </div>
      <div>
        <div class="detail-label">Year · Pages</div>
        <div class="detail-val">${esc(paper.year||'?')} · ${paper.page_count||'?'} pages</div>
      </div>
      <div style="grid-column:1/-1">
        <div class="detail-label">Abstract</div>
        <div class="detail-val" style="color:var(--muted);line-height:1.6">${esc(paper.abstract||'–')}</div>
      </div>
      <div>
        <div class="detail-label">Topics</div>
        <div>${tagsHtml(paper.topics,'tag-topic')}</div>
      </div>
      <div>
        <div class="detail-label">Methods</div>
        <div>${tagsHtml(paper.methods,'tag-method')}</div>
      </div>
      <div>
        <div class="detail-label">Datasets</div>
        <div>${tagsHtml(paper.datasets,'tag-dataset')}</div>
      </div>
      <div>
        <div class="detail-label">Metrics</div>
        <div class="detail-val" style="color:var(--muted)">${esc((paper.metrics||[]).join(', ')||'–')}</div>
      </div>
      <div style="grid-column:1/-1">
        <div class="detail-label">Key Findings</div>
        <ul class="detail-list">
          ${(paper.key_findings||['–']).map(f=>`<li>${esc(f)}</li>`).join('')}
        </ul>
      </div>
      <div style="grid-column:1/-1">
        <div class="detail-label">Limitations</div>
        <ul class="detail-list">
          ${(paper.limitations||['–']).map(l=>`<li>${esc(l)}</li>`).join('')}
        </ul>
      </div>
    </div>

    <div class="modal-ask-section">
      <div class="detail-label">Ask a question about this paper</div>
      <div class="paper-ask-row">
        <input class="paper-ask-input" id="paperAskInput" type="text"
               placeholder="e.g. What method did they use?" autocomplete="off"/>
        <button class="btn-xs primary" id="paperAskBtn" onclick="askPaper('${pid}')">Ask</button>
      </div>
      <div class="paper-ask-result" id="paperAskResult"></div>
    </div>`;

  document.getElementById('paperAskInput').addEventListener('keydown', e => {
    if (e.key === 'Enter') askPaper(pid);
  });

  document.getElementById('paperModal').classList.remove('hidden');
}

async function askPaper(pid) {
  const input  = document.getElementById('paperAskInput');
  const result = document.getElementById('paperAskResult');
  const btn    = document.getElementById('paperAskBtn');
  const q = input.value.trim();
  if (!q) return;

  result.style.display = 'block';
  result.innerHTML = spinner('Searching…');
  btn.disabled = true;

  try {
    const data = await API.post(`/api/papers/${pid}/ask`, { question: q });
    result.innerHTML = `
      <div style="margin-bottom:.5rem">${renderMarkdown(data.answer)}</div>
      ${data.sources && data.sources.length ? `
        <div class="sources-panel">
          <div class="sources-title">
            <svg viewBox="0 0 20 20" fill="currentColor" width="12" height="12"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/></svg>
            Retrieved Evidence
          </div>
          ${data.sources.map(s=>`
            <div class="source-item">
              <strong>${esc(s.title)}</strong> · p.${s.page}
              <div class="source-excerpt">"${esc((s.excerpt||'').slice(0,120))}…"</div>
            </div>`).join('')}
        </div>` : ''}`;
  } catch (err) {
    result.innerHTML = `<span style="color:var(--red)">Error: ${esc(err.message)}</span>`;
  } finally {
    btn.disabled = false;
  }
}

/* Close modal — X button, backdrop click, Escape key */
function closeModal() { document.getElementById('paperModal').classList.add('hidden'); }
document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('paperModal').addEventListener('click', e => {
  if (e.target === document.getElementById('paperModal')) closeModal();
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

/* ── File Upload ─────────────────────────────────────────────────────────── */
const uploadZone   = document.getElementById('uploadZone');
const fileInput    = document.getElementById('fileInput');
const uploadProg   = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressLbl  = document.getElementById('progressLabel');

uploadZone.addEventListener('click', e => { if (!e.target.closest('label')) fileInput.click(); });
fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleUpload(fileInput.files[0]); });
uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault(); uploadZone.classList.remove('dragover');
  if (e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]);
});

async function handleUpload(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) { toast('Only PDF files are supported', 'error'); return; }
  uploadProg.classList.remove('hidden');

  let pct = 0;
  const tick = setInterval(() => {
    pct = Math.min(pct + (pct < 65 ? 10 : 2), 88);
    progressFill.style.width = pct + '%';
  }, 220);
  progressLbl.textContent = `Extracting and indexing ${file.name}…`;

  try {
    const form  = new FormData();
    form.append('file', file);
    const paper = await API.upload('/api/papers/upload', form);

    clearInterval(tick);
    progressFill.style.width = '100%';
    progressLbl.innerHTML = `<span style="color:var(--green)">✓ Indexed:</span> ${esc(paper.title)}`;
    State.papers.push(paper);
    renderPapersGrid();
    toast(`Paper added: ${paper.title}`, 'success');

    setTimeout(() => {
      uploadProg.classList.add('hidden');
      progressFill.style.width = '0';
      fileInput.value = '';
    }, 2500);
  } catch (err) {
    clearInterval(tick);
    uploadProg.classList.add('hidden');
    progressFill.style.width = '0';
    toast('Upload failed: ' + err.message, 'error');
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   RESEARCH CHAT
═══════════════════════════════════════════════════════════════════════════ */
let _chatInitialised = false;

async function initChat() {
  if (!State.papers.length) {
    try { State.papers = await API.get('/api/papers'); } catch {}
  }
  // Populate scope selector
  const sel = document.getElementById('chatScope');
  sel.innerHTML = '<option value="">All Papers</option>'
    + State.papers.map(p => `<option value="${p.paper_id}">${esc(p.title.slice(0,55))}</option>`).join('');

  if (!_chatInitialised) {
    _chatInitialised = true;
    // Chip clicks
    document.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', () => {
        document.getElementById('chatInput').value = chip.dataset.q;
        sendChat();
      });
    });
  }
}

function appendChatMsg(role, html, sources) {
  const win     = document.getElementById('chatWindow');
  const welcome = document.getElementById('chatWelcome');
  if (welcome) welcome.remove();

  const msg = document.createElement('div');
  msg.className = `chat-msg ${role}`;
  msg.innerHTML = `
    <div class="chat-label">${role === 'user' ? 'You' : '🔬 ResearchPilot AI'}</div>
    <div class="chat-bubble">${html}</div>
    ${sources && sources.length ? `
      <div class="sources-panel">
        <div class="sources-title">
          <svg viewBox="0 0 20 20" fill="currentColor" width="12" height="12"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/></svg>
          Retrieved Evidence (${sources.length} chunks)
        </div>
        ${sources.map(s => `
          <div class="source-item">
            <strong>${esc(s.title)}</strong> · p.${s.page}
            <div class="source-excerpt">"${esc((s.excerpt||'').slice(0,100))}…"</div>
          </div>`).join('')}
      </div>` : ''}`;
  win.appendChild(msg);
  win.scrollTop = win.scrollHeight;
}

function appendTypingIndicator() {
  const win = document.getElementById('chatWindow');
  const welcome = document.getElementById('chatWelcome');
  if (welcome) welcome.remove();
  const div = document.createElement('div');
  div.className = 'chat-typing'; div.id = 'chatTyping';
  div.innerHTML = spinner('Searching papers and generating grounded answer…');
  win.appendChild(div);
  win.scrollTop = win.scrollHeight;
}

document.getElementById('chatSend').addEventListener('click', sendChat);
document.getElementById('chatInput').addEventListener('keydown', e => { if (e.key === 'Enter') sendChat(); });

async function sendChat() {
  const input   = document.getElementById('chatInput');
  const scopeSel= document.getElementById('chatScope');
  const sendBtn = document.getElementById('chatSend');
  const q = input.value.trim();
  if (!q) return;

  input.value = '';
  sendBtn.disabled = true;
  appendChatMsg('user', `<p>${esc(q)}</p>`, null);
  appendTypingIndicator();

  try {
    const body = { question: q };
    if (scopeSel.value) body.paper_id = scopeSel.value;
    const data = await API.post('/api/chat', body);
    document.getElementById('chatTyping')?.remove();
    appendChatMsg('assistant', renderMarkdown(data.answer), data.sources);
  } catch (err) {
    document.getElementById('chatTyping')?.remove();
    appendChatMsg('assistant',
      `<span style="color:var(--red)">Error: ${esc(err.message)}</span>`, null);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   PAPER COMPARISON
═══════════════════════════════════════════════════════════════════════════ */
async function loadCompareList() {
  if (!State.papers.length) {
    try { State.papers = await API.get('/api/papers'); } catch {}
  }
  const list = document.getElementById('compareCheckList');
  list.innerHTML = State.papers.map((p, i) => `
    <label class="check-item">
      <input type="checkbox" name="compareCheck" value="${p.paper_id}" ${i < 3 ? 'checked' : ''}/>
      ${esc(p.title.slice(0, 48))}${p.title.length > 48 ? '…' : ''}
    </label>`).join('');
  updateCompareHint();
  document.querySelectorAll('[name=compareCheck]').forEach(cb =>
    cb.addEventListener('change', updateCompareHint));
}

function updateCompareHint() {
  const n   = document.querySelectorAll('[name=compareCheck]:checked').length;
  const hint = document.getElementById('compareHint');
  if (hint) hint.textContent = n > 0 ? `${n} selected` : 'Select 2–5 papers';
}

document.getElementById('compareBtn').addEventListener('click', async () => {
  const ids = [...document.querySelectorAll('[name=compareCheck]:checked')].map(c => c.value);
  if (ids.length < 2) { toast('Select at least 2 papers', 'error'); return; }
  if (ids.length > 5) { toast('Select at most 5 papers', 'error'); return; }

  const btn = document.getElementById('compareBtn');
  btn.disabled = true;
  btn.innerHTML = spinner('Comparing…');

  try {
    const data = await API.post('/api/compare', { paper_ids: ids });
    renderCompareTable(data);
    document.getElementById('compareResult').classList.remove('hidden');
    document.getElementById('compareMode').textContent =
      data.mode === 'watsonx' ? '✓ Generated by IBM Granite' :
      '⚠ Demo comparison — upload papers & connect watsonx for AI-generated analysis';
  } catch (err) {
    toast('Comparison failed: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14" style="margin-right:.3rem"><path d="M5 4a1 1 0 00-2 0v7.268a2 2 0 000 3.464V16a1 1 0 102 0v-1.268a2 2 0 000-3.464V4zM11 4a1 1 0 10-2 0v1.268a2 2 0 000 3.464V16a1 1 0 102 0V8.732a2 2 0 000-3.464V4zM16 3a1 1 0 011 1v7.268a2 2 0 010 3.464V16a1 1 0 11-2 0v-1.268a2 2 0 010-3.464V4a1 1 0 011-1z"/></svg>Compare Selected`;
  }
});

function renderCompareTable({ comparison, papers }) {
  const wrap = document.getElementById('compareTableWrap');
  const headerCols = papers.map(p =>
    `<th style="min-width:160px" title="${esc(p.title)}">${esc(p.title.slice(0,32))}…</th>`
  ).join('');

  const DIM_ORDER = ['problem_statement','methodology','model_architecture','datasets',
                     'metrics','key_results','limitations','future_work'];
  const dims = DIM_ORDER.filter(d => comparison[d])
    .concat(Object.keys(comparison).filter(d => !DIM_ORDER.includes(d)));

  const rows = dims.map(dim => {
    const cells = papers.map(p =>
      `<td>${esc(comparison[dim]?.[p.paper_id] || '–')}</td>`).join('');
    return `<tr><td class="dim-label">${esc(formatDimLabel(dim))}</td>${cells}</tr>`;
  }).join('');

  wrap.innerHTML = `
    <table class="compare-table">
      <thead><tr><th class="dim-col">Dimension</th>${headerCols}</tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

/* ═══════════════════════════════════════════════════════════════════════════
   RESEARCH GAPS (auto-load on nav, button to re-analyze)
═══════════════════════════════════════════════════════════════════════════ */
let _gapsLoaded = false;

async function loadGapsAuto() {
  if (_gapsLoaded) return;
  await runGapAnalysis();
}

document.getElementById('analyzeGapsBtn').addEventListener('click', async () => {
  _gapsLoaded = false;
  await runGapAnalysis();
});

async function runGapAnalysis() {
  const btn     = document.getElementById('analyzeGapsBtn');
  const loading = document.getElementById('gapsLoading');
  const result  = document.getElementById('gapsResult');

  btn.disabled = true;
  btn.innerHTML = spinner('Analyzing…');
  loading.classList.remove('hidden');
  result.classList.add('hidden');

  try {
    const data = await API.get('/api/gaps');
    renderGaps(data);
    result.classList.remove('hidden');
    _gapsLoaded = true;
  } catch (err) {
    toast('Gap analysis failed: ' + err.message, 'error');
  } finally {
    loading.classList.add('hidden');
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14" style="margin-right:.3rem"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/></svg>Analyze Gaps`;
  }
}

const GAP_DEFS = [
  { key: 'common_limitations',   cls: 'gap-common',       icon: '⚠', title: 'Common Limitations' },
  { key: 'underexplored_areas',  cls: 'gap-underexplored',icon: '🔍', title: 'Underexplored Areas' },
  { key: 'missing_comparisons',  cls: 'gap-missing',      icon: '⚖', title: 'Missing Comparisons' },
  { key: 'dataset_gaps',         cls: 'gap-dataset',      icon: '📊', title: 'Dataset Gaps' },
  { key: 'evaluation_gaps',      cls: 'gap-evaluation',   icon: '📐', title: 'Evaluation Gaps' },
  { key: 'methodological_gaps',  cls: 'gap-methodological',icon:'🔧', title: 'Methodological Gaps' },
];

function renderGaps({ gaps, directions }) {
  const grid = document.getElementById('gapsGrid');
  grid.innerHTML = GAP_DEFS.map(({ key, cls, icon, title }) => {
    const items = gaps[key] || [];
    return `
      <div class="gap-card ${cls}">
        <div class="gap-card-title">${icon} ${title}</div>
        <ul class="gap-list">
          ${items.length
            ? items.map(i => `<li>${esc(i)}</li>`).join('')
            : '<li style="color:var(--faint)">None identified</li>'}
        </ul>
      </div>`;
  }).join('');

  document.getElementById('directionsList').innerHTML = (directions || []).map(d => `
    <div class="direction-card">
      <div class="direction-num">${d.id}</div>
      <div>
        <div class="direction-title">${esc(d.title)}</div>
        <div class="direction-desc">${esc(d.description)}</div>
        <div class="direction-badges">
          <span class="badge badge-${(d.impact||'').toLowerCase()}">Impact: ${esc(d.impact||'–')}</span>
          <span class="badge badge-${(d.difficulty||'').toLowerCase()}">Difficulty: ${esc(d.difficulty||'–')}</span>
        </div>
      </div>
    </div>`).join('');
}

/* ═══════════════════════════════════════════════════════════════════════════
   RESEARCH LANDSCAPE (D3 force graph)
═══════════════════════════════════════════════════════════════════════════ */
let _graphRendered = false;

async function loadLandscape() {
  if (_graphRendered) return;
  const overlay = document.getElementById('graphLoading');
  overlay.style.display = 'flex';

  try {
    const data = await API.get('/api/landscape');
    overlay.style.display = 'none';
    renderGraph(data.nodes, data.links);
    _graphRendered = true;
  } catch (err) {
    overlay.innerHTML = `<div style="color:var(--red)">Failed to load graph: ${esc(err.message)}</div>`;
  }
}

function renderGraph(nodes, links) {
  const container = document.getElementById('graphContainer');
  const svgEl     = document.getElementById('graphSvg');
  while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild);

  const W = container.clientWidth  || 900;
  const H = container.clientHeight || 520;

  const svg   = d3.select(svgEl).attr('viewBox', `0 0 ${W} ${H}`);
  const zoom  = d3.zoom().scaleExtent([0.25, 4])
                   .on('zoom', e => g.attr('transform', e.transform));
  svg.call(zoom);
  const g = svg.append('g');

  /* Arrow marker for links */
  svg.append('defs').append('marker')
    .attr('id','arrowhead').attr('viewBox','0 -4 8 8').attr('refX',16).attr('refY',0)
    .attr('markerWidth',6).attr('markerHeight',6).attr('orient','auto')
    .append('path').attr('d','M0,-4L8,0L0,4').attr('fill','#3d4451');

  const COLOR = { paper:'#6366f1', topic:'#10b981', method:'#f59e0b', dataset:'#ef4444' };
  const RADIUS = { paper: 16, topic: 11, method: 11, dataset: 9 };

  const sim = d3.forceSimulation(nodes)
    .force('link',    d3.forceLink(links).id(d => d.id).distance(90).strength(0.4))
    .force('charge',  d3.forceManyBody().strength(-220))
    .force('center',  d3.forceCenter(W/2, H/2))
    .force('collide', d3.forceCollide(d => (RADIUS[d.group]||10) + 10))
    .force('x',       d3.forceX(W/2).strength(0.04))
    .force('y',       d3.forceY(H/2).strength(0.04));

  const link = g.append('g').selectAll('line').data(links).join('line')
    .attr('class','graph-link')
    .attr('marker-end','url(#arrowhead)');

  const node = g.append('g').selectAll('g').data(nodes).join('g')
    .attr('class','graph-node')
    .call(d3.drag()
      .on('start', (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; })
      .on('drag',  (e, d) => { d.fx=e.x; d.fy=e.y; })
      .on('end',   (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx=null; d.fy=null; }));

  node.append('circle')
    .attr('r',    d => RADIUS[d.group]||10)
    .attr('fill', d => COLOR[d.group]||'#7a8898')
    .attr('fill-opacity', d => d.group==='paper' ? 0.9 : 0.7)
    .attr('stroke', d => COLOR[d.group]||'#7a8898')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.5);

  node.append('text').attr('class','graph-label')
    .attr('dy', d => (RADIUS[d.group]||10) + 12)
    .attr('text-anchor','middle')
    .text(d => d.label.slice(0,22));

  /* Tooltip */
  const tip = d3.select(container).append('div')
    .style('position','absolute').style('pointer-events','none').style('opacity',0)
    .style('background','var(--surface2)').style('border','1px solid var(--border2)')
    .style('border-radius','6px').style('padding','.4rem .7rem')
    .style('font-size','.73rem').style('color','var(--text)').style('z-index','10')
    .style('max-width','220px').style('line-height','1.4');

  node.on('mouseover', (e, d) => {
    tip.style('opacity',1).html(`<strong>${esc(d.label)}</strong><br><span style="color:var(--muted)">${d.group}</span>`);
  }).on('mousemove', e => {
    tip.style('left', (e.offsetX+14)+'px').style('top', (e.offsetY-30)+'px');
  }).on('mouseleave', () => tip.style('opacity',0));

  sim.on('tick', () => {
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  /* Initial zoom-to-fit after sim settles */
  sim.on('end', () => {
    const bounds  = g.node().getBBox();
    const scale   = Math.min(0.85, Math.min(W/bounds.width, H/bounds.height));
    const tx = W/2 - scale*(bounds.x + bounds.width/2);
    const ty = H/2 - scale*(bounds.y + bounds.height/2);
    svg.call(zoom.transform, d3.zoomIdentity.translate(tx,ty).scale(scale));
  });
}

/* ═══════════════════════════════════════════════════════════════════════════
   LITERATURE REVIEW
═══════════════════════════════════════════════════════════════════════════ */
async function loadReviewList() {
  if (!State.papers.length) {
    try { State.papers = await API.get('/api/papers'); } catch {}
  }
  document.getElementById('reviewCheckList').innerHTML = State.papers.map(p => `
    <label class="check-item">
      <input type="checkbox" name="reviewCheck" value="${p.paper_id}" checked/>
      ${esc(p.title.slice(0,48))}${p.title.length > 48 ? '…' : ''}
    </label>`).join('');
}

document.getElementById('generateReviewBtn').addEventListener('click', async () => {
  const ids = [...document.querySelectorAll('[name=reviewCheck]:checked')].map(c => c.value);
  if (!ids.length) { toast('Select at least one paper', 'error'); return; }

  const btn = document.getElementById('generateReviewBtn');
  btn.disabled = true;
  btn.innerHTML = spinner('Generating…');

  try {
    const data = await API.post('/api/review', { paper_ids: ids });
    document.getElementById('reviewContent').innerHTML = renderMarkdown(data.review);
    document.getElementById('reviewMode').textContent =
      data.mode === 'watsonx'
        ? '✓ Generated by IBM Granite'
        : '⚠ Demo review — connect IBM watsonx for personalised AI-generated content';
    document.getElementById('reviewResult').classList.remove('hidden');
  } catch (err) {
    toast('Review generation failed: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14" style="margin-right:.3rem"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clip-rule="evenodd"/></svg>Generate Review`;
  }
});

document.getElementById('copyReviewBtn').addEventListener('click', () => {
  const text = document.getElementById('reviewContent').innerText;
  navigator.clipboard.writeText(text).then(
    ()  => toast('Copied to clipboard', 'success'),
    ()  => toast('Copy failed — use Ctrl+A / Cmd+A to select manually', 'error')
  );
});

/* ═══════════════════════════════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════════════════════════════ */
(async function init() {
  await checkStatus();
  await loadDashboard();
})();
