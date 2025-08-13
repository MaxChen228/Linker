/**
 * Linker Web 前端互動增強
 * 功能：自動儲存草稿、統一日誌管理
 */

// 初始化日誌系統
const logger = window.getLogger ? window.getLogger('main') : {
  debug: (...args) => console.log(...args),
  info: (...args) => console.info(...args),
  log: (...args) => console.log(...args),
  warn: (...args) => console.warn(...args),
  warning: (...args) => console.warn(...args),
  error: (...args) => console.error(...args),
  logUserAction: (action, details) => console.log(`[USER] ${action}:`, details),
  logPerformance: (operation, duration) => console.log(`[PERF] ${operation}: ${duration}ms`)
};

/**
 * EventManager - 統一管理事件監聽器，防止記憶體洩漏
 */
class EventManager {
  constructor() {
    this.listeners = new Map();
    this.listenerIdCounter = 0;
  }

  /**
   * 添加可追蹤的事件監聽器
   * @param {Element} element - DOM 元素
   * @param {string} event - 事件類型
   * @param {Function} handler - 事件處理函數
   * @param {Object} options - 事件選項
   * @returns {number|null} 監聽器 ID
   */
  add(element, event, handler, options) {
    if (!element) return null;
    
    const id = ++this.listenerIdCounter;
    const wrappedHandler = (e) => handler(e);
    
    element.addEventListener(event, wrappedHandler, options);
    
    this.listeners.set(id, {
      element,
      event,
      handler: wrappedHandler,
      options
    });
    
    return id;
  }

  /**
   * 移除特定事件監聽器
   * @param {number} id - 監聽器 ID
   */
  remove(id) {
    const listener = this.listeners.get(id);
    if (listener) {
      listener.element.removeEventListener(
        listener.event,
        listener.handler,
        listener.options
      );
      this.listeners.delete(id);
    }
  }

  /**
   * 移除元素的所有事件監聽器
   * @param {Element} element - DOM 元素
   */
  removeAll(element) {
    for (const [id, listener] of this.listeners) {
      if (listener.element === element) {
        this.remove(id);
      }
    }
  }

  /**
   * 清理所有事件監聽器
   */
  cleanup() {
    for (const [id] of this.listeners) {
      this.remove(id);
    }
  }
}

// 全域事件管理器實例
const globalEventManager = new EventManager();

class DraftManager {
  constructor() {
    this.STORAGE_KEY = 'linker_practice_draft';
    this.AUTOSAVE_INTERVAL = 5000; // 5秒自動儲存
    this.autosaveTimer = null;
    this.lastSavedContent = '';
    this.isDraftRestored = false;
    this.eventIds = []; // 儲存所有事件監聽器 ID
  }

  /**
   * 初始化草稿管理器
   */
  init() {
    const englishInput = document.querySelector('textarea[name="english"]');
    if (!englishInput) return;

    // 檢查並恢復草稿
    this.checkAndRestoreDraft();

    // 設置自動儲存
    this.setupAutosave(englishInput);

    // 監聽表單提交，成功後清除草稿
    const form = englishInput.closest('form');
    if (form) {
      const id = globalEventManager.add(form, 'submit', () => {
        // 提交時先儲存最新內容（以防提交失敗）
        this.saveDraft(this.collectDraftData());
      });
      if (id) this.eventIds.push(id);
    }

    // 如果有批改結果顯示，說明提交成功，清除草稿
    const hasResult = Array.from(document.querySelectorAll('.card h2')).some(
      h2 => h2.textContent.includes('批改結果')
    );
    if (hasResult || document.querySelector('section.card')) {
      this.clearDraft();
    }
  }

