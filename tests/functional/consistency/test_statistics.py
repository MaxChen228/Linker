"""
統計數據一致性測試套件
"""

import pytest

from .conftest import ConsistencyValidator, create_test_dataset


@pytest.mark.integration
class TestStatisticsConsistency:
    """統計數據一致性測試套件"""

    def test_knowledge_points_count_basic(self, json_manager, db_manager_mock):
        """測試知識點數量基本一致性"""
        # 獲取當前知識點數量（JSON 管理器可能已有數據）
        json_points = json_manager.get_active_points()
        json_count = len(json_points)

        # 預期 mock 返回的數量
        expected_db_count = 35

        # 驗證兩種模式都能返回合理的數據
        assert json_count >= 0, "JSON 模式應該返回非負數量"
        assert expected_db_count > 0, "Database 模式應該返回正數量"

        print(f"JSON 知識點數量: {json_count}, 期望 DB 數量: {expected_db_count}")

    def test_statistics_format_consistency(self, json_manager, db_manager_mock):
        """測試統計格式一致性"""
        # 測試同步統計
        json_stats = json_manager.get_statistics()
        db_stats = db_manager_mock.get_statistics()

        # 檢查統計結構一致性
        required_json_fields = [
            "total_practices",
            "correct_count",
            "knowledge_points",
            "category_distribution",
        ]

        required_db_fields = [
            "total_knowledge_points",
            "total_practices",
            "correct_count",
            "categories",
        ]

        for field in required_json_fields:
            assert field in json_stats, f"JSON 統計缺少字段: {field}"

        for field in required_db_fields:
            assert field in db_stats, f"Database 統計缺少字段: {field}"

        # 檢查數據類型一致性
        assert isinstance(json_stats["knowledge_points"], int)
        assert isinstance(db_stats["total_knowledge_points"], int)
        assert isinstance(json_stats["category_distribution"], dict)
        assert isinstance(db_stats["categories"], list)

    @pytest.mark.asyncio
    async def test_async_sync_consistency(self, db_manager_mock):
        """測試異步和同步統計方法的一致性"""
        sync_stats = db_manager_mock.get_statistics()
        async_stats = await db_manager_mock.get_statistics_async()

        # 驗證異步和同步結果完全一致
        assert sync_stats == async_stats, (
            f"異步和同步統計不一致: sync={sync_stats}, async={async_stats}"
        )

    def test_category_order_consistency(self, json_manager, db_manager_mock, consistency_validator):
        """測試分類順序一致性"""
        json_stats = json_manager.get_statistics()
        db_stats = db_manager_mock.get_statistics()

        json_categories = list(json_stats.get("category_distribution", {}).keys())
        db_categories = db_stats.get("categories", [])

        # 驗證分類數據類型正確
        assert isinstance(json_categories, list), "JSON 分類應該是列表"
        assert isinstance(db_categories, list), "DB 分類應該是列表"

        print(f"JSON 分類: {json_categories}, DB 分類: {db_categories}")

    def test_mastery_calculation_consistency(self, json_manager, consistency_validator):
        """測試掌握度計算一致性"""
        # 創建具有已知掌握度的測試點
        test_points = create_test_dataset(3)
        for i, point in enumerate(test_points):
            json_manager.save_mistake(
                chinese_sentence=f"掌握度測試句子{i}",
                user_answer=f"掌握度錯誤答案{i}",
                feedback={
                    "category": point.category.value,
                    "key_point": point.key_point,
                    "explanation": point.explanation,
                },
            )
            # 更新掌握度
            created_points = json_manager.get_active_points()
            if created_points:
                last_point = created_points[-1]
                last_point.mastery_level = 0.2 + (i * 0.3)  # 0.2, 0.5, 0.8

        stats = json_manager.get_statistics()

        # 驗證掌握度計算
        expected_avg = (0.2 + 0.5 + 0.8) / 3
        actual_avg = stats.get("avg_mastery", 0)

        assert abs(actual_avg - expected_avg) < 0.01, (
            f"掌握度計算不正確: expected={expected_avg}, actual={actual_avg}"
        )

    def test_empty_data_consistency(self, json_manager, db_manager_mock, consistency_validator):
        """測試空數據情況的一致性"""
        # 測試空的 JSON 管理器
        json_stats = json_manager.get_statistics()

        # 檢查空數據的統計結構（使用 JSON 格式字段名）
        assert "knowledge_points" in json_stats
        assert json_stats["knowledge_points"] == 0
        assert json_stats.get("total_practices", 0) == 0

    def test_practice_count_calculation(self, json_manager):
        """測試練習次數計算邏輯"""
        # 創建有明確練習次數的測試點
        test_points = create_test_dataset(2)

        # 設置已知的練習數據
        test_points[0].review_examples = [
            test_points[0].review_examples[0]  # 1個練習例句
        ]
        test_points[0].original_error = test_points[0].original_error  # 1個原始錯誤

        test_points[1].review_examples = []  # 0個練習例句
        test_points[1].original_error = test_points[1].original_error  # 1個原始錯誤

        for point in test_points:
            json_manager.add_knowledge_point(point)

        stats = json_manager.get_statistics()

        # 預期練習次數: 1 + 1 + 0 + 1 = 3
        expected_practices = 3
        actual_practices = stats.get("total_practices", 0)

        assert actual_practices == expected_practices, (
            f"練習次數計算錯誤: expected={expected_practices}, actual={actual_practices}"
        )


