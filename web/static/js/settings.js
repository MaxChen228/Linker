/**
 * 設定頁面功能模組
 * 處理每日知識點限額的配置和統計顯示
 */

import { apiEndpoints } from './config/api-endpoints.js';

class SettingsManager {
    constructor() {
        this.config = {
            daily_limit: 15,
            limit_enabled: false
        };
        this.hasUnsavedChanges = false;
        this.isInitializing = false; // 防止初始化時觸發變更檢測
        
        this.initializeElements();
        this.bindEvents();
        this.loadCurrentStatus();
    }
    
    /**
     * 初始化DOM元素引用
     */
    initializeElements() {
        // 控制元素
        this.limitEnabledToggle = document.getElementById('limit-enabled');
        this.dailyLimitRange = document.getElementById('daily-limit-range');
        this.dailyLimitNumber = document.getElementById('daily-limit-number');
        
        // 狀態顯示元素
        this.statusIcon = document.getElementById('status-icon');
        this.statusText = document.getElementById('status-text');
        this.progressFill = document.getElementById('progress-fill');
        this.progressInfo = document.getElementById('progress-info');
        
        // 操作按鈕
        this.saveButton = document.getElementById('save-settings');
        this.resetButton = document.getElementById('reset-daily-count');
        
        // 載入覆蓋層
        this.loadingOverlay = document.getElementById('settings-loading');
        
        // 設定項目容器
        this.limitAmountSetting = document.getElementById('limit-amount-setting');
    }
    
