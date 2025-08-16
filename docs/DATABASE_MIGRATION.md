# Linker 資料庫遷移指南 (完整版)

本指南詳細介紹了 Linker 專案中已實現的、從 JSON 檔案遷移到 PostgreSQL 資料庫的完整系統，包含操作步驟和底層技術方案。

---

## 🚀 自動遷移流程（推薦）

使用一鍵遷移腳本：

```bash
# 執行完整遷移流程
./migrate_to_database.sh

# 查看可用選項
./migrate_to_database.sh --help
```

此腳本會自動執行以下步驟：
1. ✅ 檢查依賴
2. ✅ 備份 JSON 資料
3. ✅ 初始化資料庫結構
4. ✅ 執行資料遷移
5. ✅ 驗證遷移結果
6. ✅ 配置應用程式使用資料庫

---

## 🔧 手動遷移流程（進階用戶）

如果你偏好手動控制每個步驟：

### 步驟 1: 準備工作

1.  **確保 PostgreSQL 已安裝並運行**

    ```bash
    # 檢查 PostgreSQL 狀態
    pg_ctl status
    ```

2.  **建立資料庫和用戶**

    ```sql
    -- 連線到 PostgreSQL
    psql -U postgres

    -- 執行以下 SQL
    CREATE DATABASE linker;
    CREATE USER linker_user WITH PASSWORD 'your_password';
    GRANT ALL PRIVILEGES ON DATABASE linker TO linker_user;
    \q
    ```

3.  **設定環境變數**

    ```bash
    # 設定資料庫連線 URL
    export DATABASE_URL="postgresql://linker_user:your_password@localhost:5432/linker"
    ```

### 步驟 2: 初始化資料庫結構

```bash
# 設定資料庫模式（不會實際切換，僅用於初始化）
export USE_DATABASE=true

# 初始化資料庫 schema
python scripts/init_database.py

# 檢查資料庫狀態
python scripts/init_database.py --check-only
```

### 步驟 3: 執行資料遷移

```bash
# 乾跑檢查（不會實際遷移）
python scripts/migrate_data.py --dry-run

# 執行實際遷移
python scripts/migrate_data.py

# 驗證遷移結果
python scripts/migrate_data.py --verify-only
```

### 步驟 4: 切換到資料庫模式

```bash
# 配置為資料庫模式
python scripts/configure_db.py --mode database

# 確認配置
python scripts/configure_db.py --show
```

### 步驟 5: 重啟應用程式

```bash
# 重啟應用程式以套用新配置
./run.sh
```

---

## 🔍 驗證與回滾

### 驗證遷移

1.  **啟動應用程式** (`./run.sh`)
2.  **測試 API 端點** (如 `curl http://localhost:8000/api/knowledge`)
3.  **檢查資料一致性** (`python scripts/migrate_data.py --verify-only`)

### 回滾機制

如果遇到問題需要回滾到 JSON 模式：

```bash
# 切換回 JSON 模式
python scripts/configure_db.py --mode json

# 重啟應用程式
./run.sh
```
遷移前的 JSON 備份檔案會保存在 `data/knowledge_backup_*.json`。

---
---

## 📐 技術方案與架構設計

> 從 JSON 文件遷移到關聯式資料庫的零技術債方案

### 一、現狀分析

#### 主要問題
- 並發寫入不安全
- 全文件讀寫效能差
- 缺乏事務支援
- 無法做複雜查詢
- 沒有索引優化

### 二、資料庫架構設計

#### 技術選型：PostgreSQL
理由：
- 支援 JSONB 欄位（平滑過渡）
- 強大的全文搜索
- 優秀的並發控制
- 支援部分索引和複合索引

#### 完整 Schema 設計

```sql
-- 1. 知識點主表
CREATE TABLE knowledge_points (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    key_point VARCHAR(500) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subtype VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    original_phrase VARCHAR(200) NOT NULL,
    correction VARCHAR(200) NOT NULL,
    mastery_level DECIMAL(3,2) DEFAULT 0.00,
    mistake_count INTEGER DEFAULT 1,
    correct_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_review TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_reason TEXT,
    custom_notes TEXT,
    metadata JSONB DEFAULT '{}'
);

-- 索引
CREATE INDEX idx_next_review ON knowledge_points (next_review) WHERE is_deleted = FALSE;
CREATE INDEX idx_mastery_level ON knowledge_points (mastery_level) WHERE is_deleted = FALSE;

-- 2. 原始錯誤表（1對1關係）
CREATE TABLE original_errors (
    id SERIAL PRIMARY KEY,
    knowledge_point_id INTEGER NOT NULL UNIQUE REFERENCES knowledge_points(id) ON DELETE CASCADE,
    chinese_sentence TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ai_analysis JSONB
);

-- 3. 複習例句表（1對多關係）
CREATE TABLE review_examples (
    id SERIAL PRIMARY KEY,
    knowledge_point_id INTEGER NOT NULL REFERENCES knowledge_points(id) ON DELETE CASCADE,
    is_correct BOOLEAN NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- ... 其他欄位
);

-- 4. 標籤系統
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE knowledge_point_tags (
    knowledge_point_id INTEGER REFERENCES knowledge_points(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (knowledge_point_id, tag_id)
);

-- 其他表格如 study_sessions, daily_records 等...
```

### 三、Repository Pattern 抽象層設計

為了實現無縫遷移且不修改現有業務邏輯，我們採用 Repository Pattern 和適配器模式。

```python
# core/database/base.py
class BaseRepository(ABC, Generic[T]):
    # ... 基礎 Repository 抽象類 ...

# core/database/repositories/know_repo.py
class KnowledgePointRepository(BaseRepository[KnowledgePoint]):
    # ... 知識點的具體資料庫操作 ...

# core/database/adapter.py
class KnowledgeManagerAdapter:
    """
    資料庫適配器，保持與原 KnowledgeManager 相同的介面
    可以在配置中切換使用 JSON 或資料庫
    """
    def __init__(self, use_database: bool = False):
        if use_database:
            # 使用資料庫
            self.repository = KnowledgePointRepository(...)
        else:
            # 使用傳統 JSON 檔案
            self.legacy_manager = LegacyKnowledgeManager(...)

    # ... 實現所有 KnowledgeManager 的公開方法 ...
```

### 四、遷移策略

採用漸進式遷移計劃，確保系統穩定和資料安全。

1.  **準備階段**: 部署新 Repository 層和適配器，並啟用**雙寫模式**（同時寫入 JSON 和 DB，但讀取仍從 JSON）。
2.  **遷移階段**: 執行資料遷移腳本，將現有 JSON 資料批量匯入資料庫。
3.  **驗證階段**: 執行驗證腳本，比對 JSON 和資料庫中的資料，確保一致性。
4.  **切換階段**: 將讀取操作從 JSON 切換到資料庫。
5.  **清理階段**: 停止 JSON 寫入，移除舊的資料處理代碼。

這套完整的遷移系統確保了 Linker 專案可以從簡單的 JSON 文件儲存平滑過渡到一個高效、穩定且可擴展的 PostgreSQL 資料庫後端，為未來的發展奠定了堅實的基礎。

---
