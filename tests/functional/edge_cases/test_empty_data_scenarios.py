"""
空數據場景邊界測試

測試系統在完全空白或最小數據情況下的行為，確保兩種模式在極端情況下的一致性。
"""

import pytest
from tests.functional.edge_cases.conftest import (
    assert_stats_match,
    assert_stats_consistent,
    recommendations_consistent,
)


class TestEmptyDataScenarios:
    """空數據場景測試套件"""

    @pytest.mark.asyncio
    async def test_empty_system_statistics(
        self, mock_json_manager, mock_db_manager, clean_test_environment
    ):
        """測試完全空白系統的統計行為"""
        # 設置空系統狀態
        mock_json_manager.knowledge_points = []
        mock_json_manager.get_statistics.return_value = {
            "total_practices": 0,
            "correct_count": 0,
            "knowledge_points": 0,
            "mistake_count": 0,
            "avg_mastery": 0.0,
            "category_distribution": {},
            "due_reviews": 0,
        }

        mock_db_manager.get_statistics_async.return_value = {
            "total_practices": 0,
            "correct_count": 0,
            "knowledge_points": 0,
            "mistake_count": 0,
            "avg_mastery": 0.0,
            "category_distribution": {},
            "due_reviews": 0,
        }

        # 測試空系統統計
        json_stats = mock_json_manager.get_statistics()
        db_stats = await mock_db_manager.get_statistics_async()

        expected_empty_stats = {
            "total_practices": 0,
            "correct_count": 0,
            "knowledge_points": 0,
            "mistake_count": 0,
            "avg_mastery": 0.0,
            "category_distribution": {},
            "due_reviews": 0,
        }

        # 驗證每種模式都符合空系統期望
        assert_stats_match(json_stats, expected_empty_stats)
        assert_stats_match(db_stats, expected_empty_stats)

        # 驗證兩種模式一致性
        assert_stats_consistent(json_stats, db_stats)

    @pytest.mark.asyncio
    async def test_empty_system_operations(
        self, mock_json_manager, mock_db_manager, clean_test_environment
    ):
        """測試空系統下的各種操作"""
        # 設置空系統狀態
        mock_json_manager.knowledge_points = []
        mock_json_manager.get_review_candidates.return_value = []
        mock_json_manager.search_knowledge_points.return_value = []
        mock_json_manager.get_learning_recommendations.return_value = {
            "recommendations": ["開始第一次練習，建立學習基礎"],
            "next_review_count": 0,
        }

        mock_db_manager.get_knowledge_points_async.return_value = []
        mock_db_manager.get_review_candidates_async.return_value = []
        mock_db_manager.search_knowledge_points_async.return_value = []
        mock_db_manager.get_learning_recommendations.return_value = {
            "recommendations": ["開始第一次練習，建立學習基礎"],
            "next_review_count": 0,
        }

        # 測試複習候選選擇
        json_candidates = mock_json_manager.get_review_candidates()
        db_candidates = await mock_db_manager.get_review_candidates_async()

        assert len(json_candidates) == 0
        assert len(db_candidates) == 0

        # 測試搜索
        json_search = mock_json_manager.search_knowledge_points("test")
        db_search = await mock_db_manager.search_knowledge_points_async("test")

        assert len(json_search) == 0
        assert len(db_search) == 0

        # 測試學習推薦
        json_recommendations = mock_json_manager.get_learning_recommendations()
        db_recommendations = await mock_db_manager.get_learning_recommendations()

        # 空系統應該給出基本的開始建議
        assert json_recommendations["recommendations"] == ["開始第一次練習，建立學習基礎"]
        assert json_recommendations["next_review_count"] == 0
        assert recommendations_consistent(json_recommendations, db_recommendations)

    @pytest.mark.asyncio
    async def test_single_knowledge_point_system(
        self,
        create_test_knowledge_point,
        mock_json_manager,
        mock_db_manager,
        clean_test_environment,
    ):
        """測試只有單一知識點的極簡系統"""
        # 創建單一測試知識點
        single_point = create_test_knowledge_point(
            id=1,
            key_point="單一測試知識點",
            category="systematic",
            mastery_level=0.5,
            mistake_count=1,
            correct_count=1,
        )

        # 設置單一知識點狀態
        mock_json_manager.knowledge_points = [single_point]
        mock_json_manager.get_statistics.return_value = {
            "total_practices": 2,  # mistake_count + correct_count
            "correct_count": 1,
            "knowledge_points": 1,
            "mistake_count": 1,
            "avg_mastery": 0.5,
            "category_distribution": {"systematic": 1},
            "due_reviews": 0,
        }

        mock_db_manager.get_knowledge_points_async.return_value = [single_point]
        mock_db_manager.get_statistics_async.return_value = {
            "total_practices": 2,
            "correct_count": 1,
            "knowledge_points": 1,
            "mistake_count": 1,
            "avg_mastery": 0.5,
            "category_distribution": {"systematic": 1},
            "due_reviews": 0,
        }

        # 測試單一知識點統計
        json_stats = mock_json_manager.get_statistics()
        db_stats = await mock_db_manager.get_statistics_async()

        expected_single_stats = {
            "total_practices": 2,
            "correct_count": 1,
            "knowledge_points": 1,
            "mistake_count": 1,
            "avg_mastery": 0.5,
            "category_distribution": {"systematic": 1},
            "due_reviews": 0,
        }

        # 驗證統計準確性
        assert_stats_match(json_stats, expected_single_stats)
        assert_stats_match(db_stats, expected_single_stats)

        # 驗證一致性
        assert_stats_consistent(json_stats, db_stats)

    @pytest.mark.asyncio
    async def test_zero_mastery_knowledge_points(
        self,
        create_test_knowledge_point,
        mock_json_manager,
        mock_db_manager,
        clean_test_environment,
    ):
        """測試掌握度為零的知識點系統"""
        # 創建零掌握度知識點
        zero_mastery_points = [
            create_test_knowledge_point(
                id=i + 1,
                key_point=f"零掌握度知識點 {i + 1}",
                mastery_level=0.0,
                mistake_count=5,  # 多次錯誤
                correct_count=0,  # 從未正確
            )
            for i in range(3)
        ]

        mock_json_manager.knowledge_points = zero_mastery_points
        mock_json_manager.get_statistics.return_value = {
            "total_practices": 15,  # 3 * 5 mistakes
            "correct_count": 0,
            "knowledge_points": 3,
            "mistake_count": 15,
            "avg_mastery": 0.0,
            "category_distribution": {"systematic": 3},
            "due_reviews": 3,  # 所有都需要復習
        }

        mock_db_manager.get_knowledge_points_async.return_value = zero_mastery_points
        mock_db_manager.get_statistics_async.return_value = {
            "total_practices": 15,
            "correct_count": 0,
            "knowledge_points": 3,
            "mistake_count": 15,
            "avg_mastery": 0.0,
            "category_distribution": {"systematic": 3},
            "due_reviews": 3,
        }

        # 測試零掌握度統計
        json_stats = mock_json_manager.get_statistics()
        db_stats = await mock_db_manager.get_statistics_async()

        # 驗證一致性
        assert_stats_consistent(json_stats, db_stats)

        # 特別驗證零掌握度場景
        assert json_stats["avg_mastery"] == 0.0
        assert db_stats["avg_mastery"] == 0.0
        assert json_stats["correct_count"] == 0
        assert db_stats["correct_count"] == 0

    @pytest.mark.asyncio
    async def test_perfect_mastery_knowledge_points(
        self,
        create_test_knowledge_point,
        mock_json_manager,
        mock_db_manager,
        clean_test_environment,
    ):
        """測試完美掌握度的知識點系統"""
        # 創建完美掌握度知識點
        perfect_mastery_points = [
            create_test_knowledge_point(
                id=i + 1,
                key_point=f"完美掌握知識點 {i + 1}",
                mastery_level=1.0,
                mistake_count=0,  # 從未錯誤
                correct_count=10,  # 多次正確
            )
            for i in range(2)
        ]

        mock_json_manager.knowledge_points = perfect_mastery_points
        mock_json_manager.get_statistics.return_value = {
            "total_practices": 20,  # 2 * 10 correct
            "correct_count": 20,
            "knowledge_points": 2,
            "mistake_count": 0,
            "avg_mastery": 1.0,
            "category_distribution": {"systematic": 2},
            "due_reviews": 0,  # 完美掌握不需要復習
        }

        mock_db_manager.get_knowledge_points_async.return_value = perfect_mastery_points
        mock_db_manager.get_statistics_async.return_value = {
            "total_practices": 20,
            "correct_count": 20,
            "knowledge_points": 2,
            "mistake_count": 0,
            "avg_mastery": 1.0,
            "category_distribution": {"systematic": 2},
            "due_reviews": 0,
        }

        # 測試完美掌握統計
        json_stats = mock_json_manager.get_statistics()
        db_stats = await mock_db_manager.get_statistics_async()

        # 驗證一致性
        assert_stats_consistent(json_stats, db_stats)

        # 特別驗證完美掌握場景
        assert json_stats["avg_mastery"] == 1.0
        assert db_stats["avg_mastery"] == 1.0
        assert json_stats["mistake_count"] == 0
        assert db_stats["mistake_count"] == 0
        assert json_stats["due_reviews"] == 0
        assert db_stats["due_reviews"] == 0

    @pytest.mark.asyncio
    async def test_empty_category_distribution(
        self, mock_json_manager, mock_db_manager, clean_test_environment
    ):
        """測試空分類分布的處理"""
        # 設置空分類分布
        mock_json_manager.get_statistics.return_value = {
            "total_practices": 0,
            "correct_count": 0,
            "knowledge_points": 0,
            "mistake_count": 0,
            "avg_mastery": 0.0,
            "category_distribution": {},  # 空分布
            "due_reviews": 0,
        }

        mock_db_manager.get_statistics_async.return_value = {
            "total_practices": 0,
            "correct_count": 0,
            "knowledge_points": 0,
            "mistake_count": 0,
            "avg_mastery": 0.0,
            "category_distribution": {},  # 空分布
            "due_reviews": 0,
        }

        # 測試空分類分布統計
        json_stats = mock_json_manager.get_statistics()
        db_stats = await mock_db_manager.get_statistics_async()

        # 驗證空分類分布處理
        assert isinstance(json_stats["category_distribution"], dict)
        assert isinstance(db_stats["category_distribution"], dict)
        assert len(json_stats["category_distribution"]) == 0
        assert len(db_stats["category_distribution"]) == 0

        # 驗證一致性
        assert_stats_consistent(json_stats, db_stats)


@pytest.mark.asyncio
async def test_edge_case_empty_search_and_filter(
    mock_json_manager, mock_db_manager, clean_test_environment
):
    """測試空系統的搜索和過濾操作"""
    # 設置空系統
    mock_json_manager.search_knowledge_points.return_value = []
    mock_db_manager.search_knowledge_points_async.return_value = []

    # 測試各種搜索條件
    search_terms = ["", "不存在的關鍵字", "~!@#$%^&*()", "      ", "\n\t"]

    for term in search_terms:
        json_results = mock_json_manager.search_knowledge_points(term)
        db_results = await mock_db_manager.search_knowledge_points_async(term)

        assert len(json_results) == 0, f"空系統搜索 '{term}' 應返回空結果"
        assert len(db_results) == 0, f"空系統搜索 '{term}' 應返回空結果"
        assert len(json_results) == len(db_results), "JSON和DB搜索結果數量應一致"