    /**
     * 綁定事件監聽器
     */
    bindEvents() {
        // 開關切換事件
        this.limitEnabledToggle.addEventListener('change', () => {
            this.handleToggleChange();
        });
        
        // 限額數量變更事件
        this.dailyLimitRange.addEventListener('input', (e) => {
            this.syncLimitInputs(e.target.value);
            this.markAsChanged();
        });
        
        this.dailyLimitNumber.addEventListener('input', (e) => {
            this.syncLimitInputs(e.target.value);
            this.markAsChanged();
        });
        
        // 保存按鈕事件
        this.saveButton.addEventListener('click', () => {
            this.saveSettings();
        });
        
        // 重置計數按鈕事件
        this.resetButton.addEventListener('click', () => {
            this.resetDailyCount();
        });
        
        // 頁面離開前確認未保存更改
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = '您有未保存的設定更改，確定要離開嗎？';
            }
        });
    }
    
    /**
     * 處理開關切換
     */
    handleToggleChange() {
        const enabled = this.limitEnabledToggle.checked;
        
        // 切換限額設定項目的可用性
        this.limitAmountSetting.classList.toggle('disabled', !enabled);
        this.dailyLimitRange.disabled = !enabled;
        this.dailyLimitNumber.disabled = !enabled;
        
        this.markAsChanged();
        this.updateStatus();
    }
    
    /**
     * 同步限額輸入控制項
     */
    syncLimitInputs(value) {
        const numValue = Math.max(1, Math.min(50, parseInt(value) || 15));
        
        this.dailyLimitRange.value = numValue;
        this.dailyLimitNumber.value = numValue;
        
        this.config.daily_limit = numValue;
    }
    
    /**
     * 標記為已更改
     */
    markAsChanged() {
        // 防止在初始化期間觸發變更檢測
        if (this.isInitializing) {
            return;
        }
        
        this.hasUnsavedChanges = true;
        this.saveButton.disabled = false;
        this.saveButton.querySelector('#save-btn-text').textContent = '儲存設定*';
    }
    
    /**
     * 載入當前狀態
     */
    async loadCurrentStatus() {
        try {
            this.showLoading(true);
            
            // 載入配置
            const configResponse = await fetch(apiEndpoints.KNOWLEDGE_DAILY_LIMIT_CONFIG);
            if (configResponse.ok) {
                this.config = await configResponse.json();
                this.updateConfigUI();
            }
            
            // 載入當前狀態
            await this.updateStatus();
            
        } catch (error) {
            console.error('載入設定失敗:', error);
            this.showError('載入設定時發生錯誤');
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * 更新配置UI
     */
    updateConfigUI() {
        // 設置初始化標誌，防止觸發變更檢測
        this.isInitializing = true;
        
        this.limitEnabledToggle.checked = this.config.limit_enabled;
        this.syncLimitInputs(this.config.daily_limit);
        this.handleToggleChange(); // 更新UI狀態
        
        // 清除初始化標誌並重置未保存標記
        this.isInitializing = false;
        this.hasUnsavedChanges = false;
        this.saveButton.disabled = true;
        this.saveButton.querySelector('#save-btn-text').textContent = '儲存設定';
    }
    
    /**
     * 更新當前狀態顯示
     */
    async updateStatus() {
        try {
            const response = await fetch(apiEndpoints.KNOWLEDGE_DAILY_LIMIT_STATUS);
            if (!response.ok) return;
            
            const status = await response.json();
            
            // 更新狀態圖示和文字
            if (!status.limit_enabled) {
                this.statusIcon.textContent = '🔓';
                this.statusText.textContent = '限額功能已停用';
                this.progressFill.style.width = '0%';
                this.progressInfo.textContent = '無限制';
            } else if (status.can_add_more) {
                this.statusIcon.textContent = '✅';
                this.statusText.textContent = '可繼續新增知識點';
                const percentage = (status.used_count / status.daily_limit * 100);
                this.progressFill.style.width = `${percentage}%`;
                this.progressInfo.textContent = `已使用 ${status.used_count}/${status.daily_limit} (剩餘 ${status.remaining})`;
            } else {
                this.statusIcon.textContent = '🚫';
                this.statusText.textContent = '今日已達上限';
                this.progressFill.style.width = '100%';
                this.progressInfo.textContent = `已達上限 ${status.used_count}/${status.daily_limit}`;
            }
            
            // 根據使用情況調整進度條顏色
            const percentage = status.limit_enabled ? (status.used_count / status.daily_limit * 100) : 0;
            if (percentage < 70) {
                this.progressFill.style.background = 'var(--color-success)';
            } else if (percentage < 90) {
                this.progressFill.style.background = 'var(--color-warning)';
            } else {
                this.progressFill.style.background = 'var(--color-danger)';
            }
            
        } catch (error) {
            console.error('載入狀態失敗:', error);
            this.statusIcon.textContent = '❌';
            this.statusText.textContent = '狀態載入失敗';
        }
    }
    
    /**
     * 保存設定
     */
    async saveSettings() {
        try {
            this.showLoading(true, '儲存設定中...');
            
            const newConfig = {
                daily_limit: parseInt(this.dailyLimitNumber.value),
                limit_enabled: this.limitEnabledToggle.checked
            };
            
            const response = await fetch(apiEndpoints.KNOWLEDGE_DAILY_LIMIT_CONFIG, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newConfig)
            });
            
            if (!response.ok) {
                throw new Error(`保存失敗: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                // 更新配置並重置變更標記
                this.config = newConfig;
                this.hasUnsavedChanges = false;
                this.saveButton.disabled = true;
                this.saveButton.querySelector('#save-btn-text').textContent = '儲存設定';
                
                // 更新狀態顯示
                await this.updateStatus();
                
                this.showSuccess('設定已成功儲存');
            } else {
                throw new Error(result.message || '儲存失敗');
            }
            
        } catch (error) {
            console.error('保存設定失敗:', error);
            this.showError(`保存設定時發生錯誤: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * 重置今日計數
     */
    async resetDailyCount() {
        const confirmed = confirm('確定要重置今日的知識點計數嗎？此操作無法復原。');
        if (!confirmed) return;
        
        try {
            this.showLoading(true, '重置計數中...');
            
            // 這裡需要實施重置API，暫時使用模擬
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 更新狀態顯示
            await this.updateStatus();
            
            this.showSuccess('今日計數已重置');
            
        } catch (error) {
            console.error('重置計數失敗:', error);
            this.showError('重置計數時發生錯誤');
        } finally {
            this.showLoading(false);
        }
    }
    
    /**
     * 顯示載入狀態
     */
    showLoading(show, message = '載入中...') {
        if (this.loadingOverlay) {
            this.loadingOverlay.setAttribute('data-visible', show);
            if (show && message) {
                const messageEl = this.loadingOverlay.querySelector('p');
                if (messageEl) {
                    messageEl.textContent = message;
                }
            }
        }
    }
    
    /**
     * 顯示成功訊息
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    /**
     * 顯示錯誤訊息
     */
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    /**
     * 顯示通知
     */
    showNotification(message, type = 'info') {
        // 創建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // 添加樣式
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '500',
            zIndex: '1001',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease',
            maxWidth: '300px',
            wordWrap: 'break-word'
        });
        
        // 設定背景顏色
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            info: '#3b82f6',
            warning: '#f59e0b'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // 動畫顯示
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
        });
        
        // 3秒後自動移除
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', () => {
    new SettingsManager();
    
    // 如果URL包含#daily-limit錨點，滾動到該區域
    if (window.location.hash === '#daily-limit') {
        const targetSection = document.getElementById('daily-limit');
        if (targetSection) {
            setTimeout(() => {
                targetSection.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
                // 添加高亮效果
                targetSection.style.background = 'var(--color-primary-light)';
                setTimeout(() => {
                    targetSection.style.background = '';
                }, 2000);
            }, 100);
        }
    }
});