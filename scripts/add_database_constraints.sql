-- 資料庫約束添加遷移腳本
-- 執行前請先運行 check_data_integrity.sql 確保數據完整性
-- 
-- 注意：此腳本包含三個部分：
-- 1. 檢查約束（CHECK constraints）
-- 2. 唯一約束（UNIQUE constraints）  
-- 3. 性能索引（Performance indexes）
--
-- 可根據需要分階段執行

-- ==========================================
-- 階段 1：添加檢查約束
-- ==========================================

-- 1.1 knowledge_points 表的檢查約束

-- category 值域檢查（如果尚未存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_kp_category'
    ) THEN
        ALTER TABLE knowledge_points
        ADD CONSTRAINT chk_kp_category
        CHECK (category IN ('systematic', 'isolated', 'enhancement', 'other'));
        RAISE NOTICE 'Added constraint: chk_kp_category';
    END IF;
END $$;

-- 時間邏輯檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_kp_review_time'
    ) THEN
        ALTER TABLE knowledge_points
        ADD CONSTRAINT chk_kp_review_time
        CHECK (next_review IS NULL OR last_seen IS NULL OR next_review >= last_seen);
        RAISE NOTICE 'Added constraint: chk_kp_review_time';
    END IF;
END $$;

-- 掌握度與計數的邏輯一致性
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_kp_count_logic'
    ) THEN
        ALTER TABLE knowledge_points
        ADD CONSTRAINT chk_kp_count_logic
        CHECK (
            (mistake_count = 0 AND correct_count = 0 AND mastery_level = 0) OR
            (mistake_count + correct_count > 0)
        );
        RAISE NOTICE 'Added constraint: chk_kp_count_logic';
    END IF;
END $$;

-- 1.2 tags 表的格式檢查

-- HEX 顏色格式驗證
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_tag_color_format'
    ) THEN
        ALTER TABLE tags
        ADD CONSTRAINT chk_tag_color_format
        CHECK (color IS NULL OR color ~ '^#[0-9A-Fa-f]{6}$');
        RAISE NOTICE 'Added constraint: chk_tag_color_format';
    END IF;
END $$;

-- 1.3 study_sessions 表的檢查約束

-- mode 值域檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_ss_mode'
    ) THEN
        ALTER TABLE study_sessions
        ADD CONSTRAINT chk_ss_mode
        CHECK (mode IS NULL OR mode IN ('practice', 'review', 'test'));
        RAISE NOTICE 'Added constraint: chk_ss_mode';
    END IF;
END $$;

-- 統計數據邏輯檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_ss_stats_logic'
    ) THEN
        ALTER TABLE study_sessions
        ADD CONSTRAINT chk_ss_stats_logic
        CHECK (
            questions_correct <= questions_attempted AND
            questions_correct >= 0 AND
            questions_attempted >= 0 AND
            knowledge_points_reviewed >= 0 AND
            new_errors_found >= 0
        );
        RAISE NOTICE 'Added constraint: chk_ss_stats_logic';
    END IF;
END $$;

-- 時間邏輯檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_ss_time_logic'
    ) THEN
        ALTER TABLE study_sessions
        ADD CONSTRAINT chk_ss_time_logic
        CHECK (ended_at IS NULL OR ended_at >= started_at);
        RAISE NOTICE 'Added constraint: chk_ss_time_logic';
    END IF;
END $$;

-- 1.4 daily_records 表的檢查約束

-- 統計數據邏輯檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_dr_stats_logic'
    ) THEN
        ALTER TABLE daily_records
        ADD CONSTRAINT chk_dr_stats_logic
        CHECK (
            questions_correct <= questions_attempted AND
            questions_correct >= 0 AND
            questions_attempted >= 0 AND
            knowledge_points_reviewed >= 0 AND
            new_knowledge_points >= 0 AND
            mastery_improvements >= 0 AND
            total_practice_time >= 0
        );
        RAISE NOTICE 'Added constraint: chk_dr_stats_logic';
    END IF;
END $$;

-- 1.5 weekly_goals 表的檢查約束

-- 目標值合理性檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_wg_targets'
    ) THEN
        ALTER TABLE weekly_goals
        ADD CONSTRAINT chk_wg_targets
        CHECK (
            target_practice_days BETWEEN 1 AND 7 AND
            target_questions >= 0 AND
            target_mastery_points >= 0
        );
        RAISE NOTICE 'Added constraint: chk_wg_targets';
    END IF;
END $$;

-- 實際值合理性檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_wg_actuals'
    ) THEN
        ALTER TABLE weekly_goals
        ADD CONSTRAINT chk_wg_actuals
        CHECK (
            actual_practice_days BETWEEN 0 AND 7 AND
            actual_questions >= 0 AND
            actual_mastery_points >= 0
        );
        RAISE NOTICE 'Added constraint: chk_wg_actuals';
    END IF;
END $$;

-- 1.6 practice_queue 表的檢查約束

-- reason 值域檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_pq_reason'
    ) THEN
        ALTER TABLE practice_queue
        ADD CONSTRAINT chk_pq_reason
        CHECK (reason IS NULL OR reason IN ('due_review', 'low_mastery', 'recent_error', 'manual'));
        RAISE NOTICE 'Added constraint: chk_pq_reason';
    END IF;
END $$;

-- priority 範圍檢查
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'chk_pq_priority'
    ) THEN
        ALTER TABLE practice_queue
        ADD CONSTRAINT chk_pq_priority
        CHECK (priority BETWEEN 0 AND 100);
        RAISE NOTICE 'Added constraint: chk_pq_priority';
    END IF;
