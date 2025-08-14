# 03. 資料庫約束與完整性修復

## 優先級: MEDIUM
## 預估時間: 8-12 小時
## 狀態: 🚧 IN_PROGRESS [@agent-1 at:2025-08-14 16:30]

### 背景
當前資料庫 schema 缺少關鍵的外鍵約束和檢查約束，可能導致數據不一致。

### 子任務清單

#### A. 分析現有 Schema (2小時)
- [ ] 審查 `core/database/schema.sql`
  - [ ] 列出所有表結構
  - [ ] 識別缺失的約束
  - [ ] 評估約束影響

- [ ] 數據完整性檢查
  - [ ] 檢查孤立記錄
  - [ ] 驗證數據類型一致性
  - [ ] 查找重複數據

#### B. 外鍵約束實現 (3小時)
- [ ] 創建遷移腳本 `add_foreign_keys.sql`
  ```sql
  -- knowledge_points 表
  ALTER TABLE knowledge_points
  ADD CONSTRAINT fk_kp_user_id
  FOREIGN KEY (user_id) REFERENCES users(id)
  ON DELETE CASCADE;

  -- original_errors 表
  ALTER TABLE original_errors
  ADD CONSTRAINT fk_oe_knowledge_point_id
  FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id)
  ON DELETE CASCADE;

  -- review_examples 表
  ALTER TABLE review_examples
  ADD CONSTRAINT fk_re_knowledge_point_id
  FOREIGN KEY (knowledge_point_id) REFERENCES knowledge_points(id)
  ON DELETE CASCADE;
  ```

- [ ] 測試外鍵約束
  - [ ] 測試級聯刪除
  - [ ] 測試引用完整性
  - [ ] 驗證錯誤處理

#### C. 檢查約束實現 (2小時)
- [ ] 添加數據驗證約束
  ```sql
  -- mastery_level 範圍檢查
  ALTER TABLE knowledge_points
  ADD CONSTRAINT chk_mastery_level
  CHECK (mastery_level >= 0 AND mastery_level <= 1);

  -- category 有效值檢查
  ALTER TABLE knowledge_points
  ADD CONSTRAINT chk_category
  CHECK (category IN ('systematic', 'isolated', 'enhancement', 'other'));

  -- 時間邏輯檢查
  ALTER TABLE knowledge_points
  ADD CONSTRAINT chk_review_time
  CHECK (next_review >= last_reviewed OR next_review IS NULL);
  ```

- [ ] 測試檢查約束
  - [ ] 測試無效數據插入
  - [ ] 驗證錯誤訊息
  - [ ] 確認既有數據符合約束

#### D. 唯一約束實現 (1.5小時)
- [ ] 添加唯一性約束
  ```sql
  -- 防止重複知識點
  ALTER TABLE knowledge_points
  ADD CONSTRAINT uk_knowledge_content
  UNIQUE (key_point, original_phrase, chinese_context);

  -- 用戶郵箱唯一
  ALTER TABLE users
  ADD CONSTRAINT uk_user_email
  UNIQUE (email);
  ```

- [ ] 處理既有重複數據
  - [ ] 識別重複記錄
  - [ ] 決定保留策略
  - [ ] 執行數據清理

#### E. 索引優化 (2小時)
- [ ] 分析查詢模式
  - [ ] 使用 EXPLAIN ANALYZE
  - [ ] 識別慢查詢
  - [ ] 確定索引需求

- [ ] 創建性能索引
  ```sql
  -- 常用查詢索引
  CREATE INDEX idx_kp_category_mastery
  ON knowledge_points(category, mastery_level)
  WHERE is_deleted = FALSE;

  -- 全文搜索優化
  CREATE INDEX idx_kp_search
  ON knowledge_points USING gin(to_tsvector('english', key_point));
  ```

#### F. 遷移執行計劃 (1.5小時)
- [ ] 備份策略
  - [ ] 完整數據備份
  - [ ] 記錄當前狀態
  - [ ] 準備回滾腳本

- [ ] 執行步驟
  1. [ ] 停止應用服務
  2. [ ] 執行備份
  3. [ ] 運行遷移腳本
  4. [ ] 驗證約束
  5. [ ] 重啟服務
  6. [ ] 監控錯誤

### 風險評估
- **高風險**: 外鍵約束可能阻止某些刪除操作
- **中風險**: 檢查約束可能拒絕既有的無效數據
- **低風險**: 索引可能暫時影響寫入性能

### 回滾計劃
```sql
-- 移除所有約束的回滾腳本
ALTER TABLE knowledge_points DROP CONSTRAINT IF EXISTS fk_kp_user_id;
ALTER TABLE knowledge_points DROP CONSTRAINT IF EXISTS chk_mastery_level;
ALTER TABLE knowledge_points DROP CONSTRAINT IF EXISTS uk_knowledge_content;
-- ... 其他約束
```

### 驗收標準
1. 所有約束成功添加
2. 既有數據符合新約束
3. 應用功能正常運行
4. 查詢性能提升 > 20%

### 相關文件
- `/Users/chenliangyu/Desktop/linker/core/database/schema.sql`
- `/Users/chenliangyu/Desktop/linker/scripts/init_database.py`
- PostgreSQL 文檔: https://www.postgresql.org/docs/current/ddl-constraints.html
