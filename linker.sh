#!/usr/bin/env bash

# ================================================================
#  Linker 專案管理系統 v2.0
#  整合式專案管理腳本，提供完整的開發、測試和維護功能
# ================================================================

set -euo pipefail

# ==================== 環境設定 ====================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip"
ENV_FILE="$PROJECT_DIR/.env"
SERVER_LOG="$PROJECT_DIR/server.log"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 預設設定
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT="8000"
DEFAULT_DAILY_LIMIT="15"

# ==================== 基礎函數 ====================

# 顯示標題
show_header() {
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${BOLD}        Linker 英文學習系統 - 管理控制台         ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}            AI 驅動的智慧翻譯練習平台            ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 顯示狀態
show_status() {
    echo -e "${BLUE}📊 系統狀態：${NC}"
    
    # 檢查服務器狀態
    if pgrep -f "uvicorn web.main:app" > /dev/null; then
        echo -e "  • 服務器：${GREEN}✅ 運行中${NC}"
        
        # 嘗試獲取 API 狀態
        if STATUS=$(curl -s http://localhost:${PORT:-8000}/api/knowledge/daily-limit/status 2>/dev/null); then
            USED_COUNT=$(echo $STATUS | python3 -c "import sys, json; print(json.load(sys.stdin).get('used_count', 0))" 2>/dev/null || echo "0")
            DAILY_LIMIT=$(echo $STATUS | python3 -c "import sys, json; print(json.load(sys.stdin).get('daily_limit', 15))" 2>/dev/null || echo "15")
            echo -e "  • 今日進度：${CYAN}${USED_COUNT}/${DAILY_LIMIT}${NC} 個知識點"
        fi
    else
        echo -e "  • 服務器：${RED}❌ 未運行${NC}"
    fi
    
    # 檢查資料庫連接
    if [ -f "$ENV_FILE" ] && grep -q "DATABASE_URL" "$ENV_FILE"; then
        echo -e "  • 資料庫：${GREEN}已配置${NC}"
    else
        echo -e "  • 資料庫：${YELLOW}⚠️  未配置${NC}"
    fi
    
    # 檢查 API Key
    if [ -f "$ENV_FILE" ] && grep -q "GEMINI_API_KEY" "$ENV_FILE" && ! grep -q "your_gemini_api_key_here" "$ENV_FILE"; then
        echo -e "  • AI 服務：${GREEN}已配置${NC}"
    else
        echo -e "  • AI 服務：${YELLOW}⚠️  未配置${NC}"
    fi
    
    echo ""
}

# 確認操作
confirm_action() {
    local message="$1"
    echo -e "${YELLOW}${message}${NC}"
    read -p "確定要繼續嗎？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ 操作已取消${NC}"
        return 1
    fi
    return 0
}

# 等待任意鍵
wait_key() {
    echo ""
    read -p "按任意鍵返回主選單..." -n 1 -r
    echo
}

# 檢查 Python 環境
check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        echo -e "${RED}❌ Python3 未安裝${NC}"
        echo "請先安裝 Python 3.9 或以上版本"
        exit 1
    fi
    
    # 檢查 Python 版本
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION} 已安裝"
}

# 設置虛擬環境
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${BLUE}📦 建立虛擬環境...${NC}"
        python3 -m venv "$VENV_DIR"
        echo -e "${GREEN}✓${NC} 虛擬環境已建立"
    else
        echo -e "${GREEN}✓${NC} 虛擬環境已存在"
    fi
}

# 安裝依賴
install_dependencies() {
    echo -e "${BLUE}📚 檢查並安裝依賴...${NC}"
    "$PIP_BIN" install -q --upgrade pip
    "$PIP_BIN" install -q -r "$PROJECT_DIR/requirements.txt"
    echo -e "${GREEN}✓${NC} 依賴安裝完成"
}

