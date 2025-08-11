/**
 * 練習頁面標籤系統互動邏輯
 */

class TagPracticeSystem {
  constructor() {
    this.selectedTags = new Set();
    this.tagData = new Map();
    this.combinationMode = 'all';
    this.currentMode = 'single'; // 'single' or 'combo'
    this.init();
  }
  
  async init() {
    await this.loadTags();
    this.initEventListeners();
    this.renderInterface();
  }
  
  async loadTags() {
    try {
      const response = await fetch('/api/tags?type=grammar');
      const data = await response.json();
      
      if (data.success) {
        data.tags.forEach(tag => {
          this.tagData.set(tag.id, tag);
        });
        console.log(`Loaded ${this.tagData.size} tags`);
      }
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  }
  
  initEventListeners() {
    // 模式切換
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-tag-mode]')) {
        this.switchMode(e.target.dataset.tagMode);
      }
      
      // 快速練習按鈕
      if (e.target.matches('.tag-card-action')) {
        const tagId = e.target.closest('.tag-card').dataset.tagId;
        this.practiceWithSingleTag(tagId);
      }
      
      // 移除標籤
      if (e.target.matches('.remove-tag')) {
        const tagId = e.target.closest('.selected-tag').dataset.tagId;
        this.removeTag(tagId);
      }
    });
    
    // 組合邏輯選擇
    document.addEventListener('change', (e) => {
      if (e.target.name === 'combination-logic') {
        this.combinationMode = e.target.value;
        if (this.selectedTags.size > 0) {
          this.updatePreview();
        }
      }
    });
  }
  
  switchMode(mode) {
    this.currentMode = mode;
    this.selectedTags.clear();
    this.renderInterface();
    
    // 更新按鈕狀態
    document.querySelectorAll('[data-tag-mode]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tagMode === mode);
    });
  }
  
  renderInterface() {
    const container = document.getElementById('tag-selector-content');
    if (!container) return;
    
    if (this.currentMode === 'single') {
      this.renderSingleMode(container);
    } else {
      this.renderComboMode(container);
    }
  }
  
  renderSingleMode(container) {
    // 按類別分組標籤
    const categories = new Map();
    this.tagData.forEach(tag => {
      const category = tag.category || '其他';
      if (!categories.has(category)) {
        categories.set(category, []);
      }
      categories.get(category).push(tag);
    });
    
    // 渲染快速選擇卡片
    let html = '<div class="quick-tag-cards">';
    
    // 優先顯示常用標籤
    const popularTags = Array.from(this.tagData.values())
      .sort((a, b) => b.usage_count - a.usage_count)
      .slice(0, 9);
    
    popularTags.forEach(tag => {
      const successRate = Math.round(tag.success_rate * 100);
      html += `
        <div class="tag-card" data-tag-id="${tag.id}">
          <div class="tag-card-header">
            <span class="tag-icon">📌</span>
            <span class="tag-name">${tag.name}</span>
          </div>
          <div class="tag-card-body">
            <div class="tag-stats">
              <span class="stat-item">
                <span class="stat-label">掌握度</span>
                <div class="progress-bar">
                  <div class="progress-fill" style="width: ${successRate}%"></div>
                </div>
                <span class="stat-value">${successRate}%</span>
              </span>
              <span class="stat-item">
                <span class="stat-label">練習次數</span>
                <span class="stat-value">${tag.usage_count}</span>
              </span>
            </div>
            ${tag.description ? `
              <div class="tag-preview">
                ${tag.description.substring(0, 50)}...
              </div>
            ` : ''}
          </div>
          <button class="tag-card-action">立即練習</button>
        </div>
      `;
    });
    
    html += '</div>';
    container.innerHTML = html;
  }
  
  renderComboMode(container) {
    container.innerHTML = `
      <div class="tag-composer">
        <!-- 左側：標籤庫 -->
        <div class="tag-library">
          <div class="library-header">
            <input type="text" placeholder="搜尋標籤..." class="tag-search" id="tag-search">
            <div class="tag-filters">
              <button class="filter-btn active" data-filter="all">全部</button>
              <button class="filter-btn" data-filter="popular">熱門</button>
              <button class="filter-btn" data-filter="weak">弱項</button>
            </div>
          </div>
          <div class="tag-categories" id="tag-categories">
            ${this.renderTagCategories()}
          </div>
        </div>
        
        <!-- 中間：組合區域 -->
        <div class="composition-area">
          <div class="drop-zone" id="tag-drop-zone">
            <div class="drop-hint" id="drop-hint">
              點選標籤添加到組合中
            </div>
            <div class="selected-tags-container" id="selected-tags">
              <!-- 動態插入 -->
            </div>
          </div>
          
          <!-- 組合邏輯選擇 -->
          <div class="combination-logic">
            <label>組合方式：</label>
            <div class="logic-options">
              <label class="radio-option">
                <input type="radio" name="combination-logic" value="all" checked>
                <div>
                  <span>全部包含</span>
                  <span class="logic-hint">題目必須包含所有標籤</span>
                </div>
              </label>
              <label class="radio-option">
                <input type="radio" name="combination-logic" value="any">
                <div>
                  <span>任一包含</span>
                  <span class="logic-hint">題目包含至少一個標籤</span>
                </div>
              </label>
              <label class="radio-option">
                <input type="radio" name="combination-logic" value="focus">
                <div>
                  <span>重點練習</span>
                  <span class="logic-hint">主要練習第一個，其他為輔</span>
                </div>
              </label>
            </div>
          </div>
        </div>
        
        <!-- 右側：預覽面板 -->
        <div class="preview-panel">
          <div class="preview-header">題目預覽</div>
          <div class="preview-content" id="preview-content">
            <div class="preview-empty">選擇標籤後顯示預覽</div>
          </div>
          <div class="preview-stats">
            <div class="stat-row">
              <span>預計難度：</span>
              <div class="difficulty-meter">
                <div class="meter-fill" id="difficulty-meter" style="width: 0%"></div>
              </div>
            </div>
            <div class="stat-row">
              <span>題目變化性：</span>
              <span id="variety-score">-</span>
            </div>
          </div>
          <button class="start-practice-btn" id="start-practice-btn" disabled>
            開始練習
          </button>
        </div>
      </div>
    `;
    
    // 綁定標籤點擊事件
    this.bindComboModeEvents();
  }
  
  renderTagCategories() {
    // 按類別分組
    const categories = new Map();
    this.tagData.forEach(tag => {
      const category = tag.category || '其他';
      if (!categories.has(category)) {
        categories.set(category, []);
      }
      categories.get(category).push(tag);
    });
    
    let html = '';
    categories.forEach((tags, category) => {
      html += `
        <div class="category-section">
          <div class="category-header" onclick="tagSystem.toggleCategory(this)">
            <span class="toggle-icon">▼</span>
            <span class="category-name">${category}</span>
            <span class="category-count">${tags.length}</span>
          </div>
          <div class="category-tags">
            ${tags.map(tag => `
              <div class="draggable-tag" data-tag-id="${tag.id}" onclick="tagSystem.addTagToCombo('${tag.id}')">
                <span class="tag-text">${tag.name}</span>
                <span class="tag-indicator" style="opacity: ${tag.complexity / 5}"></span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    });
    
    return html;
  }
  
  bindComboModeEvents() {
    // 搜尋功能
    const searchInput = document.getElementById('tag-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.filterTags(e.target.value);
      });
    }
    
    // 篩選按鈕
    document.querySelectorAll('.tag-filters .filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.tag-filters .filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        this.applyFilter(e.target.dataset.filter);
      });
    });
    
    // 開始練習按鈕
    const startBtn = document.getElementById('start-practice-btn');
    if (startBtn) {
      startBtn.addEventListener('click', () => {
        this.startTaggedPractice();
      });
    }
  }
  
  toggleCategory(header) {
    header.classList.toggle('collapsed');
  }
  
  addTagToCombo(tagId) {
    if (this.selectedTags.has(tagId)) {
      return;
    }
    
    // 檢查標籤數量限制
    if (this.selectedTags.size >= 3) {
      alert('最多選擇3個標籤');
      return;
    }
    
    this.selectedTags.add(tagId);
    this.renderSelectedTags();
    this.validateCombination();
    this.updatePreview();
  }
  
  removeTag(tagId) {
    this.selectedTags.delete(tagId);
    this.renderSelectedTags();
    
    if (this.selectedTags.size > 0) {
      this.validateCombination();
      this.updatePreview();
    } else {
      this.clearPreview();
    }
  }
  
  renderSelectedTags() {
    const container = document.getElementById('selected-tags');
    if (!container) return;
    
    if (this.selectedTags.size === 0) {
      container.innerHTML = '';
      document.getElementById('drop-hint').style.display = 'block';
      document.getElementById('start-practice-btn').disabled = true;
      return;
    }
    
    document.getElementById('drop-hint').style.display = 'none';
    document.getElementById('start-practice-btn').disabled = false;
    
    let html = '';
    this.selectedTags.forEach(tagId => {
      const tag = this.tagData.get(tagId);
      if (tag) {
        html += `
          <div class="selected-tag" data-tag-id="${tagId}">
            <div class="tag-content">
              <span class="tag-type-icon">📝</span>
              <span class="tag-name">${tag.name}</span>
              <span class="tag-complexity">Lv.${tag.complexity}</span>
            </div>
            <button class="remove-tag">×</button>
          </div>
        `;
      }
    });
    
    container.innerHTML = html;
  }
  
  async validateCombination() {
    try {
      const response = await fetch('/api/validate-tag-combination', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tags: Array.from(this.selectedTags)
        })
      });
      
      const data = await response.json();
      if (data.success && data.validation) {
        this.showValidationResult(data.validation);
      }
    } catch (error) {
      console.error('Failed to validate combination:', error);
    }
  }
  
  showValidationResult(validation) {
    // 顯示警告
    if (validation.warnings && validation.warnings.length > 0) {
      const warningsHtml = validation.warnings.map(w => 
        `<div class="warning-item">⚠️ ${w}</div>`
      ).join('');
      
      // 在組合區域顯示警告
      let warningContainer = document.getElementById('combination-warnings');
      if (!warningContainer) {
        const dropZone = document.getElementById('tag-drop-zone');
        warningContainer = document.createElement('div');
        warningContainer.id = 'combination-warnings';
        warningContainer.className = 'combination-warnings';
        dropZone.parentNode.insertBefore(warningContainer, dropZone.nextSibling);
      }
      warningContainer.innerHTML = warningsHtml;
    } else {
      // 清除警告
      const warningContainer = document.getElementById('combination-warnings');
      if (warningContainer) {
        warningContainer.remove();
      }
    }
    
    // 顯示建議
    if (validation.suggestions && validation.suggestions.length > 0) {
      console.log('Suggestions:', validation.suggestions);
    }
  }
  
  async updatePreview() {
    const preview = document.getElementById('preview-content');
    if (!preview) return;
    
    if (this.selectedTags.size === 0) {
      this.clearPreview();
      return;
    }
    
    // 顯示載入狀態
    preview.innerHTML = '<div class="preview-loading">生成預覽中...</div>';
    
    try {
      const response = await fetch('/api/preview-tagged-question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tags: Array.from(this.selectedTags),
          mode: this.combinationMode
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // 顯示預覽
        preview.innerHTML = `
          <div class="preview-question">
            <div class="preview-label">範例題目：</div>
            <div class="preview-chinese">${data.chinese || '生成中...'}</div>
            <div class="preview-hint">
              <span class="hint-icon">💡</span>
              ${data.hint || '注意文法句型的使用'}
            </div>
            <div class="preview-tags">
              ${(data.covered_points || []).map(p => 
                `<span class="covered-point">${p}</span>`
              ).join('')}
            </div>
          </div>
        `;
        
        // 更新統計
        if (data.stats) {
          const difficultyMeter = document.getElementById('difficulty-meter');
          const varietyScore = document.getElementById('variety-score');
          
          if (difficultyMeter) {
            difficultyMeter.style.width = `${(data.stats.estimated_difficulty / 5) * 100}%`;
          }
          if (varietyScore) {
            varietyScore.textContent = `${data.stats.question_variety}%`;
          }
        }
      } else {
        preview.innerHTML = '<div class="preview-empty">預覽生成失敗，請重試</div>';
      }
    } catch (error) {
      console.error('Failed to update preview:', error);
      preview.innerHTML = '<div class="preview-empty">預覽生成失敗</div>';
    }
  }
  
  clearPreview() {
    const preview = document.getElementById('preview-content');
    if (preview) {
      preview.innerHTML = '<div class="preview-empty">選擇標籤後顯示預覽</div>';
    }
    
    const difficultyMeter = document.getElementById('difficulty-meter');
    if (difficultyMeter) {
      difficultyMeter.style.width = '0%';
    }
    
    const varietyScore = document.getElementById('variety-score');
    if (varietyScore) {
      varietyScore.textContent = '-';
    }
  }
  
  filterTags(query) {
    const tags = document.querySelectorAll('.draggable-tag');
    const lowerQuery = query.toLowerCase();
    
    tags.forEach(tag => {
      const tagText = tag.querySelector('.tag-text').textContent.toLowerCase();
      tag.style.display = tagText.includes(lowerQuery) ? '' : 'none';
    });
  }
  
  applyFilter(filter) {
    const tags = document.querySelectorAll('.draggable-tag');
    
    tags.forEach(tagEl => {
      const tagId = tagEl.dataset.tagId;
      const tag = this.tagData.get(tagId);
      
      let show = true;
      if (filter === 'popular') {
        show = tag.usage_count > 5;
      } else if (filter === 'weak') {
        show = tag.success_rate < 0.6;
      }
      
      tagEl.style.display = show ? '' : 'none';
    });
  }
  
  async practiceWithSingleTag(tagId) {
    // 設置單一標籤並開始練習
    this.selectedTags.clear();
    this.selectedTags.add(tagId);
    this.combinationMode = 'focus';
    
    await this.startTaggedPractice();
  }
  
  async startTaggedPractice() {
    if (this.selectedTags.size === 0) {
      alert('請至少選擇一個標籤');
      return;
    }
    
    // 將標籤信息存儲到 sessionStorage
    const practiceData = {
      tags: Array.from(this.selectedTags),
      mode: this.combinationMode,
      timestamp: Date.now()
    };
    
    sessionStorage.setItem('taggedPractice', JSON.stringify(practiceData));
    
    // 跳轉到練習頁面，使用 tagged 模式
    window.location.href = '/practice?mode=tagged';
  }
}

// 初始化標籤系統（如果在練習頁面且有標籤選擇器）
let tagSystem = null;

document.addEventListener('DOMContentLoaded', () => {
  const tagSelector = document.getElementById('tag-selector');
  if (tagSelector) {
    tagSystem = new TagPracticeSystem();
  }
  
  // 檢查是否從標籤選擇跳轉過來
  const taggedPracticeData = sessionStorage.getItem('taggedPractice');
  if (taggedPracticeData && window.location.pathname === '/practice') {
    const data = JSON.parse(taggedPracticeData);
    // 清除 sessionStorage
    sessionStorage.removeItem('taggedPractice');
    
    // 使用標籤數據生成題目
    if (window.generateTaggedQuestion) {
      window.generateTaggedQuestion(data.tags, data.mode);
    }
  }
});