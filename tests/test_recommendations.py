"""
測試學習推薦系統
"""

import json
from datetime import datetime, timedelta

import pytest

from core.database.adapter import KnowledgeManagerAdapter
from core.error_types import ErrorCategory
from core.knowledge import KnowledgePoint, OriginalError


class TestLearningRecommendations:
    """測試學習推薦功能"""

    @pytest.fixture
    def mock_knowledge_points(self):
        """創建模擬知識點數據"""
        now = datetime.now()
        past_due = (now - timedelta(days=7)).isoformat()
        future = (now + timedelta(days=7)).isoformat()

        points = [
            # 低掌握度系統性錯誤
            KnowledgePoint(
                id=1,
                key_point="Past tense usage",
                category=ErrorCategory.SYSTEMATIC,
                subtype="past tense",
                explanation="動詞過去式使用錯誤",
                original_phrase="I go there yesterday",
                correction="I went there yesterday",
                original_error=OriginalError(
                    chinese_sentence="我昨天去那裡",
                    user_answer="I go there yesterday",
                    correct_answer="I went there yesterday",
                    timestamp=now.isoformat(),
                ),
                mastery_level=0.2,
                mistake_count=5,
                correct_count=1,
                next_review=past_due,
            ),
            # 中等掌握度個別錯誤
            KnowledgePoint(
                id=2,
                key_point="Spelling: necessary",
                category=ErrorCategory.ISOLATED,
                subtype="spelling",
                explanation="單字拼寫錯誤",
                original_phrase="necesary",
                correction="necessary",
                original_error=OriginalError(
                    chinese_sentence="這是必要的",
                    user_answer="This is necesary",
                    correct_answer="This is necessary",
                    timestamp=now.isoformat(),
                ),
                mastery_level=0.5,
                mistake_count=3,
                correct_count=3,
                next_review=future,
            ),
            # 高掌握度優化建議
            KnowledgePoint(
                id=3,
                key_point="Formal expression",
                category=ErrorCategory.ENHANCEMENT,
                subtype="formality",
                explanation="更正式的表達方式",
                original_phrase="get",
                correction="obtain",
                original_error=OriginalError(
                    chinese_sentence="獲得許可",
                    user_answer="get permission",
                    correct_answer="obtain permission",
                    timestamp=now.isoformat(),
                ),
                mastery_level=0.8,
                mistake_count=1,
                correct_count=5,
                next_review=future,
            ),
            # 待複習的低掌握度點
            KnowledgePoint(
                id=4,
                key_point="Article usage",
                category=ErrorCategory.SYSTEMATIC,
                subtype="articles",
                explanation="冠詞使用錯誤",
                original_phrase="a apple",
                correction="an apple",
                original_error=OriginalError(
                    chinese_sentence="一個蘋果",
                    user_answer="a apple",
                    correct_answer="an apple",
                    timestamp=now.isoformat(),
                ),
                mastery_level=0.15,
                mistake_count=4,
                correct_count=0,
                next_review=past_due,
            ),
        ]

        return points

    @pytest.fixture
    def adapter_with_mock_data(self, mock_knowledge_points, temp_dir):
        """創建包含模擬數據的適配器"""
        # 創建臨時 JSON 文件
        data_file = temp_dir / "knowledge.json"
        data = {
            "version": "4.0",
            "knowledge_points": [
                {
                    "id": p.id,
                    "key_point": p.key_point,
                    "category": p.category.value,
                    "subtype": p.subtype,
                    "explanation": p.explanation,
                    "original_phrase": p.original_phrase,
                    "correction": p.correction,
                    "original_error": {
                        "chinese_sentence": p.original_error.chinese_sentence,
                        "user_answer": p.original_error.user_answer,
                        "correct_answer": p.original_error.correct_answer,
                        "timestamp": datetime.now().isoformat(),
                    },
                    "review_examples": [],
                    "mastery_level": p.mastery_level,
                    "mistake_count": p.mistake_count,
                    "correct_count": p.correct_count,
                    "created_at": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "next_review": p.next_review,
                    "is_deleted": False,
                    "deleted_at": "",
                    "deleted_reason": "",
                    "tags": [],
                    "custom_notes": "",
                    "version_history": [],
                    "last_modified": datetime.now().isoformat(),
                }
                for p in mock_knowledge_points
            ],
        }

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 創建適配器
        adapter = KnowledgeManagerAdapter(use_database=False, data_dir=str(temp_dir))
        return adapter

    def test_get_recommendations_with_data(self, adapter_with_mock_data):
        """測試有數據時的推薦生成"""
        recommendations = adapter_with_mock_data.get_learning_recommendations()

        # 驗證返回結構
        assert "recommendations" in recommendations
        assert "focus_areas" in recommendations
        assert "suggested_difficulty" in recommendations
        assert "next_review_count" in recommendations
        assert "priority_points" in recommendations
        assert "statistics" in recommendations

        # 驗證推薦內容
        assert len(recommendations["recommendations"]) > 0
        assert len(recommendations["recommendations"]) <= 3

        # 驗證重點領域
        assert "systematic" in recommendations["focus_areas"]

        # 驗證統計數據
        stats = recommendations["statistics"]
        assert stats["total_points"] == 4
        assert stats["low_mastery_count"] == 2
        assert stats["due_for_review"] == 2

        # 驗證優先學習點
        priority_points = recommendations["priority_points"]
        assert len(priority_points) > 0
        assert priority_points[0]["mastery_level"] < 0.3

    def test_get_recommendations_empty_data(self, temp_dir):
        """測試無數據時的推薦生成"""
        # 創建空的知識庫文件
        data_file = temp_dir / "knowledge.json"
        data = {"version": "4.0", "knowledge_points": []}
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        adapter = KnowledgeManagerAdapter(use_database=False, data_dir=str(temp_dir))
        recommendations = adapter.get_learning_recommendations()

        # 驗證返回默認推薦
        assert recommendations["recommendations"][0] == "開始第一次練習，建立學習基礎"
        assert recommendations["focus_areas"] == []
        assert recommendations["suggested_difficulty"] == 1
        assert recommendations["next_review_count"] == 0
        assert recommendations["priority_points"] == []

    def test_permanent_delete_old_points_dry_run(self, adapter_with_mock_data):
        """測試預覽模式刪除舊知識點"""
        # 添加一些已刪除的知識點
        adapter = adapter_with_mock_data
        points = adapter.get_active_points()

        # 軟刪除一些點
        old_date = (datetime.now() - timedelta(days=35)).isoformat()
        recent_date = (datetime.now() - timedelta(days=5)).isoformat()

        points[0].is_deleted = True
        points[0].deleted_at = old_date
        points[0].mastery_level = 0.7  # 高掌握度，應該刪除

        points[1].is_deleted = True
        points[1].deleted_at = recent_date  # 最近刪除，不應該刪除

        points[2].is_deleted = True
        points[2].deleted_at = old_date
        points[2].mastery_level = 0.2  # 低掌握度，應該保留

        # 執行預覽
        result = adapter.permanent_delete_old_points(days_old=30, dry_run=True)

        # 驗證結果
        assert result["dry_run"]
        assert result["scanned"] == 3
        assert result["eligible_for_deletion"] == 1  # 只有 points[0]
        assert result["preserved_high_value"] == 1  # points[2] 因為低掌握度被保留
        assert len(result["deleted_ids"]) == 0  # 預覽模式不實際刪除

    def test_permanent_delete_old_points_actual(self, adapter_with_mock_data):
        """測試實際刪除舊知識點"""
        adapter = adapter_with_mock_data
        points = adapter.get_active_points()

        # 設置要刪除的點
        old_date = (datetime.now() - timedelta(days=35)).isoformat()
        points[0].is_deleted = True
        points[0].deleted_at = old_date
        points[0].mastery_level = 0.7
        points[0].mistake_count = 2

        original_count = len(adapter._legacy_manager.knowledge_points)

        # 執行實際刪除
        result = adapter.permanent_delete_old_points(days_old=30, dry_run=False)

        # 驗證結果
        assert not result["dry_run"]
        assert result["eligible_for_deletion"] == 1
        assert len(result["deleted_ids"]) == 1
        assert points[0].id in result["deleted_ids"]

        # 驗證實際被刪除
        final_count = len(adapter._legacy_manager.knowledge_points)
        assert final_count == original_count - 1

    @pytest.mark.unit
    def test_recommendation_performance(self, adapter_with_mock_data):
        """測試推薦系統性能"""
        import time

        # 測試執行時間
        start_time = time.time()
        recommendations = adapter_with_mock_data.get_learning_recommendations()
        execution_time = (time.time() - start_time) * 1000  # 轉換為毫秒

        # 確保響應時間小於100ms
        assert execution_time < 100, f"推薦生成耗時 {execution_time:.2f}ms，超過100ms限制"

        # 確保返回有效結果
        assert recommendations is not None
        assert isinstance(recommendations, dict)


