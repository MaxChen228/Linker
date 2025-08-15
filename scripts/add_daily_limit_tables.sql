-- TASK-32: 每日知識點上限功能 - 資料庫遷移腳本
-- 創建用戶設定和每日統計表

BEGIN;

-- 1. 用戶設定表（支援個人化限額配置）
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) DEFAULT 'default_user',
    daily_knowledge_limit INTEGER DEFAULT 15 CHECK (daily_knowledge_limit BETWEEN 1 AND 50),
    limit_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 確保每個用戶只有一個設定記錄
    UNIQUE(user_id)
);

-- 2. 每日知識點統計表
CREATE TABLE IF NOT EXISTS daily_knowledge_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    user_id VARCHAR(50) DEFAULT 'default_user',
    
    -- 分類計數（只計算受限制的類型）
    isolated_count INTEGER DEFAULT 0 CHECK (isolated_count >= 0),
    enhancement_count INTEGER DEFAULT 0 CHECK (enhancement_count >= 0),
    
    -- 自動計算總數
    total_limited_count INTEGER GENERATED ALWAYS AS (isolated_count + enhancement_count) STORED,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 確保每個用戶每天只有一條記錄
    UNIQUE(date, user_id)
);

-- 3. 創建索引優化查詢性能
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date_user ON daily_knowledge_stats(date, user_id);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date_desc ON daily_knowledge_stats(date DESC);

-- 4. 自動更新 updated_at 觸發器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 為兩個新表添加觸發器
CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON user_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_knowledge_stats_updated_at
    BEFORE UPDATE ON daily_knowledge_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 5. 插入預設設定（如果不存在）
INSERT INTO user_settings (user_id, daily_knowledge_limit, limit_enabled) 
VALUES ('default_user', 15, false) 
ON CONFLICT (user_id) DO NOTHING;

-- 6. 創建便利視圖（用於統計查詢）
CREATE OR REPLACE VIEW daily_limit_overview AS
SELECT 
    dks.date,
    dks.user_id,
    dks.isolated_count,
    dks.enhancement_count,
    dks.total_limited_count,
    us.daily_knowledge_limit,
    us.limit_enabled,
    CASE 
        WHEN us.limit_enabled = false THEN 'disabled'
        WHEN dks.total_limited_count >= us.daily_knowledge_limit THEN 'exceeded'
        WHEN dks.total_limited_count >= us.daily_knowledge_limit * 0.8 THEN 'warning'
        ELSE 'normal'
    END as status,
    (us.daily_knowledge_limit - dks.total_limited_count) as remaining_quota
FROM daily_knowledge_stats dks
JOIN user_settings us ON dks.user_id = us.user_id
ORDER BY dks.date DESC;

-- 7. 添加註釋說明
COMMENT ON TABLE user_settings IS 'TASK-32: 用戶個人化設定，包含每日知識點上限配置';
COMMENT ON TABLE daily_knowledge_stats IS 'TASK-32: 每日知識點儲存統計，用於限額控制';
COMMENT ON COLUMN user_settings.daily_knowledge_limit IS '每日可儲存知識點上限（5-50）';
COMMENT ON COLUMN user_settings.limit_enabled IS '是否啟用限額功能';
COMMENT ON COLUMN daily_knowledge_stats.isolated_count IS 'isolated類型錯誤計數（單一知識點）';
COMMENT ON COLUMN daily_knowledge_stats.enhancement_count IS 'enhancement類型錯誤計數（可以更好）';
COMMENT ON VIEW daily_limit_overview IS 'TASK-32: 每日限額狀態總覽視圖';

COMMIT;

-- 驗證創建結果
\echo '=== TASK-32 資料庫遷移完成 ==='
\echo '檢查新建的表和視圖：'
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name IN ('user_settings', 'daily_knowledge_stats') 
   OR table_name = 'daily_limit_overview'
ORDER BY table_name;