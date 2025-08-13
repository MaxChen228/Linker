/**
 * Linker 練習頁面核心邏輯 (重構版)
 * - 採用狀態驅動 UI 模式
 * - 職責清晰，易於維護
 */
class PracticeSystem {
    constructor() {
        // 狀態管理 (Single Source of Truth)
        this.questionQueue = [];
        this.currentQuestionId = null;
        this.isSubmitting = false;
        this.generatingCount = 0;

        // DOM 元素快取
        this.elements = {
            queueContainer: document.getElementById('queue-items'),
            queueCount: document.getElementById('queue-count'),
            sandboxContent: document.getElementById('sandbox-content'),
            modeSelect: document.getElementById('mode-select'),
            lengthSelect: document.getElementById('length-select'),
            levelSelect: document.getElementById('level-select'),
            addQuestionBtn: document.getElementById('add-question-btn'),
            clearQueueBtn: document.getElementById('clear-queue-btn'),
            // Modal 相關元素
            patternModal: document.getElementById('pattern-selector-modal'),
            patternListContainer: document.getElementById('pattern-list-container'),
            patternSearchInput: document.getElementById('pattern-search-input'),
            modalCloseBtn: document.getElementById('modal-close-btn'),
        };
        
        // 快取所有句型
        this.allPatterns = [];

        // 題目狀態
        this.QuestionStatus = {
            GENERATING: 'generating',
            READY: 'ready',
            ACTIVE: 'active',
            GRADING: 'grading',
            COMPLETED: 'completed',
            ERROR: 'error'
        };

        this.init();
    }

    /**
     * 初始化系統
     */
    init() {
        this.loadState();
        this.bindEventListeners();
        this.renderQueue();

        if (this.currentQuestionId) {
            this.selectQuestion(this.currentQuestionId);
        } else {
            this.renderSandboxInitial();
        }
    }

    /**
     * 綁定所有事件監聽器
     */
    bindEventListeners() {
        this.elements.addQuestionBtn.addEventListener('click', () => this.handleAddNewQuestion());
        this.elements.clearQueueBtn.addEventListener('click', () => this.clearQueue());

        // 使用事件委派處理沙盒內的動態按鈕
        this.elements.sandboxContent.addEventListener('click', (e) => {
            if (e.target.id === 'submit-btn') this.handleSubmit();
            if (e.target.id === 'retry-btn') this.retryCurrentQuestion();
            if (e.target.id === 'next-btn') this.selectNextQuestion();
        });
        
        // Modal 相關事件
        if (this.elements.modalCloseBtn) {
            this.elements.modalCloseBtn.addEventListener('click', () => this.elements.patternModal?.close());
        }
        if (this.elements.patternListContainer) {
            this.elements.patternListContainer.addEventListener('click', (e) => {
                const item = e.target.closest('.pattern-item');
                if (item) {
                    const patternId = item.dataset.patternId;
                    const patternName = item.dataset.patternName;
                    this.addNewQuestionFromPattern(patternId, patternName);
                }
            });
        }
        if (this.elements.patternSearchInput) {
            this.elements.patternSearchInput.addEventListener('input', (e) => this.filterPatterns(e.target.value));
        }
    }
    
    /**
     * 根據模式決定新增題目的方式
     */
    handleAddNewQuestion() {
        const mode = this.elements.modeSelect.value;
        if (mode === 'pattern') {
            this.openPatternSelector();
        } else {
            this.addNewQuestion();
        }
    }
    
    // ========================================================================
    // 狀態管理 (State Management)
    // ========================================================================

    /**
     * 從 sessionStorage 載入狀態
     */
    loadState() {
        const savedQueue = window.queuePersistence?.loadQueue();
        const savedCurrentId = window.queuePersistence?.loadCurrentQuestion();
        if (savedQueue && savedQueue.length > 0) {
            this.questionQueue = savedQueue;
            this.currentQuestionId = savedCurrentId;
        }
    }

    /**
     * 保存狀態到 sessionStorage
     */
    saveState() {
        window.queuePersistence?.saveQueue(this.questionQueue);
        window.queuePersistence?.saveCurrentQuestion(this.currentQuestionId);
    }
    
    /**
     * 更新佇列中的題目狀態
     */
    updateQuestionState(questionId, updates) {
        const index = this.questionQueue.findIndex(q => q.id === questionId);
        if (index !== -1) {
            this.questionQueue[index] = { ...this.questionQueue[index], ...updates };
            this.saveState();
            return true;
        }
        return false;
    }
    
