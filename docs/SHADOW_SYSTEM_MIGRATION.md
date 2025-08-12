# 陰影系統替換對照表

## 基礎黑色陰影替換

| 硬編碼值 | 新變數 | 使用場景 | 檔案位置 |
|---------|--------|---------|----------|
| `rgba(0, 0, 0, 0.04)` | `var(--shadow-2xs)` | 極淺陰影 | 3 處 |
| `rgba(0, 0, 0, 0.05)` | `var(--shadow-xs)` | 輕微陰影 | 4 處 |
| `rgba(0, 0, 0, 0.06)` | `var(--shadow-inner-sm)` | 內陰影 | 3 處 |
| `rgba(0, 0, 0, 0.08)` | `var(--shadow-sm)` | 標準卡片陰影 | 5 處 |
| `rgba(0, 0, 0, 0.1)` | `var(--shadow-md)` | 中等陰影 | 6 處 |
| `rgba(0, 0, 0, 0.15)` | `var(--shadow-lg)` | 深色陰影 | 3 處 |
| `rgba(0, 0, 0, 0.2)` | `var(--shadow-xl)` | 最深陰影 | 4 處 |
| `rgba(0, 0, 0, 0.07)` | `var(--shadow-elevated-md)` (第一層) | 複合陰影 | 1 處 |

## 複合陰影替換

| 硬編碼值 | 新變數 | 說明 |
|---------|--------|------|
| `0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)` | `var(--shadow-elevated-sm)` | 卡片懸停效果 |
| `0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.04)` | `var(--shadow-elevated-md)` | 一般複合陰影 |
| `0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)` | `var(--shadow-elevated-xl)` | 模態框陰影 |

## 內陰影替換

| 硬編碼值 | 新變數 | 說明 |
|---------|--------|------|
| `inset 0 2px 4px 0 rgb(0 0 0 / 0.05)` | `var(--shadow-inner-md)` | 按鈕按下效果 |
| `inset 0 2px 4px rgba(0, 0, 0, 0.06)` | `var(--shadow-inner-sm)` | 輕微內陰影 |

## 彩色陰影替換

### 主色系陰影
| 硬編碼值 | 新變數 | 說明 |
|---------|--------|------|
| `rgba(79, 70, 229, 0.25)` | `var(--shadow-primary)` | 主按鈕陰影 |
| `rgba(79, 70, 229, 0.3)` | `var(--shadow-primary-lg)` | 主按鈕懸停陰影 |

### 焦點陰影
| 硬編碼值 | 新變數 | 說明 |
|---------|--------|------|
| `0 0 0 3px rgba(79, 70, 229, 0.2)` | `var(--shadow-focus)` | 標準焦點陰影 |
| `0 0 0 3px rgba(99, 102, 241, 0.1)` | `var(--shadow-focus-purple)` | 紫色焦點陰影 |
| `0 0 0 3px rgba(33, 150, 243, 0.2)` | `var(--shadow-focus-blue)` | 藍色焦點陰影 |
| `0 0 0 3px rgba(76, 175, 80, 0.2)` | `var(--shadow-focus-green)` | 綠色焦點陰影 |

### 狀態陰影
| 硬編碼值 | 新變數 | 說明 |
|---------|--------|------|
| `rgba(34, 197, 94, 0.1)` | `var(--shadow-success-light)` | 成功狀態淺陰影 |
| `rgba(34, 197, 94, 0.15)` | `var(--shadow-success-heavy)` | 成功狀態深陰影 |

## 使用 CSS 變數但仍硬編碼透明度的情況

| 硬編碼值 | 新變數 | 說明 |
|---------|--------|------|
| `rgba(var(--accent-600-rgb), 0.2)` | `var(--shadow-focus)` | 表單焦點陰影 |
| `rgba(var(--accent-rgb), 0.2)` | `var(--shadow-focus)` | 表單焦點陰影（通用） |
| `rgba(var(--accent-rgb), 0.1)` | `var(--shadow-focus-light)` | 輕微焦點陰影 |
| `rgba(var(--accent-rgb), 0.3)` | `var(--shadow-primary-lg)` | 重點陰影 |

