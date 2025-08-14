-- 資料完整性檢查腳本
-- 用於檢測現有數據中的問題，為添加約束做準備

-- ==========================================
-- 1. 檢查孤立記錄
-- ==========================================

-- 檢查 original_errors 中的孤立記錄
SELECT 'Orphaned original_errors' as check_type, COUNT(*) as count
FROM original_errors oe
LEFT JOIN knowledge_points kp ON oe.knowledge_point_id = kp.id
WHERE kp.id IS NULL;

-- 檢查 review_examples 中的孤立記錄
SELECT 'Orphaned review_examples' as check_type, COUNT(*) as count
FROM review_examples re
LEFT JOIN knowledge_points kp ON re.knowledge_point_id = kp.id
WHERE kp.id IS NULL;

-- 檢查 knowledge_point_tags 中的孤立記錄
SELECT 'Orphaned knowledge_point_tags (missing kp)' as check_type, COUNT(*) as count
FROM knowledge_point_tags kpt
LEFT JOIN knowledge_points kp ON kpt.knowledge_point_id = kp.id
WHERE kp.id IS NULL;

SELECT 'Orphaned knowledge_point_tags (missing tag)' as check_type, COUNT(*) as count
FROM knowledge_point_tags kpt
LEFT JOIN tags t ON kpt.tag_id = t.id
WHERE t.id IS NULL;

-- 檢查 knowledge_point_versions 中的孤立記錄
SELECT 'Orphaned knowledge_point_versions' as check_type, COUNT(*) as count
FROM knowledge_point_versions kpv
LEFT JOIN knowledge_points kp ON kpv.knowledge_point_id = kp.id
WHERE kp.id IS NULL;

-- 檢查 practice_queue 中的孤立記錄
SELECT 'Orphaned practice_queue' as check_type, COUNT(*) as count
FROM practice_queue pq
LEFT JOIN knowledge_points kp ON pq.knowledge_point_id = kp.id
WHERE kp.id IS NULL;

-- ==========================================
-- 2. 數據類型一致性檢查
-- ==========================================

-- 檢查 knowledge_points.category 的值域
SELECT 'Invalid category values' as check_type, 
       category, 
       COUNT(*) as count
FROM knowledge_points
WHERE category NOT IN ('systematic', 'isolated', 'enhancement', 'other')
  AND is_deleted = FALSE
GROUP BY category;

-- 檢查 mastery_level 範圍
SELECT 'Invalid mastery_level' as check_type, COUNT(*) as count
FROM knowledge_points
WHERE (mastery_level < 0 OR mastery_level > 1)
  AND is_deleted = FALSE;

-- 檢查負數計數
SELECT 'Negative mistake_count' as check_type, COUNT(*) as count
FROM knowledge_points
WHERE mistake_count < 0;

SELECT 'Negative correct_count' as check_type, COUNT(*) as count
FROM knowledge_points
WHERE correct_count < 0;

-- 檢查時間邏輯
SELECT 'Invalid time logic (next_review < last_seen)' as check_type, COUNT(*) as count
FROM knowledge_points
WHERE next_review IS NOT NULL 
  AND last_seen IS NOT NULL
  AND next_review < last_seen
  AND is_deleted = FALSE;

-- ==========================================
-- 3. 查找重複數據
-- ==========================================

-- 查找重複的知識點（基於 key_point, original_phrase, correction）
WITH duplicates AS (
    SELECT 
        key_point,
        original_phrase,
        correction,
        COUNT(*) as duplicate_count
    FROM knowledge_points
    WHERE is_deleted = FALSE
    GROUP BY key_point, original_phrase, correction
    HAVING COUNT(*) > 1
)
SELECT 
    'Duplicate knowledge points' as check_type,
    COUNT(*) as groups_count,
    SUM(duplicate_count) as total_duplicates
FROM duplicates;

-- 詳細列出重複的知識點
SELECT 
    kp.id,
    kp.key_point,
    kp.original_phrase,
    kp.correction,
    kp.category,
    kp.created_at
FROM knowledge_points kp
INNER JOIN (
    SELECT 
        key_point,
        original_phrase,
        correction
    FROM knowledge_points
    WHERE is_deleted = FALSE
    GROUP BY key_point, original_phrase, correction
    HAVING COUNT(*) > 1
) dup ON kp.key_point = dup.key_point 
     AND kp.original_phrase = dup.original_phrase 
     AND kp.correction = dup.correction
WHERE kp.is_deleted = FALSE
ORDER BY kp.key_point, kp.original_phrase, kp.created_at;

-- ==========================================
-- 4. 檢查格式問題
-- ==========================================

-- 檢查 tags.color 格式（應該是 7 位的 HEX 顏色）
SELECT 'Invalid color format in tags' as check_type, COUNT(*) as count
FROM tags
WHERE color IS NOT NULL 
  AND color !~ '^#[0-9A-Fa-f]{6}$';

-- 檢查 study_sessions.mode 值域
SELECT 'Invalid mode in study_sessions' as check_type, 
       mode, 
       COUNT(*) as count
