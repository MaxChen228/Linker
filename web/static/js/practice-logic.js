/**
 * @file Linker 練習頁面核心邏輯
 * @author Gemini
 * @description 採用狀態驅動 UI 模式，管理練習題目的完整生命週期。
 */

/**
 * @class PracticeSystem
 * @classdesc 主類別，封裝了練習系統的所有狀態和行為。
 */
class PracticeSystem {
    /**
     * @constructor
     */
    constructor() {
        /**
         * @property {Array<object>} questionQueue - 儲存所有題目的佇列。
         */
        this.questionQueue = [];
        /**
         * @property {?string} currentQuestionId - 當前選中題目的 ID。
         */
        this.currentQuestionId = null;
        /**
         * @property {boolean} isSubmitting - 防止重複提交的鎖定旗標。
         */
        this.isSubmitting = false;
        /**
         * @property {number} generatingCount - 正在生成中的題目數量，用於速率限制。
         */
        this.generatingCount = 0;

        /**
         * @property {object} elements - 快取的 DOM 元素，避免重複查詢。
         */
        this.elements = {
            queueContainer: document.getElementById('queue-items'),
            queueCount: document.getElementById('queue-count'),
            sandboxContent: document.getElementById('sandbox-content'),
            modeSelect: document.getElementById('mode-select'),
            lengthSelect: document.getElementById('length-select'),
            levelSelect: document.getElementById('level-select'),
            addQuestionBtn: document.getElementById('add-question-btn'),
            clearQueueBtn: document.getElementById('clear-queue-btn'),
        };

        /**
         * @property {object} QuestionStatus - 定義題目所有可能的狀態。
         * @enum {string}
         */
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
     * 初始化系統，綁定事件並渲染初始畫面。
     * @returns {void}
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
     * 綁定所有固定的 DOM 事件監聽器。
     * @returns {void}
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
    }
    
    /**
     * 處理「新增題目」按鈕點擊事件，統一所有模式的處理流程。
     * @returns {void}
     */
    handleAddNewQuestion() {
        this.addNewQuestion();
    }
    
    // ========================================================================
    // 狀態管理 (State Management)
    // ========================================================================

    /**
     * 從 sessionStorage 載入先前儲存的佇列和當前題目 ID。
     * @returns {void}
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
     * 將目前狀態儲存到 sessionStorage。
     * @returns {void}
     */
    saveState() {
        window.queuePersistence?.saveQueue(this.questionQueue);
        window.queuePersistence?.saveCurrentQuestion(this.currentQuestionId);
    }
    
    /**
     * 更新佇列中指定題目的狀態。
     * @param {string} questionId - 要更新的題目 ID。
     * @param {object} updates - 包含要更新的鍵值對物件。
     * @returns {boolean} - 是否成功找到並更新題目。
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
     * 獲取當前選中的題目物件。
     * @returns {?object} - 當前題目物件，如果沒有則返回 null。
     */
    getCurrentQuestion() {
        if (!this.currentQuestionId) return null;
        return this.questionQueue.find(q => q.id === this.currentQuestionId);
    }

    // ========================================================================
    // API 通訊 (API Communication)
    // ========================================================================

    /**
     * API 呼叫的通用包裝函式，包含錯誤處理。
     * @param {string} endpoint - 要呼叫的 API 端點路徑。
     * @param {object} body - 要傳送的請求主體 (request body)。
     * @returns {Promise<object>} - API 回傳的 JSON 資料，或在失敗時回傳包含 error 的物件。
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
     * 非同步新增一個題目到佇列，並向後端請求題目內容。
     * @returns {Promise<void>}
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
     * 清空整個題目佇列和當前狀態。
     * @returns {void}
     */
    clearQueue() {
        this.questionQueue = [];
        this.currentQuestionId = null;
        this.saveState();
        this.renderQueue();
        this.renderSandboxInitial();
    }
    
