/**
 * @file Linker 練習頁面核心邏輯
 * @author Gemini
 * @description 採用狀態驅動 UI 模式，管理練習題目的完整生命週期。
 */

// TASK-34: 引入統一API端點管理系統，消除硬編碼
import { apiEndpoints } from './config/api-endpoints.js';

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
         * @property {object} dailyLimitStatus - TASK-32: 每日知識點上限狀態
         */
        this.dailyLimitStatus = {
            limit_enabled: false,
            daily_limit: 15,
            used_count: 0,
            can_add_more: true,
            breakdown: { isolated: 0, enhancement: 0 }
        };

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
        
        // TASK-32: 初始化時獲取每日限額狀態
        this.updateDailyLimitStatus();
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

        const data = await this.fetchAPI(apiEndpoints.getUrl('generateQuestion'), params);

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

        const result = await this.fetchAPI(apiEndpoints.getUrl('gradeAnswer'), {
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
        
        // 🔥 調試信息：檢查實際API響應
        console.log('🔍 API Response Debug:', {
            auto_save: result.auto_save,
            pending_knowledge_points: result.pending_knowledge_points,
            error_analysis: result.error_analysis,
            has_error_analysis: result.error_analysis && result.error_analysis.length > 0
        });
        
        // 檢查是否有待確認的知識點
        const pendingPoints = result.pending_knowledge_points || [];
        const showConfirmationUI = !result.auto_save && pendingPoints.length > 0;
        
        console.log('🔍 UI Logic Debug:', {
            pendingPointsLength: pendingPoints.length,
            autoSave: result.auto_save,
            showConfirmationUI: showConfirmationUI
        });
        
        if (showConfirmationUI) {
            // 渲染待確認的知識點介面
            const pendingList = pendingPoints.map((point, index) => {
                const e = point.error;
                return `
                    <li class="pending-point" data-point-id="${point.id}" data-index="${index}">
                        <div class="error-analysis-item">
                            <div class="error-header">
                                <div class="error-title">${this.escapeHtml(e.key_point_summary)}</div>
                                ${e.category ? `<span class="badge" data-variant="${e.category === 'systematic' ? 'error' : e.category === 'isolated' ? 'warning' : e.category === 'enhancement' ? 'info' : 'neutral'}" data-size="sm">${e.category === 'systematic' ? '系統性錯誤' : e.category === 'isolated' ? '單一性錯誤' : e.category === 'enhancement' ? '可以更好' : '其他錯誤'}</span>` : ''}
                            </div>
                            ${e.explanation ? `<p class="error-explanation">${this.escapeHtml(e.explanation)}</p>` : ''}
                            ${e.original_phrase || e.correction ? `<div class="error-examples">
                                    ${e.original_phrase ? `<div class="error-original">原：${this.escapeHtml(e.original_phrase)}</div>` : ''}
                                    ${e.correction ? `<div class="error-correction">正：${this.escapeHtml(e.correction)}</div>` : ''}
                                </div>` : ''}
                        </div>
                        <div class="point-actions">
                            <button class="btn btn-confirm-point" data-variant="success" data-size="sm" data-point-id="${point.id}">
                                ✓ 加入知識庫
                            </button>
                            <button class="btn btn-ignore-point" data-variant="neutral" data-size="sm" data-point-id="${point.id}">
                                × 忽略
                            </button>
                        </div>
                    </li>
                `;
            }).join('');
            
            this.elements.sandboxContent.innerHTML = `
                <section class="card result-section">
                    <h2 class="result-score ${score >= 80 ? 'score-high' : score >= 60 ? 'score-medium' : 'score-low'}">批改結果 (${score}%)</h2>
                    <div class="result-content">
                        <div class="feedback-section">
                            <div class="feedback-label">建議：</div>
                            <div class="feedback-content">${this.escapeHtml(result.feedback)}</div>
                        </div>
                        <div class="confirmation-section">
                            <div class="confirmation-label">請確認是否將以下錯誤加入知識庫：</div>
                            <ul class="pending-points-list">${pendingList}</ul>
                            ${this.generateKnowledgeButtons(pendingPoints)}
                        </div>
                        <div class="result-actions">
                            <button id="retry-btn" class="btn" data-variant="secondary">重新作答</button>
                            <button id="next-btn" class="btn" data-variant="primary">下一題</button>
                        </div>
                    </div>
                </section>
            `;
            
            // 儲存待確認點到當前題目
            this.updateQuestionState(question.id, { pendingPoints: pendingPoints });
            
            // 綁定確認/忽略按鈕事件
            this.bindConfirmationEvents(question.id);
            
            // TASK-32: 綁定限額相關事件
            this.bindLimitEvents();
        } else {
            // 傳統的錯誤列表展示（自動保存模式）
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
    }
    
    /**
     * 綁定確認/忽略按鈕的事件處理
     * @param {string} questionId - 題目ID
     * @returns {void}
     */
    bindConfirmationEvents(questionId) {
        // 單個確認按鈕
        document.querySelectorAll('.btn-confirm-point').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const pointId = e.target.dataset.pointId;
                await this.confirmSinglePoint(questionId, pointId);
            });
        });
        
        // 單個忽略按鈕
        document.querySelectorAll('.btn-ignore-point').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const pointId = e.target.dataset.pointId;
                this.ignoreSinglePoint(questionId, pointId);
            });
        });
        
        // 全部確認按鈕
        const confirmAllBtn = document.querySelector('.btn-confirm-all');
        if (confirmAllBtn) {
            confirmAllBtn.addEventListener('click', async () => {
                await this.confirmAllPoints(questionId);
            });
        }
        
        // 全部忽略按鈕
        const ignoreAllBtn = document.querySelector('.btn-ignore-all');
        if (ignoreAllBtn) {
            ignoreAllBtn.addEventListener('click', () => {
                this.ignoreAllPoints(questionId);
            });
        }
    }
    
    /**
     * 確認單個知識點
     * @param {string} questionId - 題目ID
     * @param {string} pointId - 知識點ID
     * @returns {Promise<void>}
     */
    async confirmSinglePoint(questionId, pointId) {
        const question = this.questionQueue.find(q => q.id === questionId);
        if (!question || !question.pendingPoints) return;
        
        const point = question.pendingPoints.find(p => p.id === pointId);
        if (!point) return;
        
        // 調用API確認知識點
        const response = await this.fetchAPI(apiEndpoints.getUrl('confirmKnowledge'), {
            confirmed_points: [point]
        });
        
        if (response.success) {
            // 更新UI狀態
            const pointElement = document.querySelector(`[data-point-id="${pointId}"]`);
            if (pointElement) {
                pointElement.classList.add('confirmed');
                pointElement.querySelector('.point-actions').innerHTML = '<span class="status-confirmed">✓ 已加入</span>';
            }
            this.showNotification('已加入知識庫', 'success');
            
            // 從待確認列表移除
            question.pendingPoints = question.pendingPoints.filter(p => p.id !== pointId);
            this.updateQuestionState(questionId, { pendingPoints: question.pendingPoints });
        } else {
            this.showNotification('確認失敗，請重試', 'error');
        }
    }
    
    /**
     * 忽略單個知識點
     * @param {string} questionId - 題目ID
     * @param {string} pointId - 知識點ID
     * @returns {void}
     */
    ignoreSinglePoint(questionId, pointId) {
        const question = this.questionQueue.find(q => q.id === questionId);
        if (!question || !question.pendingPoints) return;
        
        // 更新UI狀態
        const pointElement = document.querySelector(`[data-point-id="${pointId}"]`);
        if (pointElement) {
            pointElement.classList.add('ignored');
            pointElement.querySelector('.point-actions').innerHTML = '<span class="status-ignored">× 已忽略</span>';
        }
        
        // 從待確認列表移除
        question.pendingPoints = question.pendingPoints.filter(p => p.id !== pointId);
        this.updateQuestionState(questionId, { pendingPoints: question.pendingPoints });
        
        this.showNotification('已忽略此知識點', 'info');
    }
    
    /**
     * 確認所有知識點
     * @param {string} questionId - 題目ID
     * @returns {Promise<void>}
     */
    async confirmAllPoints(questionId) {
        const question = this.questionQueue.find(q => q.id === questionId);
        if (!question || !question.pendingPoints || question.pendingPoints.length === 0) return;
        
        // 調用API確認所有知識點
        const response = await this.fetchAPI(apiEndpoints.getUrl('confirmKnowledge'), {
            confirmed_points: question.pendingPoints
        });
        
        if (response.success) {
            // 更新所有點的UI狀態
            document.querySelectorAll('.pending-point').forEach(elem => {
                elem.classList.add('confirmed');
                elem.querySelector('.point-actions').innerHTML = '<span class="status-confirmed">✓ 已加入</span>';
            });
            
            this.showNotification(`已加入 ${response.confirmed_count} 個知識點`, 'success');
            
            // 清空待確認列表
            question.pendingPoints = [];
            this.updateQuestionState(questionId, { pendingPoints: [] });
        } else {
            this.showNotification('批量確認失敗，請重試', 'error');
        }
    }
    
    /**
     * 忽略所有知識點
     * @param {string} questionId - 題目ID
     * @returns {void}
     */
    ignoreAllPoints(questionId) {
        const question = this.questionQueue.find(q => q.id === questionId);
        if (!question || !question.pendingPoints) return;
        
        const count = question.pendingPoints.length;
        
        // 更新所有點的UI狀態
        document.querySelectorAll('.pending-point').forEach(elem => {
            elem.classList.add('ignored');
            elem.querySelector('.point-actions').innerHTML = '<span class="status-ignored">× 已忽略</span>';
        });
        
        // 清空待確認列表
        question.pendingPoints = [];
        this.updateQuestionState(questionId, { pendingPoints: [] });
        
        this.showNotification(`已忽略 ${count} 個知識點`, 'info');
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
    
    // ==================== TASK-32: 每日知識點上限功能 ====================
    
    /**
     * 更新每日限額狀態
     * @returns {Promise<void>}
     */
    async updateDailyLimitStatus() {
        try {
            const response = await fetch(apiEndpoints.getUrl('knowledgeDailyLimitStatus'));
            if (response.ok) {
                const data = await response.json();
                this.dailyLimitStatus = data;
                this.updateDailyLimitDisplay();
            }
        } catch (error) {
            console.error('獲取每日限額狀態失敗:', error);
            // 失敗時使用預設值（不阻擋正常功能）
        }
    }
    
    /**
     * 更新限額顯示在頁面上
     * @returns {void}
     */
    updateDailyLimitDisplay() {
        // 在練習簡介下方添加限額顯示
        let limitIndicator = document.getElementById('daily-limit-indicator');
        
        if (!limitIndicator) {
            limitIndicator = document.createElement('div');
            limitIndicator.id = 'daily-limit-indicator';
            limitIndicator.className = 'daily-limit-indicator';
            
            // 插入到 practice-header 之後
            const header = document.querySelector('.practice-header');
            if (header && header.parentNode) {
                header.parentNode.insertBefore(limitIndicator, header.nextSibling);
            }
        }
        
        if (!this.dailyLimitStatus.limit_enabled) {
            limitIndicator.style.display = 'none';
            return;
        }
        
        const percentage = this.dailyLimitStatus.daily_limit > 0 
            ? (this.dailyLimitStatus.used_count / this.dailyLimitStatus.daily_limit) * 100 
            : 0;
        
        limitIndicator.style.display = 'block';
        limitIndicator.innerHTML = `
            <div class="limit-progress">
                <span class="limit-text">今日已儲存: <strong>${this.dailyLimitStatus.used_count}</strong>/<strong>${this.dailyLimitStatus.daily_limit}</strong></span>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${Math.min(100, percentage)}%"></div>
                </div>
            </div>
            <small class="limit-detail">重點複習: ${this.dailyLimitStatus.breakdown.isolated} | 可改進: ${this.dailyLimitStatus.breakdown.enhancement}</small>
        `;
    }
    
    /**
     * 根據限額狀態生成按鈕組合
     * @param {Array} pendingPoints - 待確認的知識點列表
     * @returns {string} - 按鈕HTML
     */
    generateKnowledgeButtons(pendingPoints) {
        // 檢查是否有限制類型的知識點
        const hasLimitedTypes = pendingPoints.some(point => 
            point.subtype === 'isolated' || point.subtype === 'enhancement'
        );
        
        // 如果沒有限制類型或未啟用限額，顯示正常按鈕
        if (!hasLimitedTypes || !this.dailyLimitStatus.limit_enabled || this.dailyLimitStatus.can_add_more) {
            return `
                <div class="batch-actions" id="knowledge-actions">
                    <button class="btn btn-confirm-all" data-variant="primary" data-size="sm">全部加入</button>
                    <button class="btn btn-ignore-all" data-variant="secondary" data-size="sm">全部忽略</button>
                </div>
            `;
        }
        
        // 達到上限時，顯示限額提示 + 忽略按鈕（忽略不消耗限額）
        return `
            <div class="batch-actions limit-reached" id="knowledge-actions-limited">
                <div class="limit-warning">
                    <span class="limit-icon">📊</span>
                    <span class="limit-message">今日已達上限 (${this.dailyLimitStatus.used_count}/${this.dailyLimitStatus.daily_limit})</span>
                    <button class="btn btn-settings-link" id="limit-settings-btn" data-variant="ghost" data-size="sm">
                        調整設定
                    </button>
                </div>
                <div class="available-actions">
                    <button class="btn btn-ignore-all" data-variant="secondary" data-size="sm">全部忽略</button>
                    <small class="action-hint">💡 忽略不會消耗每日限額</small>
                </div>
            </div>
        `;
    }
    
    /**
     * 綁定限額相關的事件處理
     * @returns {void}
     */
    bindLimitEvents() {
        const settingsBtn = document.getElementById('limit-settings-btn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                // 跳轉到設定頁面的限額設定區域
                window.location.href = '/settings#daily-limit';
            });
        }
    }
    
    /**
     * 使用限額檢查的知識點儲存
     * @param {object} point - 知識點數據
     * @returns {Promise<object>} - 儲存結果
     */
    async saveKnowledgePointWithLimit(point) {
        try {
            const response = await this.fetchAPI(apiEndpoints.getUrl('knowledgeSaveWithLimit'), point);
            
            if (response.success) {
                // 更新限額狀態
                if (response.limit_status) {
                    this.dailyLimitStatus = response.limit_status;
                    this.updateDailyLimitDisplay();
                }
            }
            
            return response;
        } catch (error) {
            console.error('帶限額檢查的知識點儲存失敗:', error);
            return { success: false, message: '儲存失敗' };
        }
    }
}

// CSS styles are now handled by the design system in practice.css

// 當 DOM 載入完成後，啟動系統
document.addEventListener('DOMContentLoaded', () => {
    window.practiceSystem = new PracticeSystem();
});
