# TASK-35-03: 硬編碼顏色清理 - 轉換290個rgba值為設計令牌

- **Priority**: 🟡 MEDIUM
- **Estimated Time**: 16-24 hours
- **Related Components**: 全系統CSS文件，22個文件含有rgba用法
- **Parent Task**: TASK-35-main.md

---

### 🎯 Task Objective

系統性地將所有硬編碼的顏色值（290個rgba用法）轉換為設計令牌，建立一致的色彩系統，提高維護性和設計一致性。

### ✅ Acceptance Criteria

- [ ] **完全清除**: 290個rgba硬編碼值全部轉換為CSS變量
- [ ] **設計令牌擴展**: 必要時添加新的顏色令牌
- [ ] **一致性驗證**: 所有顏色使用符合設計系統
- [ ] **視覺回歸測試**: 所有頁面視覺效果保持一致
- [ ] **文檔更新**: 更新色彩使用指南
- [ ] **工具檢查**: 建立硬編碼檢查規則
- [ ] **團隊培訓**: 提供色彩令牌使用說明

### 📊 問題統計分析

**硬編碼分佈:**
```bash
# 發現的290個rgba用法分佈在22個文件中
/web/static/css/design-system/01-tokens/colors-v2.css: 35個
/web/static/css/design-system/01-tokens/glass.css: 38個  
/web/static/css/design-system/03-components/buttons.css: 4個
/web/static/css/design-system/03-components/cards.css: 20個
/web/static/css/pages/practice.css: 8個
# ... 其他17個文件
```

**常見硬編碼模式:**
```css
/* 陰影顏色 */
rgba(0, 0, 0, 0.1)           /* 290個中的~80個 */
rgba(0, 0, 0, 0.2)           /* ~60個 */

/* 背景顏色 */
rgba(255, 255, 255, 0.9)     /* ~40個 */
rgba(255, 255, 255, 0.8)     /* ~30個 */

/* 品牌色彩 */
rgba(79, 70, 229, 0.2)       /* accent色相關 ~25個 */
rgba(16, 185, 129, 0.1)      /* success色相關 ~20個 */

/* 其他語義色彩 */
rgba(239, 68, 68, 0.1)       /* error色相關 ~15個 */
rgba(245, 158, 11, 0.15)     /* warning色相關 ~15個 */
```

### 📋 具體執行步驟

#### Step 1: 全面盤點和分類 (3-4小時)

1. **生成完整清單**
   ```bash
   # 創建詳細的rgba使用清單
   grep -rn "rgba(" web/static/css/ > rgba_audit.txt
   
   # 按文件分組統計
   grep -r "rgba(" web/static/css/ | cut -d: -f1 | sort | uniq -c | sort -nr
   ```

2. **分類硬編碼類型**
   ```bash
   # 陰影相關
   grep -r "rgba(0, 0, 0," web/static/css/ | wc -l
   
   # 背景相關  
   grep -r "rgba(255, 255, 255," web/static/css/ | wc -l
   
   # 品牌色相關
   grep -r "rgba(79, 70, 229," web/static/css/ | wc -l
   ```

3. **建立轉換對照表**
   ```markdown
   | 硬編碼值 | 使用場景 | 建議令牌 | 檔案數量 |
   |---------|---------|----------|----------|
   | rgba(0, 0, 0, 0.1) | 陰影 | var(--shadow-light) | 15 |
   | rgba(255, 255, 255, 0.9) | 背景 | var(--surface-overlay) | 12 |
   | rgba(79, 70, 229, 0.2) | 焦點 | var(--focus-ring) | 8 |
   ```

#### Step 2: 擴展設計令牌系統 (4-5小時)

1. **分析缺失的令牌**
   ```css
   /* 在 colors-v2.css 中添加缺失的令牌 */
   
   /* 透明度級別系統化 */
   --alpha-1: 0.05;
   --alpha-2: 0.1; 
   --alpha-3: 0.15;
   --alpha-4: 0.2;
   --alpha-5: 0.25;
   --alpha-6: 0.3;
   
   /* 陰影系統令牌 */
   --shadow-color-light: rgb(var(--shadow-rgb) / var(--alpha-2));
   --shadow-color-medium: rgb(var(--shadow-rgb) / var(--alpha-4));
   --shadow-color-heavy: rgb(var(--shadow-rgb) / var(--alpha-6));
   ```

