# 資料庫約束分析報告

## 現有表結構清單

### 1. knowledge_points (知識點主表)
- **主鍵**: id (SERIAL)
- **唯一約束**: uuid
- **檢查約束**:
  - mastery_level: CHECK (mastery_level >= 0 AND mastery_level <= 1) ✅
  - mistake_count: CHECK (mistake_count >= 0) ✅
  - correct_count: CHECK (correct_count >= 0) ✅
- **外鍵約束**: 無 ❌
- **索引**: 
  - idx_kp_category_subtype
  - idx_kp_next_review (條件索引)
  - idx_kp_mastery_level (條件索引)
  - idx_kp_created_at
  - idx_kp_key_point_trgm (全文搜索)

### 2. original_errors (原始錯誤表)
- **主鍵**: id (SERIAL)
- **唯一約束**: knowledge_point_id ✅
- **外鍵約束**: knowledge_point_id → knowledge_points(id) ON DELETE CASCADE ✅
- **索引**: idx_oe_knowledge_point

### 3. review_examples (複習例句表)
- **主鍵**: id (SERIAL)
- **外鍵約束**: knowledge_point_id → knowledge_points(id) ON DELETE CASCADE ✅
- **索引**: 
  - idx_re_knowledge_point_time
  - idx_re_timestamp

### 4. tags (標籤表)
- **主鍵**: id (SERIAL)
- **唯一約束**: name ✅
- **檢查約束**: 無 ❌ (color 格式未驗證)

### 5. knowledge_point_tags (關聯表)
- **複合主鍵**: (knowledge_point_id, tag_id) ✅
- **外鍵約束**:
  - knowledge_point_id → knowledge_points(id) ON DELETE CASCADE ✅
  - tag_id → tags(id) ON DELETE CASCADE ✅

### 6. knowledge_point_versions (版本歷史)
- **主鍵**: id (SERIAL)
- **唯一約束**: (knowledge_point_id, version_number) ✅
- **外鍵約束**: knowledge_point_id → knowledge_points(id) ON DELETE CASCADE ✅
- **索引**: idx_kpv_kp_version

### 7. study_sessions (學習會話)
- **主鍵**: id (SERIAL)
- **唯一約束**: session_id (UUID) ✅
- **檢查約束**: 無 ❌ (數值合理性未驗證)
- **索引**: idx_ss_started_at

### 8. daily_records (每日記錄)
- **主鍵**: date ✅
- **檢查約束**: 無 ❌ (數值合理性未驗證)

### 9. weekly_goals (週目標)
- **主鍵**: week_start
- **檢查約束**: CHECK (week_end > week_start) ✅

### 10. grammar_patterns (文法模式)
- **主鍵**: id (SERIAL)
- **檢查約束**: CHECK (difficulty_level BETWEEN 1 AND 5) ✅
- **索引**:
  - idx_gp_pattern_type
  - idx_gp_difficulty

### 11. practice_queue (練習佇列)
- **主鍵**: id (SERIAL)
- **唯一約束**: (knowledge_point_id, scheduled_for) ✅
- **外鍵約束**: knowledge_point_id → knowledge_points(id) ON DELETE CASCADE ✅
- **索引**: idx_pq_scheduled (條件索引)

## 缺失的約束分析

### 🔴 關鍵缺失

1. **knowledge_points 表缺少重要約束**:
   - ❌ category 值域檢查 (應限制為 'systematic', 'isolated', 'enhancement', 'other')
   - ❌ subtype 值域檢查
   - ❌ 防止重複知識點的唯一約束 (key_point, original_phrase, correction 的組合)
   - ❌ next_review 與 last_seen 的時間邏輯檢查

2. **數值合理性檢查缺失**:
   - ❌ study_sessions: questions_correct <= questions_attempted
   - ❌ daily_records: questions_correct <= questions_attempted
   - ❌ weekly_goals: 目標值的合理範圍

3. **格式驗證缺失**:
   - ❌ tags.color: HEX 顏色格式驗證
   - ❌ study_sessions.mode: 有效值檢查 ('practice', 'review', 'test')
   - ❌ practice_queue.reason: 有效值檢查

### 🟡 建議改進

1. **防止數據異常**:
   - knowledge_points.chinese_context 欄位在 schema 中不存在（但在任務文檔中提到）
   - 需要確認 users 表是否存在（任務文檔中提到但 schema 中未見）

2. **性能優化索引**:
   - knowledge_points 表的 category + mastery_level 組合索引
   - review_examples 表的 is_correct 索引（用於統計分析）

## 數據完整性風險

### 高風險
1. **孤立記錄風險**: 雖然有外鍵約束，但需檢查現有數據
2. **重複知識點**: 無唯一約束可能導致相同知識點重複記錄
3. **無效類別**: category/subtype 無約束可能包含任意值

### 中風險
1. **時間邏輯錯誤**: next_review 可能早於 last_seen
2. **統計數據不一致**: correct_count 可能超過 attempted_count

### 低風險
1. **格式不一致**: 顏色代碼、模式類型等無格式驗證

## 建議執行順序

1. **階段一：數據清理** (2小時)
   - 檢查並修復現有數據的一致性問題
   - 識別並處理重複記錄

2. **階段二：添加檢查約束** (2小時)
   - 實施 category/subtype 值域檢查
   - 添加數值合理性檢查
   - 實施格式驗證

3. **階段三：添加唯一約束** (1.5小時)
   - 防止重複知識點
   - 確保數據唯一性

4. **階段四：優化索引** (2小時)
   - 分析查詢模式
   - 創建性能索引

5. **階段五：測試與驗證** (1.5小時)
   - 測試所有約束
   - 驗證應用功能
   - 性能測試

## 注意事項

1. **users 表問題**: 任務文檔中提到的 users 表在當前 schema 中不存在，需要確認是否為未來擴展
2. **chinese_context 欄位**: 任務文檔中提到但 schema 中不存在此欄位
3. **外鍵約束**: 大部分表已有良好的外鍵約束設計，主要問題在檢查約束和唯一約束