  /**
   * 收集草稿資料
   */
  collectDraftData() {
    const chineseText = document.querySelector('textarea[name="chinese"]');
    const englishText = document.querySelector('textarea[name="english"]');
    const lengthSelect = document.querySelector('select[name="length"]');
    const levelSelect = document.querySelector('select[name="level"]');

    return {
      chinese: chineseText ? chineseText.value : '',
      english: englishText ? englishText.value : '',
      length: lengthSelect ? lengthSelect.value : 'short',
      level: levelSelect ? levelSelect.value : '1',
      timestamp: Date.now(),
      url: window.location.href
    };
  }

  /**
   * 儲存草稿到 LocalStorage
   */
  saveDraft(data) {
    try {
      // 只在有實際內容時儲存
      if (data.english && data.english.trim()) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
        this.lastSavedContent = data.english;
        this.showSaveIndicator('saved');
        logger.debug('草稿已儲存:', new Date().toLocaleTimeString());
      }
    } catch (e) {
      logger.error('儲存草稿失敗:', e);
      this.showSaveIndicator('error');
    }
  }

  /**
   * 從 LocalStorage 載入草稿
   */
  loadDraft() {
    try {
      const draftStr = localStorage.getItem(this.STORAGE_KEY);
      if (!draftStr) return null;

      const draft = JSON.parse(draftStr);
      
      // 檢查草稿是否過期（24小時）
      const isExpired = Date.now() - draft.timestamp > 24 * 60 * 60 * 1000;
      if (isExpired) {
        this.clearDraft();
        return null;
      }

      return draft;
    } catch (e) {
      logger.error('載入草稿失敗:', e);
      return null;
    }
  }

  /**
   * 檢查並恢復草稿
   */
  checkAndRestoreDraft() {
    const draft = this.loadDraft();
    if (!draft || !draft.english) return;

    const englishInput = document.querySelector('textarea[name="english"]');
    const chineseInput = document.querySelector('textarea[name="chinese"]');
    
    // 檢查是否為同一題（比較中文句子）
    const currentChinese = chineseInput ? chineseInput.value : '';
    const isSameQuestion = draft.chinese === currentChinese;

    if (isSameQuestion && englishInput && !englishInput.value) {
      // 顯示恢復提示
      this.showDraftNotification(draft, englishInput);
    }
  }

  /**
   * 顯示草稿恢復提示
   */
  showDraftNotification(draft, inputElement) {
    const notification = document.createElement('div');
    notification.className = 'draft-notification';
    notification.innerHTML = `
      <span>偵測到未完成的草稿（${this.getTimeAgo(draft.timestamp)}）</span>
      <button class="btn-restore">恢復</button>
      <button class="btn-discard">捨棄</button>
    `;

    // 插入到輸入框上方
    inputElement.parentElement.insertBefore(notification, inputElement);

    // 恢復按鈕
    notification.querySelector('.btn-restore').addEventListener('click', () => {
      inputElement.value = draft.english;
      this.isDraftRestored = true;
      notification.remove();
      this.showSaveIndicator('restored');
    });

    // 捨棄按鈕
    notification.querySelector('.btn-discard').addEventListener('click', () => {
      this.clearDraft();
      notification.remove();
    });

    // 10秒後自動隱藏
    setTimeout(() => {
      if (notification.parentElement) {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
      }
    }, 10000);
  }

  /**
   * 設置自動儲存
   */
  setupAutosave(inputElement) {
    const inputId = globalEventManager.add(inputElement, 'input', () => {
      // 清除之前的計時器
      clearTimeout(this.autosaveTimer);
      
      // 顯示儲存中狀態
      this.showSaveIndicator('saving');

      // 設置新的自動儲存計時器
      this.autosaveTimer = setTimeout(() => {
        const data = this.collectDraftData();
        
        // 只在內容有變化時儲存
        if (data.english !== this.lastSavedContent) {
          this.saveDraft(data);
        } else {
          this.showSaveIndicator('saved');
        }
      }, this.AUTOSAVE_INTERVAL);
    });
    if (inputId) this.eventIds.push(inputId);

    // 頁面關閉前儲存
    const beforeUnloadId = globalEventManager.add(window, 'beforeunload', () => {
      const data = this.collectDraftData();
      if (data.english && data.english !== this.lastSavedContent) {
        this.saveDraft(data);
      }
    });
    if (beforeUnloadId) this.eventIds.push(beforeUnloadId);
  }

  /**
   * 清理所有事件監聽器
   */
  destroy() {
    // 清理所有這個類別的事件監聽器
    this.eventIds.forEach(id => globalEventManager.remove(id));
    this.eventIds = [];
    
    // 清理計時器
    if (this.autosaveTimer) {
      clearTimeout(this.autosaveTimer);
    }
  }

  /**
   * 清除草稿
   */
  clearDraft() {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
      this.lastSavedContent = '';
      logger.debug('草稿已清除');
    } catch (e) {
      logger.error('清除草稿失敗:', e);
    }
  }

  /**
   * 顯示儲存狀態指示器
   */
  showSaveIndicator(status) {
    let indicator = document.querySelector('.save-indicator');
    
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.className = 'save-indicator';
      document.body.appendChild(indicator);
    }

    const messages = {
      saving: '儲存中...',
      saved: '已自動儲存',
      restored: '草稿已恢復',
      error: '儲存失敗'
    };

    indicator.textContent = messages[status] || '';
    indicator.className = `save-indicator ${status}`;
    
    // 顯示指示器
    indicator.style.opacity = '1';

    // 3秒後淡出（儲存中狀態除外）
    if (status !== 'saving') {
      setTimeout(() => {
        indicator.style.opacity = '0';
      }, 3000);
    }
  }

  /**
   * 計算時間差描述
   */
  getTimeAgo(timestamp) {
    const diff = Date.now() - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return '剛剛';
    if (minutes < 60) return `${minutes}分鐘前`;
    if (hours < 24) return `${hours}小時前`;
    return '超過一天前';
  }
}

