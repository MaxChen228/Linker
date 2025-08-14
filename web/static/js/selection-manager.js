/**
 * 知識點選擇狀態管理器
 * 管理批量選擇、狀態同步、事件通知等功能
 */

class SelectionManager {
    constructor() {
        // 核心狀態
        this.selectedItems = new Set();
        this.selectMode = false;
        this.lastSelectedIndex = -1;
        
        // 事件監聽器
        this.listeners = {
            'selectionchange': [],
            'modechange': [],
            'selectall': [],
            'deselectall': []
        };
        
        // 緩存 DOM 元素
        this.itemsCache = null;
        this.toolbarEl = null;
        
        // 初始化
        this.init();
    }
    
    /**
     * 初始化管理器
     */
    init() {
        // 綁定全局事件
        this.bindGlobalEvents();
        
        // 初始化工具列
        this.initToolbar();
        
        // 恢復會話狀態（如果有）
        this.restoreSession();
    }
    
    /**
     * 進入/退出選擇模式
     */
    toggleSelectMode() {
        this.selectMode = !this.selectMode;
        
        if (!this.selectMode) {
            this.clearSelection();
        }
        
        // 更新 UI
        document.body.classList.toggle('select-mode', this.selectMode);
        
        // 觸發事件
        this.emit('modechange', { mode: this.selectMode });
        
        // 更新工具列
        this.updateToolbar();
        
        console.log(`[SelectionManager] 選擇模式: ${this.selectMode ? '開啟' : '關閉'}`);
    }
    
    /**
     * 選擇/取消選擇單個項目
     */
    toggleItem(itemId, index = -1) {
        if (!this.selectMode) {
            return false;
        }
        
        const id = String(itemId);
        
        if (this.selectedItems.has(id)) {
            this.selectedItems.delete(id);
        } else {
            this.selectedItems.add(id);
        }
        
        // 記錄最後選擇的索引（用於範圍選擇）
        if (index >= 0) {
            this.lastSelectedIndex = index;
        }
        
        // 更新 UI
        this.updateItemUI(id);
        
        // 觸發事件
        this.emit('selectionchange', {
            selected: Array.from(this.selectedItems),
            count: this.selectedItems.size
        });
        
        // 更新工具列
        this.updateToolbar();
        
        return true;
    }
    
    /**
     * 範圍選擇（Shift + Click）
     */
    selectRange(startIndex, endIndex) {
        if (!this.selectMode) {
            return;
        }
        
        const items = this.getAllItems();
        const min = Math.min(startIndex, endIndex);
        const max = Math.max(startIndex, endIndex);
        
        for (let i = min; i <= max; i++) {
            const item = items[i];
            if (item) {
                const id = this.getItemId(item);
                if (id) {
                    this.selectedItems.add(String(id));
                    this.updateItemUI(id);
                }
            }
        }
        
        this.emit('selectionchange', {
            selected: Array.from(this.selectedItems),
            count: this.selectedItems.size
        });
        
        this.updateToolbar();
    }
    
    /**
     * 全選
     */
    selectAll() {
        if (!this.selectMode) {
            this.toggleSelectMode();
        }
        
        const items = this.getAllItems();
        
        items.forEach(item => {
            const id = this.getItemId(item);
            if (id) {
                this.selectedItems.add(String(id));
                this.updateItemUI(id);
            }
        });
        
        this.emit('selectall', {
            count: this.selectedItems.size
        });
        
        this.emit('selectionchange', {
            selected: Array.from(this.selectedItems),
            count: this.selectedItems.size
        });
        
        this.updateToolbar();
    }
    
    /**
     * 取消全選
     */
    deselectAll() {
        this.clearSelection();
        
        this.emit('deselectall', {});
        
        this.updateToolbar();
    }
    
