"""
搜索過濾和統計分析一致性測試
驗證搜索、過濾和統計分析功能在兩種模式下的一致性
"""

import pytest

from core.error_types import ErrorCategory

from tests.fixtures.test_data_manager import (
    UserJourneyTestDataManager,
    get_db_manager,
    get_json_manager,
)


@pytest.mark.asyncio
async def test_comprehensive_search_experience():
    """測試完整的搜索和過濾體驗"""

    await UserJourneyTestDataManager.setup_diverse_knowledge_points()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # === 階段 1: 基本關鍵字搜索 ===
    search_terms = ["動詞", "時態", "grammar", "語法", "錯誤"]

    for term in search_terms:
        # JSON 搜索
        if hasattr(json_manager, "search_knowledge_points"):
            json_results = json_manager.search_knowledge_points(term)
        else:
            # 基本過濾搜索
            all_points = json_manager.get_active_points()
            json_results = [p for p in all_points if term.lower() in p.key_point.lower()]

        # DB 搜索
        if hasattr(db_manager, "search_knowledge_points_async"):
            db_results = await db_manager.search_knowledge_points_async(term)
        else:
            all_points = await db_manager.get_knowledge_points_async()
            db_results = [p for p in all_points if term.lower() in p.key_point.lower()]

        # 搜索結果應該有合理的一致性
        json_count = len(json_results)
        db_count = len(db_results)

        # 如果有結果，數量差異不應該太大
        if json_count > 0 or db_count > 0:
            max_count = max(json_count, db_count, 1)
            diff_ratio = abs(json_count - db_count) / max_count

            assert diff_ratio <= 0.5, (
                f"搜索詞 '{term}' 結果數量差異過大: JSON={json_count}, DB={db_count}, 差異比例={diff_ratio:.2f}"
            )

            # 如果兩邊都有結果，檢查內容相關性
            if json_results and db_results:
                json_keys = {p.key_point for p in json_results}
                db_keys = {p.key_point for p in db_results}

                common_keys = json_keys & db_keys
                union_keys = json_keys | db_keys

                if union_keys:
                    overlap_ratio = len(common_keys) / len(union_keys)
                    assert overlap_ratio >= 0.3, (
                        f"搜索詞 '{term}' 結果重疊度過低: 共同={len(common_keys)}, 總計={len(union_keys)}, 重疊度={overlap_ratio:.2f}"
                    )

    # === 階段 2: 分類過濾 ===
    for category in [
        ErrorCategory.SYSTEMATIC,
        ErrorCategory.ISOLATED,
        ErrorCategory.ENHANCEMENT,
        ErrorCategory.OTHER,
    ]:
        # JSON 分類過濾
        if hasattr(json_manager, "get_points_by_category"):
            json_category_points = json_manager.get_points_by_category(category.value)
        else:
            all_points = json_manager.get_active_points()
            json_category_points = [p for p in all_points if p.category == category]

        # DB 分類過濾
        all_db_points = await db_manager.get_knowledge_points_async()
        db_category_points = [p for p in all_db_points if p.category == category]

        # 分類過濾結果應該一致
        json_count = len(json_category_points)
        db_count = len(db_category_points)

        assert json_count == db_count, (
            f"分類 {category.value} 的知識點數量不一致: JSON={json_count}, DB={db_count}"
        )

        if json_category_points and db_category_points:
            json_ids = {p.id for p in json_category_points}
            db_ids = {p.id for p in db_category_points}
            assert json_ids == db_ids, f"分類 {category.value} 的知識點ID不一致"

    # === 階段 3: 掌握度過濾 ===
    mastery_ranges = [(0.0, 0.3, "beginner"), (0.3, 0.7, "intermediate"), (0.7, 1.0, "advanced")]

    json_all_points = json_manager.get_active_points()
    db_all_points = await db_manager.get_knowledge_points_async()

    for min_mastery, max_mastery, level_name in mastery_ranges:
        json_filtered = [p for p in json_all_points if min_mastery <= p.mastery_level < max_mastery]
        db_filtered = [p for p in db_all_points if min_mastery <= p.mastery_level < max_mastery]

        # 掌握度過濾的結果可能有小幅差異，但應該相近
        json_count = len(json_filtered)
        db_count = len(db_filtered)

        if json_count > 0 or db_count > 0:
            max_count = max(json_count, db_count, 1)
            diff_ratio = abs(json_count - db_count) / max_count

            assert diff_ratio <= 0.3, (
                f"{level_name} 掌握度範圍的知識點數量差異過大: JSON={json_count}, DB={db_count}, 差異比例={diff_ratio:.2f}"
            )

    # === 階段 4: 複合搜索條件 ===
    # 搜索系統性錯誤且掌握度低的知識點
    json_complex_results = [
        p
        for p in json_all_points
        if p.category == ErrorCategory.SYSTEMATIC and p.mastery_level < 0.5
    ]

    db_complex_results = [
        p for p in db_all_points if p.category == ErrorCategory.SYSTEMATIC and p.mastery_level < 0.5
    ]

    # 複合條件搜索結果應該一致
    json_count = len(json_complex_results)
    db_count = len(db_complex_results)

    if json_count > 0 or db_count > 0:
        max_count = max(json_count, db_count, 1)
        diff_ratio = abs(json_count - db_count) / max_count

        assert diff_ratio <= 0.2, (
            f"複合條件搜索結果差異過大: JSON={json_count}, DB={db_count}, 差異比例={diff_ratio:.2f}"
        )


