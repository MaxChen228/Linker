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
            // Modal 相關元素已移除
        };

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
        
        // Modal 相關代碼已移除 - 現在使用後端隨機選擇句型
    }
    
    /**
     * 新增題目 - 統一處理所有模式
     */
    handleAddNewQuestion() {
        // 所有模式都直接生成題目，不再有特殊處理
        this.addNewQuestion();
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
            // 額外檢查：確保結果真的有效
            if (!result.score && result.score !== 0) {
                // 分數無效，視為錯誤
                this.updateQuestionState(question.id, { 
                    status: this.QuestionStatus.ACTIVE, 
                    error: '批改結果無效' 
                });
                this.showNotification('批改失敗：未能獲得有效的批改結果', 'error');
            } else {
                this.updateQuestionState(question.id, { 
                    status: this.QuestionStatus.COMPLETED, 
                    gradeResult: result 
                });
                const emoji = result.score >= 80 ? '🎉' : result.score >= 60 ? '👍' : '💪';
                this.showNotification(`${emoji} 批改完成！得分：${result.score}%`, 'success');
            }
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
    
    // Modal 相關方法已全部移除 - 現在使用後端隨機選擇句型
    
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
                        <span class="badge" data-variant="${question.status === this.QuestionStatus.ACTIVE ? 'warning' : 'info'}" data-size="sm">${modeIcon} ${modeLabel}-${statusText}</span>
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
        // 確保分數有效，無效時設為 0
        const score = (result && typeof result.score === 'number') ? result.score : 0;
        const scoreColor = score >= 80 ? '#48bb78' : score >= 60 ? '#ed8936' : '#f56565';
        
        const errorList = (result.error_analysis || []).map(e => `
            <li class="item" style="margin-bottom: 16px; padding: 12px; background: #f7fafc; border-left: 4px solid #4299e1; border-radius: 4px;">
                <div class="error-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div class="title" style="font-weight: 600; color: #2d3748;">${this.escapeHtml(e.key_point_summary)}</div>
                    ${e.category ? `
                        <span class="badge" data-variant="${e.category === 'systematic' ? 'error' : 
                              e.category === 'isolated' ? 'warning' : 
                              e.category === 'enhancement' ? 'info' : 'neutral'}" data-size="sm">
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
                <h2 style="color: ${scoreColor}; margin: 0 0 20px 0;">批改結果 (${score}%)</h2>
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
    
    /* Modal 相關樣式已全部移除 - 現在使用後端隨機選擇句型 */
`;
document.head.appendChild(style);

// 當 DOM 載入完成後，啟動系統
document.addEventListener('DOMContentLoaded', () => {
    window.practiceSystem = new PracticeSystem();
});