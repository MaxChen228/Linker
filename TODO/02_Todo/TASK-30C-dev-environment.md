# TASK-30C: 開發環境準備和工具配置

- **優先級**: 🟠 HIGH
- **預計時間**: 4-6 小時
- **關聯組件**: Docker, scripts/, .env, development tools
- **父任務**: TASK-30 純 Database 系統重構專案
- **前置條件**: TASK-30A, TASK-30B 完成
- **後續任務**: TASK-30D~H (可並行)

---

## 🎯 任務目標

建立完整的純資料庫開發環境，包括 Docker 容器化、自動化腳本、開發工具配置，確保團隊成員可以快速啟動和切換到純資料庫模式進行開發。

## ✅ 驗收標準

### 環境配置
- [ ] Docker Compose 資料庫服務配置完成
- [ ] 一鍵啟動腳本 (setup_pure_db_dev.sh) 可用
- [ ] 環境變數配置模板和驗證
- [ ] 開發資料庫自動初始化和 seed data

### 開發工具
- [ ] 資料庫管理 CLI 工具就緒
- [ ] 代碼檢查和測試自動化腳本
- [ ] 性能監控和日誌工具配置
- [ ] 調試和診斷工具準備

### 團隊支援
- [ ] 開發環境設置文檔更新
- [ ] 故障排除指南完成
- [ ] 團隊培訓材料準備
- [ ] 環境驗證檢查清單

## 📋 詳細執行步驟

### 1️⃣ Docker 環境配置 (1.5-2 小時)

#### 創建 Docker Compose 配置
```bash
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL 開發資料庫
  linker-db-dev:
    image: postgres:15-alpine
    container_name: linker-db-dev
    environment:
      POSTGRES_DB: linker_dev
      POSTGRES_USER: linker_dev_user
      POSTGRES_PASSWORD: linker_dev_pass
      POSTGRES_INITDB_ARGS: "--auth-host=scram-sha-256"
    ports:
      - "5433:5432"  # 避免與系統 PostgreSQL 衝突
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./core/database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./scripts/seed_data.sql:/docker-entrypoint-initdb.d/02-seed.sql
      - ./scripts/dev_sample_data.sql:/docker-entrypoint-initdb.d/03-sample.sql
    networks:
      - linker-dev-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U linker_dev_user -d linker_dev"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  # Redis 緩存 (未來擴展)
  linker-redis-dev:
    image: redis:7-alpine
    container_name: linker-redis-dev
    ports:
      - "6380:6379"  # 避免與系統 Redis 衝突
    volumes:
      - redis_dev_data:/data
    networks:
      - linker-dev-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # 資料庫管理工具 (可選)
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: linker-pgadmin-dev
    environment:
      PGADMIN_DEFAULT_EMAIL: dev@linker.local
      PGADMIN_DEFAULT_PASSWORD: devpassword
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "8080:80"
    volumes:
      - pgadmin_dev_data:/var/lib/pgadmin
    networks:
      - linker-dev-network
    depends_on:
      linker-db-dev:
        condition: service_healthy

volumes:
  postgres_dev_data:
  redis_dev_data:
  pgadmin_dev_data:

networks:
  linker-dev-network:
    driver: bridge
EOF
```

#### 創建開發用 seed data
```bash
cat > scripts/seed_data.sql << 'EOF'
-- 基礎開發用 seed data
-- 這些是系統運行的最基本數據

-- 插入基本標籤
INSERT INTO tags (name, color, description) VALUES
  ('grammar', '#FF6B6B', '文法相關錯誤'),
  ('vocabulary', '#4ECDC4', '詞彙使用錯誤'),
  ('pronunciation', '#45B7D1', '發音相關問題'),
  ('structure', '#96CEB4', '句子結構問題'),
  ('tense', '#FFEAA7', '時態使用錯誤'),
  ('preposition', '#DDA0DD', '介詞使用錯誤')
ON CONFLICT (name) DO UPDATE SET
  color = EXCLUDED.color,
  description = EXCLUDED.description;

-- 插入系統初始化知識點（避免空資料庫問題）
INSERT INTO knowledge_points (
  key_point, category, subtype, explanation, 
  original_phrase, correction, mastery_level
) VALUES
  (
    'Subject-Verb Agreement Basic',
    'systematic',
    'grammar',
    'The subject and verb must agree in number (singular/plural).',
    'The students is happy',
    'The students are happy',
    0.5
  ),
  (
    'Article Usage with Countable Nouns',
    'systematic', 
    'grammar',
    'Use "a/an" with singular countable nouns, "the" for specific references.',
    'I need book',
    'I need a book',
    0.3
  ),
  (
    'Past Tense Formation',
    'systematic',
    'grammar', 
    'Regular verbs add -ed, irregular verbs have special forms.',
    'I go to school yesterday',
    'I went to school yesterday',
    0.7
  )
ON CONFLICT (key_point) DO UPDATE SET
  explanation = EXCLUDED.explanation,
  last_modified = CURRENT_TIMESTAMP;

-- 初始化每日記錄（今天）
INSERT INTO daily_records (date, total_practice_time, daily_goal)
VALUES (CURRENT_DATE, 0, 30)
ON CONFLICT (date) DO NOTHING;

-- 初始化本週目標
INSERT INTO weekly_goals (week_start, week_end, target_practice_days, target_questions)
VALUES (
  DATE_TRUNC('week', CURRENT_DATE),
  DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '6 days',
  5,
  50
) ON CONFLICT (week_start) DO NOTHING;

-- 創建開發用的學習會話
INSERT INTO study_sessions (session_id, started_at, ended_at, questions_attempted, questions_correct, mode)
VALUES (
  uuid_generate_v4(),
  CURRENT_TIMESTAMP - INTERVAL '1 hour',
  CURRENT_TIMESTAMP - INTERVAL '30 minutes', 
  10,
  7,
  'practice'
);
EOF
```

