# TODO: 前端命名規範統一改善計劃

## 🎯 目標
統一整個前端的命名規範，解決命名混亂問題，提升程式碼可維護性。

## 📋 現況問題分析

### 主要問題
1. **分隔符不一致**
   - 底線：`pattern_detail.css`, `patterns_new.css`
   - 連字號：`knowledge-detail.css`

2. **單複數混亂**
   - 列表頁：`patterns.css` (複數) vs `knowledge.css` (單數)
   - 詳情頁：`pattern_detail.css` (單數正確)

3. **版本標記遺留**
   - 新版：`patterns_new.html`, `patterns_new.css`
   - 舊版：`patterns.html` (透過 `/patterns/old` 路由)
   - 歷史：`/patterns/v2` 重定向

4. **路由與文件不匹配**
   - `/patterns` → `patterns_new.html` (名稱不一致)
   - `/patterns/old` → `patterns.html` (版本混淆)

## 🚀 執行計劃

### Phase 1: 文件命名統一 ⏱️ 預計 2 小時

#### 1.1 備份現有文件
- [ ] 備份 `web/static/css/pages/` 目錄
- [ ] 備份 `web/templates/` 目錄
- [ ] 建立 git commit 點

#### 1.2 CSS 文件重命名
- [ ] `pattern_detail.css` → `pattern-detail.css`
- [ ] `patterns_new.css` → `patterns.css` (覆蓋舊版)
- [ ] 刪除未使用的舊 CSS 文件

#### 1.3 HTML 模板重命名
- [ ] `pattern_detail.html` → `pattern-detail.html`
- [ ] `patterns_new.html` → `patterns.html` (覆蓋舊版)
- [ ] `knowledge_detail.html` → `knowledge-detail.html`
- [ ] 刪除未使用的舊模板

#### 1.4 更新引用
- [ ] 更新 `base.html` 中的 CSS 引用
- [ ] 更新各模板中的 `{% block styles %}` 區塊
- [ ] 更新 `main.py` 中的模板路徑

### Phase 2: 路由整理 ⏱️ 預計 1 小時

#### 2.1 清理路由
- [ ] 移除 `/patterns/old` 路由
- [ ] 移除 `/patterns/v2` 重定向
- [ ] 移除 `/patterns/v2/{pattern_id}` 重定向

#### 2.2 更新路由對應
```python
# 統一的路由結構
/patterns           → patterns.html
/patterns/{id}      → pattern-detail.html
/knowledge          → knowledge.html
/knowledge/{id}     → knowledge-detail.html
/practice           → practice.html
```

#### 2.3 建立臨時重定向 (可選)
- [ ] 301 重定向從舊路由到新路由
- [ ] 設定 3 個月後移除重定向

### Phase 3: CSS 類名統一 ⏱️ 預計 3 小時

#### 3.1 制定命名規範
```css
/* 規範：使用連字號，BEM 風格 */
.page-container      /* 頁面容器 */
.page-header         /* 頁面標題區 */
.card-grid           /* 卡片網格 */
.card                /* 基礎卡片 */
.card__title         /* 卡片標題 */
.card__content       /* 卡片內容 */
.card--featured      /* 卡片修飾符 */
```

#### 3.2 更新 CSS 文件
- [ ] 統一 `patterns.css` 中的類名
- [ ] 統一 `pattern-detail.css` 中的類名
- [ ] 統一 `knowledge.css` 中的類名
- [ ] 統一 `knowledge-detail.css` 中的類名
- [ ] 統一 `practice.css` 中的類名

#### 3.3 更新 HTML 模板
- [ ] 更新所有模板中的 CSS 類名
- [ ] 確保與新的 CSS 類名對應

### Phase 4: JavaScript 更新 ⏱️ 預計 2 小時

#### 4.1 更新選擇器
- [ ] 更新 `main.js` 中的所有 querySelector
- [ ] 更新 `main.js` 中的所有 getElementById
- [ ] 更新 `main.js` 中的所有 getElementsByClassName

#### 4.2 更新數據屬性
- [ ] 統一 data-* 屬性命名
- [ ] 更新 JavaScript 中的 dataset 存取

