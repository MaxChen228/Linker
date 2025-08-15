/**
 * 批量操作處理器 v1.1 - 修復群組ID問題
 * 處理批量操作的 API 調用、進度追蹤、錯誤處理等
 */

// TASK-34: 引入統一API端點管理系統，消除硬編碼
import { apiEndpoints } from './config/api-endpoints.js';

class BatchOperations {
    constructor(selectionManager) {
        this.selection = selectionManager;
        this.activeTasks = new Map();
        this.progressPollers = new Map();
        
        // 版本確認日誌
        console.log('[BatchOperations v1.1] 已載入修復版本 - 群組ID過濾功能已啟用');
    }
    
    /**
     * 過濾並解析有效的知識點ID
     * 排除群組ID (group-*) 和其他無效ID
     */
    parseValidIds(selectedIds) {
        return selectedIds
            .filter(id => {
                // 排除群組ID
                if (String(id).startsWith('group-')) {
                    console.log('[BatchOperations] 排除群組ID:', id);
                    return false;
                }
                return true;
            })
            .map(id => parseInt(id, 10))
            .filter(id => {
                // 排除NaN和負數
                if (isNaN(id) || id <= 0) {
                    console.log('[BatchOperations] 排除無效ID:', id);
                    return false;
                }
                return true;
            });
    }
    
    /**
     * 執行批量刪除
     */
    async batchDelete(ids = null) {
        const selectedIds = ids || this.selection.getSelectedIds();
        
        if (selectedIds.length === 0) {
            this.showNotification('請先選擇要刪除的項目', 'warning');
            return;
        }
        
        // 過濾有效ID
        const validIds = this.parseValidIds(selectedIds);
        
        if (validIds.length === 0) {
            this.showNotification('所選項目中沒有有效的知識點', 'warning');
            return;
        }
        
        if (validIds.length < selectedIds.length) {
            console.log(`[BatchOperations] 過濾後: ${validIds.length}/${selectedIds.length} 個有效ID`);
        }
        
        const confirmMsg = `確定要刪除 ${validIds.length} 個知識點嗎？\n這些知識點將被移至回收站，可以在回收站中復原。\n\n請輸入刪除原因（選填）：`;
        const reason = prompt(confirmMsg);
        
        if (reason === null) {
            return; // 用戶取消
        }
        
        try {
            const response = await fetch(apiEndpoints.getUrl('knowledgeBatch'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'delete',
                    ids: validIds,
                    data: { reason },
                    options: { async: validIds.length > 20 }
                })
            });
            
            const result = await response.json();
            
