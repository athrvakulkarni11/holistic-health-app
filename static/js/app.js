/**
 * HolisticAI — Main Application JavaScript
 * Controls: Form Analysis, Chat Interface, File Upload
 */
document.addEventListener('DOMContentLoaded', () => {
    // ═══════════════════════════════════════════════════
    //   ELEMENT REFERENCES
    // ═══════════════════════════════════════════════════
    const navLinks = document.querySelectorAll('.nav-links li');
    const tabContents = document.querySelectorAll('.tab-content');
    const pageHeading = document.getElementById('page-heading');
    const pageSubtitle = document.getElementById('page-subtitle');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');

    // Form Tab
    const form = document.getElementById('biomarker-form');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    const resultsSection = document.getElementById('results-section');
    const inputSection = document.getElementById('input-section');
    const backBtn = document.getElementById('back-to-form-btn');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');
    const fillDemoBtn = document.getElementById('fill-demo-btn');

    // Chat Tab
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatFileInput = document.getElementById('chat-file-input');
    const chatFilePreview = document.getElementById('chat-file-preview');
    const chatFileName = document.getElementById('chat-file-name');
    const chatFileRemove = document.getElementById('chat-file-remove');

    // Upload Tab
    const uploadDropZone = document.getElementById('upload-drop-zone');
    const uploadFileInput = document.getElementById('upload-file-input');
    const uploadProgress = document.getElementById('upload-progress');
    const uploadProgressBar = document.getElementById('upload-progress-bar');
    const uploadProgressText = document.getElementById('upload-progress-text');
    const uploadFileNameEl = document.getElementById('upload-file-name');
    const uploadResultsCard = document.getElementById('upload-results-card');
    const rawTextToggle = document.getElementById('raw-text-toggle');
    const rawTextContent = document.getElementById('raw-text-content');
    const rawTextDisplay = document.getElementById('raw-text-display');
    const extractedBiomarkersGrid = document.getElementById('extracted-biomarkers-grid');
    const uploadAnotherBtn = document.getElementById('upload-another-btn');
    const runAnalysisBtn = document.getElementById('run-analysis-btn');
    const uploadAnalysisResults = document.getElementById('upload-analysis-results');
    const uploadBackBtn = document.getElementById('upload-back-btn');

    // State
    let chatSessionId = null;
    let chatSelectedFile = null;
    let lastUploadedData = null;

    // ═══════════════════════════════════════════════════
    //   DISCLAIMER MODAL
    // ═══════════════════════════════════════════════════
    const disclaimerModal = document.getElementById('disclaimer-modal');
    const agreeCheckbox = document.getElementById('agree-checkbox');
    const acceptDisclaimerBtn = document.getElementById('accept-disclaimer-btn');

    // Check if previously accepted
    if (!localStorage.getItem('medical_disclaimer_accepted')) {
        // Show modal after a short delay
        setTimeout(() => {
            disclaimerModal.classList.add('active');
        }, 800);
    } else {
        // Already accepted, ensure it's hidden
        disclaimerModal.classList.remove('active');
    }

    agreeCheckbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            acceptDisclaimerBtn.removeAttribute('disabled');
        } else {
            acceptDisclaimerBtn.setAttribute('disabled', 'true');
        }
    });

    acceptDisclaimerBtn.addEventListener('click', () => {
        localStorage.setItem('medical_disclaimer_accepted', 'true');
        disclaimerModal.classList.remove('active');
        showToast('Welcome to HolisticAI. Stay healthy!', 'success');
    });

    // ═══════════════════════════════════════════════════
    //   TAB NAVIGATION
    // ═══════════════════════════════════════════════════
    const tabConfig = {
        'form-tab': { heading: 'Biomarker Analysis', subtitle: 'Unlock insights from your blood work using AI.' },
        'chat-tab': { heading: 'Chat with AI', subtitle: 'Ask health questions, get evidence-based answers.' },
        'upload-tab': { heading: 'Upload Lab Reports', subtitle: 'Upload files and extract biomarkers automatically.' },
    };

    navLinks.forEach(li => {
        li.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = li.getAttribute('data-tab');
            switchTab(tabId);
            // Close mobile sidebar
            sidebar.classList.remove('open');
        });
    });

    function switchTab(tabId) {
        navLinks.forEach(l => l.classList.remove('active'));
        tabContents.forEach(t => t.classList.remove('active'));

        const activeNav = document.querySelector(`[data-tab="${tabId}"]`);
        const activeTab = document.getElementById(tabId);

        if (activeNav) activeNav.classList.add('active');
        if (activeTab) activeTab.classList.add('active');

        const config = tabConfig[tabId];
        if (config) {
            pageHeading.textContent = config.heading;
            pageSubtitle.textContent = config.subtitle;
        }
    }

    // Mobile menu
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // ═══════════════════════════════════════════════════
    //   TAB 1: BIOMARKER FORM
    // ═══════════════════════════════════════════════════
    const loadingMessages = [
        "Consulting medical knowledge base...",
        "Searching latest clinical research via Google...",
        "Analyzing biomarker deviations...",
        "Generating personalized health insights...",
        "Formulating dietary recommendations..."
    ];
    let messageInterval;

    fillDemoBtn.addEventListener('click', () => {
        document.getElementById('age').value = 45;
        document.getElementById('gender').value = 'male';
        document.getElementById('height').value = 178;
        document.getElementById('weight').value = 85;
        document.getElementById('hemoglobin').value = 14.2;
        document.getElementById('rbc_count').value = 4.8;
        document.getElementById('ferritin').value = 280;
        document.getElementById('vitamin_b12').value = 350;
        document.getElementById('vitamin_d').value = 22;
        document.getElementById('fasting_glucose').value = 105;
        document.getElementById('hba1c').value = 5.8;
        document.getElementById('total_cholesterol').value = 210;
        document.getElementById('ldl').value = 130;
        document.getElementById('hdl').value = 45;
        document.getElementById('triglycerides').value = 160;
        document.getElementById('hs_crp').value = 2.5;
        document.getElementById('tsh').value = 2.1;
        document.getElementById('sgpt_alt').value = 35;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = {
            profile: {
                age: parseInt(formData.get('age')),
                gender: formData.get('gender'),
                height: parseFloat(formData.get('height')) || null,
                weight: parseFloat(formData.get('weight')) || null
            },
            biomarkers: {}
        };

        const biomarkerFields = [
            'hemoglobin', 'rbc_count', 'ferritin', 'vitamin_b12', 'vitamin_d',
            'fasting_glucose', 'hba1c', 'total_cholesterol', 'ldl', 'hdl',
            'triglycerides', 'hs_crp', 'tsh', 'sgpt_alt'
        ];

        biomarkerFields.forEach(field => {
            const val = formData.get(field);
            if (val) data.biomarkers[field] = parseFloat(val);
        });

        showLoading();

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => null);
                throw new Error(errData?.detail || 'Analysis failed');
            }

            const result = await response.json();
            renderFormResults(result);

            setTimeout(() => {
                hideLoading();
                inputSection.classList.add('hidden');
                resultsSection.classList.remove('hidden');
                animateScoreHealth(result.risk_score.score, '.score-ring .ring-progress', 'main-score');
            }, 800);

        } catch (err) {
            console.error(err);
            hideLoading();
            showToast('Analysis failed: ' + err.message, 'error');
        }
    });

    backBtn.addEventListener('click', resetFormView);
    newAnalysisBtn.addEventListener('click', () => {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab) {
            if (activeTab.id === 'form-tab') resetFormView();
            else if (activeTab.id === 'upload-tab') resetUploadView();
        }
    });

    function resetFormView() {
        resultsSection.classList.add('hidden');
        inputSection.classList.remove('hidden');
        form.reset();
        window.scrollTo(0, 0);
    }

    function showLoading() {
        loadingOverlay.classList.remove('hidden');
        let msgIndex = 0;
        loadingText.textContent = loadingMessages[0];
        messageInterval = setInterval(() => {
            msgIndex = (msgIndex + 1) % loadingMessages.length;
            loadingText.textContent = loadingMessages[msgIndex];
        }, 1500);
    }

    function hideLoading() {
        loadingOverlay.classList.add('hidden');
        clearInterval(messageInterval);
    }

    function renderFormResults(data) {
        const analysis = data.analysis;
        const score = data.risk_score;

        // score.score is now HEALTH SCORE (higher = healthier), no inversion needed
        const healthScore = score.score;
        document.getElementById('main-score').setAttribute('data-target', healthScore);

        document.getElementById('score-level').textContent =
            healthScore > 80 ? "Excellent Health Status" :
                healthScore > 60 ? "Good Health Status" :
                    healthScore > 40 ? "Needs Attention" : "High Risk Indicators";

        document.getElementById('score-summary').textContent = analysis.summary || "Analysis complete.";
        document.getElementById('abnormal-count').textContent = `${score.abnormal_markers || 0} Abnormal Markers`;
        document.getElementById('risk-count').textContent = `${analysis.health_risks ? analysis.health_risks.length : 0} Risks Identified`;

        // Score breakdown, explanation & priority actions
        renderScoreBreakdown(score.category_scores, 'score-breakdown');
        renderScoreExplanation(analysis.score_explanation, 'score-interpretation', 'score-top-contributors');
        renderPriorityActions(analysis.priority_actions, 'priority-actions-list');

        renderFindings('key-findings-list', analysis.key_findings);
        renderRisks('health-risks-list', analysis.health_risks);
        renderList('nutrition-list', analysis.dietary_recommendations, item =>
            `<strong>${item.category}:</strong> ${item.items.join(', ')} -- ${item.reason}`);
        renderList('lifestyle-list', analysis.lifestyle_recommendations, item =>
            `<strong>${item.priority ? item.priority.toUpperCase() : 'ADVICE'}:</strong> ${item.recommendation}`);
        renderList('supplements-list', analysis.supplement_suggestions, item =>
            `<strong>${item.supplement}:</strong> ${item.dosage}${item.duration ? ' (' + item.duration + ')' : ''} -- ${item.reason}`);
        renderFollowUp('follow-up-list', analysis.follow_up_tests);
        renderPositiveFindings(analysis.positive_findings, 'positive-findings-section', 'positive-findings-list');
        renderWebSources(data.web_sources, 'web-sources-section', 'web-sources-list');
    }

    function renderFindings(elementId, findings) {
        const el = document.getElementById(elementId);
        el.innerHTML = '';
        if (!findings) return;
        findings.forEach(f => {
            const statusClass = f.status === 'high' ? 'high' : f.status === 'low' ? 'low' : 'normal';
            const div = document.createElement('div');
            div.className = `finding-item ${statusClass}`;
            div.innerHTML = `
                <div class="finding-header">
                    <span class="finding-name">${f.biomarker || 'Biomarker'}</span>
                    <span class="finding-status">${(f.status || '').toUpperCase()}</span>
                </div>
                <p style="color: var(--text-muted); margin: 0; font-size: 0.88rem;">${f.explanation || ''}</p>`;
            el.appendChild(div);
        });
    }

    function renderRisks(elementId, risks) {
        const el = document.getElementById(elementId);
        el.innerHTML = '';
        if (!risks) return;
        risks.forEach(r => {
            const div = document.createElement('div');
            div.className = 'risk-item';
            div.innerHTML = `
                <div class="risk-header"><i class="fa-solid fa-triangle-exclamation"></i> ${r.risk}</div>
                <p style="color: var(--text-muted); margin: 0.25rem 0; font-size: 0.88rem;">${r.explanation}</p>
                <small>Preventive: ${r.preventive_actions ? r.preventive_actions.join(', ') : 'Consult doctor'}</small>`;
            el.appendChild(div);
        });
    }

    function renderList(elementId, items, formatter) {
        const el = document.getElementById(elementId);
        el.innerHTML = '';
        if (!items) return;
        items.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = formatter(item);
            el.appendChild(li);
        });
    }

    function renderFollowUp(elementId, tests) {
        const el = document.getElementById(elementId);
        el.innerHTML = '';
        if (!tests) return;
        tests.forEach(t => {
            const span = document.createElement('span');
            span.className = 'status-tag';
            span.textContent = `${t.test}${t.timeframe ? ' (' + t.timeframe + ')' : ''}`;
            el.appendChild(span);
        });
    }

    // ─── Score Breakdown (Category Bars) ─────────
    // health_score: 100 = healthy, 0 = critical
    function renderScoreBreakdown(categoryScores, containerId) {
        const el = document.getElementById(containerId);
        el.innerHTML = '';
        if (!categoryScores || Object.keys(categoryScores).length === 0) {
            el.innerHTML = '<p style="color:var(--text-dim);">No category breakdown available.</p>';
            return;
        }

        // Sort by health_score ascending (worst categories first)
        const sorted = Object.entries(categoryScores)
            .sort(([, a], [, b]) => a.health_score - b.health_score);

        sorted.forEach(([catKey, cs]) => {
            const hs = cs.health_score;
            // Colors: green = healthy (high score), red = critical (low score)
            const colorClass = hs >= 80 ? 'green' : hs >= 55 ? 'yellow' : hs >= 30 ? 'orange' : 'red';
            const colorVal = hs >= 80 ? 'var(--success)' : hs >= 55 ? 'var(--warning)' : hs >= 30 ? '#f97316' : 'var(--danger)';

            // Status badge
            const statusLabel = cs.status_label || (hs >= 90 ? 'Healthy' : hs >= 70 ? 'Mild Concern' : hs >= 40 ? 'Needs Attention' : 'High Risk');
            const statusClass = hs >= 90 ? 'healthy' : hs >= 70 ? 'concern' : hs >= 40 ? 'attention' : 'risk';

            const row = document.createElement('div');
            row.className = 'score-cat-row';
            row.innerHTML = `
                <div class="score-cat-icon" style="color:${colorVal};border-color:${colorVal}30;">
                    <i class="fa-solid fa-${cs.icon || 'circle'}"></i>
                </div>
                <div class="score-cat-info">
                    <div class="score-cat-label">
                        <span class="score-cat-name">${cs.label}
                            <span class="score-cat-status ${statusClass}">${statusLabel}</span>
                        </span>
                        <span class="score-cat-value" style="color:${colorVal}">${hs}/100</span>
                    </div>
                    <div class="score-cat-bar">
                        <div class="score-cat-fill ${colorClass}" data-width="${hs}"></div>
                    </div>
                    <div class="score-cat-markers">${cs.abnormal_markers}/${cs.total_markers} markers abnormal</div>
                </div>`;
            el.appendChild(row);
        });

        // Animate bars after a brief delay
        setTimeout(() => {
            el.querySelectorAll('.score-cat-fill').forEach(bar => {
                bar.style.width = bar.getAttribute('data-width') + '%';
            });
        }, 200);
    }

    // ─── Score Explanation (LLM Interpretation) ──
    function renderScoreExplanation(scoreExplanation, interpretationId, contributorsId) {
        const interpEl = document.getElementById(interpretationId);
        const contribEl = document.getElementById(contributorsId);

        if (!scoreExplanation) {
            interpEl.textContent = 'Score explanation not available.';
            contribEl.innerHTML = '';
            return;
        }

        interpEl.textContent = scoreExplanation.interpretation || 'Score explanation not available.';

        contribEl.innerHTML = '';
        const contributors = scoreExplanation.top_contributors || [];
        contributors.forEach(c => {
            const impactNum = parseFloat(String(c.impact).replace(/[^0-9.-]/g, '')) || 0;
            const impactClass = Math.abs(impactNum) > 15 ? 'high-impact' : Math.abs(impactNum) > 8 ? 'med-impact' : 'low-impact';
            const chip = document.createElement('span');
            chip.className = `contributor-chip ${impactClass}`;
            chip.innerHTML = `<i class="fa-solid fa-arrow-down"></i> ${c.category}: ${c.impact}`;
            contribEl.appendChild(chip);
        });
    }

    // ─── Priority Action Plan ────────────────────
    function renderPriorityActions(actions, containerId) {
        const el = document.getElementById(containerId);
        el.innerHTML = '';
        if (!actions || actions.length === 0) {
            el.innerHTML = '<p style="color:var(--text-dim);">No priority actions available.</p>';
            return;
        }

        actions.forEach((item, idx) => {
            const urgency = item.urgency || '';
            const urgencyLabel = urgency.replace(/_/g, ' ');
            const div = document.createElement('div');
            div.className = 'priority-item';
            div.setAttribute('data-urgency', urgency);
            div.innerHTML = `
                <div class="priority-number">${item.priority || idx + 1}</div>
                <div class="priority-content">
                    <div class="priority-action-text">${item.action || ''}</div>
                    <div class="priority-rationale">${item.rationale || ''}</div>
                    <div class="priority-meta">
                        ${urgency ? `<span class="urgency-badge ${urgency}">${urgencyLabel}</span>` : ''}
                        ${item.category ? `<span class="category-badge">${item.category}</span>` : ''}
                    </div>
                </div>`;
            el.appendChild(div);
        });
    }

    // animateScoreHealth: score is already health score (0-100, higher = healthier)
    function animateScoreHealth(healthScore, ringSelector, scoreElId) {
        const circle = document.querySelector(ringSelector);
        if (!circle) return;
        const radius = circle.r.baseVal.value;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (healthScore / 100) * circumference;

        circle.style.strokeDashoffset = circumference;

        setTimeout(() => {
            circle.style.strokeDashoffset = offset;
            if (healthScore > 80) circle.style.stroke = '#10b981';
            else if (healthScore > 50) circle.style.stroke = '#f59e0b';
            else circle.style.stroke = '#ef4444';
        }, 100);

        const scoreEl = document.getElementById(scoreElId);
        let current = 0;
        const target = healthScore;
        const stepTime = Math.max(10, Math.abs(Math.floor(1500 / (target || 1))));
        const timer = setInterval(() => {
            current++;
            scoreEl.textContent = current;
            if (current >= target) clearInterval(timer);
        }, stepTime);
    }

    // Render web sources
    function renderWebSources(sources, sectionId, listId) {
        const section = document.getElementById(sectionId);
        const list = document.getElementById(listId);
        list.innerHTML = '';

        if (!sources || sources.length === 0) {
            section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');
        sources.forEach(s => {
            const card = document.createElement('a');
            card.className = 'source-card';
            card.href = s.url || '#';
            card.target = '_blank';
            card.rel = 'noopener noreferrer';
            card.innerHTML = `
                <div class="source-icon"><i class="fa-solid fa-arrow-up-right-from-square"></i></div>
                <div class="source-content">
                    <span class="source-title">${s.title || 'Source'}</span>
                    <span class="source-snippet">${s.snippet || ''}</span>
                    ${s.biomarker ? `<span class="source-biomarker-tag">${s.biomarker} (${s.direction})</span>` : ''}
                </div>`;
            list.appendChild(card);
        });
    }

    // Render positive findings
    function renderPositiveFindings(positives, sectionId, listId) {
        const section = document.getElementById(sectionId);
        const list = document.getElementById(listId);
        list.innerHTML = '';

        if (!positives || positives.length === 0) {
            section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');
        positives.forEach(p => {
            const li = document.createElement('li');
            li.textContent = p;
            list.appendChild(li);
        });
    }

    // ═══════════════════════════════════════════════════
    //   TAB 2: CHAT INTERFACE
    // ═══════════════════════════════════════════════════

    // Quick prompts
    document.querySelectorAll('.quick-prompt').forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.getAttribute('data-prompt');
            chatInput.value = prompt;
            sendChatMessage();
        });
    });

    // Chat file attachment
    chatFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            chatSelectedFile = file;
            chatFileName.textContent = file.name;
            chatFilePreview.classList.remove('hidden');
        }
    });

    chatFileRemove.addEventListener('click', () => {
        chatSelectedFile = null;
        chatFileInput.value = '';
        chatFilePreview.classList.add('hidden');
    });

    // Send message
    chatSendBtn.addEventListener('click', sendChatMessage);

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });

    async function sendChatMessage() {
        const message = chatInput.value.trim();
        if (!message && !chatSelectedFile) return;

        // Remove welcome screen
        const welcome = chatMessages.querySelector('.chat-welcome');
        if (welcome) welcome.remove();

        // Display user message
        const displayMsg = message || `📎 Uploaded: ${chatSelectedFile.name}`;
        appendMessage('user', displayMsg, chatSelectedFile ? chatSelectedFile.name : null);

        // Clear input
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // Show typing indicator
        const typingEl = showTypingIndicator();

        try {
            let result;

            if (chatSelectedFile) {
                // Send with file via multipart form
                const formData = new FormData();
                formData.append('message', message || 'Please analyze this uploaded file.');
                formData.append('file', chatSelectedFile);
                if (chatSessionId) formData.append('session_id', chatSessionId);

                const response = await fetch('/api/chat/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => null);
                    throw new Error(errData?.detail || 'Request failed');
                }
                result = await response.json();

                // Clear file
                chatSelectedFile = null;
                chatFileInput.value = '';
                chatFilePreview.classList.add('hidden');

            } else {
                // Text-only chat
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: chatSessionId,
                        message: message
                    })
                });

                if (!response.ok) {
                    const errData = await response.json().catch(() => null);
                    throw new Error(errData?.detail || 'Request failed');
                }
                result = await response.json();
            }

            chatSessionId = result.session_id;
            removeTypingIndicator(typingEl);
            appendMessage('assistant', result.response);

        } catch (err) {
            removeTypingIndicator(typingEl);
            appendMessage('assistant', `⚠️ Error: ${err.message}`);
        }
    }

    function appendMessage(role, content, fileName) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;

        const avatarIcon = role === 'user' ? 'fa-user' : 'fa-robot';
        const formattedContent = formatMarkdown(content);

        let fileHtml = '';
        if (fileName) {
            fileHtml = `<div class="message-file-badge"><i class="fa-solid fa-paperclip"></i> ${escHtml(fileName)}</div>`;
        }

        msgDiv.innerHTML = `
            <div class="message-avatar"><i class="fa-solid ${avatarIcon}"></i></div>
            <div class="message-bubble">${fileHtml}${formattedContent}</div>`;

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function showTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'message assistant';
        div.id = 'typing-msg';
        div.innerHTML = `
            <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return div;
    }

    function removeTypingIndicator(el) {
        if (el && el.parentElement) el.remove();
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let html = escHtml(text);

        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Headers
        html = html.replace(/^### (.+)$/gm, '<strong style="color:var(--primary);font-size:1rem;">$1</strong>');
        html = html.replace(/^## (.+)$/gm, '<strong style="color:var(--primary);font-size:1.05rem;">$1</strong>');
        // Bullet points
        html = html.replace(/^[-•] (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul style="margin:0.5rem 0;padding-left:1.25rem;">$&</ul>');
        // Numbered list
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
        // Paragraphs
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');

        return `<p>${html}</p>`;
    }

    function escHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ═══════════════════════════════════════════════════
    //   TAB 3: FILE UPLOAD
    // ═══════════════════════════════════════════════════

    // Click to browse
    uploadDropZone.addEventListener('click', () => uploadFileInput.click());

    // Drag & drop
    uploadDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadDropZone.classList.add('dragover');
    });

    uploadDropZone.addEventListener('dragleave', () => {
        uploadDropZone.classList.remove('dragover');
    });

    uploadDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadDropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handleFileUpload(file);
    });

    uploadFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileUpload(file);
    });

    // Raw text toggle
    rawTextToggle.addEventListener('click', () => {
        rawTextContent.classList.toggle('hidden');
        rawTextToggle.classList.toggle('open');
    });

    // Upload another
    uploadAnotherBtn.addEventListener('click', resetUploadView);
    if (uploadBackBtn) uploadBackBtn.addEventListener('click', resetUploadView);

    async function handleFileUpload(file) {
        // Validate extension
        const allowedExts = ['pdf', 'png', 'jpg', 'jpeg', 'csv', 'txt', 'docx'];
        const ext = file.name.split('.').pop().toLowerCase();
        if (!allowedExts.includes(ext)) {
            showToast(`File type .${ext} not supported. Allowed: ${allowedExts.join(', ')}`, 'error');
            return;
        }

        // Validate size
        if (file.size > 10 * 1024 * 1024) {
            showToast('File too large. Maximum is 10 MB.', 'error');
            return;
        }

        // Show progress
        uploadDropZone.classList.add('hidden');
        uploadProgress.classList.remove('hidden');
        uploadFileNameEl.textContent = file.name;

        // Animate progress bar
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            uploadProgressBar.style.width = progress + '%';
            uploadProgressText.textContent = progress < 30 ? 'Uploading file...' :
                progress < 60 ? 'Extracting text...' :
                    'Identifying biomarkers...';
        }, 400);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            clearInterval(progressInterval);
            uploadProgressBar.style.width = '100%';
            uploadProgressText.textContent = 'Complete!';

            if (!response.ok) {
                const errData = await response.json().catch(() => null);
                throw new Error(errData?.detail || 'Upload failed');
            }

            const result = await response.json();

            setTimeout(() => {
                uploadProgress.classList.add('hidden');
                displayUploadResults(result);
            }, 500);

        } catch (err) {
            clearInterval(progressInterval);
            uploadProgress.classList.add('hidden');
            uploadDropZone.classList.remove('hidden');
            showToast('Upload failed: ' + err.message, 'error');
        }
    }

    function displayUploadResults(result) {
        lastUploadedData = result;
        uploadResultsCard.classList.remove('hidden');

        // Raw text
        rawTextDisplay.textContent = result.raw_text || 'No text extracted.';

        // Extracted biomarkers
        extractedBiomarkersGrid.innerHTML = '';
        const extracted = result.extracted_data || {};
        const biomarkers = extracted.biomarkers || {};

        const biomarkerNames = {
            hemoglobin: 'Hemoglobin', rbc_count: 'RBC Count', ferritin: 'Ferritin',
            vitamin_b12: 'Vitamin B12', vitamin_d: 'Vitamin D', fasting_glucose: 'Fasting Glucose',
            hba1c: 'HbA1c', total_cholesterol: 'Total Cholesterol', ldl: 'LDL', hdl: 'HDL',
            triglycerides: 'Triglycerides', hs_crp: 'hs-CRP', tsh: 'TSH', sgpt_alt: 'SGPT/ALT',
        };

        let foundAny = false;
        for (const [key, val] of Object.entries(biomarkers)) {
            if (val !== null && val !== undefined) {
                foundAny = true;
                const div = document.createElement('div');
                div.className = 'extracted-item';
                div.innerHTML = `
                    <span class="biomarker-name">${biomarkerNames[key] || key}</span>
                    <span class="biomarker-value">${val}</span>`;
                extractedBiomarkersGrid.appendChild(div);
            }
        }

        // Additional biomarkers
        const additional = extracted.additional_biomarkers || {};
        for (const [key, val] of Object.entries(additional)) {
            if (val !== null && val !== undefined) {
                foundAny = true;
                const div = document.createElement('div');
                div.className = 'extracted-item';
                div.innerHTML = `
                    <span class="biomarker-name">${key}</span>
                    <span class="biomarker-value">${val}</span>`;
                extractedBiomarkersGrid.appendChild(div);
            }
        }

        if (!foundAny) {
            extractedBiomarkersGrid.innerHTML = '<p style="color:var(--text-dim);">No biomarkers detected. The AI could not extract numerical values from the file.</p>';
        }

        // Profile
        const profile = extracted.profile || {};
        const profileSection = document.getElementById('extracted-profile-section');
        const profileInfo = document.getElementById('extracted-profile-info');

        if (profile.age || profile.gender) {
            profileSection.classList.remove('hidden');
            profileInfo.innerHTML = `
                <div class="grid-2" style="max-width:400px;">
                    ${profile.age ? `<div class="extracted-item"><span class="biomarker-name">Age</span><span class="biomarker-value">${profile.age}</span></div>` : ''}
                    ${profile.gender ? `<div class="extracted-item"><span class="biomarker-name">Gender</span><span class="biomarker-value">${profile.gender}</span></div>` : ''}
                </div>`;

            // Pre-fill override fields
            if (profile.age) document.getElementById('upload-age').value = profile.age;
            if (profile.gender) {
                const g = profile.gender.toLowerCase();
                if (g === 'male' || g === 'm') document.getElementById('upload-gender').value = 'male';
                if (g === 'female' || g === 'f') document.getElementById('upload-gender').value = 'female';
            }
        } else {
            profileSection.classList.add('hidden');
        }
    }

    // Run analysis on uploaded data
    runAnalysisBtn.addEventListener('click', async () => {
        if (!lastUploadedData || !lastUploadedData.extracted_data) {
            showToast('No extracted data available. Upload a file first.', 'error');
            return;
        }

        const extracted = lastUploadedData.extracted_data;
        const biomarkers = extracted.biomarkers || {};
        const cleanBiomarkers = {};
        for (const [k, v] of Object.entries(biomarkers)) {
            if (v !== null && v !== undefined) cleanBiomarkers[k] = v;
        }

        if (Object.keys(cleanBiomarkers).length === 0) {
            showToast('No biomarker values were extracted. Cannot run analysis.', 'error');
            return;
        }

        // Get profile
        const age = parseInt(document.getElementById('upload-age').value);
        const gender = document.getElementById('upload-gender').value;

        if (!age || !gender) {
            showToast('Please provide Age and Gender to run analysis.', 'error');
            return;
        }

        showLoading();

        try {
            const data = {
                profile: {
                    age: age,
                    gender: gender,
                    height: null,
                    weight: null,
                },
                biomarkers: cleanBiomarkers,
            };

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error('Analysis failed');

            const result = await response.json();
            renderUploadAnalysis(result);

            setTimeout(() => {
                hideLoading();
                uploadResultsCard.classList.add('hidden');
                document.querySelector('.upload-zone-card').classList.add('hidden');
                uploadAnalysisResults.classList.remove('hidden');
                animateScoreHealth(result.risk_score.score, '.upload-score-ring .ring-progress', 'upload-main-score');
            }, 800);

        } catch (err) {
            hideLoading();
            showToast('Analysis failed: ' + err.message, 'error');
        }
    });

    function renderUploadAnalysis(data) {
        const analysis = data.analysis;
        const score = data.risk_score;
        // score.score is already health score (higher = healthier)
        const healthScore = score.score;

        document.getElementById('upload-score-level').textContent =
            healthScore > 80 ? "Excellent Health Status" :
                healthScore > 60 ? "Good Health Status" :
                    healthScore > 40 ? "Needs Attention" : "High Risk Indicators";

        document.getElementById('upload-score-summary').textContent = analysis.summary || "Analysis complete.";

        renderScoreBreakdown(score.category_scores, 'upload-score-breakdown');
        renderScoreExplanation(analysis.score_explanation, 'upload-score-interpretation', 'upload-score-top-contributors');
        renderPriorityActions(analysis.priority_actions, 'upload-priority-actions');

        renderFindings('upload-key-findings', analysis.key_findings);
        renderRisks('upload-health-risks', analysis.health_risks);
        renderList('upload-nutrition', analysis.dietary_recommendations, item =>
            `<strong>${item.category}:</strong> ${item.items.join(', ')} -- ${item.reason}`);
        renderList('upload-lifestyle', analysis.lifestyle_recommendations, item =>
            `<strong>${item.priority ? item.priority.toUpperCase() : 'ADVICE'}:</strong> ${item.recommendation}`);
        renderList('upload-supplements', analysis.supplement_suggestions, item =>
            `<strong>${item.supplement}:</strong> ${item.dosage}${item.duration ? ' (' + item.duration + ')' : ''} -- ${item.reason}`);
        renderPositiveFindings(analysis.positive_findings, 'upload-positive-section', 'upload-positive-list');
        renderWebSources(data.web_sources, 'upload-sources-section', 'upload-sources-list');
    }

    function resetUploadView() {
        uploadDropZone.classList.remove('hidden');
        uploadProgress.classList.add('hidden');
        uploadResultsCard.classList.add('hidden');
        uploadAnalysisResults.classList.add('hidden');
        document.querySelector('.upload-zone-card').classList.remove('hidden');
        uploadFileInput.value = '';
        uploadProgressBar.style.width = '0%';
        lastUploadedData = null;
        rawTextContent.classList.add('hidden');
        rawTextToggle.classList.remove('open');
        document.getElementById('upload-age').value = '';
        document.getElementById('upload-gender').value = '';
    }

    // ═══════════════════════════════════════════════════
    //   TOAST NOTIFICATIONS
    // ═══════════════════════════════════════════════════
    function showToast(message, type = 'info') {
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.cssText = `
            position: fixed; bottom: 2rem; right: 2rem; z-index: 9999;
            padding: 1rem 1.5rem; border-radius: 12px;
            font-family: inherit; font-size: 0.9rem; max-width: 400px;
            backdrop-filter: blur(20px);
            animation: fadeIn 0.3s ease-out;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid ${type === 'error'
                ? 'rgba(239,68,68,0.3)'
                : 'rgba(0,242,234,0.3)'
            };
            background: ${type === 'error'
                ? 'rgba(239,68,68,0.15)'
                : 'rgba(0,242,234,0.1)'
            };
            color: ${type === 'error' ? '#fca5a5' : '#7dd3fc'};
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
});