#### 創建豐富的開發樣本數據
```bash
cat > scripts/dev_sample_data.sql << 'EOF'
-- 開發環境樣本數據
-- 用於測試和開發的豐富數據集

-- 插入更多知識點樣本
INSERT INTO knowledge_points (
  key_point, category, subtype, explanation, 
  original_phrase, correction, mastery_level,
  mistake_count, correct_count
) VALUES
  (
    'Conditional Sentences Type 1',
    'systematic',
    'conditional',
    'If + present simple, will + base verb for real future possibilities.',
    'If it will rain, I stay home',
    'If it rains, I will stay home',
    0.4, 3, 2
  ),
  (
    'Modal Verbs - Ability',
    'systematic', 
    'modal',
    'Use "can" for present ability, "could" for past ability.',
    'I could swim when I was young, now I cannot',
    'I could swim when I was young, now I can''t',
    0.6, 2, 4
  ),
  (
    'Phrasal Verb - Turn On',
    'isolated',
    'phrasal_verb', 
    'Turn on = to activate or start a device.',
    'Please turn the light',
    'Please turn on the light',
    0.8, 1, 8
  ),
  (
    'Comparison Adjectives',
    'systematic',
    'comparison',
    'Add -er for short adjectives, use "more" for long adjectives.',
    'She is more tall than me',
    'She is taller than me',
    0.3, 4, 1
  ),
  (
    'Question Formation with "Do"',
    'systematic',
    'question',
    'Use "do/does" for present simple questions with main verbs.',
    'What you do for living?',
    'What do you do for a living?',
    0.5, 2, 3
  )
ON CONFLICT (key_point) DO NOTHING;

-- 插入原始錯誤記錄
INSERT INTO original_errors (
  knowledge_point_id, chinese_sentence, user_answer, correct_answer, timestamp
) 
SELECT 
  kp.id,
  '如果明天下雨，我會待在家裡。',
  'If it will rain tomorrow, I will stay at home.',
  'If it rains tomorrow, I will stay at home.',
  CURRENT_TIMESTAMP - INTERVAL '2 days'
FROM knowledge_points kp 
WHERE kp.key_point = 'Conditional Sentences Type 1';

-- 插入複習例句
INSERT INTO review_examples (
  knowledge_point_id, chinese_sentence, user_answer, correct_answer, is_correct, timestamp
)
SELECT 
  kp.id,
  '學生們很開心。',
  'The students are happy.',
  'The students are happy.',
  true,
  CURRENT_TIMESTAMP - INTERVAL '1 day'
FROM knowledge_points kp 
WHERE kp.key_point = 'Subject-Verb Agreement Basic';

-- 插入知識點標籤關聯
INSERT INTO knowledge_point_tags (knowledge_point_id, tag_id)
SELECT kp.id, t.id
FROM knowledge_points kp, tags t
WHERE (kp.category = 'systematic' AND t.name = 'grammar')
   OR (kp.subtype = 'phrasal_verb' AND t.name = 'vocabulary')
   OR (kp.subtype = 'conditional' AND t.name = 'structure')
ON CONFLICT (knowledge_point_id, tag_id) DO NOTHING;

-- 插入練習佇列樣本
INSERT INTO practice_queue (knowledge_point_id, priority, scheduled_for, reason)
SELECT 
  kp.id,
  CASE 
    WHEN kp.mastery_level < 0.4 THEN 3
    WHEN kp.mastery_level < 0.7 THEN 2
    ELSE 1
  END,
  CURRENT_TIMESTAMP + INTERVAL '1 hour',
  CASE 
    WHEN kp.mastery_level < 0.4 THEN 'low_mastery'
    ELSE 'regular_review'
  END
FROM knowledge_points kp
WHERE kp.mastery_level < 0.8;

-- 更新統計數據
UPDATE daily_records 
SET 
  questions_attempted = 15,
  questions_correct = 11,
  knowledge_points_reviewed = 5,
  new_knowledge_points = 2,
  total_practice_time = 45
WHERE date = CURRENT_DATE;

-- 添加歷史數據
INSERT INTO daily_records (
  date, total_practice_time, questions_attempted, questions_correct,
  knowledge_points_reviewed, new_knowledge_points
) VALUES
  (CURRENT_DATE - 1, 30, 12, 9, 4, 1),
  (CURRENT_DATE - 2, 25, 8, 6, 3, 2),
  (CURRENT_DATE - 3, 40, 16, 13, 6, 0)
ON CONFLICT (date) DO NOTHING;
EOF
```

### 2️⃣ 自動化啟動腳本 (1 小時)

