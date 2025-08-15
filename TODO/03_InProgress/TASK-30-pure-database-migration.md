# TASK-30: 純 Database 系統重構專案 (主任務)

- **優先級**: 🔴 CRITICAL
- **預計時間**: 7-10 天
- **關聯組件**: core/database/, web/, tests/, scripts/, docs/
- **父任務**: 無 (主要架構重構)
- **子任務**: TASK-30A 至 TASK-30M (共13個子任務)

---

## 🎯 任務目標

將 Linker 系統從雙後端架構（JSON + Database）重構為純 Database 架構，為後續知識圖譜功能做準備。完全移除 JSON 依賴和降級邏輯，建立統一的資料庫資料管理系統。

**🚀 最終目標**: 建立一個完全基於 PostgreSQL 的穩定、高效能、可擴展的英語學習平台，為知識圖譜功能奠定堅實基礎。

## ✅ 驗收標準 (Acceptance Criteria)

### 主要標準
- [ ] 移除所有 JSON 依賴（42個檔案中的相關邏輯）
- [ ] 刪除超過 50 處 `_legacy_manager` 引用
- [ ] 移除 `DatabaseToJsonFallback` 降級策略
- [ ] 重構 `DatabaseAdapter` 為純資料庫版本
- [ ] 建立資料庫初始化和 seed data 系統
- [ ] 所有測試通過且覆蓋率保持 >90%

### 技術標準
- [ ] `grep -r "import json" core/` 無相關結果
- [ ] 所有 web routes 使用統一的資料庫 API
- [ ] 錯誤處理不再包含 JSON 降級路徑
- [ ] 開發環境支援一鍵資料庫啟動
- [ ] CI/CD 包含資料庫服務配置

### 準備知識圖譜
- [ ] Schema 支援關係型資料結構
- [ ] 預留圖查詢 API 接口
- [ ] 標籤系統準備擴展為圖節點

## 📋 實施階段與子任務分解

### 🗑️ 階段 1: 移除 JSON 依賴 (2-3 天)
**子任務:**
- [x] **TASK-30B**: 清理 core/knowledge.py 和 JSON 模組 ✅ 2025-01-15
  - 重構 KnowledgeManager 為純資料庫版本
  - 創建 core/models.py 解決循環導入
  - 保留 knowledge_json_backup.py 維持向後兼容
  - 移除 DatabaseToJsonFallback 策略
- [x] **TASK-30C**: 重構 web/dependencies.py 移除條件載入 ✅ 2025-01-15
  - 移除 USE_DATABASE 環境變數檢查
  - 簡化為純資料庫依賴注入
- [x] **TASK-30D**: 簡化 DatabaseAdapter 移除降級邏輯 ✅ 2025-01-15
  - 創建 SimplifiedDatabaseAdapter 替代複雜的 adapter.py
  - 提供相同的公開 API，內部使用 DatabaseKnowledgeManager
  - 保留向後兼容的同步方法
- [x] **TASK-30E**: 移除 fallback_strategies JSON 策略 ✅ 2025-01-15
  - 清理註釋和文檔
  - 移除未使用的 json import

### 🛠️ 階段 2: 錯誤處理重構 (1-2 天)
**子任務:**
- [ ] **TASK-30F**: 創建新的 DatabaseErrorHandler
- [ ] **TASK-30G**: 重新設計 fallback 策略

### 💾 階段 3: 資料初始化 (1 天)
**子任務:**
- [ ] **TASK-30H**: 創建 seed data 和初始化系統

### 🧪 階段 4: 測試環境重構 (1-2 天)
**子任務:**
- [ ] **TASK-30I**: 重構測試 fixtures 和 conftest.py
- [ ] **TASK-30J**: 更新測試案例移除 JSON 依賴

### 🔗 階段 5: 知識圖譜準備 (1 天)
**子任務:**
- [ ] **TASK-30K**: 擴展 schema 支援圖關係
- [ ] **TASK-30L**: 設計圖 API 和標籤系統擴展