# 載入環境變數
load_env() {
    if [ -f "$ENV_FILE" ]; then
        # shellcheck disable=SC2046
        export $(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" | xargs)
    fi
}

# ==================== 功能函數 ====================

# 1. 快速啟動
quick_start() {
    show_header
    echo -e "${BOLD}🚀 快速啟動服務${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 檢查是否已在運行
    if pgrep -f "uvicorn web.main:app" > /dev/null; then
        echo -e "${YELLOW}⚠️  服務器已在運行中${NC}"
        wait_key
        return
    fi
    
    check_python
    setup_venv
    install_dependencies
    load_env
    
    # 檢查關鍵配置
    if [ -z "${GEMINI_API_KEY:-}" ]; then
        echo -e "${YELLOW}⚠️  未設定 GEMINI_API_KEY${NC}"
        echo "AI 批改功能將不可用，但可以瀏覽頁面"
    fi
    
    # 啟動服務
    HOST="${HOST:-$DEFAULT_HOST}"
    PORT="${PORT:-$DEFAULT_PORT}"
    echo ""
    echo -e "${GREEN}🎉 啟動 Web 服務於 http://${HOST}:${PORT}${NC}"
    echo ""
    echo "提示："
    echo "  • 使用 Ctrl+C 停止服務器"
    echo "  • 日誌將顯示在下方"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    exec "$PYTHON_BIN" -m uvicorn web.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level info
}

# 2. 開發模式
dev_mode() {
    show_header
    echo -e "${BOLD}🔧 開發模式${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 檢查是否已在運行
    if pgrep -f "uvicorn web.main:app" > /dev/null; then
        echo -e "${YELLOW}⚠️  服務器已在運行中${NC}"
        
        # 顯示當前日誌
        echo ""
        echo "顯示最近的服務器日誌："
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        if [ -f "$SERVER_LOG" ]; then
            tail -n 20 "$SERVER_LOG"
        fi
        wait_key
        return
    fi
    
    check_python
    setup_venv
    install_dependencies
    load_env
    
    # 設置開發環境變數
    export DEV_MODE=true
    export LOG_LEVEL=DEBUG
    
    HOST="${HOST:-$DEFAULT_HOST}"
    PORT="${PORT:-$DEFAULT_PORT}"
    
    echo ""
    echo -e "${GREEN}🔧 啟動開發服務器（自動重載）${NC}"
    echo -e "訪問地址: http://${HOST}:${PORT}"
    echo ""
    
    # 在背景啟動，並保存日誌
    nohup "$PYTHON_BIN" -m uvicorn web.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level debug > "$SERVER_LOG" 2>&1 &
    
    SERVER_PID=$!
    echo -e "${GREEN}✓${NC} 服務器已在背景啟動 (PID: $SERVER_PID)"
    echo ""
    echo "提示："
    echo "  • 使用 'tail -f $SERVER_LOG' 查看日誌"
    echo "  • 使用選項 5 停止服務器"
    
    wait_key
}

# 3. 系統重置
system_reset() {
    show_header
    echo -e "${BOLD}🔄 系統重置${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo -e "${YELLOW}⚠️  警告：此操作將會：${NC}"
    echo "  • 清空所有知識點"
    echo "  • 清空所有練習記錄"
    echo "  • 重置每日統計"
    echo "  • 重置用戶設定為默認值"
    echo ""
    
    if ! confirm_action "確定要重置系統嗎？"; then
        return
    fi
    
    echo ""
    echo -e "${BLUE}開始重置...${NC}"
    
    # 停止服務器
    echo "1. 停止服務器..."
    pkill -f "uvicorn web.main:app" 2>/dev/null || true
    sleep 2
    
    # 清空資料庫
    echo "2. 清空資料庫..."
    load_env
    "$PYTHON_BIN" << 'EOF'
import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://linker_user:linker_pass123@localhost:5432/linker")

async def reset_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 清空表
        tables = ["knowledge_points", "daily_knowledge_stats", "user_settings"]
        for table in tables:
            try:
                await conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                print(f"  ✓ 清空表: {table}")
            except:
                await conn.execute(f"DELETE FROM {table}")
                print(f"  ✓ 清空表: {table} (使用 DELETE)")
        
        # 重置默認設定
        await conn.execute("""
            INSERT INTO user_settings (user_id, daily_knowledge_limit, limit_enabled)
            VALUES ('default_user', 15, true)
            ON CONFLICT (user_id) DO UPDATE SET
                daily_knowledge_limit = 15,
                limit_enabled = true,
                updated_at = CURRENT_TIMESTAMP
        """)
        print("  ✓ 用戶設定已重置為默認值")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
        return False

asyncio.run(reset_db())
EOF
    
    # 清理快取
    echo "3. 清理快取..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    echo ""
    echo -e "${GREEN}✅ 系統重置完成！${NC}"
    wait_key
}

# 4. 資料庫管理
database_management() {
    show_header
    echo -e "${BOLD}🗄️  資料庫管理${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1) 初始化資料庫結構"
    echo "2) 備份資料庫"
    echo "3) 還原資料庫"
    echo "4) 檢查資料庫狀態"
    echo "5) 清空資料庫（危險）"
    echo "0) 返回主選單"
    echo ""
    read -p "請選擇操作 [0-5]: " -n 1 -r
    echo
    
    case $REPLY in
        1)
            echo -e "\n${BLUE}初始化資料庫結構...${NC}"
            load_env
            "$PYTHON_BIN" scripts/init_database.py
            echo -e "${GREEN}✓${NC} 資料庫結構已初始化"
            ;;
        2)
            echo -e "\n${BLUE}備份資料庫...${NC}"
            BACKUP_FILE="data/backups/backup_$(date +%Y%m%d_%H%M%S).sql"
            mkdir -p data/backups
            load_env
            DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
            pg_dump $DATABASE_URL > "$BACKUP_FILE"
            echo -e "${GREEN}✓${NC} 備份已保存至: $BACKUP_FILE"
            ;;
        3)
            echo -e "\n${BLUE}還原資料庫...${NC}"
            echo "可用的備份檔案："
            ls -la data/backups/*.sql 2>/dev/null || echo "  沒有找到備份檔案"
            ;;
        4)
            echo -e "\n${BLUE}檢查資料庫狀態...${NC}"
            load_env
            "$PYTHON_BIN" scripts/check_config.py
            ;;
        5)
            echo -e "\n${RED}⚠️  危險操作！${NC}"
            if confirm_action "確定要清空整個資料庫嗎？"; then
                "$PYTHON_BIN" scripts/reset_database.py
            fi
            ;;
        0)
            return
            ;;
    esac
    
    wait_key
    database_management  # 返回子選單
}

# 5. 停止服務
stop_server() {
    show_header
    echo -e "${BOLD}⏹️  停止服務${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if pgrep -f "uvicorn web.main:app" > /dev/null; then
        echo -e "${BLUE}正在停止服務器...${NC}"
        pkill -f "uvicorn web.main:app"
        sleep 2
        echo -e "${GREEN}✓${NC} 服務器已停止"
    else
        echo -e "${YELLOW}服務器未在運行${NC}"
    fi
    
    wait_key
}

# 6. 程式碼品質檢查
code_quality() {
    show_header
    echo -e "${BOLD}🔍 程式碼品質檢查${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    setup_venv
    
    echo -e "${BLUE}執行 Ruff 檢查...${NC}"
    echo ""
    
    # 安裝 ruff
    "$PIP_BIN" install -q ruff
    
    # 執行檢查
    "$VENV_DIR/bin/ruff" check . --statistics
    
    echo ""
    echo -e "${BLUE}程式碼格式化建議：${NC}"
    "$VENV_DIR/bin/ruff" format . --check
    
    echo ""
    read -p "是否要自動修復可修復的問題？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        "$VENV_DIR/bin/ruff" check . --fix
        "$VENV_DIR/bin/ruff" format .
        echo -e "${GREEN}✓${NC} 自動修復完成"
    fi
    
    wait_key
}

# 7. 測試套件
run_tests() {
    show_header
    echo -e "${BOLD}🧪 執行測試${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    setup_venv
    install_dependencies
    
    echo ""
    echo "1) 執行所有測試"
    echo "2) 執行單元測試"
    echo "3) 執行整合測試"
    echo "4) 測試 API 端點"
    echo "5) 測試資料庫連接"
    echo "0) 返回主選單"
    echo ""
    read -p "請選擇測試類型 [0-5]: " -n 1 -r
    echo
    
    case $REPLY in
        1)
            echo -e "\n${BLUE}執行所有測試...${NC}"
            "$PYTHON_BIN" -m pytest tests/ -v --cov=core --cov=web
            ;;
        2)
            echo -e "\n${BLUE}執行單元測試...${NC}"
            "$PYTHON_BIN" -m pytest tests/ -m unit -v
            ;;
        3)
            echo -e "\n${BLUE}執行整合測試...${NC}"
            "$PYTHON_BIN" -m pytest tests/ -m integration -v
            ;;
        4)
            echo -e "\n${BLUE}測試 API 端點...${NC}"
            "$PYTHON_BIN" scripts/test_all_routes.py
            ;;
        5)
            echo -e "\n${BLUE}測試資料庫連接...${NC}"
            "$PYTHON_BIN" scripts/test_database_mode.py
            ;;
        0)
            return
            ;;
    esac
    
    wait_key
}

# 8. 環境設定
environment_setup() {
    show_header
    echo -e "${BOLD}⚙️  環境設定${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 檢查 .env 文件
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}未找到 .env 文件，正在建立...${NC}"
        cp .env.example "$ENV_FILE" 2>/dev/null || touch "$ENV_FILE"
    fi
    
    echo -e "${BLUE}當前環境設定：${NC}"
    echo ""
    
    # 顯示關鍵設定
    if grep -q "GEMINI_API_KEY" "$ENV_FILE"; then
        API_KEY=$(grep "GEMINI_API_KEY" "$ENV_FILE" | cut -d '=' -f2)
        if [ "$API_KEY" != "your_gemini_api_key_here" ] && [ ! -z "$API_KEY" ]; then
            echo -e "  • Gemini API Key: ${GREEN}已設定${NC}"
        else
            echo -e "  • Gemini API Key: ${RED}未設定${NC}"
        fi
    else
        echo -e "  • Gemini API Key: ${RED}未設定${NC}"
    fi
    
    if grep -q "DATABASE_URL" "$ENV_FILE"; then
        echo -e "  • 資料庫連接: ${GREEN}已設定${NC}"
    else
        echo -e "  • 資料庫連接: ${RED}未設定${NC}"
    fi
    
    if grep -q "DEFAULT_DAILY_LIMIT" "$ENV_FILE"; then
        LIMIT=$(grep "DEFAULT_DAILY_LIMIT" "$ENV_FILE" | cut -d '=' -f2)
        echo -e "  • 每日限額: ${CYAN}${LIMIT}${NC}"
    else
        echo -e "  • 每日限額: ${CYAN}15${NC} (預設)"
    fi
    
    echo ""
    echo "選項："
    echo "1) 設定 Gemini API Key"
    echo "2) 設定資料庫連接"
    echo "3) 設定每日限額"
    echo "4) 查看完整 .env 文件"
    echo "5) 編輯 .env 文件"
    echo "0) 返回主選單"
    echo ""
    read -p "請選擇操作 [0-5]: " -n 1 -r
    echo
    
    case $REPLY in
        1)
            echo ""
            read -p "請輸入 Gemini API Key: " API_KEY
            if [ ! -z "$API_KEY" ]; then
                if grep -q "GEMINI_API_KEY" "$ENV_FILE"; then
                    sed -i.bak "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$API_KEY/" "$ENV_FILE"
                else
                    echo "GEMINI_API_KEY=$API_KEY" >> "$ENV_FILE"
                fi
                echo -e "${GREEN}✓${NC} API Key 已設定"
            fi
            ;;
        2)
            echo ""
            echo "資料庫連接格式: postgresql://user:password@host:port/database"
            read -p "請輸入資料庫連接字串: " DB_URL
            if [ ! -z "$DB_URL" ]; then
                if grep -q "DATABASE_URL" "$ENV_FILE"; then
                    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=$DB_URL|" "$ENV_FILE"
                else
                    echo "DATABASE_URL=$DB_URL" >> "$ENV_FILE"
                fi
                echo -e "${GREEN}✓${NC} 資料庫連接已設定"
            fi
            ;;
        3)
            echo ""
            read -p "請輸入每日限額 (1-50): " LIMIT
            if [[ "$LIMIT" =~ ^[0-9]+$ ]] && [ "$LIMIT" -ge 1 ] && [ "$LIMIT" -le 50 ]; then
                if grep -q "DEFAULT_DAILY_LIMIT" "$ENV_FILE"; then
                    sed -i.bak "s/DEFAULT_DAILY_LIMIT=.*/DEFAULT_DAILY_LIMIT=$LIMIT/" "$ENV_FILE"
                else
                    echo "DEFAULT_DAILY_LIMIT=$LIMIT" >> "$ENV_FILE"
                fi
                echo -e "${GREEN}✓${NC} 每日限額已設定為 $LIMIT"
            else
                echo -e "${RED}無效的數值${NC}"
            fi
            ;;
        4)
            echo ""
            echo -e "${BLUE}.env 文件內容：${NC}"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            cat "$ENV_FILE"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ;;
        5)
            ${EDITOR:-nano} "$ENV_FILE"
            ;;
        0)
            return
            ;;
    esac
    
    wait_key
    environment_setup  # 返回子選單
}

