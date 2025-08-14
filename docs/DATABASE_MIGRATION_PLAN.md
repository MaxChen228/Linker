# 資料庫遷移完整方案
> 從 JSON 文件遷移到關聯式資料庫的零技術債方案

## 一、現狀分析

### 現有資料結構
1. **knowledge.json** - 知識點儲存（核心資料）
   - 巢狀結構：KnowledgePoint → OriginalError + ReviewExamples[]
   - 版本控制：version_history[]
   - 軟刪除機制

2. **learning_calendar.json** - 學習日曆
   - daily_records: 每日學習記錄
   - weekly_goals: 週目標
   - study_sessions: 學習會話

3. **patterns.json** - 文法模式（目前不存在但規劃中）

### 主要問題
- 並發寫入不安全
- 全文件讀寫效能差
- 缺乏事務支援
- 無法做複雜查詢
- 沒有索引優化

## 二、資料庫架構設計

### 技術選型：PostgreSQL
理由：
- 支援 JSONB 欄位（平滑過渡）
- 強大的全文搜索
- 優秀的並發控制
- 支援部分索引和複合索引
- 內建 UUID 支援

### 完整 Schema 設計

```sql
-- 1. 知識點主表
CREATE TABLE knowledge_points (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    
    -- 核心欄位
    key_point VARCHAR(500) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subtype VARCHAR(50) NOT NULL,
    explanation TEXT NOT NULL,
    original_phrase VARCHAR(200) NOT NULL,
    correction VARCHAR(200) NOT NULL,
    
    -- 掌握度追蹤
    mastery_level DECIMAL(3,2) DEFAULT 0.00 CHECK (mastery_level >= 0 AND mastery_level <= 1),
    mistake_count INTEGER DEFAULT 1 CHECK (mistake_count >= 0),
    correct_count INTEGER DEFAULT 0 CHECK (correct_count >= 0),
    
    -- 時間管理
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_review TIMESTAMP WITH TIME ZONE,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 軟刪除
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_reason TEXT,
    
    -- 擴展欄位
    custom_notes TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- 索引優化
    INDEX idx_category_subtype (category, subtype),
    INDEX idx_next_review (next_review) WHERE is_deleted = FALSE,
    INDEX idx_mastery_level (mastery_level) WHERE is_deleted = FALSE,
    INDEX idx_created_at (created_at DESC),
    INDEX idx_key_point_trgm USING gin (key_point gin_trgm_ops) -- 全文搜索
);

-- 2. 原始錯誤表（1對1關係）
CREATE TABLE original_errors (
    id SERIAL PRIMARY KEY,
    knowledge_point_id INTEGER NOT NULL UNIQUE REFERENCES knowledge_points(id) ON DELETE CASCADE,
    chinese_sentence TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- AI 分析結果快取
    ai_analysis JSONB,
    
    INDEX idx_knowledge_point (knowledge_point_id)
);

-- 3. 複習例句表（1對多關係）
CREATE TABLE review_examples (
    id SERIAL PRIMARY KEY,
    knowledge_point_id INTEGER NOT NULL REFERENCES knowledge_points(id) ON DELETE CASCADE,
    chinese_sentence TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 複習上下文
    review_context JSONB DEFAULT '{}', -- 儲存當時的學習狀態、模式等
    
    INDEX idx_knowledge_point_time (knowledge_point_id, timestamp DESC),
    INDEX idx_timestamp (timestamp DESC)
);

-- 4. 標籤系統
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7), -- HEX color
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE knowledge_point_tags (
    knowledge_point_id INTEGER REFERENCES knowledge_points(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (knowledge_point_id, tag_id)
);

-- 5. 版本歷史（審計日誌）
CREATE TABLE knowledge_point_versions (
    id SERIAL PRIMARY KEY,
    knowledge_point_id INTEGER NOT NULL REFERENCES knowledge_points(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    changed_fields JSONB NOT NULL,
    previous_values JSONB NOT NULL,
    change_reason TEXT,
    changed_by VARCHAR(100), -- 未來支援多用戶
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(knowledge_point_id, version_number),
    INDEX idx_kp_version (knowledge_point_id, version_number DESC)
);

-- 6. 學習日曆
CREATE TABLE study_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- 統計資料
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    knowledge_points_reviewed INTEGER DEFAULT 0,
    new_errors_found INTEGER DEFAULT 0,
    
    -- 會話元資料
    mode VARCHAR(50), -- 'practice', 'review', 'test'
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_started_at (started_at DESC)
);

-- 7. 每日學習記錄
CREATE TABLE daily_records (
    date DATE PRIMARY KEY,
    total_practice_time INTEGER DEFAULT 0, -- 分鐘
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    knowledge_points_reviewed INTEGER DEFAULT 0,
    new_knowledge_points INTEGER DEFAULT 0,
    mastery_improvements INTEGER DEFAULT 0,
    
    -- 每日目標
    daily_goal INTEGER,
    goal_achieved BOOLEAN DEFAULT FALSE,
    
    -- 統計快照
    stats_snapshot JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. 週目標
CREATE TABLE weekly_goals (
    week_start DATE PRIMARY KEY,
    week_end DATE NOT NULL,
    target_practice_days INTEGER DEFAULT 5,
    target_questions INTEGER DEFAULT 50,
    target_mastery_points INTEGER DEFAULT 10,
    
    -- 實際達成
    actual_practice_days INTEGER DEFAULT 0,
    actual_questions INTEGER DEFAULT 0,
    actual_mastery_points INTEGER DEFAULT 0,
    
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CHECK (week_end > week_start)
);

-- 9. 文法模式庫（未來擴展）
CREATE TABLE grammar_patterns (
    id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(200) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    explanation TEXT NOT NULL,
    examples JSONB DEFAULT '[]',
    usage_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_pattern_type (pattern_type),
    INDEX idx_difficulty (difficulty_level)
);

-- 10. 練習佇列（優化練習體驗）
CREATE TABLE practice_queue (
    id SERIAL PRIMARY KEY,
    knowledge_point_id INTEGER REFERENCES knowledge_points(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    reason VARCHAR(50), -- 'due_review', 'low_mastery', 'recent_error'
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(knowledge_point_id, scheduled_for),
    INDEX idx_scheduled (scheduled_for, priority DESC) WHERE completed_at IS NULL
);

-- 觸發器：自動更新 last_modified
CREATE OR REPLACE FUNCTION update_last_modified()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_knowledge_points_last_modified
BEFORE UPDATE ON knowledge_points
FOR EACH ROW
EXECUTE FUNCTION update_last_modified();

-- 觸發器：版本歷史記錄
CREATE OR REPLACE FUNCTION record_knowledge_point_version()
RETURNS TRIGGER AS $$
DECLARE
    changed_fields JSONB;
    previous_values JSONB;
    next_version INTEGER;
BEGIN
    -- 只記錄實際變更的欄位
    changed_fields := '{}';
    previous_values := '{}';
    
    -- 比較每個重要欄位
    IF OLD.key_point IS DISTINCT FROM NEW.key_point THEN
        changed_fields := changed_fields || jsonb_build_object('key_point', NEW.key_point);
        previous_values := previous_values || jsonb_build_object('key_point', OLD.key_point);
    END IF;
    
    IF OLD.explanation IS DISTINCT FROM NEW.explanation THEN
        changed_fields := changed_fields || jsonb_build_object('explanation', NEW.explanation);
        previous_values := previous_values || jsonb_build_object('explanation', OLD.explanation);
    END IF;
    
    -- ... 其他欄位比較
    
    IF changed_fields != '{}' THEN
        SELECT COALESCE(MAX(version_number), 0) + 1 INTO next_version
        FROM knowledge_point_versions
        WHERE knowledge_point_id = NEW.id;
        
        INSERT INTO knowledge_point_versions 
        (knowledge_point_id, version_number, changed_fields, previous_values)
        VALUES (NEW.id, next_version, changed_fields, previous_values);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER record_version_on_update
AFTER UPDATE ON knowledge_points
FOR EACH ROW
EXECUTE FUNCTION record_knowledge_point_version();
```