    /**
     * 反選
     */
    invertSelection() {
        if (!this.selectMode) {
            this.toggleSelectMode();
        }
        
        const items = this.getAllItems();
        const newSelection = new Set();
        
        items.forEach(item => {
            const id = String(this.getItemId(item));
            if (id) {
                if (!this.selectedItems.has(id)) {
                    newSelection.add(id);
                }
                this.updateItemUI(id);
            }
        });
        
        this.selectedItems = newSelection;
        
        // 更新所有項目的 UI
        items.forEach(item => {
            const id = this.getItemId(item);
            if (id) {
                this.updateItemUI(id);
            }
        });
        
        this.emit('selectionchange', {
            selected: Array.from(this.selectedItems),
            count: this.selectedItems.size
        });
        
        this.updateToolbar();
    }
    
    /**
     * 清除所有選擇
     */
    clearSelection() {
        this.selectedItems.forEach(id => {
            this.updateItemUI(id, false);
        });
        
        this.selectedItems.clear();
        this.lastSelectedIndex = -1;
        
        this.emit('selectionchange', {
            selected: [],
            count: 0
        });
    }
    
    /**
     * 獲取選中的項目 ID 列表
     */
    getSelectedIds() {
        return Array.from(this.selectedItems);
    }
    
    /**
     * 獲取選中數量
     */
    getSelectedCount() {
        return this.selectedItems.size;
    }
    
    /**
     * 檢查項目是否被選中
     */
    isSelected(itemId) {
        return this.selectedItems.has(String(itemId));
    }
    
    /**
     * 更新單個項目的 UI
     */
    updateItemUI(itemId, selected = null) {
        const isSelected = selected !== null ? selected : this.isSelected(itemId);
        const elements = document.querySelectorAll(`[data-item-id="${itemId}"]`);
        
        elements.forEach(el => {
            el.classList.toggle('selected', isSelected);
            
            // 更新 checkbox
            const checkbox = el.querySelector('.selection-checkbox');
            if (checkbox) {
                checkbox.checked = isSelected;
            }
        });
    }
    
    /**
     * 更新工具列顯示
     */
    updateToolbar() {
        if (!this.toolbarEl) {
            this.toolbarEl = document.querySelector('.batch-toolbar');
        }
        
        if (!this.toolbarEl) return;
        
        const count = this.getSelectedCount();
        const hasSelection = count > 0;
        
        // 更新工具列狀態
        this.toolbarEl.dataset.mode = this.selectMode ? 
            (hasSelection ? 'selection' : 'select') : 'normal';
        
        // 更新選中數量
        const countEl = this.toolbarEl.querySelector('.selection-count span');
        if (countEl) {
            countEl.textContent = count;
        }
        
        // 更新按鈕狀態
        const batchActions = this.toolbarEl.querySelectorAll('.batch-actions button');
        batchActions.forEach(btn => {
            btn.disabled = !hasSelection;
        });
    }
    
    /**
     * 獲取所有可選項目
     */
    getAllItems() {
        if (!this.itemsCache || this.itemsCache.length === 0) {
            this.itemsCache = Array.from(document.querySelectorAll(
                '.knowledge-card-compact, .knowledge-group-compact, .point-item-compact'
            ));
        }
        return this.itemsCache;
    }
    
    /**
     * 從元素獲取項目 ID
     */
    getItemId(element) {
        return element.dataset.itemId || 
               element.dataset.knowledgeId || 
               element.getAttribute('href')?.match(/\/knowledge\/(\d+)/)?.[1];
    }
    
    /**
     * 獲取元素的索引
     */
    getItemIndex(element) {
        const items = this.getAllItems();
        return items.indexOf(element);
    }
    