/**
 * 練習頁面選項同步
 */
class PracticeSync {
  constructor() {
    this.lengthSelect = document.querySelector('select[name="length"]');
    this.levelSelect = document.querySelector('select[name="level"]');
    this.shuffleButton = document.getElementById('shuffle-btn');
    
    // 詳細調試信息
    logger.log('=== PracticeSync Debug ===');
    logger.log('Length select found:', !!this.lengthSelect, this.lengthSelect);
    logger.log('Level select found:', !!this.levelSelect, this.levelSelect);
    logger.log('Shuffle button found:', !!this.shuffleButton, this.shuffleButton);
    
    if (this.lengthSelect) {
      logger.log('Current length value:', this.lengthSelect.value);
    }
    if (this.levelSelect) {
      logger.log('Current level value:', this.levelSelect.value);
    }
    if (this.shuffleButton) {
      logger.log('Current button href:', this.shuffleButton.href);
    }
    
    if (this.lengthSelect && this.levelSelect) {
      this.init();
    } else {
      logger.error('❌ Required elements not found!');
    }
  }
  
  init() {
    // 從 URL 參數同步選項值
    this.syncFromURL();
    
    // 初始更新換一句按鈕
    this.updateShuffleButton();
    
    // 監聽選項變更 - 只更新按鈕，不自動跳轉
    this.lengthSelect.addEventListener('change', () => {
      this.updateShuffleButton();
      logger.log('Length changed to:', this.lengthSelect.value);
    });
    
    this.levelSelect.addEventListener('change', () => {
      this.updateShuffleButton();
      logger.log('Level changed to:', this.levelSelect.value);
    });
    
    // 攔截換一句按鈕點擊，確保使用最新的參數
    // 2024-12-10: 暫時禁用這個功能，因為在 practice.html 中已有更完善的實現
    // 這個代碼會覆蓋 practice.html 中的事件處理器，導致複習模式無法正常工作
    /*
    if (this.shuffleButton) {
      logger.log('✅ Setting up click handler for shuffle button');
      
      // 移除可能存在的舊事件監聽器
      const newButton = this.shuffleButton.cloneNode(true);
      this.shuffleButton.parentNode.replaceChild(newButton, this.shuffleButton);
      this.shuffleButton = newButton;
      
      this.shuffleButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        // 讀取當前選擇器的值，包括模式
        // 修正：使用正確的 ID 'mode-input' 而不是 'modeSelect'
        const modeInput = document.getElementById('mode-input');
        const urlParams = new URLSearchParams(window.location.search);
        const urlMode = urlParams.get('mode');
        const mode = urlMode || (modeInput ? modeInput.value : 'new');
        const length = this.lengthSelect.value;
        const level = this.levelSelect.value;
        const newUrl = `/practice?mode=${mode}&length=${length}&level=${level}&shuffle=1`;
        
        logger.log('🎲 Shuffle button clicked!');
        logger.log('Current mode select value:', mode);
        logger.log('Current length select value:', length);
        logger.log('Current level select value:', level);
        logger.log('Will navigate to:', newUrl);
        
        // 確保跳轉
        window.location.href = newUrl;
      });
      
      logger.log('✅ Click handler attached');
    } else {
      logger.error('❌ Shuffle button not found, cannot attach handler');
    }
    */
    logger.log('[PracticeSync] Skipping shuffle button handler - handled in practice.html');
  }
  
