#!/usr/bin/env python3
"""
資料庫初始化腳本
執行 schema.sql 來建立必要的資料表和索引
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import get_database_connection  # noqa: E402
from core.database.exceptions import DatabaseError  # noqa: E402
from core.log_config import get_module_logger  # noqa: E402

logger = get_module_logger("init_database")


async def init_database():
    """初始化資料庫結構"""
    try:
        # 取得資料庫連線
        db_conn = get_database_connection()

        # 建立連線
        pool = await db_conn.connect()
        if not pool:
            logger.error("無法建立資料庫連線")
            return False

        # 執行 schema 腳本
        schema_path = project_root / "core" / "database" / "schema.sql"
        if not schema_path.exists():
            logger.error(f"找不到 schema 檔案: {schema_path}")
            return False

        logger.info("正在執行資料庫 schema...")
        await db_conn.execute_script(str(schema_path))

        # 驗證資料表是否建立成功
        async with db_conn.get_connection() as conn:
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            table_names = [row["table_name"] for row in tables]
            logger.info(f"成功建立資料表: {table_names}")

            # 檢查必要的資料表
            required_tables = [
                "knowledge_points",
                "original_errors",
                "review_examples",
                "tags",
                "knowledge_point_tags",
                "knowledge_point_versions",
                "study_sessions",
                "daily_records",
                "weekly_goals",
            ]

            missing_tables = set(required_tables) - set(table_names)
            if missing_tables:
                logger.warning(f"缺少資料表: {missing_tables}")
            else:
                logger.info("✓ 所有必要資料表已建立")

        logger.info("資料庫初始化完成")
        return True

    except DatabaseError as e:
        logger.error(f"資料庫初始化失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"初始化過程中發生錯誤: {e}")
        return False
    finally:
        # 清理連線
        await db_conn.disconnect()


async def check_database_status():
    """檢查資料庫狀態"""
    try:
        db_conn = get_database_connection()
        health = await db_conn.health_check()

        logger.info("資料庫狀態檢查:")
        logger.info(f"  狀態: {health.get('status')}")
        logger.info(f"  訊息: {health.get('message')}")

        if pool_status := health.get("pool_status"):
            logger.info(f"  連線池大小: {pool_status.get('size')}")
            logger.info(f"  空閒連線: {pool_status.get('idle_connections')}")

        return health.get("status") == "healthy"

    except Exception as e:
        logger.error(f"資料庫狀態檢查失敗: {e}")
        return False


async def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="資料庫初始化工具")
    parser.add_argument("--check-only", action="store_true", help="僅檢查資料庫狀態")
    parser.add_argument("--force", action="store_true", help="強制重新初始化")

    args = parser.parse_args()

    if args.check_only:
        logger.info("檢查資料庫狀態...")
        success = await check_database_status()
        sys.exit(0 if success else 1)

    logger.info("開始資料庫初始化...")

    # 先檢查現有狀態
    if not args.force:
        logger.info("檢查現有資料庫狀態...")
        if await check_database_status():
            logger.info("資料庫已經初始化且狀態良好")
            response = input("是否要重新初始化? (y/N): ")
            if response.lower() != "y":
                logger.info("取消初始化")
                sys.exit(0)

    # 執行初始化
    success = await init_database()

    if success:
        logger.info("✓ 資料庫初始化成功")
        sys.exit(0)
    else:
        logger.error("✗ 資料庫初始化失敗")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
