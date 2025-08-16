#!/usr/bin/env python3
"""
檢查資料庫中的 NULL 時間戳
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import get_database_connection


async def check_null_timestamps():
    """檢查資料庫中的 NULL 時間戳"""

    print("\n" + "=" * 60)
    print("檢查資料庫中的 NULL 時間戳")
    print("=" * 60)

    db_connection = get_database_connection()

    try:
        pool = await db_connection.connect()
        if not pool:
            print("❌ 無法連接到資料庫")
            return

        async with pool.acquire() as conn:
            # 檢查 knowledge_points 表
            print("\n1. 檢查 knowledge_points 表：")
            query = """
                SELECT id, key_point,
                       created_at IS NULL as created_null,
                       last_seen IS NULL as seen_null,
                       next_review IS NULL as review_null,
                       last_modified IS NULL as modified_null
                FROM knowledge_points
                WHERE created_at IS NULL
                   OR last_seen IS NULL
                   OR last_modified IS NULL
                LIMIT 10
            """
            rows = await conn.fetch(query)

            if rows:
                print(f"   ⚠️ 發現 {len(rows)} 個知識點有 NULL 時間戳：")
                for row in rows:
                    print(f"      ID {row['id']}: {row['key_point'][:30]}...")
                    if row["created_null"]:
                        print("         - created_at 為 NULL")
                    if row["seen_null"]:
                        print("         - last_seen 為 NULL")
                    if row["review_null"]:
                        print("         - next_review 為 NULL")
                    if row["modified_null"]:
                        print("         - last_modified 為 NULL")
            else:
                print("   ✅ 沒有發現 NULL 時間戳")

            # 檢查 original_errors 表
            print("\n2. 檢查 original_errors 表：")
            query = """
                SELECT knowledge_point_id,
                       timestamp IS NULL as timestamp_null
                FROM original_errors
                WHERE timestamp IS NULL
                LIMIT 10
            """
            rows = await conn.fetch(query)

            if rows:
                print(f"   ⚠️ 發現 {len(rows)} 個原始錯誤有 NULL 時間戳：")
                for row in rows:
                    print(f"      知識點 ID {row['knowledge_point_id']}: timestamp 為 NULL")
            else:
                print("   ✅ 沒有發現 NULL 時間戳")

            # 檢查 ID 22 的具體情況
            print("\n3. 檢查 ID 22 的知識點：")
            query = """
                SELECT
                    kp.id,
                    kp.key_point,
                    kp.created_at,
                    kp.last_seen,
                    kp.next_review,
                    kp.last_modified,
                    oe.timestamp as oe_timestamp
                FROM knowledge_points kp
                LEFT JOIN original_errors oe ON kp.id = oe.knowledge_point_id
                WHERE kp.id = 22
            """
            row = await conn.fetchrow(query)

            if row:
                print(f"   知識點 ID 22: {row['key_point'][:50]}...")
                print(f"      created_at: {row['created_at']}")
                print(f"      last_seen: {row['last_seen']}")
                print(f"      next_review: {row['next_review']}")
                print(f"      last_modified: {row['last_modified']}")
                print(f"      oe_timestamp: {row['oe_timestamp']}")
            else:
                print("   ❌ 找不到 ID 22 的知識點")

    finally:
        await db_connection.disconnect()

    print("\n" + "=" * 60)
    print("檢查完成")
    print("=" * 60 + "\n")


async def main():
    """主程式"""
    try:
        await check_null_timestamps()
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