  syncFromURL() {
    const params = new URLSearchParams(window.location.search);
    const urlLength = params.get('length') || 'short';
    const urlLevel = params.get('level') || '1';
    
    // 設置選擇器的值
    this.lengthSelect.value = urlLength;
    this.levelSelect.value = urlLevel;
  }
  
  updateShuffleButton() {
    // 動態更新「換一句」按鈕的 href（作為備份）
    if (this.shuffleButton) {
      // 從 URL 獲取當前的 mode
      const urlParams = new URLSearchParams(window.location.search);
      const mode = urlParams.get('mode') || 'new';
      const length = this.lengthSelect.value;
      const level = this.levelSelect.value;
      // 重要：包含 mode 參數！
      const newHref = `/practice?mode=${mode}&length=${length}&level=${level}&shuffle=1`;
      this.shuffleButton.href = newHref;
      logger.log('📝 Updated button href');
      logger.log('  Mode:', mode);
      logger.log('  Length:', length);
      logger.log('  Level:', level);
      logger.log('  New href:', newHref);
    } else {
      logger.error('❌ Cannot update button - button not found');
    }
  }
}

/**
 * 文法句型頁面管理器
 */
class PatternsManager {
  constructor() {
    this.searchInput = document.getElementById('search-input');
    this.categoryTabs = document.querySelectorAll('.category-tab');
    this.patternCards = document.querySelectorAll('.pattern-card');
    this.noResults = document.getElementById('no-results');
    this.totalCount = document.getElementById('total-count');
    this.visibleCount = document.getElementById('visible-count');
    this.copyToast = document.getElementById('copy-toast');
    this.favorites = this.loadFavorites();
    
    this.currentCategory = '';
    this.searchQuery = '';
  }
  
