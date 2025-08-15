/**
 * 學習推薦卡片組件 - 浮動模態框版本
 * 負責獲取和顯示個性化學習推薦
 */

class RecommendationCard {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.triggerButton = null;
        this.modalOverlay = null;
        this.modalContainer = null;
        this.recommendations = null;
        this.isLoading = false;
        this.isVisible = false;
        this.autoRefreshInterval = null;
        
        // 配置
        this.config = {
            autoRefresh: false,
            refreshInterval: 300000, // 5 分鐘
            maxPriorityPoints: 5,
            position: options.position || 'bottom-right', // 觸發按鈕位置
            size: options.size || 'default',
            ...options
        };
        
        this.init();
    }
    
    /**
     * 初始化組件
     */
    async init() {
        this.createTriggerButton();
        this.createModal();
        this.setupEventListeners();
        
        // 預載推薦數據
        await this.loadRecommendations();
        
        if (this.config.autoRefresh) {
            this.startAutoRefresh();
        }
    }
    
    /**
     * 創建觸發按鈕
     */
    createTriggerButton() {
        this.triggerButton = document.createElement('button');
        this.triggerButton.className = 'recommendation-trigger';
        this.triggerButton.setAttribute('data-position', this.config.position);
        this.triggerButton.setAttribute('data-size', this.config.size);
        this.triggerButton.setAttribute('aria-label', '查看學習推薦');
        this.triggerButton.setAttribute('title', '學習推薦');
        
        this.triggerButton.innerHTML = `
            <svg class="recommendation-trigger-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 11l3 3L22 4" />
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
            </svg>
        `;
        
        document.body.appendChild(this.triggerButton);
    }
    
    /**
     * 創建模態框
     */
    createModal() {
        // 創建模態框遮罩
        this.modalOverlay = document.createElement('div');
        this.modalOverlay.className = 'recommendation-modal-overlay';
        this.modalOverlay.setAttribute('data-visible', 'false');
        this.modalOverlay.setAttribute('aria-hidden', 'true');
        this.modalOverlay.setAttribute('role', 'dialog');
        this.modalOverlay.setAttribute('aria-labelledby', 'recommendation-modal-title');
        
        // 創建模態框容器
        this.modalContainer = document.createElement('div');
        this.modalContainer.className = 'recommendation-modal';
        this.modalContainer.setAttribute('tabindex', '-1');
        
        this.modalContainer.innerHTML = `
            <div class="recommendation-modal-header">
                <h3 id="recommendation-modal-title" class="recommendation-modal-title">學習推薦</h3>
                <button class="recommendation-modal-close" aria-label="關閉推薦" title="關閉">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="recommendation-modal-content">
                <div class="recommendation-container"></div>
            </div>
        `;
        
        this.modalOverlay.appendChild(this.modalContainer);
        document.body.appendChild(this.modalOverlay);
        
        // 獲取內容容器引用
        this.container = this.modalContainer.querySelector('.recommendation-container');
    }
    
    /**
     * 從 API 載入推薦數據
     */
    async loadRecommendations() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.renderLoadingState();
        
        try {
            const response = await fetch('/api/knowledge/recommendations', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to load recommendations: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success && result.data) {
                this.recommendations = result.data;
                this.render();
            } else {
                this.renderEmptyState();
            }
        } catch (error) {
            console.error('Error loading recommendations:', error);
            this.renderErrorState();
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * 渲染推薦卡片
     */
    render() {
        if (!this.recommendations) {
            this.renderEmptyState();
            return;
        }
        
        const { 
            recommendations = [], 
            focus_areas = [], 
            suggested_difficulty = 2,
            next_review_count = 0,
            priority_points = []
        } = this.recommendations;
        
        const html = `
            <div class="recommendation-card" data-loading="false">
                ${this.renderHeader()}
                
                <div class="recommendation-content">
                    ${recommendations.length > 0 ? this.renderRecommendationList(recommendations) : ''}
                    ${priority_points.length > 0 ? this.renderPriorityPoints(priority_points) : ''}
                    ${this.renderStats(suggested_difficulty, next_review_count)}
                    ${focus_areas.length > 0 ? this.renderFocusAreas(focus_areas) : ''}
                </div>
                
                ${this.renderActions()}
            </div>
        `;
        
        this.container.innerHTML = html;
    }
    
    /**
     * 渲染頭部
     */
    renderHeader() {
        return `
            <div class="recommendation-header">
                <div class="recommendation-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 11l3 3L22 4" />
                        <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
                    </svg>
                </div>
                <div class="recommendation-title-group">
                    <h3 class="recommendation-title">學習推薦</h3>
                    <p class="recommendation-subtitle">根據您的學習進度量身定制</p>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染推薦列表
     */
    renderRecommendationList(recommendations) {
        const items = recommendations.slice(0, 3).map((rec, index) => {
            const priority = index === 0 ? 'high' : index === 1 ? 'medium' : 'low';
            return `
                <li class="recommendation-item">
                    <div class="recommendation-item-icon">
                        ${this.getRecommendationIcon(rec)}
                    </div>
                    <div class="recommendation-item-content">
                        <p class="recommendation-item-text">${this.escapeHtml(rec)}</p>
                        ${this.extractMetaInfo(rec) ? 
                            `<div class="recommendation-item-meta">${this.extractMetaInfo(rec)}</div>` 
                            : ''}
                    </div>
                    <div class="priority-indicator" data-priority="${priority}">
                        <span class="priority-dot"></span>
                    </div>
                </li>
            `;
        }).join('');
        
        return `
            <ul class="recommendation-list">
                ${items}
            </ul>
        `;
    }
    
    /**
     * 渲染優先學習點
     */
    renderPriorityPoints(points) {
        if (points.length === 0) return '';
        
        const displayPoints = points.slice(0, this.config.maxPriorityPoints);
        const items = displayPoints.map(point => {
            const badge = this.getErrorTypeBadge(point.category);
            return `
                <div class="recommendation-item">
                    <div class="recommendation-item-content">
                        <p class="recommendation-item-text">
                            ${badge}
                            <strong>${this.escapeHtml(point.key_point)}</strong>
                        </p>
                        <div class="recommendation-item-meta">
                            掌握度: ${Math.round(point.mastery_level * 100)}% | 
                            錯誤次數: ${point.mistake_count}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        return `
            <div class="priority-points-section">
                <h4 style="font-size: var(--text-sm); color: var(--text-muted); margin: var(--space-3) 0;">
                    優先複習項目
                </h4>
                ${items}
            </div>
        `;
    }
    
    /**
     * 渲染統計資訊
     */
    renderStats(difficulty, reviewCount) {
        return `
            <div class="recommendation-stats">
                <div class="recommendation-stat">
                    <div class="recommendation-stat-value">${difficulty}</div>
                    <div class="recommendation-stat-label">建議難度</div>
                </div>
                <div class="recommendation-stat">
                    <div class="recommendation-stat-value">${reviewCount}</div>
                    <div class="recommendation-stat-label">待複習</div>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染重點領域
     */
    renderFocusAreas(areas) {
        const tags = areas.map(area => {
            const label = this.getFocusAreaLabel(area);
            return `<span class="focus-area-tag">${label}</span>`;
        }).join('');
        
        return `
            <div class="focus-areas">
                <span class="focus-area-label">重點領域:</span>
                ${tags}
            </div>
        `;
    }
    
    /**
     * 渲染行動按鈕
     */
    renderActions() {
        return `
            <div class="recommendation-actions">
                <button class="recommendation-action" data-action="start-practice">
                    開始練習
                </button>
                <button class="recommendation-action" data-variant="secondary" data-action="refresh">
                    刷新推薦
                </button>
            </div>
        `;
    }
    
    /**
     * 渲染載入狀態
     */
    renderLoadingState() {
        this.container.innerHTML = `
            <div class="recommendation-card" data-loading="true">
                <div class="recommendation-header">
                    <div class="recommendation-icon">
                        <div class="spinner"></div>
                    </div>
                    <div class="recommendation-title-group">
                        <h3 class="recommendation-title">載入推薦中...</h3>
                        <p class="recommendation-subtitle">正在分析您的學習數據</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染空狀態
     */
    renderEmptyState() {
        this.container.innerHTML = `
            <div class="recommendation-card">
                <div class="recommendation-empty">
                    <svg class="recommendation-empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M12 2L2 7l10 5 10-5-10-5z" />
                        <path d="M2 17l10 5 10-5" />
                        <path d="M2 12l10 5 10-5" />
                    </svg>
                    <p class="recommendation-empty-text">
                        開始練習以獲得個性化推薦
                    </p>
                </div>
            </div>
        `;
    }
    
    /**
     * 渲染錯誤狀態
     */
    renderErrorState() {
        this.container.innerHTML = `
            <div class="recommendation-card">
                <div class="recommendation-empty">
                    <p class="recommendation-empty-text">
                        載入推薦時發生錯誤，請稍後再試
                    </p>
                </div>
            </div>
        `;
    }
    
    /**
     * 顯示模態框
     */
    showModal() {
        if (this.isVisible) return;
        
        this.isVisible = true;
        this.modalOverlay.setAttribute('data-visible', 'true');
        this.modalOverlay.setAttribute('aria-hidden', 'false');
        
        // 聚焦到模態框以支援鍵盤導航
        this.modalContainer.focus();
        
        // 防止背景滾動
        document.body.style.overflow = 'hidden';
        
        // 如果數據還未載入，顯示載入狀態
        if (!this.recommendations && !this.isLoading) {
            this.loadRecommendations();
        }
    }
    
    /**
     * 隱藏模態框
     */
    hideModal() {
        if (!this.isVisible) return;
        
        this.isVisible = false;
        this.modalOverlay.setAttribute('data-visible', 'false');
        this.modalOverlay.setAttribute('aria-hidden', 'true');
        
        // 恢復背景滾動
        document.body.style.overflow = '';
        
        // 聚焦回觸發按鈕
        this.triggerButton.focus();
    }
    
    /**
     * 切換模態框顯示狀態
     */
    toggleModal() {
        if (this.isVisible) {
            this.hideModal();
        } else {
            this.showModal();
        }
    }
    
    /**
     * 設置事件監聽器
     */
    setupEventListeners() {
        // 觸發按鈕點擊事件
        this.triggerButton.addEventListener('click', () => {
            this.toggleModal();
        });
        
        // 關閉按鈕點擊事件
        const closeButton = this.modalContainer.querySelector('.recommendation-modal-close');
        closeButton.addEventListener('click', () => {
            this.hideModal();
        });
        
        // 點擊遮罩關閉
        this.modalOverlay.addEventListener('click', (e) => {
            if (e.target === this.modalOverlay) {
                this.hideModal();
            }
        });
        
        // ESC 鍵關閉
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hideModal();
            }
        });
        
        // 推薦內容的點擊事件
        this.container.addEventListener('click', (e) => {
            const action = e.target.closest('[data-action]');
            if (!action) return;
            
            switch (action.dataset.action) {
                case 'start-practice':
                    this.handleStartPractice();
                    // 開始練習後關閉模態框
                    this.hideModal();
                    break;
                case 'refresh':
                    this.loadRecommendations();
                    break;
            }
        });
        
        // 防止模態框內容點擊時關閉
        this.modalContainer.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    /**
     * 處理開始練習
     */
    handleStartPractice() {
        if (!this.recommendations) return;
        
        const { suggested_difficulty = 2, focus_areas = [] } = this.recommendations;
        
        // 觸發自定義事件，讓練習頁面處理
        const event = new CustomEvent('recommendation-practice', {
            detail: {
                difficulty: suggested_difficulty,
                focus_areas: focus_areas,
                mode: focus_areas.includes('systematic') ? 'review' : 'new'
            }
        });
        
        document.dispatchEvent(event);
    }
    
    /**
     * 開始自動刷新
     */
    startAutoRefresh() {
        this.stopAutoRefresh();
        this.autoRefreshInterval = setInterval(() => {
            this.loadRecommendations();
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
     * 獲取推薦圖標
     */
    getRecommendationIcon(text) {
        if (text.includes('systematic') || text.includes('系統性')) {
            return '📊';
        } else if (text.includes('isolated') || text.includes('個別')) {
            return '📝';
        } else if (text.includes('複習')) {
            return '🔄';
        } else if (text.includes('練習')) {
            return '✏️';
        }
        return '💡';
    }
    
    /**
     * 提取元信息
     */
    extractMetaInfo(text) {
        const match = text.match(/\(([^)]+)\)/);
        return match ? match[1] : null;
    }
    
    /**
     * 獲取錯誤類型徽章
     */
    getErrorTypeBadge(category) {
        const badges = {
            'systematic': '<span class="error-type-badge" data-type="systematic">系統性</span>',
            'isolated': '<span class="error-type-badge" data-type="isolated">個別</span>',
            'enhancement': '<span class="error-type-badge" data-type="enhancement">增強</span>',
            'other': '<span class="error-type-badge" data-type="other">其他</span>'
        };
        return badges[category] || '';
    }
    
    /**
     * 獲取重點領域標籤
     */
    getFocusAreaLabel(area) {
        const labels = {
            'systematic': '文法規則',
            'isolated': '單詞記憶',
            'enhancement': '表達優化',
            'review': '複習鞏固',
            'new': '新知識'
        };
        return labels[area] || area;
    }
    
    /**
     * HTML 轉義
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * 銷毀組件
     */
    destroy() {
        this.stopAutoRefresh();
        
        // 隱藏模態框
        this.hideModal();
        
        // 移除元素
        if (this.triggerButton && this.triggerButton.parentNode) {
            this.triggerButton.parentNode.removeChild(this.triggerButton);
        }
        
        if (this.modalOverlay && this.modalOverlay.parentNode) {
            this.modalOverlay.parentNode.removeChild(this.modalOverlay);
        }
        
        // 清理引用
        this.triggerButton = null;
        this.modalOverlay = null;
        this.modalContainer = null;
        this.container = null;
        this.recommendations = null;
    }
    
    /**
     * 公開方法：手動顯示模態框
     */
    show() {
        this.showModal();
    }
    
    /**
     * 公開方法：手動隱藏模態框
     */
    hide() {
        this.hideModal();
    }
    
    /**
     * 公開方法：獲取推薦狀態
     */
    getRecommendations() {
        return this.recommendations;
    }
    
    /**
     * 公開方法：檢查是否正在載入
     */
    isLoadingRecommendations() {
        return this.isLoading;
    }
    
    /**
     * 公開方法：檢查模態框是否可見
     */
    isModalVisible() {
        return this.isVisible;
    }
}

// 導出給全局使用
window.RecommendationCard = RecommendationCard;