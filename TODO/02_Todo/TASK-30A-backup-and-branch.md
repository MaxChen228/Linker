# TASK-30A: 完整系統備份和分支管理

- **優先級**: 🔴 CRITICAL
- **預計時間**: 4-6 小時
- **關聯組件**: 整個專案, git, 資料庫
- **父任務**: TASK-30 純 Database 系統重構專案
- **前置條件**: 無
- **後續任務**: TASK-30B

---

## 🎯 任務目標

建立完整的系統備份和安全的分支管理策略，確保在重構過程中可以安全回滾到任何穩定狀態。

## ✅ 驗收標準

### 數據備份
- [ ] 創建完整的 JSON 數據備份（knowledge.json, practice_log.json）
- [ ] 創建資料庫完整備份（schema + data）
- [ ] 驗證備份完整性和可恢復性
- [ ] 備份存放在安全位置且有版本標記

### 分支管理
- [ ] 創建 `feature/pure-database-migration` 主分支
- [ ] 設置分支保護規則
- [ ] 創建子任務分支模板
- [ ] 建立 PR 模板和 review checklist

### 回滾準備
- [ ] 創建快速回滾腳本
- [ ] 測試回滾流程的有效性
- [ ] 建立緊急恢復程序文檔
- [ ] 設置系統狀態檢查點

## 📋 詳細執行步驟

### 1️⃣ 數據完整備份 (1-2 小時)

#### JSON 數據備份
```bash
# 創建備份目錄
mkdir -p backups/pure-db-migration/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/pure-db-migration/$(date +%Y%m%d_%H%M%S)"

# 備份所有 JSON 文件
cp data/knowledge.json "$BACKUP_DIR/knowledge_backup.json"
cp data/practice_log.json "$BACKUP_DIR/practice_log_backup.json"

# 創建數據清單
echo "JSON Backup created at $(date)" > "$BACKUP_DIR/backup_manifest.txt"
echo "Files:" >> "$BACKUP_DIR/backup_manifest.txt"
ls -la "$BACKUP_DIR" >> "$BACKUP_DIR/backup_manifest.txt"
```

#### 資料庫備份
```bash
# PostgreSQL 完整備份
pg_dump -h localhost -U linker_user -d linker_db \
  --verbose --create --clean --if-exists \
  --format=custom \
  --file="$BACKUP_DIR/database_full_backup.dump"

# Schema 單獨備份
pg_dump -h localhost -U linker_user -d linker_db \
  --schema-only --verbose \
  --file="$BACKUP_DIR/schema_backup.sql"

# 數據單獨備份
pg_dump -h localhost -U linker_user -d linker_db \
  --data-only --verbose \
  --file="$BACKUP_DIR/data_backup.sql"
```

#### 備份驗證
```bash
# 驗證 JSON 文件完整性
python3 -c "
import json
import sys

files = [
    '$BACKUP_DIR/knowledge_backup.json',
    '$BACKUP_DIR/practice_log_backup.json'
]

for file in files:
    try:
        with open(file, 'r') as f:
            data = json.load(f)
        print(f'✅ {file}: Valid JSON, {len(data)} records')
    except Exception as e:
        print(f'❌ {file}: Invalid - {e}')
        sys.exit(1)

print('🎉 All JSON backups verified successfully')
"

# 驗證資料庫備份
psql -h localhost -U linker_user -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables 
ORDER BY schemaname, tablename;" \
> "$BACKUP_DIR/table_stats_before.txt"
```

### 2️⃣ 分支策略設置 (1 小時)

#### 創建主要分支
```bash
# 確保在最新的 main 分支
git checkout main
git pull origin main

# 創建特性分支
git checkout -b feature/pure-database-migration
git push -u origin feature/pure-database-migration

# 創建子任務分支模板
git checkout -b task-30a-backup
git push -u origin task-30a-backup
```

#### 設置分支保護（GitHub CLI）
```bash
# 保護主分支
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/tests","ci/lint"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null

# 保護特性分支
gh api repos/:owner/:repo/branches/feature/pure-database-migration/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/tests"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field restrictions=null
```

### 3️⃣ 回滾系統準備 (1-2 小時)

#### 創建回滾腳本
```bash
cat > scripts/emergency_rollback.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="$1"
if [[ -z "$BACKUP_DIR" ]]; then
    echo "Usage: $0 <backup_directory>"
    echo "Available backups:"
    ls -la backups/pure-db-migration/
    exit 1
fi

echo "🚨 Emergency Rollback Starting..."
echo "Backup source: $BACKUP_DIR"

# 1. 停止應用服務
echo "Stopping application..."
pkill -f "uvicorn web.main:app" || true

# 2. 恢復資料庫
echo "Restoring database..."
dropdb --if-exists linker_db_temp
createdb linker_db_temp
pg_restore -d linker_db_temp "$BACKUP_DIR/database_full_backup.dump"

# 3. 恢復 JSON 文件
echo "Restoring JSON files..."
cp "$BACKUP_DIR/knowledge_backup.json" data/knowledge.json
cp "$BACKUP_DIR/practice_log_backup.json" data/practice_log.json

# 4. 切換資料庫
echo "Switching databases..."
psql -c "ALTER DATABASE linker_db RENAME TO linker_db_broken;"
psql -c "ALTER DATABASE linker_db_temp RENAME TO linker_db;"

echo "✅ Rollback completed successfully"
echo "⚠️  Please restart the application manually"
EOF

chmod +x scripts/emergency_rollback.sh
```

