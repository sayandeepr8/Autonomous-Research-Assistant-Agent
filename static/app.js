/* ═══════════════════════════════════════════════════════════════
   Autonomous Research Assistant — Frontend Logic
   ═══════════════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────────
let currentSessionId = null;
let sessionData = null;

// ── Background Particles ───────────────────────────────────────
(function initParticles() {
    const container = document.getElementById('bgParticles');
    if (!container) return;
    const colors = ['#818cf8', '#c084fc', '#f472b6', '#34d399', '#38bdf8'];
    for (let i = 0; i < 20; i++) {
        const p = document.createElement('div');
        p.classList.add('particle');
        const size = Math.random() * 4 + 2;
        p.style.width = size + 'px';
        p.style.height = size + 'px';
        p.style.left = Math.random() * 100 + '%';
        p.style.top = Math.random() * 100 + '%';
        p.style.background = colors[Math.floor(Math.random() * colors.length)];
        p.style.animationDelay = Math.random() * 20 + 's';
        p.style.animationDuration = (15 + Math.random() * 20) + 's';
        container.appendChild(p);
    }
})();

// ── Quick Topic ────────────────────────────────────────────────
function setTopic(text) {
    document.getElementById('topicInput').value = text;
    document.getElementById('topicInput').focus();
}

// ── Start Research ─────────────────────────────────────────────
async function startResearch() {
    const input = document.getElementById('topicInput');
    const topic = input.value.trim();
    if (!topic) {
        input.focus();
        return;
    }

    const btn = document.getElementById('startBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span><span>Starting...</span>';

    try {
        const resp = await fetch('/api/research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic }),
        });

        const data = await resp.json();

        if (!resp.ok) {
            alert(data.error || 'Failed to start research.');
            btn.disabled = false;
            btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><span>Begin Research</span>';
            return;
        }

        currentSessionId = data.session_id;
        showWorkflowUI();
        listenToStream(currentSessionId);

    } catch (err) {
        alert('Network error: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><span>Begin Research</span>';
    }
}

// ── Show Workflow UI ───────────────────────────────────────────
function showWorkflowUI() {
    document.getElementById('inputSection').classList.add('hidden');
    document.getElementById('workflowSection').classList.remove('hidden');
    document.getElementById('feedSection').classList.remove('hidden');
    document.getElementById('workflowSection').classList.add('fade-in-up');
    document.getElementById('feedSection').classList.add('fade-in-up');
}

// ── SSE Listener ───────────────────────────────────────────────
function listenToStream(sessionId) {
    const evtSource = new EventSource(`/api/research/${sessionId}/stream`);

    evtSource.onmessage = function (e) {
        try {
            const event = JSON.parse(e.data);
            handleEvent(event);

            if (['done', 'error', 'complete'].includes(event.stage)) {
                evtSource.close();
                if (event.stage !== 'error') {
                    fetchFinalResults(sessionId);
                }
            }
        } catch (err) {
            console.error('SSE parse error:', err);
        }
    };

    evtSource.onerror = function () {
        evtSource.close();
        addFeedItem('Connection lost. Attempting to load results...');
        setTimeout(() => fetchFinalResults(sessionId), 3000);
    };
}

// ── Event Handler ──────────────────────────────────────────────
const agentStageMap = {
    planning: 'agentPlanner',
    planning_done: 'agentPlanner',
    retrieving: 'agentRetriever',
    retrieving_done: 'agentRetriever',
    analyzing: 'agentAnalyzer',
    analyzing_done: 'agentAnalyzer',
    critiquing: 'agentCritic',
    critiquing_done: 'agentCritic',
    reporting: 'agentReporter',
    reporting_done: 'agentReporter',
    refining: 'agentPlanner',
    refining_done: 'agentPlanner',
};

const activeSet = new Set();
let currentIteration = 0;

function handleEvent(event) {
    const { stage, message, data } = event;

    // Update activity feed
    addFeedItem(message);

    // Update agent pipeline
    const agentId = agentStageMap[stage];
    if (agentId) {
        const node = document.getElementById(agentId);
        if (stage.endsWith('_done')) {
            node.classList.remove('active');
            node.classList.add('completed');
            node.querySelector('.agent-status').textContent = 'Done';
            activeSet.delete(agentId);
            // Activate connector
            activateConnectorBefore(agentId);
        } else {
            // Reset completed state if we're iterating
            node.classList.remove('completed');
            node.classList.add('active');
            node.querySelector('.agent-status').textContent = 'Working...';
            activeSet.add(agentId);
        }
    }

    // Handle iteration tracking
    if (stage === 'iteration_start') {
        currentIteration++;
        const bar = document.getElementById('iterationBar');
        bar.classList.remove('hidden');
        const badges = document.getElementById('iterationBadges');
        const badge = document.createElement('span');
        badge.className = 'iter-badge active';
        badge.textContent = `Iteration ${currentIteration}`;
        badge.id = `iterBadge${currentIteration}`;
        badges.appendChild(badge);

        // Reset agent nodes for new iteration
        resetAgentNodes();
    }

    if (stage === 'iteration_accepted') {
        const badge = document.getElementById(`iterBadge${currentIteration}`);
        if (badge) {
            badge.classList.remove('active');
            badge.classList.add('done');
            badge.textContent += ' ✓';
        }
    }

    // Store intermediate data
    if (stage === 'planning_done' && data) {
        sessionData = sessionData || {};
        sessionData.plan = data;
    }
    if (stage === 'analyzing_done' && data) {
        sessionData = sessionData || {};
        sessionData.analysis = data;
    }
    if (stage === 'critiquing_done' && data) {
        sessionData = sessionData || {};
        sessionData.critic_evaluation = data;
    }
    if (stage === 'complete' && data) {
        sessionData = sessionData || {};
        Object.assign(sessionData, data);
    }
}

function resetAgentNodes() {
    ['agentPlanner', 'agentRetriever', 'agentAnalyzer', 'agentCritic', 'agentReporter'].forEach(id => {
        const node = document.getElementById(id);
        node.classList.remove('active', 'completed');
        node.querySelector('.agent-status').textContent = 'Waiting';
    });
    // Reset connectors
    document.querySelectorAll('.pipeline-connector').forEach(c => c.classList.remove('active'));
}

function activateConnectorBefore(agentId) {
    const node = document.getElementById(agentId);
    const prev = node.previousElementSibling;
    if (prev && prev.classList.contains('pipeline-connector')) {
        prev.classList.add('active');
    }
}

// ── Activity Feed ──────────────────────────────────────────────
function addFeedItem(message) {
    const feed = document.getElementById('activityFeed');
    const item = document.createElement('div');
    item.className = 'feed-item';

    const now = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    item.innerHTML = `
        <span class="feed-time">${now}</span>
        <span class="feed-msg">${escapeHtml(message)}</span>
    `;

    feed.appendChild(item);
    feed.scrollTop = feed.scrollHeight;
}

// ── Fetch Final Results ────────────────────────────────────────
async function fetchFinalResults(sessionId) {
    let retries = 0;
    const maxRetries = 10;

    while (retries < maxRetries) {
        try {
            const resp = await fetch(`/api/research/${sessionId}`);
            if (resp.ok) {
                sessionData = await resp.json();
                renderResults(sessionData);
                return;
            }
        } catch (err) {
            console.error('Fetch error:', err);
        }
        retries++;
        await new Promise(r => setTimeout(r, 3000));
    }

    addFeedItem('❌ Could not load final results. Please refresh the page.');
}

// ── Render Results ─────────────────────────────────────────────
function renderResults(data) {
    const section = document.getElementById('resultsSection');
    section.classList.remove('hidden');
    section.classList.add('fade-in-up');
    document.getElementById('newResearchBtn').classList.remove('hidden');

    // Stats
    const totalPapers = countUniquePapers(data.papers || {});
    const iterations = (data.iterations || []).length;
    const coverage = (data.critic_evaluation || {}).overall_coverage_score || 'N/A';
    const clusters = ((data.analysis || {}).thematic_clusters || []).length;

    animateCounter('statPapersVal', totalPapers);
    animateCounter('statIterationsVal', iterations);
    document.getElementById('statCoverageVal').textContent = coverage + '/10';
    animateCounter('statClustersVal', clusters);

    // Render tabs
    renderReport(data.final_report || '');
    renderPlan(data.plan || {});
    renderAnalysis(data.analysis || {});
    renderCritic(data.critic_evaluation || {});
    renderPapers(data.papers || {});
    renderLog(data.agent_log || []);
}

function countUniquePapers(papers) {
    const ids = new Set();
    for (const [, list] of Object.entries(papers)) {
        for (const p of list) {
            if (p.arxiv_id) ids.add(p.arxiv_id);
        }
    }
    return ids.size;
}

function animateCounter(id, target) {
    const el = document.getElementById(id);
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 30));
    const interval = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(interval);
        }
        el.textContent = current;
    }, 40);
}

// ── Render: Report ─────────────────────────────────────────────
function renderReport(markdown) {
    const container = document.getElementById('reportContent');
    container.innerHTML = simpleMarkdown(markdown);
}

// ── Render: Plan ───────────────────────────────────────────────
function renderPlan(plan) {
    const container = document.getElementById('planContent');
    let html = `<div class="plan-topic">📌 ${escapeHtml(plan.main_topic || 'Research Topic')}</div>`;

    if (plan.scope_notes) {
        html += `<p style="color: var(--text-secondary); margin-bottom: 24px; font-style: italic;">${escapeHtml(plan.scope_notes)}</p>`;
    }

    // Research questions
    html += `<div class="plan-block"><div class="plan-block-title">❓ Research Questions</div>`;
    for (const q of (plan.research_questions || [])) {
        html += `<div class="question-card">
            <div class="question-id">${escapeHtml(q.id || '')}</div>
            <div class="question-text">${escapeHtml(q.question || '')}</div>
            <div class="question-meta">
                <span class="meta-tag category">${escapeHtml(q.category || 'general')}</span>
                <span class="meta-tag priority-${q.priority || 'medium'}">${escapeHtml(q.priority || 'medium')}</span>
            </div>
        </div>`;
    }
    html += `</div>`;

    // Search queries
    html += `<div class="plan-block"><div class="plan-block-title">🔍 Search Queries</div>`;
    for (const s of (plan.search_queries || [])) {
        html += `<div class="query-card">
            <div class="question-id">${escapeHtml(s.id || '')} → ${(s.targets_questions || []).join(', ')}</div>
            <div class="query-text">${escapeHtml(s.query || '')}</div>
            <div class="query-rationale">${escapeHtml(s.rationale || '')}</div>
        </div>`;
    }
    html += `</div>`;

    container.innerHTML = html;
}

// ── Render: Analysis ───────────────────────────────────────────
function renderAnalysis(analysis) {
    const container = document.getElementById('analysisContent');
    let html = '';

    // Thematic clusters
    html += `<div class="plan-block"><div class="plan-block-title">🔗 Thematic Clusters</div>`;
    for (const c of (analysis.thematic_clusters || [])) {
        html += `<div class="cluster-card">
            <div class="cluster-theme">${escapeHtml(c.theme || '')}</div>
            <div class="cluster-desc">${escapeHtml(c.description || '')}</div>
            <ul class="cluster-findings">
                ${(c.key_findings || []).map(f => `<li>${escapeHtml(f)}</li>`).join('')}
            </ul>
            <div class="paper-meta" style="margin-top:8px">
                ${(c.paper_ids || []).map(id => `<span class="paper-cat">${escapeHtml(id)}</span>`).join('')}
            </div>
        </div>`;
    }
    html += `</div>`;

    // Question coverage
    html += `<div class="plan-block"><div class="plan-block-title">📊 Question Coverage</div>`;
    for (const cov of (analysis.question_coverage || [])) {
        const level = cov.coverage_level || 'not_covered';
        html += `<div class="coverage-card ${level}">
            <div class="coverage-level">${escapeHtml(cov.question_id || '')} — ${level.replace('_', ' ')}</div>
            <div class="question-text" style="margin-bottom:6px">${escapeHtml(cov.question_text || '')}</div>
            <div class="coverage-summary">${escapeHtml(cov.summary || '')}</div>
        </div>`;
    }
    html += `</div>`;

    // Methodology landscape
    const methods = analysis.methodology_landscape || {};
    if (Object.keys(methods).length) {
        html += `<div class="plan-block"><div class="plan-block-title">🧪 Methodology Landscape</div>`;
        html += `<div class="cluster-card">`;
        if (methods.dominant_methods) {
            html += `<p style="margin-bottom:8px"><strong style="color:var(--text-primary)">Dominant:</strong> ${escapeHtml((methods.dominant_methods || []).join(', '))}</p>`;
        }
        if (methods.emerging_methods) {
            html += `<p style="margin-bottom:8px"><strong style="color:var(--text-primary)">Emerging:</strong> ${escapeHtml((methods.emerging_methods || []).join(', '))}</p>`;
        }
        if (methods.comparison_notes) {
            html += `<p style="color:var(--text-secondary);font-style:italic">${escapeHtml(methods.comparison_notes)}</p>`;
        }
        html += `</div></div>`;
    }

    // Cross-cutting insights
    const insights = analysis.cross_cutting_insights || [];
    if (insights.length) {
        html += `<div class="plan-block"><div class="plan-block-title">💡 Cross-Cutting Insights</div>`;
        html += `<ul class="cluster-findings">`;
        for (const ins of insights) {
            html += `<li>${escapeHtml(ins)}</li>`;
        }
        html += `</ul></div>`;
    }

    container.innerHTML = html;
}

// ── Render: Critic ─────────────────────────────────────────────
function renderCritic(critic) {
    const container = document.getElementById('criticContent');
    const score = critic.overall_coverage_score || 0;

    let html = `
        <div class="critic-score-ring">
            <svg class="score-ring-svg" viewBox="0 0 120 120">
                <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#818cf8"/>
                        <stop offset="100%" stop-color="#c084fc"/>
                    </linearGradient>
                </defs>
                <circle class="score-ring-bg" cx="60" cy="60" r="50"/>
                <circle class="score-ring-fill" cx="60" cy="60" r="50" id="scoreRing"/>
            </svg>
            <div class="score-ring-label">
                <span class="score-ring-value">${score}</span>
                <span class="score-ring-max">/ 10</span>
            </div>
        </div>
    `;

    // Dimension scores
    const dims = critic.dimension_scores || {};
    if (Object.keys(dims).length) {
        html += `<div class="dimension-grid">`;
        for (const [name, val] of Object.entries(dims)) {
            html += `<div class="dimension-card">
                <div class="dimension-name">${escapeHtml(name.replace('_', ' '))}</div>
                <div class="dimension-score">${val}/10</div>
                <div class="dim-bar"><div class="dim-bar-fill" style="width: ${val * 10}%"></div></div>
            </div>`;
        }
        html += `</div>`;
    }

    // Recommendation
    const rec = critic.recommendation || 'N/A';
    const recColor = rec === 'accept' ? 'var(--accent-4)' : 'var(--accent-6)';
    html += `<div style="text-align:center;margin-bottom:24px">
        <span style="padding:6px 16px;background:rgba(52,211,153,0.1);border:1px solid ${recColor};border-radius:100px;color:${recColor};font-size:0.82rem;font-weight:600;text-transform:uppercase">${escapeHtml(rec)}</span>
    </div>`;

    // Reasoning
    if (critic.reasoning) {
        html += `<div class="cluster-card" style="margin-bottom:20px">
            <div class="plan-block-title">💭 Reasoning</div>
            <p style="color:var(--text-secondary);font-size:0.88rem">${escapeHtml(critic.reasoning)}</p>
        </div>`;
    }

    // Covered well
    if ((critic.covered_well || []).length) {
        html += `<div class="plan-block"><div class="plan-block-title">✅ Well Covered</div>`;
        html += `<ul class="cluster-findings">`;
        for (const item of critic.covered_well) {
            html += `<li>${escapeHtml(item)}</li>`;
        }
        html += `</ul></div>`;
    }

    // Knowledge gaps
    if ((critic.knowledge_gaps || []).length) {
        html += `<div class="plan-block"><div class="plan-block-title">⚠️ Knowledge Gaps</div>`;
        for (const gap of critic.knowledge_gaps) {
            html += `<div class="gap-card ${gap.severity || 'moderate'}">
                <div class="gap-severity">${escapeHtml(gap.severity || 'unknown')}</div>
                <div class="gap-text">${escapeHtml(gap.gap || '')}</div>
            </div>`;
        }
        html += `</div>`;
    }

    container.innerHTML = html;

    // Animate the score ring
    requestAnimationFrame(() => {
        const ring = document.getElementById('scoreRing');
        if (ring) {
            const circumference = 2 * Math.PI * 50;
            const offset = circumference - (score / 10) * circumference;
            ring.style.strokeDasharray = circumference;
            ring.style.strokeDashoffset = offset;
        }
    });
}

// ── Render: Papers ─────────────────────────────────────────────
function renderPapers(papers) {
    const container = document.getElementById('papersContent');
    const allPapers = [];
    const seen = new Set();

    for (const [, list] of Object.entries(papers)) {
        for (const p of list) {
            if (p.arxiv_id && !seen.has(p.arxiv_id)) {
                seen.add(p.arxiv_id);
                allPapers.push(p);
            }
        }
    }

    let html = `<div class="plan-block-title">📄 ${allPapers.length} Papers Retrieved</div>`;

    for (const p of allPapers) {
        html += `<div class="paper-card">
            <div class="paper-title">${escapeHtml(p.title || 'Untitled')}</div>
            <div class="paper-authors">${escapeHtml((p.authors || []).join(', '))}</div>
            <div class="paper-abstract">${escapeHtml(p.abstract || '')}</div>
            <div class="paper-meta">
                <span class="paper-date">${escapeHtml((p.published || '').slice(0, 10))}</span>
                ${(p.categories || []).slice(0, 3).map(c => `<span class="paper-cat">${escapeHtml(c)}</span>`).join('')}
                ${p.pdf_url ? `<a class="paper-link" href="${escapeHtml(p.pdf_url)}" target="_blank" rel="noopener">PDF ↗</a>` : ''}
            </div>
        </div>`;
    }

    container.innerHTML = html;
}

// ── Render: Agent Log ──────────────────────────────────────────
function renderLog(log) {
    const container = document.getElementById('logContent');
    let html = '';

    for (const entry of log) {
        const time = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString('en-US', { hour12: false }) : '';
        html += `<div class="log-entry">
            <span class="log-timestamp">${escapeHtml(time)}</span>
            <span class="log-agent">${escapeHtml(entry.agent || '')}</span>
            <span class="log-detail">${escapeHtml(entry.action || '')}${entry.detail ? ': ' + escapeHtml(entry.detail) : ''}</span>
        </div>`;
    }

    container.innerHTML = html;
}

// ── Tab Switching ──────────────────────────────────────────────
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ── Reset UI ───────────────────────────────────────────────────
function resetUI() {
    currentSessionId = null;
    sessionData = null;
    currentIteration = 0;
    activeSet.clear();

    document.getElementById('inputSection').classList.remove('hidden');
    document.getElementById('workflowSection').classList.add('hidden');
    document.getElementById('feedSection').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('newResearchBtn').classList.add('hidden');
    document.getElementById('activityFeed').innerHTML = '';
    document.getElementById('iterationBadges').innerHTML = '';
    document.getElementById('iterationBar').classList.add('hidden');

    resetAgentNodes();

    const btn = document.getElementById('startBtn');
    btn.disabled = false;
    btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><span>Begin Research</span>';

    document.getElementById('topicInput').value = '';
    document.getElementById('topicInput').focus();

    // Reset tabs
    switchTab('report');
}

// ── Utilities ──────────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

/**
 * Very simple Markdown → HTML converter for the report content.
 * Handles headings, bold, italic, lists, code, blockquotes, links, and hr.
 */