# 9. 快速連結
quick_links() {
    show_header
    echo -e "${BOLD}🔗 快速連結${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    PORT="${PORT:-$DEFAULT_PORT}"
    
    echo -e "${BLUE}網頁介面：${NC}"
    echo "  • 主頁: http://localhost:$PORT"
    echo "  • 練習頁面: http://localhost:$PORT/practice"
    echo "  • 知識點管理: http://localhost:$PORT/knowledge"
    echo "  • 文法模式: http://localhost:$PORT/patterns"
    echo "  • 設定頁面: http://localhost:$PORT/settings"
    echo ""
    echo -e "${BLUE}API 端點：${NC}"
    echo "  • 健康檢查: http://localhost:$PORT/healthz"
    echo "  • API 文檔: http://localhost:$PORT/docs"
    echo "  • 每日狀態: http://localhost:$PORT/api/knowledge/daily-limit/status"
    echo ""
    echo -e "${BLUE}開發工具：${NC}"
    echo "  • 查看日誌: tail -f $SERVER_LOG"
    echo "  • Python Shell: $PYTHON_BIN"
    echo "  • 資料庫 Shell: psql \$DATABASE_URL"
    
    wait_key
}

# 10. 系統資訊
system_info() {
    show_header
    echo -e "${BOLD}ℹ️  系統資訊${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo -e "${BLUE}專案資訊：${NC}"
    echo "  • 專案路徑: $PROJECT_DIR"
    echo "  • Python 版本: $(python3 --version)"
    echo "  • 虛擬環境: $VENV_DIR"
    echo ""
    
    echo -e "${BLUE}依賴套件：${NC}"
    if [ -d "$VENV_DIR" ]; then
        "$PIP_BIN" list | head -20
        echo "  ..."
        echo "  (使用 '$PIP_BIN list' 查看完整列表)"
    else
        echo "  虛擬環境未建立"
    fi
    echo ""
    
    echo -e "${BLUE}資料統計：${NC}"
    if [ -f "$ENV_FILE" ]; then
        load_env
        "$PYTHON_BIN" -c "
import asyncio
import asyncpg
import os

async def get_stats():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        
        # 獲取統計
        kp_count = await conn.fetchval('SELECT COUNT(*) FROM knowledge_points WHERE NOT is_deleted')
        deleted_count = await conn.fetchval('SELECT COUNT(*) FROM knowledge_points WHERE is_deleted')
        
        print(f'  • 知識點總數: {kp_count}')
        print(f'  • 已刪除知識點: {deleted_count}')
        
        await conn.close()
    except Exception as e:
        print(f'  • 無法連接資料庫: {e}')

asyncio.run(get_stats())
" 2>/dev/null || echo "  • 無法獲取統計資料"
    fi
    
    wait_key
}