#### 測試回滾流程
```bash
# 創建測試備份
TEST_BACKUP_DIR="backups/test_rollback_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEST_BACKUP_DIR"
cp data/knowledge.json "$TEST_BACKUP_DIR/knowledge_backup.json"
cp data/practice_log.json "$TEST_BACKUP_DIR/practice_log_backup.json"

# 模擬數據庫備份（測試用）
pg_dump -h localhost -U linker_user -d linker_db \
  --format=custom \
  --file="$TEST_BACKUP_DIR/database_full_backup.dump"

# 測試回滾腳本（乾運行）
echo "Testing rollback script..."
bash -n scripts/emergency_rollback.sh
echo "✅ Rollback script syntax is valid"
```

### 4️⃣ 文檔和模板創建 (1 小時)

#### 子任務 PR 模板
```bash
cat > .github/pull_request_template.md << 'EOF'
## 子任務完成檢查清單

### 基本資訊
- **任務 ID**: TASK-30X
- **任務名稱**: 
- **預計時間**: 
- **實際耗時**: 

### 技術變更
- [ ] 代碼變更經過 code review
- [ ] 所有測試通過（`pytest --cov=core --cov=web`）
- [ ] Linting 通過（`ruff check . && ruff format .`）
- [ ] 沒有新的安全漏洞引入

### 數據安全
- [ ] 創建了變更前的數據備份
- [ ] 驗證了數據遷移的正確性
- [ ] 測試了回滾流程

### 文檔更新
- [ ] 更新了相關技術文檔
- [ ] 更新了 CLAUDE.md（如有需要）
- [ ] 記錄了重要的設計決策

### 測試覆蓋
- [ ] 添加了新功能的單元測試
- [ ] 更新了集成測試
- [ ] 手動測試了核心功能

### 部署準備
- [ ] 確認環境變量需求
- [ ] 確認資料庫遷移需求
- [ ] 確認向後兼容性

## 風險評估

### 高風險項目
- [ ] 無高風險變更
- [ ] 已識別風險並制定緩解措施

### 回滾計劃
- [ ] 明確的回滾步驟
- [ ] 回滾測試通過

## 審查者檢查清單

- [ ] 代碼邏輯正確且高效
- [ ] 安全考量充分
- [ ] 測試覆蓋充分
- [ ] 文檔清晰完整
- [ ] 與整體架構一致
EOF
```

#### 緊急聯絡和程序文檔
```bash
cat > docs/EMERGENCY_PROCEDURES.md << 'EOF'
# 🚨 緊急程序指南

## 立即聯絡資訊
- **Tech Lead**: [聯絡方式]
- **DevOps**: [聯絡方式]
- **數據庫管理員**: [聯絡方式]

## 緊急回滾
```bash
# 立即回滾到最近備份
./scripts/emergency_rollback.sh backups/pure-db-migration/[LATEST_BACKUP]

# 切換到穩定分支
git checkout main
git reset --hard origin/main
```

## 數據恢復
1. 停止應用服務
2. 執行回滾腳本
3. 驗證數據完整性
4. 重新啟動服務
5. 通知相關人員

## 狀態檢查
```bash
# 檢查應用狀態
curl -f http://localhost:8000/health || echo "❌ App down"

# 檢查資料庫連接
psql -h localhost -U linker_user -d linker_db -c "SELECT 1;" || echo "❌ DB down"

# 檢查重要功能
python3 scripts/test_database_mode.py
```
EOF
```

## 🔧 執行驗證

### 備份完整性檢查
```bash
# 驗證所有備份文件存在且有效
ls -la "$BACKUP_DIR"
file "$BACKUP_DIR"/*

# 驗證 JSON 數據完整性
python3 -c "
import json
with open('$BACKUP_DIR/knowledge_backup.json') as f:
    knowledge = json.load(f)
with open('$BACKUP_DIR/practice_log_backup.json') as f:
    practice = json.load(f)
print(f'Knowledge points: {len(knowledge)}')
print(f'Practice records: {len(practice)}')
"

# 驗證資料庫備份
pg_restore --list "$BACKUP_DIR/database_full_backup.dump" | head -20
```

### 分支保護驗證
```bash
# 檢查分支保護設置
gh api repos/:owner/:repo/branches/main/protection | jq '.required_status_checks'
gh api repos/:owner/:repo/branches/feature/pure-database-migration/protection | jq '.required_status_checks'
```

### 回滾測試
```bash
# 測試緊急回滾腳本
bash -n scripts/emergency_rollback.sh
echo "Script syntax validation: ✅"

# 驗證備份可恢復性（使用測試資料庫）
createdb test_restore_db
pg_restore -d test_restore_db "$BACKUP_DIR/database_full_backup.dump"
psql -d test_restore_db -c "SELECT COUNT(*) FROM knowledge_points;"
dropdb test_restore_db
```

## 📝 執行筆記

### 完成檢查清單
- [ ] 所有 JSON 數據已備份並驗證
- [ ] 資料庫完整備份已創建並測試
- [ ] 分支策略已設置並保護
- [ ] 回滾腳本已創建並測試
- [ ] 緊急程序文檔已建立
- [ ] 團隊已通知備份位置和程序

### 風險提醒
- ⚠️ 定期檢查備份存儲空間
- ⚠️ 每週驗證一次備份完整性
- ⚠️ 確保團隊成員了解緊急程序

## 🔍 審查意見 (For Reviewer)

_(留空，供 reviewer 填寫)_

---

**✅ 任務完成標準**: 所有備份驗證通過，分支保護啟用，回滾流程測試成功，團隊成員確認了解緊急程序。