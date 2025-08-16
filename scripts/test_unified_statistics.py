#!/usr/bin/env python3
"""
TASK-19D 測試腳本：驗證統一統計計算邏輯

此腳本用於測試統一後的統計邏輯是否成功解決 JSON 和 Database 模式的不一致問題
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import DATA_DIR
from core.database.adapter import KnowledgeManagerAdapter
from core.knowledge import KnowledgeManager


async def test_json_unified_statistics():
    """測試 JSON 模式的統一統計邏輯"""
    print("=== JSON 模式統一統計測試 ===")

    try:
        manager = KnowledgeManager(data_dir=str(DATA_DIR))
        stats = manager.get_statistics()

        print("JSON 統計結果 (使用統一邏輯):")
        print(f"  總練習次數: {stats['total_practices']}")
        print(f"  正確次數: {stats['correct_count']}")
        print(f"  錯誤次數: {stats['mistake_count']}")
        print(f"  準確率: {stats['accuracy']:.4f}")
        print(f"  知識點數量: {stats['knowledge_points']}")
        print(f"  平均掌握度: {stats.get('avg_mastery', 0):.6f}")
        print(f"  分類分布: {stats.get('category_distribution', {})}")
        print(f"  待複習: {stats.get('due_reviews', 0)}")

        return stats

    except Exception as e:
        print(f"JSON 統計測試錯誤: {e}")
        import traceback

        traceback.print_exc()
        return {}


async def test_database_unified_statistics():
    """測試 Database 模式的統一統計邏輯"""
    print("\n=== Database 模式統一統計測試 ===")

    try:
        adapter = KnowledgeManagerAdapter(use_database=True)

        # 測試異步統計
        async_stats = await adapter.get_statistics_async()
        print("Database 異步統計結果 (使用統一邏輯):")
        print(f"  總練習次數: {async_stats.get('total_practices', 0)}")
        print(f"  正確次數: {async_stats.get('correct_count', 0)}")
        print(f"  錯誤次數: {async_stats.get('mistake_count', 0)}")
        print(f"  準確率: {async_stats.get('accuracy', 0):.4f}")
        print(f"  知識點數量: {async_stats.get('knowledge_points', 0)}")
        print(f"  平均掌握度: {async_stats.get('avg_mastery', 0):.6f}")
        print(f"  分類分布: {async_stats.get('category_distribution', {})}")
        print(f"  待複習: {async_stats.get('due_reviews', 0)}")

        # 測試同步統計
        sync_stats = adapter.get_statistics()
        print("\nDatabase 同步統計結果 (使用統一邏輯):")
        print(f"  總練習次數: {sync_stats.get('total_practices', 0)}")
        print(f"  正確次數: {sync_stats.get('correct_count', 0)}")
        print(f"  錯誤次數: {sync_stats.get('mistake_count', 0)}")
        print(f"  準確率: {sync_stats.get('accuracy', 0):.4f}")
        print(f"  知識點數量: {sync_stats.get('knowledge_points', 0)}")
        print(f"  平均掌握度: {sync_stats.get('avg_mastery', 0):.6f}")
        print(f"  分類分布: {sync_stats.get('category_distribution', {})}")
        print(f"  待複習: {sync_stats.get('due_reviews', 0)}")

        return {"async": async_stats, "sync": sync_stats}

    except Exception as e:
        print(f"Database 統計測試錯誤: {e}")
        import traceback

        traceback.print_exc()
        return {}


async def verify_statistics_consistency():
    """驗證統計結果一致性"""
    print("\n" + "=" * 70)
    print("TASK-19D 統一統計邏輯驗證")
    print("=" * 70)

    json_stats = await test_json_unified_statistics()
    db_stats = await test_database_unified_statistics()

    if not json_stats or not db_stats:
        print("❌ 統計數據獲取失敗，無法進行一致性驗證")
        return False

    async_stats = db_stats.get("async", {})
    sync_stats = db_stats.get("sync", {})

    print("\n=== 統一邏輯一致性驗證 ===")

    # 檢查關鍵指標一致性
    consistency_report = []

    # 1. 練習次數一致性
    json_practices = json_stats.get("total_practices", 0)
    async_practices = async_stats.get("total_practices", 0)
    sync_practices = sync_stats.get("total_practices", 0)

    practices_consistent = json_practices == async_practices == sync_practices
    consistency_report.append(
        {
            "metric": "總練習次數",
            "json": json_practices,
            "db_async": async_practices,
            "db_sync": sync_practices,
            "consistent": practices_consistent,
            "diff": abs(json_practices - async_practices) + abs(json_practices - sync_practices),
        }
    )

    # 2. 正確次數一致性
    json_correct = json_stats.get("correct_count", 0)
    async_correct = async_stats.get("correct_count", 0)
    sync_correct = sync_stats.get("correct_count", 0)

    correct_consistent = json_correct == async_correct == sync_correct
    consistency_report.append(
        {
            "metric": "正確次數",
            "json": json_correct,
            "db_async": async_correct,
            "db_sync": sync_correct,
            "consistent": correct_consistent,
            "diff": abs(json_correct - async_correct) + abs(json_correct - sync_correct),
        }
    )

    # 3. 知識點數量一致性
    json_points = json_stats.get("knowledge_points", 0)
    async_points = async_stats.get("knowledge_points", 0)
    sync_points = sync_stats.get("knowledge_points", 0)

    points_consistent = json_points == async_points == sync_points
    consistency_report.append(
        {
            "metric": "知識點數量",
            "json": json_points,
            "db_async": async_points,
            "db_sync": sync_points,
            "consistent": points_consistent,
            "diff": abs(json_points - async_points) + abs(json_points - sync_points),
        }
    )

    # 4. 平均掌握度一致性
    json_mastery = json_stats.get("avg_mastery", 0)
    async_mastery = async_stats.get("avg_mastery", 0)
    sync_mastery = sync_stats.get("avg_mastery", 0)

    mastery_consistent = (
        abs(json_mastery - async_mastery) < 0.001 and abs(json_mastery - sync_mastery) < 0.001
    )
    consistency_report.append(
        {
            "metric": "平均掌握度",
            "json": json_mastery,
            "db_async": async_mastery,
            "db_sync": sync_mastery,
            "consistent": mastery_consistent,
            "diff": abs(json_mastery - async_mastery) + abs(json_mastery - sync_mastery),
        }
    )

    # 5. 分類分布一致性
    json_categories = json_stats.get("category_distribution", {})
    async_categories = async_stats.get("category_distribution", {})
    sync_categories = sync_stats.get("category_distribution", {})

    categories_consistent = json_categories == async_categories == sync_categories
    consistency_report.append(
        {
            "metric": "分類分布",
            "json": json_categories,
            "db_async": async_categories,
            "db_sync": sync_categories,
            "consistent": categories_consistent,
            "diff": 0,  # 分類是字典，難以計算數值差異
        }
    )

    # 輸出一致性報告
    print("\n📊 統計一致性報告:")
    print("-" * 80)
    print(f"{'指標':<15} {'JSON':<10} {'DB-異步':<10} {'DB-同步':<10} {'一致性':<8} {'差異'}")
    print("-" * 80)

    consistent_count = 0
    total_count = len(consistency_report)

    for report in consistency_report:
        status = "✅" if report["consistent"] else "❌"
        diff = report["diff"] if isinstance(report["diff"], (int, float)) else "N/A"

        print(
            f"{report['metric']:<15} {str(report['json']):<10} {str(report['db_async']):<10} {str(report['db_sync']):<10} {status:<8} {diff}"
        )

        if report["consistent"]:
            consistent_count += 1

    print("-" * 80)
    print(
        f"總體一致性: {consistent_count}/{total_count} ({consistent_count / total_count * 100:.1f}%)"
    )

    # 特別關注原來的問題
    practices_fixed = json_practices == async_practices == sync_practices
    print("\n🎯 TASK-19D 核心目標驗證:")
    print(f"   練習次數統計統一: {'✅ 成功' if practices_fixed else '❌ 仍有差異'}")
    if not practices_fixed:
        print(f"   - JSON: {json_practices}, DB-異步: {async_practices}, DB-同步: {sync_practices}")
        print(f"   - 差異: JSON vs DB = {abs(json_practices - async_practices)}")

    return consistent_count >= 4  # 至少80%一致性


async def test_practice_records_extraction():
    """測試練習記錄提取邏輯"""
    print("\n=== 練習記錄提取測試 ===")

    try:
        from core.statistics_utils import UnifiedStatistics

        # JSON 模式記錄提取
        manager = KnowledgeManager(data_dir=str(DATA_DIR))
        json_records = UnifiedStatistics.extract_json_practice_records(manager)

        print("JSON 模式提取記錄:")
        print(f"  總記錄數: {len(json_records)}")

        record_types = {}
        for record in json_records:
            record_types[record.record_type] = record_types.get(record.record_type, 0) + 1

        print(f"  記錄類型分布: {record_types}")

        # Database 模式記錄提取
        adapter = KnowledgeManagerAdapter(use_database=True)
        db_records = await UnifiedStatistics.extract_database_practice_records(adapter)

        print("\nDatabase 模式提取記錄:")
        print(f"  總記錄數: {len(db_records)}")

        db_record_types = {}
        for record in db_records:
            db_record_types[record.record_type] = db_record_types.get(record.record_type, 0) + 1

        print(f"  記錄類型分布: {db_record_types}")

        # 分析記錄差異
        print("\n📋 記錄差異分析:")
        print(f"  記錄數量差異: {abs(len(json_records) - len(db_records))}")

        return len(json_records), len(db_records)

    except Exception as e:
        print(f"練習記錄提取測試錯誤: {e}")
        import traceback

        traceback.print_exc()
        return 0, 0


async def main():
    """主測試函數"""
    print("TASK-19D: 統一統計計算邏輯驗證測試")
    print("=" * 70)

    # 測試練習記錄提取
    json_count, db_count = await test_practice_records_extraction()

    # 驗證統計一致性
    is_consistent = await verify_statistics_consistency()

    print("\n" + "=" * 70)
    print("TASK-19D 完成評估")
    print("=" * 70)

    if is_consistent:
        print("🎉 成功！統一統計邏輯已實現，JSON 和 Database 模式統計結果高度一致！")
        print(f"✅ 練習記錄提取: JSON({json_count}) vs DB({db_count})")
        print("✅ 統計計算邏輯已統一")
        print("✅ 兩種模式結果一致性 ≥ 80%")
    else:
        print("⚠️  統一邏輯部分成功，但仍需進一步調整...")
        print(f"📊 練習記錄: JSON({json_count}) vs DB({db_count})")
        print("🔧 建議檢查練習記錄提取邏輯的差異")

    print("\n💡 建議後續步驟:")
    print("1. 如果一致性良好，可標記 TASK-19D 為完成")
    print("2. 如果仍有差異，需要深入分析練習記錄的數據來源")
    print("3. 可考慮建立定期一致性檢查機制")


if __name__ == "__main__":
    asyncio.run(main())
