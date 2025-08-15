"""
邊界測試專用配置和夾具
"""

import asyncio
import os
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.knowledge import KnowledgePoint, OriginalError


# 測試配置
@pytest.fixture(scope="session")
def edge_case_test_config():
    """邊界測試配置"""
    return {
        "run_slow_tests": os.getenv("RUN_SLOW_TESTS", "false").lower() == "true",
        "run_stress_tests": os.getenv("RUN_STRESS_TESTS", "false").lower() == "true",
        "run_memory_tests": os.getenv("RUN_MEMORY_TESTS", "false").lower() == "true",
        "max_test_duration": int(os.getenv("MAX_TEST_DURATION", "300")),  # 5分鐘
        "large_dataset_size": int(os.getenv("LARGE_DATASET_SIZE", "100")),  # 減少到100便於測試
    }


# 測試標記定義
pytest.mark.slow = pytest.mark.slow
pytest.mark.stress = pytest.mark.stress
pytest.mark.memory_intensive = pytest.mark.memory_intensive


# 測試數據生成器
@pytest.fixture
def create_test_knowledge_point():
    """創建測試知識點的工廠函數"""

    def _create_point(
        id: int = None,
        key_point: str = None,
        category: str = "systematic",
        mastery_level: float = 0.5,
        mistake_count: int = 0,
        correct_count: int = 1,
        created_at: str = None,
        last_seen: str = None,
        next_review: str = None,
        is_deleted: bool = False,
        **kwargs,
    ) -> KnowledgePoint:
        if id is None:
            id = random.randint(1000, 9999)

        if key_point is None:
            key_point = f"測試知識點 {id}"

        if created_at is None:
            created_at = datetime.now(timezone.utc).isoformat()

        # 創建原始錯誤對象
        original_error = OriginalError(
            chinese_sentence=f"測試中文句子 {id}",
            user_answer=f"用戶答案 {id}",
            correct_answer=f"正確答案 {id}",
            timestamp=created_at,
        )

        # 確保category是ErrorCategory枚舉
        if isinstance(category, str):
            from core.error_types import ErrorCategory

            category = ErrorCategory.from_string(category)

        point_data = {
            "id": id,
            "key_point": key_point,
            "category": category,
            "subtype": "test",
            "explanation": f"這是知識點 {id} 的解釋",
            "original_phrase": f"原始短語 {id}",
            "correction": f"修正短語 {id}",
            "original_error": original_error,
            "mastery_level": mastery_level,
            "mistake_count": mistake_count,
            "correct_count": correct_count,
            "created_at": created_at,
            "last_seen": last_seen,
            "next_review": next_review,
            "is_deleted": is_deleted,
            **kwargs,
        }

        return KnowledgePoint(**point_data)

    return _create_point


@pytest.fixture
def large_dataset_generator(create_test_knowledge_point, edge_case_test_config):
    """大數據集生成器"""

    def _generate_dataset(size: int = None) -> List[KnowledgePoint]:
        if size is None:
            size = edge_case_test_config["large_dataset_size"]

        knowledge_points = []
        categories = ["systematic", "isolated", "enhancement", "other"]

        for i in range(size):
            point = create_test_knowledge_point(
                id=i + 1,
                key_point=f"大數據測試知識點 {i + 1}",
                category=random.choice(categories),
                mastery_level=random.uniform(0, 1),
                mistake_count=random.randint(0, 10),
                correct_count=random.randint(0, 5),
            )
            knowledge_points.append(point)

        return knowledge_points

    return _generate_dataset