## 三、Repository Pattern 抽象層設計

### 3.1 基礎架構

```python
# core/database/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime
import asyncio
import asyncpg
from contextlib import asynccontextmanager

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """基礎 Repository 抽象類"""
    
    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
    
    @asynccontextmanager
    async def transaction(self):
        """事務管理器"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    async def find_all(self, **filters) -> List[T]:
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
```

### 3.2 知識點 Repository

```python
# core/database/repositories/knowledge_repository.py
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import json

from core.database.base import BaseRepository
from core.knowledge import KnowledgePoint, OriginalError, ReviewExample

class KnowledgePointRepository(BaseRepository[KnowledgePoint]):
    """知識點資料庫操作層"""
    
    async def find_by_id(self, id: int) -> Optional[KnowledgePoint]:
        """根據 ID 查詢知識點"""
        query = """
            SELECT 
                kp.*,
                oe.chinese_sentence as oe_chinese,
                oe.user_answer as oe_user_answer,
                oe.correct_answer as oe_correct_answer,
                oe.timestamp as oe_timestamp,
                array_agg(
                    json_build_object(
                        'chinese_sentence', re.chinese_sentence,
                        'user_answer', re.user_answer,
                        'correct_answer', re.correct_answer,
                        'timestamp', re.timestamp,
                        'is_correct', re.is_correct
                    ) ORDER BY re.timestamp DESC
                ) FILTER (WHERE re.id IS NOT NULL) as review_examples,
                array_agg(DISTINCT t.name) FILTER (WHERE t.id IS NOT NULL) as tags
            FROM knowledge_points kp
            LEFT JOIN original_errors oe ON kp.id = oe.knowledge_point_id
            LEFT JOIN review_examples re ON kp.id = re.knowledge_point_id
            LEFT JOIN knowledge_point_tags kpt ON kp.id = kpt.knowledge_point_id
            LEFT JOIN tags t ON kpt.tag_id = t.id
            WHERE kp.id = $1 AND kp.is_deleted = FALSE
            GROUP BY kp.id, oe.chinese_sentence, oe.user_answer, oe.correct_answer, oe.timestamp
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, id)
            
        if not row:
            return None
            
        return self._row_to_knowledge_point(row)
    
    async def find_due_for_review(self, limit: int = 20) -> List[KnowledgePoint]:
        """查詢需要複習的知識點"""
        query = """
            SELECT * FROM knowledge_points
            WHERE next_review <= $1 
                AND is_deleted = FALSE
                AND mastery_level < 0.9
            ORDER BY next_review ASC, mastery_level ASC
            LIMIT $2
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, datetime.now(), limit)
            
        return [self._row_to_knowledge_point(row) for row in rows]
    
    async def find_by_category(self, category: str, subtype: Optional[str] = None) -> List[KnowledgePoint]:
        """根據分類查詢"""
        if subtype:
            query = """
                SELECT * FROM knowledge_points
                WHERE category = $1 AND subtype = $2 AND is_deleted = FALSE
                ORDER BY created_at DESC
            """
            params = [category, subtype]
        else:
            query = """
                SELECT * FROM knowledge_points
                WHERE category = $1 AND is_deleted = FALSE
                ORDER BY created_at DESC
            """
            params = [category]
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        return [self._row_to_knowledge_point(row) for row in rows]
    
    async def search(self, keyword: str) -> List[KnowledgePoint]:
        """全文搜索"""
        query = """
            SELECT * FROM knowledge_points
            WHERE (
                key_point ILIKE $1 
                OR explanation ILIKE $1
                OR original_phrase ILIKE $1
            ) AND is_deleted = FALSE
            ORDER BY 
                CASE 
                    WHEN key_point ILIKE $1 THEN 1
                    WHEN original_phrase ILIKE $1 THEN 2
                    ELSE 3
                END,
                created_at DESC
            LIMIT 50
        """
        
        pattern = f"%{keyword}%"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, pattern)
            
        return [self._row_to_knowledge_point(row) for row in rows]
    
    async def create(self, knowledge_point: KnowledgePoint) -> KnowledgePoint:
        """創建新知識點"""
        async with self.transaction() as conn:
            # 1. 插入主表
            kp_query = """
                INSERT INTO knowledge_points 
                (key_point, category, subtype, explanation, original_phrase, correction,
                 mastery_level, mistake_count, correct_count, next_review, custom_notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
            """
            
            kp_row = await conn.fetchrow(
                kp_query,
                knowledge_point.key_point,
                knowledge_point.category,
                knowledge_point.subtype,
                knowledge_point.explanation,
                knowledge_point.original_phrase,
                knowledge_point.correction,
                knowledge_point.mastery_level,
                knowledge_point.mistake_count,
                knowledge_point.correct_count,
                knowledge_point.next_review,
                knowledge_point.custom_notes
            )
            
            kp_id = kp_row['id']
            
            # 2. 插入原始錯誤
            oe = knowledge_point.original_error
            oe_query = """
                INSERT INTO original_errors 
                (knowledge_point_id, chinese_sentence, user_answer, correct_answer, timestamp)
                VALUES ($1, $2, $3, $4, $5)
            """
            
            await conn.execute(
                oe_query,
                kp_id,
                oe.chinese_sentence,
                oe.user_answer,
                oe.correct_answer,
                datetime.fromisoformat(oe.timestamp)
            )
            
            # 3. 插入複習例句
            if knowledge_point.review_examples:
                re_query = """
                    INSERT INTO review_examples 
                    (knowledge_point_id, chinese_sentence, user_answer, correct_answer, is_correct, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """
                
                for example in knowledge_point.review_examples:
                    await conn.execute(
                        re_query,
                        kp_id,
                        example.chinese_sentence,
                        example.user_answer,
                        example.correct_answer,
                        example.is_correct,
                        datetime.fromisoformat(example.timestamp)
                    )
            
            # 4. 插入標籤
            if knowledge_point.tags:
                for tag_name in knowledge_point.tags:
                    # 先確保標籤存在
                    tag_id = await conn.fetchval(
                        "INSERT INTO tags (name) VALUES ($1) ON CONFLICT (name) DO UPDATE SET name = $1 RETURNING id",
                        tag_name
                    )
                    
                    # 建立關聯
                    await conn.execute(
                        "INSERT INTO knowledge_point_tags (knowledge_point_id, tag_id) VALUES ($1, $2)",
                        kp_id, tag_id
                    )
            
            knowledge_point.id = kp_id
            return knowledge_point
    
    async def update(self, knowledge_point: KnowledgePoint) -> KnowledgePoint:
        """更新知識點"""
        query = """
            UPDATE knowledge_points SET
                key_point = $2,
                explanation = $3,
                mastery_level = $4,
                mistake_count = $5,
                correct_count = $6,
                last_seen = $7,
                next_review = $8,
                custom_notes = $9
            WHERE id = $1
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                knowledge_point.id,
                knowledge_point.key_point,
                knowledge_point.explanation,
                knowledge_point.mastery_level,
                knowledge_point.mistake_count,
                knowledge_point.correct_count,
                datetime.now(),
                knowledge_point.next_review,
                knowledge_point.custom_notes
            )
            
        return self._row_to_knowledge_point(row)
    
    async def soft_delete(self, id: int, reason: str = "") -> bool:
        """軟刪除"""
        query = """
            UPDATE knowledge_points 
            SET is_deleted = TRUE, 
                deleted_at = $2, 
                deleted_reason = $3
            WHERE id = $1
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, id, datetime.now(), reason)
            
        return result is not None
    
    async def add_review_example(self, knowledge_point_id: int, example: ReviewExample) -> bool:
        """添加複習例句"""
        query = """
            INSERT INTO review_examples 
            (knowledge_point_id, chinese_sentence, user_answer, correct_answer, is_correct, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                knowledge_point_id,
                example.chinese_sentence,
                example.user_answer,
                example.correct_answer,
                example.is_correct,
                datetime.fromisoformat(example.timestamp)
            )
            
        return result is not None
    
    async def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資料"""
        query = """
            SELECT 
                COUNT(*) FILTER (WHERE is_deleted = FALSE) as total_active,
                COUNT(*) FILTER (WHERE mastery_level >= 0.8 AND is_deleted = FALSE) as mastered,
                COUNT(*) FILTER (WHERE mastery_level < 0.3 AND is_deleted = FALSE) as struggling,
                COUNT(*) FILTER (WHERE next_review <= NOW() AND is_deleted = FALSE) as due_review,
                AVG(mastery_level) FILTER (WHERE is_deleted = FALSE) as avg_mastery,
                COUNT(DISTINCT category) as categories_count
            FROM knowledge_points
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query)
            
        return dict(row)
    
    def _row_to_knowledge_point(self, row: asyncpg.Record) -> KnowledgePoint:
        """將資料庫記錄轉換為 KnowledgePoint 物件"""
        # 建構原始錯誤
        original_error = OriginalError(
            chinese_sentence=row.get('oe_chinese', ''),
            user_answer=row.get('oe_user_answer', ''),
            correct_answer=row.get('oe_correct_answer', ''),
            timestamp=row.get('oe_timestamp', datetime.now()).isoformat()
        )
        
        # 建構複習例句列表
        review_examples = []
        if row.get('review_examples'):
            for example_data in row['review_examples']:
                if example_data:  # 過濾掉 None
                    review_examples.append(ReviewExample(
                        chinese_sentence=example_data['chinese_sentence'],
                        user_answer=example_data['user_answer'],
                        correct_answer=example_data['correct_answer'],
                        timestamp=example_data['timestamp'],
                        is_correct=example_data['is_correct']
                    ))
        
        # 建構知識點物件
        return KnowledgePoint(
            id=row['id'],
            key_point=row['key_point'],
            category=row['category'],
            subtype=row['subtype'],
            explanation=row['explanation'],
            original_phrase=row['original_phrase'],
            correction=row['correction'],
            original_error=original_error,
            review_examples=review_examples,
            mastery_level=float(row['mastery_level']),
            mistake_count=row['mistake_count'],
            correct_count=row['correct_count'],
            created_at=row['created_at'].isoformat(),
            last_seen=row['last_seen'].isoformat(),
            next_review=row['next_review'].isoformat() if row['next_review'] else "",
            is_deleted=row['is_deleted'],
            deleted_at=row['deleted_at'].isoformat() if row['deleted_at'] else "",
            deleted_reason=row['deleted_reason'] or "",
            tags=row.get('tags', []) or [],
            custom_notes=row['custom_notes'] or "",
            version_history=[],  # 需要時才載入
            last_modified=row['last_modified'].isoformat()
        )
```

