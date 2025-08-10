# Linker UI 設計系統使用指南

## 📚 概述

Linker UI 設計系統是一套完整、模組化、高性能的前端組件庫，基於現代 CSS 架構和 Glass Morphism 設計風格。

## 🏗️ 架構

```
design-system/
├── 01-tokens/       # 設計令牌（變數）
├── 02-base/         # 基礎樣式
├── 03-components/   # 組件樣式
└── 04-layouts/      # 佈局系統
```

## 🎨 核心組件

### 1. 按鈕 (Buttons)

#### 基本用法
```html
<!-- 主要按鈕 -->
<button class="btn" data-variant="primary">主要操作</button>

<!-- 次要按鈕 -->
<button class="btn" data-variant="secondary">次要操作</button>

<!-- 危險按鈕 -->
<button class="btn" data-variant="danger">刪除</button>

<!-- Ghost 按鈕 -->
<button class="btn" data-variant="ghost">取消</button>
```

#### 尺寸變化
```html
<button class="btn" data-variant="primary" data-size="sm">小按鈕</button>
<button class="btn" data-variant="primary" data-size="md">中按鈕</button>
<button class="btn" data-variant="primary" data-size="lg">大按鈕</button>
```

#### 載入狀態
```html
<button class="btn" data-variant="primary" data-loading="true">
  <span class="spinner"></span>
  載入中...
</button>
```

### 2. 卡片 (Cards)

#### 基本卡片
```html
<div class="card">
  <h3>卡片標題</h3>
  <p>卡片內容</p>
</div>
```

#### 互動式卡片
```html
<div class="card" data-interactive="true">
  <h3>可點擊卡片</h3>
  <p>滑鼠懸停有效果</p>
</div>
```

#### Glass 效果卡片
```html
<div class="card" data-glass="true">
  <h3>玻璃質感卡片</h3>
  <p>半透明模糊效果</p>
</div>
```

### 3. 徽章 (Badges)

```html
<!-- 狀態徽章 -->
<span class="badge" data-variant="success">成功</span>
<span class="badge" data-variant="warning">警告</span>
<span class="badge" data-variant="error">錯誤</span>
<span class="badge" data-variant="info">資訊</span>

<!-- 尺寸 -->
<span class="badge" data-variant="primary" data-size="sm">小徽章</span>
<span class="badge" data-variant="primary" data-size="lg">大徽章</span>
```

### 4. 表單 (Forms)

#### 輸入框
```html
<div class="form-group">
  <label class="form-label">標籤</label>
  <input type="text" class="form-control" placeholder="請輸入...">
  <span class="form-hint">提示文字</span>
</div>
```

#### 下拉選單
```html
<select class="form-control">
  <option>選項 1</option>
  <option>選項 2</option>
</select>
```

#### 文字區域
```html
<textarea class="form-control" rows="4" placeholder="請輸入..."></textarea>
```

### 5. 載入狀態 (Loading)

#### Spinner 類型
```html
<!-- 簡單旋轉 -->
<div class="spinner"></div>

<!-- 雙環旋轉 -->
<div class="spinner" data-type="double"></div>

<!-- 多環旋轉 -->
<div class="spinner" data-type="multi-ring">
  <div class="spinner-ring"></div>
  <div class="spinner-ring"></div>
  <div class="spinner-ring"></div>
</div>

<!-- 點狀載入 -->
<div class="spinner" data-type="dots">
  <div class="spinner-dot"></div>
  <div class="spinner-dot"></div>
  <div class="spinner-dot"></div>
</div>
```

#### 載入覆蓋層
```html
<div class="loading-overlay">
  <div class="loading-modal" data-glass="true">
    <div class="spinner" data-type="multi-ring">
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
    </div>
    <h3>載入中...</h3>
  </div>
</div>
```

#### 骨架屏
```html
<div class="skeleton">
  <div class="skeleton-header"></div>
  <div class="skeleton-text"></div>
  <div class="skeleton-text" style="width: 80%"></div>
</div>
```

### 6. 模態框 (Modals)

#### 基本模態框
```html
<div class="modal-overlay">
  <div class="modal">
    <div class="modal-header">
      <h2 class="modal-title">標題</h2>
      <button class="modal-close">&times;</button>
    </div>
    <div class="modal-body">
      內容
    </div>
    <div class="modal-footer">
      <button class="btn" data-variant="secondary">取消</button>
      <button class="btn" data-variant="primary">確認</button>
    </div>
  </div>
</div>
```

#### Glass 效果模態框
```html
<div class="modal" data-glass="true">
  <!-- 內容 -->
</div>
```

## 🎯 設計令牌