#### 創建一鍵啟動腳本
```bash
cat > scripts/setup_pure_db_dev.sh << 'EOF'
#!/bin/bash
set -e

# 純資料庫開發環境一鍵設置腳本
# 使用方法: ./scripts/setup_pure_db_dev.sh [--fresh]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查依賴
check_dependencies() {
    log_info "檢查系統依賴..."
    
    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝。請先安裝 Docker Desktop。"
        exit 1
    fi
    
    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安裝。"
        exit 1
    fi
    
    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安裝。"
        exit 1
    fi
    
    log_success "所有依賴檢查通過"
}

# 環境變數設置
setup_environment() {
    log_info "設置環境變數..."
    
    # 創建開發環境配置
    cat > .env.dev << 'ENVEOF'
# 純資料庫開發環境配置
USE_DATABASE=true
DATABASE_URL=postgresql://linker_dev_user:linker_dev_pass@localhost:5433/linker_dev

# Gemini API (開發用)
GEMINI_API_KEY=your-dev-api-key-here
GEMINI_GENERATE_MODEL=gemini-2.5-flash
GEMINI_GRADE_MODEL=gemini-2.5-pro

# 資料庫連接池配置
DB_POOL_MIN_SIZE=2
DB_POOL_MAX_SIZE=10
DB_POOL_TIMEOUT=10
DB_MAX_RETRIES=3
DB_RETRY_DELAY=1

# 開發模式設置
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development

# 緩存配置 (可選)
REDIS_URL=redis://localhost:6380/0
REDIS_CACHE_TTL=300
ENVEOF
    
    # 備份現有 .env 並使用開發配置
    if [[ -f ".env" ]]; then
        cp .env .env.backup
        log_warning "已備份現有 .env 為 .env.backup"
    fi
    
    cp .env.dev .env
    log_success "開發環境變數配置完成"
}

# 啟動 Docker 服務
start_docker_services() {
    log_info "啟動 Docker 服務..."
    
    # 檢查是否需要全新安裝
    if [[ "$1" == "--fresh" ]]; then
        log_warning "執行全新安裝，將刪除現有數據..."
        docker-compose -f docker-compose.dev.yml down -v
    fi
    
    # 啟動服務
    docker-compose -f docker-compose.dev.yml up -d
    
    # 等待服務健康檢查
    log_info "等待資料庫服務啟動..."
    timeout=60
    elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        if docker-compose -f docker-compose.dev.yml exec -T linker-db-dev pg_isready -U linker_dev_user -d linker_dev; then
            log_success "資料庫服務已就緒"
            break
        fi
        
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done
    
    if [[ $elapsed -ge $timeout ]]; then
        log_error "資料庫服務啟動超時"
        exit 1
    fi
}

# 驗證資料庫連接
verify_database() {
    log_info "驗證資料庫連接..."
    
    # 測試連接
    docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev -c "SELECT 1;" > /dev/null
    
    if [[ $? -eq 0 ]]; then
        log_success "資料庫連接測試成功"
    else
        log_error "資料庫連接測試失敗"
        exit 1
    fi
    
    # 檢查表是否創建
    table_count=$(docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    
    log_info "已創建 $table_count 個資料表"
    
    # 檢查 seed data
    knowledge_count=$(docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev -t -c "SELECT count(*) FROM knowledge_points;" | tr -d ' ')
    
    log_info "已載入 $knowledge_count 個知識點"
}

# 安裝 Python 依賴
setup_python_environment() {
    log_info "設置 Python 環境..."
    
    # 檢查虛擬環境
    if [[ ! -d ".venv" ]]; then
        log_info "創建 Python 虛擬環境..."
        python3 -m venv .venv
    fi
    
    # 啟動虛擬環境並安裝依賴
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 安裝開發依賴
    if [[ -f "requirements-dev.txt" ]]; then
        pip install -r requirements-dev.txt
    fi
    
    log_success "Python 環境設置完成"
}

# 運行初始化測試
run_initial_tests() {
    log_info "運行初始化測試..."
    
    source .venv/bin/activate
    
    # 測試資料庫連接
    python3 scripts/test_database_mode.py
    
    if [[ $? -eq 0 ]]; then
        log_success "初始化測試通過"
    else
        log_error "初始化測試失敗"
        exit 1
    fi
}

# 生成開發工具
generate_dev_tools() {
    log_info "生成開發工具..."
    
    # 資料庫管理工具
    cat > scripts/db_dev_tools.sh << 'TOOLSEOF'
#!/bin/bash
# 資料庫開發工具腳本

# 進入資料庫 CLI
db_cli() {
    docker-compose -f docker-compose.dev.yml exec linker-db-dev psql -U linker_dev_user -d linker_dev
}

# 重置資料庫
db_reset() {
    echo "⚠️  這將重置所有開發數據！"
    read -p "確定要繼續嗎？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f docker-compose.dev.yml down
        docker volume rm $(docker volume ls -q | grep linker.*dev) 2>/dev/null || true
        docker-compose -f docker-compose.dev.yml up -d
        echo "✅ 資料庫重置完成"
    fi
}

# 備份開發數據
db_backup() {
    backup_file="backups/dev_backup_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p backups
    docker-compose -f docker-compose.dev.yml exec -T linker-db-dev pg_dump -U linker_dev_user -d linker_dev > "$backup_file"
    echo "✅ 資料庫已備份到: $backup_file"
}

# 查看資料庫狀態
db_status() {
    echo "=== 資料庫連接狀態 ==="
    docker-compose -f docker-compose.dev.yml exec linker-db-dev pg_isready -U linker_dev_user -d linker_dev
    
    echo -e "\n=== 表格統計 ==="
    docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev -c "
    SELECT 
        schemaname,
        tablename,
        n_tup_ins as total_records
    FROM pg_stat_user_tables 
    ORDER BY n_tup_ins DESC;
    "
}

# 幫助信息
show_help() {
    echo "資料庫開發工具使用方法:"
    echo "  source scripts/db_dev_tools.sh"
    echo ""
    echo "可用命令:"
    echo "  db_cli     - 進入資料庫命令行"
    echo "  db_reset   - 重置資料庫 (⚠️ 危險操作)"
    echo "  db_backup  - 備份當前數據"
    echo "  db_status  - 查看資料庫狀態"
}

# 如果直接執行腳本，顯示幫助
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    show_help
fi
TOOLSEOF
    
    chmod +x scripts/db_dev_tools.sh
    
    log_success "開發工具生成完成"
}

# 主函數
main() {
    echo "🚀 Linker 純資料庫開發環境設置"
    echo "=================================="
    
    check_dependencies
    setup_environment
    start_docker_services "$1"
    verify_database
    setup_python_environment
    run_initial_tests
    generate_dev_tools
    
    echo ""
    log_success "🎉 開發環境設置完成！"
    echo ""
    echo "📋 下一步:"
    echo "1. 啟動開發服務器: source .venv/bin/activate && uvicorn web.main:app --reload"
    echo "2. 訪問應用: http://localhost:8000"
    echo "3. 訪問資料庫管理: http://localhost:8080 (pgAdmin)"
    echo "4. 使用資料庫工具: source scripts/db_dev_tools.sh"
    echo ""
    echo "🔧 有用的命令:"
    echo "- 重啟服務: docker-compose -f docker-compose.dev.yml restart"
    echo "- 查看日誌: docker-compose -f docker-compose.dev.yml logs -f"
    echo "- 停止服務: docker-compose -f docker-compose.dev.yml down"
}

# 執行主函數
main "$@"
EOF

chmod +x scripts/setup_pure_db_dev.sh
```

