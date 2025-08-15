# TASK-35-04: 硬編碼尺寸清理 - 轉換435個px值為間距系統

- **Priority**: 🟡 MEDIUM  
- **Estimated Time**: 20-30 hours
- **Related Components**: 全系統CSS文件，36個文件含有px硬編碼
- **Parent Task**: TASK-35-main.md

---

### 🎯 Task Objective

系統性地將所有硬編碼的像素值（435個px用法）轉換為設計令牌的間距系統，建立一致的尺寸規範，提高響應式設計和維護效率。

### ✅ Acceptance Criteria

- [ ] **完全清除**: 435個px硬編碼值轉換為CSS變量或相對單位
- [ ] **間距系統完善**: 確保所有常用尺寸都有對應令牌
- [ ] **響應式優化**: 改善移動設備和不同螢幕的適應性
- [ ] **一致性驗證**: 相同用途的尺寸使用統一標準
- [ ] **視覺回歸測試**: 所有頁面布局保持正確
- [ ] **性能提升**: 減少重複計算，優化渲染性能
- [ ] **文檔更新**: 建立間距使用指南

### 📊 問題統計分析

**硬編碼分佈:**
```bash
# 發現的435個px用法分佈在36個文件中
/web/static/css/design-system/01-tokens/spacing.css: 24個
/web/static/css/design-system/01-tokens/shadows-v2.css: 59個
/web/static/css/design-system/01-tokens/breakpoints.css: 12個
/web/static/css/design-system/03-components/cards.css: 5個
/web/static/css/pages/settings.css: 60個
# ... 其他31個文件
```

**常見硬編碼模式:**
```css
/* 間距相關 */
padding: 12px;               /* ~80個 */
margin: 16px;                /* ~70個*/
gap: 8px;                    /* ~50個*/

/* 尺寸相關 */
width: 24px;                 /* ~40個 */
height: 48px;                /* ~35個*/
border-radius: 8px;          /* ~30個*/

/* 陰影和邊框 */
box-shadow: 0 2px 8px;       /* ~25個 */
border-width: 1px;           /* ~20個*/

/* 字體相關 */
font-size: 14px;             /* ~15個 */
line-height: 20px;           /* ~12個 */

/* 其他 */
transform: translateY(-2px); /* ~8個 */
```

### 📋 具體執行步驟

#### Step 1: 全面盤點和分類 (4-5小時)

1. **生成完整清單**
   ```bash
   # 創建詳細的px使用清單
   grep -rn "\d\+px" web/static/css/ > px_audit.txt
   
   # 按類型分組
   grep -r "padding.*px" web/static/css/ | wc -l    # 間距
   grep -r "margin.*px" web/static/css/ | wc -l     # 外邊距
   grep -r "width.*px" web/static/css/ | wc -l      # 寬度
   grep -r "height.*px" web/static/css/ | wc -l     # 高度
   grep -r "font-size.*px" web/static/css/ | wc -l  # 字體
   ```

2. **分析px值分佈頻率**
   ```bash
   # 統計最常用的px值
   grep -ro "\d\+px" web/static/css/ | sort | uniq -c | sort -nr
   
   # 預期結果類似:
   #  45 8px
   #  38 16px  
   #  32 12px
   #  28 24px
   #  20 4px
   ```

3. **建立分類對照表**
   ```markdown
   | px值 | 使用場景 | 建議令牌 | 出現次數 |
   |------|---------|----------|----------|
   | 4px  | 小間距   | var(--space-1) | 20 |
   | 8px  | 基礎間距 | var(--space-2) | 45 |
   | 12px | 中間距   | var(--space-3) | 32 |
   | 16px | 標準間距 | var(--space-4) | 38 |
   | 24px | 大間距   | var(--space-6) | 28 |
   ```

#### Step 2: 完善間距令牌系統 (3-4小時)

1. **檢查現有spacing.css覆蓋度**
   ```css
   /* 確認現有的間距令牌 */
   :root {
     --space-0: 0;
     --space-1: 0.25rem;    /* 4px */
     --space-2: 0.5rem;     /* 8px */
     --space-3: 0.75rem;    /* 12px */
     --space-4: 1rem;       /* 16px */
     --space-5: 1.25rem;    /* 20px */
     --space-6: 1.5rem;     /* 24px */
     /* ... 檢查是否有遺漏的尺寸 */
   }
   ```

2. **添加缺失的尺寸令牌**
   ```css
   /* 在spacing.css中添加常用但缺失的尺寸 */
   
   /* 微調間距 */
   --space-0-5: 0.125rem;   /* 2px - 微調用 */
   --space-1-5: 0.375rem;   /* 6px - 介於4px和8px */
   --space-2-5: 0.625rem;   /* 10px - 介於8px和12px */
   
   /* 大尺寸間距 */
   --space-14: 3.5rem;      /* 56px */
   --space-16: 4rem;        /* 64px */
   --space-20: 5rem;        /* 80px */
   --space-24: 6rem;        /* 96px */
   --space-32: 8rem;        /* 128px */
   ```