  init() {
    // 初始化分類計數
    this.updateCategoryCounts();
    
    // 即時搜尋
    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.toLowerCase();
        this.filterPatterns();
      });
    }
    
    // 分類標籤切換
    this.categoryTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        this.categoryTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentCategory = tab.dataset.category;
        this.filterPatterns();
      });
    });
    
    // 複製功能
    document.querySelectorAll('[data-copy]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const text = btn.dataset.copy;
        this.copyToClipboard(text);
      });
    });
    
    // 收藏功能
    document.querySelectorAll('.btn-favorite').forEach(btn => {
      const card = btn.closest('.pattern-card');
      const pattern = card.querySelector('.pattern-title').textContent;
      
      // 檢查是否已收藏
      if (this.favorites.includes(pattern)) {
        btn.classList.add('active');
      }
      
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleFavorite(pattern, btn);
      });
    });
    
    // 展開/收合例句
    document.querySelectorAll('.btn-expand').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const examples = btn.closest('.pattern-examples');
        examples.classList.toggle('expanded');
        btn.classList.toggle('rotated');
      });
    });
    
    // 從 URL 恢復搜尋狀態
    const urlParams = new URLSearchParams(window.location.search);
    const urlQuery = urlParams.get('q');
    if (urlQuery && this.searchInput) {
      this.searchInput.value = urlQuery;
      this.searchQuery = urlQuery.toLowerCase();
      this.filterPatterns();
    }
  }
  
  updateCategoryCounts() {
    const categoryCounts = {};
    let totalCount = 0;
    
    this.patternCards.forEach(card => {
      const category = card.dataset.category || '';
      categoryCounts[category] = (categoryCounts[category] || 0) + 1;
      totalCount++;
    });
    
    // 更新全部計數
    const allCountEl = document.getElementById('count-all');
    if (allCountEl) allCountEl.textContent = totalCount;
    
    // 更新各分類計數
    Object.keys(categoryCounts).forEach(category => {
      if (category) {
        const countEl = document.getElementById(`count-${category}`);
        if (countEl) countEl.textContent = categoryCounts[category];
      }
    });
  }
  
  filterPatterns() {
    let visibleCount = 0;
    let hasResults = false;
    
    this.patternCards.forEach(card => {
      const category = card.dataset.category || '';
      const pattern = card.dataset.pattern || '';
      const explanation = card.dataset.explanation || '';
      const examples = card.dataset.examples || '';
      
      // 檢查分類篩選
      const categoryMatch = !this.currentCategory || category === this.currentCategory;
      
      // 檢查搜尋匹配
      const searchMatch = !this.searchQuery || 
        pattern.includes(this.searchQuery) ||
        explanation.includes(this.searchQuery) ||
        examples.includes(this.searchQuery);
      
      // 顯示或隱藏
      if (categoryMatch && searchMatch) {
        card.style.display = '';
        visibleCount++;
        hasResults = true;
      } else {
        card.style.display = 'none';
      }
    });
    
    // 更新統計
    if (this.visibleCount) {
      this.visibleCount.textContent = visibleCount;
    }
    
    // 顯示或隱藏無結果提示
    if (this.noResults) {
      this.noResults.style.display = hasResults ? 'none' : 'flex';
    }
    
    // 更新 URL（不重新載入頁面）
    const url = new URL(window.location);
    if (this.searchQuery) {
      url.searchParams.set('q', this.searchQuery);
    } else {
      url.searchParams.delete('q');
    }
    if (this.currentCategory) {
      url.searchParams.set('category', this.currentCategory);
    } else {
      url.searchParams.delete('category');
    }
    window.history.replaceState({}, '', url);
  }
  
  copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
      // 顯示成功提示
      if (this.copyToast) {
        this.copyToast.classList.add('show');
        setTimeout(() => {
          this.copyToast.classList.remove('show');
        }, 2000);
      }
    }).catch(err => {
      logger.error('複製失敗:', err);
    });
  }
  
  toggleFavorite(pattern, btn) {
    const index = this.favorites.indexOf(pattern);
    
    if (index === -1) {
      // 加入收藏
      this.favorites.push(pattern);
      btn.classList.add('active');
    } else {
      // 移除收藏
      this.favorites.splice(index, 1);
      btn.classList.remove('active');
    }
    
    // 儲存到 LocalStorage
    this.saveFavorites();
  }
  
  loadFavorites() {
    try {
      const saved = localStorage.getItem('linker_pattern_favorites');
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      return [];
    }
  }
  
  saveFavorites() {
    try {
      localStorage.setItem('linker_pattern_favorites', JSON.stringify(this.favorites));
    } catch (e) {
      logger.error('儲存收藏失敗:', e);
    }
  }
}

// 全域函數供 HTML 使用
function clearSearch() {
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input'));
  }
}

/**
 * 知識點管理器
 */
