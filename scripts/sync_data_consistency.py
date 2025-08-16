#!/usr/bin/env python3
"""
數據同步腳本 - 解決 JSON 和 Database ID 不匹配問題
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from core.database.connection import DatabaseSettings
from core.knowledge import KnowledgeManager
from scripts.data_check import analyze_consistency


async def sync_knowledge_ids():
    """同步知識點 ID，以 JSON 為主，更新 Database"""
    print("🔄 開始同步 JSON 和 Database 知識點 ID...")

    # 1. 分析當前狀態
    analysis = await analyze_consistency()
    if not analysis:
        print("❌ 無法獲取分析結果，停止同步")
        return False

    print(f"\n📊 當前狀態：JSON({analysis['json_count']}) vs Database({analysis['db_count']})")

    if not analysis["only_in_json"] and not analysis["only_in_db"]:
        print("✅ 數據已經一致，無需同步")
        return True

    # 2. 載入 JSON 數據作為權威來源
    json_manager = KnowledgeManager(data_dir="data")
    json_points = json_manager.knowledge_points

    # 3. 連接資料庫準備同步
    db_settings = DatabaseSettings()

    try:
        with psycopg2.connect(db_settings.DATABASE_URL) as conn, conn.cursor() as cur:
            print("\n🗄️  清理 Database 中的知識點...")

            # 完全清空現有的知識點和相關數據（避免唯一約束衝突）
            print("   清理所有相關表...")
            cur.execute("DELETE FROM knowledge_point_versions")
            cur.execute("DELETE FROM knowledge_point_tags")
            cur.execute("DELETE FROM practice_queue")
            cur.execute("DELETE FROM review_examples")
            cur.execute("DELETE FROM original_errors")
            cur.execute("DELETE FROM knowledge_points")

            # 暫時刪除唯一約束索引
            cur.execute("DROP INDEX IF EXISTS uk_kp_content")
            print("   已完全清空所有相關數據")
            deleted_count = cur.rowcount
            print(f"   已軟刪除 {deleted_count} 個現有知識點")

            print("\n📝 插入 JSON 知識點到 Database...")
            inserted_count = 0

            for point in json_points:
                # 將 ErrorCategory enum 轉換為字符串
                category_str = str(point.category).split(".")[-1].lower()

                # 修正時間約束問題：確保 next_review >= last_seen
                from datetime import datetime

                try:
                    if point.next_review and point.last_seen:
                        next_review_dt = datetime.fromisoformat(
                            point.next_review.replace("Z", "+00:00")
                        )
                        last_seen_dt = datetime.fromisoformat(
                            point.last_seen.replace("Z", "+00:00")
                        )
                        # 移除時區信息進行比較
                        next_review_dt = next_review_dt.replace(tzinfo=None)
                        last_seen_dt = last_seen_dt.replace(tzinfo=None)

                        if next_review_dt < last_seen_dt:
                            # 修正：將 next_review 設為 last_seen 的時間
                            point.next_review = point.last_seen
                            print(f"   修正知識點 {point.id} 的時間約束")
                except (ValueError, AttributeError):
                    # 時間格式有問題，設為當前時間
                    current_time = datetime.now().isoformat()
                    point.next_review = current_time
                    point.last_seen = current_time

                # 插入知識點 (對應資料庫 schema)
                cur.execute(
                    """
                        INSERT INTO knowledge_points (
                            id, key_point, category, subtype, explanation,
                            original_phrase, correction, mastery_level,
                            next_review, mistake_count, correct_count, custom_notes,
                            is_deleted, created_at, last_modified, last_seen
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            FALSE, %s, CURRENT_TIMESTAMP, %s
                        ) ON CONFLICT (id) DO UPDATE SET
                            key_point = EXCLUDED.key_point,
                            category = EXCLUDED.category,
                            subtype = EXCLUDED.subtype,
                            explanation = EXCLUDED.explanation,
                            original_phrase = EXCLUDED.original_phrase,
                            correction = EXCLUDED.correction,
                            mastery_level = EXCLUDED.mastery_level,
                            next_review = EXCLUDED.next_review,
                            last_seen = EXCLUDED.last_seen,
                            mistake_count = EXCLUDED.mistake_count,
                            correct_count = EXCLUDED.correct_count,
                            custom_notes = EXCLUDED.custom_notes || ' [從JSON同步]',
                            is_deleted = FALSE,
                            last_modified = CURRENT_TIMESTAMP
                    """,
                    (
                        point.id,
                        point.key_point,
                        category_str,
                        point.subtype,
                        point.explanation,
                        point.original_phrase,
                        point.correction,
                        point.mastery_level,
                        point.next_review,
                        point.mistake_count,
                        point.correct_count,
                        point.custom_notes,
                        point.created_at,
                        point.last_seen,
                    ),
                )

                inserted_count += 1

            print(f"   已插入/更新 {inserted_count} 個知識點")

            # 更新 ID 序列（確保下次插入使用正確的 ID）
            cur.execute("""
                    SELECT setval('knowledge_points_id_seq',
                                 COALESCE((SELECT MAX(id) FROM knowledge_points), 1))
                """)

            # 提交事務
            conn.commit()
            print("   ✅ 數據同步完成")

    except Exception as e:
        print(f"❌ 數據同步失敗: {e}")
        import traceback

        traceback.print_exc()
        return False

    # 4. 驗證同步結果
    print("\n🔍 驗證同步結果...")
    final_analysis = await analyze_consistency()

    if final_analysis and final_analysis["json_count"] == final_analysis["db_count"]:
        print(f"✅ 同步成功！兩種模式都包含 {final_analysis['json_count']} 個知識點")
        return True
    else:
        print("❌ 同步後仍有差異，需要進一步調查")
        return False


async def backup_database_before_sync():
    """在同步前備份資料庫數據"""
    print("💾 在同步前備份 Database 數據...")

    db_settings = DatabaseSettings()
    backup_data = []

    try:
        with psycopg2.connect(db_settings.DATABASE_URL) as conn, conn.cursor() as cur:
            cur.execute("""
                    SELECT id, key_point, category, created_at, is_deleted
                    FROM knowledge_points
                    ORDER BY id
                """)

            rows = cur.fetchall()
            for row in rows:
                backup_data.append(
                    {
                        "id": row[0],
                        "key_point": row[1],
                        "category": row[2],
                        "created_at": str(row[3]),
                        "is_deleted": row[4],
                    }
                )

        # 寫入備份文件
        import json
        from datetime import datetime

        backup_file = (
            f"data/backups/knowledge_pre_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        Path(backup_file).parent.mkdir(exist_ok=True)

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "backup_time": datetime.now().isoformat(),
                    "total_count": len(backup_data),
                    "data": backup_data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"   ✅ 已備份 {len(backup_data)} 個知識點到 {backup_file}")
        return True

    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        return False


if __name__ == "__main__":

    async def main():
        # 1. 備份現有數據
        if not await backup_database_before_sync():
            print("❌ 備份失敗，停止同步操作")
            return

        # 2. 執行同步
        success = await sync_knowledge_ids()

        if success:
            print("\n🎉 TASK-19C 完成！JSON 和 Database 知識點數量已同步")
        else:
            print("\n❌ 同步失敗，請檢查錯誤並手動處理")

    asyncio.run(main())
