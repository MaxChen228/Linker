# TASK-35-02: CSS架構統一 - 解決雙重樣式系統問題

- **Priority**: 🔴 CRITICAL
- **Estimated Time**: 8-12 hours
- **Related Components**: web/static/css/design-system/, web/static/css/components.css, web/templates/base.html
- **Parent Task**: TASK-35-main.md

---

### 🎯 Task Objective

解決當前同時存在兩套CSS系統（design-system 和 components.css）的問題，統一為單一、清晰的設計系統架構，消除樣式衝突和重複定義。

### ✅ Acceptance Criteria

- [ ] **單一樣式系統**: 消除 `design-system/index.css` 和 `components.css` 的並存
- [ ] **樣式遷移**: 將 `components.css` 中的有效樣式整合到設計系統
- [ ] **引用統一**: `base.html` 只引用一套CSS系統
- [ ] **重複清理**: 移除所有重複的CSS規則
- [ ] **命名統一**: 確保CSS類別命名符合設計系統規範
- [ ] **功能驗證**: 所有頁面樣式和功能正常
- [ ] **載入優化**: CSS載入請求減少，檔案大小合理
- [ ] **文檔更新**: 更新CLAUDE.md中的CSS架構說明

### 📋 當前問題分析

#### 問題1: 雙重引用造成衝突
```html
<!-- base.html 同時引入兩套系統 -->
<link rel="stylesheet" href="/static/css/design-system/index.css" />
<link rel="stylesheet" href="/static/css/components.css" />
```

#### 問題2: 重複樣式定義
```css
/* components.css 中的重複定義 */
.card { /* 與 design-system/03-components/cards.css 重複 */ }
.btn { /* 與 design-system/03-components/buttons.css 重複 */ }
```

#### 問題3: 文件組織混亂
```
web/static/css/
├── design-system/          # 新設計系統
├── pages/                  # 頁面專屬CSS
├── components/             # 舊組件CSS  
└── components.css          # 遺留組件文件 (問題)
```

### 📋 具體執行步驟

#### Step 1: 分析現有CSS架構 (2小時)

1. **盤點所有CSS文件**
   ```bash
   find web/static/css/ -name "*.css" | sort
   du -h web/static/css/**/*.css
   ```

2. **分析重複定義**
   ```bash
   # 尋找重複的class定義
   grep -r "\.card\s*{" web/static/css/
   grep -r "\.btn\s*{" web/static/css/
   grep -r "\.list\s*{" web/static/css/
   ```

3. **檢查樣式覆蓋情況**
   - 使用瀏覽器開發者工具檢查樣式來源
   - 記錄哪些樣式被覆蓋，哪些是有效的

#### Step 2: 設計新的統一架構 (2小時)

1. **確定保留的架構**
   ```
   web/static/css/
   ├── design-system/
   │   ├── index.css           # 主入口
   │   ├── 01-tokens/          # 設計令牌
   │   ├── 02-base/            # 基礎樣式
   │   ├── 03-components/      # 通用組件
   │   └── 04-layouts/         # 佈局系統
   ├── pages/                  # 頁面專屬樣式
   └── [移除 components.css]
   ```

2. **分類components.css中的樣式**
   - 通用組件 → 移到 `03-components/`
   - 實用工具類 → 移到 `03-components/utilities.css`
   - 頁面專屬 → 移到對應的 `pages/` 文件
   - 重複定義 → 刪除

#### Step 3: 樣式遷移和整合 (4-5小時)

1. **創建components.css內容清單**
   ```bash
   # 分析components.css的內容
   grep -n "^[^/].*{" web/static/css/components.css
   ```

2. **逐一遷移有效樣式**
   
   a. **Lists組件遷移**
   ```css
   /* 從components.css移到design-system/03-components/lists.css */
   .list { /* 移動到新位置 */ }
   .item { /* 移動到新位置 */ }
   ```
   
   b. **Error Styles遷移**
   ```css
   /* 移到design-system/03-components/error-displays.css */
   .error-header { /* 移動 */ }
   .examples { /* 移動 */ }
   ```
   
   c. **Utility Classes整理**
   ```css
   /* 整合到design-system/03-components/utilities.css */
   .muted { /* 檢查是否與現有衝突 */ }
   .gradient-text { /* 移動 */ }
   ```