### 3.3 適配器模式（向後兼容）

```python
# core/database/adapter.py
"""
適配器層：提供與現有 KnowledgeManager 相同的介面
實現無縫遷移，不需要修改現有業務邏輯
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime

from core.knowledge import KnowledgeManager as LegacyKnowledgeManager
from core.database.repositories.knowledge_repository import KnowledgePointRepository
from core.database.connection import DatabaseConnection

class KnowledgeManagerAdapter:
    """
    資料庫適配器，保持與原 KnowledgeManager 相同的介面
    可以在配置中切換使用 JSON 或資料庫
    """
    
    def __init__(self, use_database: bool = False, data_dir: Optional[str] = None):
        self.use_database = use_database
        
        if use_database:
            # 使用資料庫
            self.db_conn = DatabaseConnection()
            self.repository = KnowledgePointRepository(self.db_conn.pool)
            self._knowledge_points_cache = []
            self._load_from_database()
        else:
            # 使用傳統 JSON 檔案
            self.legacy_manager = LegacyKnowledgeManager(data_dir=data_dir)
    
    @property
    def knowledge_points(self) -> List:
        """獲取所有知識點（保持同步介面）"""
        if self.use_database:
            return self._knowledge_points_cache
        else:
            return self.legacy_manager.knowledge_points
    
    def add_knowledge_point(self, knowledge_point) -> bool:
        """添加知識點"""
        if self.use_database:
            # 異步操作轉同步
            future = asyncio.run(self.repository.create(knowledge_point))
            self._refresh_cache()
            return future is not None
        else:
            return self.legacy_manager.add_knowledge_point(knowledge_point)
    
    def update_knowledge_point(self, point_id: int, **kwargs) -> bool:
        """更新知識點"""
        if self.use_database:
            point = self.get_knowledge_point_by_id(point_id)
            if not point:
                return False
            
            # 更新屬性
            for key, value in kwargs.items():
                if hasattr(point, key):
                    setattr(point, key, value)
            
            future = asyncio.run(self.repository.update(point))
            self._refresh_cache()
            return future is not None
        else:
            return self.legacy_manager.update_knowledge_point(point_id, **kwargs)
    
    def delete_knowledge_point(self, point_id: int, reason: str = "") -> bool:
        """刪除知識點"""
        if self.use_database:
            future = asyncio.run(self.repository.soft_delete(point_id, reason))
            self._refresh_cache()
            return future
        else:
            return self.legacy_manager.delete_knowledge_point(point_id, reason)
    
    def get_knowledge_point_by_id(self, point_id: int):
        """根據 ID 獲取知識點"""
        if self.use_database:
            return asyncio.run(self.repository.find_by_id(point_id))
        else:
            return self.legacy_manager.get_knowledge_point_by_id(point_id)
    
    def search_knowledge_points(self, keyword: str):
        """搜索知識點"""
        if self.use_database:
            return asyncio.run(self.repository.search(keyword))
        else:
            return self.legacy_manager.search_knowledge_points(keyword)
    
    def get_due_review_points(self, limit: int = 20):
        """獲取待複習知識點"""
        if self.use_database:
            return asyncio.run(self.repository.find_due_for_review(limit))
        else:
            return self.legacy_manager.get_due_review_points(limit)
    
    def _load_from_database(self):
        """從資料庫載入資料到快取"""
        self._knowledge_points_cache = asyncio.run(
            self.repository.find_all(is_deleted=False)
        )
    
    def _refresh_cache(self):
        """刷新快取"""
        self._load_from_database()
    
    def export_to_json(self, filepath: str):
        """匯出到 JSON（用於備份）"""
        data = {
            'version': '4.0',
            'last_updated': datetime.now().isoformat(),
            'data': [kp.to_dict() for kp in self.knowledge_points]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_from_json(self, filepath: str):
        """從 JSON 匯入（用於遷移）"""
        if not self.use_database:
            raise ValueError("Import only works in database mode")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for point_data in data.get('data', []):
            # 轉換為 KnowledgePoint 物件
            point = self._dict_to_knowledge_point(point_data)
            asyncio.run(self.repository.create(point))
        
        self._refresh_cache()
```

