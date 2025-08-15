# TASK-35-01: Critical Cleanup - 清理調試文件和完成遷移

- **Priority**: 🔴 CRITICAL
- **Estimated Time**: 4-6 hours
- **Related Components**: web/static/css/design-system/, web/static/css/debug-z-index.css
- **Parent Task**: TASK-35-main.md

---

### 🎯 Task Objective

清理生產環境中不應該存在的調試文件，完成未完成的遷移工作，確保CSS架構的完整性和一致性。這是整個技術債清理的第一步，必須首先完成。

### ✅ Acceptance Criteria

- [ ] **調試文件清理**: 移除 `debug-z-index.css` 文件
- [ ] **模板引用清理**: 檢查並移除所有對調試CSS的引用
- [ ] **陰影遷移完成**: 刪除 `shadows-migration.css` 文件
- [ ] **遷移驗證**: 確認所有陰影系統正常工作
- [ ] **版本文件清理**: 處理 `colors-v2.css`, `shadows-v2.css` 命名
- [ ] **測試通過**: 所有頁面視覺效果正常
- [ ] **文件大小減少**: CSS總大小減少5-10%

### 📋 具體執行步驟

#### Step 1: 調試文件清理 (1小時)

1. **檢查調試文件使用情況**
   ```bash
   grep -r "debug-z-index" web/templates/
   grep -r "debug-z-index" web/static/css/
   ```

2. **移除調試CSS文件**
   ```bash
   rm web/static/css/debug-z-index.css
   ```

3. **清理相關引用**
   - 檢查 `base.html` 和所有模板
   - 移除任何 `debug-z-index` 的引用

#### Step 2: 陰影遷移完成 (2-3小時)

1. **分析遷移文件依賴**
   ```bash
   grep -r "shadows-migration" web/static/css/
   grep -r "shadow-color" web/static/css/
   ```

2. **驗證新陰影系統**
   - 檢查 `shadows-v2.css` 是否涵蓋所有用法
   - 測試所有組件的陰影效果

3. **移除遷移文件**
   ```bash
   rm web/static/css/design-system/01-tokens/shadows-migration.css
   ```

4. **更新 design-system/index.css**
   - 移除對 `shadows-migration.css` 的引用

#### Step 3: 版本文件重命名 (1小時)

1. **重命名v2文件**
   ```bash
   # 重命名為標準名稱
   mv web/static/css/design-system/01-tokens/colors-v2.css \
      web/static/css/design-system/01-tokens/colors.css
   
   mv web/static/css/design-system/01-tokens/shadows-v2.css \
      web/static/css/design-system/01-tokens/shadows.css
   ```

2. **更新import引用**
   - 修改 `design-system/index.css` 中的引用
   - 確保所有 `@import` 路徑正確

#### Step 4: 清理驗證 (1小時)

1. **功能測試**
   - 瀏覽所有頁面確認視覺效果
   - 特別檢查陰影和z-index效果

2. **文件大小檢查**
   ```bash
   du -sh web/static/css/ # 記錄清理前後大小
   ```

3. **代碼品質檢查**
   ```bash
   ruff check .
   ruff format .
   ```

### 🎯 相關文件清單

**需要檢查的文件:**
- `web/static/css/debug-z-index.css` (刪除)
- `web/static/css/design-system/01-tokens/shadows-migration.css` (刪除)
- `web/static/css/design-system/01-tokens/colors-v2.css` (重命名)
- `web/static/css/design-system/01-tokens/shadows-v2.css` (重命名)
- `web/static/css/design-system/index.css` (更新引用)
- `web/templates/base.html` (檢查引用)

**需要測試的頁面:**
- `/` (首頁)
- `/practice` (練習頁面)
- `/patterns` (文法句型)
- `/knowledge` (知識點)
- `/calendar` (學習日曆)

### ⚠️ 注意事項

1. **備份策略**: 開始前先提交當前狀態
2. **漸進式清理**: 一次處理一個文件，立即測試
3. **視覺檢查**: 每步完成後檢查UI是否正常
4. **回滾準備**: 如果有問題立即回滾

### 🔧 工具和命令

```bash
# 搜尋文件引用
grep -r "filename" web/
find web/ -name "*.css" -exec grep -l "pattern" {} \;

# 檢查CSS語法
npx stylelint web/static/css/**/*.css

# 測試載入
curl -I http://localhost:8000/static/css/design-system/index.css
```

### 📊 預期成果

**清理前:**
- 調試文件: 1個 (debug-z-index.css)
- 遷移文件: 1個 (shadows-migration.css)
- 版本文件: 2個 (-v2後綴)
- CSS總大小: ~XXXkB

**清理後:**
- 調試文件: 0個
- 遷移文件: 0個
- 版本文件: 0個 (統一命名)
- CSS總大小: 減少5-10%

### 📝 Execution Notes

**執行過程記錄:**
- 開始時間: 
- 遇到的問題:
- 解決方案:
- 完成時間:
- 實際vs預估工時:

### 🔍 Review Comments (For Reviewer)

(審查者確認每個檔案都已正確清理，無殘留引用)