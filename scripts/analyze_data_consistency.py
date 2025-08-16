#!/usr/bin/env python3
"""
數據一致性分析腳本
分析 JSON 和 Database 模式中的知識點差異
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database.connection import DatabaseSettings
from core.knowledge import KnowledgeManager


async def analyze_consistency():
    """分析數據一致性"""
    print("🔍 開始分析 JSON 和 Database 數據一致性...")

    try:
        # 1. 載入 JSON 數據
        print("\n📊 載入 JSON 模式數據...")
        json_manager = KnowledgeManager(data_dir="data")
        json_points = json_manager.knowledge_points
        json_ids = {point.id for point in json_points}

        print(f"   JSON 模式知識點數量: {len(json_ids)}")

        # 2. 載入 Database 數據
        print("\n🗄️  載入 Database 模式數據...")

        # 使用同步連接避免事件循環問題
        import psycopg2

        db_settings = DatabaseSettings()

        # 使用現有的 DATABASE_URL
        conn_str = db_settings.DATABASE_URL

        try:
            with psycopg2.connect(conn_str) as conn, conn.cursor() as cur:
                # 查詢所有未刪除的知識點
                cur.execute("""
                        SELECT id, key_point, category, created_at, is_deleted
                        FROM knowledge_points
                        WHERE is_deleted = FALSE
                        ORDER BY id
                    """)
                db_rows = cur.fetchall()

                # 轉換為字典格式便於處理
                db_points = []
                for row in db_rows:
                    db_points.append(
                        {
                            "id": row[0],
                            "key_point": row[1],
                            "category": row[2],
                            "created_at": row[3],
                            "is_deleted": row[4],
                        }
                    )
        except Exception as e:
            print(f"❌ 資料庫連接失敗: {e}")
            return None

        db_ids = {point["id"] for point in db_points}
        print(f"   Database 模式知識點數量: {len(db_ids)}")

        # 3. 分析差異
        print("\n🔍 分析數據差異...")
        only_in_json = json_ids - db_ids
        only_in_db = db_ids - json_ids
        common_ids = json_ids & db_ids

        print(f"   共同知識點: {len(common_ids)} 個")
        print(f"   僅存在於 JSON: {len(only_in_json)} 個")
        print(f"   僅存在於 Database: {len(only_in_db)} 個")

        # 4. 詳細分析多出的記錄
        if only_in_json:
            print(f"\n📄 僅存在於 JSON 的知識點 ID: {sorted(only_in_json)}")
            for missing_id in sorted(only_in_json):
                missing_point = next(p for p in json_points if p.id == missing_id)
                print(f"   ID {missing_id}: {missing_point.key_point[:60]}...")
                print(f"     分類: {missing_point.category}")

        if only_in_db:
            print(f"\n🗄️  僅存在於 Database 的知識點 ID: {sorted(only_in_db)}")
            for extra_id in sorted(only_in_db):
                extra_point = next(p for p in db_points if p["id"] == extra_id)
                print(f"   ID {extra_id}: {extra_point['key_point'][:60]}...")
                print(f"     分類: {extra_point['category']}")
                print(f"     創建時間: {extra_point['created_at']}")
                print(f"     是否刪除: {extra_point['is_deleted']}")

        # 5. 分析結果摘要
        print("\n📋 分析結果摘要:")
        if len(json_ids) == len(db_ids) and not only_in_json and not only_in_db:
            print("   ✅ 數據完全一致，無需處理")
        else:
            print("   ❌ 發現數據不一致:")
            print(f"      - 數量差異: JSON({len(json_ids)}) vs Database({len(db_ids)})")
            print(f"      - 需要同步的記錄: {len(only_in_json) + len(only_in_db)} 個")

        return {
            "json_count": len(json_ids),
            "db_count": len(db_ids),
            "only_in_json": only_in_json,
            "only_in_db": only_in_db,
            "common_count": len(common_ids),
            "db_details": {pid: p for p in db_points for pid in [p["id"]] if pid in only_in_db},
            "json_details": {pid: p for p in json_points for pid in [p.id] if pid in only_in_json},
        }

    except Exception as e:
        print(f"❌ 分析過程發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(analyze_consistency())
    if result:
        print(
            f"\n✅ 分析完成。需要處理 {len(result['only_in_db']) + len(result['only_in_json'])} 個差異記錄。"
        )
    else:
        print("\n❌ 分析失敗，請檢查錯誤訊息。")
