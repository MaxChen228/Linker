# Linker 間距系統使用指南

## 概述

Linker 的間距系統採用 **8px 基礎單位系統**，基於這個數學基礎建立了一套完整、一致的空間尺度。這個系統確保了界面的韻律感和視覺平衡，同時提供了足夠的靈活性滿足不同場景的需求。

## 設計理念

### 為什麼選擇 8px？

1. **視覺和諧**: 8px 是視覺上舒適的基礎單位，既不會太小影響可讀性，也不會太大浪費空間
2. **數學邏輯**: 8 的倍數容易計算和記憶，支援整數倍縮放
3. **設備友好**: 在各種螢幕密度下都能良好顯示，避免像素模糊
4. **生態相容**: 與主流設計系統（如 Material Design、Ant Design）相容

### 空間層次哲學

間距系統遵循**層次遞進**的原則：
- **微觀間距** (1-6px): 元素內部的細節間距
- **元素間距** (8-16px): 相關元素之間的間距
- **組件間距** (20-32px): 不同組件之間的間距
- **區塊間距** (40-64px): 大區塊之間的間距
- **頁面間距** (80px+): 頁面級別的間距

## 完整間距變數清單

### 基礎間距階梯

```css
:root {
  /* 基礎間距 (8px 為核心基準) */
  --space-0: 0;        /* 無間距 */
  --space-1: 4px;      /* 0.5 * 8 - 最小間距 */
  --space-1-5: 6px;    /* 0.75 * 8 - 微調間距 */
  --space-2: 8px;      /* 1 * 8 - 基準間距 */
  --space-2-5: 10px;   /* 1.25 * 8 - 特殊需求 */
  --space-3: 12px;     /* 1.5 * 8 - 小組件間距 */
  --space-4: 16px;     /* 2 * 8 - 標準間距 */
  --space-5: 20px;     /* 2.5 * 8 - 中等間距 */
  --space-6: 24px;     /* 3 * 8 - 大組件間距 */
  --space-8: 32px;     /* 4 * 8 - 區塊間距 */
  --space-10: 40px;    /* 5 * 8 - 大區塊間距 */
  --space-12: 48px;    /* 6 * 8 - 主要區塊間距 */
  --space-16: 64px;    /* 8 * 8 - 頁面級間距 */
  --space-20: 80px;    /* 10 * 8 - 超大間距 */
}
```

### 組件特定間距

```css
:root {
  /* 按鈕系統 */
  --btn-height-sm: 32px;   /* 小型按鈕高度 */
  --btn-height-md: 40px;   /* 中型按鈕高度 */
  --btn-height-lg: 48px;   /* 大型按鈕高度 */
  
  --btn-padding-sm: 0 var(--space-4);   /* 小型按鈕內距 */
  --btn-padding-md: 0 var(--space-5);   /* 中型按鈕內距 */
  --btn-padding-lg: 0 var(--space-8);   /* 大型按鈕內距 */
  
  --btn-gap-sm: var(--space-1);   /* 小型按鈕內容間距 */
  --btn-gap-md: var(--space-2);   /* 中型按鈕內容間距 */
  --btn-gap-lg: var(--space-3);   /* 大型按鈕內容間距 */
}
```

## 使用場景指南

### 1. 微觀間距 (0-6px)

**使用場合**: 元素內部的精細調整

- `--space-0` (0px): 重置間距，緊密佈局
- `--space-1` (4px): 圖標與文字間的最小間距
- `--space-1-5` (6px): 徽章內部間距、小標籤

```css
/* 範例：徽章內部間距 */
.badge {
  padding: var(--space-1) var(--space-2);
}

/* 範例：按鈕圖標與文字 */
.btn-icon {
  gap: var(--space-1);
}
```

### 2. 元素間距 (8-16px)

**使用場合**: 相關元素之間的間距

- `--space-2` (8px): 基礎間距，緊密相關的元素
- `--space-3` (12px): 表單元素間距、清單項目間距
- `--space-4` (16px): 標準內容間距、卡片內部間距