## 四、遷移策略

### 4.1 漸進式遷移計劃

#### 階段一：準備階段（1週）
1. 建立資料庫環境
2. 部署新的 Repository 層
3. 實施適配器模式
4. 保持雙寫（JSON + DB）

```python
# settings.py 配置
class Settings:
    # 遷移開關
    USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"
    ENABLE_DUAL_WRITE = os.getenv("ENABLE_DUAL_WRITE", "false").lower() == "true"
    
    # 資料庫配置
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/linker")
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    
    # 遷移配置
    MIGRATION_BATCH_SIZE = int(os.getenv("MIGRATION_BATCH_SIZE", "100"))
```

#### 階段二：雙寫階段（2週）
- 所有寫入操作同時寫入 JSON 和資料庫
- 讀取仍從 JSON
- 驗證資料一致性

```python
# core/migration/dual_write.py
class DualWriteManager:
    """雙寫管理器，確保資料一致性"""
    
    def __init__(self):
        self.json_manager = LegacyKnowledgeManager()
        self.db_manager = KnowledgeManagerAdapter(use_database=True)
    
    async def write(self, operation: str, *args, **kwargs):
        """執行雙寫操作"""
        # 先寫 JSON（保證向後兼容）
        json_result = getattr(self.json_manager, operation)(*args, **kwargs)
        
        # 再寫資料庫
        try:
            db_result = getattr(self.db_manager, operation)(*args, **kwargs)
            
            # 驗證一致性
            if json_result != db_result:
                self.log_inconsistency(operation, json_result, db_result)
        except Exception as e:
            # 資料庫寫入失敗不影響 JSON
            self.log_error(f"Database write failed: {e}")
        
        return json_result
```