FROM study_sessions
WHERE mode IS NOT NULL 
  AND mode NOT IN ('practice', 'review', 'test')
GROUP BY mode;

-- 檢查 practice_queue.reason 值域
SELECT 'Invalid reason in practice_queue' as check_type,
       reason,
       COUNT(*) as count
FROM practice_queue
WHERE reason IS NOT NULL
  AND reason NOT IN ('due_review', 'low_mastery', 'recent_error')
GROUP BY reason;

-- ==========================================
-- 5. 統計數據一致性
-- ==========================================

-- 檢查 study_sessions 中的邏輯錯誤
SELECT 'Invalid study_sessions (correct > attempted)' as check_type, COUNT(*) as count
FROM study_sessions
WHERE questions_correct > questions_attempted;

-- 檢查 daily_records 中的邏輯錯誤
SELECT 'Invalid daily_records (correct > attempted)' as check_type, COUNT(*) as count
FROM daily_records
WHERE questions_correct > questions_attempted;

-- 檢查 weekly_goals 的日期邏輯
SELECT 'Invalid weekly_goals (end <= start)' as check_type, COUNT(*) as count
FROM weekly_goals
WHERE week_end <= week_start;

-- ==========================================
-- 6. 總結報告
-- ==========================================

SELECT '=== Data Integrity Check Summary ===' as report;

-- 統計所有問題
WITH issues AS (
    SELECT COUNT(*) as orphaned_records FROM (
        SELECT id FROM original_errors oe
        LEFT JOIN knowledge_points kp ON oe.knowledge_point_id = kp.id
        WHERE kp.id IS NULL
        UNION ALL
        SELECT id FROM review_examples re
        LEFT JOIN knowledge_points kp ON re.knowledge_point_id = kp.id
        WHERE kp.id IS NULL
    ) orphans
),
duplicates AS (
    SELECT COUNT(*) as duplicate_groups
    FROM (
        SELECT key_point, original_phrase, correction
        FROM knowledge_points
        WHERE is_deleted = FALSE
        GROUP BY key_point, original_phrase, correction
        HAVING COUNT(*) > 1
    ) dup
),
invalid_data AS (
    SELECT COUNT(*) as invalid_values
    FROM knowledge_points
    WHERE (category NOT IN ('systematic', 'isolated', 'enhancement', 'other')
        OR mastery_level < 0 
        OR mastery_level > 1
        OR mistake_count < 0
        OR correct_count < 0)
      AND is_deleted = FALSE
)
SELECT 
    (SELECT orphaned_records FROM issues) as "Orphaned Records",
    (SELECT duplicate_groups FROM duplicates) as "Duplicate Groups",
    (SELECT invalid_values FROM invalid_data) as "Invalid Values",
    CASE 
        WHEN (SELECT orphaned_records FROM issues) = 0
         AND (SELECT duplicate_groups FROM duplicates) = 0
         AND (SELECT invalid_values FROM invalid_data) = 0
        THEN 'PASSED - Safe to add constraints'
        ELSE 'FAILED - Data cleanup required'
    END as "Status";

-- ==========================================
-- 7. 建議的修復查詢（註釋狀態，需手動執行）
-- ==========================================

-- 刪除孤立記錄（謹慎執行）
-- DELETE FROM original_errors WHERE knowledge_point_id NOT IN (SELECT id FROM knowledge_points);
-- DELETE FROM review_examples WHERE knowledge_point_id NOT IN (SELECT id FROM knowledge_points);
-- DELETE FROM knowledge_point_tags WHERE knowledge_point_id NOT IN (SELECT id FROM knowledge_points);
-- DELETE FROM knowledge_point_tags WHERE tag_id NOT IN (SELECT id FROM tags);
-- DELETE FROM knowledge_point_versions WHERE knowledge_point_id NOT IN (SELECT id FROM knowledge_points);
-- DELETE FROM practice_queue WHERE knowledge_point_id NOT IN (SELECT id FROM knowledge_points);

-- 修復無效的 category 值（設為 'other'）
-- UPDATE knowledge_points 
-- SET category = 'other' 
-- WHERE category NOT IN ('systematic', 'isolated', 'enhancement', 'other')
--   AND is_deleted = FALSE;

-- 修復無效的顏色格式
-- UPDATE tags 
-- SET color = '#' || SUBSTRING(color FROM 2 FOR 6)
-- WHERE color IS NOT NULL 
--   AND color !~ '^#[0-9A-Fa-f]{6}$';

-- 處理重複知識點（保留最早的）
-- WITH duplicates_to_delete AS (
--     SELECT id
--     FROM (
--         SELECT id, 
--                ROW_NUMBER() OVER (PARTITION BY key_point, original_phrase, correction 
--                                  ORDER BY created_at) as rn
--         FROM knowledge_points
--         WHERE is_deleted = FALSE
--     ) t
--     WHERE rn > 1
-- )
-- UPDATE knowledge_points 
-- SET is_deleted = TRUE, 
--     deleted_at = CURRENT_TIMESTAMP,
--     deleted_reason = 'Duplicate entry cleanup'
-- WHERE id IN (SELECT id FROM duplicates_to_delete);