### 3️⃣ 開發工具和腳本 (1-1.5 小時)

#### 創建代碼質量檢查腳本
```bash
cat > scripts/dev_code_quality.sh << 'EOF'
#!/bin/bash
set -e

# 代碼質量檢查腳本 - 純資料庫開發版本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 顏色輸出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 檢查 JSON 依賴
check_json_dependencies() {
    log_info "檢查 JSON 依賴..."
    
    # 檢查直接 JSON import
    json_imports=$(rg "import json|from json" --type py -c || echo "0")
    if [[ "$json_imports" != "0" ]]; then
        log_error "發現 JSON import，純資料庫模式不應包含 JSON 依賴"
        rg "import json|from json" --type py -n
        return 1
    fi
    
    # 檢查 JSON 方法調用
    json_calls=$(rg "json\.(load|loads|dump|dumps)" --type py -c || echo "0")
    if [[ "$json_calls" != "0" ]]; then
        log_error "發現 JSON 方法調用"
        rg "json\.(load|loads|dump|dumps)" --type py -n
        return 1
    fi
    
    # 檢查 legacy manager 引用
    legacy_refs=$(rg "_legacy_manager|legacy.*manager" --type py -c || echo "0")
    if [[ "$legacy_refs" != "0" ]]; then
        log_error "發現 legacy manager 引用"
        rg "_legacy_manager|legacy.*manager" --type py -n
        return 1
    fi
    
    log_success "✅ 無 JSON 依賴"
    return 0
}

# 代碼風格檢查
check_code_style() {
    log_info "執行代碼風格檢查..."
    
    # Ruff linting
    if ! ruff check .; then
        log_error "Ruff linting 失敗"
        return 1
    fi
    
    # Ruff formatting check
    if ! ruff format --check .; then
        log_error "代碼格式不符合標準，執行 'ruff format .' 修復"
        return 1
    fi
    
    log_success "✅ 代碼風格檢查通過"
    return 0
}

# 類型檢查
check_types() {
    log_info "執行類型檢查..."
    
    # 如果有 mypy 配置，使用 mypy
    if [[ -f "pyproject.toml" ]] && grep -q "mypy" pyproject.toml; then
        if ! mypy .; then
            log_error "類型檢查失敗"
            return 1
        fi
    else
        log_warning "跳過類型檢查 (mypy 未配置)"
    fi
    
    log_success "✅ 類型檢查通過"
    return 0
}

# 運行測試
run_tests() {
    log_info "運行測試套件..."
    
    # 確保使用開發資料庫
    export USE_DATABASE=true
    export DATABASE_URL="postgresql://linker_dev_user:linker_dev_pass@localhost:5433/linker_dev"
    
    # 運行測試
    if ! pytest --cov=core --cov=web --cov-fail-under=90 -v; then
        log_error "測試失敗或覆蓋率不足"
        return 1
    fi
    
    log_success "✅ 測試套件通過"
    return 0
}

# 資料庫連接測試
test_database_connection() {
    log_info "測試資料庫連接..."
    
    if ! python3 scripts/test_database_mode.py; then
        log_error "資料庫連接測試失敗"
        return 1
    fi
    
    log_success "✅ 資料庫連接正常"
    return 0
}

# 性能基準測試
run_performance_tests() {
    log_info "執行性能基準測試..."
    
    # 簡單的響應時間測試
    python3 << 'PYTEST'
import asyncio
import time
import sys
import os

# 添加專案路徑
sys.path.insert(0, '.')

async def test_database_performance():
    from core.database.adapter import get_knowledge_manager_async
    
    try:
        manager = await get_knowledge_manager_async(use_database=True)
        
        # 測試統計查詢性能
        start_time = time.time()
        stats = await manager.get_statistics_async()
        stats_time = time.time() - start_time
        
        # 測試知識點查詢性能
        start_time = time.time()
        points = await manager.get_knowledge_points_async()
        points_time = time.time() - start_time
        
        # 測試複習候選查詢性能
        start_time = time.time()
        candidates = await manager.get_review_candidates_async(max_points=10)
        candidates_time = time.time() - start_time
        
        print(f"統計查詢: {stats_time:.3f}s")
        print(f"知識點查詢: {points_time:.3f}s") 
        print(f"複習候選查詢: {candidates_time:.3f}s")
        
        # 性能閾值檢查
        if stats_time > 1.0 or points_time > 0.5 or candidates_time > 0.5:
            print("⚠️ 性能警告: 查詢時間超過預期")
            return False
            
        return True
        
    except Exception as e:
        print(f"性能測試錯誤: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_database_performance())
    sys.exit(0 if result else 1)
PYTEST
    
    if [[ $? -eq 0 ]]; then
        log_success "✅ 性能基準測試通過"
        return 0
    else
        log_warning "⚠️ 性能基準測試未通過"
        return 1
    fi
}

# 生成質量報告
generate_quality_report() {
    log_info "生成代碼質量報告..."
    
    # 創建報告目錄
    mkdir -p reports/quality
    
    # 生成測試覆蓋率報告
    pytest --cov=core --cov=web --cov-report=html:reports/quality/coverage --cov-report=term > reports/quality/test_results.txt 2>&1
    
    # 生成複雜度報告 (如果有 radon)
    if command -v radon &> /dev/null; then
        radon cc . -s > reports/quality/complexity.txt
        radon mi . -s > reports/quality/maintainability.txt
    fi
    
    # 生成依賴檢查報告
    echo "=== JSON Dependencies Check ===" > reports/quality/dependency_check.txt
    rg "import json|from json|json\.|_legacy_manager" --type py -n >> reports/quality/dependency_check.txt 2>&1 || echo "No JSON dependencies found" >> reports/quality/dependency_check.txt
    
    log_success "✅ 質量報告已生成: reports/quality/"
}

# 主函數
main() {
    echo "🔍 純資料庫開發代碼質量檢查"
    echo "============================"
    
    errors=0
    
    # 執行所有檢查
    check_json_dependencies || ((errors++))
    check_code_style || ((errors++))
    check_types || ((errors++))
    test_database_connection || ((errors++))
    run_tests || ((errors++))
    run_performance_tests || ((errors++))
    
    # 生成報告
    generate_quality_report
    
    echo ""
    if [[ $errors -eq 0 ]]; then
        log_success "🎉 所有質量檢查通過！"
        echo "📊 詳細報告: reports/quality/"
        exit 0
    else
        log_error "❌ $errors 項檢查失敗"
        echo "📊 詳細報告: reports/quality/"
        exit 1
    fi
}

# 命令行參數處理
case "${1:-all}" in
    json)
        check_json_dependencies
        ;;
    style)
        check_code_style
        ;;
    types)
        check_types
        ;;
    test)
        run_tests
        ;;
    db)
        test_database_connection
        ;;
    perf)
        run_performance_tests
        ;;
    report)
        generate_quality_report
        ;;
    all)
        main
        ;;
    *)
        echo "使用方法: $0 [json|style|types|test|db|perf|report|all]"
        exit 1
        ;;
esac
EOF

chmod +x scripts/dev_code_quality.sh
```

