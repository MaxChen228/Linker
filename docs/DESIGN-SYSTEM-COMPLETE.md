# Linker 設計系統完整文檔

## 設計系統概述

Linker 的設計系統基於簡約、一致、專業的設計理念，採用 Indigo 單一主色調配合灰階系統，創造清晰的視覺層次和優雅的用戶體驗。

## 設計令牌 (Design Tokens)

### 色彩系統

#### 主色調 (Accent Colors)
```css
/* Indigo 色階 - 用於主要交互元素 */
--accent-50: #eef2ff;
--accent-100: #e0e7ff;
--accent-200: #c7d2fe;
--accent-300: #a5b4fc;
--accent-400: #818cf8;
--accent-500: #6366f1;  /* 主要色 */
--accent-600: #4f46e5;  /* hover */
--accent-700: #4338ca;  /* active */
--accent-800: #3730a3;
--accent-900: #312e81;
--accent-950: #1e1b4b;
```

#### 灰階系統 (Neutral Colors)
```css
/* 完整灰階 - 用於文字、背景、邊框 */
--gray-50: #f9fafb;   /* 最淺背景 */
--gray-100: #f3f4f6;  /* 次要背景 */
--gray-200: #e5e7eb;  /* 邊框 */
--gray-300: #d1d5db;
--gray-400: #9ca3af;
--gray-500: #6b7280;  /* 次要文字 */
--gray-600: #4b5563;
--gray-700: #374151;  /* 主要文字 */
--gray-800: #1f2937;
--gray-900: #111827;  /* 標題 */
--gray-950: #030712;
```

#### 語義色彩 (Semantic Colors)
```css
/* 狀態指示色 */
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
--color-info: #3b82f6;
```

#### 表面層次 (Surface Levels)
```css
/* 創造深度的背景層次 */
--surface-base: rgba(255, 255, 255, 0.05);
--surface-elevated: rgba(255, 255, 255, 0.1);
--surface-subtle: rgba(156, 163, 175, 0.1);
```

### 字型系統

#### 字型大小
```css
--text-xs: 0.75rem;   /* 12px - 標籤 */
--text-sm: 0.875rem;  /* 14px - 次要內容 */
--text-base: 1rem;    /* 16px - 正文 */
--text-lg: 1.125rem;  /* 18px - 副標題 */
--text-xl: 1.25rem;   /* 20px */
--text-2xl: 1.5rem;   /* 24px - 標題 */
--text-3xl: 1.875rem; /* 30px */
--text-4xl: 2.25rem;  /* 36px - 頁面標題 */
```

#### 字重規範
```css
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 間距系統 (8px Grid)

```css
--space-0: 0;
--space-0.5: 0.125rem;  /* 2px */
--space-1: 0.25rem;     /* 4px */
--space-1.5: 0.375rem;  /* 6px */
--space-2: 0.5rem;      /* 8px - 基準 */
--space-2.5: 0.625rem;  /* 10px */
--space-3: 0.75rem;     /* 12px */
--space-4: 1rem;        /* 16px */
--space-5: 1.25rem;     /* 20px */
--space-6: 1.5rem;      /* 24px */
--space-8: 2rem;        /* 32px */
--space-10: 2.5rem;     /* 40px */
--space-12: 3rem;       /* 48px */
--space-16: 4rem;       /* 64px */
```

### 圓角系統

```css
--radius-sm: 0.25rem;   /* 4px - 小元素 */
--radius: 0.375rem;     /* 6px */
--radius-md: 0.5rem;    /* 8px - 預設 */
--radius-lg: 0.75rem;   /* 12px - 卡片 */
--radius-xl: 1rem;      /* 16px - 模態框 */
--radius-2xl: 1.5rem;   /* 24px */
--radius-full: 9999px;  /* 圓形 */
```

### 陰影系統

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
--shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

### 動畫系統

```css
/* 過渡時長 */
--transition-fast: 150ms;
--transition-base: 200ms;
--transition-slow: 300ms;

/* 緩動函數 */
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

## 核心組件

### 按鈕組件

#### 基礎樣式
```css
.btn {
  /* 基礎樣式 */
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-weight: var(--font-medium);
  transition: all var(--transition-base);
}
```

#### 變體類型
- **Primary**: 主要操作按鈕（深色背景）
- **Secondary**: 次要操作（透明背景+邊框）
- **Ghost**: 最小化樣式（純透明）
- **Danger**: 危險操作（紅色）

### 卡片組件

#### 變體類型
- **Default**: 基礎卡片（細邊框）
- **Elevated**: 提升卡片（陰影）
- **Bordered**: 邊框卡片（強調邊框）
- **Interactive**: 可交互卡片（hover效果）

### 徽章組件

#### 語義變體
- **Success**: 成功狀態（綠色）
- **Warning**: 警告狀態（橙色）
- **Error**: 錯誤狀態（紅色）
- **Info**: 信息狀態（藍色）
- **Default**: 預設狀態（灰色）