# ==================== 主程式 ====================

main_menu() {
    while true; do
        show_header
        show_status
        
        echo -e "${BOLD}📋 主選單${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "  1) 🚀 快速啟動"
        echo "  2) 🔧 開發模式（背景執行 + 自動重載）"
        echo "  3) 🔄 系統重置"
        echo "  4) 🗄️  資料庫管理"
        echo "  5) ⏹️  停止服務"
        echo "  6) 🔍 程式碼品質檢查"
        echo "  7) 🧪 執行測試"
        echo "  8) ⚙️  環境設定"
        echo "  9) 🔗 快速連結"
        echo " 10) ℹ️  系統資訊"
        echo "  0) 🚪 離開"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        read -p "請選擇功能 [0-10]: " choice
        
        case $choice in
            1) quick_start ;;
            2) dev_mode ;;
            3) system_reset ;;
            4) database_management ;;
            5) stop_server ;;
            6) code_quality ;;
            7) run_tests ;;
            8) environment_setup ;;
            9) quick_links ;;
            10) system_info ;;
            0) 
                echo ""
                echo -e "${GREEN}感謝使用 Linker！再見！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}無效的選項${NC}"
                sleep 1
                ;;
        esac
    done
}

# ==================== 程式入口 ====================

# 處理命令列參數
case "${1:-}" in
    start|run)
        quick_start
        ;;
    dev)
        dev_mode
        ;;
    stop)
        stop_server
        ;;
    reset)
        system_reset
        ;;
    test)
        run_tests
        ;;
    help|--help|-h)
        echo "Linker 專案管理系統"
        echo ""
        echo "用法: ./linker.sh [命令]"
        echo ""
        echo "命令:"
        echo "  start, run   快速啟動服務"
        echo "  dev          開發模式"
        echo "  stop         停止服務"
        echo "  reset        重置系統"
        echo "  test         執行測試"
        echo "  help         顯示此說明"
        echo ""
        echo "不帶參數執行將顯示互動式選單"
        ;;
    *)
        main_menu
        ;;
esac