2. **建立語義化別名**
   ```css
   /* 常用組合的語義化別名 */
   --overlay-light: rgba(255, 255, 255, 0.9);    /* → var(--surface-overlay-light) */
   --overlay-medium: rgba(255, 255, 255, 0.8);   /* → var(--surface-overlay-medium) */
   --backdrop-light: rgba(0, 0, 0, 0.4);         /* → var(--backdrop-light) */
   --backdrop-heavy: rgba(0, 0, 0, 0.6);         /* → var(--backdrop-heavy) */
   ```

3. **創建專用顏色令牌**
   ```css
   /* Glass morphism 專用 */
   --glass-bg-light: rgba(255, 255, 255, 0.85);
   --glass-bg-medium: rgba(255, 255, 255, 0.75);
   --glass-border: rgba(255, 255, 255, 0.3);
   
   /* 互動狀態專用 */
   --hover-overlay-light: rgba(0, 0, 0, 0.05);
   --hover-overlay-medium: rgba(0, 0, 0, 0.1);
   --active-overlay: rgba(0, 0, 0, 0.15);
   ```

#### Step 3: 系統化替換 (8-10小時)

1. **按文件優先級替換**
   
   **高優先級文件 (首先處理):**
   ```bash
   # 設計令牌文件
   web/static/css/design-system/01-tokens/colors-v2.css
   web/static/css/design-system/01-tokens/shadows-v2.css
   web/static/css/design-system/01-tokens/glass.css
   ```
   
   **中優先級文件:**
   ```bash
   # 核心組件
   web/static/css/design-system/03-components/buttons.css
   web/static/css/design-system/03-components/cards.css
   web/static/css/design-system/03-components/modals.css
   ```
   
   **低優先級文件:**
   ```bash
   # 頁面專用CSS
   web/static/css/pages/*.css
   ```

2. **建立替換腳本**
   ```bash
   #!/bin/bash
   # rgba_replace.sh - 自動化替換腳本
   
   # 陰影相關替換
   sed -i 's/rgba(0, 0, 0, 0\.1)/rgb(var(--shadow-rgb) \/ var(--alpha-2))/g' $1
   sed -i 's/rgba(0, 0, 0, 0\.2)/rgb(var(--shadow-rgb) \/ var(--alpha-4))/g' $1
   
   # 背景相關替換
   sed -i 's/rgba(255, 255, 255, 0\.9)/var(--surface-overlay-light)/g' $1
   sed -i 's/rgba(255, 255, 255, 0\.8)/var(--surface-overlay-medium)/g' $1
   
   # 品牌色相關替換
   sed -i 's/rgba(79, 70, 229, 0\.2)/var(--focus-ring)/g' $1
   ```

3. **手動驗證複雜情況**
   ```css
   /* 複雜的組合需要手動處理 */
   background: linear-gradient(135deg, 
     rgba(99, 102, 241, 0.03) 0%, 
     transparent 100%);
   /* 轉換為 */
   background: linear-gradient(135deg, 
     rgb(var(--accent-rgb) / var(--alpha-1)) 0%, 
     transparent 100%);
   ```

#### Step 4: 驗證和測試 (3-4小時)

1. **視覺回歸測試**
   ```bash
   # 截圖對比工具
   npm install -g backstopjs
   backstop init
   # 配置所有頁面的視覺測試
   ```

2. **顏色一致性檢查**
   ```bash
   # 確認不再有rgba硬編碼
   grep -r "rgba(" web/static/css/ | grep -v "var("
   
   # 檢查是否有遺漏的硬編碼
   grep -r "#[0-9a-fA-F]\{3,6\}" web/static/css/
   ```