```css
/* 範例：表單組間距 */
.form-group {
  margin-bottom: var(--space-3);
}

/* 範例：卡片內部間距 */
.card {
  padding: var(--space-4);
}
```

### 3. 組件間距 (20-32px)

**使用場合**: 不同組件之間的分隔

- `--space-5` (20px): 中等組件間距
- `--space-6` (24px): 卡片間距、主要組件間距
- `--space-8` (32px): 大組件間距、區段分隔

```css
/* 範例：題目佇列系統 */
.question-queue {
  margin: var(--space-6) 0;
  padding: var(--space-6);
}

/* 範例：組件間的標準間距 */
.section + .section {
  margin-top: var(--space-8);
}
```

### 4. 區塊間距 (40-64px)

**使用場合**: 主要內容區塊之間的間距

- `--space-10` (40px): 主要內容區塊間距
- `--space-12` (48px): 頁面主要區段間距
- `--space-16` (64px): 頁面級別的大間距

```css
/* 範例：頁面主要區段 */
.main-section {
  padding: var(--space-12) 0;
}

/* 範例：內容與邊欄 */
.content-area {
  margin-bottom: var(--space-16);
}
```

### 5. 頁面間距 (80px+)

**使用場合**: 頁面級別的超大間距

- `--space-20` (80px): 頁面頂部/底部間距

```css
/* 範例：頁面容器 */
.page-container {
  padding: var(--space-20) 0;
}
```

## 間距層次結構

### 視覺層次原則

```
頁面間距 (80px+)
    ├── 區塊間距 (40-64px)
    │   ├── 組件間距 (20-32px)
    │   │   ├── 元素間距 (8-16px)
    │   │   │   └── 微觀間距 (0-6px)
```

### 實際應用範例

```css
/* 頁面結構 */
.page {
  padding: var(--space-16) var(--space-6); /* 頁面級間距 */
}

.main-content {
  display: flex;
  gap: var(--space-8); /* 主要內容區塊間距 */
}

.content-section {
  margin-bottom: var(--space-6); /* 組件間距 */
}

.card {
  padding: var(--space-4); /* 卡片內部間距 */
  margin-bottom: var(--space-4); /* 卡片間距 */
}

.card-title {
  margin-bottom: var(--space-2); /* 標題與內容間距 */
}

.inline-elements {
  gap: var(--space-1); /* 行內元素間距 */
}
```

## 常見佈局模式

### 1. 卡片佈局

```css
/* 卡片容器 */
.card-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--space-6); /* 卡片間距 */
  padding: var(--space-4); /* 容器內距 */
}

/* 卡片內部 */
.card {
  padding: var(--space-4); /* 卡片內距 */
  border-radius: var(--radius-lg);
}

.card-header {
  margin-bottom: var(--space-3); /* 標題與內容間距 */
}

.card-body {
  margin-bottom: var(--space-4); /* 內容與動作間距 */
}
```

### 2. 表單佈局

```css
/* 表單容器 */
.form {
  max-width: 500px;
  padding: var(--space-6);
}

/* 表單組 */
.form-group {
  margin-bottom: var(--space-4); /* 表單組間距 */
}

.form-label {
  margin-bottom: var(--space-1); /* 標籤與輸入框間距 */
}

.form-input {
  padding: var(--space-2) var(--space-3); /* 輸入框內距 */
}

.form-actions {
  margin-top: var(--space-6); /* 動作區間距 */
  gap: var(--space-3); /* 按鈕間距 */
}
```

### 3. 清單佈局

```css
/* 清單容器 */
.list {
  padding: 0;
  margin: 0;
}

.list-item {
  padding: var(--space-3) var(--space-4); /* 清單項內距 */
  border-bottom: 1px solid var(--border-light);
}

.list-item:last-child {
  border-bottom: none;
}

/* 清單項內容 */
.item-content {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4); /* 內容間距 */
}

.item-meta {
  display: flex;
  gap: var(--space-2); /* 元資料間距 */
}
```

### 4. 導航佈局