    /**
     * 綁定全局事件
     */
    bindGlobalEvents() {
        // 點擊事件委託
        document.addEventListener('click', (e) => {
            // 檢查是否點擊了可選項目
            const item = e.target.closest('[data-item-id], .knowledge-card-compact, .knowledge-group-compact');
            
            if (item && this.selectMode) {
                e.preventDefault();
                
                const id = this.getItemId(item);
                const index = this.getItemIndex(item);
                
                if (e.shiftKey && this.lastSelectedIndex >= 0) {
                    // 範圍選擇
                    this.selectRange(this.lastSelectedIndex, index);
                } else {
                    // 單選/取消選擇
                    this.toggleItem(id, index);
                }
            }
            
            // 檢查是否點擊了 checkbox
            if (e.target.classList.contains('selection-checkbox')) {
                e.stopPropagation();
                const item = e.target.closest('[data-item-id]');
                if (item) {
                    const id = this.getItemId(item);
                    this.toggleItem(id);
                }
            }
        });
        
        // 鍵盤快捷鍵
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'a':
                        if (this.selectMode) {
                            e.preventDefault();
                            this.selectAll();
                        }
                        break;
                    case 'd':
                        if (this.selectMode) {
                            e.preventDefault();
                            this.deselectAll();
                        }
                        break;
                    case 'i':
                        if (this.selectMode) {
                            e.preventDefault();
                            this.invertSelection();
                        }
                        break;
                }
            } else if (e.key === 'Escape' && this.selectMode) {
                e.preventDefault();
                this.toggleSelectMode();
            }
        });
    }
    
    /**
     * 初始化工具列
     */
    initToolbar() {
        // 工具列將在 HTML 中定義，這裡只綁定事件
        setTimeout(() => {
            const toolbar = document.querySelector('.batch-toolbar');
            if (toolbar) {
                this.toolbarEl = toolbar;
                
                // 綁定工具列按鈕事件
                const selectModeBtn = toolbar.querySelector('.btn-select-mode');
                if (selectModeBtn) {
                    selectModeBtn.addEventListener('click', () => this.toggleSelectMode());
                }
                
                const selectAllBtn = toolbar.querySelector('.btn-select-all');
                if (selectAllBtn) {
                    selectAllBtn.addEventListener('click', () => this.selectAll());
                }
                
                const invertBtn = toolbar.querySelector('.btn-invert');
                if (invertBtn) {
                    invertBtn.addEventListener('click', () => this.invertSelection());
                }
                
                const clearBtn = toolbar.querySelector('.btn-clear');
                if (clearBtn) {
                    clearBtn.addEventListener('click', () => this.deselectAll());
                }
            }
        }, 100);
    }
    
    /**
     * 註冊事件監聽器
     */
    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        }
    }
    
    /**
     * 移除事件監聽器
     */
    off(event, callback) {
        if (this.listeners[event]) {
            const index = this.listeners[event].indexOf(callback);
            if (index > -1) {
                this.listeners[event].splice(index, 1);
            }
        }
    }
    
    /**
     * 觸發事件
     */
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                callback(data);
            });
        }
    }
    
    /**
     * 保存會話狀態
     */
    saveSession() {
        if (this.selectMode && this.selectedItems.size > 0) {
            sessionStorage.setItem('selection_state', JSON.stringify({
                mode: this.selectMode,
                items: Array.from(this.selectedItems)
            }));
        } else {
            sessionStorage.removeItem('selection_state');
        }
    }
    
    /**
     * 恢復會話狀態
     */
    restoreSession() {
        const saved = sessionStorage.getItem('selection_state');
        if (saved) {
            try {
                const state = JSON.parse(saved);
                if (state.mode) {
                    this.selectMode = true;
                    state.items.forEach(id => this.selectedItems.add(id));
                    document.body.classList.add('select-mode');
                    
                    // 延遲更新 UI（等待 DOM 載入）
                    setTimeout(() => {
                        this.selectedItems.forEach(id => this.updateItemUI(id));
                        this.updateToolbar();
                    }, 100);
                }
            } catch (e) {
                console.error('[SelectionManager] 恢復會話狀態失敗:', e);
            }
        }
    }
    
    /**
     * 清理資源
     */
    destroy() {
        this.clearSelection();
        this.listeners = {};
        this.itemsCache = null;
        this.toolbarEl = null;
        sessionStorage.removeItem('selection_state');
    }
}

// 導出為全局變量
window.SelectionManager = SelectionManager;