# Linker UI 設計系統統一化專案

## 📊 當前狀態總覽

### 整體進度
- **Phase 1 - 基礎建設**: `██████████` 100% ✅ 完成
- **Phase 2 - 核心組件**: `██████████` 100% ✅ 完成  
- **Phase 3 - 頁面遷移**: `██████████` 100% ✅ 完成
- **Phase 4 - 優化清理**: `░░░░░░░░░░` 0% 待開始

### 已完成組件
| 組件 | 文件 | 測試頁面 | 狀態 |
|------|------|----------|------|
| 🎨 顏色系統 | `01-tokens/colors.css` | - | ✅ 完成 |
| 📐 間距系統 | `01-tokens/spacing.css` | - | ✅ 完成 |
| 🔤 字型系統 | `01-tokens/typography.css` | - | ✅ 完成 |
| ✨ 效果系統 | `01-tokens/effects.css` | - | ✅ 完成 |
| 🔘 按鈕系統 | `03-components/buttons.css` | `/test-buttons` | ✅ 完成 |
| 📋 卡片系統 | `03-components/cards.css` | `/test-cards` | ✅ 完成 |
| 🏷️ 徽章系統 | `03-components/badges.css` | `/test-badges` | ✅ 完成 |
| 📝 表單系統 | `03-components/forms.css` | `/test-forms` | ✅ 完成 |
| 🎬 動畫系統 | `01-tokens/animations.css` | - | ✅ 完成 |
| 🌑 陰影系統 | `01-tokens/shadows.css` | - | ✅ 完成 |
| ⏳ 載入狀態 | `03-components/loading.css` | `/test-loading` | ✅ 完成 |
| 🪟 模態框系統 | `03-components/modals.css` | `/test-modals` | ✅ 完成 |

---

## 🎯 立即行動項目

### 🔴 緊急（影響其他工作）
1. ~~**創建 animations.css**~~ - ✅ 已統一所有動畫定義
2. ~~**創建 shadows.css**~~ - ✅ 已優化性能問題
3. ~~**修復硬編碼顏色值**~~ - ✅ 已完成主要文件修復

### 🟡 重要（核心功能）
4. ~~**統一載入狀態組件**~~ - ✅ 已統一3處重複實現
5. ~~**統一模態框系統**~~ - ✅ 已完成所有模態框類型
6. **開始頁面遷移** - 應用新設計系統

### 🟢 優化（提升品質）
7. **清理舊代碼** - 減少技術債
8. **優化 Glass Morphism** - 解決性能問題
9. **添加深色模式支援** - 完善主題系統

---

## 📋 詳細任務清單

### Phase 1: 基礎建設 ✅ [100% 完成]
```
✅ animations.css - 統一動畫定義
  - 20+ 動畫定義完成
  - 支援 prefers-reduced-motion
  - 包含實用工具類
  
✅ shadows.css - 優化陰影系統  
  - 6個層級（xs, sm, md, lg, xl, 2xl）
  - 性能優化，移除複雜疊加
  - 深色模式支援
```

### Phase 2: 核心組件補完 ✅ [100% 完成]
```
✅ loading.css - 載入狀態組件
  - 5種 spinner 類型（簡單、雙環、多環、點狀）
  - 載入覆蓋層和模態框
  - 骨架屏系統
  - 進度條組件
  - 按鈕/表單/卡片載入狀態
  
✅ modals.css - 模態框系統
  - 基礎模態框（多種尺寸）
  - 確認對話框（成功/警告/錯誤）
  - 表單模態框
  - 調試資訊視窗
  - 媒體預覽模態框
  - Glass Morphism 效果
  - 響應式設計（移動端 sheet 樣式）
```

### Phase 3: 頁面遷移 ✅ [100% 完成]
```
✅ 首頁 (index.html)
  - 創建專屬樣式文件 index.css
  - 應用新統計卡片設計
  - 使用 Glass Morphism 效果
  - 實施響應式設計

✅ 練習頁 (practice.html)
  - 創建 practice-new.css 使用新設計系統
  - 統一表單元素和選擇器
  - 更新載入覆蓋層使用新組件
  - 優化題目卡片和答案輸入區

✅ 知識點頁 (knowledge.html)
  - 創建 knowledge-new.css 全面重構
  - 實施 Glass Morphism 統計卡片
  - 優化複習佇列區塊
  - 重新設計知識群組卡片

✅ 文法頁 (patterns.html)
  - 創建 patterns-new.css 全面重構
  - 優化分類標籤與統計欄
  - 重新設計句型卡片
  - 實施 Glass Morphism 效果
```

### Phase 4: 優化清理 [0% → 100%]
```
□ 移除舊樣式
  - 刪除 components.css 中的舊代碼
  - 清理 utilities.css 重複部分
  - 整合 base.css

□ 性能優化
  - 減少 backdrop-filter 使用
  - 優化動畫 will-change
  - 壓縮 CSS 檔案

□ 文檔更新
  - 組件使用指南
  - 設計系統文檔
  - 遷移指南
```

---

## 🔧 技術規範

