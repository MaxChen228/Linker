/**
 * 每日目標組件 - 可復用的每日進度追蹤和目標設定組件
 * 可在主頁統計卡片和設定頁面等多處使用
 */

class DailyGoalWidget {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = null;
        this.data = null;
        this.isLoading = false;
        this.isUpdating = false;
        this.autoRefreshInterval = null;
        
        // 配置
        this.config = {
            mode: options.mode || 'card', // 'card' | 'detailed'
            autoRefresh: options.autoRefresh || false,
            refreshInterval: options.refreshInterval || 60000, // 1 分鐘
            showInput: options.showInput !== false, // 預設顯示輸入框
            inline: options.inline || false, // 是否內聯模式
            initialData: options.initialData || null, // 初始數據
            ...options
        };
        
        this.init();
    }
    
    /**
     * 初始化組件
     */
    async init() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`DailyGoalWidget: Container with id '${this.containerId}' not found`);
            return;
        }
        
        this.setupContainer();
        this.setupEventListeners();
        
        // 使用初始數據或載入新數據
        if (this.config.initialData) {
            this.processInitialData(this.config.initialData);
        } else {
            await this.loadData();
        }
        
        if (this.config.autoRefresh) {
            this.startAutoRefresh();
        }
    }
    
    /**
     * 設置容器
     */
    setupContainer() {
        this.container.className = `daily-goal-widget ${this.config.mode} ${this.config.inline ? 'inline' : ''}`;
        this.container.setAttribute('data-widget', 'daily-goal');
    }
    
    /**
     * 處理初始數據
     */
    processInitialData(initialData) {
        try {
            // 合併初始數據
            const { status = {}, config = {} } = initialData;
            
            this.data = {
                ...status,
                ...config,
                // 計算進度百分比 - 修復：daily_limit 在 config 中，不在 status 中
                progressPercent: status.used_count >= 0 && config.daily_limit > 0 ?
                    Math.round((status.used_count / config.daily_limit) * 100) : 0
            };
            
            this.render();
            
            // 標記為已載入，但不打擾後續的 API 調用
            console.log('DailyGoalWidget: 初始數據已載入', this.data);
        } catch (error) {
            console.error('Error processing initial data:', error);
            // 🔥 防止無限循環：只在沒有正在載入時才備用為 API 載入
            if (!this.isLoading) {
                console.log('Initial data failed, falling back to API load');
                this.loadData();
            } else {
                console.error('Cannot fallback to API load: already loading');
                this.renderErrorState();
            }
        }
    }
    
    /**
     * 載入每日目標數據
     */
    async loadData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.renderLoadingState();
        
        try {
            // 使用全局 apiEndpoints（已在 api-endpoints.js 中註冊到 window）
            const apiEndpoints = window.apiEndpoints;
            if (!apiEndpoints) {
                throw new Error('API endpoints not available');
            }
            
            // 🔥 優化：只調用 status 端點，它已經包含所有數據！
            const statusResponse = await fetch(apiEndpoints.getUrl('knowledgeDailyLimitStatus'));
            
            if (!statusResponse.ok) {
                throw new Error('Failed to load daily goal data');
            }
            
            const mergedData = await statusResponse.json();
            
            console.log('🎯 優化成功：從2個API調用減少到1個', mergedData);
            
            // 驗證必要字段
            if (typeof mergedData.daily_limit !== 'number' || mergedData.daily_limit <= 0) {
                throw new Error(`Invalid daily_limit: ${mergedData.daily_limit}. 必須是正整數`);
            }
            
            if (typeof mergedData.used_count !== 'number' || mergedData.used_count < 0) {
                throw new Error(`Invalid used_count: ${mergedData.used_count}. 必須是非負整數`);
            }
            
            // 計算進度百分比（只有在數據有效時）
            const progressPercent = mergedData.used_count > 0 ? 
                Math.round((mergedData.used_count / mergedData.daily_limit) * 100) : 0;
                
            this.data = {
                ...mergedData,
                progressPercent
            };
            
            console.log('✅ Daily goal data loaded successfully:', this.data);
            this.render();
        } catch (error) {
            console.error('Error loading daily goal data:', error);
            this.renderErrorState();
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * 更新目標設定
     */
    async updateGoal(newLimit) {
        if (this.isUpdating) return false;
        
        const limit = parseInt(newLimit);
        if (isNaN(limit) || limit < 1 || limit > 50) {
            this.showError('目標必須在 1-50 之間');
            return false;
        }
        
        this.isUpdating = true;
        this.showUpdatingState();
        
        try {
            // 使用全局 apiEndpoints
            const apiEndpoints = window.apiEndpoints;
            if (!apiEndpoints) {
                throw new Error('API endpoints not available');
            }
            
            const response = await fetch(apiEndpoints.getUrl('knowledgeDailyLimitConfig'), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    daily_limit: limit,
                    limit_enabled: true
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to update goal: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // 更新本地數據
                this.data.daily_limit = limit;
                this.data.progressPercent = this.data.used_count ? 
                    Math.round((this.data.used_count / limit) * 100) : 0;
                
                this.render();
                this.showSuccess('目標已更新');
                
                // 觸發更新事件
                this.dispatchEvent('goalUpdated', { newLimit: limit });
                return true;
            } else {
                throw new Error(result.message || 'Update failed');
            }
        } catch (error) {
            console.error('Error updating goal:', error);
            this.showError('目標更新失敗');
            return false;
        } finally {
            this.isUpdating = false;
            this.clearUpdatingState();
        }
    }
    
    /**
     * 渲染組件
     */
    render() {
        if (!this.data) {
            this.renderEmptyState();
            return;
        }
        
        const html = this.config.mode === 'card' ? 
            this.renderCardMode() : 
            this.renderDetailedMode();
        
        this.container.innerHTML = html;
        this.bindInputEvents();
    }
    
    /**
     * 渲染卡片模式（主頁統計區域）
     */
    renderCardMode() {
        // 🔥 數據驅動：只有在數據完全有效時才渲染
        if (!this.data || typeof this.data.daily_limit !== 'number') {
            console.error('❌ renderCardMode called with invalid data:', this.data);
            return this.renderErrorState();
        }
        
        const { used_count, daily_limit, progressPercent, can_add_more } = this.data;
        
        return `
            <div class="daily-goal-card">
                <div class="goal-header">
                    <h3 class="goal-title">每日目標</h3>
                    <span class="goal-status ${can_add_more ? 'active' : 'completed'}" 
                          title="${can_add_more ? '可繼續新增' : '今日已達上限'}">
                        ${can_add_more ? '●' : '✓'}
                    </span>
                </div>
                
                <div class="goal-progress">
                    <div class="progress-numbers">
                        <span class="progress-current">${used_count}</span>
                        <span class="progress-separator">/</span>
                        <span class="progress-total">${daily_limit}</span>
                        <span class="progress-unit">個</span>
                    </div>
                    
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${Math.min(progressPercent, 100)}%"></div>
                    </div>
                    
                    <div class="progress-percent">${progressPercent}%</div>
                </div>
                
                ${this.config.showInput ? this.renderGoalInput(daily_limit) : ''}
            </div>
        `;
    }
    
    /**
     * 渲染詳細模式（設定頁面）
     */
    renderDetailedMode() {
        // 🔥 數據驅動：只有在數據完全有效時才渲染
        if (!this.data || typeof this.data.daily_limit !== 'number') {
            console.error('❌ renderDetailedMode called with invalid data:', this.data);
            return this.renderErrorState();
        }
        
        const { 
            used_count, 
            daily_limit, 
            progressPercent, 
            can_add_more,
            breakdown = { isolated: 0, enhancement: 0 }
        } = this.data;
        
        return `
            <div class="daily-goal-detailed">
                <div class="goal-overview">
                    <div class="goal-main-stats">
                        <div class="main-progress">
                            <div class="progress-circle" data-percent="${progressPercent}">
                                <svg viewBox="0 0 36 36" class="circular-chart">
                                    <path class="circle-bg" 
                                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                    <path class="circle" 
                                          stroke-dasharray="${progressPercent}, 100"
                                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                                </svg>
                                <div class="progress-text">
                                    <span class="progress-number">${used_count}</span>
                                    <span class="progress-total-small">/ ${daily_limit}</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="progress-info">
                            <h3>今日進度</h3>
                            <p class="status-text ${can_add_more ? 'active' : 'completed'}">
                                ${can_add_more ? 
                                    `還可新增 ${daily_limit - used_count} 個知識點` : 
                                    '今日目標已達成！'}
                            </p>
                        </div>
                    </div>
                    
                    <div class="goal-breakdown">
                        <div class="breakdown-item">
                            <span class="breakdown-label">單一知識點</span>
                            <span class="breakdown-value">${breakdown.isolated || 0}</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">可以更好</span>
                            <span class="breakdown-value">${breakdown.enhancement || 0}</span>
                        </div>
                    </div>
                </div>
                
                ${this.config.showInput ? this.renderGoalInput(daily_limit, true) : ''}
            </div>
        `;
    }
    
    /**
     * 渲染目標輸入框
     */
    renderGoalInput(currentLimit, detailed = false) {
        return `
            <div class="goal-input-section ${detailed ? 'detailed' : ''}">
                <div class="goal-input-group">
                    <label for="goal-input-${this.containerId}" class="goal-input-label">
                        ${detailed ? '調整每日目標' : '目標'}
                    </label>
                    <div class="goal-input-wrapper">
                        <input type="number" 
                               id="goal-input-${this.containerId}"
                               class="goal-input" 
                               value="${currentLimit}" 
                               min="1" 
                               max="50"
                               ${this.isUpdating ? 'disabled' : ''} />
                        <button class="goal-update-btn" 
                                ${this.isUpdating ? 'disabled' : ''}
                                title="更新目標">
                            ${this.isUpdating ? 
                                '<span class="spinner-sm"></span>' : 
                                '✓'}
                        </button>
                    </div>
                </div>
                
                <div class="goal-feedback" id="goal-feedback-${this.containerId}"></div>
            </div>
        `;
    }
    
    /**
     * 渲染載入狀態
     */
    renderLoadingState() {
        this.container.innerHTML = `
            <div class="daily-goal-loading">
                <div class="spinner"></div>
                <span class="loading-text">載入中...</span>
            </div>
        `;
    }
    
    /**
     * 渲染空狀態
     */
    renderEmptyState() {
        this.container.innerHTML = `
            <div class="daily-goal-empty">
                <span class="empty-icon">📊</span>
                <p class="empty-text">無法載入每日目標數據</p>
            </div>
        `;
    }
    
    /**
     * 渲染錯誤狀態
     */
    renderErrorState() {
        this.container.innerHTML = `
            <div class="daily-goal-error">
                <span class="error-icon">⚠️</span>
                <p class="error-text">載入失敗</p>
                <button class="error-retry-btn" onclick="this.parentElement.parentElement.__dailyGoalWidget?.loadData()">
                    重試
                </button>
            </div>
        `;
        
        // 儲存實例引用以便重試
        this.container.__dailyGoalWidget = this;
    }
    
    /**
     * 綁定輸入事件
     */
    bindInputEvents() {
        const input = this.container.querySelector('.goal-input');
        const updateBtn = this.container.querySelector('.goal-update-btn');
        
        if (!input || !updateBtn) return;
        
        // 輸入變化時顯示更新按鈕
        input.addEventListener('input', () => {
            const currentValue = parseInt(input.value);
            const originalValue = this.data?.daily_limit;
            
            if (currentValue !== originalValue) {
                updateBtn.style.opacity = '1';
                updateBtn.style.transform = 'scale(1)';
            } else {
                updateBtn.style.opacity = '0.6';
                updateBtn.style.transform = 'scale(0.9)';
            }
        });
        
        // Enter 鍵更新
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleGoalUpdate();
            }
        });
        
        // 按鈕點擊更新
        updateBtn.addEventListener('click', () => {
            this.handleGoalUpdate();
        });
    }
    
    /**
     * 處理目標更新
     */
    async handleGoalUpdate() {
        const input = this.container.querySelector('.goal-input');
        if (!input) return;
        
        const newValue = input.value.trim();
        await this.updateGoal(newValue);
    }
    
    /**
     * 顯示更新狀態
     */
    showUpdatingState() {
        const btn = this.container.querySelector('.goal-update-btn');
        if (btn) {
            btn.innerHTML = '<span class="spinner-sm"></span>';
            btn.disabled = true;
        }
    }
    
    /**
     * 清除更新狀態
     */
    clearUpdatingState() {
        const btn = this.container.querySelector('.goal-update-btn');
        if (btn) {
            btn.innerHTML = '✓';
            btn.disabled = false;
        }
    }
    
    /**
     * 顯示成功訊息
     */
    showSuccess(message) {
        this.showFeedback(message, 'success');
    }
    
    /**
     * 顯示錯誤訊息
     */
    showError(message) {
        this.showFeedback(message, 'error');
    }
    
    /**
     * 顯示反饋訊息
     */
    showFeedback(message, type) {
        const feedback = this.container.querySelector(`#goal-feedback-${this.containerId}`);
        if (!feedback) return;
        
        feedback.innerHTML = `
            <div class="feedback-message ${type}">
                ${type === 'success' ? '✓' : '⚠️'} ${message}
            </div>
        `;
        
        // 3秒後清除
        setTimeout(() => {
            if (feedback) {
                feedback.innerHTML = '';
            }
        }, 3000);
    }
    
    /**
     * 設置事件監聽器
     */
    setupEventListeners() {
        // 全局事件監聽（例如其他組件的更新）
        document.addEventListener('dailyGoalUpdated', () => {
            this.loadData();
        });
    }
    
    /**
     * 觸發自定義事件
     */
    dispatchEvent(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
        
        // 也在容器上觸發
        this.container.dispatchEvent(event);
    }
    
    /**
     * 開始自動刷新
     */
    startAutoRefresh() {
        this.stopAutoRefresh();
        this.autoRefreshInterval = setInterval(() => {
            this.loadData();
        }, this.config.refreshInterval);
    }
    
    /**
     * 停止自動刷新
     */
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
    
    /**
     * 獲取當前數據
     */
    getData() {
        return this.data;
    }
    
    /**
     * 手動刷新數據
     */
    refresh() {
        return this.loadData();
    }
    
    /**
     * 銷毀組件
     */
    destroy() {
        this.stopAutoRefresh();
        
        // 清理事件監聽器
        document.removeEventListener('dailyGoalUpdated', this.loadData);
        
        // 清理容器
        if (this.container) {
            this.container.innerHTML = '';
            this.container.className = '';
            this.container.removeAttribute('data-widget');
            delete this.container.__dailyGoalWidget;
        }
        
        // 清理引用
        this.container = null;
        this.data = null;
    }
}

// 導出給全局使用
window.DailyGoalWidget = DailyGoalWidget;