#### 階段三：遷移階段（1週）
1. 執行資料遷移腳本
2. 驗證資料完整性
3. 切換讀取到資料庫

```python
# scripts/migrate_to_database.py
import asyncio
from pathlib import Path
import json
from tqdm import tqdm

from core.database.connection import DatabaseConnection
from core.database.repositories.knowledge_repository import KnowledgePointRepository

async def migrate_knowledge_points():
    """遷移知識點資料"""
    # 讀取 JSON 資料
    json_file = Path("data/knowledge.json")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 建立資料庫連線
    db = DatabaseConnection()
    await db.connect()
    repo = KnowledgePointRepository(db.pool)
    
    # 批次遷移
    points = data.get('data', [])
    batch_size = 10
    
    with tqdm(total=len(points), desc="Migrating knowledge points") as pbar:
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            
            async with repo.transaction() as conn:
                for point_data in batch:
                    # 轉換並插入
                    knowledge_point = json_to_knowledge_point(point_data)
                    await repo.create(knowledge_point)
            
            pbar.update(len(batch))
    
    await db.disconnect()
    print(f"Successfully migrated {len(points)} knowledge points")

async def verify_migration():
    """驗證遷移資料完整性"""
    # 比較 JSON 和資料庫中的資料
    json_data = load_json_data()
    db_data = await load_db_data()
    
    discrepancies = []
    
    for json_point in json_data:
        db_point = find_in_db(db_data, json_point['id'])
        
        if not db_point:
            discrepancies.append(f"Missing in DB: {json_point['id']}")
            continue
        
        # 比較關鍵欄位
        for field in ['key_point', 'category', 'explanation']:
            if json_point[field] != db_point[field]:
                discrepancies.append(
                    f"Field mismatch for {json_point['id']}.{field}"
                )
    
    if discrepancies:
        print(f"Found {len(discrepancies)} discrepancies:")
        for d in discrepancies[:10]:
            print(f"  - {d}")
    else:
        print("✓ Migration verified successfully")
    
    return len(discrepancies) == 0

if __name__ == "__main__":
    asyncio.run(migrate_knowledge_points())
    asyncio.run(verify_migration())
```