    /**
     * 選擇一個題目進行作答或查看，並更新相關狀態。
     * @param {string} questionId - 要選擇的題目 ID。
     * @returns {void}
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
     * 處理答案提交，呼叫批改 API 並更新 UI。
     * @returns {Promise<void>}
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
            if (!result.score && result.score !== 0) {
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
     * 重新作答當前題目，重設其狀態。
     * @returns {void}
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
     * 從目前題目開始，選擇佇列中下一個未完成的題目。
     * @returns {void}
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
    
    // ========================================================================
    // 渲染 (Rendering)
    // ========================================================================
    
    /**
     * 根據目前 this.questionQueue 的狀態，重新渲染整個題目佇列 UI。
     * @returns {void}
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
     * 根據單個題目物件的狀態，創建其對應的佇列卡片 DOM 元素。
     * @param {object} question - 題目物件。
     * @returns {HTMLElement} - 創建好的卡片 DOM 元素。
     */
    createQueueCard(question) {
        const card = document.createElement('div');
        card.className = 'queue-item';
        card.dataset.status = question.status;
        card.dataset.id = question.id;
        card.dataset.mode = question.mode || 'new';
        
        if (question.id === this.currentQuestionId) {
            card.classList.add('active');
        }
        
        let content = '';
        switch(question.status) {
            case this.QuestionStatus.GENERATING:
                content = `<div class="queue-item-body"><div class="spinner" data-type="simple"></div><span>生成中...</span></div>`;
                break;
            case this.QuestionStatus.READY:
            case this.QuestionStatus.ACTIVE:
                const preview = question.chinese ? question.chinese.substring(0, 15) : '待生成';
                const statusText = question.status === this.QuestionStatus.ACTIVE ? '作答中' : '就緒';
                const modeIcon = question.mode === 'review' ? '🔄' : question.mode === 'pattern' ? '📝' : '✨';
                const modeLabel = question.mode === 'review' ? '複習' : question.mode === 'pattern' ? '句型' : '新題';
                content = `<div class="queue-item-body"><span class="queue-item-text">${preview}...</span><span class="badge" data-variant="${question.status === this.QuestionStatus.ACTIVE ? 'warning' : 'info'}" data-size="sm">${modeIcon} ${modeLabel}-${statusText}</span></div>`;
                break;
            case this.QuestionStatus.GRADING:
                content = `<div class="queue-item-body"><span>批改中...</span><div class="spinner" data-type="simple"></div></div>`;
                break;
            case this.QuestionStatus.COMPLETED:
                const score = question.gradeResult?.score || 0;
                const scoreColor = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';
                content = `<div class="queue-item-body"><span>已完成</span><span class="score-display ${scoreColor}">${score}%</span></div>`;
                break;
            case this.QuestionStatus.ERROR:
                content = `<div class="queue-item-body"><span class="error-text">生成失敗</span></div>`;
                break;
        }
        card.innerHTML = content;
        
        if (question.status !== this.QuestionStatus.GENERATING && question.status !== this.QuestionStatus.ERROR) {
            card.addEventListener('click', () => this.selectQuestion(question.id));
        }

        return card;
    }
    
    /**
     * 渲染沙盒區域的主函式，根據當前題目狀態決定渲染哪個介面。
     * @returns {void}
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
     * 渲染沙盒的初始/空狀態介面。
     * @returns {void}
     */
    renderSandboxInitial() {
        this.elements.sandboxContent.innerHTML = `<div class="practice-ready"><p>請從上方佇列選擇題目，或點擊「新增題目」。</p></div>`;
    }
    
    /**
     * 渲染沙盒的作答介面。
     * @param {object} question - 要渲染的題目物件。
     * @returns {void}
     */
    renderSandboxQuestion(question) {
        const modeIndicator = question.mode === 'review' ? '<span class="mode-indicator review">複習模式</span>' : '';
        
        this.elements.sandboxContent.innerHTML = `
            <section class="question-section">
                <div class="card" data-type="question">
                    <div class="question-label"><span>中文句子</span>${modeIndicator}</div>
                    <p class="question-content">${this.escapeHtml(question.chinese)}</p>
                    ${question.hint ? `<div class="question-hint">💡 ${this.escapeHtml(question.hint)}</div>` : ''}
                    ${question.target_points_description ? `<div class="review-focus"><span class="focus-label">複習重點：</span><span class="focus-content">${this.escapeHtml(question.target_points_description)}</span></div>` : ''}
                </div>
            </section>
            <section class="answer-section">
                <textarea id="answer-input" class="answer-input" rows="4" placeholder="請輸入你的英文翻譯...">${question.userAnswer || ''}</textarea>
            </section>
            <section class="submit-section">
                <button id="submit-btn" class="btn" data-variant="primary" data-size="lg">提交答案</button>
            </section>
        `;
        document.getElementById('answer-input').focus();
    }
    