```css
/* 主導航 */
.nav {
  padding: var(--space-4) var(--space-6); /* 導航內距 */
  display: flex;
  justify-content: space-between;
  gap: var(--space-8); /* 導航區塊間距 */
}

.nav-links {
  display: flex;
  gap: var(--space-6); /* 導航連結間距 */
}

.nav-link {
  padding: var(--space-2) var(--space-3); /* 連結內距 */
}
```

## 最佳實踐

### 1. 選擇間距的黃金法則

```css
/* ✅ 好的做法 */
.component {
  padding: var(--space-4);
  margin-bottom: var(--space-6);
  gap: var(--space-2);
}

/* ❌ 避免的做法 */
.component {
  padding: 15px;           /* 不符合 8px 網格 */
  margin-bottom: 25px;     /* 不符合 8px 網格 */
  gap: 7px;               /* 不符合 8px 網格 */
}
```

### 2. 響應式間距

```css
/* 響應式間距調整 */
.responsive-section {
  padding: var(--space-4);
}

@media (min-width: 768px) {
  .responsive-section {
    padding: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .responsive-section {
    padding: var(--space-8);
  }
}
```

### 3. 組件內部間距策略

```css
/* 組件間距從內向外遞增 */
.component {
  /* 最外層間距最大 */
  padding: var(--space-6);
}

.component-header {
  /* 內部區塊間距中等 */
  margin-bottom: var(--space-4);
}

.component-title {
  /* 標題間距較小 */
  margin-bottom: var(--space-2);
}

.component-meta {
  /* 最小間距 */
  gap: var(--space-1);
}
```

### 4. 避免的反模式

```css
/* ❌ 不要疊加 margin */
.item {
  margin-bottom: var(--space-4);
}
.item:last-child {
  margin-bottom: 0; /* 需要重置 */
}

/* ✅ 推薦使用 gap */
.container {
  display: flex;
  flex-direction: column;
  gap: var(--space-4); /* 自動處理最後一個元素 */
}

/* ❌ 不要使用不規律的間距 */
.bad-spacing {
  padding: 13px 17px; /* 不符合系統 */
}

/* ✅ 使用系統化間距 */
.good-spacing {
  padding: var(--space-3) var(--space-4);
}
```

## 視覺化間距對照表

### 間距大小視覺對照

```
--space-1  (4px)   ■
--space-2  (8px)   ■■
--space-3  (12px)  ■■■
--space-4  (16px)  ■■■■
--space-5  (20px)  ■■■■■
--space-6  (24px)  ■■■■■■
--space-8  (32px)  ■■■■■■■■
--space-10 (40px)  ■■■■■■■■■■
--space-12 (48px)  ■■■■■■■■■■■■
--space-16 (64px)  ■■■■■■■■■■■■■■■■
--space-20 (80px)  ■■■■■■■■■■■■■■■■■■■■
```

### 實際應用場景對照

| 間距大小 | 像素值 | 主要用途 | 範例場景 |
|---------|--------|----------|----------|
| `--space-1` | 4px | 最小間距 | 圖標與文字、徽章內距 |
| `--space-2` | 8px | 基礎間距 | 按鈕內容、緊密元素 |
| `--space-3` | 12px | 小間距 | 表單元素、清單項目 |
| `--space-4` | 16px | 標準間距 | 卡片內距、標準內容 |
| `--space-5` | 20px | 中等間距 | 按鈕內距、中型組件 |
| `--space-6` | 24px | 大間距 | 卡片間距、主要組件 |
| `--space-8` | 32px | 區塊間距 | 大組件間距、區段分隔 |
| `--space-10` | 40px | 大區塊間距 | 主要內容區塊 |
| `--space-12` | 48px | 主要間距 | 頁面主要區段 |
| `--space-16` | 64px | 頁面級間距 | 頁面主要區域 |
| `--space-20` | 80px | 超大間距 | 頁面容器邊距 |

## 開發工具建議

### 1. CSS Utilities 類別