3. **更新design-system/index.css引用**
   ```css
   /* 添加新組件的引用 */
   @import url('./03-components/lists.css');
   @import url('./03-components/error-displays.css');
   /* 其他新組件... */
   ```

#### Step 4: 清理和統一 (2小時)

1. **移除components.css**
   ```bash
   # 備份後刪除
   cp web/static/css/components.css web/static/css/components.css.backup
   rm web/static/css/components.css
   ```

2. **更新base.html引用**
   ```html
   <!-- 移除這行 -->
   <!-- <link rel="stylesheet" href="/static/css/components.css" /> -->
   
   <!-- 保留統一的設計系統引用 -->
   <link rel="stylesheet" href="/static/css/design-system/index.css" />
   ```

3. **檢查其他可能的引用**
   ```bash
   grep -r "components.css" web/templates/
   grep -r "components.css" web/static/
   ```

#### Step 5: 測試和驗證 (2小時)

1. **功能測試**
   - 瀏覽所有頁面確認樣式正常
   - 測試所有互動元素
   - 檢查響應式設計

2. **性能檢查**
   ```bash
   # 檢查CSS載入時間
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/
   
   # 檢查文件大小
   du -sh web/static/css/design-system/
   ```

3. **代碼品質檢查**
   ```bash
   ruff check .
   ruff format .
   ```

### 🎯 遷移對照表

| components.css 內容 | 目標位置 | 處理方式 |
|-------------------|----------|----------|
| `.list`, `.item` | `03-components/lists.css` | 新建文件 |
| `.error-header`, `.examples` | `03-components/error-displays.css` | 新建文件 |
| `.muted`, `.gradient-text` | `03-components/utilities.css` | 整合現有 |
| `.toast` | `03-components/notifications.css` | 檢查重複 |
| `.empty-state` | `03-components/empty-states.css` | 新建文件 |
| `.divider` | `03-components/dividers.css` | 新建文件 |
| 重複的 `.card`, `.btn` | 無 | 刪除 |

### ⚠️ 風險評估和緩解

**風險1: 樣式遺失或破損**
- 緩解: 逐一遷移，每步驟都測試
- 備份: 保留components.css.backup

**風險2: 樣式優先級改變**
- 緩解: 檢查CSS特異性，保持一致
- 測試: 使用瀏覽器開發者工具驗證

**風險3: 頁面載入問題**
- 緩解: 更新後立即測試所有頁面
- 監控: 檢查控制台錯誤

### 📊 預期成果

**架構清理前:**
- CSS系統: 2套並存
- 檔案數量: design-system/* + components.css + pages/*
- 重複定義: 多個組件重複
- 載入請求: 2個主要CSS檔案

**架構清理後:**
- CSS系統: 1套統一
- 檔案數量: design-system/* + pages/*
- 重複定義: 0個
- 載入請求: 1個主要CSS檔案

### 🔧 工具和命令

```bash
# CSS重複檢查
npx css-tree-shake --css web/static/css/ --html web/templates/

# 樣式覆蓋分析
npx specificity-graph web/static/css/**/*.css

# 載入性能測試
lighthouse http://localhost:8000 --only-categories=performance
```

### 📝 Execution Notes

**遷移清單:**
- [ ] Lists組件 (.list, .item)
- [ ] Error displays (.error-header, .examples)
- [ ] Utility classes (.muted, .gradient-text)
- [ ] Toast notifications (.toast)
- [ ] Empty states (.empty-state)
- [ ] Dividers (.divider)
- [ ] Focus states (.focus-ring)
- [ ] Accessibility helpers (.visually-hidden)

**測試檢查點:**
- [ ] 首頁樣式正常
- [ ] 練習頁面功能完整
- [ ] 文法句型頁面正常
- [ ] 知識點頁面正常
- [ ] 學習日曆正常
- [ ] 響應式設計正常

### 🔍 Review Comments (For Reviewer)

(審查者驗證CSS架構統一，無重複定義，所有頁面正常)