3. **建立專用尺寸令牌**
   ```css
   /* 組件專用尺寸 */
   --btn-height-sm: 2rem;     /* 32px */
   --btn-height-md: 2.5rem;   /* 40px */
   --btn-height-lg: 3rem;     /* 48px */
   
   /* 圖標尺寸 */
   --icon-xs: 0.75rem;        /* 12px */
   --icon-sm: 1rem;           /* 16px */
   --icon-md: 1.5rem;         /* 24px */
   --icon-lg: 2rem;           /* 32px */
   --icon-xl: 3rem;           /* 48px */
   
   /* 邊框和陰影 */
   --border-width-thin: 1px;
   --border-width-normal: 2px;
   --border-width-thick: 4px;
   
   /* 圓角系統 */
   --radius-xs: 0.125rem;     /* 2px */
   --radius-sm: 0.25rem;      /* 4px */  
   --radius-md: 0.5rem;       /* 8px */
   --radius-lg: 0.75rem;      /* 12px */
   --radius-xl: 1rem;         /* 16px */
   --radius-2xl: 1.5rem;      /* 24px */
   --radius-full: 9999px;     /* 圓形 */
   ```

#### Step 3: 系統化替換工作 (12-15小時)

1. **按文件類型分批處理**

   **Phase 1: 設計令牌文件 (3小時)**
   ```bash
   # 優先處理tokens文件，確保基礎正確
   web/static/css/design-system/01-tokens/spacing.css
   web/static/css/design-system/01-tokens/shadows-v2.css  
   web/static/css/design-system/01-tokens/dimensions.css
   web/static/css/design-system/01-tokens/typography.css
   ```

   **Phase 2: 組件文件 (4-5小時)**
   ```bash
   # 處理所有組件CSS
   web/static/css/design-system/03-components/*.css
   web/static/css/components/batch-operations.css
   ```

   **Phase 3: 頁面文件 (4-5小時)**
   ```bash
   # 處理頁面專用CSS
   web/static/css/pages/*.css
   ```

   **Phase 4: 布局文件 (1-2小時)**
   ```bash
   # 處理布局相關
   web/static/css/design-system/04-layouts/*.css
   web/static/css/design-system/02-base/reset.css
   ```

2. **建立替換映射腳本**
   ```bash
   #!/bin/bash
   # px_replace.sh - 智能px替換腳本
   
   # 間距替換
   sed -i 's/padding: 4px/padding: var(--space-1)/g' $1
   sed -i 's/padding: 8px/padding: var(--space-2)/g' $1
   sed -i 's/margin: 12px/margin: var(--space-3)/g' $1
   sed -i 's/gap: 16px/gap: var(--space-4)/g' $1
   
   # 尺寸替換
   sed -i 's/width: 24px/width: var(--icon-md)/g' $1
   sed -i 's/height: 32px/height: var(--btn-height-sm)/g' $1
   
   # 圓角替換
   sed -i 's/border-radius: 4px/border-radius: var(--radius-sm)/g' $1
   sed -i 's/border-radius: 8px/border-radius: var(--radius-md)/g' $1
   ```

3. **處理複雜情況**
   ```css
   /* 複合屬性需要手動處理 */
   
   /* Before */
   padding: 12px 16px 8px 12px;
   
   /* After */
   padding: var(--space-3) var(--space-4) var(--space-2) var(--space-3);
   
   /* Before */
   box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
   
   /* After */
   box-shadow: 0 var(--shadow-offset-sm) var(--shadow-blur-md) var(--shadow-light);
   ```

#### Step 4: 響應式改善 (3-4小時)

1. **檢查移動設備適應性**
   ```css
   /* 將固定px改為響應式 */
   
   /* Before */
   .container {
     max-width: 1200px;
     padding: 24px;
   }
   
   /* After */
   .container {
     max-width: var(--container-max-width);
     padding: var(--space-6);
   }
   
   @media (max-width: var(--breakpoint-md)) {
     .container {
       padding: var(--space-4);
     }
   }
   ```

2. **優化字體尺寸**
   ```css
   /* 使用相對單位替換固定px */
   
   /* Before */
   h1 { font-size: 32px; }
   h2 { font-size: 24px; }
   p { font-size: 16px; }
   
   /* After */
   h1 { font-size: var(--text-2xl); }
   h2 { font-size: var(--text-xl); }
   p { font-size: var(--text-base); }
   ```

3. **建立斷點系統**
   ```css
   /* 在breakpoints.css中確保完整覆蓋 */
   :root {
     --breakpoint-xs: 480px;
     --breakpoint-sm: 640px;
     --breakpoint-md: 768px;  
     --breakpoint-lg: 1024px;
     --breakpoint-xl: 1280px;
     --breakpoint-2xl: 1536px;
   }
   ```

#### Step 5: 驗證和優化 (3-4小時)

