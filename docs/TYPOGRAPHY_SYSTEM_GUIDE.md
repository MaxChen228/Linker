# 文字系統使用指南 | Typography System Guide

## 系統概述

Linker 專案採用三層文字系統架構，提供完整的文字設計令牌支援。

### 三層架構

1. **原始值層 (Raw Values)**
   - 定義所有基礎數值
   - 字體大小、字重、行高、字距

2. **語義組合層 (Semantic Combinations)**
   - 組合原始值為有意義的集合
   - 標題、內容、特殊文字

3. **組件應用層 (Component Applications)**
   - 為特定組件定義文字樣式
   - 按鈕、表單、卡片等

## 變數清單

### 字體大小 (Font Sizes)

| 變數 | 值 | 用途 |
|------|-----|------|
| `--text-2xs` | 0.625rem (10px) | 極小文字、版權資訊 |
| `--text-xxs` | 0.6875rem (11px) | 特殊小字、元數據 |
| `--text-xs` | 0.75rem (12px) | 輔助文字、標籤 |
| `--text-sm` | 0.875rem (14px) | 次要內容、按鈕 |
| `--text-base` | 1rem (16px) | 正文基準 |
| `--text-lg` | 1.125rem (18px) | 強調內容 |
| `--text-xl` | 1.25rem (20px) | 小標題 |
| `--text-2xl` | 1.5rem (24px) | 標題 |
| `--text-3xl` | 1.875rem (30px) | 大標題 |
| `--text-4xl` | 2.25rem (36px) | 特大標題 |
| `--text-5xl` | 3rem (48px) | 超大標題 |
| `--text-6xl` | 3.75rem (60px) | 巨大標題 |

### 字重 (Font Weights)

| 變數 | 值 | 用途 |
|------|-----|------|
| `--font-thin` | 100 | 極細字重 |
| `--font-extralight` | 200 | 超細字重 |
| `--font-light` | 300 | 輕字重 |
| `--font-normal` | 400 | 標準字重 |
| `--font-medium` | 500 | 中等字重 |
| `--font-semibold` | 600 | 半粗體 |
| `--font-bold` | 700 | 粗體 |
| `--font-extrabold` | 800 | 超粗體 |
| `--font-black` | 900 | 極粗體 |

### 行高 (Line Heights)

| 變數 | 值 | 用途 |
|------|-----|------|
| `--leading-tight` | 1.25 | 標題、緊湊內容 |
| `--leading-normal` | 1.5 | 標準內容 |
| `--leading-relaxed` | 1.625 | 寬鬆閱讀 |
| `--leading-loose` | 2.0 | 超寬鬆間距 |

### 字距 (Letter Spacing)

| 變數 | 值 | 用途 |
|------|-----|------|
| `--tracking-tight` | -0.02em | 緊密字距 |
| `--tracking-normal` | 0 | 標準字距 |
| `--tracking-wide` | 0.025em | 寬鬆字距 |

### 字體系列 (Font Families)

| 變數 | 值 | 用途 |
|------|-----|------|
| `--font-sans` | -apple-system, BlinkMacSystemFont, 'Segoe UI'... | 無襯線字體 |
| `--font-mono` | 'SF Mono', 'Monaco', 'Inconsolata'... | 等寬字體 |

## 使用範例

### 標題層級

```css
h1 {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
}

h2 {
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
}

h3 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-normal);
}
```

### 內容文字

```css
.body-text {
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-relaxed);
}

.body-small {
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
}

.caption {
  font-size: var(--text-xs);
  line-height: var(--leading-normal);
}
```

### 組件應用

```css
.button {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  letter-spacing: var(--tracking-wide);
}

.form-label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.helper-text {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.code {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}
```

## 語義化變數 (建議擴展)

為了更好的可維護性，建議創建語義化變數：

