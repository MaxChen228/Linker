# 🎯 命名規範統一改善計劃 v2.0

## 📋 現況分析總結

經過全面掃描，專案命名大致符合各語言慣例，但仍有少數不一致處需要調整。

### ✅ 已符合規範的部分
- **Python 文件**: 使用 snake_case ✓
- **Python 程式碼**: 類名 PascalCase、函數 snake_case ✓
- **JavaScript 程式碼**: 類名 PascalCase、函數 camelCase ✓
- **CSS 類名**: 大部分使用 kebab-case ✓
- **HTML 模板**: 使用 kebab-case ✓
- **路由**: 使用 kebab-case、資源用複數 ✓
- **data 屬性**: 使用 kebab-case ✓

### ❌ 需要改善的部分
1. **HTML 元素 ID**: 混用 camelCase 和 kebab-case
   - 問題例子: `id="patternSearch"` 應改為 `id="pattern-search"`
   
2. **Shell 腳本命名**: 不一致
   - `build-css.sh` (kebab-case) vs `start.py` (無連字號)
   
3. **文檔命名**: 大寫和 kebab-case 混用
   - `CHANGELOG.md` vs `DESIGN-SYSTEM-COMPLETE.md`

## 🎯 統一命名規則

### 1. 文件命名
| 類型 | 規則 | 範例 |
|-----|------|------|
| Python | snake_case | `ai_service.py` |
| JavaScript | kebab-case | `main.js` |
| CSS | kebab-case | `pattern-detail.css` |
| HTML | kebab-case | `knowledge-detail.html` |
| Shell 腳本 | kebab-case | `build-css.sh` |
| 文檔 (重要) | UPPERCASE | `README.md`, `LICENSE.md` |
| 文檔 (一般) | kebab-case | `quick-start.md` |

### 2. 程式碼命名
| 語言 | 類名 | 函數/方法 | 變數 | 常數 |
|------|------|-----------|------|------|
| Python | PascalCase | snake_case | snake_case | UPPER_SNAKE |
| JavaScript | PascalCase | camelCase | camelCase | UPPER_SNAKE |

### 3. Web 相關
| 項目 | 規則 | 範例 |
|-----|------|------|
| CSS 類名 | kebab-case | `.pattern-card` |
| HTML ID | kebab-case | `id="search-input"` |
| data 屬性 | kebab-case | `data-filter-type` |
| 路由 | kebab-case, 複數 | `/patterns`, `/knowledge` |

## 🔧 改善任務清單

### Phase 1: HTML ID 規範化 (15分鐘)
- [ ] 將 `id="patternSearch"` 改為 `id="pattern-search"`
- [ ] 將 `id="knowledgeSearch"` 改為 `id="knowledge-search"` 
- [ ] 將 `id="searchInput"` 改為 `id="search-input"`
- [ ] 將 `id="categoryTabs"` 改為 `id="category-tabs"`
- [ ] 將 `id="noResults"` 改為 `id="no-results"`
- [ ] 將 `id="totalCount"` 改為 `id="total-count"`
- [ ] 將 `id="visibleCount"` 改為 `id="visible-count"`
- [ ] 將 `id="copyToast"` 改為 `id="copy-toast"`
- [ ] 將 `id="submitBtn"` 改為 `id="submit-btn"`
- [ ] 將 `id="shuffleBtn"` 改為 `id="shuffle-btn"`
- [ ] 將 `id="practiceForm"` 改為 `id="practice-form"`
- [ ] 將 `id="loadingOverlay"` 改為 `id="loading-overlay"`
- [ ] 將 `id="loadingTitle"` 改為 `id="loading-title"`
- [ ] 將 `id="loadingMessage"` 改為 `id="loading-message"`
- [ ] 將 `id="modeInput"` 改為 `id="mode-input"`
- [ ] 將 `id="noKnowledgeResults"` 改為 `id="no-knowledge-results"`
- [ ] 更新 JavaScript 中所有對應的 getElementById 調用

### Phase 2: 檔案命名清理 (10分鐘)
- [ ] 統一 Shell 腳本命名為 kebab-case
- [ ] 統一一般文檔命名為 kebab-case
- [ ] 保留重要文檔的 UPPERCASE 命名

### Phase 3: 測試驗證 (20分鐘)
- [ ] 測試所有頁面功能是否正常
- [ ] 測試搜尋功能
- [ ] 測試篩選功能
- [ ] 測試表單提交
- [ ] 測試載入狀態

## 📊 影響評估

### 低風險改動
- HTML ID 改名（只需同步更新 JS）
- Shell 腳本重命名

### 中風險改動
- 無

### 高風險改動
- 無

## ⏱️ 預估時間
- **總計**: 45 分鐘
- **Phase 1**: 15 分鐘
- **Phase 2**: 10 分鐘
- **Phase 3**: 20 分鐘

## 🚀 執行步驟

### 1. 備份
```bash
git add -A
git commit -m "backup: 命名規範改善前備份"
```

### 2. 執行 Phase 1
```bash
# 批量替換 HTML ID
# 更新對應的 JavaScript
```

### 3. 執行 Phase 2
```bash
# 重命名檔案
mv start.py start-app.py  # 或其他合適名稱
```

### 4. 測試
```bash
python -m uvicorn web.main:app --reload --port 8000
# 手動測試所有功能
```

### 5. 提交
```bash
git add -A
git commit -m "refactor: 統一命名規範

- HTML ID 全部改為 kebab-case
- Shell 腳本統一使用 kebab-case
- 保持各語言的慣例命名規則"
```

## ✅ 驗收標準
1. 所有 HTML ID 使用 kebab-case
2. 所有 Shell 腳本使用 kebab-case  
3. JavaScript 能正確找到所有元素
4. 所有功能測試通過
5. 無控制台錯誤

## 📝 備註
- 大部分命名已經符合規範，只需做小幅調整
- 重點在 HTML ID 的統一
- 改動風險低，主要是搜尋替換工作