END $$;

-- ==========================================
-- 階段 2：添加唯一約束
-- ==========================================

-- 2.1 防止重複知識點（基於內容的唯一性）
-- 注意：這個約束可能需要先清理重複數據
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uk_kp_content'
    ) THEN
        -- 先檢查是否有重複
        IF NOT EXISTS (
            SELECT 1
            FROM knowledge_points
            WHERE is_deleted = FALSE
            GROUP BY key_point, original_phrase, correction
            HAVING COUNT(*) > 1
        ) THEN
            -- 創建部分唯一索引（只對未刪除的記錄生效）
            CREATE UNIQUE INDEX uk_kp_content
            ON knowledge_points(key_point, original_phrase, correction)
            WHERE is_deleted = FALSE;
            RAISE NOTICE 'Added unique constraint: uk_kp_content';
        ELSE
            RAISE WARNING 'Cannot add uk_kp_content - duplicate data exists. Please clean up first.';
        END IF;
    END IF;
END $$;

-- 2.2 防止同一知識點多個原始錯誤（已由 UNIQUE 約束保證）
-- original_errors.knowledge_point_id 已經有 UNIQUE 約束

-- ==========================================
-- 階段 3：添加性能優化索引
-- ==========================================

-- 3.1 knowledge_points 表的優化索引

-- 組合索引：category + mastery_level（用於分類查詢和推薦系統）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_kp_category_mastery'
    ) THEN
        CREATE INDEX idx_kp_category_mastery
        ON knowledge_points(category, mastery_level)
        WHERE is_deleted = FALSE;
        RAISE NOTICE 'Added index: idx_kp_category_mastery';
    END IF;
END $$;

-- 索引：mistake_count（用於找出高錯誤率的知識點）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_kp_mistake_count'
    ) THEN
        CREATE INDEX idx_kp_mistake_count
        ON knowledge_points(mistake_count DESC)
        WHERE is_deleted = FALSE AND mistake_count > 0;
        RAISE NOTICE 'Added index: idx_kp_mistake_count';
    END IF;
END $$;

-- 3.2 review_examples 表的優化索引

-- 索引：is_correct（用於統計分析）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_re_is_correct'
    ) THEN
        CREATE INDEX idx_re_is_correct
        ON review_examples(is_correct, knowledge_point_id);
        RAISE NOTICE 'Added index: idx_re_is_correct';
    END IF;
END $$;

-- 3.3 study_sessions 表的優化索引

-- 索引：mode + started_at（用於按模式查詢會話）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_ss_mode_time'
    ) THEN
        CREATE INDEX idx_ss_mode_time
        ON study_sessions(mode, started_at DESC)
        WHERE mode IS NOT NULL;
        RAISE NOTICE 'Added index: idx_ss_mode_time';
    END IF;
END $$;

-- 3.4 daily_records 表的優化索引

-- 索引：goal_achieved（用於目標達成統計）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'idx_dr_goal_achieved'
    ) THEN
        CREATE INDEX idx_dr_goal_achieved
        ON daily_records(goal_achieved, date DESC)
        WHERE daily_goal IS NOT NULL;
        RAISE NOTICE 'Added index: idx_dr_goal_achieved';
    END IF;
END $$;

-- ==========================================
-- 階段 4：添加外鍵約束（補充可能缺失的）
-- ==========================================

-- 注意：根據 schema 分析，大部分外鍵約束已存在
-- 這裡只是確保所有必要的外鍵都存在

-- 確保 knowledge_point_versions 的外鍵存在
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'knowledge_point_versions_knowledge_point_id_fkey'
    ) THEN
        ALTER TABLE knowledge_point_versions
        ADD CONSTRAINT knowledge_point_versions_knowledge_point_id_fkey
        FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id) ON DELETE CASCADE;
        RAISE NOTICE 'Added foreign key: knowledge_point_versions -> knowledge_points';
    END IF;
END $$;

-- ==========================================
-- 驗證約束添加結果
-- ==========================================

-- 顯示所有添加的約束
SELECT 
    'CHECK Constraints' as constraint_type,
    COUNT(*) as count
FROM pg_constraint
WHERE contype = 'c'
  AND conrelid IN (
    SELECT oid FROM pg_class 
    WHERE relname IN ('knowledge_points', 'tags', 'study_sessions', 
                     'daily_records', 'weekly_goals', 'practice_queue')
  )
UNION ALL
SELECT 
    'UNIQUE Constraints' as constraint_type,
    COUNT(*) as count
FROM pg_constraint
WHERE contype = 'u'
  AND conrelid IN (
    SELECT oid FROM pg_class 
    WHERE relname IN ('knowledge_points', 'original_errors', 'tags')
  )
UNION ALL
SELECT 
    'FOREIGN KEY Constraints' as constraint_type,
    COUNT(*) as count
FROM pg_constraint
WHERE contype = 'f'
  AND conrelid IN (
    SELECT oid FROM pg_class 
    WHERE relname IN ('original_errors', 'review_examples', 'knowledge_point_tags',
                     'knowledge_point_versions', 'practice_queue')
  )
UNION ALL
SELECT 
    'Performance Indexes' as constraint_type,
    COUNT(*) as count
FROM pg_indexes
WHERE tablename IN ('knowledge_points', 'review_examples', 'study_sessions', 
                   'daily_records', 'practice_queue')
  AND indexname LIKE 'idx_%';

-- ==========================================
-- 成功訊息
-- ==========================================

SELECT '✅ Database constraints migration completed successfully!' as status;