    /**
     * 渲染沙盒的「批改中」介面。
     * @returns {void}
     */
    renderSandboxGrading() {
        this.elements.sandboxContent.innerHTML = `<div class="grading-indicator"><div class="spinner" data-type="simple"></div><span>AI 正在批改中，請稍候...</span></div>`;
    }

    /**
     * 渲染沙盒的批改結果介面。
     * @param {object} question - 包含批改結果的題目物件。
     * @returns {void}
     */
    renderSandboxResult(question) {
        const result = question.gradeResult;
        const score = (result && typeof result.score === 'number') ? result.score : 0;
        const scoreColor = score >= 80 ? '#48bb78' : score >= 60 ? '#ed8936' : '#f56565';
        
        const errorList = (result.error_analysis || []).map(e => `
            <li class="error-analysis-item">
                <div class="error-header">
                    <div class="error-title">${this.escapeHtml(e.key_point_summary)}</div>
                    ${e.category ? `<span class="badge" data-variant="${e.category === 'systematic' ? 'error' : e.category === 'isolated' ? 'warning' : e.category === 'enhancement' ? 'info' : 'neutral'}" data-size="sm">${e.category === 'systematic' ? '系統性錯誤' : e.category === 'isolated' ? '單一性錯誤' : e.category === 'enhancement' ? '可以更好' : '其他錯誤'}</span>` : ''}
                </div>
                ${e.explanation ? `<p class="error-explanation">${this.escapeHtml(e.explanation)}</p>` : ''}
                ${e.original_phrase || e.correction ? `<div class="error-examples">
                        ${e.original_phrase ? `<div class="error-original">原：${this.escapeHtml(e.original_phrase)}</div>` : ''}
                        ${e.correction ? `<div class="error-correction">正：${this.escapeHtml(e.correction)}</div>` : ''}
                    </div>` : ''}
            </li>
        `).join('');

        this.elements.sandboxContent.innerHTML = `
            <section class="card result-section">
                <h2 class="result-score ${score >= 80 ? 'score-high' : score >= 60 ? 'score-medium' : 'score-low'}">批改結果 (${score}%)</h2>
                <div class="result-content">
                    <div class="feedback-section">
                        <div class="feedback-label">建議：</div>
                        <div class="feedback-content">${this.escapeHtml(result.feedback)}</div>
                    </div>
                    ${errorList ? `<div class="error-analysis-section"><div class="error-analysis-label">錯誤分析：</div><ul class="error-analysis-list">${errorList}</ul></div>` : ''}
                    <div class="result-actions">
                        <button id="retry-btn" class="btn" data-variant="secondary">重新作答</button>
                        <button id="next-btn" class="btn" data-variant="primary">下一題</button>
                    </div>
                </div>
            </section>
        `;
    }
    
    // ========================================================================
    // 工具函式 (Utility Functions)
    // ========================================================================
    
    /**
     * 對字串進行 HTML 轉義，防止 XSS 攻擊。
     * @param {string} unsafe - 未經轉義的原始字串。
     * @returns {string} - 轉義後的安全字串。
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
     * 在畫面上方顯示一個短暫的通知訊息。
     * @param {string} message - 要顯示的訊息。
     * @param {'info'|'success'|'warning'|'error'} type - 通知的類型。
     * @returns {void}
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.classList.add('notification-toast');
        notification.setAttribute('data-type', type);
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('notification-exit');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// CSS styles are now handled by the design system in practice.css

// 當 DOM 載入完成後，啟動系統
document.addEventListener('DOMContentLoaded', () => {
    window.practiceSystem = new PracticeSystem();
});