### ✅ 階段 6: 驗證與部署 (0.5 天)
**子任務:**
- [ ] **TASK-30M**: 完整系統驗證和部署準備

## 🏗️ 架構設計

### 新架構概覽
```
┌─────────────────┐
│   Web Routes    │
└────────┬────────┘
         │
┌────────▼────────┐
│ KnowledgeManager│ ◄─── 純資料庫版本，無降級
│ (Database Only) │
└────────┬────────┘
         │
┌────────▼────────┐
│  Repository     │
│   Layer         │
└────────┬────────┘
         │
┌────────▼────────┐
│  PostgreSQL     │ ◄─── 唯一資料來源
│ + Knowledge     │
│   Graph Schema  │
└─────────────────┘
```

### 核心組件變更

#### KnowledgeManager 簡化
```python
class KnowledgeManager:
    """純資料庫版本 - 移除所有 JSON 邏輯"""
    
    def __init__(self):
        self._repository = KnowledgePointRepository()
        self._cache_manager = UnifiedCacheManager()
        self._error_handler = DatabaseErrorHandler()
        # 移除：_legacy_manager, _fallback_manager
```

#### 新錯誤處理策略
```python
class DatabaseErrorHandler:
    """純資料庫錯誤處理 - 無 JSON 降級"""
    
    def __init__(self):
        self.strategies = [
            CacheFallback(),        # 使用快取資料
            NetworkRetryFallback(), # 重試連線
            CircuitBreakerFallback() # 熔斷保護
            # 移除：DatabaseToJsonFallback
        ]
```

## 🔧 資料初始化方案

### Seed Data 設計
```sql
-- seed_data.sql
INSERT INTO knowledge_points (key_point, category, subtype, explanation, original_phrase, correction)
VALUES 
  ('系統初始化範例', 'systematic', 'grammar', '系統首次啟動的範例知識點', 'example error', 'example correction');

INSERT INTO tags (name, color, description) VALUES
  ('grammar', '#FF6B6B', '文法相關'),
  ('vocabulary', '#4ECDC4', '詞彙相關'),
  ('pronunciation', '#45B7D1', '發音相關');
```

### 知識圖譜 Schema 準備
```sql
-- knowledge_graph_relations.sql (未來擴展)
CREATE TABLE knowledge_relationships (
    id SERIAL PRIMARY KEY,
    from_knowledge_id INTEGER REFERENCES knowledge_points(id),
    to_knowledge_id INTEGER REFERENCES knowledge_points(id),
    relationship_type VARCHAR(50) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 0.5,
    confidence DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## ⚠️ 風險評估

### 高風險項目
| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| **資料遺失** | 🔴 高 | 完整備份 + 雙重驗證 |
| **向後不兼容** | 🟡 中 | 版本管理 + 遷移腳本 |
| **開發環境複雜化** | 🟡 中 | Docker化 + 自動化腳本 |
| **測試覆蓋下降** | 🟠 中高 | 重寫測試 + CI監控 |

### 緩解措施
```bash
# 1. 資料安全
./scripts/backup_all_data.sh
./scripts/validate_migration.sh

# 2. 開發環境自動化
./scripts/setup_dev_db.sh
docker-compose up db

# 3. 測試保證
pytest --cov=core --cov-fail-under=90
```

## 📊 子任務執行優先級

### 🚦 依賴關係圖
```
TASK-30A (前置) ⟶ TASK-30B,C,D,E (移除JSON) ⟶ TASK-30F,G (錯誤處理)
                                     ⟶ TASK-30H (初始化)
                                             ⟶ TASK-30I,J (測試)
                                                     ⟶ TASK-30K,L (圖譜)
                                                             ⟶ TASK-30M (驗證)
