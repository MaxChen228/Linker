# 03. 資料庫約束與完整性修復

## 優先級: MEDIUM
## 預估時間: 8-12 小時
## 狀態: 🚧 IN_PROGRESS [@agent-1 at:2025-08-14 16:30]
## 最後更新: 2025-08-14 19:16
## 進度: 60% 完成

### 背景
當前資料庫 schema 缺少關鍵的外鍵約束和檢查約束，可能導致數據不一致。

### 子任務清單

#### A. 分析現有 Schema (2小時)
- [x] 審查 `core/database/schema.sql`
  - [x] 列出所有表結構
  - [x] 識別缺失的約束
  - [x] 評估約束影響

- [x] 數據完整性檢查
  - [x] 檢查孤立記錄
  - [x] 驗證數據類型一致性
  - [x] 查找重複數據

#### B. 外鍵約束實現 (3小時)
- [x] 創建遷移腳本 `add_database_constraints.sql`
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

### 進度記錄

#### 2025-08-14 19:16 - Agent-1
**已完成項目：**
1. ✅ 分析現有 Schema
   - 審查了 11 個表的結構
   - 識別出缺少的檢查約束和唯一約束
   - 創建了詳細的分析報告 `docs/database_constraints_analysis.md`

2. ✅ 數據完整性檢查
   - 創建了 `scripts/check_data_integrity.sql` 檢查腳本
   - 發現並修復了 22 個重複記錄（ID 重複和內容重複）
   - 創建了 `scripts/fix_duplicate_data.py` 自動修復工具

3. ✅ 創建遷移腳本
   - 完成了 `scripts/add_database_constraints.sql`
   - 包含 4 個階段：檢查約束、唯一約束、性能索引、外鍵補充
   - 使用 DO 塊避免重複添加約束

**待完成項目：**
- [ ] 測試外鍵約束（級聯刪除、引用完整性）
- [ ] 測試檢查約束（無效數據插入、錯誤訊息）
- [ ] 測試唯一約束
- [ ] 分析查詢模式並創建性能索引
- [ ] 制定遷移執行計劃和備份策略

**關鍵發現：**
- 現有 schema 已包含大部分外鍵約束，設計良好
- 主要缺失：category 值域檢查、時間邏輯檢查、統計數據一致性檢查
- JSON 模式下發現大量測試數據重複（已清理）

**創建的文件：**
- `docs/database_constraints_analysis.md` - 約束分析報告
- `scripts/check_data_integrity.sql` - 數據完整性檢查
- `scripts/add_database_constraints.sql` - 約束添加遷移腳本
- `scripts/fix_duplicate_data.py` - 重複數據修復工具
- `data/knowledge.json.backup_20250814_191448` - 數據備份

**Commits：**
- 158f053: chore: agent-1 claiming task-03 database constraints
- 0e498fa: feat: 完成資料庫約束任務第一階段