#### 階段四：切換階段（3天）
1. 灰度切換：部分用戶使用資料庫
2. 監控效能和錯誤
3. 全量切換

#### 階段五：清理階段（1週）
1. 停止 JSON 寫入
2. 保留 JSON 作為備份
3. 移除舊代碼

### 4.2 回滾計劃

```python
# scripts/rollback.py
async def rollback_to_json():
    """緊急回滾到 JSON"""
    # 1. 從資料庫匯出最新資料
    db_manager = KnowledgeManagerAdapter(use_database=True)
    db_manager.export_to_json("data/knowledge_backup.json")
    
    # 2. 切換配置
    os.environ["USE_DATABASE"] = "false"
    
    # 3. 重啟服務
    print("Rollback completed. Please restart the service.")

# 配置快速切換
class FeatureToggle:
    @property
    def use_database(self):
        # 可以從遠端配置服務讀取
        return self._check_remote_config("use_database", default=False)
```

## 五、測試策略

### 5.1 單元測試

```python
# tests/test_repository.py
import pytest
import asyncio
from datetime import datetime

from core.database.repositories.knowledge_repository import KnowledgePointRepository
from core.knowledge import KnowledgePoint, OriginalError

@pytest.mark.asyncio
async def test_create_and_find_knowledge_point(db_connection):
    repo = KnowledgePointRepository(db_connection)
    
    # 創建測試資料
    original_error = OriginalError(
        chinese_sentence="測試句子",
        user_answer="test answer",
        correct_answer="correct answer",
        timestamp=datetime.now().isoformat()
    )
    
    kp = KnowledgePoint(
        id=0,
        key_point="測試知識點",
        category="systematic",
        subtype="grammar",
        explanation="測試說明",
        original_phrase="test",
        correction="test",
        original_error=original_error
    )
    
    # 測試創建
    created = await repo.create(kp)
    assert created.id > 0
    
    # 測試查詢
    found = await repo.find_by_id(created.id)
    assert found is not None
    assert found.key_point == "測試知識點"

@pytest.mark.asyncio 
async def test_concurrent_updates(db_connection):
    """測試並發更新"""
    repo = KnowledgePointRepository(db_connection)
    
    # 創建測試資料
    kp = await create_test_knowledge_point(repo)
    
    # 並發更新
    async def update_mastery(value):
        kp.mastery_level = value
        return await repo.update(kp)
    
    results = await asyncio.gather(
        update_mastery(0.5),
        update_mastery(0.6),
        update_mastery(0.7)
    )
    
    # 驗證最終狀態
    final = await repo.find_by_id(kp.id)
    assert final.mastery_level in [0.5, 0.6, 0.7]
```

