"""
大數據量場景邊界測試

測試系統在大量數據情況下的性能和一致性，確保兩種模式在高負載下的穩定性。
"""

import asyncio
import time
from datetime import datetime
from typing import List

import pytest
from core.knowledge import KnowledgePoint, OriginalError
from tests.functional.edge_cases.conftest import (
    assert_stats_consistent,
    assert_user_session_consistent,
)


class TestLargeDataScenarios:
    """大數據量場景測試套件"""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_dataset_statistics_consistency(
        self,
        large_dataset_generator,
        mock_json_manager,
        mock_db_manager,
        performance_monitor,
        edge_case_test_config,
    ):
        """測試大數據集的統計一致性"""
        # 生成大數據集
        dataset_size = edge_case_test_config["large_dataset_size"]
        large_dataset = large_dataset_generator(dataset_size)

        # 計算預期統計數據
        total_practices = sum(p.mistake_count + p.correct_count for p in large_dataset)
        correct_count = sum(p.correct_count for p in large_dataset)
        mistake_count = sum(p.mistake_count for p in large_dataset)
        avg_mastery = sum(p.mastery_level for p in large_dataset) / len(large_dataset)

        # 統計分類分布
        category_distribution = {}
        for point in large_dataset:
            category_distribution[point.category] = category_distribution.get(point.category, 0) + 1

        expected_stats = {
            "knowledge_points": dataset_size,
            "total_practices": total_practices,
            "correct_count": correct_count,
            "mistake_count": mistake_count,
            "avg_mastery": avg_mastery,
            "category_distribution": category_distribution,
            "due_reviews": 0,  # 簡化，不計算復習
        }

        # 設置mock管理器
        mock_json_manager.knowledge_points = large_dataset
        mock_json_manager.get_statistics.return_value = expected_stats

        mock_db_manager.get_knowledge_points_async.return_value = large_dataset
        mock_db_manager.get_statistics_async.return_value = expected_stats

        # 測試JSON統計性能
        performance_monitor.start("json_stats")
        json_stats = mock_json_manager.get_statistics()
        json_time = performance_monitor.end("json_stats")

        # 測試Database統計性能
        performance_monitor.start("db_stats")
        db_stats = await mock_db_manager.get_statistics_async()
        db_time = performance_monitor.end("db_stats")

        # 性能要求：大數據集統計應該在合理時間內完成
        max_time = 2.0  # 2秒
        assert json_time < max_time, f"JSON 統計耗時過長: {json_time:.2f}s > {max_time}s"
        assert db_time < max_time, f"Database 統計耗時過長: {db_time:.2f}s > {max_time}s"

        # 一致性驗證（大數據集允許更大誤差範圍）
        assert_stats_consistent(json_stats, db_stats, tolerance=0.02)  # 2% 誤差容忍

        # 驗證具體統計項目
        assert json_stats["knowledge_points"] == dataset_size
        assert db_stats["knowledge_points"] == dataset_size
        assert abs(json_stats["avg_mastery"] - expected_stats["avg_mastery"]) < 0.01
        assert abs(db_stats["avg_mastery"] - expected_stats["avg_mastery"]) < 0.01

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_concurrent_large_data_access(
        self, large_dataset_generator, mock_json_manager, mock_db_manager, edge_case_test_config
    ):
        """測試大數據集的併發訪問"""
        # 只在壓力測試模式下運行
        if not edge_case_test_config["run_stress_tests"]:
            pytest.skip("壓力測試已跳過，設置 RUN_STRESS_TESTS=true 啟用")

        # 生成大數據集
        large_dataset = large_dataset_generator()

        # 設置預期的統計結果
        expected_stats = {
            "knowledge_points": len(large_dataset),
            "total_practices": sum(p.mistake_count + p.correct_count for p in large_dataset),
            "correct_count": sum(p.correct_count for p in large_dataset),
            "mistake_count": sum(p.mistake_count for p in large_dataset),
            "avg_mastery": sum(p.mastery_level for p in large_dataset) / len(large_dataset),
            "category_distribution": {},
            "due_reviews": 0,
        }

        # 設置mock管理器
        mock_json_manager.knowledge_points = large_dataset
        mock_json_manager.get_statistics.return_value = expected_stats
        mock_json_manager.get_review_candidates.return_value = large_dataset[:5]
        mock_json_manager.search_knowledge_points.return_value = large_dataset[:10]

        mock_db_manager.get_knowledge_points_async.return_value = large_dataset
        mock_db_manager.get_statistics_async.return_value = expected_stats
        mock_db_manager.get_review_candidates_async.return_value = large_dataset[:5]
        mock_db_manager.search_knowledge_points_async.return_value = large_dataset[:10]

        # 模擬10個併發用戶同時查詢
        concurrent_users = 10
        tasks = []

        for i in range(concurrent_users):
            tasks.append(
                self._simulate_user_session(
                    user_id=i, json_manager=mock_json_manager, db_manager=mock_db_manager
                )
            )

        # 執行併發測試
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time

        # 性能要求：10個併發用戶在5秒內完成
        assert duration < 5.0, f"併發訪問耗時過長: {duration:.2f}s"

        # 驗證所有用戶都獲得了一致的結果
        baseline = results[0]
        for i, result in enumerate(results[1:], 1):
            try:
                assert_user_session_consistent(result, baseline)
            except AssertionError as e:
                pytest.fail(f"用戶 {i} 的會話結果與基準不一致: {e}")

    async def _simulate_user_session(self, user_id: int, json_manager, db_manager):
        """模擬用戶會話操作"""
        operations = {
            "statistics": (json_manager.get_statistics(), await db_manager.get_statistics_async()),
            "review_candidates": (
                json_manager.get_review_candidates(5),
                await db_manager.get_review_candidates_async(5),
            ),
            "search": (
                json_manager.search_knowledge_points("測試"),
                await db_manager.search_knowledge_points_async("測試"),
            ),
        }

        return operations

    @pytest.mark.asyncio
    async def test_large_dataset_memory_usage(
        self, large_dataset_generator, mock_json_manager, mock_db_manager, edge_case_test_config
    ):
        """測試大數據集的記憶體使用情況"""
        import psutil
        import os

        # 記錄初始記憶體使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 生成大數據集
        dataset_size = edge_case_test_config["large_dataset_size"]
        large_dataset = large_dataset_generator(dataset_size)

        # 設置管理器
        mock_json_manager.knowledge_points = large_dataset
        mock_db_manager.get_knowledge_points_async.return_value = large_dataset

        # 執行多次操作以觀察記憶體使用
        for _ in range(10):
            json_stats = mock_json_manager.get_statistics()
            db_stats = await mock_db_manager.get_statistics_async()

            # 簡單的一致性檢查
            assert json_stats["knowledge_points"] == db_stats["knowledge_points"]

        # 檢查記憶體使用增長
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # 記憶體增長應該在合理範圍內（小於100MB）
        assert memory_increase < 100, f"記憶體使用增長過多: {memory_increase:.2f}MB"

    @pytest.mark.asyncio
    async def test_large_dataset_search_performance(
        self, large_dataset_generator, mock_json_manager, mock_db_manager, performance_monitor
    ):
        """測試大數據集的搜索性能"""
        # 生成大數據集，包含各種關鍵字
        dataset_size = 100
        large_dataset = []

        for i in range(dataset_size):
            # 創建包含搜索關鍵字的知識點
            keywords = ["測試", "語法", "單詞", "句型", "語言"]
            keyword = keywords[i % len(keywords)]

            # 創建原始錯誤
            original_error = OriginalError(
                chinese_sentence=f"測試中文句子包含{keyword}",
                user_answer=f"用戶的{keyword}答案",
                correct_answer=f"正確的{keyword}答案",
                timestamp=datetime.now().isoformat(),
            )

            from core.error_types import ErrorCategory

            point = KnowledgePoint(
                id=i + 1,
                key_point=f"{keyword}知識點 {i + 1}",
                category=ErrorCategory.SYSTEMATIC,
                subtype="test",
                explanation=f"關於{keyword}的解釋",
                original_phrase=f"原始{keyword}短語",
                correction=f"修正{keyword}短語",
                original_error=original_error,
                mastery_level=0.5,
                mistake_count=1,
                correct_count=1,
            )
            large_dataset.append(point)

        # 設置搜索結果（前10個匹配的結果）
        search_results = [p for p in large_dataset if "測試" in p.key_point][:10]

        mock_json_manager.knowledge_points = large_dataset
        mock_json_manager.search_knowledge_points.return_value = search_results

        mock_db_manager.get_knowledge_points_async.return_value = large_dataset
        mock_db_manager.search_knowledge_points_async.return_value = search_results

        # 測試搜索性能
        search_terms = ["測試", "語法", "不存在的關鍵字", ""]

        for term in search_terms:
            # JSON搜索性能測試
            performance_monitor.start("json_search")
            json_results = mock_json_manager.search_knowledge_points(term)
            json_search_time = performance_monitor.end("json_search")

            # Database搜索性能測試
            performance_monitor.start("db_search")
            db_results = await mock_db_manager.search_knowledge_points_async(term)
            db_search_time = performance_monitor.end("db_search")

            # 性能要求：搜索應該在0.5秒內完成
            assert json_search_time < 0.5, f"JSON搜索'{term}'耗時過長: {json_search_time:.3f}s"
            assert db_search_time < 0.5, f"DB搜索'{term}'耗時過長: {db_search_time:.3f}s"

            # 結果一致性檢查
            assert len(json_results) == len(db_results), (
                f"搜索'{term}'結果數量不一致: JSON={len(json_results)}, DB={len(db_results)}"
            )

    @pytest.mark.asyncio
    async def test_large_dataset_category_distribution(
        self, large_dataset_generator, mock_json_manager, mock_db_manager
    ):
        """測試大數據集的分類分布一致性"""
        # 生成包含多種分類的大數據集
        dataset_size = 200
        categories = ["systematic", "isolated", "enhancement", "other"]
        large_dataset = []

        for i in range(dataset_size):
            category = categories[i % len(categories)]

            # 創建原始錯誤
            original_error = OriginalError(
                chinese_sentence=f"分類測試中文句子 {i + 1}",
                user_answer=f"用戶答案 {i + 1}",
                correct_answer=f"正確答案 {i + 1}",
                timestamp=datetime.now().isoformat(),
            )

            from core.error_types import ErrorCategory

            point = KnowledgePoint(
                id=i + 1,
                key_point=f"分類測試知識點 {i + 1}",
                category=ErrorCategory.from_string(category),
                subtype="test",
                explanation=f"分類{category}的解釋",
                original_phrase=f"原始短語 {i + 1}",
                correction=f"修正短語 {i + 1}",
                original_error=original_error,
                mastery_level=0.5,
                mistake_count=1,
                correct_count=1,
            )
            large_dataset.append(point)

        # 計算預期的分類分布
        expected_distribution = {}
        for point in large_dataset:
            expected_distribution[point.category] = expected_distribution.get(point.category, 0) + 1

        # 設置統計結果
        stats_with_distribution = {
            "knowledge_points": dataset_size,
            "total_practices": dataset_size * 2,  # mistake_count + correct_count
            "correct_count": dataset_size,
            "mistake_count": dataset_size,
            "avg_mastery": 0.5,
            "category_distribution": expected_distribution,
            "due_reviews": 0,
        }

        mock_json_manager.knowledge_points = large_dataset
        mock_json_manager.get_statistics.return_value = stats_with_distribution

        mock_db_manager.get_knowledge_points_async.return_value = large_dataset
        mock_db_manager.get_statistics_async.return_value = stats_with_distribution

        # 測試分類分布統計
        json_stats = mock_json_manager.get_statistics()
        db_stats = await mock_db_manager.get_statistics_async()

        # 驗證分類分布的一致性
        json_distribution = json_stats["category_distribution"]
        db_distribution = db_stats["category_distribution"]

        # 檢查每個分類的數量
        for category in categories:
            expected_count = dataset_size // len(categories)

            assert json_distribution[category] == expected_count, (
                f"JSON分類{category}數量不正確: 期望={expected_count}, 實際={json_distribution[category]}"
            )

            assert db_distribution[category] == expected_count, (
                f"DB分類{category}數量不正確: 期望={expected_count}, 實際={db_distribution[category]}"
            )

        # 總體一致性驗證
        assert_stats_consistent(json_stats, db_stats)