class KnowledgeManager {
  constructor() {
    this.searchInput = document.getElementById('knowledge-search');
    this.filterTabs = document.querySelectorAll('.filter-tab');
    // 改為同時選擇群組卡片和單一卡片
    this.knowledgeGroups = document.querySelectorAll('.knowledge-group-card');
    this.singleCards = document.querySelectorAll('.knowledge-single-card');
    this.noResults = document.getElementById('no-knowledge-results');
    
    this.currentCategory = '';
    this.currentMastery = '';
    this.searchQuery = '';
  }
  
  init() {
    // 統計各分類數量
    this.updateCategoryStats();
    
    // 即時搜尋
    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.toLowerCase();
        this.filterKnowledge();
      });
    }
    
    // 篩選標籤
    this.filterTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const filterType = tab.dataset.filterType;
        const filterValue = tab.dataset.filterValue;
        
        // 更新active狀態
        document.querySelectorAll(`.filter-tab[data-filter-type="${filterType}"]`).forEach(t => {
          t.classList.remove('active');
        });
        tab.classList.add('active');
        
        // 設置篩選條件
        if (filterType === 'category') {
          this.currentCategory = filterValue;
        } else if (filterType === 'mastery') {
          this.currentMastery = filterValue;
        }
        
        this.filterKnowledge();
      });
    });
    
    // 設置互動按鈕
    this.setupActionButtons();
  }
  
  updateCategoryStats() {
    // 統計計數由後端提供，這裡不需要重新計算
    // 如果需要動態更新，可以透過 data attributes 取得
    logger.log('Knowledge groups:', this.knowledgeGroups.length);
    logger.log('Single cards:', this.singleCards.length);
  }
  
  filterKnowledge() {
    let visibleGroups = 0;
    let visibleCards = 0;
    let hasResults = false;
    
    // 篩選知識群組（系統性錯誤）
    this.knowledgeGroups.forEach(group => {
      const groupName = group.dataset.groupName || '';
      
      // 搜尋匹配 - 檢查群組名稱或內部實例
      let searchMatch = !this.searchQuery || groupName.toLowerCase().includes(this.searchQuery);
      
      // 檢查群組內的實例
      if (!searchMatch) {
        const instances = group.querySelectorAll('.instance-card');
        searchMatch = Array.from(instances).some(instance => {
          const text = instance.textContent.toLowerCase();
          return text.includes(this.searchQuery);
        });
      }
      
      // 篩選條件
      const categoryMatch = !this.currentCategory || this.currentCategory === '系統性錯誤';
      const shouldShow = categoryMatch && searchMatch;
      
      // 顯示或隱藏整個群組
      const section = group.closest('.knowledge-section');
      if (shouldShow) {
        group.style.display = '';
        if (section) section.style.display = '';
        visibleGroups++;
        hasResults = true;
      } else {
        group.style.display = 'none';
      }
    });
    
    // 篩選單一知識卡片
    this.singleCards.forEach(card => {
      const category = card.dataset.category || '';
      const mastery = parseFloat(card.dataset.mastery || '0');
      const cardText = card.textContent.toLowerCase();
      
      // 分類篩選
      const categoryMatch = !this.currentCategory || category === this.currentCategory;
      
      // 掌握度篩選
      let masteryMatch = true;
      if (this.currentMastery === 'low') {
        masteryMatch = mastery < 0.3;
      } else if (this.currentMastery === 'medium') {
        masteryMatch = mastery >= 0.3 && mastery < 0.7;
      } else if (this.currentMastery === 'high') {
        masteryMatch = mastery >= 0.7;
      }
      
      // 搜尋匹配
      const searchMatch = !this.searchQuery || cardText.includes(this.searchQuery);
      
      // 顯示或隱藏
      const section = card.closest('.knowledge-section');
      if (categoryMatch && masteryMatch && searchMatch) {
        card.style.display = '';
        if (section) section.style.display = '';
        visibleCards++;
        hasResults = true;
      } else {
        card.style.display = 'none';
      }
    });
    
    // 隱藏空的區段
    document.querySelectorAll('.knowledge-section').forEach(section => {
      const visibleItems = section.querySelectorAll('.knowledge-group-card:not([style*="display: none"]), .knowledge-single-card:not([style*="display: none"])');
      if (visibleItems.length === 0 && !section.querySelector('.knowledge-groups')) {
        section.style.display = 'none';
      }
    });
    
    // 顯示或隱藏無結果提示
    if (this.noResults) {
      this.noResults.style.display = hasResults ? 'none' : 'flex';
    }
  }
  
  setupActionButtons() {
    // 群組展開/收合功能在模板中直接處理
    // 這裡可以添加其他互動功能
  }
}

