#!/usr/bin/env python3
"""
TASK-19D 分析腳本：比較 JSON 和 Database 模式的統計計算邏輯

此腳本用於分析和比較兩種模式的統計計算差異
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import DATA_DIR
from core.database.adapter import KnowledgeManagerAdapter
from core.knowledge import KnowledgeManager


async def analyze_json_statistics():
    """分析 JSON 模式的統計邏輯"""
    print("=== JSON 模式統計邏輯分析 ===")

    try:
        manager = KnowledgeManager(data_dir=str(DATA_DIR))
        stats = manager.get_statistics()

        print("JSON 統計結果:")
        print(f"  總練習次數: {stats['total_practices']}")
        print(f"  正確次數: {stats['correct_count']}")
        print(f"  知識點數量: {stats['knowledge_points']}")
        print(f"  平均掌握度: {stats.get('avg_mastery', 0):.6f}")
        print(f"  分類分布: {stats.get('category_distribution', {})}")

        # 詳細分析統計來源
        print("\n詳細分析:")
        print(f"  practice_history 長度: {len(manager.practice_history)}")

        # 分析練習歷史中的正確答案
        correct_in_history = sum(1 for p in manager.practice_history if p.get("is_correct", False))
        print(f"  practice_history 中正確答案: {correct_in_history}")

        # 分析知識點中的複習例句
        total_review_examples = 0
        correct_review_examples = 0
        for point in manager.knowledge_points:
            total_review_examples += len(point.review_examples)
            correct_review_examples += sum(1 for ex in point.review_examples if ex.is_correct)

        print(f"  知識點中複習例句總數: {total_review_examples}")
        print(f"  知識點中正確複習例句: {correct_review_examples}")

        return stats

    except Exception as e:
        print(f"JSON 分析錯誤: {e}")
        return {}


async def analyze_database_statistics():
    """分析 Database 模式的統計邏輯"""
    print("\n=== Database 模式統計邏輯分析 ===")

    try:
        adapter = KnowledgeManagerAdapter(use_database=True)

        # 異步統計
        async_stats = await adapter.get_statistics_async()
        print("Database 異步統計結果:")
        print(f"  總練習次數: {async_stats.get('total_practices', 0)}")
        print(f"  正確次數: {async_stats.get('correct_count', 0)}")
        print(f"  知識點數量: {async_stats.get('knowledge_points', 0)}")
        print(f"  平均掌握度: {async_stats.get('avg_mastery', 0):.6f}")
        print(f"  分類分布: {async_stats.get('category_distribution', {})}")

        # 同步統計（使用緩存）
        sync_stats = adapter.get_statistics()
        print("\nDatabase 同步統計結果:")
        print(f"  總練習次數: {sync_stats.get('total_practices', 0)}")
        print(f"  正確次數: {sync_stats.get('correct_count', 0)}")
        print(f"  知識點數量: {sync_stats.get('knowledge_points', 0)}")
        print(f"  平均掌握度: {sync_stats.get('avg_mastery', 0):.6f}")
        print(f"  分類分布: {sync_stats.get('category_distribution', {})}")

        # 如果有直接數據庫訪問，分析原始數據
        if adapter._repository:
            raw_stats = await adapter._repository.get_statistics()
            print("\n原始數據庫統計:")
            print(f"  {raw_stats}")

            # 手動計算練習次數
            await analyze_database_practice_counts(adapter)

        return {"async": async_stats, "sync": sync_stats}

    except Exception as e:
        print(f"Database 分析錯誤: {e}")
        return {}


async def analyze_database_practice_counts(adapter):
    """分析數據庫中的練習次數計算邏輯"""
    print("\n=== Database 練習次數詳細分析 ===")

    try:
        # 獲取連接池
        await adapter._ensure_initialized()

        if adapter.connection_pool:
            async with adapter.connection_pool.get_connection() as conn:
                # 方法1: 基於 review_examples 表計算
                review_count = await conn.fetchrow("""
                    SELECT COUNT(*) as total_reviews
                    FROM review_examples re
                    JOIN knowledge_points kp ON re.knowledge_point_id = kp.id
                    WHERE kp.is_deleted = FALSE
                """)

                # 方法2: 基於 original_errors 表計算
                error_count = await conn.fetchrow("""
                    SELECT COUNT(*) as total_errors
                    FROM original_errors oe
                    JOIN knowledge_points kp ON oe.knowledge_point_id = kp.id
                    WHERE kp.is_deleted = FALSE
                """)

                # 方法3: 基於知識點的 correct_count 和 mistake_count
                knowledge_counts = await conn.fetchrow("""
                    SELECT
                        SUM(correct_count + mistake_count) as total_from_counts,
                        SUM(correct_count) as correct_from_counts,
                        SUM(mistake_count) as mistakes_from_counts
                    FROM knowledge_points
                    WHERE is_deleted = FALSE
                """)

                print(
                    f"方法1 (review_examples): {review_count['total_reviews'] if review_count else 0}"
                )
                print(
                    f"方法2 (original_errors): {error_count['total_errors'] if error_count else 0}"
                )
                print(
                    f"方法3 (知識點計數): 總計={knowledge_counts['total_from_counts'] if knowledge_counts else 0}, "
                    + f"正確={knowledge_counts['correct_from_counts'] if knowledge_counts else 0}, "
                    + f"錯誤={knowledge_counts['mistakes_from_counts'] if knowledge_counts else 0}"
                )

                # 組合計算（所有練習記錄）
                total_practices = (review_count["total_reviews"] if review_count else 0) + (
                    error_count["total_errors"] if error_count else 0
                )
                print(f"組合計算總練習次數: {total_practices}")

    except Exception as e:
        print(f"數據庫練習次數分析錯誤: {e}")


async def compare_statistics():
    """比較兩種模式的統計結果"""
    print("\n" + "=" * 60)
    print("統計邏輯對比分析")
    print("=" * 60)

    json_stats = await analyze_json_statistics()
    db_stats = await analyze_database_statistics()

    print("\n=== 統計結果對比 ===")

    if json_stats and db_stats:
        async_stats = db_stats.get("async", {})
        sync_stats = db_stats.get("sync", {})

        print(f"{'指標':<20} {'JSON':<10} {'DB-異步':<10} {'DB-同步':<10} {'差異分析'}")
        print("-" * 80)

        # 練習次數對比
        json_practices = json_stats.get("total_practices", 0)
        async_practices = async_stats.get("total_practices", 0)
        sync_practices = sync_stats.get("total_practices", 0)

        print(
            f"{'總練習次數':<20} {json_practices:<10} {async_practices:<10} {sync_practices:<10} "
            + f"JSON vs DB-同步: {abs(json_practices - sync_practices)}"
        )

        # 正確次數對比
        json_correct = json_stats.get("correct_count", 0)
        async_correct = async_stats.get("correct_count", 0)
        sync_correct = sync_stats.get("correct_count", 0)

        print(
            f"{'正確次數':<20} {json_correct:<10} {async_correct:<10} {sync_correct:<10} "
            + f"一致性: {json_correct == async_correct == sync_correct}"
        )

        # 知識點數量對比
        json_points = json_stats.get("knowledge_points", 0)
        async_points = async_stats.get("knowledge_points", 0)
        sync_points = sync_stats.get("knowledge_points", 0)

        print(
            f"{'知識點數量':<20} {json_points:<10} {async_points:<10} {sync_points:<10} "
            + f"差異: {abs(json_points - max(async_points, sync_points))}"
        )


def identify_root_causes():
    """分析根本原因"""
    print("\n=== 根本原因分析 ===")
    print("1. 練習次數統計差異原因:")
    print("   - JSON 模式: 基於 practice_history 數組")
    print("   - Database 模式: 基於多個數據表的組合計算")
    print("   - 可能的問題: 數據來源不同，計算邏輯不一致")

    print("\n2. 統計邏輯差異:")
    print("   - JSON: len(practice_history)")
    print("   - Database: review_examples + original_errors 或 知識點計數欄位")

    print("\n3. 建議的統一標準:")
    print("   - 採用: 所有練習記錄的總和")
    print("   - 包括: original_errors (初始錯誤) + review_examples (複習例句)")
    print("   - 排除: 軟刪除的知識點相關記錄")


async def main():
    """主函數"""
    print("TASK-19D: 統計計算邏輯分析工具")
    print("=" * 60)

    await compare_statistics()
    identify_root_causes()

    print("\n=== 下一步建議 ===")
    print("1. 創建統一的統計計算函數")
    print("2. 修改兩種模式使用相同的計算邏輯")
    print("3. 驗證統計結果一致性")


if __name__ == "__main__":
    asyncio.run(main())
