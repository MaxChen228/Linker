"""
應用程式配置管理

此模組集中管理所有環境變數和配置設定，並提供以下功能：
- 從 .env 文件或環境變數載入配置。
- 根據不同部署環境（如本地、Render）決定資料目錄。
- 在應用啟動時驗證配置的有效性，並提供清晰的錯誤和警告訊息。
- 提供資料庫健康檢查功能。
- 匯總並提供配置摘要。

此模組的設計旨在消除硬編碼，提高應用的可配置性和安全性。
"""

import contextlib
import os
import sys
from pathlib import Path

# 嘗試導入新的統一配置管理系統，如果失敗則優雅降級
# TASK-34: 導入統一配置管理系統，消除硬編碼
try:
    from core.settings.database import get_database_config

    _database_config_available = True
except ImportError:
    _database_config_available = False

# 載入 .env 文件，優先使用 .env，若不存在則使用 .env.example 作為備用
try:
    from dotenv import load_dotenv

    if Path(".env").exists():
        load_dotenv(".env")
    elif Path(".env.example").exists():
        print("⚠️  警告：正在使用 .env.example 作為後備配置。建議複製為 .env 並進行修改。")
        load_dotenv(".env.example")
except ImportError:
    # 如果 python-dotenv 未安裝，則忽略
    pass


def get_data_dir() -> Path:
    """
    根據運行環境獲取資料目錄的路徑。

    處理 Render 部署環境、自訂環境變數和本地預設路徑。

    Returns:
        資料目錄的 Path 物件。
    """
    # 檢查是否在 Render 環境運行
    if os.environ.get("RENDER"):
        # 在 Render 上，如果掛載了磁碟，則使用 /data 目錄
        render_disk = Path("/data")
        if render_disk.exists() and os.access(render_disk, os.W_OK):
            return render_disk
        # 否則，退回到專案原始碼目錄中的 data 資料夾
        return Path("/opt/render/project/src/data")

    # 檢查是否有自訂的 DATA_DIR 環境變數
    if custom_dir := os.environ.get("DATA_DIR"):
        return Path(custom_dir)

    # 預設使用專案根目錄下的 data 資料夾
    return Path(__file__).resolve().parent.parent / "data"


def validate_config() -> tuple[bool, list[str], list[str]]:
    """
    驗證應用程式的關鍵配置。

    檢查 Gemini API 金鑰、資料庫連接、資料目錄和日誌級別等。

    Returns:
        一個元組 (is_valid, errors, warnings)，包含驗證結果、
        致命錯誤列表和非致命警告列表。
    """
    errors = []
    warnings = []

    # 1. 驗證 Gemini API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        errors.append("❌ GEMINI_API_KEY 未設定或使用預設值。請提供有效的 API Key。")

    # 2. 驗證資料庫配置 (系統現在強制使用資料庫模式)
    if _database_config_available:
        try:
            db_config = get_database_config()
            if not db_config.is_configured():
                errors.append("❌ 資料庫連接未配置。請設定 DATABASE_URL 環境變數。")
            else:
                db_info = db_config.get_database_info()
                if (
                    db_info.get("environment") == "production"
                    and db_info.get("hostname") == "localhost"
                ):
                    warnings.append("⚠️  警告：生產環境不建議使用 localhost 作為資料庫主機。")
        except Exception as e:
            errors.append(f"❌ 資料庫配置驗證失敗: {e}")
    else:
        # 向後相容性檢查
        if not DATABASE_URL:
            errors.append("❌ 資料庫連接 URL (DATABASE_URL) 未設定。")

    # 3. 驗證資料目錄
    if not DATA_DIR.exists():
        try:
            DATA_DIR.mkdir(exist_ok=True, parents=True)
            warnings.append(f"ℹ️  資料目錄不存在，已自動創建於: {DATA_DIR}")
        except Exception as e:
            errors.append(f"❌ 無法創建資料目錄 {DATA_DIR}: {e}")

    # 4. 驗證日誌級別
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL not in valid_log_levels:
        warnings.append(f"⚠️  無效的日誌級別 (LOG_LEVEL): {LOG_LEVEL}。將使用預設值 INFO。")

    return not errors, errors, warnings


