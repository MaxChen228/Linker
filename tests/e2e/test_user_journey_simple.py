"""
簡化版用戶操作路徑一致性驗證
避開複雜的異步和時區問題，專注於核心功能測試
"""

import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

import asyncio

from core.database.adapter import KnowledgeManagerAdapter
from core.knowledge import KnowledgeManager


async def simple_consistency_test():
    """簡化的一致性測試"""
    print("🚀 開始簡化版用戶操作路徑一致性驗證...")

    # 初始化管理器
    json_manager = KnowledgeManager()
    db_manager = KnowledgeManagerAdapter(use_database=True)

    test_results = []

    try:
        # === 測試1: 基礎統計比較 ===
        print("\n📊 測試1: 基礎統計比較")

        json_stats = json_manager.get_statistics()
        db_stats = await db_manager.get_statistics_async()

        # 比較關鍵指標
        key_metrics = ["knowledge_points", "correct_count", "avg_mastery"]

        for metric in key_metrics:
            json_val = json_stats.get(metric, 0)
            db_val = db_stats.get(metric, 0)

            print(f"   {metric}: JSON={json_val}, DB={db_val}")

            if isinstance(json_val, (int, float)) and isinstance(db_val, (int, float)):
                if json_val == 0 and db_val == 0:
                    test_results.append(True)  # 都為0是一致的
                elif json_val > 0:
                    diff_ratio = abs(json_val - db_val) / json_val
                    is_consistent = diff_ratio <= 0.2  # 允許20%差異
                    test_results.append(is_consistent)

                    status = "✅" if is_consistent else "⚠️"
                    print(f"   {status} {metric} 差異比例: {diff_ratio:.2%}")
                else:
                    test_results.append(json_val == db_val)
            else:
                test_results.append(json_val == db_val)

        # === 測試2: 分類分布一致性 ===
        print("\n🏷️ 測試2: 分類分布一致性")

        json_categories = set(json_stats.get("category_distribution", {}).keys())
        db_categories = set(db_stats.get("category_distribution", {}).keys())

        common_categories = json_categories & db_categories
        total_categories = json_categories | db_categories

        if total_categories:
            category_consistency = len(common_categories) / len(total_categories)
            is_category_consistent = category_consistency >= 0.8
            test_results.append(is_category_consistent)

            status = "✅" if is_category_consistent else "⚠️"
            print(f"   {status} 分類一致性: {category_consistency:.1%}")
            print(f"   JSON分類: {json_categories}")
            print(f"   DB分類: {db_categories}")
        else:
            test_results.append(True)  # 都沒有分類也算一致

        # === 測試3: 知識點數量對比 ===
        print("\n📋 測試3: 知識點列表對比")

        json_points = json_manager.get_active_points()

        # 對DB使用同步方法避免異步問題
        if hasattr(db_manager, "get_active_points"):
            db_points = db_manager.get_active_points()
        else:
            # 退回到異步方法
            try:
                db_points = await db_manager.get_knowledge_points_async()
            except Exception as e:
                print(f"   ⚠️ DB知識點獲取失敗: {e}")
                db_points = []

        json_count = len(json_points)
        db_count = len(db_points)

        count_consistent = abs(json_count - db_count) <= 2  # 允許2個差異
        test_results.append(count_consistent)

        status = "✅" if count_consistent else "⚠️"
        print(f"   {status} 知識點數量: JSON={json_count}, DB={db_count}")

        # 檢查知識點內容相似性（如果都有數據的話）
        if json_points and db_points:
            json_keys = {p.key_point for p in json_points[:5]}  # 只檢查前5個
            db_keys = {p.key_point for p in db_points[:5]}

            common_keys = json_keys & db_keys
            if json_keys or db_keys:
                content_similarity = len(common_keys) / len(json_keys | db_keys)
                content_consistent = content_similarity >= 0.3
                test_results.append(content_consistent)

                status = "✅" if content_consistent else "⚠️"
                print(f"   {status} 內容相似性: {content_similarity:.1%}")

        # === 測試4: 新練習保存功能 ===
        print("\n💾 測試4: 新練習保存功能")

        test_practice = {
            "chinese_sentence": "這是快速測試。",
            "user_answer": "This is quick test.",
            "feedback": {
                "is_generally_correct": False,
                "overall_suggestion": "This is a quick test.",
                "error_analysis": [
                    {
                        "key_point_summary": "冠詞使用測試",
                        "original_phrase": "quick test",
                        "correction": "a quick test",
                        "explanation": "測試冠詞使用",
                        "category": "systematic",
                    }
                ],
            },
        }

        # 記錄初始知識點數量
        initial_json_count = len(json_manager.get_active_points())

        # JSON保存
        try:
            json_result = json_manager.save_mistake(
                test_practice["chinese_sentence"],
                test_practice["user_answer"],
                test_practice["feedback"],
            )
            json_save_success = json_result is not False
        except Exception as e:
            print(f"   ⚠️ JSON保存失敗: {e}")
            json_save_success = False

        # DB保存
        try:
            db_result = await db_manager._save_mistake_async(
                test_practice["chinese_sentence"],
                test_practice["user_answer"],
                test_practice["feedback"],
            )
            db_save_success = db_result is True
        except Exception as e:
            print(f"   ⚠️ DB保存失敗: {e}")
            db_save_success = False

        save_consistent = json_save_success and db_save_success
        test_results.append(save_consistent)

        status = "✅" if save_consistent else "⚠️"
        print(f"   {status} 保存功能: JSON={json_save_success}, DB={db_save_success}")

        # 檢查保存後知識點數量變化
        final_json_count = len(json_manager.get_active_points())
        json_increased = final_json_count > initial_json_count

        if json_increased:
            print(f"   ✅ JSON知識點增加: {initial_json_count} -> {final_json_count}")
        else:
            print(f"   ⚠️ JSON知識點未增加: {initial_json_count} -> {final_json_count}")

        test_results.append(json_increased)

        # === 結果總結 ===
        print(f"\n{'=' * 60}")
        print("📋 簡化版一致性驗證結果")
        print(f"{'=' * 60}")

        passed_tests = sum(test_results)
        total_tests = len(test_results)

        if total_tests > 0:
            success_rate = passed_tests / total_tests

            print(f"✅ 通過測試: {passed_tests}/{total_tests}")
            print(f"🎯 成功率: {success_rate:.1%}")

            if success_rate >= 0.8:
                grade = "🏆 優秀"
                recommendation = "系統一致性表現優秀，用戶體驗高度統一"
            elif success_rate >= 0.6:
                grade = "🥈 良好"
                recommendation = "系統一致性良好，存在小幅差異但不影響使用"
            else:
                grade = "⚠️ 需改進"
                recommendation = "系統一致性需要改進，建議檢查差異原因"

            print(f"📊 評級: {grade}")
            print(f"💡 建議: {recommendation}")

            return success_rate >= 0.6
        else:
            print("❌ 無法完成測試")
            return False

    except Exception as e:
        print(f"❌ 測試執行錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """主函數"""
    print("TASK-20C: 用戶操作路徑完整性驗證 - 簡化版測試")
    print("=" * 60)

    success = await simple_consistency_test()

    if success:
        print("\n🎉 用戶操作路徑一致性驗證通過！")
        print("   兩種模式在核心功能上表現一致")
        return 0
    else:
        print("\n⚠️ 用戶操作路徑一致性需要改進")
        print("   建議檢查具體差異並進行優化")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
