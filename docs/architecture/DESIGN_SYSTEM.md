# Design System Architecture

## Overview

Linker 專案採用完整的設計令牌系統 (Design Token System)，實現了 95.6% 的零硬編碼率。這個文檔詳細說明設計系統的架構、使用方式和最佳實踐。

## 🎯 核心原則

### Zero Hardcode Principle
- **嚴禁魔術數字**: 所有尺寸、顏色、間距必須使用設計令牌
- **語義化命名**: 優先使用語義令牌而非原始數值
- **一致性保證**: 統一的視覺語言和用戶體驗
- **可維護性**: 集中管理所有設計決策

## 📁 Design System 結構

```
web/static/css/design-system/
├── index.css                 # 主入口文件
├── 01-tokens/               # 設計令牌層
│   ├── colors.css          # 顏色系統
│   ├── spacing.css         # 間距系統
│   ├── typography.css      # 字體系統
│   ├── dimensions.css      # 尺寸系統
│   ├── breakpoints.css     # 響應式斷點
│   ├── shadows.css         # 陰影系統
│   ├── animations.css      # 動畫時長
│   └── ...                 # 其他令牌
├── 02-base/                # 基礎樣式層
│   ├── reset.css          # CSS Reset
│   ├── typography.css     # 基礎字體樣式
│   └── accessibility.css  # 無障礙樣式
├── 03-components/          # 組件樣式層
│   ├── buttons.css        # 按鈕組件
│   ├── forms.css          # 表單組件
│   ├── cards.css          # 卡片組件
│   ├── modals.css         # 模態框組件
│   └── ...                # 其他組件
├── 04-layouts/             # 佈局樣式層
│   ├── grid.css           # 網格系統
│   └── layout.css         # 佈局工具
└── 05-utilities/           # 工具類樣式層
    ├── spacing.css        # 間距工具類
    ├── display.css        # 顯示工具類
    └── ...                # 其他工具類
```

## 🎨 設計令牌系統

### 顏色系統 (Colors)
```css
/* 原始色彩 */
--primary-50: #f0f9ff;
--primary-500: #3b82f6;
--primary-900: #1e3a8a;

/* 語義顏色 */
--text-primary: var(--gray-900);
--text-secondary: var(--gray-700);
--bg-surface: var(--white);
--border-default: var(--gray-300);

/* Alpha 透明度系統 */
--alpha-1: 0.02;     /* 極輕微 */
--alpha-3: 0.1;      /* 標準背景疊加 */
--alpha-6: 0.5;      /* 半透明 */
--alpha-7: 0.75;     /* 模態背景 */
```

### 間距系統 (Spacing)
```css
/* 基礎間距 (8px 基準) */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */

/* 特殊間距 */
--space-0-5: 0.125rem;  /* 2px */
--space-1-5: 0.375rem;  /* 6px */
--space-15: 3.75rem;    /* 60px */
```

### 尺寸系統 (Dimensions)
```css
/* 容器最大寬度 */
--max-width-content: 900px;
--max-width-modal: 600px;
--max-width-practice: 1200px;

/* 特定寬度 */
--width-sidebar: 280px;
--width-icon: 24px;
--width-button-icon: 40px;

/* 邊框寬度 */
--border-width-thin: 1px;
--border-width-normal: 2px;
--border-width-thick: 3px;
```

### 字體系統 (Typography)
```css
/* 字體大小 */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px */
--text-xl: 1.25rem;     /* 20px */

/* 字體重量 */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* 行高 */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

## 💡 使用指南

### 基本使用
```css
/* ✅ 正確 - 使用設計令牌 */
.card {
  padding: var(--space-6);
  background: var(--surface-elevated);
  border: var(--border-width-thin) solid var(--border-light);
  border-radius: var(--radius-lg);
}

/* ❌ 錯誤 - 硬編碼值 */
.card {
  padding: 24px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
```

### 語義令牌優先
```css
/* ✅ 優先使用語義令牌 */
.text-primary {
  color: var(--text-primary);
}

/* ⚠️ 次選原始令牌 */
.text-custom {
  color: var(--gray-900);
}

/* ❌ 避免硬編碼 */
.text-bad {
  color: #111827;
}
```

### 響應式設計
```css
/* 使用斷點令牌 */
@media (max-width: var(--breakpoint-md)) {
  .container {
    padding: var(--space-4);
  }
}
```

### Alpha 透明度系統
```css
/* 使用 Alpha 令牌 */
.overlay {
  background: rgba(var(--gray-900-rgb), var(--alpha-7));
}

.subtle-bg {
  background: rgba(var(--primary-rgb), var(--alpha-3));
}
```

## 🔧 擴展設計系統

### 添加新令牌
1. 識別需求類型 (顏色/間距/尺寸等)
2. 添加到對應的 tokens 文件
3. 遵循命名約定
4. 更新相關文檔

### 命名約定
```css
/* 顏色 */
--{category}-{variant}-{intensity}
--primary-500, --success-100, --error-700

/* 間距 */
--space-{multiplier}
--space-4, --space-1-5, --space-15

/* 尺寸 */
--{type}-{variant}
--max-width-content, --width-sidebar, --height-button

/* 語義 */
--{purpose}-{variant}
--text-primary, --bg-surface, --border-default
```

## 📊 TASK-35 完成成果

### 清理統計
- **RGBA 硬編碼**: 218 → 3 (98.6% 清理率)
- **PX 硬編碼**: 420 → 25 (94.0% 清理率)
- **總體清理率**: 638 → 28 (95.6% 零硬編碼達成)

### 保留的硬編碼值 (28個)
- **Letter-spacing 註釋**: 11個 (幫助理解 rem 轉 px)
- **SR-only 樣式**: 3個 (無障礙標準實現)
- **媒體查詢斷點**: 5個 (特殊響應式需求)
- **設計註釋**: 9個 (說明設計意圖)

### 新增令牌
- **28個 Alpha 透明度令牌**: 系統化透明度管理
- **8個語義覆蓋層**: 常用疊加效果
- **6個新間距令牌**: 特殊間距需求
- **4個語義寬度令牌**: 組件特定寬度

## 🚨 開發注意事項

### 禁止事項
- ❌ 絕不使用魔術數字 (hardcoded px, rgba 等)
- ❌ 不要修改 `01-tokens/` 核心令牌
- ❌ 避免內聯樣式
- ❌ 不要繞過設計系統

### 最佳實踐
- ✅ 總是使用設計令牌
- ✅ 優先語義令牌而非原始值
- ✅ 遵循模組化結構
- ✅ 保持一致的命名約定
- ✅ 新增組件前檢查現有令牌

### 代碼審查檢查清單
- [ ] 無硬編碼 px 值
- [ ] 無硬編碼 rgba/hex 顏色
- [ ] 正確使用設計令牌
- [ ] 遵循 @import 依賴結構
- [ ] 語義令牌優於原始令牌

## 🔗 相關文檔

- [CLAUDE.md](../CLAUDE.md) - 項目總體指南
- [Project Structure](../PROJECT_STRUCTURE.md) - 項目結構說明
- [CSS Guidelines](./CSS_GUIDELINES.md) - CSS 編碼規範

---

**最後更新**: 2025-08-16  
**版本**: 1.0 (TASK-35 完成版)  
**狀態**: ✅ 零硬編碼原則完全實施