/**
 * 載入管理器 - 處理所有載入狀態
 */
class LoadingManager {
  constructor() {
    this.overlay = document.getElementById('loading-overlay');
    this.title = document.getElementById('loading-title');
    this.message = document.getElementById('loading-message');
  }
  
  show(title = 'AI 正在處理中', message = '請稍候片刻...') {
    if (this.overlay) {
      if (this.title) this.title.textContent = title;
      if (this.message) this.message.textContent = message;
      this.overlay.classList.add('show');
    }
  }
  
  hide() {
    if (this.overlay) {
      this.overlay.classList.remove('show');
    }
  }
  
  showButtonLoading(button) {
    if (!button) return;
    button.classList.add('loading');
    button.disabled = true;
    
    // 保存原始文字
    const textElement = button.querySelector('.btn-text');
    if (textElement) {
      button.dataset.originalText = textElement.textContent;
    }
  }
  
  hideButtonLoading(button) {
    if (!button) return;
    button.classList.remove('loading');
    button.disabled = false;
    
    // 恢復原始文字
    const textElement = button.querySelector('.btn-text');
    if (textElement && button.dataset.originalText) {
      textElement.textContent = button.dataset.originalText;
    }
  }
}

/**
 * 頁面載入完成後初始化
 */
document.addEventListener('DOMContentLoaded', () => {
  // 初始化載入管理器
  const loadingManager = new LoadingManager();
  window.loadingManager = loadingManager;
  
  // 練習頁面功能 - 已移至 practice-logic.js
  // 舊的 DraftManager 和 PracticeSync 功能已經被新架構取代
  
  // 文法句型頁面功能
  if (window.location.pathname === '/patterns') {
    const patternsManager = new PatternsManager();
    patternsManager.init();
    
    // 掛載到全域
    window.patternsManager = patternsManager;
  }
  
  // 知識點頁面功能
  if (window.location.pathname === '/knowledge') {
    const knowledgeManager = new KnowledgeManager();
    knowledgeManager.init();
    
    // 掛載到全域
    window.knowledgeManager = knowledgeManager;
  }
  
  // 頁面載入完成時，確保隱藏載入畫面
  const loadId = globalEventManager.add(window, 'load', () => {
    setTimeout(() => {
      loadingManager.hide();
    }, 300);
  });
});

/**
 * 頁面卸載時清理所有事件監聽器
 */
window.addEventListener('unload', () => {
  // 清理全域事件管理器中的所有事件
  globalEventManager.cleanup();
  
  // 清理各個管理器實例
  if (window.draftManager && typeof window.draftManager.destroy === 'function') {
    window.draftManager.destroy();
  }
  if (window.practiceSync && typeof window.practiceSync.destroy === 'function') {
    window.practiceSync.destroy();
  }
  if (window.patternsManager && typeof window.patternsManager.destroy === 'function') {
    window.patternsManager.destroy();
  }
  if (window.knowledgeManager && typeof window.knowledgeManager.destroy === 'function') {
    window.knowledgeManager.destroy();
  }
  
  // 清理所有計時器
  const highestTimeoutId = setTimeout(() => {}, 0);
  for (let i = 0; i < highestTimeoutId; i++) {
    clearTimeout(i);
  }
});