-- Linker 專案資料庫 Schema
-- 第一階段：準備階段 - 完整的 PostgreSQL 資料庫設計

-- 啟用必要的擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 全文搜索

-- 1. 知識點主表
CREATE TABLE knowledge_points (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,

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
    metadata JSONB DEFAULT '{}'
);

-- 知識點索引
CREATE INDEX idx_kp_category_subtype ON knowledge_points(category, subtype);
CREATE INDEX idx_kp_next_review ON knowledge_points(next_review) WHERE is_deleted = FALSE;
CREATE INDEX idx_kp_mastery_level ON knowledge_points(mastery_level) WHERE is_deleted = FALSE;
CREATE INDEX idx_kp_created_at ON knowledge_points(created_at DESC);
CREATE INDEX idx_kp_key_point_trgm ON knowledge_points USING gin (key_point gin_trgm_ops);

-- 2. 原始錯誤表（1對1關係）
CREATE TABLE original_errors (
    id SERIAL PRIMARY KEY,
    knowledge_point_id INTEGER NOT NULL UNIQUE REFERENCES knowledge_points(id) ON DELETE CASCADE,
    chinese_sentence TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    -- AI 分析結果快取
    ai_analysis JSONB
);

CREATE INDEX idx_oe_knowledge_point ON original_errors(knowledge_point_id);

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
    review_context JSONB DEFAULT '{}'
);

CREATE INDEX idx_re_knowledge_point_time ON review_examples(knowledge_point_id, timestamp DESC);
CREATE INDEX idx_re_timestamp ON review_examples(timestamp DESC);

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

    UNIQUE(knowledge_point_id, version_number)
);

CREATE INDEX idx_kpv_kp_version ON knowledge_point_versions(knowledge_point_id, version_number DESC);

-- 6. 學習日曆
CREATE TABLE study_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
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
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_ss_started_at ON study_sessions(started_at DESC);

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_gp_pattern_type ON grammar_patterns(pattern_type);
CREATE INDEX idx_gp_difficulty ON grammar_patterns(difficulty_level);

-- 10. 練習佇列（優化練習體驗）
CREATE TABLE practice_queue (
    id SERIAL PRIMARY KEY,
    knowledge_point_id INTEGER REFERENCES knowledge_points(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    reason VARCHAR(50), -- 'due_review', 'low_mastery', 'recent_error'
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(knowledge_point_id, scheduled_for)
);

CREATE INDEX idx_pq_scheduled ON practice_queue(scheduled_for, priority DESC) WHERE completed_at IS NULL;

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

    IF OLD.mastery_level IS DISTINCT FROM NEW.mastery_level THEN
        changed_fields := changed_fields || jsonb_build_object('mastery_level', NEW.mastery_level);
        previous_values := previous_values || jsonb_build_object('mastery_level', OLD.mastery_level);
    END IF;

    IF OLD.category IS DISTINCT FROM NEW.category THEN
        changed_fields := changed_fields || jsonb_build_object('category', NEW.category);
        previous_values := previous_values || jsonb_build_object('category', OLD.category);
    END IF;

    IF OLD.subtype IS DISTINCT FROM NEW.subtype THEN
        changed_fields := changed_fields || jsonb_build_object('subtype', NEW.subtype);
        previous_values := previous_values || jsonb_build_object('subtype', OLD.subtype);
    END IF;

    -- 如果有變更，記錄版本歷史
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

-- 觸發器：自動更新 daily_records 的 updated_at
CREATE TRIGGER update_daily_records_updated_at
BEFORE UPDATE ON daily_records
FOR EACH ROW
EXECUTE FUNCTION update_last_modified();