def print_config_status():
    """在非測試環境中，打印配置狀態檢查的結果。"""
    if "pytest" in sys.modules:
        return

    is_valid, errors, warnings = validate_config()

    if not is_valid or warnings:
        print("\n" + "=" * 50)
        print("          應用程式配置狀態檢查")
        print("=" * 50)

        if errors:
            print("\n❌ 發現致命錯誤 (必須修復才能啟動):")
            for error in errors:
                print(f"  {error}")

        if warnings:
            print("\n⚠️  發現警告 (建議處理):")
            for warning in warnings:
                print(f"  {warning}")

        print("\n" + "=" * 50)

        if not is_valid:
            print("\n💡 解決建議:")
            print("  1. 如果您是初次使用，請將 .env.example 複製為 .env。")
            print(
                "  2. 編輯 .env 文件，填寫必要的環境變數，特別是 DATABASE_URL 和 GEMINI_API_KEY。"
            )
            print("  3. 儲存後重新啟動應用程式。")
            print("\n")


# --- 全域配置變數定義 ---

# 資料目錄
DATA_DIR = get_data_dir()

# 資料庫配置 (JSON 模式已移除，強制使用資料庫)
USE_DATABASE = True
ENABLE_DUAL_WRITE = False  # 雙寫模式已移除

# 使用統一的資料庫配置管理系統
if _database_config_available:
    try:
        db_config = get_database_config()
        DATABASE_URL = db_config.get_url() if db_config.is_configured() else None
    except Exception as e:
        print(f"⚠️  警告：載入資料庫配置時發生錯誤: {e}")
        DATABASE_URL = None
else:
    # 向後相容：直接從環境變數讀取，不提供不安全的硬編碼預設值
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("⚠️  警告：DATABASE_URL 環境變數未設定，資料庫功能將不可用。")

# 日誌級別
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 開發模式
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# 練習相關配置
AUTO_SAVE_KNOWLEDGE_POINTS = os.getenv("AUTO_SAVE_KNOWLEDGE_POINTS", "false").lower() == "true"
SHOW_CONFIRMATION_UI = os.getenv("SHOW_CONFIRMATION_UI", "true").lower() == "true"

# 確保資料目錄存在
with contextlib.suppress(PermissionError):
    DATA_DIR.mkdir(exist_ok=True, parents=True)


def check_database_health() -> tuple[bool, str]:
    """
    檢查資料庫連線的健康狀態。

    Returns:
        一個元組 (is_healthy, message)，表示健康狀態和相關訊息。
    """
    if not USE_DATABASE:
        return False, "系統配置錯誤：USE_DATABASE 應為 True（JSON 模式已移除）。"

    try:
        import asyncio

        from core.database.connection import get_database_connection

        async def test_connection():
            conn = get_database_connection()
            try:
                pool = await conn.connect()
                if pool:
                    await conn.disconnect()
                    return True, "資料庫連線正常。"
                return False, "無法建立資料庫連線池。"
            except Exception as e:
                return False, f"資料庫連線失敗: {e}"

        # 安全地執行異步測試，避免在已運行的事件循環中創建新循環
        try:
            loop = asyncio.get_running_loop()
            return False, "無法在異步上下文中執行同步健康檢查。"
        except RuntimeError:
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(test_connection())
            finally:
                if loop:
                    loop.close()
                    asyncio.set_event_loop(None)

    except ImportError:
        return False, "資料庫相關模組未安裝 (例如 asyncpg)。"
    except Exception as e:
        return False, f"資料庫健康檢查失敗: {e}"


def switch_storage_mode(mode: str) -> bool:
    """
    切換儲存模式。此功能已廢棄，因為系統僅支援資料庫模式。

    Args:
        mode: 目標模式 ('json' 或 'database')。

    Returns:
        如果操作被接受，返回 True。
    """
    if mode == "json":
        print("❌ JSON 模式已移除，系統僅支援資料庫模式。")
        return False
    if mode == "database":
        print("✅ 系統已設定為資料庫模式。")
        return True
    print(f"❌ 無效的模式: {mode}。僅支援 'database' 模式。")
    return False


def get_config_summary() -> dict:
    """
    獲取應用程式配置的摘要。

    Returns:
        一個包含主要配置資訊和健康狀態的字典。
    """
    is_valid, errors, warnings = validate_config()
    db_healthy, db_message = check_database_health()

    return {
        "storage_mode": "database",  # JSON 模式已移除
        "data_directory": str(DATA_DIR),
        "log_level": LOG_LEVEL,
        "dev_mode": DEV_MODE,
        "dual_write_enabled": ENABLE_DUAL_WRITE,  # 雙寫模式已移除
        "config_is_valid": is_valid,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "database_is_healthy": db_healthy,
        "database_status_message": db_message,
        "gemini_api_key_is_set": bool(
            os.getenv("GEMINI_API_KEY")
            and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here"
        ),
    }


# 配置檢查由 web/main.py 手動執行，避免模塊導入時的環境變量載入順序問題
# print_config_status()