#### 創建性能監控工具
```bash
cat > scripts/dev_monitoring.sh << 'EOF'
#!/bin/bash

# 開發環境性能監控工具

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 監控資料庫性能
monitor_database() {
    echo "📊 資料庫性能監控"
    echo "=================="
    
    # 連接池狀態
    echo "=== 連接池狀態 ==="
    docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev -c "
    SELECT 
        count(*) as total_connections,
        count(*) FILTER (WHERE state = 'active') as active_connections,
        count(*) FILTER (WHERE state = 'idle') as idle_connections
    FROM pg_stat_activity 
    WHERE datname = 'linker_dev';
    "
    
    # 查詢性能統計
    echo -e "\n=== 查詢性能統計 ==="
    docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev -c "
    SELECT 
        schemaname,
        tablename,
        seq_scan,
        seq_tup_read,
        idx_scan,
        idx_tup_fetch,
        n_tup_ins,
        n_tup_upd,
        n_tup_del
    FROM pg_stat_user_tables 
    ORDER BY seq_scan DESC;
    "
    
    # 索引使用情況
    echo -e "\n=== 索引使用情況 ==="
    docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev -c "
    SELECT 
        schemaname,
        tablename,
        indexname,
        idx_scan,
        idx_tup_read,
        idx_tup_fetch
    FROM pg_stat_user_indexes 
    ORDER BY idx_scan DESC;
    "
}

# 監控應用性能
monitor_application() {
    echo "🚀 應用性能監控"
    echo "=============="
    
    # 檢查應用是否運行
    if ! curl -s http://localhost:8000/health > /dev/null; then
        echo "❌ 應用未運行或無響應"
        return 1
    fi
    
    # 測試關鍵端點響應時間
    echo "=== API 響應時間測試 ==="
    
    endpoints=(
        "/health"
        "/api/knowledge/statistics"
        "/api/knowledge/review-candidates"
        "/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000$endpoint)
        printf "%-30s: %s seconds\n" "$endpoint" "$response_time"
    done
}

# 監控系統資源
monitor_system_resources() {
    echo "💻 系統資源監控"
    echo "=============="
    
    # Docker 容器資源使用
    echo "=== Docker 容器資源 ==="
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" $(docker-compose -f docker-compose.dev.yml ps -q)
    
    # 磁碟空間
    echo -e "\n=== 磁碟空間 ==="
    df -h | grep -E "Filesystem|/dev/"
    
    # Docker 卷大小
    echo -e "\n=== Docker 卷大小 ==="
    docker system df
}

# 生成性能報告
generate_performance_report() {
    echo "📈 生成性能報告..."
    
    mkdir -p reports/performance
    report_file="reports/performance/performance_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Linker 純資料庫開發環境性能報告"
        echo "生成時間: $(date)"
        echo "==============================="
        echo
        
        monitor_database
        echo
        monitor_application  
        echo
        monitor_system_resources
        
    } > "$report_file"
    
    echo "✅ 性能報告已保存: $report_file"
}

# 持續監控模式
continuous_monitoring() {
    echo "🔄 啟動持續監控模式 (Ctrl+C 停止)"
    echo "================================"
    
    while true; do
        clear
        echo "$(date) - Linker 開發環境監控"
        echo "=============================="
        
        # 簡化的實時監控
        echo "=== 資料庫連接 ==="
        if docker-compose -f docker-compose.dev.yml exec -T linker-db-dev pg_isready -U linker_dev_user -d linker_dev > /dev/null 2>&1; then
            echo "✅ 資料庫連接正常"
        else
            echo "❌ 資料庫連接異常"
        fi
        
        echo -e "\n=== 應用狀態 ==="
        if curl -s http://localhost:8000/health > /dev/null; then
            echo "✅ 應用運行正常"
            
            # 快速性能測試
            response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/api/knowledge/statistics)
            echo "📊 統計 API 響應時間: ${response_time}s"
        else
            echo "❌ 應用無響應"
        fi
        
        echo -e "\n=== 資源使用 ==="
        docker stats --no-stream --format "{{.Container}}: CPU {{.CPUPerc}}, Memory {{.MemPerc}}" $(docker-compose -f docker-compose.dev.yml ps -q) | head -3
        
        echo -e "\n按 Ctrl+C 停止監控..."
        sleep 10
    done
}

# 主函數
main() {
    case "${1:-status}" in
        db)
            monitor_database
            ;;
        app)
            monitor_application
            ;;
        sys)
            monitor_system_resources
            ;;
        report)
            generate_performance_report
            ;;
        watch)
            continuous_monitoring
            ;;
        status)
            monitor_database
            echo
            monitor_application
            echo
            monitor_system_resources
            ;;
        *)
            echo "使用方法: $0 [db|app|sys|report|watch|status]"
            echo ""
            echo "選項:"
            echo "  db     - 資料庫性能監控"
            echo "  app    - 應用性能監控"
            echo "  sys    - 系統資源監控"
            echo "  report - 生成性能報告"
            echo "  watch  - 持續監控模式"
            echo "  status - 全面狀態檢查 (默認)"
            exit 1
            ;;
    esac
}

main "$@"
EOF

chmod +x scripts/dev_monitoring.sh
```