```css
/* 間距 Utility 類別 */
.p-1 { padding: var(--space-1); }
.p-2 { padding: var(--space-2); }
.p-3 { padding: var(--space-3); }
.p-4 { padding: var(--space-4); }
.p-5 { padding: var(--space-5); }
.p-6 { padding: var(--space-6); }

.m-1 { margin: var(--space-1); }
.m-2 { margin: var(--space-2); }
.m-3 { margin: var(--space-3); }
.m-4 { margin: var(--space-4); }
.m-5 { margin: var(--space-5); }
.m-6 { margin: var(--space-6); }

.gap-1 { gap: var(--space-1); }
.gap-2 { gap: var(--space-2); }
.gap-3 { gap: var(--space-3); }
.gap-4 { gap: var(--space-4); }
.gap-5 { gap: var(--space-5); }
.gap-6 { gap: var(--space-6); }

/* 方向性間距 */
.pt-4 { padding-top: var(--space-4); }
.pr-4 { padding-right: var(--space-4); }
.pb-4 { padding-bottom: var(--space-4); }
.pl-4 { padding-left: var(--space-4); }

.mt-4 { margin-top: var(--space-4); }
.mr-4 { margin-right: var(--space-4); }
.mb-4 { margin-bottom: var(--space-4); }
.ml-4 { margin-left: var(--space-4); }
```

### 2. 調試工具

```css
/* 開發階段的間距視覺化 */
.debug-spacing * {
  outline: 1px solid rgba(255, 0, 0, 0.3);
  background: rgba(255, 0, 0, 0.05);
}

/* 顯示間距值的調試工具 */
.debug-spacing::before {
  content: attr(data-spacing);
  position: absolute;
  top: -20px;
  left: 0;
  font-size: 10px;
  color: red;
  background: white;
  padding: 2px 4px;
  border: 1px solid red;
}
```

### 3. 間距檢查器

```javascript
// JavaScript 間距檢查器
function checkSpacing() {
  const elements = document.querySelectorAll('*');
  const invalidSpacing = [];
  
  elements.forEach(el => {
    const styles = window.getComputedStyle(el);
    const padding = parseInt(styles.padding);
    const margin = parseInt(styles.margin);
    
    // 檢查是否符合 8px 網格
    if (padding % 4 !== 0 || margin % 4 !== 0) {
      invalidSpacing.push({
        element: el,
        padding: padding,
        margin: margin
      });
    }
  });
  
  console.log('不符合間距系統的元素:', invalidSpacing);
  return invalidSpacing;
}
```

## 遷移指南

### 1. 硬編碼間距識別

目前系統中發現的需要遷移的硬編碼間距：

```css
/* 發現的硬編碼值 */
padding: 20px;          → padding: var(--space-5);
margin: 20px 0;         → margin: var(--space-5) 0;
margin-bottom: 4px;     → margin-bottom: var(--space-1);
gap: 12px;              → gap: var(--space-3);
padding: 8px 0;         → padding: var(--space-2) 0;
margin-bottom: 24px;    → margin-bottom: var(--space-6);
padding: 64px 24px;     → padding: var(--space-16) var(--space-6);
```

### 2. 遷移步驟

1. **識別階段**
   ```bash
   # 使用 grep 尋找硬編碼間距
   grep -r "padding:\|margin:\|gap:" --include="*.css" web/static/css/pages/
   ```

2. **替換階段**
   ```bash
   # 逐一替換為設計令牌
   sed -i 's/padding: 20px/padding: var(--space-5)/g' file.css
   ```

3. **驗證階段**
   - 視覺回歸測試
   - 確保所有間距符合 8px 網格
   - 檢查響應式行為

### 3. 遷移清單

- [ ] `/pages/examples.css` - 大量硬編碼間距需要替換
- [ ] `/pages/pattern-detail.css` - 檢查間距一致性
- [ ] `/pages/practice-tags.css` - 更新間距變數
- [ ] 其他發現的硬編碼間距檔案

### 4. 自動化工具建議