### 設計令牌架構
```
design-system/
├── 01-tokens/        # 設計令牌
│   ├── colors.css    ✅
│   ├── spacing.css   ✅
│   ├── typography.css ✅
│   ├── effects.css   ✅
│   ├── animations.css ⏳
│   └── shadows.css   ⏳
├── 02-base/          # 基礎樣式
├── 03-components/    # 組件庫
│   ├── buttons.css   ✅
│   ├── cards.css     ✅
│   ├── badges.css    ✅
│   ├── forms.css     ✅
│   ├── loading.css   ⏳
│   └── modals.css    ⏳
└── 04-layouts/       # 佈局系統
```

### 組件 API 規範
```html
<!-- 使用 data 屬性控制變體 -->
<button class="btn" data-variant="primary" data-size="lg">
<div class="card" data-type="knowledge" data-interactive="true">
<span class="badge" data-variant="success" data-size="sm">

<!-- 保留舊類名以兼容 -->
<button class="btn mode-btn" data-variant="card"> <!-- 漸進式遷移 -->
```

### CSS 變數命名規範
```css
/* 顏色 */
--color-{semantic}     /* primary, success, error */
--{surface}-{variant}  /* surface-base, surface-elevated */
--text-{level}        /* text-primary, text-muted */

/* 間距 (8px 基準) */
--space-{n}           /* space-2 = 8px, space-4 = 16px */

/* 組件專用 */
--{component}-{property}-{variant}  /* btn-height-sm */
```

---

## 📈 品質指標

### 必須達成
- [x] 視覺一致性 - 所有組件使用統一設計語言
- [x] 向後兼容 - 保留關鍵舊類名
- [ ] 性能不降 - Lighthouse 分數 ≥ 85
- [ ] 無障礙支援 - WCAG 2.1 AA 級

### 目標指標
| 指標 | 現況 | 目標 | 進度 |
|------|------|------|------|
| CSS 檔案數 | 15 | 10 | 進行中 |
| 總代碼行數 | ~3500 | ~2000 | -40% |
| 組件數量 | 47 | 12 | -74% |
| 載入時間 | 基準 | -20% | 待測 |

---

## 🚨 關鍵問題追蹤

### 待解決問題
| # | 問題 | 影響 | 解決方案 | 負責人 | 狀態 |
|---|------|------|----------|--------|------|
| 1 | 動畫重複定義 | 維護困難 | 創建 animations.css | - | 🔴 待處理 |
| 2 | 硬編碼顏色值 | 主題切換困難 | 替換為 CSS 變數 | - | 🔴 待處理 |
| 3 | Glass Morphism 性能 | 渲染緩慢 | 簡化實現 | - | 🟡 進行中 |
| 4 | 載入狀態不一致 | 用戶體驗差 | 統一組件 | - | 🟡 待處理 |

### 已解決問題 ✅
- 按鈕系統碎片化 → 統一為單一系統
- 卡片樣式不一致 → 建立統一卡片系統
- 徽章命名混亂 → 統一徽章組件
- 表單元素分散 → 完整表單系統

---

## 📅 時間規劃

### 本週目標（Week 1）
- **週一-二**: 完成基礎建設（animations.css, shadows.css）
- **週三-四**: 完成核心組件（loading, modals）
- **週五**: 開始頁面遷移（首頁）

### 下週目標（Week 2）
- **週一-三**: 完成所有頁面遷移
- **週四**: 性能優化和測試
- **週五**: 文檔整理和交付

---

## 🛠️ 開發指引

### 快速開始
```bash
# 啟動開發伺服器
python -m uvicorn web.main:app --reload --port 8000

# 查看測試頁面
http://localhost:8000/test-buttons
http://localhost:8000/test-cards
http://localhost:8000/test-badges
http://localhost:8000/test-forms
```

### 新增組件流程
1. 在 `design-system/03-components/` 創建新文件
2. 使用現有設計令牌（不要硬編碼值）
3. 創建對應測試頁面
4. 更新 `design-system/index.css` 引入
5. 在 TODO.md 記錄進度

### Git 工作流程
```bash
# 功能分支
git checkout -b feature/ui-unified-[component]

# 提交規範
git commit -m "feat(ui): 統一[組件名]系統"
git commit -m "fix(ui): 修復[問題描述]"
git commit -m "docs(ui): 更新[文檔名稱]"
```

---

## 📝 參考資源

- [設計系統最佳實踐](https://www.designsystems.com/)
- [CSS 架構指南](https://cssguidelin.es/)
- [Web 性能優化](https://web.dev/performance/)
- [無障礙設計規範](https://www.w3.org/WAI/WCAG21/quickref/)

---

## ✅ 完成記錄

<details>
<summary>查看歷史完成項目</summary>

### 2024-12-XX 完成項目
- ✅ 建立設計令牌系統基礎
- ✅ 統一按鈕組件（9種 → 1個系統）
- ✅ 統一卡片組件（6種 → 1個系統）
- ✅ 統一徽章組件（6種 → 1個系統）
- ✅ 統一表單組件（新增）
- ✅ 創建動畫系統（animations.css）
- ✅ 創建陰影系統（shadows.css）
- ✅ 統一載入狀態組件（loading.css）
- ✅ 統一模態框系統（modals.css）
- ✅ 創建 Glass Morphism 令牌（glass.css）
- ✅ 修復硬編碼顏色值（components.css, utilities.css）
- ✅ 創建6個測試頁面
- ✅ 保持向後兼容性

</details>

---

**最後更新**: 2024-12-XX
**版本**: v2.0.0
**狀態**: 🚧 進行中