1. **視覺回歸測試**
   ```bash
   # 自動化視覺測試
   npm run test:visual
   
   # 手動檢查關鍵頁面
   # - 桌面版 (1920x1080)
   # - 平板版 (768x1024)  
   # - 手機版 (375x667)
   ```

2. **性能測試**
   ```bash
   # 測試CSS載入和渲染性能
   lighthouse http://localhost:8000 --only-categories=performance
   
   # 檢查CSS檔案大小變化
   du -sh web/static/css/ # before vs after
   ```

3. **硬編碼檢查**
   ```bash
   # 確認無遺漏的px硬編碼
   grep -r "\d\+px" web/static/css/ | grep -v "var(" | grep -v "breakpoint"
   
   # 檢查是否有新的硬編碼模式
   grep -r "rem\|em" web/static/css/ | grep -E "\d+\.?\d*(rem|em)" | head -20
   ```

#### Step 6: 文檔和工具建立 (2-3小時)

1. **建立間距使用指南**
   ```markdown
   # 間距系統使用指南
   
   ## 基礎間距
   - `var(--space-1)` (4px): 微小間距，按鈕內邊距
   - `var(--space-2)` (8px): 小間距，圖標間距
   - `var(--space-4)` (16px): 標準間距，表單間距
   - `var(--space-6)` (24px): 大間距，卡片間距
   
   ## 組件專用
   - `var(--btn-height-md)`: 標準按鈕高度
   - `var(--icon-md)`: 標準圖標尺寸
   - `var(--radius-md)`: 標準圓角
   ```

2. **設置檢查工具**
   ```javascript
   // css-spacing-audit.js
   const pxPattern = /\d+px/g;
   const allowedPx = ['1px', '2px']; // 邊框等特殊情況
   
   function auditSpacing(cssContent) {
     const matches = cssContent.match(pxPattern) || [];
     return matches.filter(match => !allowedPx.includes(match));
   }
   ```

3. **更新pre-commit檢查**
   ```bash
   # 添加到.git/hooks/pre-commit
   if git diff --cached --name-only | grep '\.css$' | xargs grep -l '\d\+px' 2>/dev/null; then
     echo "Warning: Found px hardcoded values. Consider using design tokens."
     # 不阻止提交，只警告
   fi
   ```

### 🎯 替換優先級參考

| px值範圍 | 替換策略 | 對應令牌 | 處理優先級 |
|---------|----------|----------|-----------|
| 1-2px | 保留 | border-width | 低 |
| 4px | 替換 | var(--space-1) | 高 |
| 8px | 替換 | var(--space-2) | 高 |
| 12px | 替換 | var(--space-3) | 高 |
| 16px | 替換 | var(--space-4) | 高 |
| 24px | 替換 | var(--space-6) | 高 |
| 32px+ | 檢查語義 | 組件專用令牌 | 中 |
| 特殊值 | 分析用途 | 建立新令牌 | 中 |

### ⚠️ 特殊注意事項

1. **保留必要的px值**
   ```css
   /* 某些情況下px是必要的 */
   border-width: 1px;           /* 保留 - 邊框基準 */
   transform: translateX(1px);  /* 保留 - 微調位移 */
   box-shadow: 0 0 0 1px;      /* 保留 - 邊框效果 */
   ```

2. **響應式考慮**
   ```css
   /* 確保間距在不同設備上合理 */
   @media (max-width: var(--breakpoint-sm)) {
     .container {
       padding: var(--space-4); /* 手機上減少間距 */
     }
   }
   ```

3. **瀏覽器兼容性**
   ```css
   /* 提供fallback支援 */
   .element {
     padding: 16px; /* fallback */
     padding: var(--space-4);
   }
   ```

### 📊 預期成果

**清理前:**
- px硬編碼: 435個
- 響應式: 部分支援，固定尺寸多
- 維護性: 修改間距需要多處更新
- 一致性: 相似用途的間距不統一

**清理後:**
- px硬編碼: <20個 (僅保留必要的邊框等)
- 響應式: 完整支援，彈性布局
- 維護性: 統一令牌管理，易於調整
- 一致性: 語義化間距系統

### 📝 Execution Notes

**進度追蹤:**
- [ ] Step 1: 盤點分類完成 (XX/435個)
- [ ] Step 2: 間距系統完善
- [ ] Step 3: 替換工作完成 (XX/435個)
- [ ] Step 4: 響應式改善完成
- [ ] Step 5: 驗證測試通過
- [ ] Step 6: 文檔工具建立

**各階段檢查點:**
- [ ] Phase 1: 設計令牌文件 (XX個px處理)
- [ ] Phase 2: 組件文件 (XX個px處理)
- [ ] Phase 3: 頁面文件 (XX個px處理)  
- [ ] Phase 4: 布局文件 (XX個px處理)

### 🔍 Review Comments (For Reviewer)

(審查者確認px硬編碼基本清理，間距系統完整，響應式設計改善)