#### 4.3 測試 JavaScript 功能
- [ ] 測試 PatternsManager 功能
- [ ] 測試 KnowledgeManager 功能
- [ ] 測試 PracticeSync 功能
- [ ] 測試 DraftManager 功能

### Phase 5: 測試與驗證 ⏱️ 預計 2 小時

#### 5.1 功能測試
- [ ] 首頁載入正常
- [ ] 文法句型列表頁正常
- [ ] 文法句型詳情頁正常
- [ ] 知識點列表頁正常
- [ ] 知識點詳情頁正常
- [ ] 練習頁面正常

#### 5.2 樣式測試
- [ ] 響應式設計正常
- [ ] 動畫效果正常
- [ ] 深色模式正常（如有）

#### 5.3 互動測試
- [ ] 搜尋功能正常
- [ ] 篩選功能正常
- [ ] 複製功能正常
- [ ] 自動儲存功能正常

### Phase 6: 文檔更新 ⏱️ 預計 1 小時

#### 6.1 更新開發文檔
- [ ] 更新 CLAUDE.md 中的文件結構說明
- [ ] 更新 PROJECT_HANDOVER.md 中的相關部分
- [ ] 建立命名規範文檔

#### 6.2 建立命名規範指南
- [ ] CSS 命名規範
- [ ] JavaScript 命名規範
- [ ] 文件命名規範
- [ ] 路由命名規範

## 📊 進度追蹤

| Phase | 狀態 | 預計時間 | 實際時間 | 負責人 | 完成日期 |
|-------|------|----------|----------|--------|----------|
| Phase 1 | ✅ 完成 | 2小時 | 0.5小時 | Claude | 2025-01-11 |
| Phase 2 | ✅ 完成 | 1小時 | 0.2小時 | Claude | 2025-01-11 |
| Phase 3 | ✅ 完成 | 3小時 | 0.1小時 | Claude | 2025-01-11 |
| Phase 4 | 待開始 | 2小時 | - | - | - |
| Phase 5 | 待開始 | 2小時 | - | - | - |
| Phase 6 | 待開始 | 1小時 | - | - | - |

**總預計時間**: 11 小時

## ⚠️ 風險與注意事項

### 風險項目
1. **快取問題**：用戶瀏覽器可能快取舊的 CSS/JS
   - 解決方案：加入版本號參數 `?v=1.0.1`

2. **書籤失效**：用戶保存的舊路由連結
   - 解決方案：保留 301 重定向 3-6 個月

3. **SEO 影響**：路由變更可能影響搜尋引擎索引
   - 解決方案：提交新的 sitemap，設定正確的重定向

### 回滾計劃
1. 保留所有備份文件至少 1 週
2. 記錄所有變更的 git commit
3. 準備快速回滾腳本

## 📝 命名規範總結

### 文件命名
- **規則**：使用連字號分隔 kebab-case
- **單複數**：列表頁用複數，詳情頁用單數
- **範例**：
  - `patterns.css` (列表頁)
  - `pattern-detail.css` (詳情頁)

### CSS 類名
- **規則**：使用連字號分隔，可選用 BEM
- **前綴**：頁面級用 page-，組件級用組件名
- **範例**：
  - `.patterns-page` (頁面容器)
  - `.pattern-card` (組件)
  - `.pattern-card__title` (子元素)

### JavaScript 變數
- **規則**：使用駝峰命名 camelCase
- **類名**：使用大駝峰 PascalCase
- **範例**：
  - `class PatternsManager`
  - `const patternCards`
  - `function updatePatternView()`

### 路由命名
- **規則**：使用斜線分隔，全小寫
- **單複數**：資源列表用複數
- **範例**：
  - `/patterns` (列表)
  - `/patterns/{id}` (詳情)

## ✅ 完成標準

1. 所有文件命名符合規範
2. 所有功能測試通過
3. 無控制台錯誤
4. 文檔已更新
5. 團隊成員已知悉變更

## 🔄 更新記錄

- 2024-12-11: 初始版本建立
- 2025-01-11: 完成 Phase 1-3
  - ✅ Phase 1: 文件命名統一（kebab-case）
  - ✅ Phase 2: 路由整理（移除舊路由）
  - ✅ Phase 3: CSS 類名檢查（已符合規範）

---

**注意**：執行前請確保已經備份所有相關文件，並在開發環境充分測試。