```

### 🎯 關鍵里程碑
1. **里程碑 1**: 完成 JSON 依賴移除 (TASK-30A~E)
2. **里程碑 2**: 新錯誤處理系統就緒 (TASK-30F~G)
3. **里程碑 3**: 純資料庫系統運行 (TASK-30H)
4. **里程碑 4**: 測試環境完全遷移 (TASK-30I~J)
5. **里程碑 5**: 知識圖譜基礎就緒 (TASK-30K~L)
6. **里程碑 6**: 生產部署準備完成 (TASK-30M)

## 📝 執行筆記

### 當前分析結果
- ✅ 識別 42 個檔案涉及 JSON 依賴
- ✅ 發現 DatabaseAdapter 中 50+ 處降級邏輯
- ✅ 確認標籤系統可作為知識圖譜基礎
- ✅ 評估實施可行性為高
- ✅ 設計簡化的 13 個子任務分解

### 階段 1 完成報告 (2025-01-15)

#### TASK-30B: 清理 core/knowledge.py 和 JSON 模組
1. 重構 KnowledgeManager 為純資料庫版本 (V3.0)
2. 創建 `core/models.py` 分離數據模型，解決循環導入
3. 保留舊版本為 `core/knowledge_json_backup.py` 維持向後兼容
4. 移除 `DatabaseToJsonFallback` 策略

#### TASK-30C: 重構 web/dependencies.py
1. 移除 USE_DATABASE 環境變數檢查
2. 簡化為純資料庫依賴注入
3. 更新同步和異步初始化方法

#### TASK-30D: 簡化 DatabaseAdapter
1. 創建新的 SimplifiedDatabaseAdapter（644行）替代舊 adapter.py（1694行）
2. 創建 DatabaseKnowledgeManager 純資料庫管理器
3. 提供完整的同步和異步 API 維持向後兼容
4. 移除所有 _legacy_manager 引用和條件分支

#### TASK-30E: 清理 fallback_strategies.py
1. 更新模組文檔，移除 JSON 降級相關說明
2. 刪除未使用的 json import
3. 保留其他降級策略（快取、網路重試、優雅降級）

**驗證結果:**
- ✅ 資料庫模式正常啟動和運行
- ✅ 所有 API 功能測試通過
- ✅ 無循環導入錯誤
- ✅ 快取和錯誤處理正常

### 重要發現
1. **深度整合**: JSON 邏輯深度整合於 2000+ 行程式碼中
2. **標籤關聯**: 現有 `RELATED_TAGS` 和 `EXCLUSIVE_TAGS` 是知識圖譜雛形
3. **測試依賴**: 大量測試依賴雙系統切換邏輯
4. **初始化問題**: 目前完全依賴 JSON 遷移作為資料來源
5. **並行機會**: 部分子任務可並行執行以加速進度

### 技術債務清單
- DatabaseAdapter 過度複雜（1694 行）→ 拆分為多個專責類別
- 錯誤處理邏輯分散 → 統一到 DatabaseErrorHandler
- 測試環境設定不一致 → 標準化測試 fixtures
- 文檔與實際架構脫節 → 更新技術文檔
- 缺乏資料庫效能監控 → 加入 metrics 和 logging

## 🔍 審查意見 (For Reviewer)

_(留空，供 reviewer 填寫)_

---

## 📚 參考資料

- [系統架構分析報告](../docs/pure-database-analysis.md)
- [知識圖譜需求文檔](../docs/knowledge-graph-requirements.md)
- [風險評估詳細報告](../docs/migration-risks.md)

---

## 🚨 執行注意事項

### 分支策略
- **主分支**: `feature/pure-database-migration`
- **子任務分支**: `task-30a-backup`, `task-30b-analysis`, ...
- **合併策略**: 每完成一個階段 PR review 後合併

### 回滾計劃
- 保持完整的 JSON 系統備份
- 每個階段完成後創建 checkpoint
- 準備快速回滾腳本

### 團隊協作
- 建議 2-3 人並行處理不同階段
- 每日 standup 同步進度
- 關鍵決策需要 tech lead review

**⚠️ 重要**: 此任務為系統核心架構重構，影響範圍廣泛。務必嚴格按照子任務順序執行，確保每個階段充分測試後再進行下一階段。