### 表單組件

#### 輸入框樣式
- 統一邊框和圓角
- 清晰的焦點狀態
- 驗證狀態指示
- 無障礙支援

## 頁面設計規範

### 練習頁面 (/practice)

#### 設計特點
- 內嵌式模式切換器
- 灰色背景容器分組
- 左側邊框強調重點
- 簡化的參數設定區

### 知識點頁面 (/knowledge)

#### 設計特點
- 左側色條分類指示
- 半透明掌握度徽章
- 統一卡片hover效果
- 清晰的視覺層次

### 文法句型頁面 (/patterns)

#### 設計特點
- 簡化的搜尋欄
- 無邊框分類標籤
- 水平例句佈局
- hover顯示複製按鈕

### 首頁 (/index)

#### 設計特點
- 統一的統計卡片
- 頂部邊框裝飾
- 透明度層次區分
- 簡潔的數據展示

## 設計原則

### 1. 最少顏色原則
- 主要使用灰階創造層次
- 單一主色調（Indigo）作為強調
- 透明度變化區分層級
- 語義色彩僅用於狀態指示

### 2. 一致性原則
- 統一的圓角系統（8px, 12px, 16px）
- 標準化的陰影強度
- 8px網格間距系統
- 一致的動畫時長

### 3. 簡潔性原則
- 移除不必要的裝飾元素
- 減少視覺噪音
- 清晰的信息架構
- 充足的留白空間

### 4. 可訪問性原則
- WCAG AA 對比度標準
- 清晰的焦點狀態
- 合理的點擊區域（最小44x44px）
- 支援鍵盤導航

## 響應式設計

### 斷點系統
```css
--breakpoint-sm: 640px;   /* 手機橫屏 */
--breakpoint-md: 768px;   /* 平板豎屏 */
--breakpoint-lg: 1024px;  /* 平板橫屏 */
--breakpoint-xl: 1280px;  /* 桌面 */
--breakpoint-2xl: 1536px; /* 大屏幕 */
```

### 適配策略
- Mobile-first 設計方法
- 彈性網格佈局
- 自適應字型大小
- 觸控友好的交互區域

## 性能優化

### CSS 優化成果
- 檔案大小減少 40-50%
- 移除重複樣式規則
- 簡化選擇器層級
- 使用 CSS 變數避免重複

### 載入優化
- 關鍵 CSS 內聯
- 非關鍵 CSS 延遲載入
- 使用 will-change 優化動畫
- 減少重繪和重排

## 暗色模式支援

### 實施策略
```css
@media (prefers-color-scheme: dark) {
  :root {
    /* 暗色模式變數覆蓋 */
  }
}
```

### 注意事項
- 調整顏色對比度
- 減少亮度避免刺眼
- 保持品牌一致性
- 測試可讀性

## 組件使用指南

### 按鈕使用
```html
<!-- 主要按鈕 -->
<button class="btn btn-primary">確認</button>

<!-- 次要按鈕 -->
<button class="btn btn-secondary">取消</button>

<!-- 幽靈按鈕 -->
<button class="btn btn-ghost">更多</button>
```

### 卡片使用
```html
<!-- 基礎卡片 -->
<div class="card">內容</div>

<!-- 可交互卡片 -->
<div class="card card-interactive">可點擊內容</div>
```

### 徽章使用
```html
<!-- 狀態徽章 -->
<span class="badge badge-success">完成</span>
<span class="badge badge-warning">進行中</span>
```

## 維護指南

### 新增組件
1. 在對應的組件文件中定義
2. 使用設計令牌而非硬編碼值
3. 提供多個變體選項
4. 添加使用文檔

### 修改令牌
1. 在 `01-tokens/` 目錄中修改
2. 確保全局一致性
3. 測試所有受影響的組件
4. 更新文檔

## 已完成的改進

### Phase 1: 設計令牌建立 ✅
- 統一色彩系統
- 標準化間距
- 字型層級定義
- 效果系統建立

### Phase 2: 組件重構 ✅
- 按鈕系統統一
- 卡片組件簡化
- 徽章系統優化
- 表單元素改進

### Phase 3: 頁面遷移 ✅
- 4個主要頁面完成
- 視覺一致性達成
- 響應式優化
- 無障礙改善

### Phase 4: 深度優化 ✅
- CSS 檔案精簡
- 性能提升
- 代碼審查
- 文檔完善

## 後續建議

1. **持續優化**
   - 監控用戶反饋
   - 性能指標追蹤
   - A/B 測試新設計

2. **擴展功能**
   - 深色模式完善
   - 動畫庫擴充
   - 組件變體增加

3. **文檔維護**
   - 保持文檔更新
   - 添加更多範例
   - 建立設計規範

---

**最後更新**: 2025-08-10  
**版本**: 1.0.0  
**狀態**: 生產就緒