            if (result.async) {
                // 異步處理，開始追蹤進度
                this.trackProgress(result.task_id, '批量刪除');
            } else {
                // 同步處理完成
                this.handleBatchResult(result, '批量刪除');
            }
            
        } catch (error) {
            console.error('批量刪除失敗:', error);
            this.showNotification('批量刪除失敗', 'error');
        }
    }
    
    /**
     * 執行批量導出
     */
    async batchExport(ids = null, format = 'json') {
        const selectedIds = ids || this.selection.getSelectedIds();
        
        if (selectedIds.length === 0) {
            this.showNotification('請先選擇要導出的項目', 'warning');
            return;
        }
        
        // 過濾有效ID
        const validIds = this.parseValidIds(selectedIds);
        
        if (validIds.length === 0) {
            this.showNotification('所選項目中沒有有效的知識點', 'warning');
            return;
        }
        
        if (validIds.length < selectedIds.length) {
            console.log(`[BatchOperations] 導出過濾後: ${validIds.length}/${selectedIds.length} 個有效ID`);
        }
        
        try {
            const response = await fetch(apiEndpoints.getUrl('knowledgeBatch'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'export',
                    ids: validIds,
                    data: { format },
                    options: { async: false } // 導出通常同步處理
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.result) {
                this.downloadExportData(result.result);
            } else {
                this.handleBatchResult(result, '批量導出');
            }
            
        } catch (error) {
            console.error('批量導出失敗:', error);
            this.showNotification('批量導出失敗', 'error');
        }
    }
    
    /**
     * 執行批量添加標籤
     */
    async batchTag(ids = null) {
        const selectedIds = ids || this.selection.getSelectedIds();
        
        if (selectedIds.length === 0) {
            this.showNotification('請先選擇要添加標籤的項目', 'warning');
            return;
        }
        
        // 過濾有效ID
        const validIds = this.parseValidIds(selectedIds);
        
        if (validIds.length === 0) {
            this.showNotification('所選項目中沒有有效的知識點', 'warning');
            return;
        }
        
        if (validIds.length < selectedIds.length) {
            console.log(`[BatchOperations] 標籤過濾後: ${validIds.length}/${selectedIds.length} 個有效ID`);
        }
        
        // 顯示標籤對話框
        const tags = await this.showTagDialog();
        
        if (!tags || tags.length === 0) {
            return;
        }
        
        try {
            const response = await fetch(apiEndpoints.getUrl('knowledgeBatch'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    operation: 'tag',
                    ids: validIds,
                    data: { tags },
                    options: { async: validIds.length > 30 }
                })
            });
            
            const result = await response.json();
            
            if (result.async) {
                this.trackProgress(result.task_id, '批量添加標籤');
            } else {
                this.handleBatchResult(result, '批量添加標籤');
            }
            
        } catch (error) {
            console.error('批量添加標籤失敗:', error);
            this.showNotification('批量添加標籤失敗', 'error');
        }
    }
    
    /**
     * 追蹤異步任務進度
     */
    async trackProgress(taskId, operationName) {
        // 顯示進度條
        const progressBar = this.createProgressBar(taskId, operationName);
        document.body.appendChild(progressBar);
        
        // 開始輪詢
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/knowledge/batch/${taskId}/progress`);
                const progress = await response.json();
                
                // 更新進度條
                this.updateProgressBar(taskId, progress);
                
                // 檢查是否完成
                if (progress.status === 'completed' || progress.status === 'failed') {
                    clearInterval(pollInterval);
                    this.progressPollers.delete(taskId);
                    
                    // 處理結果
                    this.handleBatchResult(progress, operationName);
                    
                    // 移除進度條
                    setTimeout(() => {
                        const bar = document.getElementById(`progress-${taskId}`);
                        if (bar) {
                            bar.remove();
                        }
                    }, 2000);
                }
                
            } catch (error) {
                console.error('獲取進度失敗:', error);
                clearInterval(pollInterval);
                this.progressPollers.delete(taskId);
            }
        }, 1000);
        
        this.progressPollers.set(taskId, pollInterval);
    }
    
    /**
     * 創建進度條 UI
     */
    createProgressBar(taskId, operationName) {
        const container = document.createElement('div');
        container.id = `progress-${taskId}`;
        container.className = 'batch-progress-container';
        container.innerHTML = `
            <div class="batch-progress-card">
                <div class="progress-header">
                    <span class="progress-title">${operationName}</span>
                    <button class="progress-close" onclick="this.parentElement.parentElement.remove()">×</button>
                </div>
                <div class="progress-bar-wrapper">
                    <div class="progress-bar-fill"></div>
                </div>
                <div class="progress-info">
                    <span class="progress-text">準備中...</span>
                    <span class="progress-percentage">0%</span>
                </div>
            </div>
        `;
        
        // 添加樣式
        if (!document.getElementById('batch-progress-styles')) {
            const styles = document.createElement('style');
            styles.id = 'batch-progress-styles';
            styles.textContent = `
                .batch-progress-container {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 1000;
                    animation: slideInUp 0.3s ease;
                }
                
                .batch-progress-card {
                    background: var(--surface-elevated);
                    border: 1px solid var(--border-default);
                    border-radius: var(--radius-lg);
                    padding: var(--space-4);
                    min-width: 300px;
                    box-shadow: var(--shadow-lg);
                }
                
                .progress-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--space-3);
                }
                
                .progress-title {
                    font-weight: var(--font-medium);
                    color: var(--text-primary);
                }
                
                .progress-close {
                    background: none;
                    border: none;
                    font-size: var(--text-xl);
                    color: var(--text-muted);
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                }
                
                .progress-bar-wrapper {
                    height: 8px;
                    background: var(--bg-tertiary);
                    border-radius: var(--radius-full);
                    overflow: hidden;
                    margin-bottom: var(--space-2);
                }
                
                .progress-bar-fill {
                    height: 100%;
                    background: linear-gradient(90deg, var(--accent-400), var(--accent-600));
                    transition: width 0.3s ease;
                    width: var(--progress, 0%);
                }
                
                .progress-info {
                    display: flex;
                    justify-content: space-between;
                    font-size: var(--text-sm);
                    color: var(--text-secondary);
                }
                
                @keyframes slideInUp {
                    from {
                        transform: translateY(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(styles);
        }
        
        return container;
    }
    
    /**
     * 更新進度條
     */
    updateProgressBar(taskId, progress) {
        const container = document.getElementById(`progress-${taskId}`);
        if (!container) return;
        
        const fill = container.querySelector('.progress-bar-fill');
        const text = container.querySelector('.progress-text');
        const percentage = container.querySelector('.progress-percentage');
        
        if (fill) {
            fill.style.setProperty('--progress', `${progress.progress}%`);
        }
        
        if (text) {
            if (progress.status === 'processing') {
                text.textContent = `處理中 ${progress.processed}/${progress.total}`;
            } else if (progress.status === 'completed') {
                text.textContent = '完成';
            } else if (progress.status === 'failed') {
                text.textContent = '失敗';
            }
        }
        
        if (percentage) {
            percentage.textContent = `${progress.progress}%`;
        }
    }
    
    /**
     * 處理批量操作結果
     */
    handleBatchResult(result, operationName) {
        console.log('[BatchOperations] 處理結果:', result, operationName);
        const hasErrors = result.errors && result.errors.length > 0;
        
        // 修正：正確獲取處理數量
        const processedCount = result.processed || result.total || 0;
        const successCount = hasErrors ? processedCount - result.errors.length : processedCount;
        
        if (result.status === 'completed' || result.success) {
            if (hasErrors) {
                this.showNotification(
                    `${operationName}部分完成：成功 ${successCount} 項，失敗 ${result.errors.length} 項`,
                    'warning'
                );
            } else if (processedCount > 0) {
                this.showNotification(
                    `${operationName}成功：已處理 ${processedCount} 項`,
                    'success'
                );
            } else {
                this.showNotification(
                    `${operationName}完成，但沒有處理任何項目`,
                    'warning'
                );
            }
            
            // 清除選擇並刷新頁面
            this.selection.toggleSelectMode();
            setTimeout(() => {
                location.reload();
            }, 1500);
            
        } else {
            this.showNotification(
                `${operationName}失敗：${result.errors?.[0]?.error || '未知錯誤'}`,
                'error'
            );
        }
        
        // 顯示錯誤詳情
        if (hasErrors) {
            console.error(`${operationName}錯誤詳情:`, result.errors);
        }
    }
    
    /**
     * 下載導出數據
     */
    downloadExportData(exportResult) {
        const { data, format } = exportResult;
        
        let content;
        let filename;
        let mimeType;
        
        if (format === 'json') {
            content = JSON.stringify(data, null, 2);
            filename = `knowledge_export_${new Date().toISOString().split('T')[0]}.json`;
            mimeType = 'application/json';
        } else if (format === 'csv') {
            // TODO: 實作 CSV 格式轉換
            content = this.convertToCSV(data);
            filename = `knowledge_export_${new Date().toISOString().split('T')[0]}.csv`;
            mimeType = 'text/csv';
        } else {
            content = JSON.stringify(data, null, 2);
            filename = `knowledge_export_${new Date().toISOString().split('T')[0]}.txt`;
            mimeType = 'text/plain';
        }
        
        // 創建下載連結
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        this.showNotification(`已導出 ${data.length} 個知識點`, 'success');
    }
    
    /**
     * 顯示標籤對話框
     */
    async showTagDialog() {
        return new Promise((resolve) => {
            // 先確保樣式已加載
            this.ensureStyles();
            
            // 創建模態框
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.innerHTML = `
                <div class="modal-content">
                    <h3>添加標籤</h3>
                    <p class="modal-description">
                        為選中的知識點添加標籤，多個標籤請用逗號分隔
                    </p>
                    <input type="text" id="tag-input" placeholder="例如：重要, 待複習, 語法" class="modal-input" />
                    <div class="modal-actions">
                        <button class="modal-btn" onclick="this.closest('.modal-overlay').remove()">取消</button>
                        <button id="confirm-tags" class="modal-btn btn-primary">確定</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // 綁定事件
            const input = modal.querySelector('#tag-input');
            const confirmBtn = modal.querySelector('#confirm-tags');
            
            input.focus();
            
            const confirm = () => {
                const tags = input.value
                    .split(',')
                    .map(tag => tag.trim())
                    .filter(tag => tag.length > 0);
                
                modal.remove();
                resolve(tags);
            };
            
            confirmBtn.addEventListener('click', confirm);
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    confirm();
                }
            });
            
            // 點擊外部關閉
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    resolve(null);
                }
            });
        });
    }
    
    /**
     * 確保樣式已加載
     */
    ensureStyles() {
        if (!document.getElementById('batch-operation-styles')) {
            const styles = document.createElement('style');
            styles.id = 'batch-operation-styles';
            styles.textContent = this.getStyles();
            document.head.appendChild(styles);
        }
    }
    
    /**
     * 顯示通知
     */
    showNotification(message, type = 'info') {
        // 確保樣式已加載
        this.ensureStyles();
        
        // 創建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // 自動移除
        setTimeout(() => {
            notification.classList.remove('animate-slide-in');
            notification.classList.add('animate-slide-out');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
    
    /**
     * 轉換為 CSV 格式
     */
    convertToCSV(data) {
        if (!data || data.length === 0) return '';
        
        const headers = ['ID', '關鍵點', '錯誤片段', '正確片段', '分類', '掌握度', '錯誤次數'];
        const rows = data.map(point => [
            point.id,
            point.key_point,
            point.original_phrase,
            point.correction,
            point.category,
            (point.mastery_level * 100).toFixed(0) + '%',
            point.mistake_count
        ]);
        
        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');
        
        return csvContent;
    }
    
    /**
     * 獲取所有樣式
     */
    getStyles() {
        return `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: var(--space-3) var(--space-4);
                border-radius: var(--radius-md);
                background: var(--surface-elevated);
                border: 1px solid var(--border-default);
                box-shadow: var(--shadow-lg);
                z-index: 2000;
                animation: slideInRight 0.3s ease;
                max-width: 400px;
            }
            
            .notification-success {
                background: var(--success-100);
                border-color: var(--success-300);
                color: var(--success-700);
            }
            
            .notification-warning {
                background: var(--warning-100);
                border-color: var(--warning-300);
                color: var(--warning-700);
            }
            
            .notification-error {
                background: var(--error-100);
                border-color: var(--error-300);
                color: var(--error-700);
            }
            
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            .notification-exit {
                animation: slideOutRight 0.3s ease !important;
            }
            
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1500;
                animation: fadeIn 0.2s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .modal-content {
                background: var(--surface-base);
                padding: var(--space-6);
                border-radius: var(--radius-lg);
                min-width: 400px;
                box-shadow: var(--shadow-xl);
                animation: slideUp 0.3s ease;
            }
            
            @keyframes slideUp {
                from {
                    transform: translateY(20px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            .modal-content h3 {
                margin: 0 0 var(--space-3) 0;
                color: var(--text-primary);
            }
            
            .modal-description {
                color: var(--text-secondary);
                font-size: var(--text-sm);
                margin-bottom: var(--space-3);
            }
            
            .modal-input {
                width: 100%;
                padding: var(--space-2);
                border: 1px solid var(--border-default);
                border-radius: var(--radius-sm);
                margin-bottom: var(--space-4);
                font-size: var(--text-base);
            }
            
            .modal-actions {
                display: flex;
                gap: var(--space-3);
                justify-content: flex-end;
            }
            
            .modal-btn {
                padding: var(--space-2) var(--space-4);
                border-radius: var(--radius-md);
                border: 1px solid var(--border-default);
                background: var(--surface-base);
                cursor: pointer;
                font-size: var(--text-sm);
                transition: all var(--transition-base);
            }
            
            .modal-btn:hover {
                background: var(--surface-elevated);
            }
            
            .modal-btn.btn-primary {
                background: var(--accent-600);
                color: white;
                border: none;
            }
            
            .modal-btn.btn-primary:hover {
                background: var(--accent-700);
            }
        `;
    }
}

// 導出為全局變量
window.BatchOperations = BatchOperations;