# 📚 版本遷移系統文檔

## 🎯 問題背景

專案存在版本管理混亂的問題：
1. **版本不一致**：`pattern_enrichment.py` 輸出 v2.0，但 `patterns_enriched_complete.json` 標記為 v3.0
2. **缺失版本管理**：沒有統一的版本檢查和遷移機制
3. **資料結構變更無法追蹤**：從簡單陣列到含元數據的物件結構，缺乏遷移路徑

## 🏗️ 解決方案架構

### 1. 版本管理器 (`core/version_manager.py`)

統一管理所有資料檔案的版本控制與遷移：

```python
# 版本定義
class DataVersion(Enum):
    V1_0 = "1.0"  # 原始格式（無版本標記）
    V2_0 = "2.0"  # 第一次擴充
    V3_0 = "3.0"  # 完整擴充版
    V3_1 = "3.1"  # 修正版本不一致問題後的版本
```

### 2. 支援的檔案類型

- **patterns_basic**: `grammar_patterns.json` - 原始句型資料
- **patterns_enriched**: `patterns_enriched_complete.json` - 擴充後的句型資料
- **knowledge**: `knowledge.json` - 知識點資料
- **practice_log**: `practice_log.json` - 練習記錄

### 3. 版本遷移路徑

```
grammar_patterns.json:
  無版本 → v1.0 → v2.0 → v3.0 → v3.1

patterns_enriched_complete.json:
  v2.0 → v3.0 → v3.1

knowledge.json:
  無版本 → v1.0 → v2.0
```

## 🔧 使用方式

### 命令行工具

```bash
# 檢查版本狀態
python -m core.version_manager check

# 執行版本遷移
python -m core.version_manager migrate

# 備份所有檔案
python -m core.version_manager backup
```

### 程式碼整合

```python
from core.version_manager import VersionManager

# 創建版本管理器
manager = VersionManager()

# 檢查並自動遷移
results = manager.check_and_migrate_all()

# 獲取版本報告
report = manager.get_version_report()
```

## 📊 版本遷移內容

### v1.0 → v2.0 (句型資料)
- 從純陣列轉換為含元數據的物件結構
- 新增 `version`、`generated_at`、`total_patterns` 欄位

### v2.0 → v3.0 (句型資料)
- 新增 `enrichment_summary` 欄位
- 包含 `completed`、`failed`、`model`、`temperature` 等統計資訊

### v3.0 → v3.1 (句型資料)
- 標準化所有欄位
- 確保每個句型都有必要的基礎欄位
- 新增 `last_migration` 時間戳記

## ✅ 實施成果

### 測試結果
```
=== 版本遷移測試 ===
✓ v1.0 -> v2.0: 添加版本標記和元數據
✓ v2.0 -> v3.0: 添加 enrichment_summary
✓ v3.0 -> v3.1: 標準化欄位

遷移結果：
  grammar_patterns.json: ✅ 已遷移
  patterns_enriched_complete.json: ⏭️ 已是最新
  knowledge.json: ✅ 已遷移
  practice_log.json: ⏭️ 已是最新
```

### 檔案結構變化

**遷移前 (grammar_patterns.json)**：
```json
[
  {
    "id": "GP001",
    "category": "強調用法",
    "pattern": "It is ~ that ~",
    ...
  }
]
```

**遷移後 (v3.1)**：
```json
{
  "version": "3.1",
  "generated_at": "2025-08-11T09:37:33.666669",
  "total_patterns": 111,
  "enrichment_summary": {...},
  "last_migration": "2025-08-11T09:37:33.666734",
  "patterns": [...]
}
```

## 🔐 安全機制

1. **自動備份**：遷移前自動備份到 `data/backups/` 目錄
2. **版本檢測**：自動識別檔案版本，避免重複遷移
3. **錯誤處理**：遷移失敗時保留原始檔案
4. **進度追蹤**：支援斷點續傳（用於 pattern enrichment）

## 🚀 後續優化建議

1. **整合到啟動流程**：在應用啟動時自動檢查和遷移
2. **版本相容性檢查**：在讀取資料前驗證版本
3. **回滾機制**：支援版本降級和回滾
4. **資料驗證**：加強遷移後的資料完整性檢查
5. **UI 介面**：提供圖形化的版本管理介面

## 📝 注意事項

- 遷移是不可逆的，請確保備份重要資料
- 建議在非生產環境先測試遷移
- 遷移後需要重啟應用以載入新格式資料
- 若遇到問題，可從 `data/backups/` 目錄還原備份