3. **功能測試清單**
   - [ ] 所有按鈕hover/active狀態
   - [ ] 模態框背景和陰影
   - [ ] 卡片組件陰影效果
   - [ ] Glass morphism效果
   - [ ] 焦點指示器
   - [ ] 載入動畫
   - [ ] 通知和提示

#### Step 5: 工具和流程建立 (2-3小時)

1. **建立檢查工具**
   ```javascript
   // css-color-audit.js
   const fs = require('fs');
   const glob = require('glob');
   
   const rgbaPattern = /rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)/g;
   
   glob('web/static/css/**/*.css', (err, files) => {
     files.forEach(file => {
       const content = fs.readFileSync(file, 'utf8');
       const matches = content.match(rgbaPattern);
       if (matches) {
         console.log(`${file}: ${matches.length} rgba values found`);
       }
     });
   });
   ```

2. **設置pre-commit hook**
   ```bash
   #!/bin/sh
   # .git/hooks/pre-commit
   
   # 檢查是否有新的rgba硬編碼
   if git diff --cached --name-only | grep '\.css$' | xargs grep -l 'rgba(' 2>/dev/null; then
     echo "Error: Found rgba() hardcoded values in CSS files"
     echo "Please use design tokens instead"
     exit 1
   fi
   ```

3. **更新文檔**
   ```markdown
   # 色彩使用指南
   
   ## 禁止使用
   - `rgba()` 硬編碼值
   - `#hexcolor` 硬編碼值
   
   ## 建議使用
   - `var(--primary)` 語義化令牌
   - `rgb(var(--accent-rgb) / var(--alpha-2))` 組合令牌
   ```

### 🎯 替換對照參考表

| 常見硬編碼 | 建議替換 | 使用場景 |
|-----------|----------|----------|
| `rgba(0, 0, 0, 0.05)` | `rgb(var(--shadow-rgb) / var(--alpha-1))` | 極淺陰影 |
| `rgba(0, 0, 0, 0.1)` | `rgb(var(--shadow-rgb) / var(--alpha-2))` | 輕陰影 |
| `rgba(0, 0, 0, 0.2)` | `rgb(var(--shadow-rgb) / var(--alpha-4))` | 中陰影 |
| `rgba(255, 255, 255, 0.9)` | `var(--surface-overlay-light)` | 淺色背景 |
| `rgba(255, 255, 255, 0.8)` | `var(--surface-overlay-medium)` | 中透明背景 |
| `rgba(79, 70, 229, 0.2)` | `var(--focus-ring)` | 焦點指示 |
| `rgba(16, 185, 129, 0.1)` | `var(--success-subtle)` | 成功狀態背景 |
| `rgba(239, 68, 68, 0.1)` | `var(--error-subtle)` | 錯誤狀態背景 |

### ⚠️ 特殊注意事項

1. **向後兼容性**: 確保在添加新令牌時不破壞現有功能
2. **暗色模式**: 所有新令牌都要有暗色模式對應值
3. **瀏覽器支援**: 某些舊瀏覽器可能需要fallback
4. **性能影響**: CSS變量可能略微影響性能，但可接受

### 📊 預期成果

**清理前:**
- rgba硬編碼: 290個
- 維護困難: 修改顏色需要多處更新
- 一致性差: 相似顏色有微小差異

**清理後:**
- rgba硬編碼: 0個
- 維護簡單: 修改令牌即可全局更新
- 一致性好: 統一的色彩系統

### 📝 Execution Notes

**進度追蹤:**
- [ ] Step 1: 盤點分類完成
- [ ] Step 2: 令牌系統擴展完成  
- [ ] Step 3: 替換工作完成 (XX/290)
- [ ] Step 4: 驗證測試完成
- [ ] Step 5: 工具流程建立完成

**品質檢查:**
- [ ] 所有頁面視覺正常
- [ ] 暗色模式正常
- [ ] 響應式設計正常
- [ ] 無rgba硬編碼殘留

### 🔍 Review Comments (For Reviewer)

(審查者確認所有rgba硬編碼已清理，色彩系統一致性良好)