```css
:root {
  /* 標題系統 */
  --text-heading-1: var(--text-4xl);
  --text-heading-2: var(--text-3xl);
  --text-heading-3: var(--text-2xl);
  --text-heading-4: var(--text-xl);
  --text-heading-5: var(--text-lg);
  --text-heading-6: var(--text-base);
  
  /* 內容系統 */
  --text-body-large: var(--text-lg);
  --text-body: var(--text-base);
  --text-body-small: var(--text-sm);
  --text-caption: var(--text-xs);
  --text-overline: var(--text-xxs);
  
  /* 組件系統 */
  --text-button: var(--text-sm);
  --text-label: var(--text-sm);
  --text-input: var(--text-base);
  --text-helper: var(--text-xs);
  --text-error: var(--text-xs);
}
```

## 響應式文字 (建議實現)

使用 clamp() 函數實現流體文字：

```css
:root {
  /* 響應式標題 */
  --text-responsive-6xl: clamp(2.25rem, 3.75rem + 4vw, 4.5rem);
  --text-responsive-5xl: clamp(2rem, 3rem + 3vw, 3.75rem);
  --text-responsive-4xl: clamp(1.75rem, 2.25rem + 2vw, 3rem);
  --text-responsive-3xl: clamp(1.5rem, 1.875rem + 1.5vw, 2.25rem);
  --text-responsive-2xl: clamp(1.25rem, 1.5rem + 1vw, 1.875rem);
  --text-responsive-xl: clamp(1.125rem, 1.25rem + 0.5vw, 1.5rem);
  
  /* 響應式內容 */
  --text-responsive-lg: clamp(1rem, 1.125rem + 0.25vw, 1.25rem);
  --text-responsive-base: clamp(0.875rem, 1rem, 1.125rem);
  --text-responsive-sm: clamp(0.75rem, 0.875rem, 1rem);
}
```

## 中文優化 (建議實現)

針對中文顯示的特殊處理：

```css
:root {
  /* 中文字體堆疊 */
  --font-chinese: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 
                  'WenQuanYi Micro Hei', sans-serif;
  
  /* 中文行高優化 */
  --leading-chinese-tight: 1.4;
  --leading-chinese-normal: 1.7;
  --leading-chinese-relaxed: 1.9;
  
  /* 中文字距優化 */
  --tracking-chinese: 0.05em;
}

.chinese-content {
  font-family: var(--font-chinese);
  line-height: var(--leading-chinese-normal);
  letter-spacing: var(--tracking-chinese);
}
```

## 可讀性優化建議

### 對比度

確保文字顏色與背景的對比度符合 WCAG 標準：
- 正文文字：最少 4.5:1
- 大型文字（18px+ 或 14px+ 粗體）：最少 3:1

### 行長度

建議每行文字長度：
- 英文：45-75 字符
- 中文：20-35 字符

### 間距

垂直節奏建議：
- 段落間距：1.5-2倍行高
- 標題與內容間距：1.2-1.5倍標題行高

## 最佳實踐

1. **保持一致性**
   - 使用變數而非硬編碼值
   - 遵循設計系統規範

2. **語義化使用**
   - 選擇合適的語義變數
   - 避免直接使用原始值

3. **響應式考量**
   - 大標題使用響應式變數
   - 考慮不同設備的閱讀體驗

4. **性能優化**
   - 避免過多的字體載入
   - 使用系統字體優先

5. **無障礙設計**
   - 確保足夠的顏色對比度
   - 支援文字縮放功能

## 遷移指南

從硬編碼值遷移到變數系統：

```css
/* 舊寫法 */
.old-style {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
}

/* 新寫法 */
.new-style {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  line-height: var(--leading-relaxed);
}
```

## 工具和測試

### 視覺測試

建議創建測試頁面來驗證文字系統：
- 所有字體大小的展示
- 不同字重的對比
- 行高效果展示
- 中英混排測試
- 響應式效果驗證

### 程式化檢查

可以創建腳本來檢查：
- 硬編碼字體大小的使用
- 變數使用覆蓋率
- 一致性檢查

## 版本歷史

- **v1.0**: 基礎文字變數定義
- **v1.1**: 新增更多字重選項
- **v1.2**: 優化行高系統
- **v1.3**: 新增字距變數
- **v2.0**: 建議的語義化擴展

---

本指南幫助開發團隊有效使用 Linker 專案的文字系統，確保設計一致性和可維護性。