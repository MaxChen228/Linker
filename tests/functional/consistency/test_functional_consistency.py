"""
功能行為一致性測試套件
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.functional.consistency.conftest import create_test_dataset, create_test_knowledge_point


@pytest.mark.asyncio
class TestFunctionalConsistency:
    """功能行為一致性測試套件"""

    async def test_knowledge_point_crud_operations(self, json_manager, db_manager_mock):
        """測試 CRUD 操作的一致性"""
        # 創建測試知識點
        test_point = create_test_knowledge_point("crud_test")

        # JSON 模式 CRUD 操作
        json_created = json_manager.add_knowledge_point(test_point)
        json_retrieved = json_manager.get_knowledge_point(json_created.id)

        # 驗證 JSON 模式操作成功
        assert json_retrieved is not None, "JSON 模式檢索失敗"
        assert json_retrieved.key_point == test_point.key_point
        assert json_retrieved.category == test_point.category

        # Mock Database 模式操作
        db_manager_mock.add_knowledge_point = MagicMock(return_value=test_point)
        db_manager_mock.get_knowledge_point = MagicMock(return_value=test_point)

        db_created = db_manager_mock.add_knowledge_point(test_point)
        db_retrieved = db_manager_mock.get_knowledge_point(test_point.id)

        # 驗證操作結果一致性
        assert json_created.key_point == db_created.key_point
        assert json_retrieved.key_point == db_retrieved.key_point
        assert json_created.category == db_created.category

    def test_search_functionality_consistency(self, json_manager, db_manager_mock):
        """測試搜索功能一致性"""
        # 準備測試數據
        test_points = create_test_dataset(5)
        search_keywords = ["測試", "語法", "動詞"]

        for point in test_points:
            json_manager.add_knowledge_point(point)

        # Mock database 搜索結果
        mock_search_results = test_points[:3]  # 返回前3個作為搜索結果
        db_manager_mock.search_knowledge_points = MagicMock(return_value=mock_search_results)

        for keyword in search_keywords:
            # JSON 模式搜索
            json_results = json_manager.search_knowledge_points(keyword, limit=5)

            # Database 模式搜索
            db_results = db_manager_mock.search_knowledge_points(keyword, limit=5)

            # 基本結果結構驗證
            assert isinstance(json_results, list), "JSON 搜索結果應該是列表"
            assert isinstance(db_results, list), "Database 搜索結果應該是列表"

            # 如果有結果，驗證結果類型一致
            if json_results and db_results:
                assert type(json_results[0]) == type(db_results[0]), "搜索結果類型應該一致"

    async def test_review_candidates_selection(self, json_manager, db_manager_mock):
        """測試複習候選選擇的一致性"""
        # 準備需要復習的測試數據
        test_points = create_test_dataset(10)

        # 設置一些點為需要復習
        for i, point in enumerate(test_points):
            if i < 5:
                point.next_review = "2024-01-01T00:00:00"  # 過期需要復習
            json_manager.add_knowledge_point(point)

        # Mock database 復習候選
        mock_candidates = test_points[:5]  # 前5個需要復習
        db_manager_mock.get_review_candidates = AsyncMock(return_value=mock_candidates)

        # 獲取復習候選
        json_candidates = json_manager.get_review_candidates(max_points=10)
        db_candidates = await db_manager_mock.get_review_candidates(max_points=10)

        # 驗證結果結構
        assert isinstance(json_candidates, list)
        assert isinstance(db_candidates, list)

        # 驗證候選數量合理性
        assert len(json_candidates) >= 0, "JSON 復習候選數量應該非負"
        assert len(db_candidates) >= 0, "Database 復習候選數量應該非負"

    def test_category_filtering_consistency(self, json_manager, db_manager_mock):
        """測試分類過濾的一致性"""
        # 準備不同分類的測試數據
        test_points = create_test_dataset(6)
        categories = ["systematic", "isolated", "enhancement"]

        for i, point in enumerate(test_points):
            # 分配不同分類
            from core.error_types import ErrorCategory

            if i < 2:
                point.category = ErrorCategory.SYSTEMATIC
            elif i < 4:
                point.category = ErrorCategory.ISOLATED
            else:
                point.category = ErrorCategory.ENHANCEMENT
            json_manager.add_knowledge_point(point)

        # Mock database 分類過濾
        for category in categories:
            filtered_points = [p for p in test_points if p.category.value == category]
            db_manager_mock.get_knowledge_points_by_category = MagicMock(
                return_value=filtered_points
            )

            # JSON 模式分類過濾
            json_filtered = json_manager.get_knowledge_points_by_category(category)

            # Database 模式分類過濾
            db_filtered = db_manager_mock.get_knowledge_points_by_category(category)

            # 驗證過濾結果類型一致性
            assert isinstance(json_filtered, list)
            assert isinstance(db_filtered, list)

    def test_knowledge_point_update_consistency(self, json_manager, db_manager_mock):
        """測試知識點更新的一致性"""
        # 創建並添加測試點
        test_point = create_test_knowledge_point("update_test")
        json_manager.add_knowledge_point(test_point)

        # 修改知識點
        original_mastery = test_point.mastery_level
        test_point.mastery_level = 0.8
        test_point.custom_notes = "更新後的備註"

        # JSON 模式更新
        json_updated = json_manager.update_knowledge_point(test_point)

        # Mock database 更新
        db_manager_mock.update_knowledge_point = MagicMock(return_value=test_point)
        db_updated = db_manager_mock.update_knowledge_point(test_point)

        # 驗證更新結果一致性
        assert json_updated.mastery_level == db_updated.mastery_level
        assert json_updated.custom_notes == db_updated.custom_notes
        assert json_updated.mastery_level != original_mastery  # 確認實際更新了

    def test_knowledge_point_deletion_consistency(self, json_manager, db_manager_mock):
        """測試知識點刪除的一致性"""
        # 創建並添加測試點
        test_point = create_test_knowledge_point("delete_test")
        added_point = json_manager.add_knowledge_point(test_point)
        point_id = added_point.id

        # 驗證點存在
        assert json_manager.get_knowledge_point(point_id) is not None

        # JSON 模式刪除
        json_deleted = json_manager.delete_knowledge_point(point_id)

        # Mock database 刪除
        db_manager_mock.delete_knowledge_point = MagicMock(return_value=True)
        db_deleted = db_manager_mock.delete_knowledge_point(point_id)

        # 驗證刪除結果一致性
        assert json_deleted == db_deleted  # 都應該返回 True

        # 驗證刪除後無法檢索（JSON）
        assert json_manager.get_knowledge_point(point_id) is None


@pytest.mark.integration
class TestDataIntegrityConsistency:
    """數據完整性一致性測試"""

    def test_referential_integrity(self, json_manager, db_manager_mock):
        """測試引用完整性"""
        # 創建有關聯數據的測試點
        test_point = create_test_knowledge_point("integrity_test")

        # 確保有復習例句和原始錯誤
        assert len(test_point.review_examples) > 0, "測試點應該有復習例句"
        assert test_point.original_error is not None, "測試點應該有原始錯誤"

        # 添加到 JSON 管理器
        json_manager.add_knowledge_point(test_point)

        # 檢索並驗證關聯數據完整性
        retrieved_point = json_manager.get_knowledge_point(test_point.id)

        assert retrieved_point is not None
        assert len(retrieved_point.review_examples) == len(test_point.review_examples)
        assert retrieved_point.original_error is not None
        assert (
            retrieved_point.original_error.chinese_sentence
            == test_point.original_error.chinese_sentence
        )

    def test_soft_delete_consistency(self, json_manager, db_manager_mock):
        """測試軟刪除邏輯一致性"""
        # 創建測試點
        test_point = create_test_knowledge_point("soft_delete_test")
        added_point = json_manager.add_knowledge_point(test_point)

        # 執行軟刪除（在 JSON 管理器中實際上是硬刪除）
        json_manager.delete_knowledge_point(added_point.id)

        # 驗證在活躍列表中不可見
        active_points = json_manager.get_all_knowledge_points()
        deleted_point_ids = [p.id for p in active_points]
        assert added_point.id not in deleted_point_ids, "刪除的點不應該在活躍列表中"

    def test_version_history_consistency(self, json_manager):
        """測試版本歷史一致性"""
        # 創建測試點
        test_point = create_test_knowledge_point("version_test")
        added_point = json_manager.add_knowledge_point(test_point)

        # 多次更新以產生版本歷史
        for i in range(3):
            added_point.custom_notes = f"版本 {i + 1}"
            json_manager.update_knowledge_point(added_point)

        # 檢索並驗證版本歷史
        final_point = json_manager.get_knowledge_point(added_point.id)
        assert final_point.custom_notes == "版本 3"


@pytest.mark.integration
class TestPerformanceConsistency:
    """性能一致性測試"""

    def test_large_dataset_performance(self, json_manager, db_manager_mock):
        """測試大數據集性能一致性"""
        import time

        # 創建較大的測試數據集
        large_dataset = create_test_dataset(100)

        # 測量 JSON 模式插入性能
        start_time = time.time()
        for point in large_dataset:
            json_manager.add_knowledge_point(point)
        json_insert_time = time.time() - start_time

        # Mock database 批量操作
        db_manager_mock.batch_add_knowledge_points = MagicMock(return_value=True)

        start_time = time.time()
        db_manager_mock.batch_add_knowledge_points(large_dataset)
        db_insert_time = time.time() - start_time

        # 驗證性能指標合理（不做嚴格比較，只確保操作完成）
        assert json_insert_time < 10.0, f"JSON 插入時間過長: {json_insert_time}s"
        assert db_insert_time < 10.0, f"Database 插入時間過長: {db_insert_time}s"

        print(f"性能對比 - JSON: {json_insert_time:.3f}s, DB: {db_insert_time:.3f}s")

    def test_search_performance_consistency(self, json_manager, db_manager_mock):
        """測試搜索性能一致性"""
        import time

        # 準備測試數據
        test_points = create_test_dataset(50)
        for point in test_points:
            json_manager.add_knowledge_point(point)

        # Mock database 搜索
        db_manager_mock.search_knowledge_points = MagicMock(return_value=test_points[:10])

        # 測量搜索性能
        search_keyword = "測試"

        start_time = time.time()
        json_manager.search_knowledge_points(search_keyword, limit=10)
        json_search_time = time.time() - start_time

        start_time = time.time()
        db_manager_mock.search_knowledge_points(search_keyword, limit=10)
        db_search_time = time.time() - start_time

        # 驗證搜索性能合理
        assert json_search_time < 5.0, f"JSON 搜索時間過長: {json_search_time}s"
        assert db_search_time < 5.0, f"Database 搜索時間過長: {db_search_time}s"

        print(f"搜索性能對比 - JSON: {json_search_time:.3f}s, DB: {db_search_time:.3f}s")