# 環境管理夾具
@pytest.fixture
async def clean_test_environment():
    """清理測試環境"""
    original_env = os.environ.copy()

    # 設置測試環境
    test_env = {
        "USE_DATABASE": "false",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "GEMINI_API_KEY": "test-key",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    yield

    # 恢復環境
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_json_manager():
    """模擬 JSON 模式管理器"""
    from unittest.mock import MagicMock

    manager = MagicMock()
    manager.knowledge_points = []
    manager.get_statistics.return_value = {
        "total_practices": 0,
        "correct_count": 0,
        "knowledge_points": 0,
        "mistake_count": 0,
        "avg_mastery": 0.0,
        "category_distribution": {},
        "due_reviews": 0,
    }
    manager.get_review_candidates.return_value = []
    manager.search_knowledge_points.return_value = []
    manager.get_learning_recommendations.return_value = {
        "recommendations": ["開始第一次練習，建立學習基礎"],
        "next_review_count": 0,
    }

    return manager


@pytest.fixture
async def mock_db_manager():
    """模擬 Database 模式管理器"""
    from unittest.mock import AsyncMock

    manager = AsyncMock()
    manager.get_statistics_async.return_value = {
        "total_practices": 0,
        "correct_count": 0,
        "knowledge_points": 0,
        "mistake_count": 0,
        "avg_mastery": 0.0,
        "category_distribution": {},
        "due_reviews": 0,
    }
    manager.get_knowledge_points_async.return_value = []
    manager.get_review_candidates_async.return_value = []
    manager.search_knowledge_points_async.return_value = []
    manager.get_learning_recommendations.return_value = {
        "recommendations": ["開始第一次練習，建立學習基礎"],
        "next_review_count": 0,
    }
    manager.add_knowledge_point_async.return_value = True
    manager.import_from_json_async.return_value = True
    manager.cleanup = AsyncMock()

    return manager


# 輔助函數
def assert_stats_match(actual_stats: Dict[str, Any], expected_stats: Dict[str, Any]):
    """驗證統計數據匹配"""
    for key, expected_value in expected_stats.items():
        actual_value = actual_stats.get(key, "MISSING")

        if isinstance(expected_value, float):
            # 浮點數比較使用容差
            assert abs(actual_value - expected_value) < 0.000001, (
                f"統計項目 {key} 不匹配: 期望={expected_value}, 實際={actual_value}"
            )
        else:
            assert actual_value == expected_value, (
                f"統計項目 {key} 不匹配: 期望={expected_value}, 實際={actual_value}"
            )


def assert_stats_consistent(
    stats1: Dict[str, Any], stats2: Dict[str, Any], tolerance: float = 0.000001
):
    """驗證兩個統計結果的一致性"""
    # 獲取所有鍵
    all_keys = set(stats1.keys()) | set(stats2.keys())

    for key in all_keys:
        val1 = stats1.get(key, "MISSING")
        val2 = stats2.get(key, "MISSING")

        # 處理缺失值
        if val1 == "MISSING" or val2 == "MISSING":
            assert False, f"統計項目 {key} 在某一模式中缺失: JSON={val1}, DB={val2}"

        # 處理不同類型的比較
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if isinstance(val1, float) or isinstance(val2, float):
                assert abs(val1 - val2) <= tolerance, (
                    f"統計項目 {key} 不一致: JSON={val1}, DB={val2}, 差異={abs(val1 - val2)}"
                )
            else:
                assert val1 == val2, f"統計項目 {key} 不一致: JSON={val1}, DB={val2}"
        else:
            assert val1 == val2, f"統計項目 {key} 不一致: JSON={val1}, DB={val2}"


def assert_user_session_consistent(session1: Dict[str, Any], session2: Dict[str, Any]):
    """驗證用戶會話結果的一致性"""
    for operation_name, (result1, result2) in session1.items():
        baseline1, baseline2 = session2[operation_name]

        if operation_name == "statistics":
            assert_stats_consistent(result1, baseline1)
            assert_stats_consistent(result2, baseline2)
        elif operation_name in ["review_candidates", "search"]:
            assert len(result1) == len(baseline1), f"操作 {operation_name} JSON 結果長度不一致"
            assert len(result2) == len(baseline2), f"操作 {operation_name} DB 結果長度不一致"


def recommendations_consistent(rec1: Dict[str, Any], rec2: Dict[str, Any]) -> bool:
    """檢查推薦結果是否一致"""
    return rec1.get("next_review_count") == rec2.get("next_review_count") and len(
        rec1.get("recommendations", [])
    ) == len(rec2.get("recommendations", []))


@pytest.fixture
def performance_monitor():
    """性能監控夾具"""

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.measurements = {}

        def start(self, operation: str):
            self.start_time = time.time()

        def end(self, operation: str) -> float:
            if self.start_time is None:
                return 0.0
            duration = time.time() - self.start_time
            self.measurements[operation] = duration
            self.start_time = None
            return duration

        def get_stats(self) -> Dict[str, float]:
            return self.measurements.copy()

    return PerformanceMonitor()