function simpleMarkdown(md) {
    if (!md) return '<p style="color:var(--text-muted)">No report generated yet.</p>';

    let html = md
        // Code blocks
        .replace(/```[\s\S]*?```/g, (match) => {
            const code = match.replace(/```\w*\n?/g, '').replace(/```$/g, '');
            return `<pre style="background:var(--bg-secondary);padding:16px;border-radius:8px;overflow-x:auto;font-family:var(--font-mono);font-size:0.82rem;margin:12px 0"><code>${escapeHtml(code)}</code></pre>`;
        })
        // Headings
        .replace(/^#### (.+)$/gm, '<h4 style="font-size:1rem;font-weight:600;color:var(--text-primary);margin:16px 0 8px">$1</h4>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        // Horizontal rules
        .replace(/^---$/gm, '<hr>')
        // Bold + Italic
        .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener" style="color:var(--accent-2);text-decoration:underline">$1</a>')
        // Blockquotes
        .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
        // Unordered lists
        .replace(/^[\-\*] (.+)$/gm, '<li>$1</li>')
        // Ordered lists
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        // Wrap consecutive <li> in <ul>
        .replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`)
        // Paragraphs (double newlines)
        .replace(/\n\n+/g, '</p><p>')
        // Single newlines within paragraphs
        .replace(/\n/g, '<br>');

    return `<p>${html}</p>`;
}

// ── Keyboard shortcut (Enter in textarea = Ctrl+Enter to submit) ──
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('topicInput');
    if (textarea) {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                startResearch();
            }
        });
    }
});