### 4️⃣ 團隊文檔和培訓材料 (1 小時)

#### 更新開發環境文檔
```bash
cat > docs/DEV_ENVIRONMENT_SETUP.md << 'EOF'
# 純資料庫開發環境設置指南

## 📋 概述

本指南幫助開發者設置 Linker 純資料庫開發環境。移除了 JSON 文件依賴，統一使用 PostgreSQL 作為數據存儲。

## 🎯 設置目標

- ✅ 完全基於 PostgreSQL 的開發環境
- ✅ Docker 容器化的資料庫服務
- ✅ 自動化的環境配置和驗證
- ✅ 豐富的開發工具和監控

## 🚀 快速開始

### 一鍵設置 (推薦)

```bash
# 克隆專案後執行
./scripts/setup_pure_db_dev.sh

# 如果需要全新安裝 (刪除現有數據)
./scripts/setup_pure_db_dev.sh --fresh
```

### 手動設置 (可選)

如果一鍵設置失敗，可以按照以下步驟手動設置：

#### 1. 檢查依賴
```bash
# 確保已安裝
docker --version
docker-compose --version
python3 --version
```

#### 2. 啟動資料庫服務
```bash
docker-compose -f docker-compose.dev.yml up -d
```

#### 3. 配置環境變數
```bash
cp .env.dev .env
```

#### 4. 設置 Python 環境
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 5. 驗證設置
```bash
python3 scripts/test_database_mode.py
```

## 🛠️ 開發工具使用

### 資料庫管理工具

```bash
# 載入資料庫工具
source scripts/db_dev_tools.sh

# 進入資料庫 CLI
db_cli

# 查看資料庫狀態
db_status

# 備份開發數據
db_backup

# 重置資料庫 (⚠️ 危險操作)
db_reset
```

### 代碼質量檢查

```bash
# 完整質量檢查
./scripts/dev_code_quality.sh

# 單項檢查
./scripts/dev_code_quality.sh json    # JSON 依賴檢查
./scripts/dev_code_quality.sh style  # 代碼風格檢查
./scripts/dev_code_quality.sh test   # 運行測試
./scripts/dev_code_quality.sh db     # 資料庫連接測試
```

### 性能監控

```bash
# 狀態檢查
./scripts/dev_monitoring.sh status

# 持續監控
./scripts/dev_monitoring.sh watch

# 生成性能報告
./scripts/dev_monitoring.sh report
```

## 🔧 環境配置詳解

### 環境變數 (.env)

```bash
# 核心配置
USE_DATABASE=true
DATABASE_URL=postgresql://linker_dev_user:linker_dev_pass@localhost:5433/linker_dev

# AI 服務配置
GEMINI_API_KEY=your-api-key-here
GEMINI_GENERATE_MODEL=gemini-2.5-flash
GEMINI_GRADE_MODEL=gemini-2.5-pro

# 資料庫連接池
DB_POOL_MIN_SIZE=2
DB_POOL_MAX_SIZE=10
DB_POOL_TIMEOUT=10

# 開發模式
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Docker 服務

- **linker-db-dev**: PostgreSQL 15 資料庫 (端口 5433)
- **linker-redis-dev**: Redis 緩存 (端口 6380)
- **pgadmin**: 資料庫管理界面 (端口 8080)

## 🎯 開發工作流程

### 1. 啟動開發環境

```bash
# 啟動所有服務
./scripts/setup_pure_db_dev.sh

# 啟動應用
source .venv/bin/activate
uvicorn web.main:app --reload
```

### 2. 開發過程中

```bash
# 檢查代碼質量
./scripts/dev_code_quality.sh

# 運行測試
pytest --cov=core --cov=web

# 監控性能
./scripts/dev_monitoring.sh watch
```

### 3. 提交前檢查

```bash
# 完整質量檢查
./scripts/dev_code_quality.sh all

# 確保無 JSON 依賴
./scripts/dev_code_quality.sh json

# 性能回歸測試
./scripts/dev_code_quality.sh perf
```

## 🔍 故障排除

### 常見問題

#### 1. 資料庫連接失敗
```bash
# 檢查 Docker 服務狀態
docker-compose -f docker-compose.dev.yml ps

# 查看資料庫日誌
docker-compose -f docker-compose.dev.yml logs linker-db-dev

# 重啟資料庫服務
docker-compose -f docker-compose.dev.yml restart linker-db-dev
```

#### 2. 端口衝突
```bash
# 檢查端口占用
lsof -i :5433
lsof -i :8080

# 修改 docker-compose.dev.yml 中的端口映射
```

#### 3. 數據不一致
```bash
# 重置開發資料庫
source scripts/db_dev_tools.sh
db_reset

# 或手動重置
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

#### 4. 測試失敗
```bash
# 檢查環境變數
echo $USE_DATABASE
echo $DATABASE_URL

# 確保資料庫服務運行
docker-compose -f docker-compose.dev.yml exec linker-db-dev pg_isready -U linker_dev_user -d linker_dev

# 重新運行測試
pytest -v --tb=short
```

### 性能問題

#### 1. 查詢速度慢
```bash
# 檢查資料庫性能
./scripts/dev_monitoring.sh db

# 查看查詢計劃
# 在 db_cli 中執行
EXPLAIN ANALYZE SELECT * FROM knowledge_points WHERE mastery_level < 0.5;
```

#### 2. 記憶體使用過高
```bash
# 檢查容器資源使用
docker stats

