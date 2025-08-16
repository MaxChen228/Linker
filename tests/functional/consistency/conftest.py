"""
一致性測試配置和共用夾具
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from core.error_types import ErrorCategory
from core.knowledge import KnowledgeManager, KnowledgePoint, OriginalError, ReviewExample


@pytest.fixture
def json_manager(temp_data_dir):
    """JSON 模式管理器"""
    return KnowledgeManager(data_dir=str(temp_data_dir))


@pytest.fixture
async def db_manager_mock():
    """Mock Database 模式管理器（用於初始測試）"""
    manager = MagicMock()
    manager.use_database = True

    # Mock 統計方法
    mock_stats = {
        "total_knowledge_points": 35,
        "total_practices": 30,
        "correct_count": 25,
        "average_mastery": 0.75,
        "categories": ["系統性錯誤", "單一性錯誤", "可以更好", "其他錯誤"],
        "due_reviews": 5,
    }

    async def mock_get_statistics_async():
        return mock_stats.copy()

    def mock_get_statistics():
        return mock_stats.copy()

    manager.get_statistics_async = mock_get_statistics_async
    manager.get_statistics = mock_get_statistics

    # Mock 知識點相關方法
    mock_points = [create_test_knowledge_point(f"test_{i}") for i in range(35)]

    async def mock_get_all_knowledge_points():
        return mock_points.copy()

    manager.get_all_knowledge_points = mock_get_all_knowledge_points

    # Mock 其他方法
    async def mock_cleanup():
        pass

    manager.cleanup = mock_cleanup

    yield manager


@pytest.fixture
def consistency_validator():
    """一致性驗證器"""
    return ConsistencyValidator()


class ConsistencyValidator:
    """一致性驗證工具類"""

    def __init__(self, tolerance=0.05):
        self.tolerance = tolerance

    def assert_statistics_match(self, json_stats: dict, db_stats: dict, strict_fields: list = None):
        """驗證統計數據匹配"""
        strict_fields = strict_fields or ["correct_count", "total_knowledge_points"]

        for field in strict_fields:
            if field in json_stats and field in db_stats:
                assert json_stats[field] == db_stats[field], (
                    f"{field} 不一致: JSON={json_stats[field]}, DB={db_stats[field]}"
                )

        # 總練習次數允許小範圍差異
        if "total_practices" in json_stats and "total_practices" in db_stats:
            json_practices = json_stats["total_practices"]
            db_practices = db_stats["total_practices"]

            if json_practices > 0 or db_practices > 0:  # 至少有一個不為零
                diff = abs(json_practices - db_practices)
                max_diff = max(1, min(json_practices, db_practices) * self.tolerance)
                assert diff <= max_diff, (
                    f"練習次數差異過大: JSON={json_practices}, DB={db_practices}, diff={diff}, max_allowed={max_diff}"
                )

    def assert_categories_match(self, json_categories: list, db_categories: list):
        """驗證分類順序和內容匹配"""
        # 允許空列表的情況
        if not json_categories and not db_categories:
            return

        assert json_categories == db_categories, (
            f"分類不一致: JSON={json_categories}, DB={db_categories}"
        )

    def assert_knowledge_points_similar(
        self, json_points: list, db_points: list, similarity_threshold: float = 0.8
    ):
        """驗證知識點集合的相似性"""
        if not json_points and not db_points:
            return

        json_ids = {point.id for point in json_points}
        db_ids = {point.id for point in db_points}

        intersection = json_ids & db_ids
        union = json_ids | db_ids

        similarity = len(intersection) / len(union) if union else 1.0
        assert similarity >= similarity_threshold, (
            f"知識點相似度過低: {similarity:.2%} < {similarity_threshold:.2%}, "
            f"JSON_IDs={json_ids}, DB_IDs={db_ids}"
        )


def create_test_knowledge_point(suffix: str = "") -> KnowledgePoint:
    """創建測試知識點"""
    return KnowledgePoint(
        id=hash(suffix) % 10000,  # 使用 hash 生成 ID
        key_point=f"測試語法點{suffix}",
        category=ErrorCategory.SYSTEMATIC,
        subtype="動詞時態",
        explanation="這是一個測試用的語法解釋",
        original_phrase="測試原句",
        correction="測試修正",
        original_error=OriginalError(
            chinese_sentence="我昨天去學校",
            user_answer="I go to school yesterday",
            correct_answer="I went to school yesterday",
            timestamp=datetime.now().isoformat(),
        ),
        review_examples=[
            ReviewExample(
                chinese_sentence="我今天去圖書館",
                user_answer="I went to library today",
                correct_answer="I went to the library today",
                timestamp=datetime.now().isoformat(),
                is_correct=False,
            )
        ],
        mastery_level=0.3,
        mistake_count=2,
        correct_count=1,
        created_at=datetime.now().isoformat(),
        last_seen=(datetime.now() - timedelta(days=1)).isoformat(),
        next_review=datetime.now().isoformat(),
        tags=[f"測試標籤{suffix}"],
        custom_notes=f"測試筆記{suffix}",
        is_deleted=False,
        deleted_at="",
        deleted_reason="",
        version_history=[],
        last_modified=datetime.now().isoformat(),
    )


def create_test_dataset(size: int = 10) -> list[KnowledgePoint]:
    """創建測試數據集"""
    return [create_test_knowledge_point(f"_{i}") for i in range(size)]


@pytest.fixture
def test_knowledge_points():
    """測試知識點集合"""
    return create_test_dataset(10)


@pytest.fixture
def populate_json_manager(json_manager, test_knowledge_points):
    """為 JSON 管理器填充測試數據"""
    for point in test_knowledge_points:
        json_manager.add_knowledge_point(point)
    return json_manager


# 測試數據生成器類
class TestDataGenerator:
    """測試數據生成器"""

    @staticmethod
    def generate_consistent_dataset(size: int = 20) -> tuple[list[KnowledgePoint], dict]:
        """生成一致的測試數據集"""
        points = []
        total_practices = 0
        correct_count = 0
        categories = set()

        for i in range(size):
            # 創建知識點
            point = create_test_knowledge_point(f"_consistent_{i}")

            # 計算統計
            total_practices += len(point.review_examples)
            if point.original_error:
                total_practices += 1

            correct_count += sum(1 for ex in point.review_examples if ex.is_correct)
            categories.add(point.category.to_chinese())

            points.append(point)

        expected_stats = {
            "total_knowledge_points": size,
            "total_practices": total_practices,
            "correct_count": correct_count,
            "categories": sorted(list(categories)),
            "average_mastery": sum(p.mastery_level for p in points) / size if points else 0,
            "due_reviews": sum(
                1 for p in points if p.next_review and p.next_review <= datetime.now().isoformat()
            ),
        }

        return points, expected_stats


@pytest.fixture
def test_data_generator():
    """測試數據生成器夾具"""
    return TestDataGenerator()
