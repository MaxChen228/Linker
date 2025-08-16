#!/bin/bash
# 完整的資料庫遷移流程腳本
# 自動化執行所有必要的遷移步驟

set -e  # 遇到錯誤立即退出

# 顏色定義
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

# 檢查必要的依賴
check_dependencies() {
    log_info "檢查依賴..."

    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python 3"
        exit 1
    fi

    # 檢查 PostgreSQL 客戶端
    if ! python3 -c "import asyncpg" 2>/dev/null; then
        log_warning "未安裝 asyncpg，嘗試安裝..."
        pip install asyncpg || {
            log_error "無法安裝 asyncpg"
            exit 1
        }
    fi

    log_success "依賴檢查完成"
}

# 備份現有 JSON 資料
backup_json_data() {
    log_info "備份現有 JSON 資料..."

    if [ -f "data/knowledge.json" ]; then
        backup_file="data/knowledge_backup_$(date +%Y%m%d_%H%M%S).json"
        cp "data/knowledge.json" "$backup_file"
        log_success "JSON 資料已備份到: $backup_file"
    else
        log_warning "未找到 knowledge.json 檔案"
    fi
}

# 設定環境變數用於測試
setup_test_env() {
    export USE_DATABASE=true
    export ENABLE_DUAL_WRITE=false
    log_info "已設定環境變數 (USE_DATABASE=true)"
}

# 初始化資料庫
init_database() {
    log_info "初始化資料庫..."

    if python3 scripts/init_database.py --check-only; then
        log_warning "資料庫已初始化"
        read -p "是否要重新初始化？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "跳過資料庫初始化"
            return 0
        fi
    fi

    python3 scripts/init_database.py || {
        log_error "資料庫初始化失敗"
        exit 1
    }

    log_success "資料庫初始化完成"
}

# 執行資料遷移
migrate_data() {
    log_info "執行資料遷移..."

    # 先執行乾跑檢查
    log_info "執行乾跑檢查..."
    python3 scripts/migrate_data.py --dry-run || {
        log_error "乾跑檢查失敗"
        exit 1
    }

    # 詢問用戶確認
    read -p "確定要執行資料遷移嗎？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "取消遷移"
        exit 0
    fi

    # 執行實際遷移
    python3 scripts/migrate_data.py --batch-size 20 || {
        log_error "資料遷移失敗"
        exit 1
    }

    log_success "資料遷移完成"
}

# 驗證遷移結果
verify_migration() {
    log_info "驗證遷移結果..."

    python3 scripts/migrate_data.py --verify-only || {
        log_error "遷移驗證失敗"
        return 1
    }

    log_success "遷移驗證通過"
    return 0
}

# 配置為資料庫模式
configure_database_mode() {
    log_info "配置為資料庫模式..."

    python3 scripts/configure_db.py --mode database || {
        log_error "配置資料庫模式失敗"
        exit 1
    }

    log_success "已配置為資料庫模式"
}

# 測試應用程式
test_application() {
    log_info "測試應用程式..."

    # 簡單的測試：檢查配置是否正確
    python3 scripts/configure_db.py --show

    log_info "建議手動測試應用程式功能"
}

# 主流程
main() {
    echo "======================================="
    echo "Linker 資料庫遷移工具"
    echo "從 JSON 檔案遷移到 PostgreSQL"
    echo "======================================="
    echo

    # 檢查參數
    SKIP_BACKUP=false
    SKIP_VERIFICATION=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-verification)
                SKIP_VERIFICATION=true
                shift
                ;;
            --help|-h)
                echo "使用方式: $0 [選項]"
                echo "選項:"
                echo "  --skip-backup       跳過 JSON 資料備份"
                echo "  --skip-verification 跳過遷移驗證"
                echo "  --help, -h          顯示此說明"
                exit 0
                ;;
            *)
                log_error "未知選項: $1"
                echo "使用 --help 查看可用選項"
                exit 1
                ;;
        esac
    done

    # 執行遷移流程
    log_info "開始遷移流程..."
    echo

    # 步驟 1: 檢查依賴
    check_dependencies
    echo

    # 步驟 2: 備份資料
    if [ "$SKIP_BACKUP" = false ]; then
        backup_json_data
        echo
    fi

    # 步驟 3: 設定測試環境
    setup_test_env
    echo

    # 步驟 4: 初始化資料庫
    init_database
    echo

    # 步驟 5: 執行遷移
    migrate_data
    echo

    # 步驟 6: 驗證遷移
    if [ "$SKIP_VERIFICATION" = false ]; then
        if verify_migration; then
            echo
        else
            log_warning "驗證失敗，但遷移可能仍然成功"
            read -p "是否繼續？(y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "遷移流程中止"
                exit 1
            fi
        fi
    fi

    # 步驟 7: 配置資料庫模式
    configure_database_mode
    echo

    # 步驟 8: 測試應用程式
    test_application
    echo

    # 完成
    log_success "🎉 遷移流程完成！"
    echo
    echo "後續步驟:"
    echo "1. 重啟應用程式以套用新配置"
    echo "2. 測試所有功能是否正常"
    echo "3. 如有問題，使用備份檔案回滾"
    echo "4. 確認穩定後，可刪除舊的 JSON 備份"
}

# 錯誤處理
trap 'log_error "遷移流程被中斷"; exit 1' INT TERM

# 執行主流程
main "$@"