# 調整連接池大小 (在 .env 中)
DB_POOL_MAX_SIZE=5
```

## 📚 參考資料

### 重要文件位置
- 環境配置: `.env`, `docker-compose.dev.yml`
- 資料庫 Schema: `core/database/schema.sql`
- 開發工具: `scripts/db_dev_tools.sh`
- 測試配置: `tests/conftest.py`

### 有用連結
- 應用: http://localhost:8000
- 資料庫管理: http://localhost:8080
- API 文檔: http://localhost:8000/docs
- 健康檢查: http://localhost:8000/health

### 團隊規範
- 所有新功能必須有資料庫支援
- 禁止在 core/ 中使用 JSON 文件操作
- 測試覆蓋率必須 >90%
- 所有 PR 必須通過 JSON 依賴檢查

---

**💡 提示**: 如果遇到問題，先檢查 Docker 服務狀態，然後查看相關日誌。大部分問題都可以通過重啟服務解決。
EOF
```

#### 創建故障排除指南
```bash
cat > docs/TROUBLESHOOTING_PURE_DB.md << 'EOF'
# 純資料庫開發環境故障排除指南

## 🚨 緊急問題處理

### 系統完全無法啟動

#### 症狀
- Docker 服務無法啟動
- 資料庫連接完全失敗
- 應用啟動報錯

#### 解決方案
```bash
# 1. 完全重置 Docker 環境
docker-compose -f docker-compose.dev.yml down -v
docker system prune -f

# 2. 重新啟動
./scripts/setup_pure_db_dev.sh --fresh

# 3. 如果仍然失敗，檢查系統資源
docker system df
df -h
```

### 資料庫數據丟失

#### 症狀
- 知識點數據為空
- 統計信息歸零
- 用戶數據消失

#### 解決方案
```bash
# 1. 檢查是否有可用備份
ls -la backups/dev_backup_*

# 2. 恢復最新備份
latest_backup=$(ls -t backups/dev_backup_*.sql | head -1)
docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev < "$latest_backup"

# 3. 如果沒有備份，重新載入 seed data
docker-compose -f docker-compose.dev.yml exec -T linker-db-dev psql -U linker_dev_user -d linker_dev -f /docker-entrypoint-initdb.d/02-seed.sql
```

## 🔧 常見開發問題

### 1. JSON 依賴錯誤

#### 問題描述
開發過程中意外引入了 JSON 依賴，導致純資料庫模式檢查失敗。

#### 檢測方法
```bash
./scripts/dev_code_quality.sh json
```

#### 常見錯誤模式
```python
# ❌ 錯誤: 直接使用 JSON
import json
data = json.load(file)

# ❌ 錯誤: 引用舊的 knowledge.py
from core.knowledge import KnowledgeManager

# ❌ 錯誤: 使用 legacy manager
if self._legacy_manager:
    return self._legacy_manager.get_data()
```

#### 正確做法
```python
# ✅ 正確: 使用資料庫 adapter
from core.database.adapter import get_knowledge_manager_async

# ✅ 正確: 異步資料庫操作
manager = await get_knowledge_manager_async(use_database=True)
data = await manager.get_statistics_async()
```

### 2. 測試環境問題

#### 問題: 測試使用了錯誤的數據源
```bash
# 檢查測試環境配置
echo $USE_DATABASE
echo $DATABASE_URL

# 確保測試使用開發資料庫
export USE_DATABASE=true
export DATABASE_URL="postgresql://linker_dev_user:linker_dev_pass@localhost:5433/linker_dev"
```

#### 問題: 測試數據污染
```bash
# 每次測試前重置資料庫
source scripts/db_dev_tools.sh
db_reset

# 或在測試中使用事務隔離
pytest --tb=short -v
```

### 3. 性能回歸問題

#### 問題: 查詢速度明顯變慢

**診斷步驟:**
```bash
# 1. 檢查資料庫連接池
./scripts/dev_monitoring.sh db

# 2. 分析慢查詢
docker-compose -f docker-compose.dev.yml exec linker-db-dev psql -U linker_dev_user -d linker_dev -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE mean_time > 100 
ORDER BY mean_time DESC 
LIMIT 10;"
```

**解決方案:**
```bash
# 1. 檢查索引使用
EXPLAIN ANALYZE SELECT * FROM knowledge_points WHERE mastery_level < 0.5;

# 2. 重建統計信息
ANALYZE;

# 3. 調整連接池大小
# 在 .env 中設置
DB_POOL_MAX_SIZE=10
DB_POOL_MIN_SIZE=2
```

## 🔍 診斷工具使用

### 資料庫診斷

#### 連接狀態檢查
```sql
-- 查看當前連接
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change
FROM pg_stat_activity 
WHERE datname = 'linker_dev';
```

#### 表格健康檢查
```sql
-- 檢查表格統計
SELECT 
    schemaname,
    tablename,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_analyze
FROM pg_stat_user_tables;
```

#### 索引效率檢查
```sql
-- 未使用的索引
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;
```

### 應用診斷

#### 記憶體泄漏檢查
```bash
# 監控 Python 進程記憶體使用
ps aux | grep python | grep -v grep

# 檢查 Docker 容器記憶體
docker stats --no-stream
```

#### API 響應時間分析
```bash
# 批量測試 API 響應
for i in {1..10}; do
    curl -o /dev/null -s -w "API響應時間: %{time_total}s\n" http://localhost:8000/api/knowledge/statistics
    sleep 1
done
```

## 📋 預防措施

### 開發習慣

1. **每日檢查**: 每天開始開發前運行
   ```bash
   ./scripts/dev_code_quality.sh all
   ```

2. **提交前驗證**: 每次 commit 前執行
   ```bash
   ./scripts/dev_code_quality.sh json
   pytest --cov=core --cov=web --cov-fail-under=90
   ```

3. **定期備份**: 每天結束開發時
   ```bash
   source scripts/db_dev_tools.sh
   db_backup
   ```

### 代碼審查檢查清單

- [ ] 無 `import json` 或 `from json`
- [ ] 無 `json.load/loads/dump/dumps` 調用
- [ ] 無 `_legacy_manager` 引用
- [ ] 無 `core.knowledge` 直接引用
- [ ] 所有資料庫操作使用 async 方法
- [ ] 測試覆蓋率 >90%
- [ ] 性能基準測試通過

### 環境維護

#### 每週維護
```bash
# 清理無用的 Docker 資源
docker system prune -f

