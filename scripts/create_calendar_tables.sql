-- Calendar System Database Schema
-- 學習日曆系統數據庫表結構設計

-- 1. 每日學習記錄表
CREATE TABLE IF NOT EXISTS daily_learning_records (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    record_date DATE NOT NULL,
    
    -- 學習統計
    completed_reviews INTEGER[] DEFAULT '{}',  -- 已完成的知識點 ID 列表
    planned_reviews INTEGER[] DEFAULT '{}',    -- 計劃複習的知識點 ID 列表
    new_practices INTEGER DEFAULT 0,           -- 新練習數量
    total_mistakes INTEGER DEFAULT 0,          -- 總錯誤數量
    study_minutes INTEGER DEFAULT 0,           -- 學習時長（分鐘）
    mastery_improvement DECIMAL(5,2) DEFAULT 0, -- 掌握度提升百分比
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一約束：每個用戶每天只有一條記錄
    UNIQUE(user_id, record_date)
);

-- 2. 學習會話記錄表
CREATE TABLE IF NOT EXISTS study_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    session_date DATE NOT NULL,
    
    -- 會話詳情
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER DEFAULT 0,
    
    -- 學習內容
    practice_mode VARCHAR(20) NOT NULL,  -- 'new', 'review', 'pattern'
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    knowledge_points_added INTEGER DEFAULT 0,
    knowledge_points_reviewed INTEGER DEFAULT 0,
    
    -- 性能指標
    average_score DECIMAL(5,2) DEFAULT 0,
    accuracy_rate DECIMAL(5,2) DEFAULT 0,
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 週目標設定表
CREATE TABLE IF NOT EXISTS weekly_goals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    
    -- 目標設定
    target_review_points INTEGER DEFAULT 0,    -- 目標複習點數
    target_new_points INTEGER DEFAULT 0,       -- 目標新增點數
    target_study_days INTEGER DEFAULT 5,       -- 目標學習天數
    target_study_minutes INTEGER DEFAULT 150,  -- 目標學習時長
    
    -- 實際完成
    actual_review_points INTEGER DEFAULT 0,
    actual_new_points INTEGER DEFAULT 0,
    actual_study_days INTEGER DEFAULT 0,
    actual_study_minutes INTEGER DEFAULT 0,
    
    -- 狀態
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'completed', 'failed'
    completion_rate DECIMAL(5,2) DEFAULT 0,
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一約束
    UNIQUE(user_id, week_start)
);

-- 4. 學習連續記錄表（用於追蹤連續學習天數）
CREATE TABLE IF NOT EXISTS learning_streaks (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    
    -- 連續記錄
    current_streak INTEGER DEFAULT 0,      -- 當前連續天數
    best_streak INTEGER DEFAULT 0,         -- 歷史最長連續天數
    last_study_date DATE,                  -- 最後學習日期
    streak_start_date DATE,                -- 當前連續開始日期
    
    -- 月度統計
    monthly_active_days INTEGER DEFAULT 0,  -- 本月活躍天數
    monthly_reset_date DATE,                -- 月度重置日期
    
    -- 成就相關
    total_study_days INTEGER DEFAULT 0,     -- 總學習天數
    streak_breaks INTEGER DEFAULT 0,        -- 連續中斷次數
    
    -- 時間戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一約束
    UNIQUE(user_id)
);

-- 創建索引以提高查詢性能
CREATE INDEX idx_daily_records_user_date ON daily_learning_records(user_id, record_date DESC);
CREATE INDEX idx_study_sessions_user_date ON study_sessions(user_id, session_date DESC);
CREATE INDEX idx_weekly_goals_user_week ON weekly_goals(user_id, week_start DESC);
CREATE INDEX idx_learning_streaks_user ON learning_streaks(user_id);

-- 創建更新時間觸發器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_daily_records_updated_at BEFORE UPDATE
    ON daily_learning_records FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_weekly_goals_updated_at BEFORE UPDATE
    ON weekly_goals FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_streaks_updated_at BEFORE UPDATE
    ON learning_streaks FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 視圖：每日學習摘要
CREATE OR REPLACE VIEW daily_learning_summary AS
SELECT 
    d.user_id,
    d.record_date,
    array_length(d.completed_reviews, 1) as reviews_completed,
    array_length(d.planned_reviews, 1) as reviews_planned,
    d.new_practices,
    d.total_mistakes,
    d.study_minutes,
    d.mastery_improvement,
    CASE 
        WHEN array_length(d.completed_reviews, 1) > 0 OR d.new_practices > 0 
        THEN true 
        ELSE false 
    END as has_activity
FROM daily_learning_records d
ORDER BY d.record_date DESC;