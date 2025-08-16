#!/usr/bin/env python3
"""
導入 JSON 資料到資料庫並測試一致性
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


async def import_json_to_database():
    """從 JSON 導入資料到資料庫"""
    try:
        # 設置正確的資料庫連接
        os.environ["USE_DATABASE"] = "true"
        # 使用統一的測試配置
        from tests.config import TestConfig
        test_config = TestConfig()
        os.environ["DATABASE_URL"] = test_config.get_test_url()

        from core.database.adapter import get_knowledge_manager_async

        print("=== JSON 到資料庫導入測試 ===")

        # 獲取資料庫管理器
        print("🔗 連接資料庫...")
        db_manager = await get_knowledge_manager_async(use_database=True)

        # 導入 JSON 資料
        json_file = "data/knowledge.json"
        print(f"📥 從 {json_file} 導入資料...")
        success = await db_manager.import_from_json_async(json_file)

        if success:
            print("✅ JSON 資料導入成功！")
        else:
            print("❌ JSON 資料導入失敗")
            return False

        # 獲取導入後的統計
        db_stats = await db_manager.get_statistics_async()
        print("\n📊 資料庫統計 (導入後):")
        for key, value in db_stats.items():
            print(f"  {key}: {value}")

        # 比較與 JSON 模式的一致性
        print("\n📁 獲取 JSON 模式統計進行比較...")
        os.environ["USE_DATABASE"] = "false"
        from core.database.adapter import get_knowledge_manager

        json_manager = get_knowledge_manager(use_database=False)
        json_stats = json_manager.get_statistics()

        print("📊 JSON 統計:")
        for key, value in json_stats.items():
            print(f"  {key}: {value}")

        # 詳細一致性比較
        print("\n🔍 詳細一致性分析:")

        # 基本指標比較
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
            json_val = json_stats.get(metric, "N/A")
            db_val = db_stats.get(metric, "N/A")

            if json_val == db_val:
                status = "✅ 一致"
            else:
                status = "❌ 不一致"
                all_consistent = False

            print(f"  {metric}: JSON={json_val} vs DB={db_val} - {status}")

        # 詳細知識點數據比較
        print("\n🔍 知識點詳細比較:")
        json_points = json_manager.knowledge_points
        json_active = [p for p in json_points if not p.is_deleted]

        os.environ["USE_DATABASE"] = "true"  # 重置回資料庫模式
        db_points = await db_manager.get_knowledge_points_async()
        db_active = [p for p in db_points if not p.is_deleted]

        print(f"JSON 活躍知識點: {len(json_active)}")
        print(f"資料庫活躍知識點: {len(db_active)}")

        if len(json_active) == len(db_active):
            print("✅ 知識點數量一致")
        else:
            print(f"❌ 知識點數量不一致，差異: {len(db_active) - len(json_active)}")

        # 分類分析
        print("\n📂 分類分布詳細比較:")
        json_categories = json_stats.get("category_distribution", {})
        db_categories = db_stats.get("category_distribution", {})

        all_categories = set(json_categories.keys()) | set(db_categories.keys())
        category_consistent = True

        for category in sorted(all_categories):
            json_count = json_categories.get(category, 0)
            db_count = db_categories.get(category, 0)

            if json_count == db_count:
                status = "✅"
            else:
                status = "❌"
                category_consistent = False

            print(f"  {category}: JSON={json_count}, DB={db_count} {status}")

        # 最終報告
        print("\n📊 導入和一致性測試結果:")
        if all_consistent and category_consistent:
            print("✅ 完全一致！JSON 和資料庫模式返回相同結果")
            success_level = "perfect"
        elif all_consistent:
            print("⚠️ 主要指標一致，但分類分布存在差異")
            success_level = "partial"
        else:
            print("❌ 存在重要的一致性問題")
            success_level = "failed"

        # 資源清理
        await db_manager.cleanup()

        return success_level

    except Exception as e:
        logger.error(f"導入和測試失敗: {e}", exc_info=True)
        return "error"


async def main():
    """主測試函數"""
    print(f"開始 JSON 導入和一致性測試 - {datetime.now()}")

    result = await import_json_to_database()

    if result == "perfect":
        print("\n🎉 完美！導入成功且一致性測試通過")
    elif result == "partial":
        print("\n⚠️ 部分成功，需要進一步調整")
    elif result == "failed":
        print("\n❌ 一致性測試失敗，需要修復")
    else:
        print("\n💥 測試過程中出現錯誤")

    return result


if __name__ == "__main__":
    asyncio.run(main())