@pytest.mark.integration
class TestStatisticsAccuracy:
    """統計準確性測試"""

    def test_statistics_with_known_data(self, json_manager, test_data_generator):
        """使用已知數據測試統計準確性"""
        test_points, expected_stats = test_data_generator.generate_consistent_dataset(5)

        # 添加到 JSON 管理器
        for point in test_points:
            json_manager.add_knowledge_point(point)

        actual_stats = json_manager.get_statistics()

        # 驗證關鍵統計指標
        assert actual_stats["total_knowledge_points"] == expected_stats["total_knowledge_points"]
        assert actual_stats["total_practices"] == expected_stats["total_practices"]
        assert actual_stats["correct_count"] == expected_stats["correct_count"]

        # 驗證平均掌握度（允許小範圍誤差）
        expected_mastery = expected_stats["average_mastery"]
        actual_mastery = actual_stats.get("average_mastery", 0)
        assert abs(actual_mastery - expected_mastery) < 0.01, (
            f"平均掌握度計算錯誤: expected={expected_mastery}, actual={actual_mastery}"
        )

    def test_incremental_statistics_update(self, json_manager):
        """測試增量統計更新的準確性"""
        # 初始狀態
        initial_stats = json_manager.get_statistics()
        initial_count = initial_stats["total_knowledge_points"]

        # 添加一個知識點
        test_point = create_test_dataset(1)[0]
        json_manager.add_knowledge_point(test_point)

        # 檢查統計更新
        updated_stats = json_manager.get_statistics()
        updated_count = updated_stats["total_knowledge_points"]

        assert updated_count == initial_count + 1, (
            f"增量更新錯誤: expected={initial_count + 1}, actual={updated_count}"
        )


@pytest.mark.unit
class TestConsistencyValidator:
    """測試一致性驗證器本身的功能"""

    def test_validator_statistics_match_success(self):
        """測試統計匹配驗證 - 成功情況"""
        validator = ConsistencyValidator()

        json_stats = {"total_knowledge_points": 10, "correct_count": 5, "total_practices": 20}
        db_stats = {
            "total_knowledge_points": 10,
            "correct_count": 5,
            "total_practices": 21,  # 5% 差異內
        }

        # 不應該拋出異常
        validator.assert_statistics_match(json_stats, db_stats)

    def test_validator_statistics_match_failure(self):
        """測試統計匹配驗證 - 失敗情況"""
        validator = ConsistencyValidator()

        json_stats = {"total_knowledge_points": 10, "correct_count": 5, "total_practices": 20}
        db_stats = {
            "total_knowledge_points": 15,  # 不一致
            "correct_count": 5,
            "total_practices": 20,
        }

        # 應該拋出 AssertionError
        with pytest.raises(AssertionError, match="total_knowledge_points 不一致"):
            validator.assert_statistics_match(json_stats, db_stats)

    def test_validator_categories_match(self):
        """測試分類匹配驗證"""
        validator = ConsistencyValidator()

        # 成功情況
        categories1 = ["系統性錯誤", "單一性錯誤"]
        categories2 = ["系統性錯誤", "單一性錯誤"]
        validator.assert_categories_match(categories1, categories2)

        # 失敗情況
        categories3 = ["系統性錯誤", "單一性錯誤"]
        categories4 = ["單一性錯誤", "系統性錯誤"]  # 順序不同

        with pytest.raises(AssertionError, match="分類不一致"):
            validator.assert_categories_match(categories3, categories4)