# 更新開發依賴
pip install --upgrade -r requirements.txt

# 檢查資料庫健康狀態
./scripts/dev_monitoring.sh db
```

#### 每月維護
```bash
# 清理舊的備份文件
find backups/ -name "dev_backup_*.sql" -mtime +30 -delete

# 重建開發資料庫統計信息
docker-compose -f docker-compose.dev.yml exec linker-db-dev psql -U linker_dev_user -d linker_dev -c "ANALYZE;"

# 檢查並更新文檔
```

## 🆘 求助渠道

### 自助檢查順序
1. 查看 Docker 服務狀態
2. 檢查環境變數配置
3. 運行診斷腳本
4. 查看相關日誌文件
5. 嘗試重啟服務

### 獲取幫助
- 📝 檢查 `docs/DEV_ENVIRONMENT_SETUP.md`
- 🔍 搜索類似錯誤的解決方案
- 💬 聯絡團隊 Tech Lead
- 🐛 如果是 bug，創建詳細的問題報告

### 問題報告模板
```
## 問題描述
[簡要描述問題]

## 復現步驟
1. [步驟一]
2. [步驟二]
3. [發生錯誤]

## 環境信息
- OS: [作業系統]
- Docker版本: [docker --version]
- Python版本: [python3 --version]

## 錯誤信息
```
[貼上完整錯誤信息]
```

## 已嘗試的解決方案
- [已嘗試的方法]

## 相關日誌
[貼上相關日誌片段]
```

---

**💡 記住**: 大多數問題都可以通過重啟 Docker 服務解決。如果問題持續存在，檢查系統資源和網絡連接。
EOF
```

## 🔧 執行驗證

### 環境配置驗證
```bash
# 檢查所有創建的文件
echo "=== 環境配置文件檢查 ==="
files=(
    "docker-compose.dev.yml"
    "scripts/setup_pure_db_dev.sh"
    "scripts/seed_data.sql"
    "scripts/dev_sample_data.sql"
    "scripts/db_dev_tools.sh"
    "scripts/dev_code_quality.sh" 
    "scripts/dev_monitoring.sh"
    "docs/DEV_ENVIRONMENT_SETUP.md"
    "docs/TROUBLESHOOTING_PURE_DB.md"
)

for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file"
    else
        echo "❌ $file (缺失)"
    fi
done

# 檢查腳本可執行權限
echo -e "\n=== 腳本權限檢查 ==="
for script in scripts/*.sh; do
    if [[ -x "$script" ]]; then
        echo "✅ $script (可執行)"
    else
        echo "❌ $script (無執行權限)"
    fi
done
```

### 一鍵設置測試
```bash
# 測試一鍵設置腳本語法
echo "=== 腳本語法檢查 ==="
bash -n scripts/setup_pure_db_dev.sh
if [[ $? -eq 0 ]]; then
    echo "✅ setup_pure_db_dev.sh 語法正確"
else
    echo "❌ setup_pure_db_dev.sh 語法錯誤"
fi

# 測試其他工具腳本
for script in scripts/db_dev_tools.sh scripts/dev_code_quality.sh scripts/dev_monitoring.sh; do
    bash -n "$script"
    if [[ $? -eq 0 ]]; then
        echo "✅ $(basename $script) 語法正確"
    else
        echo "❌ $(basename $script) 語法錯誤"
    fi
done
```

### Docker 配置驗證
```bash
# 驗證 Docker Compose 配置
echo "=== Docker Compose 配置驗證 ==="
docker-compose -f docker-compose.dev.yml config > /dev/null
if [[ $? -eq 0 ]]; then
    echo "✅ docker-compose.dev.yml 配置有效"
else
    echo "❌ docker-compose.dev.yml 配置無效"
fi

# 檢查 SQL 文件語法
echo -e "\n=== SQL 文件語法檢查 ==="
for sql_file in scripts/*.sql; do
    if [[ -f "$sql_file" ]]; then
        # 基本語法檢查（檢查是否有基本的 SQL 關鍵字）
        if grep -q -i "INSERT\|CREATE\|SELECT\|UPDATE" "$sql_file"; then
            echo "✅ $(basename $sql_file) 包含有效 SQL 語句"
        else
            echo "⚠️ $(basename $sql_file) 可能不包含 SQL 語句"
        fi
    fi
done
```

## 📝 執行筆記

### 完成檢查清單
- [ ] Docker Compose 開發環境配置完成
- [ ] 一鍵啟動腳本創建並測試
- [ ] 資料庫 seed data 和樣本數據準備
- [ ] 開發工具腳本集合創建
- [ ] 代碼質量檢查自動化
- [ ] 性能監控工具配置
- [ ] 開發環境文檔編寫
- [ ] 故障排除指南完成
- [ ] 所有腳本語法驗證通過

### 重要輸出
- `docker-compose.dev.yml` - 開發環境 Docker 配置
- `scripts/setup_pure_db_dev.sh` - 一鍵設置腳本
- `scripts/db_dev_tools.sh` - 資料庫管理工具
- `scripts/dev_code_quality.sh` - 代碼質量檢查
- `scripts/dev_monitoring.sh` - 性能監控工具
- `docs/DEV_ENVIRONMENT_SETUP.md` - 開發環境指南
- `docs/TROUBLESHOOTING_PURE_DB.md` - 故障排除指南

### 團隊準備狀態
- ✅ 開發環境完全自動化
- ✅ 豐富的開發工具和監控
- ✅ 詳細的文檔和故障排除指南
- ✅ 代碼質量保證機制
- ✅ 性能監控和優化工具

## 🔍 審查意見 (For Reviewer)

_(留空，供 reviewer 填寫)_

---

**✅ 任務完成標準**: 一鍵啟動腳本可以成功設置純資料庫開發環境，所有開發工具腳本運行正常，團隊成員可以根據文檔快速上手開發，代碼質量檢查能有效防止 JSON 依賴引入。