### 顏色系統
```css
/* 主要顏色 */
var(--color-primary)         /* 主色 */
var(--color-primary-hover)   /* 主色懸停 */
var(--color-primary-subtle)  /* 主色淺色 */

/* 語義顏色 */
var(--color-success)         /* 成功 */
var(--color-warning)         /* 警告 */
var(--color-error)           /* 錯誤 */
var(--color-info)            /* 資訊 */

/* 文字顏色 */
var(--text-primary)          /* 主要文字 */
var(--text-secondary)        /* 次要文字 */
var(--text-muted)            /* 輔助文字 */
```

### 間距系統 (8px 網格)
```css
var(--space-1)   /* 4px */
var(--space-2)   /* 8px */
var(--space-3)   /* 12px */
var(--space-4)   /* 16px */
var(--space-5)   /* 20px */
var(--space-6)   /* 24px */
var(--space-8)   /* 32px */
var(--space-10)  /* 40px */
var(--space-12)  /* 48px */
var(--space-16)  /* 64px */
```

### 圓角
```css
var(--radius-sm)    /* 4px */
var(--radius-md)    /* 8px */
var(--radius-lg)    /* 16px */
var(--radius-xl)    /* 24px */
var(--radius-full)  /* 9999px */
```

### 陰影
```css
var(--shadow-xs)    /* 極小陰影 */
var(--shadow-sm)    /* 小陰影 */
var(--shadow-md)    /* 中陰影 */
var(--shadow-lg)    /* 大陰影 */
var(--shadow-xl)    /* 特大陰影 */
var(--shadow-2xl)   /* 超大陰影 */
```

## 🚀 性能優化

### Glass Morphism 優化
```html
<!-- 僅在關鍵元素使用重度模糊 -->
<div class="modal" data-glass="true" data-blur="heavy">
  <!-- 內容 -->
</div>

<!-- 移動設備使用輕量模糊 -->
<div class="card" data-glass="true" data-blur="light">
  <!-- 內容 -->
</div>
```

### 動畫優化
```javascript
// 動畫開始前添加 will-change
element.classList.add('will-animate');

// 動畫結束後移除
element.addEventListener('animationend', () => {
  element.classList.add('animation-done');
  element.classList.remove('will-animate');
});
```

### 性能類別
```html
<!-- 關閉模糊效果 -->
<div class="card perf-no-blur">內容</div>

<!-- 關閉動畫 -->
<div class="btn perf-no-animation">按鈕</div>

<!-- 關閉陰影 -->
<div class="card perf-no-shadow">卡片</div>
```

## 📦 生產環境使用

### 使用壓縮版本
```html
<!-- 開發環境 -->
<link rel="stylesheet" href="/static/css/design-system/index.css">

<!-- 生產環境 -->
<link rel="stylesheet" href="/static/css/dist/design-system.min.css">
```

### 構建命令
```bash
# 壓縮 CSS
./build-css.sh

# 輸出位置
web/static/css/dist/
├── design-system.min.css    # 完整設計系統
├── index.min.css            # 首頁樣式
├── practice.min.css         # 練習頁樣式
├── knowledge.min.css        # 知識點頁樣式
└── patterns.min.css         # 文法頁樣式
```

## 🌈 主題切換

系統自動支援深色模式：
```css
/* 自動適應系統主題 */
@media (prefers-color-scheme: dark) {
  /* 深色模式樣式 */
}
```

## ♿ 無障礙支援

### 減少動態效果
```css
/* 自動適應用戶偏好 */
@media (prefers-reduced-motion: reduce) {
  /* 減少或關閉動畫 */
}
```

### 高對比模式
```css
@media (prefers-contrast: high) {
  /* 增強對比度 */
}
```

## 📝 最佳實踐

1. **使用語義化的 data 屬性**
   ```html
   <button class="btn" data-variant="primary" data-size="lg">
   ```

2. **避免硬編碼數值**
   ```css
   /* ❌ 不好 */
   padding: 16px;
   
   /* ✅ 好 */
   padding: var(--space-4);
   ```

3. **合理使用 Glass 效果**
   - 僅在關鍵視覺元素使用
   - 移動設備使用輕量版本
   - 考慮性能影響

4. **動畫性能**
   - 使用 transform 和 opacity
   - 適時添加 will-change
   - 動畫結束後清理

## 🔧 故障排除

### Glass 效果不顯示
檢查瀏覽器支援：
```css
@supports (backdrop-filter: blur(1px)) {
  /* 支援 backdrop-filter */
}
```

### 動畫卡頓
1. 檢查是否正確使用 will-change
2. 減少同時進行的動畫數量
3. 使用 transform 替代位置屬性

### 樣式優先級問題
確保正確的引入順序：
1. 設計系統 CSS
2. 頁面專屬 CSS
3. 自定義覆蓋樣式

## 📚 資源連結

- [CSS Variables MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Backdrop Filter MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/backdrop-filter)
- [Will-change MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/will-change)
- [Prefers-reduced-motion MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)

---

最後更新：2024-12
版本：1.0.0