class TestRecommendationAlgorithm:
    """測試推薦算法邏輯"""

    @pytest.fixture
    def mock_knowledge_points(self):
        """創建模擬知識點數據"""
        now = datetime.now()
        past_due = (now - timedelta(days=7)).isoformat()
        (now + timedelta(days=7)).isoformat()

        points = [
            KnowledgePoint(
                id=1,
                key_point="Past tense usage",
                category=ErrorCategory.SYSTEMATIC,
                subtype="past tense",
                explanation="動詞過去式使用錯誤",
                original_phrase="I go there yesterday",
                correction="I went there yesterday",
                original_error=OriginalError(
                    chinese_sentence="我昨天去那裡",
                    user_answer="I go there yesterday",
                    correct_answer="I went there yesterday",
                    timestamp=now.isoformat(),
                ),
                mastery_level=0.2,
                mistake_count=5,
                correct_count=1,
                next_review=past_due,
            ),
        ]
        return points

    @pytest.fixture
    def adapter_with_mock_data(self, mock_knowledge_points, temp_dir):
        """創建包含模擬數據的適配器"""
        # 創建臨時 JSON 文件
        data_file = temp_dir / "knowledge.json"
        data = {
            "version": "4.0",
            "knowledge_points": [
                {
                    "id": p.id,
                    "key_point": p.key_point,
                    "category": p.category.value,
                    "subtype": p.subtype,
                    "explanation": p.explanation,
                    "original_phrase": p.original_phrase,
                    "correction": p.correction,
                    "original_error": {
                        "chinese_sentence": p.original_error.chinese_sentence,
                        "user_answer": p.original_error.user_answer,
                        "correct_answer": p.original_error.correct_answer,
                        "timestamp": datetime.now().isoformat(),
                    },
                    "review_examples": [],
                    "mastery_level": p.mastery_level,
                    "mistake_count": p.mistake_count,
                    "correct_count": p.correct_count,
                    "created_at": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "next_review": p.next_review,
                    "is_deleted": False,
                    "deleted_at": "",
                    "deleted_reason": "",
                    "tags": [],
                    "custom_notes": "",
                    "version_history": [],
                    "last_modified": datetime.now().isoformat(),
                }
                for p in mock_knowledge_points
            ],
        }

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 創建適配器
        adapter = KnowledgeManagerAdapter(use_database=False, data_dir=str(temp_dir))
        return adapter

    def test_priority_calculation(self, adapter_with_mock_data):
        """測試優先級計算"""
        recommendations = adapter_with_mock_data.get_learning_recommendations()
        priority_points = recommendations["priority_points"]

        # 驗證優先級排序（待複習 > 低掌握度系統性 > 其他）
        if len(priority_points) > 1:
            # 第一個應該是低掌握度或待複習的
            assert priority_points[0]["mastery_level"] < 0.3

            # 系統性錯誤應該優先
            systematic_points = [p for p in priority_points if p["category"] == "systematic"]
            if systematic_points:
                # 至少有一個系統性錯誤在前3個
                top_3_categories = [p["category"] for p in priority_points[:3]]
                assert "systematic" in top_3_categories

    def test_difficulty_suggestion(self):
        """測試難度建議邏輯"""

        # 測試不同平均掌握度對應的建議難度
        test_cases = [
            (0.2, 1),  # 低掌握度 -> 簡單
            (0.5, 2),  # 中等掌握度 -> 中等
            (0.8, 3),  # 高掌握度 -> 困難
        ]

        for _avg_mastery, _expected_difficulty in test_cases:
            # 這裡應該有更細緻的測試，但需要能夠控制內部數據
            pass