```javascript
// 自動間距遷移腳本
const spacingMap = {
  '4px': 'var(--space-1)',
  '6px': 'var(--space-1-5)',
  '8px': 'var(--space-2)',
  '10px': 'var(--space-2-5)',
  '12px': 'var(--space-3)',
  '16px': 'var(--space-4)',
  '20px': 'var(--space-5)',
  '24px': 'var(--space-6)',
  '32px': 'var(--space-8)',
  '40px': 'var(--space-10)',
  '48px': 'var(--space-12)',
  '64px': 'var(--space-16)',
  '80px': 'var(--space-20)'
};

function migrateSpacing(cssContent) {
  let result = cssContent;
  
  Object.entries(spacingMap).forEach(([px, variable]) => {
    // 替換 padding, margin, gap 中的硬編碼值
    result = result.replace(
      new RegExp(`(padding|margin|gap):\\s*${px}`, 'g'),
      `$1: ${variable}`
    );
  });
  
  return result;
}
```

## 效能考量

### 1. CSS 變數效能

```css
/* ✅ 高效：使用 CSS 變數 */
.component {
  padding: var(--space-4);
  margin: var(--space-6);
}

/* ❌ 低效：重複硬編碼 */
.component1 { padding: 16px; margin: 24px; }
.component2 { padding: 16px; margin: 24px; }
.component3 { padding: 16px; margin: 24px; }
```

### 2. 重繪優化

```css
/* 避免觸發重排的間距變化 */
.smooth-spacing {
  transition: padding 0.2s ease; /* 避免，會觸發重排 */
}

/* 推薦使用 transform */
.smooth-spacing {
  transform: scale(1);
  transition: transform 0.2s ease;
}

.smooth-spacing:hover {
  transform: scale(1.05);
}
```

## 常見問題與解答

### Q1: 為什麼不用 rem 單位？

**A**: 雖然 rem 有響應式優勢，但我們的設計系統採用固定像素值有以下考量：
- 確保在所有設備上的一致性
- 避免用戶瀏覽器字體大小設定影響佈局
- 更精確的視覺控制
- 與設計稿像素值對應

### Q2: 如何處理特殊需求的間距？

**A**: 
1. 優先考慮是否能用現有間距變數組合
2. 如果確實需要，可以使用半步長值（如 `--space-1-5`, `--space-2-5`）
3. 避免創建太多特殊變數，保持系統簡潔

### Q3: 響應式設計中如何調整間距？

**A**:
```css
/* 推薦的響應式間距策略 */
.responsive-component {
  padding: var(--space-4);
}

@media (min-width: 768px) {
  .responsive-component {
    padding: var(--space-6);
  }
}

@media (min-width: 1024px) {
  .responsive-component {
    padding: var(--space-8);
  }
}
```

### Q4: 如何避免間距累積導致過大空白？

**A**:
```css
/* ❌ 間距累積問題 */
.container .item {
  margin-bottom: var(--space-4);
}

/* ✅ 使用 gap 避免累積 */
.container {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
```

## 測試建議

### 1. 視覺回歸測試

```javascript
// 間距測試配置
const spacingTests = [
  {
    name: '按鈕間距測試',
    selector: '.btn',
    expected: {
      padding: '0 20px', // var(--space-5)
      height: '40px'     // var(--btn-height-md)
    }
  },
  {
    name: '卡片間距測試',
    selector: '.card',
    expected: {
      padding: '16px',   // var(--space-4)
      marginBottom: '16px'
    }
  }
];
```

### 2. 間距一致性檢查

```css
/* 測試環境的間距標尺 */
.spacing-ruler {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 8px;
  background: repeating-linear-gradient(
    90deg,
    red 0px,
    red 1px,
    transparent 1px,
    transparent 8px
  );
  z-index: 9999;
  pointer-events: none;
}
```

---

## 總結

Linker 的間距系統提供了完整、一致、可擴展的空間設計框架。通過遵循 8px 基礎單位系統和清晰的層次結構，我們能夠創造出和諧、專業的用戶介面。

記住這些關鍵原則：
- 優先使用設計令牌而非硬編碼值
- 遵循視覺層次，從小到大遞增間距
- 使用 `gap` 屬性避免間距累積
- 保持響應式設計中的間距比例
- 定期檢查和清理不符合系統的硬編碼值

透過持續地應用和完善這個間距系統，我們能夠確保 Linker 產品的視覺一致性和用戶體驗品質。

---

**文件版本**: 1.0.0  
**最後更新**: 2025-08-11  
**維護者**: Linker 設計系統團隊