@pytest.mark.asyncio
async def test_comprehensive_statistics_journey():
    """測試完整的統計分析用戶體驗"""

    await UserJourneyTestDataManager.setup_rich_statistical_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # === 階段 1: 整體學習統計 ===
    json_stats = json_manager.get_statistics()
    db_stats = await db_manager.get_statistics_async()

    # 基礎統計一致性（使用較寬鬆的容錯）
    key_metrics = ["knowledge_points", "correct_count", "avg_mastery"]

    for metric in key_metrics:
        json_val = json_stats.get(metric, 0)
        db_val = db_stats.get(metric, 0)

        if isinstance(json_val, (int, float)) and isinstance(db_val, (int, float)):
            if json_val > 0:
                diff_ratio = abs(json_val - db_val) / max(json_val, db_val)
                assert diff_ratio <= 0.2, (
                    f"{metric} 差異過大: JSON={json_val}, DB={db_val}, 差異={diff_ratio:.4f}"
                )
            else:
                assert db_val == 0 or db_val == json_val, (
                    f"{metric} 不一致: JSON={json_val}, DB={db_val}"
                )

    # 統計數據合理性檢查
    assert json_stats["knowledge_points"] > 0, "JSON 應該有知識點"
    assert db_stats["knowledge_points"] > 0, "DB 應該有知識點"
    assert 0 <= json_stats.get("avg_mastery", 0) <= 1.0, "JSON 平均掌握度應在0-1範圍"
    assert 0 <= db_stats.get("avg_mastery", 0) <= 1.0, "DB 平均掌握度應在0-1範圍"

    # === 階段 2: 分類分析 ===
    category_dist_json = json_stats.get("category_distribution", {})
    category_dist_db = db_stats.get("category_distribution", {})

    # 兩種模式應該有分類分布數據
    assert len(category_dist_json) > 0, "JSON 應該有分類分布"
    assert len(category_dist_db) > 0, "DB 應該有分類分布"

    # 檢查分類一致性
    json_categories = set(category_dist_json.keys())
    db_categories = set(category_dist_db.keys())

    common_categories = json_categories & db_categories
    assert len(common_categories) >= len(json_categories) * 0.7, (
        f"分類一致性過低: JSON={json_categories}, DB={db_categories}, 共同={common_categories}"
    )

    # 檢查共同分類的數量一致性
    for category in common_categories:
        json_count = category_dist_json[category]
        db_count = category_dist_db[category]

        if json_count > 0:
            diff_ratio = abs(json_count - db_count) / max(json_count, db_count)
            assert diff_ratio <= 0.3, (
                f"分類 {category} 數量差異過大: JSON={json_count}, DB={db_count}"
            )

    # === 階段 3: 學習推薦分析 ===
    json_recommendations = json_manager.get_learning_recommendations()
    db_recommendations = await db_manager.get_learning_recommendations()

    # 推薦應該存在且有內容
    assert len(json_recommendations.get("recommendations", [])) > 0, "JSON 應該有學習推薦"
    assert len(db_recommendations.get("recommendations", [])) > 0, "DB 應該有學習推薦"

    # 推薦內容合理性
    json_difficulty = json_recommendations.get("suggested_difficulty", 0)
    db_difficulty = db_recommendations.get("suggested_difficulty", 0)

    if json_difficulty > 0 and db_difficulty > 0:
        assert 1 <= json_difficulty <= 3, f"JSON 推薦難度不合理: {json_difficulty}"
        assert 1 <= db_difficulty <= 3, f"DB 推薦難度不合理: {db_difficulty}"

        # 推薦難度差異不應過大
        assert abs(json_difficulty - db_difficulty) <= 1, (
            f"推薦難度差異過大: JSON={json_difficulty}, DB={db_difficulty}"
        )

    # === 階段 4: 學習進度分析 ===
    json_priority_points = json_recommendations.get("priority_points", [])
    db_priority_points = db_recommendations.get("priority_points", [])

    # 優先學習點應該存在
    assert len(json_priority_points) > 0, "JSON 應該有優先學習點"
    assert len(db_priority_points) > 0, "DB 應該有優先學習點"

    # 優先學習點數量應該相近
    json_count = len(json_priority_points)
    db_count = len(db_priority_points)

    if json_count > 0 and db_count > 0:
        diff_ratio = abs(json_count - db_count) / max(json_count, db_count)
        assert diff_ratio <= 0.5, f"優先學習點數量差異過大: JSON={json_count}, DB={db_count}"

    # === 階段 5: 複習計劃分析 ===
    json_candidates = json_manager.get_review_candidates(10)
    db_candidates = await db_manager.get_review_candidates_async(10)

    # 複習候選數量應該合理
    json_candidate_count = len(json_candidates)
    db_candidate_count = len(db_candidates)

    if json_candidate_count > 0 and db_candidate_count > 0:
        diff_ratio = abs(json_candidate_count - db_candidate_count) / max(
            json_candidate_count, db_candidate_count
        )
        assert diff_ratio <= 0.4, (
            f"複習候選數量差異過大: JSON={json_candidate_count}, DB={db_candidate_count}"
        )


