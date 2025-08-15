"""
Configuration for deployment environments

提供集中化的配置管理，包含驗證、健康檢查和降級機制
"""

import contextlib
import os
import sys
from pathlib import Path

# 載入 .env 文件
try:
    from dotenv import load_dotenv

    # 優先載入 .env，如果不存在則嘗試 .env.example
    if Path(".env").exists():
        load_dotenv(".env")
    elif Path(".env.example").exists():
        print("⚠️  使用 .env.example 作為配置，建議複製為 .env 並修改")
        load_dotenv(".env.example")
except ImportError:
    # 如果沒有 python-dotenv，忽略
    pass


def get_data_dir() -> Path:
    """Get data directory based on environment"""
    # Check if running on Render
    if os.environ.get("RENDER"):
        # On Render, use /opt/render/project/src/data unless disk is mounted
        render_disk = Path("/data")
        if render_disk.exists() and os.access(render_disk, os.W_OK):
            return render_disk
        # Fall back to project directory
        return Path("/opt/render/project/src/data")

    # Check if custom data dir is specified
    if custom_dir := os.environ.get("DATA_DIR"):
        return Path(custom_dir)

    # Default to local data directory
    return Path(__file__).resolve().parent.parent / "data"


def validate_config() -> tuple[bool, list[str], list[str]]:
    """驗證配置設定

    Returns:
        (is_valid, errors, warnings): 是否有效、錯誤訊息和警告訊息
    """
    errors = []  # 致命錯誤
    warnings = []  # 非致命警告

    # 檢查 Gemini API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        errors.append("❌ GEMINI_API_KEY 未設置或使用預設值，請設置有效的 API Key")

    # 檢查資料庫模式設定
    if USE_DATABASE:
        if (
            not DATABASE_URL
            or DATABASE_URL == "postgresql://postgres:password@localhost:5432/linker"
        ):
            warnings.append(
                "⚠️  USE_DATABASE=true 但 DATABASE_URL 使用預設值，將嘗試自動降級到 JSON 模式"
            )

        # 檢查 adapter 是否已修復
        try:
            from core.database.adapter import KnowledgeManagerAdapter

            adapter = KnowledgeManagerAdapter(use_database=False)
            required_methods = [
                "get_active_points",
                "get_deleted_points",
                "edit_knowledge_point",
                "delete_knowledge_point",
                "restore_knowledge_point",
            ]
            missing_methods = [m for m in required_methods if not hasattr(adapter, m)]
            if missing_methods:
                warnings.append(f"⚠️  Database adapter 缺少方法: {', '.join(missing_methods)}")
        except Exception as e:
            warnings.append(f"⚠️  Database adapter 載入失敗: {e}")

    # 檢查資料目錄
    if not DATA_DIR.exists():
        try:
            DATA_DIR.mkdir(exist_ok=True, parents=True)
            warnings.append(f"ℹ️  已創建資料目錄: {DATA_DIR}")
        except Exception as e:
            errors.append(f"❌ 無法創建資料目錄 {DATA_DIR}: {e}")

    # 檢查日誌級別
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL not in valid_log_levels:
        warnings.append(f"⚠️  無效的 LOG_LEVEL: {LOG_LEVEL}，使用預設值 INFO")

    return len(errors) == 0, errors, warnings


def print_config_status():
    """印出配置狀態（僅在非測試環境）"""
    if "pytest" not in sys.modules:
        is_valid, errors, warnings = validate_config()

        if errors or warnings:
            print("\n" + "=" * 50)
            print("          配置狀態檢查")
            print("=" * 50)

            if errors:
                print("\n❌ 錯誤（必須修復）:")
                for error in errors:
                    print(f"  {error}")

            if warnings:
                print("\n⚠️  警告（建議處理）:")
                for warning in warnings:
                    print(f"  {warning}")

            print("\n" + "=" * 50)

            if errors:
                print("\n💡 建議:")
                print("  1. 複製 .env.example 為 .env")
                print("  2. 編輯 .env 設置必要的環境變數")
                print("  3. 重新啟動應用程式")
                print("\n")


# Global data directory
DATA_DIR = get_data_dir()

# Database configuration
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"
ENABLE_DUAL_WRITE = os.getenv("ENABLE_DUAL_WRITE", "false").lower() == "true"

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/linker")

# Log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Development mode
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# Practice configuration
AUTO_SAVE_KNOWLEDGE_POINTS = os.getenv("AUTO_SAVE_KNOWLEDGE_POINTS", "false").lower() == "true"
SHOW_CONFIRMATION_UI = os.getenv("SHOW_CONFIRMATION_UI", "true").lower() == "true"

# Only create directory if we have permission
with contextlib.suppress(PermissionError):
    DATA_DIR.mkdir(exist_ok=True, parents=True)


def check_database_health() -> tuple[bool, str]:
    """檢查資料庫連線健康狀態

    Returns:
        (is_healthy, message): 健康狀態和訊息
    """
    if not USE_DATABASE:
        return True, "使用 JSON 模式，無需資料庫"

    try:
        import asyncio

        from core.database.connection import get_database_connection

        async def test_connection():
            conn = get_database_connection()
            try:
                pool = await conn.connect()
                if pool:
                    await conn.disconnect()
                    return True, "資料庫連線正常"
                return False, "無法建立資料庫連線"
            except Exception as e:
                return False, f"資料庫連線失敗: {e}"

        # 安全地執行異步測試
        try:
            # 先檢查是否有運行中的事件循環
            loop = asyncio.get_running_loop()
            # 如果在異步上下文中，無法直接執行
            return False, "無法在異步上下文中執行同步健康檢查"
        except RuntimeError:
            # 沒有運行中的事件循環，可以安全創建新的
            loop = None
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(test_connection())
                return result
            finally:
                if loop:
                    loop.close()
                    asyncio.set_event_loop(None)

    except ImportError:
        return False, "資料庫模組未安裝"
    except Exception as e:
        return False, f"健康檢查失敗: {e}"


def switch_storage_mode(mode: str) -> bool:
    """切換儲存模式

    Args:
        mode: 'json' 或 'database'

    Returns:
        是否成功切換
    """
    global USE_DATABASE

    if mode not in ["json", "database"]:
        print(f"❌ 無效的模式: {mode}，請使用 'json' 或 'database'")
        return False

    if mode == "database":
        # 檢查資料庫健康狀態
        is_healthy, message = check_database_health()
        if not is_healthy:
            print(f"❌ 無法切換到資料庫模式: {message}")
            return False

    USE_DATABASE = mode == "database"
    os.environ["USE_DATABASE"] = str(USE_DATABASE).lower()

    print(f"✅ 已切換到 {mode} 模式")
    return True


def get_config_summary() -> dict:
    """獲取配置摘要

    Returns:
        配置資訊字典
    """
    is_valid, errors, warnings = validate_config()
    db_healthy, db_message = check_database_health() if USE_DATABASE else (True, "N/A")

    return {
        "storage_mode": "database" if USE_DATABASE else "json",
        "data_directory": str(DATA_DIR),
        "log_level": LOG_LEVEL,
        "dev_mode": DEV_MODE,
        "dual_write": ENABLE_DUAL_WRITE,
        "config_valid": is_valid,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "database_healthy": db_healthy,
        "database_message": db_message,
        "api_key_set": bool(
            os.getenv("GEMINI_API_KEY")
            and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here"
        ),
    }


# 在模組載入時執行配置檢查
print_config_status()
