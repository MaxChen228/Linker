#!/usr/bin/env python3
"""
最終一致性驗證測試
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


async def final_consistency_test():
    """最終一致性測試 - 測試相同的資料在兩種模式下的一致性"""
    try:
        print("=== 最終一致性驗證測試 ===")
        print("此測試將驗證相同的資料在 JSON 和 Database 模式下返回一致的結果")

        # 首先獲取原始 JSON 資料統計（作為基準）
        print("\n📁 步驟1: 獲取原始 JSON 資料統計...")
        os.environ["USE_DATABASE"] = "false"

        from core.database.adapter import get_knowledge_manager

        json_manager = get_knowledge_manager(use_database=False)
        json_stats = json_manager.get_statistics()
        json_points = json_manager.knowledge_points
        json_active = [p for p in json_points if not p.is_deleted]

        print("原始 JSON 統計:")
        print(f"  知識點總數: {len(json_points)}")
        print(f"  活躍知識點: {len(json_active)}")
        print(f"  總練習次數: {json_stats.get('total_practices', 0)}")
        print(f"  正確次數: {json_stats.get('correct_count', 0)}")
        print(f"  平均掌握度: {json_stats.get('avg_mastery', 0):.6f}")
        print(f"  分類分布: {json_stats.get('category_distribution', {})}")

        if len(json_active) == 0:
            print("❌ 警告：JSON 資料為空，無法進行有意義的一致性測試")
            return False

        # 步驟2: 資料庫模式測試（使用相同的原始資料）
        print("\n🔗 步驟2: 測試資料庫模式統計...")
        os.environ["USE_DATABASE"] = "true"
        # 使用統一的測試配置
        from tests.config import TestConfig
        test_config = TestConfig()
        os.environ["DATABASE_URL"] = test_config.get_test_url()

        from core.database.adapter import get_knowledge_manager_async

        # 清空資料庫並重新導入（確保一致性）
        print("🗑️ 清空並重新初始化資料庫...")

        # 清空資料表
        # 使用環境變數配置
        from urllib.parse import urlparse

        import psycopg2

        from tests.config import TestConfig
        test_config = TestConfig()
        db_url = urlparse(test_config.get_test_url())
        conn = psycopg2.connect(
            host=db_url.hostname or 'localhost',
            database=db_url.path.lstrip('/') or 'linker_test',
            user=db_url.username or 'chenliangyu',
            password=db_url.password
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM knowledge_points")
        conn.commit()
        cur.close()
        conn.close()
        print("✅ 資料庫已清空")

        # 重新導入 - 需要確保重新實例化
        from core.database.adapter import reset_knowledge_manager

        await reset_knowledge_manager()  # 重置實例

        db_manager = await get_knowledge_manager_async(use_database=True)
        success = await db_manager.import_from_json_async("data/knowledge.json")

        if not success:
            print("❌ 資料庫導入失敗")
            return False

        print("✅ 資料重新導入成功")

        # 獲取資料庫統計
        db_stats = await db_manager.get_statistics_async()
        db_points = await db_manager.get_knowledge_points_async()
        db_active = [p for p in db_points if not p.is_deleted]

        print("\n資料庫統計:")
        print(f"  知識點總數: {len(db_points)}")
        print(f"  活躍知識點: {len(db_active)}")
        print(f"  總練習次數: {db_stats.get('total_practices', 0)}")
        print(f"  正確次數: {db_stats.get('correct_count', 0)}")
        print(f"  平均掌握度: {db_stats.get('avg_mastery', 0):.6f}")
        print(f"  分類分布: {db_stats.get('category_distribution', {})}")

        # 步驟3: 詳細一致性比較
        print("\n🔍 步驟3: 詳細一致性比較...")

        # 關鍵指標比較
        key_metrics = [
            "knowledge_points",
            "total_practices",
            "correct_count",
            "mistake_count",
            "avg_mastery",
        ]

        consistent_count = 0
        total_metrics = len(key_metrics)

        for metric in key_metrics:
            json_val = json_stats.get(metric, "N/A")
            db_val = db_stats.get(metric, "N/A")

            # 對於浮點數，使用較寬鬆的比較
            if isinstance(json_val, float) and isinstance(db_val, float):
                is_consistent = abs(json_val - db_val) < 0.000001
            else:
                is_consistent = json_val == db_val

            if is_consistent:
                status = "✅ 一致"
                consistent_count += 1
            else:
                status = "❌ 不一致"

            print(f"  {metric}: JSON={json_val} vs DB={db_val} - {status}")

        # 分類分布比較
        json_categories = json_stats.get("category_distribution", {})
        db_categories = db_stats.get("category_distribution", {})

        print("\n📂 分類分布比較:")
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

        # 最終評估
        print("\n📊 最終一致性評估:")
        consistency_rate = (consistent_count / total_metrics) * 100

        print(f"核心指標一致性: {consistent_count}/{total_metrics} ({consistency_rate:.1f}%)")
        print(f"分類分布一致性: {'✅ 一致' if category_consistent else '❌ 不一致'}")

        if consistent_count == total_metrics and category_consistent:
            result = "perfect"
            print("🎉 完美一致！JSON 和 Database 模式完全一致")
        elif consistency_rate >= 80 and category_consistent:
            result = "good"
            print("✅ 良好一致性！主要指標基本一致")
        elif consistency_rate >= 60:
            result = "partial"
            print("⚠️ 部分一致，存在一些差異需要調整")
        else:
            result = "poor"
            print("❌ 一致性不足，需要重大修復")

        # 資源清理
        await db_manager.cleanup()

        return result

    except Exception as e:
        logger.error(f"最終測試失敗: {e}", exc_info=True)
        return "error"


async def main():
    """主測試函數"""
    print(f"開始最終一致性驗證測試 - {datetime.now()}")

    result = await final_consistency_test()

    if result == "perfect":
        print("\n🎉 恭喜！TASK-19B 完美完成！")
        print("JSON 與 Database 模式已實現完全一致")
    elif result == "good":
        print("\n✅ TASK-19B 基本完成！")
        print("JSON 與 Database 模式基本一致")
    else:
        print("\n⚠️ TASK-19B 需要進一步優化")

    return result


if __name__ == "__main__":
    asyncio.run(main())
