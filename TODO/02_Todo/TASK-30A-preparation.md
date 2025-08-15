# TASK-30A: 重構前置準備

- **優先級**: 🔴 CRITICAL
- **預計時間**: 2-3 小時
- **關聯組件**: 整個專案, git, 資料庫
- **父任務**: TASK-30 純 Database 系統重構專案
- **前置條件**: 無
- **後續任務**: TASK-30B~T (所有實施任務)

---

## 🎯 任務目標

完成純資料庫系統重構的基本準備工作，包括數據備份、開發環境配置和分支管理，確保重構過程安全可控。

## ✅ 驗收標準

### 數據安全
- [ ] 創建完整的系統備份（JSON + 資料庫）
- [ ] 驗證備份可恢復性
- [ ] 準備快速回滾腳本

### 開發環境
- [ ] 純資料庫開發環境可用（Docker）
- [ ] 環境變數正確配置
- [ ] 基本開發工具就緒

### 分支管理
- [ ] 創建重構專用分支
- [ ] 設置基本的分支保護
- [ ] 準備 PR 模板

## 📋 執行步驟

### 1️⃣ 快速備份 (30分鐘)

```bash
# 創建備份目錄
mkdir -p backups/pure-db-migration/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/pure-db-migration/$(date +%Y%m%d_%H%M%S)"

# 備份 JSON 數據
cp data/knowledge.json "$BACKUP_DIR/"
cp data/practice_log.json "$BACKUP_DIR/"

# 備份資料庫（如果存在）
if docker ps | grep -q postgres; then
    pg_dump -h localhost -U your_user -d your_db > "$BACKUP_DIR/database_backup.sql"
fi

# 創建回滾腳本
cat > scripts/emergency_rollback.sh << 'EOF'
#!/bin/bash
# 緊急回滾腳本
cp backups/pure-db-migration/latest/knowledge.json data/
cp backups/pure-db-migration/latest/practice_log.json data/
echo "✅ 已回滾到 JSON 模式"
EOF
chmod +x scripts/emergency_rollback.sh

echo "✅ 備份完成: $BACKUP_DIR"
```

### 2️⃣ 開發環境設置 (1-1.5小時)

```bash
# 創建簡化的 Docker 配置
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'
services:
  linker-db-dev:
    image: postgres:15-alpine
    container_name: linker-db-dev
    environment:
      POSTGRES_DB: linker_dev
      POSTGRES_USER: linker_dev_user
      POSTGRES_PASSWORD: linker_dev_pass
    ports:
      - "5433:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./core/database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U linker_dev_user -d linker_dev"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  postgres_dev_data:
EOF

# 創建開發環境變數
cat > .env.dev << 'EOF'
USE_DATABASE=true
DATABASE_URL=postgresql://linker_dev_user:linker_dev_pass@localhost:5433/linker_dev
GEMINI_API_KEY=your-key-here
DEBUG=true
EOF

# 一鍵啟動腳本
cat > scripts/start_dev.sh << 'EOF'
#!/bin/bash
echo "🚀 啟動純資料庫開發環境..."
docker-compose -f docker-compose.dev.yml up -d
echo "⏳ 等待資料庫啟動..."
sleep 10
cp .env.dev .env
echo "✅ 開發環境就緒"
echo "📝 啟動應用: uvicorn web.main:app --reload"
EOF
chmod +x scripts/start_dev.sh

echo "✅ 開發環境配置完成"
```

### 3️⃣ 分支和基本工具 (30分鐘)

```bash
# 創建分支
git checkout -b feature/pure-database-migration
git push -u origin feature/pure-database-migration

# 簡單的檢查腳本
cat > scripts/check_json_deps.sh << 'EOF'
#!/bin/bash
echo "🔍 檢查 JSON 依賴..."
if rg "import json|from json|json\." --type py -q; then
    echo "❌ 發現 JSON 依賴:"
    rg "import json|from json|json\." --type py -n
    exit 1
else
    echo "✅ 無 JSON 依賴"
fi
EOF
chmod +x scripts/check_json_deps.sh

# 測試資料庫連接的簡化腳本
cat > scripts/test_db.sh << 'EOF'
#!/bin/bash
export USE_DATABASE=true
export DATABASE_URL="postgresql://linker_dev_user:linker_dev_pass@localhost:5433/linker_dev"

python3 -c "
from core.database.adapter import get_knowledge_manager_async
import asyncio

async def test():
    try:
        manager = await get_knowledge_manager_async(use_database=True)
        stats = await manager.get_statistics_async()
        print('✅ 資料庫連接正常')
        return True
    except Exception as e:
        print(f'❌ 資料庫連接失敗: {e}')
        return False

if asyncio.run(test()):
    exit(0)
else:
    exit(1)
"
EOF
chmod +x scripts/test_db.sh

echo "✅ 分支和工具準備完成"
```

## 🔧 快速驗證

```bash
# 驗證備份
ls -la "$BACKUP_DIR"

# 測試開發環境
./scripts/start_dev.sh
sleep 15
./scripts/test_db.sh

# 測試工具
./scripts/check_json_deps.sh

echo "🎉 前置準備完成！可以開始實施重構"
```

## 📝 執行筆記

### 重要文件
- 備份位置: `backups/pure-db-migration/[timestamp]/`
- 開發配置: `docker-compose.dev.yml`, `.env.dev`
- 工具腳本: `scripts/start_dev.sh`, `scripts/check_json_deps.sh`, `scripts/test_db.sh`
- 回滾腳本: `scripts/emergency_rollback.sh`

### 完成檢查
- [ ] 備份文件存在且完整
- [ ] Docker 環境可以啟動
- [ ] 資料庫連接測試通過
- [ ] 分支創建成功
- [ ] 基本工具腳本可用

## 🔍 審查意見 (For Reviewer)

_(留空，供 reviewer 填寫)_

---

**✅ 任務完成標準**: 備份創建完成，開發環境可以啟動並連接資料庫，基本工具腳本運行正常，分支管理就緒。