# 按檔案的替換計劃

## 高優先級檔案（立即替換）

### 1. `/web/static/css/pages/knowledge-detail.css` (9 個硬編碼陰影)
```css
/* 替換前 → 替換後 */
rgba(0, 0, 0, 0.1) → var(--shadow-md)
rgba(0, 0, 0, 0.06) → var(--shadow-inner-sm)
rgba(0, 0, 0, 0.04) → var(--shadow-2xs)
rgba(0, 0, 0, 0.07) → 需檢查上下文
rgba(99, 102, 241, 0.3) → var(--shadow-focus-purple)
rgba(34, 197, 94, 0.1) → var(--shadow-success-light)
rgba(34, 197, 94, 0.15) → var(--shadow-success-heavy)

/* 複合陰影 */
0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06) → var(--shadow-elevated-sm)
0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) → var(--shadow-elevated-xl)
0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.04) → var(--shadow-elevated-md)
```

### 2. `/web/static/css/design-system/03-components/forms.css` (8 個硬編碼陰影)
```css
/* 替換前 → 替換後 */
rgba(var(--accent-600-rgb), 0.2) → var(--shadow-focus)
rgba(0, 0, 0, 0.2) → var(--shadow-xl)
```

### 3. `/web/static/css/design-system/03-components/buttons.css` (7 個硬編碼陰影)
```css
/* 替換前 → 替換後 */
rgba(0, 0, 0, 0.08) → var(--shadow-sm)
rgba(0, 0, 0, 0.15) → var(--shadow-lg)
rgba(79, 70, 229, 0.25) → var(--shadow-primary)
rgba(79, 70, 229, 0.3) → var(--shadow-primary-lg)
rgba(0, 0, 0, 0.1) → var(--shadow-md)
```

## 中優先級檔案

### 4-7. 各頁面檔案 (各4個硬編碼陰影)
- `knowledge.css`
- `practice.css`
- `cards.css`
- `practice-queue.css`

## 低優先級檔案

### 8-12. 其餘檔案 (各1-3個硬編碼陰影)
- `index.css`
- `patterns.css`
- `pattern-detail.css`
- `practice-tags.css`
- `examples.css`
- `badges.css`

# 實施步驟

## 步驟 1: 準備階段
1. ✅ 建立新陰影系統 (shadows.css)
2. ✅ 建立遷移映射 (shadows-migration.css)
3. ✅ 建立替換對照表

## 步驟 2: 系統性替換（即將執行）
1. 按檔案優先級順序替換
2. 每個檔案替換後立即測試
3. 確保視覺效果一致性

## 步驟 3: 清理階段
1. 刪除舊系統重複定義
2. 移除遷移映射檔案
3. ✅ 重命名 shadows-v2.css 為 shadows.css

## 步驟 4: 驗證階段
1. 全面測試所有組件
2. 檢查深色模式效果
3. 驗證響應式表現

# 替換腳本示例

## 批量替換指令
```bash
# 替換基礎陰影值
find . -name "*.css" -type f -exec sed -i '' 's/rgba(0, 0, 0, 0\.05)/var(--shadow-xs)/g' {} \;
find . -name "*.css" -type f -exec sed -i '' 's/rgba(0, 0, 0, 0\.08)/var(--shadow-sm)/g' {} \;
find . -name "*.css" -type f -exec sed -i '' 's/rgba(0, 0, 0, 0\.1)/var(--shadow-md)/g' {} \;

# 替換焦點陰影
find . -name "*.css" -type f -exec sed -i '' 's/0 0 0 3px rgba(79, 70, 229, 0\.2)/var(--shadow-focus)/g' {} \;
```

注意：複合陰影需要手動替換，因為格式複雜。