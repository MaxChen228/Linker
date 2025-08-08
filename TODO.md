# Linker UI 統一化完整計劃書

## 目錄
1. [執行摘要](#執行摘要)
2. [現狀分析與問題診斷](#一現狀分析與問題診斷)
3. [設計系統架構](#二設計系統架構)
4. [實施計劃](#三實施計劃)
5. [🎯 按鈕組件統一化專案](#按鈕組件統一化專案)
6. [性能優化策略](#四性能優化策略)
7. [測試計劃](#五測試計劃)
8. [風險管理](#六風險管理)
9. [預期成果](#七預期成果)
10. [維護指南](#八維護指南)
11. [時間線與里程碑](#九時間線與里程碑)
12. [成功標準](#十成功標準)

## 執行摘要
本計劃旨在統一 Linker 專案的 UI 組件系統，解決現有的設計不一致、性能問題和維護困難。通過建立統一的設計系統，預期能提升 40% 的性能，減少 50% 的 CSS 代碼量，並顯著改善開發效率。

## 一、現狀分析與問題診斷

### 1.1 技術債務清單

#### 🔴 嚴重問題
1. **設計令牌混亂**
   - 直接使用 hex 色值：`#ef4444`, `#10b981` 等散落各處
   - CSS 變數命名不一致：`--accent` vs `--primary`
   - 間距值隨意：`8px`, `12px`, `16px`, `20px`, `24px` 無規律

2. **組件碎片化**
   - 按鈕類：`.btn`, `.mode-btn`, `.toggle-btn`, `.filter-tab`, `.btn-action`, `.btn-restore`, `.btn-discard`
   - 卡片類：`.card`, `.knowledge-card`, `.question-card`, `.instance-card`, `.knowledge-group-card`, `.knowledge-single-card`
   - 徽章類：`.tag`, `.category-badge`, `.stat-badge`, `.mastery-badge`, `.error-category-badge`, `.subtype-badge`

3. **Glass Morphism 過度使用**
   ```css
   /* 現有的過度複雜實現 */
   background: 
     linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%),
     radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.05) 0%, transparent 50%),
     radial-gradient(circle at 80% 20%, rgba(79, 70, 229, 0.05) 0%, transparent 50%);
   ```

#### 🟡 中度問題
1. **重複代碼**
   - Loading 效果在 3 個文件中重複定義
   - 響應式斷點不一致：`768px` vs `640px`
   - 動畫定義重複：`spin`, `fadeIn`, `slideIn` 多處定義

2. **性能問題**
   - 未優化的動畫：`will-change` 濫用
   - 過多的 `backdrop-filter` 影響渲染
   - 複雜的 box-shadow 層疊

3. **可訪問性缺失**
   - 缺少 focus 狀態定義
   - 顏色對比度未檢查
   - 缺少 reduced-motion 支援

### 1.2 影響範圍統計
- **受影響文件**：15 個 CSS 文件，8 個 HTML 模板
- **代碼行數**：約 3,500 行 CSS（預計可減少至 1,800 行）
- **組件數量**：47 個獨立組件定義（可整合至 12 個）

## 二、設計系統架構

### 2.1 文件結構規劃
```
/web/static/css/
├── design-system/
│   ├── 01-tokens/
│   │   ├── colors.css         # 顏色令牌
│   │   ├── typography.css     # 字型系統
│   │   ├── spacing.css        # 間距系統
│   │   ├── shadows.css        # 陰影系統
│   │   └── animations.css     # 動畫系統
│   ├── 02-base/
│   │   ├── reset.css          # CSS Reset
│   │   ├── global.css         # 全局樣式
│   │   └── utilities.css      # 工具類
│   ├── 03-components/
│   │   ├── buttons.css        # 按鈕系統
│   │   ├── cards.css          # 卡片系統
│   │   ├── badges.css         # 徽章系統
│   │   ├── forms.css          # 表單系統
│   │   ├── modals.css         # 模態框系統
│   │   └── loading.css        # 載入狀態
│   └── 04-layouts/
│       ├── header.css         # 頭部導航
│       ├── container.css      # 容器系統
│       └── grid.css           # 網格系統
├── pages/                      # 頁面特定樣式（保留）
├── features/                   # 功能特定樣式（保留）
└── main.css                   # 統一入口

# 廢棄文件（將被移除）
├── base.css                   # → design-system/
├── components.css             # → design-system/
└── utilities.css              # → design-system/
```

### 2.2 設計令牌定義

#### 2.2.1 顏色系統
```css
:root {
  /* Brand Colors */
  --brand-50: #eef2ff;
  --brand-100: #e0e7ff;
  --brand-200: #c7d2fe;
  --brand-300: #a5b4fc;
  --brand-400: #818cf8;
  --brand-500: #6366f1;  /* Primary */
  --brand-600: #4f46e5;  /* Primary Dark */
  --brand-700: #4338ca;
  --brand-800: #3730a3;
  --brand-900: #312e81;
  
  /* Semantic Colors */
  --color-primary: var(--brand-600);
  --color-primary-hover: var(--brand-500);
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
  
  /* Surface Colors */
  --surface-base: #ffffff;
  --surface-elevated: #fafafa;
  --surface-overlay: rgba(255, 255, 255, 0.9);
  --surface-glass: rgba(255, 255, 255, 0.8);
  
  /* Text Colors */
  --text-primary: #1a1a1a;
  --text-secondary: #4b5563;
  --text-muted: #9ca3af;
  --text-disabled: #d1d5db;
  --text-inverse: #ffffff;
  
  /* Border Colors */
  --border-light: #f3f4f6;
  --border-default: #e5e7eb;
  --border-dark: #d1d5db;
  
  /* Dark Mode */
  @media (prefers-color-scheme: dark) {
    --surface-base: #18181b;
    --surface-elevated: #27272a;
    --surface-overlay: rgba(24, 24, 27, 0.9);
    --surface-glass: rgba(24, 24, 27, 0.8);
    --text-primary: #fafafa;
    --text-secondary: #a1a1aa;
    --text-muted: #71717a;
    --border-light: #27272a;
    --border-default: #3f3f46;
    --border-dark: #52525b;
  }
}
```

#### 2.2.2 間距系統（8px 基準）
```css
:root {
  --space-0: 0;
  --space-1: 4px;   /* 0.5 * 8 */
  --space-2: 8px;   /* 1 * 8 */
  --space-3: 12px;  /* 1.5 * 8 */
  --space-4: 16px;  /* 2 * 8 */
  --space-5: 20px;  /* 2.5 * 8 */
  --space-6: 24px;  /* 3 * 8 */
  --space-8: 32px;  /* 4 * 8 */
  --space-10: 40px; /* 5 * 8 */
  --space-12: 48px; /* 6 * 8 */
  --space-16: 64px; /* 8 * 8 */
  --space-20: 80px; /* 10 * 8 */
}
```

#### 2.2.3 字型系統
```css
:root {
  /* Font Families */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  --font-mono: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  
  /* Font Sizes */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  --text-4xl: 2.25rem;   /* 36px */
  
  /* Font Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  
  /* Line Heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
}
```

#### 2.2.4 圓角系統
```css
:root {
  --radius-none: 0;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 24px;
  --radius-full: 9999px;
}
```

#### 2.2.5 陰影系統（簡化版）
```css
:root {
  --shadow-xs: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-sm: 0 2px 4px 0 rgb(0 0 0 / 0.06);
  --shadow-md: 0 4px 8px 0 rgb(0 0 0 / 0.08);
  --shadow-lg: 0 8px 16px 0 rgb(0 0 0 / 0.10);
  --shadow-xl: 0 12px 24px 0 rgb(0 0 0 / 0.12);
  --shadow-2xl: 0 16px 32px 0 rgb(0 0 0 / 0.14);
  --shadow-inner: inset 0 2px 4px 0 rgb(0 0 0 / 0.06);
}
```

### 2.3 核心組件設計

#### 2.3.1 統一按鈕系統
```css
/* 基礎按鈕 */
.btn {
  /* 結構 */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  
  /* 尺寸 - 預設 medium */
  height: 40px;
  padding: 0 var(--space-5);
  
  /* 文字 */
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  line-height: 1;
  white-space: nowrap;
  
  /* 視覺 */
  border-radius: var(--radius-lg);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  
  /* 狀態 */
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  /* 變體 - 使用 data 屬性 */
  &[data-variant="primary"] {
    background: var(--color-primary);
    color: var(--text-inverse);
    &:hover:not(:disabled) {
      background: var(--color-primary-hover);
    }
  }
  
  &[data-variant="secondary"] {
    background: var(--surface-elevated);
    color: var(--text-primary);
    border-color: var(--border-default);
    &:hover:not(:disabled) {
      background: var(--surface-base);
      border-color: var(--border-dark);
    }
  }
  
  &[data-variant="ghost"] {
    background: transparent;
    color: var(--text-secondary);
    &:hover:not(:disabled) {
      background: var(--surface-elevated);
    }
  }
  
  /* 尺寸 */
  &[data-size="sm"] {
    height: 32px;
    padding: 0 var(--space-3);
    font-size: var(--text-xs);
  }
  
  &[data-size="lg"] {
    height: 48px;
    padding: 0 var(--space-8);
    font-size: var(--text-base);
  }
  
  /* 狀態 */
  &[data-loading="true"] {
    color: transparent;
    pointer-events: none;
    &::after {
      /* Loading spinner */
    }
  }
}
```

#### 2.3.2 統一卡片系統
```css
.card {
  /* 結構 */
  background: var(--surface-base);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  
  /* 陰影 */
  box-shadow: var(--shadow-sm);
  
  /* 變體 */
  &[data-interactive="true"] {
    cursor: pointer;
    transition: all 0.2s ease;
    &:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }
  }
  
  &[data-glass="true"] {
    background: var(--surface-glass);
    backdrop-filter: blur(10px);
    border-color: rgba(255, 255, 255, 0.2);
  }
  
  /* 內部結構 */
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--space-4);
  }
  
  .card-title {
    font-size: var(--text-lg);
    font-weight: var(--font-semibold);
    color: var(--text-primary);
  }
  
  .card-body {
    color: var(--text-secondary);
  }
  
  .card-footer {
    margin-top: var(--space-4);
    padding-top: var(--space-4);
    border-top: 1px solid var(--border-light);
  }
}
```

#### 2.3.3 統一徽章系統
```css
.badge {
  /* 結構 */
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  
  /* 尺寸 */
  height: 24px;
  padding: 0 var(--space-3);
  
  /* 文字 */
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  line-height: 1;
  
  /* 視覺 */
  border-radius: var(--radius-full);
  
  /* 變體 */
  &[data-variant="primary"] {
    background: var(--brand-100);
    color: var(--brand-700);
  }
  
  &[data-variant="success"] {
    background: #d1fae5;
    color: #065f46;
  }
  
  &[data-variant="warning"] {
    background: #fed7aa;
    color: #92400e;
  }
  
  &[data-variant="error"] {
    background: #fee2e2;
    color: #991b1b;
  }
  
  /* 尺寸 */
  &[data-size="sm"] {
    height: 20px;
    padding: 0 var(--space-2);
    font-size: 0.6875rem;
  }
  
  &[data-size="lg"] {
    height: 28px;
    padding: 0 var(--space-4);
    font-size: var(--text-sm);
  }
}
```

## 三、實施計劃

### 3.1 階段劃分

#### Phase 1: 基礎建設（第1-2天）
- [ ] 建立設計令牌文件
- [ ] 創建 CSS Reset
- [ ] 建立工具類
- [ ] 設置構建流程

#### Phase 2: 核心組件（第3-4天）
- [ ] 實現按鈕系統
- [ ] 實現卡片系統
- [ ] 實現徽章系統
- [ ] 實現表單系統
- [ ] 實現載入狀態

#### Phase 3: 頁面遷移（第5-7天）
- [ ] 遷移首頁
- [ ] 遷移練習頁面
- [ ] 遷移知識點頁面
- [ ] 遷移文法句型頁面

#### Phase 4: 優化清理（第8-9天）
- [ ] 移除舊代碼
- [ ] 性能優化
- [ ] 瀏覽器測試
- [ ] 響應式測試

#### Phase 5: 文檔交付（第10天）
- [ ] 組件文檔
- [ ] 使用指南
- [ ] 遷移記錄

### 3.2 具體任務分解

#### 3.2.1 設計令牌實施
```bash
# 文件創建順序
1. /css/design-system/01-tokens/colors.css
2. /css/design-system/01-tokens/typography.css
3. /css/design-system/01-tokens/spacing.css
4. /css/design-system/01-tokens/shadows.css
5. /css/design-system/01-tokens/animations.css
```

#### 3.2.2 組件遷移映射
| 舊類名 | 新類名 | 變更說明 |
|--------|--------|----------|
| `.btn`, `.btn.primary` | `.btn[data-variant="primary"]` | 統一按鈕，使用 data 屬性 |
| `.mode-btn` | `.btn[data-variant="secondary"]` | 合併為按鈕變體 |
| `.toggle-btn` | `.btn[data-variant="ghost"][data-size="sm"]` | 合併為按鈕變體 |
| `.filter-tab` | `.btn[data-variant="ghost"]` | 合併為按鈕變體 |
| `.card` | `.card` | 保留，但重構內部 |
| `.knowledge-card` | `.card[data-type="knowledge"]` | 使用 data 屬性區分 |
| `.tag` | `.badge` | 統一命名 |
| `.category-badge` | `.badge[data-variant]` | 使用變體系統 |

#### 3.2.3 顏色映射表
| 舊值 | 新變數 | 使用場景 |
|------|--------|----------|
| `#4f46e5` | `var(--color-primary)` | 主要操作 |
| `#6366f1` | `var(--color-primary-hover)` | 懸停狀態 |
| `#10b981` | `var(--color-success)` | 成功狀態 |
| `#f59e0b` | `var(--color-warning)` | 警告狀態 |
| `#ef4444` | `var(--color-error)` | 錯誤狀態 |
| `#6b7280` | `var(--text-muted)` | 次要文字 |

---

## 🎯 按鈕組件統一化專案

### 專案概述
按鈕是最常用的 UI 組件，目前存在 9 種不同實現，造成樣式不一致和維護困難。本專案將統一所有按鈕為單一系統。

### 現狀分析

#### 按鈕類型分布統計
| 類型 | CSS 類名 | 文件位置 | 使用頁面 | 實例數 |
|------|----------|----------|----------|--------|
| 主按鈕 | `.btn`, `.btn.primary` | components.css:339-444 | 練習、首頁 | 6 |
| 次要按鈕 | `.btn.outline` | components.css:386-396 | 首頁、練習 | 3 |
| 模式選擇 | `.mode-btn` | practice.css:33-69 | 練習頁 | 2 |
| 篩選標籤 | `.filter-tab` | knowledge.css:304-344 | 知識點頁 | 7 |
| 操作按鈕 | `.btn-action` | knowledge.css:585-604 | 知識點卡片 | 3/卡 |
| 切換按鈕 | `.toggle-btn` | knowledge.css:89-108 | 知識點展開 | 多個 |
| 圖標按鈕 | `.btn-icon` | patterns.css:181-208 | 文法頁 | 多個 |
| 草稿按鈕 | `.btn-restore`, `.btn-discard` | utilities.css:54-83 | 草稿恢復 | 2 |
| 調試按鈕 | `.close-btn`, `.copy-btn` | llm-debug.css:45-180 | 調試模態 | 3 |

#### 問題點
1. **樣式定義分散**：6 個不同 CSS 文件
2. **命名不一致**：9 種命名模式
3. **重複代碼**：相似樣式重複定義
4. **難以維護**：修改需要多處更新

### 統一化設計方案

#### 新按鈕系統架構
```
.btn[data-variant][data-size][data-state]
```

#### 映射方案
| 舊類名 | 新實現 | 說明 |
|--------|--------|------|
| `.btn.primary.large` | `.btn[data-variant="primary"][data-size="lg"]` | 主要操作 |
| `.btn.outline` | `.btn[data-variant="secondary"]` | 次要操作 |
| `.mode-btn` | `.btn[data-variant="card"]` | 卡片式選擇 |
| `.filter-tab` | `.btn[data-variant="tab"]` | 標籤切換 |
| `.btn-action` | `.btn[data-variant="ghost"][data-size="sm"]` | 輕量操作 |
| `.toggle-btn` | `.btn[data-variant="primary"][data-size="sm"]` | 小號切換 |
| `.btn-icon` | `.btn[data-variant="icon"]` | 純圖標 |
| `.btn-restore` | `.btn[data-variant="success"][data-size="sm"]` | 確認操作 |
| `.btn-discard` | `.btn[data-variant="ghost"][data-size="sm"]` | 取消操作 |

### 實施步驟

#### Phase 1: 建立新系統（第1天）
- [ ] 創建設計令牌文件 `01-tokens/colors.css`
- [ ] 創建按鈕組件文件 `03-components/buttons.css`
- [ ] 定義所有變體和狀態
- [ ] 加入 base.html

#### Phase 2: 漸進式遷移（第2-3天）

##### 2.1 練習頁面 (practice.html)
- [ ] 模式選擇按鈕 (2個)
- [ ] 出題按鈕「開始出題/換一句」
- [ ] 提交按鈕「提交答案」
- [ ] 調試按鈕「🔍」

##### 2.2 知識點頁面 (knowledge.html)  
- [ ] 篩選標籤 (7個)
- [ ] 卡片操作按鈕 (複習/已掌握/刪除)
- [ ] 展開/收合按鈕

##### 2.3 其他頁面
- [ ] 首頁按鈕 (開始練習/瀏覽文法)
- [ ] 文法頁圖標按鈕
- [ ] 調試模態框按鈕

#### Phase 3: 測試驗證（第4天）
- [ ] 視覺一致性測試
- [ ] 功能完整性測試
- [ ] 響應式測試
- [ ] 性能測試

#### Phase 4: 清理優化（第5天）
- [ ] 移除舊按鈕樣式
- [ ] 合併重複代碼
- [ ] 更新文檔

### 技術規格

#### 設計令牌
```css
:root {
  /* 按鈕專用令牌 */
  --btn-height-sm: 32px;
  --btn-height-md: 40px;
  --btn-height-lg: 48px;
  --btn-padding-sm: 0 16px;
  --btn-padding-md: 0 20px;
  --btn-padding-lg: 0 32px;
  --btn-font-sm: 12px;
  --btn-font-md: 14px;
  --btn-font-lg: 16px;
  --btn-radius: 12px;
  --btn-radius-full: 9999px;
}
```

#### 核心樣式結構
```css
.btn {
  /* 基礎樣式 */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  
  /* 預設尺寸 */
  height: var(--btn-height-md);
  padding: var(--btn-padding-md);
  font-size: var(--btn-font-md);
  
  /* 通用屬性 */
  font-weight: 500;
  border-radius: var(--btn-radius);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}
```

### 測試清單

#### 視覺測試
- [ ] 所有按鈕高度一致
- [ ] 顏色符合設計規範
- [ ] hover 效果正確
- [ ] active 狀態正確
- [ ] disabled 狀態顯示
- [ ] loading 狀態動畫

#### 功能測試  
- [ ] 點擊事件正常觸發
- [ ] 表單提交功能正常
- [ ] 模式切換功能正常
- [ ] 篩選功能正常運作

#### 相容性測試
- [ ] Chrome 90+
- [ ] Firefox 88+
- [ ] Safari 14+
- [ ] 移動端顯示正常

### 預期成果

#### 量化指標
- **CSS 減少**：按鈕相關代碼從 ~500 行減至 ~200 行（-60%）
- **文件整合**：從 6 個文件整合至 1 個
- **組件數量**：從 9 種按鈕減至 1 個統一系統
- **維護時間**：預計減少 70% 維護時間

#### 質量提升
- ✅ 視覺一致性
- ✅ 代碼可維護性
- ✅ 擴展靈活性
- ✅ 性能優化

### 風險與緩解

| 風險 | 可能性 | 影響 | 緩解策略 |
|------|--------|------|----------|
| JS 事件綁定失效 | 中 | 高 | 保留關鍵 class 作為選擇器 |
| 樣式覆蓋問題 | 低 | 中 | 使用更具體的選擇器 |
| 瀏覽器兼容 | 低 | 低 | 提供 CSS 回退方案 |

### 時間表
- **Day 1**: 建立新系統（4小時）
- **Day 2**: 遷移核心頁面（6小時）
- **Day 3**: 遷移其他頁面（4小時）
- **Day 4**: 測試與修復（4小時）
- **Day 5**: 優化與文檔（2小時）

**總計**: 20小時

---

### 3.3 遷移策略

#### 3.3.1 漸進式遷移
```html
<!-- 第一階段：雙類名 -->
<button class="btn mode-btn" data-variant="primary">
  開始練習
</button>

<!-- 第二階段：移除舊類名 -->
<button class="btn" data-variant="primary">
  開始練習
</button>
```

#### 3.3.2 CSS 變數回退
```css
.btn {
  /* 提供回退值 */
  background: var(--color-primary, #4f46e5);
  color: var(--text-inverse, #ffffff);
}
```

#### 3.3.3 瀏覽器兼容性
```css
/* 漸進增強 */
.card {
  background: rgba(255, 255, 255, 0.9); /* 回退 */
  
  @supports (backdrop-filter: blur(10px)) {
    background: var(--surface-glass);
    backdrop-filter: blur(10px);
  }
}
```

## 四、性能優化策略

### 4.1 CSS 優化
1. **移除未使用的樣式**：使用 PurgeCSS
2. **合併重複規則**：使用 CSS Nano
3. **優化選擇器**：避免深層嵌套
4. **減少重繪重排**：使用 transform 代替 position

### 4.2 動畫優化
```css
/* 優化前 */
.card:hover {
  top: -4px; /* 觸發重排 */
}

/* 優化後 */
.card:hover {
  transform: translateY(-4px); /* 使用 GPU 加速 */
}
```

### 4.3 載入優化
```html
<!-- Critical CSS 內聯 -->
<style>
  /* 關鍵樣式內聯 */
  :root { /* tokens */ }
  .btn { /* 核心組件 */ }
</style>

<!-- 非關鍵樣式異步載入 -->
<link rel="preload" href="/css/main.css" as="style">
<link rel="stylesheet" href="/css/main.css" media="print" onload="this.media='all'">
```

## 五、測試計劃

### 5.1 視覺回歸測試
- [ ] 截圖對比測試
- [ ] 顏色對比度檢查
- [ ] 字體渲染測試
- [ ] 響應式斷點測試

### 5.2 性能測試
- [ ] Lighthouse 分數
- [ ] First Contentful Paint
- [ ] Cumulative Layout Shift
- [ ] CSS 文件大小

### 5.3 兼容性測試
- [ ] Chrome 90+
- [ ] Firefox 88+
- [ ] Safari 14+
- [ ] Edge 90+
- [ ] Mobile Safari
- [ ] Chrome Mobile

### 5.4 可訪問性測試
- [ ] 鍵盤導航
- [ ] 屏幕閱讀器
- [ ] 顏色對比度
- [ ] Focus 狀態
- [ ] ARIA 標籤

## 六、風險管理

### 6.1 風險識別
| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|----------|
| 樣式衝突 | 高 | 中 | 漸進式遷移，充分測試 |
| 性能下降 | 低 | 高 | 性能監控，及時回滾 |
| 瀏覽器兼容 | 中 | 中 | 提供 CSS 回退方案 |
| 用戶體驗中斷 | 低 | 高 | A/B 測試，分階段發布 |

### 6.2 回滾計劃
```bash
# 版本標記
git tag -a v1.0-pre-ui-refactor -m "Before UI refactor"

# 如需回滾
git revert --no-edit HEAD~5..HEAD
```

## 七、預期成果

### 7.1 量化指標
- **CSS 文件大小**：3.5KB → 1.8KB（-48%）
- **組件數量**：47 → 12（-74%）
- **顏色定義**：32 → 16（-50%）
- **載入時間**：改善 20-30%
- **維護時間**：減少 60%

### 7.2 質量提升
- ✅ 一致的視覺語言
- ✅ 更好的可維護性
- ✅ 提升開發效率
- ✅ 改善用戶體驗
- ✅ 增強可訪問性

## 八、維護指南

### 8.1 命名規範
```css
/* 組件命名 */
.component-name {}
.component-name__element {}
.component-name--modifier {}

/* 數據屬性 */
[data-variant="primary"] {}
[data-size="lg"] {}
[data-state="active"] {}
```

### 8.2 新增組件流程
1. 在 design-system/03-components/ 創建新文件
2. 使用現有設計令牌
3. 遵循既定模式
4. 添加文檔說明
5. 更新組件索引

### 8.3 調試技巧
```css
/* 開發模式標記 */
[data-debug="true"] {
  outline: 2px solid red !important;
}

/* 性能監控 */
.performance-monitor {
  will-change: auto !important;
  animation: none !important;
}
```

## 九、時間線與里程碑

### Week 1 (Days 1-5)
- **Day 1-2**: 設計系統基礎建設
- **Day 3-4**: 核心組件實現
- **Day 5**: 首頁遷移

### Week 2 (Days 6-10)
- **Day 6-7**: 核心頁面遷移
- **Day 8**: 性能優化
- **Day 9**: 測試與修復
- **Day 10**: 文檔完成

## 十、成功標準

### 10.1 必須達成
- [ ] 所有頁面正常顯示
- [ ] 無明顯視覺差異
- [ ] 性能不低於現有水平
- [ ] 通過所有測試

### 10.2 期望達成
- [ ] CSS 減少 40%
- [ ] 載入速度提升 20%
- [ ] Lighthouse 分數 > 90
- [ ] 零無障礙錯誤

### 10.3 超越目標
- [ ] 建立組件庫文檔站
- [ ] 實現暗色模式
- [ ] 添加動畫偏好設置
- [ ] 國際化支援

## 十一、相關人員與職責

### 11.1 執行團隊
- **前端開發**：負責實施和測試
- **UI/UX 設計**：確保設計一致性
- **QA 測試**：執行測試計劃
- **產品經理**：驗收和協調

### 11.2 溝通計劃
- 每日站會：同步進度
- 週會檢視：展示成果
- 問題追蹤：使用 GitHub Issues
- 文檔更新：即時同步

## 十二、附錄

### A. 參考資源
- [Design Tokens W3C](https://www.w3.org/community/design-tokens/)
- [CSS Architecture](https://philipwalton.com/articles/css-architecture/)
- [BEM Methodology](http://getbem.com/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### B. 工具清單
- **CSS 處理**：PostCSS, Autoprefixer
- **優化工具**：PurgeCSS, CSS Nano
- **測試工具**：Percy, Chromatic
- **性能監控**：Lighthouse CI

### C. 代碼範例
```html
<!-- 新組件使用範例 -->
<div class="card" data-interactive="true" data-glass="true">
  <div class="card-header">
    <h3 class="card-title">知識點標題</h3>
    <span class="badge" data-variant="success">已掌握</span>
  </div>
  <div class="card-body">
    <p>知識點內容...</p>
  </div>
  <div class="card-footer">
    <button class="btn" data-variant="primary" data-size="sm">
      複習
    </button>
  </div>
</div>
```

---

## 執行檢查清單

### 開始前確認
- [ ] 備份現有代碼
- [ ] 建立分支
- [ ] 通知相關人員
- [ ] 準備測試環境

### 實施中監控
- [ ] 每日進度更新
- [ ] 問題即時記錄
- [ ] 定期代碼審查
- [ ] 持續集成測試

### 完成後驗證
- [ ] 全面測試通過
- [ ] 性能指標達標
- [ ] 文檔更新完成
- [ ] 團隊培訓完成

---

**文檔版本**: v1.0.0  
**創建日期**: 2024-12-XX  
**最後更新**: 2024-12-XX  
**狀態**: 待審批

## 批准簽核

- [ ] 技術負責人
- [ ] 產品經理
- [ ] 專案經理
- [ ] QA 負責人

---

*本計劃書為 Linker 專案 UI 統一化的完整指導文件，請嚴格按照計劃執行。*