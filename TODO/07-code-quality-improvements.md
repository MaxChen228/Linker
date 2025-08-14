# 07. 代碼品質改進計劃

## 優先級: MEDIUM 🟡
## 預估時間: 4-6 小時
## 狀態: 🚧 IN_PROGRESS [@agent-2 at:2025-08-14 17:00]

### 背景
開發工作流檢查發現多個代碼品質問題，需要系統性地解決以提升代碼穩定性和可維護性。

**2025-08-14 實際狀況：**
- Ruff 檢查發現 1143 個問題（大量重複，主要是異常命名和 import 順序）
- Pytest 執行結果：36 failed, 64 passed, 13 errors
- 主要問題集中在 test_exceptions.py 的導入錯誤

### 子任務清單

#### A. Ruff Linting 問題修復 (1.5小時)
- [x] 修復異常類命名問題
  - [x] 確認所有異常類都以 Error 結尾（已正確）
  - [x] APIError, DataError, ValidationError 等都已正確命名
  
- [x] 修復 import 順序問題
  - [x] `core/database/connection.py:334` - 已修復 weakref import
  - [x] `scripts/` 目錄下的 E402 錯誤（合理，保留）
  
- [ ] 修復異常處理問題
  - [ ] 添加 `from err` 到所有異常重拋出
  - [ ] 使用 `contextlib.suppress` 替代空的 try-except
  
- [ ] 更新過時的類型註解
  - [ ] 將 `typing.Dict` 改為 `dict`
  - [ ] 將 `typing.List` 改為 `list`
  - [ ] 將 `typing.Tuple` 改為 `tuple`

#### B. 測試套件修復 (2小時)
- [ ] 修復 `test_exceptions.py` 導入問題
  - [ ] 移除不存在的類別導入
  - [ ] 更新測試以符合當前實現
  - [ ] 確保所有測試可以執行
  
- [ ] 修復失敗的測試
  - [ ] 分析 37 個失敗測試的原因
  - [ ] 修復或移除過時的測試
  - [ ] 確保測試覆蓋率達到 90%
  
- [ ] 清理未使用的測試代碼
  - [ ] 移除 `test_environment.py` 中未使用的導入
  - [ ] 清理 mock 和 fixture

#### C. 代碼優化 (1.5小時)
- [ ] 簡化條件判斷
  - [ ] 使用三元運算符替代簡單的 if-else
  - [ ] 合併嵌套的 with 語句
  
- [ ] 移除未使用的變數
  - [ ] `scripts/migrate_data.py:159` - conn 變數
  - [ ] 其他 F841 錯誤
  
- [ ] 優化測試斷言
  - [ ] 避免使用盲目的 Exception 斷言
  - [ ] 使用更具體的異常類型

#### D. 文檔字串完善 (1小時)
- [ ] 為所有公開函數添加 Google style docstrings
- [ ] 確保參數和返回值都有說明
- [ ] 添加使用範例到複雜函數

### 驗收標準
1. `ruff check .` 無錯誤（或只有可接受的警告）
2. `ruff format .` 完成格式化
3. `pytest` 所有測試通過
4. 測試覆蓋率 >= 90%
5. 無硬編碼值
6. 類型註解完整

### 測試命令
```bash
# 代碼品質檢查
ruff check .
ruff format .

# 測試執行
pytest -v
pytest --cov=core --cov=web --cov-report=term-missing

# 類型檢查（如果有 mypy）
mypy core web --ignore-missing-imports
```

### 預期成果
- 代碼品質顯著提升
- 減少潛在 bug
- 提高代碼可維護性
- 符合 Python 最佳實踐

### 相關文件
- `core/exceptions.py` - 異常類命名問題
- `tests/test_exceptions.py` - 測試導入問題
- `scripts/` - import 順序問題
- `.ruff.toml` - Ruff 配置文件

### 注意事項
1. 異常類重命名可能影響其他模組，需要全局搜索替換
2. 修復測試時要確保不是假裝通過
3. 使用 `--unsafe-fixes` 選項時要仔細檢查變更