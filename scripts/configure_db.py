#!/usr/bin/env python3
"""
資料庫配置管理工具
用於快速切換 JSON/資料庫模式
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.log_config import get_module_logger

logger = get_module_logger("configure_db")


def create_env_file(use_database: bool = False, dual_write: bool = False, database_url: str = None):
    """建立 .env 檔案"""
    env_file = project_root / ".env"

    # 讀取現有的 .env 檔案
    existing_env = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    existing_env[key.strip()] = value.strip()

    # 更新設定
    existing_env["USE_DATABASE"] = "true" if use_database else "false"
    existing_env["ENABLE_DUAL_WRITE"] = "true" if dual_write else "false"

    if database_url:
        existing_env["DATABASE_URL"] = database_url
    elif "DATABASE_URL" not in existing_env:
        existing_env["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/linker"

    # 寫入 .env 檔案
    with open(env_file, "w") as f:
        f.write("# Linker 專案配置\n")
        f.write("# 由 configure_db.py 自動生成\n\n")

        for key, value in existing_env.items():
            f.write(f"{key}={value}\n")

    logger.info(f"已建立配置檔案: {env_file}")
    return env_file


def show_current_config():
    """顯示當前配置"""
    from core.config import DATABASE_URL, ENABLE_DUAL_WRITE, USE_DATABASE

    logger.info("當前配置:")
    logger.info(f"  USE_DATABASE: {USE_DATABASE}")
    logger.info(f"  ENABLE_DUAL_WRITE: {ENABLE_DUAL_WRITE}")
    logger.info(f"  DATABASE_URL: {DATABASE_URL}")

    if USE_DATABASE:
        logger.info("  📊 模式: 資料庫模式")
    else:
        logger.info("  📁 模式: JSON 檔案模式")

    if ENABLE_DUAL_WRITE:
        logger.info("  🔄 雙寫模式: 啟用")
    else:
        logger.info("  🔄 雙寫模式: 停用")


def configure_json_mode():
    """配置為 JSON 模式"""
    logger.info("配置為 JSON 檔案模式...")
    create_env_file(use_database=False, dual_write=False)
    logger.info("✓ 已配置為 JSON 檔案模式")
    logger.info("重啟應用程式以套用更改")


def configure_database_mode(database_url: str = None):
    """配置為資料庫模式"""
    logger.info("配置為資料庫模式...")
    create_env_file(use_database=True, dual_write=False, database_url=database_url)
    logger.info("✓ 已配置為資料庫模式")
    logger.info("請確保資料庫已初始化並重啟應用程式")


def configure_dual_write_mode(database_url: str = None):
    """配置為雙寫模式"""
    logger.info("配置為雙寫模式...")
    create_env_file(use_database=False, dual_write=True, database_url=database_url)
    logger.info("✓ 已配置為雙寫模式")
    logger.info("雙寫模式將同時寫入 JSON 和資料庫，但讀取仍從 JSON")
    logger.info("重啟應用程式以套用更改")


def validate_database_connection(database_url: str) -> bool:
    """驗證資料庫連線"""
    try:
        import asyncio

        import asyncpg

        async def test_connection():
            try:
                conn = await asyncpg.connect(database_url)
                await conn.fetchval("SELECT 1")
                await conn.close()
                return True
            except Exception as e:
                logger.error(f"資料庫連線測試失敗: {e}")
                return False

        return asyncio.run(test_connection())
    except ImportError:
        logger.error("請安裝 asyncpg: pip install asyncpg")
        return False


def interactive_configure():
    """互動式配置"""
    print("\n=== Linker 資料庫配置工具 ===")

    show_current_config()

    print("\n選擇配置模式:")
    print("1. JSON 檔案模式 (預設)")
    print("2. 資料庫模式")
    print("3. 雙寫模式 (開發/測試用)")
    print("4. 顯示當前配置")
    print("0. 退出")

    choice = input("\n請選擇 (0-4): ").strip()

    if choice == "1":
        configure_json_mode()
    elif choice == "2":
        db_url = input(
            "資料庫 URL (預設: postgresql://postgres:password@localhost:5432/linker): "
        ).strip()
        if not db_url:
            db_url = None

        if db_url and not validate_database_connection(db_url):
            logger.error("無法連線到資料庫，請檢查 URL 和資料庫狀態")
            return

        configure_database_mode(db_url)
    elif choice == "3":
        db_url = input(
            "資料庫 URL (預設: postgresql://postgres:password@localhost:5432/linker): "
        ).strip()
        if not db_url:
            db_url = None

        configure_dual_write_mode(db_url)
    elif choice == "4":
        show_current_config()
    elif choice == "0":
        logger.info("退出")
    else:
        logger.error("無效選擇")


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="資料庫配置管理工具")
    parser.add_argument("--mode", choices=["json", "database", "dual"], help="設定模式")
    parser.add_argument("--database-url", help="資料庫連線 URL")
    parser.add_argument("--show", action="store_true", help="顯示當前配置")
    parser.add_argument("--interactive", action="store_true", help="互動式配置")

    args = parser.parse_args()

    if args.show:
        show_current_config()
    elif args.interactive:
        interactive_configure()
    elif args.mode:
        if args.mode == "json":
            configure_json_mode()
        elif args.mode == "database":
            configure_database_mode(args.database_url)
        elif args.mode == "dual":
            configure_dual_write_mode(args.database_url)
    else:
        # 預設為互動模式
        interactive_configure()


if __name__ == "__main__":
    main()