@pytest.mark.asyncio
async def test_search_result_ranking_consistency():
    """測試搜索結果排序的一致性"""

    await UserJourneyTestDataManager.setup_diverse_knowledge_points()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # 測試搜索排序
    search_term = "動詞"

    # JSON 搜索
    if hasattr(json_manager, "search_knowledge_points"):
        json_results = json_manager.search_knowledge_points(search_term)
    else:
        all_points = json_manager.get_active_points()
        json_results = [p for p in all_points if search_term in p.key_point]
        # 按掌握度排序（低的在前）
        json_results.sort(key=lambda x: x.mastery_level)

    # DB 搜索
    if hasattr(db_manager, "search_knowledge_points_async"):
        db_results = await db_manager.search_knowledge_points_async(search_term)
    else:
        all_points = await db_manager.get_knowledge_points_async()
        db_results = [p for p in all_points if search_term in p.key_point]
        # 按掌握度排序
        db_results.sort(key=lambda x: x.mastery_level)

    if len(json_results) > 1 and len(db_results) > 1:
        # 檢查排序一致性（至少前幾個結果應該相似）
        json_order = [p.id for p in json_results]
        db_order = [p.id for p in db_results]

        # 計算順序相關性
        common_ids = set(json_order) & set(db_order)

        if len(common_ids) >= 2:
            # 檢查前幾個結果的相對順序
            top_n = min(3, len(common_ids))
            json_top_common = [id for id in json_order if id in common_ids][:top_n]
            db_top_common = [id for id in db_order if id in common_ids][:top_n]

            # 允許部分順序差異
            order_similarity = sum(
                1
                for i, id in enumerate(json_top_common)
                if i < len(db_top_common) and id == db_top_common[i]
            )
            similarity_ratio = order_similarity / top_n

            assert similarity_ratio >= 0.5, (
                f"搜索結果順序差異過大: JSON前{top_n}={json_top_common}, DB前{top_n}={db_top_common}, 相似度={similarity_ratio:.2f}"
            )


@pytest.mark.asyncio
async def test_statistical_trend_analysis():
    """測試統計趨勢分析的一致性"""

    await UserJourneyTestDataManager.setup_rich_statistical_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # 添加一些練習歷史
    await UserJourneyTestDataManager.create_practice_history(json_manager, 10)
    await UserJourneyTestDataManager.create_practice_history(db_manager, 10)

    # 獲取更新後的統計
    json_stats_updated = json_manager.get_statistics()
    db_stats_updated = await db_manager.get_statistics_async()

    # 驗證練習歷史對統計的影響
    assert json_stats_updated["total_practices"] > 0, "JSON 應該有練習記錄"

    # 檢查練習成功率計算的一致性
    if json_stats_updated["total_practices"] > 0 and db_stats_updated.get("total_practices", 0) > 0:
        json_success_rate = (
            json_stats_updated["correct_count"] / json_stats_updated["total_practices"]
        )
        db_success_rate = (
            db_stats_updated["correct_count"] / db_stats_updated["total_practices"]
            if db_stats_updated["total_practices"] > 0
            else 0
        )

        assert 0 <= json_success_rate <= 1, f"JSON 成功率不合理: {json_success_rate}"
        assert 0 <= db_success_rate <= 1, f"DB 成功率不合理: {db_success_rate}"

        # 成功率差異不應過大
        if json_success_rate > 0 or db_success_rate > 0:
            success_rate_diff = abs(json_success_rate - db_success_rate)
            assert success_rate_diff <= 0.3, (
                f"成功率差異過大: JSON={json_success_rate:.3f}, DB={db_success_rate:.3f}"
            )

    # 檢查掌握度分布的合理性
    if json_stats_updated.get("avg_mastery", 0) > 0 and db_stats_updated.get("avg_mastery", 0) > 0:
        json_avg = json_stats_updated["avg_mastery"]
        db_avg = db_stats_updated["avg_mastery"]

        mastery_diff = abs(json_avg - db_avg)
        assert mastery_diff <= 0.2, (
            f"平均掌握度差異過大: JSON={json_avg:.3f}, DB={db_avg:.3f}, 差異={mastery_diff:.3f}"
        )
