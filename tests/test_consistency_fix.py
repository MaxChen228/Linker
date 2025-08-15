#!/usr/bin/env python3
"""
測試修復後的一致性問題
"""

import asyncio
import logging
from datetime import datetime

# 設置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_statistics_consistency():
    """測試統計一致性修復"""
    try:
        # 設置環境變量
        import os

        os.environ["USE_DATABASE"] = "true"
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/linker_test"

        from core.database.adapter import get_knowledge_manager, get_knowledge_manager_async

        print("=== 階段 1: 修復異步統計方法測試 ===")

        # 測試異步模式
        print("\n📊 測試資料庫異步統計...")
        async_manager = await get_knowledge_manager_async(use_database=True)
        async_stats = await async_manager.get_statistics_async()

        print("異步統計結果:")
        for key, value in async_stats.items():
            print(f"  {key}: {value}")

        # 測試同步模式（用於比較）
        print("\n📊 測試資料庫同步統計...")
        sync_manager = get_knowledge_manager(use_database=True)
        sync_stats = sync_manager.get_statistics()

        print("同步統計結果:")
        for key, value in sync_stats.items():
            print(f"  {key}: {value}")

        # 比較關鍵指標
        print("\n🔍 一致性檢查:")
        key_metrics = [
            "knowledge_points",
            "total_practices",
            "correct_count",
            "mistake_count",
            "avg_mastery",
            "category_distribution",
        ]

        all_consistent = True
        for metric in key_metrics:
            async_val = async_stats.get(metric, "N/A")
            sync_val = sync_stats.get(metric, "N/A")

            if async_val == sync_val:
                status = "✅ 一致"
            else:
                status = "❌ 不一致"
                all_consistent = False

            print(f"  {metric}: 異步={async_val} vs 同步={sync_val} - {status}")

        # 測試 JSON 模式進行三方比較
        print("\n📊 測試 JSON 模式統計...")
        os.environ["USE_DATABASE"] = "false"
        json_manager = get_knowledge_manager(use_database=False)
        json_stats = json_manager.get_statistics()

        print("JSON 統計結果:")
        for key, value in json_stats.items():
            print(f"  {key}: {value}")

        print("\n🔍 三方一致性檢查:")
        for metric in key_metrics:
            json_val = json_stats.get(metric, "N/A")
            async_val = async_stats.get(metric, "N/A")
            sync_val = sync_stats.get(metric, "N/A")

            if json_val == async_val == sync_val:
                status = "✅ 三方一致"
            elif async_val == sync_val:
                status = "⚠️ DB一致，JSON不同"
            elif json_val == sync_val:
                status = "⚠️ JSON-同步一致，異步不同"
            else:
                status = "❌ 全部不一致"

            print(f"  {metric}: JSON={json_val} | 異步={async_val} | 同步={sync_val} - {status}")

        print("\n📈 修復結果:")
        if all_consistent:
            print("✅ 異步統計方法修復成功！")
        else:
            print("❌ 異步統計方法仍有問題，需要進一步修復")

        # 資源清理
        await async_manager.cleanup()

        return all_consistent

    except Exception as e:
        logger.error(f"測試失敗: {e}", exc_info=True)
        return False


async def main():
    """主測試函數"""
    print(f"開始測試修復後的一致性問題 - {datetime.now()}")

    success = await test_statistics_consistency()

    if success:
        print("\n🎉 階段1修復驗證成功！")
    else:
        print("\n⚠️ 階段1修復仍有問題，請檢查日志")

    return success


if __name__ == "__main__":
    asyncio.run(main())