### 5.2 整合測試

```python
# tests/test_migration.py
@pytest.mark.integration
async def test_json_to_db_migration():
    """測試 JSON 到資料庫的完整遷移"""
    # 準備測試 JSON
    test_json = {
        "version": "4.0",
        "data": [
            # ... 測試資料
        ]
    }
    
    # 執行遷移
    migrator = DataMigrator()
    await migrator.migrate_from_json(test_json)
    
    # 驗證資料
    repo = KnowledgePointRepository(test_db)
    all_points = await repo.find_all()
    
    assert len(all_points) == len(test_json["data"])
```

### 5.3 效能測試

```python
# tests/test_performance.py
@pytest.mark.benchmark
async def test_query_performance(benchmark):
    """測試查詢效能"""
    repo = KnowledgePointRepository(db_connection)
    
    # 準備 1000 筆測試資料
    await create_test_data(repo, count=1000)
    
    # 測試查詢效能
    result = await benchmark(repo.find_due_for_review, limit=20)
    
    assert len(result) <= 20
    assert benchmark.stats["mean"] < 0.1  # 平均小於 100ms
```

## 六、監控與維護

### 6.1 資料庫監控

```python
# core/database/monitoring.py
class DatabaseMonitor:
    """資料庫健康監控"""
    
    async def health_check(self):
        """健康檢查"""
        checks = {
            "connection": await self._check_connection(),
            "pool_status": await self._check_pool(),
            "query_performance": await self._check_query_performance(),
            "table_sizes": await self._check_table_sizes()
        }
        
        return {
            "status": "healthy" if all(checks.values()) else "unhealthy",
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _check_connection(self):
        """檢查連線"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except:
            return False
    
    async def _check_query_performance(self):
        """檢查查詢效能"""
        start = time.time()
        async with self.pool.acquire() as conn:
            await conn.fetch(
                "SELECT * FROM knowledge_points LIMIT 100"
            )
        elapsed = time.time() - start
        return elapsed < 0.5  # 小於 500ms
```

