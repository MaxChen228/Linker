#!/usr/bin/env python3
"""
測試資料庫模式的一致性問題
"""

import asyncio
import logging
import os
from datetime import datetime

# 設置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_database_consistency():
    """測試資料庫模式的真實一致性"""
    try:
        # 設置正確的資料庫連接
        os.environ["USE_DATABASE"] = "true"
        os.environ["DATABASE_URL"] = "postgresql://chenliangyu@localhost:5432/linker_test"

        from core.database.adapter import get_knowledge_manager, get_knowledge_manager_async

        print("=== 資料庫模式一致性測試 ===")

        # 測試異步模式
        print("\n🔗 連接資料庫異步模式...")
        async_manager = await get_knowledge_manager_async(use_database=True)

        print("📊 獲取異步統計...")
        async_stats = await async_manager.get_statistics_async()

        print("異步統計結果:")
        for key, value in async_stats.items():
            print(f"  {key}: {value}")

        # 測試同步模式
        print("\n🔗 連接資料庫同步模式...")
        sync_manager = get_knowledge_manager(use_database=True)

        print("📊 獲取同步統計...")
        sync_stats = sync_manager.get_statistics()

        print("同步統計結果:")
        for key, value in sync_stats.items():
            print(f"  {key}: {value}")

        # 比較關鍵指標
        print("\n🔍 資料庫模式內部一致性檢查:")
        key_metrics = [
            "knowledge_points",
            "total_practices",
            "correct_count",
            "mistake_count",
            "avg_mastery",
            "category_distribution",
        ]

        db_consistent = True
        for metric in key_metrics:
            async_val = async_stats.get(metric, "N/A")
            sync_val = sync_stats.get(metric, "N/A")

            if async_val == sync_val:
                status = "✅ 一致"
            else:
                status = "❌ 不一致"
                db_consistent = False

            print(f"  {metric}: 異步={async_val} vs 同步={sync_val} - {status}")

        # 測試 JSON 模式進行比較
        print("\n📁 測試 JSON 模式...")
        os.environ["USE_DATABASE"] = "false"
        json_manager = get_knowledge_manager(use_database=False)
        json_stats = json_manager.get_statistics()

        print("JSON 統計結果:")
        for key, value in json_stats.items():
            print(f"  {key}: {value}")

        # 獲取詳細的知識點數據進行分析
        print("\n🔍 詳細數據分析:")

        # JSON 模式詳細分析
        json_points = json_manager.knowledge_points
        json_active = [p for p in json_points if not p.is_deleted]
        print(f"JSON 模式: 總數={len(json_points)}, 活躍={len(json_active)}")

        # 資料庫模式詳細分析
        os.environ["USE_DATABASE"] = "true"
        db_async_manager = await get_knowledge_manager_async(use_database=True)
        db_points = await db_async_manager.get_knowledge_points_async()
        db_active = [p for p in db_points if not p.is_deleted]
        print(f"資料庫模式: 總數={len(db_points)}, 活躍={len(db_active)}")

        # 分析數量差異
        count_diff = len(db_active) - len(json_active)
        if count_diff == 0:
            print("✅ 知識點數量一致")
        else:
            print(f"❌ 知識點數量不一致，差異: {count_diff}")

            # 找出額外的或缺失的知識點
            if count_diff > 0:
                print(f"資料庫中有 {count_diff} 個額外的知識點")
                # 找出資料庫中多出的知識點
                db_key_points = {p.key_point for p in db_active}
                json_key_points = {p.key_point for p in json_active}
                extra_points = db_key_points - json_key_points
                if extra_points:
                    print("額外的知識點:")
                    for i, point in enumerate(list(extra_points)[:5]):  # 只顯示前5個
                        print(f"  {i + 1}. {point}")
                        if i >= 4:
                            print(f"  ... 還有 {len(extra_points) - 5} 個")
                            break
            else:
                print(f"JSON中有 {abs(count_diff)} 個資料庫中沒有的知識點")

        # 最終報告
        print("\n📊 一致性測試結果:")
        if db_consistent and count_diff == 0:
            print("✅ 所有測試通過，資料庫模式與 JSON 模式一致！")
        elif db_consistent:
            print("⚠️ 資料庫內部一致，但與 JSON 模式存在數量差異")
        else:
            print("❌ 資料庫模式內部存在不一致問題")

        # 資源清理
        await async_manager.cleanup()
        await db_async_manager.cleanup()

        return db_consistent and count_diff == 0

    except Exception as e:
        logger.error(f"測試失敗: {e}", exc_info=True)
        return False


async def main():
    """主測試函數"""
    print(f"開始測試資料庫一致性問題 - {datetime.now()}")

    success = await test_database_consistency()

    if success:
        print("\n🎉 資料庫一致性測試成功！")
    else:
        print("\n⚠️ 發現一致性問題，需要進一步修復")

    return success


if __name__ == "__main__":
    asyncio.run(main())
