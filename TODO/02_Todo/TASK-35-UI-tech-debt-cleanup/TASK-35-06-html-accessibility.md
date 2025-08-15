# TASK-35-06: HTML可訪問性改善 - 語義化和ARIA支援

- **Priority**: 🟡 MEDIUM
- **Estimated Time**: 8-12 hours
- **Related Components**: web/templates/*.html, 全系統HTML模板
- **Parent Task**: TASK-35-main.md

---

### 🎯 Task Objective

全面改善HTML模板的可訪問性，實現語義化標記、完整的ARIA支援、鍵盤導航和螢幕閱讀器友好的用戶體驗，符合WCAG 2.1 AA級標準。

### ✅ Acceptance Criteria

- [ ] **語義化HTML**: 所有模板使用正確的語義化標籤
- [ ] **ARIA支援**: 完整的ARIA標籤和屬性系統
- [ ] **鍵盤導航**: 所有互動元素支援鍵盤操作
- [ ] **焦點管理**: 清晰的焦點指示和邏輯順序
- [ ] **螢幕閱讀器**: 與常見螢幕閱讀器兼容
- [ ] **色彩對比**: 符合WCAG對比度要求
- [ ] **表單可訪問性**: 完整的表單標籤和錯誤提示
- [ ] **WCAG合規**: 通過自動化可訪問性檢查工具

### 📊 當前問題分析

**發現的可訪問性問題:**

1. **語義化不足**
   ```html
   <!-- 問題: 使用div代替語義化標籤 -->
   <div class="queue-item add-new" role="button" tabindex="0">
   
   <!-- 改善: 使用正確的語義化標籤 -->
   <button type="button" class="queue-item add-new">
   ```

2. **內聯樣式問題**
   ```html
   <!-- 問題: 內聯樣式影響可訪問性 -->
   <span class="mastery-fill" style="--width: {{ item.mastery_level }}%"></span>
   
   <!-- 改善: 使用data屬性和CSS -->
   <span class="mastery-fill" data-progress="{{ item.mastery_level }}" 
         aria-label="掌握度 {{ item.mastery_level }}%"></span>
   ```

3. **缺少ARIA標籤**
   ```html
   <!-- 問題: 缺少ARIA描述 -->
   <div class="review-card">
   
   <!-- 改善: 添加適當的ARIA -->
   <article class="review-card" aria-labelledby="review-title-{{ item.id }}" 
            aria-describedby="review-desc-{{ item.id }}">
   ```

### 📋 具體執行步驟

#### Step 1: 可訪問性審查和評估 (2-3小時)

1. **使用自動化工具檢查**
   ```bash
   # 安裝可訪問性檢查工具
   npm install -g @axe-core/cli
   npm install -g pa11y
   
   # 檢查各頁面
   axe http://localhost:8000/ --reporter json > accessibility-audit.json
   pa11y http://localhost:8000/practice --reporter cli
   ```

2. **手動檢查清單**
   ```markdown
   - [ ] 鍵盤導航 (Tab, Enter, Space, Arrow keys)
   - [ ] 螢幕閱讀器測試 (NVDA, JAWS, VoiceOver)
   - [ ] 色彩對比檢查
   - [ ] 焦點可見性
   - [ ] 表單標籤關聯
   - [ ] 圖片alt屬性
   - [ ] 標題結構 (h1-h6)
   ```

3. **建立問題優先級清單**
   ```markdown
   | 問題類型 | 嚴重程度 | 影響範圍 | 修復優先級 |
   |---------|----------|----------|-----------|
   | 鍵盤無法操作 | 高 | 互動元素 | 高 |
   | 缺少alt屬性 | 中 | 圖片元素 | 高 |
   | ARIA標籤缺失 | 中 | 動態內容 | 中 |
   | 色彩對比不足 | 中 | 文字內容 | 中 |
   | 語義化不當 | 低 | 結構標籤 | 低 |
   ```

#### Step 2: 語義化HTML改善 (2-3小時)

1. **base.html結構優化**
   ```html
   <!-- 改善前 -->
   <div class="container">
     <h1 class="brand"><a href="/">Linker</a></h1>
     <div>
       <a href="/">首頁</a>
       <a href="/patterns">文法句型</a>
     </div>
   </div>
   
   <!-- 改善後 -->
   <header role="banner" class="container">
     <h1 class="brand">
       <a href="/" aria-label="Linker 首頁">Linker</a>
     </h1>
     <nav role="navigation" aria-label="主要導航">
       <ul>
         <li><a href="/" aria-current="{% if active=='home' %}page{% endif %}">首頁</a></li>
         <li><a href="/patterns" aria-current="{% if active=='patterns' %}page{% endif %}">文法句型</a></li>
         <!-- 其他導航項目 -->
       </ul>
     </nav>
   </header>
   ```

2. **index.html結構改善**
   ```html
   <!-- 統計卡片區域 -->
   <section aria-labelledby="stats-heading">
     <h2 id="stats-heading" class="visually-hidden">學習統計</h2>
     <div class="stats-grid" role="group">
       <div class="stat-card" data-variant="primary">
         <h3>總練習次數</h3>
         <p class="stat-value" aria-label="總練習次數：{{ stats.total_practices }} 次">
           {{ stats.total_practices }}
         </p>
       </div>
     </div>
   </section>
   
   <!-- 複習列表 -->
   <section aria-labelledby="review-heading">
     <h2 id="review-heading">待複習知識點</h2>
     <div class="review-grid" role="list">
       {% for item in review_items %}
       <article class="review-card" role="listitem"
                aria-labelledby="review-title-{{ item.id }}"
                aria-describedby="review-desc-{{ item.id }}">
         <h3 id="review-title-{{ item.id }}">{{ item.key_point }}</h3>
         <p id="review-desc-{{ item.id }}">
           {{ item.category }} - 掌握度 {{ item.mastery_level }}%
         </p>
       </article>
       {% endfor %}
     </div>
   </section>
   ```

3. **practice.html互動元素**
   ```html
   <!-- 佇列控制按鈕 -->
   <button type="button" class="btn queue-clear-btn" 
           aria-label="清空練習佇列"
           aria-describedby="queue-count">
     🗑️ 清空
   </button>
   
   <!-- 練習參數選擇 -->
   <div class="param-group" role="group" aria-labelledby="mode-label">
     <label id="mode-label" for="mode-select">練習模式</label>
     <select name="mode" id="mode-select" 
             aria-describedby="mode-help">
       <option value="new">新題目</option>
       <option value="review">複習題</option>
     </select>
     <div id="mode-help" class="param-help">
       選擇練習類型：新題目用於學習新內容，複習題用於鞏固已學知識
     </div>
   </div>
   ```

#### Step 3: ARIA標籤系統建立 (2-3小時)

1. **動態內容ARIA支援**
   ```html
   <!-- 載入狀態 -->
   <div class="loading-overlay" 
        role="status" 
        aria-live="polite"
        aria-label="正在載入內容">
     <div class="spinner" aria-hidden="true"></div>
     <span class="visually-hidden">AI 正在處理中，請稍候片刻</span>
   </div>
   
   <!-- 通知訊息 -->
   <div class="toast" 
        role="alert" 
        aria-live="assertive"
        aria-atomic="true">
     <span class="toast-message">操作成功完成</span>
   </div>
   ```

2. **表單可訪問性**
   ```html
   <!-- 翻譯練習表單 -->
   <form aria-labelledby="practice-form-title">
     <h2 id="practice-form-title">翻譯練習</h2>
     
     <div class="form-group">
       <label for="chinese-input">中文句子</label>
       <textarea id="chinese-input" 
                 name="chinese"
                 readonly
                 aria-describedby="chinese-help">
         {{ question.chinese }}
       </textarea>
       <div id="chinese-help" class="form-help">
         請將此中文句子翻譯成英文
       </div>
     </div>
     
     <div class="form-group">
       <label for="english-input">英文翻譯</label>
       <textarea id="english-input" 
                 name="english"
                 required
                 aria-describedby="english-help english-error"
                 aria-invalid="false">
       </textarea>
       <div id="english-help" class="form-help">
         請輸入您的英文翻譯
       </div>
       <div id="english-error" class="form-error" aria-live="polite">
         <!-- 錯誤訊息會動態插入 -->
       </div>
     </div>
   </form>
   ```

3. **導航和互動元素**
   ```html
   <!-- 知識點篩選 -->
   <div class="filter-tabs" role="tablist" aria-label="知識點篩選">
     <button type="button" 
             class="filter-tab" 
             role="tab"
             aria-selected="true"
             aria-controls="all-knowledge"
             id="tab-all">
       全部
     </button>
     <button type="button" 
             class="filter-tab" 
             role="tab"
             aria-selected="false"
             aria-controls="systematic-knowledge"
             id="tab-systematic">
       系統性錯誤
     </button>
   </div>
   
   <div class="knowledge-content">
     <div id="all-knowledge" 
          role="tabpanel" 
          aria-labelledby="tab-all">
       <!-- 全部知識點內容 -->
     </div>
   </div>
   ```

#### Step 4: 鍵盤導航和焦點管理 (2小時)

1. **鍵盤事件處理**
   ```javascript
   // 為自定義按鈕添加鍵盤支援
   document.querySelectorAll('[role="button"]').forEach(button => {
     button.addEventListener('keydown', (e) => {
       if (e.key === 'Enter' || e.key === ' ') {
         e.preventDefault();
         button.click();
       }
     });
   });
   
   // Tab鍵順序管理
   const focusableElements = document.querySelectorAll(
     'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
   );
   ```

2. **焦點指示改善**
   ```css
   /* 確保焦點可見性 */
   :focus {
     outline: 2px solid var(--focus-ring-color);
     outline-offset: 2px;
   }
   
   /* 高對比度模式支援 */
   @media (prefers-contrast: high) {
     :focus {
       outline: 3px solid HighlightText;
     }
   }
   
   /* 鍵盤用戶專用樣式 */
   .js-focus-visible :focus:not(.focus-visible) {
     outline: none;
   }
   ```

3. **模態框焦點管理**
   ```javascript
   class ModalAccessibility {
     constructor(modal) {
       this.modal = modal;
       this.previousActiveElement = null;
     }
     
     open() {
       this.previousActiveElement = document.activeElement;
       this.modal.setAttribute('aria-hidden', 'false');
       this.trapFocus();
       this.focusFirstElement();
     }
     
     close() {
       this.modal.setAttribute('aria-hidden', 'true');
       if (this.previousActiveElement) {
         this.previousActiveElement.focus();
       }
     }
   }
   ```

#### Step 5: 內容可訪問性優化 (1-2小時)

1. **移除內聯樣式**
   ```html
   <!-- 改善前 -->
   <span class="mastery-fill" style="--width: {{ item.mastery_level }}%"></span>
   
   <!-- 改善後 -->
   <div class="mastery-indicator" 
        aria-label="掌握度進度條">
     <div class="mastery-fill" 
          data-progress="{{ item.mastery_level }}"
          role="progressbar"
          aria-valuenow="{{ item.mastery_level }}"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label="掌握度 {{ item.mastery_level }}%">
     </div>
   </div>
   ```

2. **圖片和圖標可訪問性**
   ```html
   <!-- 裝飾性圖標 -->
   <svg aria-hidden="true" class="icon">
     <use href="#icon-close"></use>
   </svg>
   
   <!-- 有意義的圖標 -->
   <svg role="img" aria-label="成功" class="icon">
     <use href="#icon-check"></use>
   </svg>
   
   <!-- 複合圖標按鈕 -->
   <button type="button" aria-label="刪除項目">
     <svg aria-hidden="true">
       <use href="#icon-trash"></use>
     </svg>
     <span class="visually-hidden">刪除</span>
   </button>
   ```

3. **表格可訪問性**
   ```html
   <!-- 如果有數據表格 -->
   <table role="table" aria-label="練習記錄">
     <caption>最近的翻譯練習記錄</caption>
     <thead>
       <tr>
         <th scope="col">日期</th>
         <th scope="col">題目</th>
         <th scope="col">結果</th>
       </tr>
     </thead>
     <tbody>
       <tr>
         <td>{{ record.date }}</td>
         <td>{{ record.question }}</td>
         <td>
           <span class="badge" aria-label="練習結果：{{ record.result }}">
             {{ record.result }}
           </span>
         </td>
       </tr>
     </tbody>
   </table>
   ```

#### Step 6: 測試和驗證 (1-2小時)

1. **自動化測試**
   ```bash
   # 運行可訪問性測試
   axe http://localhost:8000/ --rules wcag2a,wcag2aa
   pa11y http://localhost:8000/practice --standard WCAG2AA
   
   # 檢查特定問題
   axe http://localhost:8000/ --tags keyboard-navigation
   ```

2. **手動測試清單**
   ```markdown
   ## 鍵盤導航測試
   - [ ] Tab鍵可以遍歷所有互動元素
   - [ ] Enter/Space鍵可以啟動按鈕
   - [ ] Arrow鍵在適當的地方工作 (導航菜單等)
   - [ ] Esc鍵可以關閉模態框
   - [ ] 焦點順序邏輯正確
   
   ## 螢幕閱讀器測試
   - [ ] 內容被正確讀出
   - [ ] 標題結構清晰
   - [ ] 表單標籤正確關聯
   - [ ] 動態內容變化被讀出
   - [ ] 圖片有適當的描述
   
   ## 色彩和對比度
   - [ ] 色彩對比度符合WCAG AA標準
   - [ ] 資訊不僅依賴顏色傳達
   - [ ] 高對比度模式正常顯示
   ```

3. **真實用戶測試**
   ```markdown
   ## 可訪問性用戶場景
   - 使用螢幕閱讀器完成一次翻譯練習
   - 僅使用鍵盤瀏覽知識點頁面
   - 在高對比度模式下使用文法句型功能
   - 使用語音控制軟體操作界面
   ```

### 🎯 可訪問性檢查清單

| 類別 | 檢查項目 | 狀態 |
|------|----------|------|
| **語義化** | 使用正確的HTML標籤 | ⭕ |
| **ARIA** | 適當的role屬性 | ⭕ |
| **鍵盤** | 所有功能可鍵盤操作 | ⭕ |
| **焦點** | 焦點指示清晰可見 | ⭕ |
| **表單** | 標籤正確關聯 | ⭕ |
| **圖片** | alt屬性完整 | ⭕ |
| **色彩** | 對比度符合標準 | ⭕ |
| **動態** | 內容變化可感知 | ⭕ |

### 📊 預期成果

**改善前:**
- WCAG合規性: 部分符合
- 螢幕閱讀器支援: 基礎
- 鍵盤導航: 不完整
- 語義化程度: 低

**改善後:**
- WCAG合規性: AA級標準
- 螢幕閱讀器支援: 完整
- 鍵盤導航: 全面支援
- 語義化程度: 高

### 🔧 工具和資源

```bash
# 可訪問性檢查工具
npm install -g @axe-core/cli pa11y lighthouse

# 瀏覽器擴展
# - axe DevTools
# - WAVE Web Accessibility Evaluator
# - Lighthouse

# 螢幕閱讀器
# - NVDA (Windows, 免費)
# - JAWS (Windows, 付費)
# - VoiceOver (macOS, 內建)
```

### 📝 Execution Notes

**改善進度:**
- [ ] 可訪問性審查完成
- [ ] base.html語義化完成
- [ ] 各頁面ARIA標籤完成
- [ ] 鍵盤導航測試通過
- [ ] 螢幕閱讀器測試通過
- [ ] 自動化檢查通過

**重點頁面:**
- [ ] 首頁 (/)
- [ ] 練習頁面 (/practice)
- [ ] 文法句型 (/patterns)
- [ ] 知識點 (/knowledge)
- [ ] 學習日曆 (/calendar)

### 🔍 Review Comments (For Reviewer)

(審查者確認可訪問性改善完整，WCAG合規性達標，用戶體驗良好)