### 6.2 自動備份

```python
# scripts/backup.py
async def automated_backup():
    """自動備份資料庫到 JSON"""
    db_manager = KnowledgeManagerAdapter(use_database=True)
    
    # 生成備份檔名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/knowledge_backup_{timestamp}.json"
    
    # 執行備份
    db_manager.export_to_json(backup_file)
    
    # 清理舊備份（保留最近 7 天）
    cleanup_old_backups(days=7)
    
    print(f"Backup completed: {backup_file}")

# 設定 cron job
# 0 2 * * * python scripts/backup.py
```

## 七、結論

這套方案實現了：

1. **零技術債** - 使用 Repository Pattern 和適配器模式
2. **平滑遷移** - 漸進式遷移，隨時可回滾
3. **向後兼容** - 不需修改現有業務邏輯
4. **效能優化** - 索引、連線池、查詢優化
5. **可測試性** - 完整的測試覆蓋
6. **可監控性** - 健康檢查和效能監控
7. **資料安全** - 自動備份和軟刪除

遷移時間表：
- 準備階段：1週
- 雙寫階段：2週
- 遷移執行：1週
- 監控穩定：1週
- **總計：5週完成遷移**

風險控制：
- 每個階段都可獨立回滾
- 保留 JSON 備份 3 個月
- 灰度發布降低風險