    /**
     * 獲取當前選中的題目物件
     */
    getCurrentQuestion() {
        if (!this.currentQuestionId) return null;
        return this.questionQueue.find(q => q.id === this.currentQuestionId);
    }

    // ========================================================================
    // API 通訊 (API Communication)
    // ========================================================================

    /**
     * API 呼叫的通用包裝
     */
    async fetchAPI(endpoint, body) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: '伺服器錯誤' }));
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            return { success: false, error: error.message };
        }
    }

    // ========================================================================
    // 核心邏輯 (Core Logic)
    // ========================================================================
    
    /**
     * 新增一個題目到佇列
     */
    async addNewQuestion() {
        if (this.generatingCount >= 3) {
            this.showNotification('同時生成太多題目，請稍候', 'warning');
            return;
        }

        this.generatingCount++;
        const questionId = 'q_' + Date.now() + Math.random().toString(16).slice(2);
        const params = {
            mode: this.elements.modeSelect.value,
            length: this.elements.lengthSelect.value,
            level: parseInt(this.elements.levelSelect.value)
        };
        
        const newQuestion = { id: questionId, status: this.QuestionStatus.GENERATING, ...params };
        this.questionQueue.push(newQuestion);
        this.renderQueue();

        const data = await this.fetchAPI('/api/generate-question', params);

        if (data.success) {
            this.updateQuestionState(questionId, { 
                status: this.QuestionStatus.READY, 
                chinese: data.chinese,
                hint: data.hint,
                target_point_ids: data.target_point_ids || [],
                target_points: data.target_points || [],
                target_points_description: data.target_points_description || ''
            });
        } else {
            this.updateQuestionState(questionId, { status: this.QuestionStatus.ERROR, error: data.error });
        }
        
        this.generatingCount--;
        this.renderQueue();
    }
    
    /**
     * 清空佇列
     */
    clearQueue() {
        this.questionQueue = [];
        this.currentQuestionId = null;
        this.saveState();
        this.renderQueue();
        this.renderSandboxInitial();
    }
    
    /**
     * 選擇一個題目進行作答或查看
     */
    selectQuestion(questionId) {
        // 保存當前題目的草稿
        const currentQuestion = this.getCurrentQuestion();
        if (currentQuestion && currentQuestion.status === this.QuestionStatus.ACTIVE) {
            const answerInput = document.getElementById('answer-input');
            if (answerInput) {
                this.updateQuestionState(currentQuestion.id, { userAnswer: answerInput.value });
            }
        }
        
        // 更新題目狀態
        this.questionQueue.forEach(q => {
            if (q.id === this.currentQuestionId && q.status === this.QuestionStatus.ACTIVE) {
                q.status = this.QuestionStatus.READY;
            }
        });
        
        const newQuestion = this.questionQueue.find(q => q.id === questionId);
        if (newQuestion && (newQuestion.status === this.QuestionStatus.READY || newQuestion.status === this.QuestionStatus.ACTIVE)) {
             newQuestion.status = this.QuestionStatus.ACTIVE;
        }
        
        this.currentQuestionId = questionId;
        this.saveState();
        
        this.renderQueue();
        this.renderSandbox();
    }
    
    /**
     * 處理答案提交
     */
    async handleSubmit() {
        if (this.isSubmitting) return;
        
        const question = this.getCurrentQuestion();
        if (!question) return;

        const answerInput = document.getElementById('answer-input');
        const userAnswer = answerInput.value.trim();
        if (!userAnswer) {
            this.showNotification('請輸入你的英文翻譯', 'warning');
            return;
        }

        this.isSubmitting = true;
        this.updateQuestionState(question.id, { status: this.QuestionStatus.GRADING, userAnswer });
        this.renderSandbox();

        const result = await this.fetchAPI('/api/grade-answer', {
            chinese: question.chinese,
            english: userAnswer,
            mode: question.mode,
            target_point_ids: question.target_point_ids
        });
        
        if (result.success) {
            this.updateQuestionState(question.id, { 
                status: this.QuestionStatus.COMPLETED, 
                gradeResult: result 
            });
            const emoji = result.score >= 80 ? '🎉' : result.score >= 60 ? '👍' : '💪';
            this.showNotification(`${emoji} 批改完成！得分：${result.score}%`, 'success');
        } else {
            this.updateQuestionState(question.id, { 
                status: this.QuestionStatus.ACTIVE, 
                error: result.error 
            });
            this.showNotification('批改失敗：' + result.error, 'error');
        }

        this.isSubmitting = false;
        this.renderSandbox();
    }
    
    /**
     * 重新作答當前題目
     */
    retryCurrentQuestion() {
        const question = this.getCurrentQuestion();
        if (!question) return;
        this.updateQuestionState(question.id, { 
            status: this.QuestionStatus.ACTIVE, 
            userAnswer: '', 
            gradeResult: null 
        });
        this.renderSandbox();
    }
    
    /**
     * 選擇下一個未完成的題目
     */
    selectNextQuestion() {
        const currentIndex = this.questionQueue.findIndex(q => q.id === this.currentQuestionId);
        const nextQuestion = this.questionQueue.find((q, i) => i > currentIndex && q.status === this.QuestionStatus.READY);
        
        if (nextQuestion) {
            this.selectQuestion(nextQuestion.id);
        } else {
            this.showNotification('沒有更多待作答的題目了', 'info');
        }
    }
    
    /**
     * 打開句型選擇視窗
     */
    async openPatternSelector() {
        if (!this.elements.patternModal) return;
        
        // 如果尚未載入句型，則從 API 獲取
        if (this.allPatterns.length === 0) {
            this.elements.patternListContainer.innerHTML = '<div style="text-align:center; padding:20px;">載入句型列表中...</div>';
            const response = await fetch('/api/patterns');
            const data = await response.json();
            if (data.success) {
                this.allPatterns = data.patterns;
            } else {
                this.elements.patternListContainer.innerHTML = '<div style="text-align:center; padding:20px; color:red;">載入失敗</div>';
                return;
            }
        }
        
        // 渲染句型列表
        this.renderPatternList(this.allPatterns);
        this.elements.patternModal.showModal();
    }
    
    /**
     * 渲染句型列表到 Modal 中
     */
    renderPatternList(patterns) {
        const categories = patterns.reduce((acc, p) => {
            const cat = p.category || '未分類';
            (acc[cat] = acc[cat] || []).push(p);
            return acc;
        }, {});

        let html = '';
        for (const category in categories) {
            html += `<h3 class="pattern-category">${category}</h3>`;
            html += `<div class="pattern-group">`;
            html += categories[category].map(p => `
                <div class="pattern-item" data-pattern-id="${p.id}" data-pattern-name="${this.escapeHtml(p.pattern)}">
                    <div class="pattern-name">${this.escapeHtml(p.pattern)}</div>
                    ${p.formula ? `<div class="pattern-formula">${this.escapeHtml(p.formula)}</div>` : ''}
                </div>
            `).join('');
            html += `</div>`;
        }
        this.elements.patternListContainer.innerHTML = html;
    }
    
    /**
     * 篩選句型列表
     */
    filterPatterns(query) {
        const lowerQuery = query.toLowerCase();
        const filtered = this.allPatterns.filter(p => 
            p.pattern.toLowerCase().includes(lowerQuery) ||
            (p.formula && p.formula.toLowerCase().includes(lowerQuery))
        );
        this.renderPatternList(filtered);
    }
    
    /**
     * 從選擇的句型生成新題目
     */
    async addNewQuestionFromPattern(patternId, patternName) {
        if (this.generatingCount >= 3) {
            this.showNotification('同時生成太多題目，請稍候', 'warning');
            return;
        }

        this.elements.patternModal?.close(); // 關閉視窗
        this.generatingCount++;
        
        const questionId = 'q_' + Date.now() + Math.random().toString(16).slice(2);
        const params = {
            mode: 'pattern',
            length: this.elements.lengthSelect.value,
            level: parseInt(this.elements.levelSelect.value),
            pattern_id: patternId
        };
        
        // 在佇列中顯示一個 "生成中" 的卡片
        const newQuestion = { 
            id: questionId, 
            status: this.QuestionStatus.GENERATING, 
            ...params,
            patternName: patternName // 保存句型名稱以便顯示
        };
        this.questionQueue.push(newQuestion);
        this.renderQueue();

        const data = await this.fetchAPI('/api/generate-question', params);

        if (data.success) {
            this.updateQuestionState(questionId, { 
                status: this.QuestionStatus.READY,
                ...data,
                patternName: patternName // 保留句型名稱
            });
        } else {
            this.updateQuestionState(questionId, { 
                status: this.QuestionStatus.ERROR, 
                error: data.error 
            });
        }
        
        this.generatingCount--;
        this.renderQueue();
    }


    // ========================================================================
    // 渲染 (Rendering)
    // ========================================================================
    
    /**
     * 渲染整個題目佇列
     */
    renderQueue() {
        this.elements.queueContainer.innerHTML = ''; // 清空
        this.questionQueue.forEach(q => {
            const card = this.createQueueCard(q);
            this.elements.queueContainer.appendChild(card);
        });
        this.elements.queueContainer.appendChild(this.elements.addQuestionBtn);
        
        const readyCount = this.questionQueue.filter(q => q.status === this.QuestionStatus.READY).length;
        this.elements.queueCount.textContent = `${readyCount} 題就緒`;
    }

    /**
     * 創建單個佇列卡片
     */
    createQueueCard(question) {
        const card = document.createElement('div');
        card.className = 'queue-item';
        card.dataset.status = question.status;
        card.dataset.id = question.id;
        card.dataset.mode = question.mode || 'new';
        
        // 如果是當前選中的題目，添加高亮
        if (question.id === this.currentQuestionId) {
            card.classList.add('active');
        }
        
        let content = '';
        switch(question.status) {
            case this.QuestionStatus.GENERATING:
                content = `
                    <div class="queue-item-body">
                        <div class="spinner" data-type="simple"></div>
                        <span>生成中...</span>
                    </div>
                `;
                break;
            case this.QuestionStatus.READY:
            case this.QuestionStatus.ACTIVE:
                const preview = question.chinese ? question.chinese.substring(0, 15) : '待生成';
                const statusText = question.status === this.QuestionStatus.ACTIVE ? '作答中' : '就緒';
                const modeIcon = question.mode === 'review' ? '🔄' : question.mode === 'pattern' ? '📝' : '✨';
                const modeLabel = question.mode === 'review' ? '複習' : question.mode === 'pattern' ? '句型' : '新題';
                content = `
                    <div class="queue-item-body">
                        <span class="queue-item-text">${preview}...</span>
                        <span class="queue-item-badge ${question.status}">${modeIcon} ${modeLabel}-${statusText}</span>
                        ${question.patternName ? `<div class="queue-item-hint" style="font-size:11px; color:#666; margin-top:4px;">${this.escapeHtml(question.patternName)}</div>` : ''}
                    </div>
                `;
                break;
            case this.QuestionStatus.GRADING:
                content = `
                    <div class="queue-item-body">
                        <span>批改中...</span>
                        <div class="spinner" data-type="simple"></div>
                    </div>
                `;
                break;
            case this.QuestionStatus.COMPLETED:
                const score = question.gradeResult?.score || 0;
                const scoreColor = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';
                content = `
                    <div class="queue-item-body">
                        <span>已完成</span>
                        <span class="score-display ${scoreColor}">${score}%</span>
                    </div>
                `;
                break;
            case this.QuestionStatus.ERROR:
                content = `
                    <div class="queue-item-body">
                        <span style="color:red">生成失敗</span>
                    </div>
                `;
                break;
        }
        card.innerHTML = content;
        
        if (question.status !== this.QuestionStatus.GENERATING && question.status !== this.QuestionStatus.ERROR) {
            card.addEventListener('click', () => this.selectQuestion(question.id));
        }

        return card;
    }
    
    /**
     * 渲染沙盒區域 (主函式)
     */
    renderSandbox() {
        const question = this.getCurrentQuestion();
        if (!question) {
            this.renderSandboxInitial();
            return;
        }
        
        switch(question.status) {
            case this.QuestionStatus.ACTIVE:
            case this.QuestionStatus.READY:
                this.renderSandboxQuestion(question);
                break;
            case this.QuestionStatus.GRADING:
                this.renderSandboxGrading();
                break;
            case this.QuestionStatus.COMPLETED:
                this.renderSandboxResult(question);
                break;
            default:
                this.renderSandboxInitial();
        }
    }
    
    /**
     * 渲染沙盒的初始/空狀態
     */
    renderSandboxInitial() {
        this.elements.sandboxContent.innerHTML = `
            <div class="practice-ready">
                <p>請從上方佇列選擇題目，或點擊「新增題目」。</p>
            </div>
        `;
    }
    
    /**
     * 渲染沙盒的作答介面
     */
    renderSandboxQuestion(question) {
        const modeIndicator = question.mode === 'review' ? 
            '<span class="mode-indicator review">複習模式</span>' : '';
        
        this.elements.sandboxContent.innerHTML = `
            <section class="question-section">
                <div class="card" data-type="question">
                    <div class="question-label">
                        <span>中文句子</span>
                        ${modeIndicator}
                    </div>
                    <p class="question-content">${this.escapeHtml(question.chinese)}</p>
                    ${question.hint ? `<div class="question-hint">💡 ${this.escapeHtml(question.hint)}</div>` : ''}
                    ${question.target_points_description ? `
                        <div class="review-focus">
                            <span class="focus-label">複習重點：</span>
                            <span class="focus-content">${this.escapeHtml(question.target_points_description)}</span>
                        </div>
                    ` : ''}
                </div>
            </section>
            <section class="answer-section">
                <textarea id="answer-input" class="answer-input" rows="4" 
                    placeholder="請輸入你的英文翻譯...">${question.userAnswer || ''}</textarea>
            </section>
            <section class="submit-section">
                <button id="submit-btn" class="btn" data-variant="primary" data-size="lg">提交答案</button>
            </section>
        `;
        document.getElementById('answer-input').focus();
    }
    
    /**
     * 渲染沙盒的批改中介面
     */
    renderSandboxGrading() {
        this.elements.sandboxContent.innerHTML = `
            <div class="grading-indicator">
                <div class="spinner" data-type="simple"></div>
                <span>AI 正在批改中，請稍候...</span>
            </div>
        `;
    }

    /**
     * 渲染沙盒的批改結果介面
     */
    renderSandboxResult(question) {
        const result = question.gradeResult;
        const scoreColor = result.score >= 80 ? '#48bb78' : result.score >= 60 ? '#ed8936' : '#f56565';
        
        const errorList = (result.error_analysis || []).map(e => `
            <li class="item" style="margin-bottom: 16px; padding: 12px; background: #f7fafc; border-left: 4px solid #4299e1; border-radius: 4px;">
                <div class="error-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div class="title" style="font-weight: 600; color: #2d3748;">${this.escapeHtml(e.key_point_summary)}</div>
                    ${e.category ? `
                        <span class="badge error-category-badge" data-category="${e.category}" style="
                            display: inline-block;
                            padding: 2px 8px;
                            background: ${e.category === 'systematic' ? '#fee' : 
                                         e.category === 'isolated' ? '#fef' : 
                                         e.category === 'enhancement' ? '#eff' : '#f5f5f5'};
                            color: ${e.category === 'systematic' ? '#c41e3a' : 
                                    e.category === 'isolated' ? '#9333ea' : 
                                    e.category === 'enhancement' ? '#0891b2' : '#666'};
                            border-radius: 12px;
                            font-size: 12px;
                        ">
                            ${e.category === 'systematic' ? '系統性錯誤' : 
                              e.category === 'isolated' ? '單一性錯誤' : 
                              e.category === 'enhancement' ? '可以更好' : '其他錯誤'}
                        </span>
                    ` : ''}
                </div>
                ${e.explanation ? `<p class="muted" style="color: #718096; margin: 8px 0; line-height: 1.5;">${this.escapeHtml(e.explanation)}</p>` : ''}
                ${e.original_phrase || e.correction ? `
                    <div class="examples" style="margin-top: 8px; padding: 8px; background: white; border-radius: 4px; font-family: monospace;">
                        ${e.original_phrase ? `<div class="zh" style="color: #e53e3e; text-decoration: line-through;">原：${this.escapeHtml(e.original_phrase)}</div>` : ''}
                        ${e.correction ? `<div class="en" style="color: #38a169; margin-top: 4px;">正：${this.escapeHtml(e.correction)}</div>` : ''}
                    </div>
                ` : ''}
            </li>
        `).join('');

        this.elements.sandboxContent.innerHTML = `
            <section class="card result-section" style="padding: 24px; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <h2 style="color: ${scoreColor}; margin: 0 0 20px 0;">批改結果 (${result.score}%)</h2>
                <div class="stack" style="display: flex; flex-direction: column; gap: 20px;">
                    <div>
                        <div class="muted" style="color: #718096; font-size: 14px; margin-bottom: 4px;">建議：</div>
                        <div style="color: #2d3748; line-height: 1.5;">${this.escapeHtml(result.feedback)}</div>
                    </div>
                    ${errorList ? `
                        <div>
                            <div class="muted" style="color: #718096; font-size: 14px; margin-bottom: 12px;">錯誤分析：</div>
                            <ul class="list" style="list-style: none; padding: 0; margin: 0;">${errorList}</ul>
                        </div>
                    ` : ''}
                    <div class="result-actions" style="display: flex; gap: 12px; justify-content: center; margin-top: 20px;">
                        <button id="retry-btn" class="btn" data-variant="secondary" style="
                            padding: 10px 24px;
                            background: #e2e8f0;
                            color: #2d3748;
                            border: none;
                            border-radius: 8px;
                            font-weight: 500;
                            cursor: pointer;
                        ">重新作答</button>
                        <button id="next-btn" class="btn" data-variant="primary" style="
                            padding: 10px 24px;
                            background: #3182ce;
                            color: white;
                            border: none;
                            border-radius: 8px;
                            font-weight: 500;
                            cursor: pointer;
                        ">下一題</button>
                    </div>
                </div>
            </section>
        `;
    }
    
    // ========================================================================
    // 工具函式 (Utility Functions)
    // ========================================================================
    
    /**
     * HTML 轉義防止 XSS
     */
    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    /**
     * 顯示通知
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed; 
            top: 20px; 
            right: 20px; 
            padding: 12px 20px; 
            background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#f56565' : type === 'warning' ? '#ed8936' : '#4299e1'}; 
            color: white; 
            border-radius: 6px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
            z-index: 10000; 
            font-weight: 500;
            max-width: 300px;
            word-wrap: break-word;
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// 添加必要的 CSS 動畫
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .spinner[data-type="simple"] {
        width: 20px;
        height: 20px;
        border: 2px solid #dee2e6;
        border-top-color: #2196f3;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    .grading-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        padding: 40px;
        color: #6c757d;
    }
    .practice-ready {
        text-align: center;
        padding: 60px 20px;
        color: #6c757d;
    }
    
    /* Modal 樣式 */
    #pattern-selector-modal {
        width: 90%;
        max-width: 600px;
        max-height: 80vh;
        border: none;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        padding: 0;
        overflow: hidden;
    }
    
    #pattern-selector-modal::backdrop {
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(4px);
    }
    
    .modal-content {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    
    .modal-header {
        padding: 20px;
        border-bottom: 1px solid #e9ecef;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f8f9fa;
    }
    
    .modal-title {
        font-size: 20px;
        font-weight: 600;
        margin: 0;
        color: #212529;
    }
    
    .modal-close {
        background: none;
        border: none;
        font-size: 28px;
        line-height: 1;
        cursor: pointer;
        color: #6c757d;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        transition: all 0.2s;
    }
    
    .modal-close:hover {
        background: #e9ecef;
        color: #212529;
    }
    
    .modal-body {
        flex: 1;
        padding: 20px;
        overflow-y: auto;
    }
    
    .modal-search {
        width: 100%;
        padding: 10px 16px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin-bottom: 20px;
        font-size: 16px;
        transition: all 0.2s;
    }
    
    .modal-search:focus {
        outline: none;
        border-color: #2196f3;
        box-shadow: 0 0 0 3px rgba(33,150,243,0.1);
    }
    
    .pattern-list {
        max-height: 400px;
        overflow-y: auto;
    }
    
    .pattern-category {
        font-size: 14px;
        font-weight: 600;
        color: #6c757d;
        margin-top: 20px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e9ecef;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .pattern-category:first-child {
        margin-top: 0;
    }
    
    .pattern-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 20px;
    }
    
    .pattern-item {
        padding: 12px 16px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        background: white;
        border: 1px solid #e9ecef;
    }
    
    .pattern-item:hover {
        background-color: #e3f2fd;
        border-color: #2196f3;
        transform: translateX(4px);
    }
    
    .pattern-name {
        font-weight: 500;
        color: #212529;
        margin-bottom: 4px;
    }
    
    .pattern-formula {
        font-size: 12px;
        color: #6c757d;
        font-family: 'Courier New', monospace;
    }
`;
document.head.appendChild(style);

// 當 DOM 載入完成後，啟動系統
document.addEventListener('DOMContentLoaded', () => {
    window.practiceSystem = new PracticeSystem();
});