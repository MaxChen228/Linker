"""
KnowledgeService 測試套件

測試知識點服務的所有核心功能，包括錯誤保存、知識點管理、複習佇列等
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List

from services.knowledge_service import KnowledgeService, SaveMistakeRequest
from services.base_service import ServiceResult
from core.knowledge import KnowledgeManager, KnowledgePoint
from core.repositories import KnowledgeRepository
from core.error_types import ErrorCategory


# Global fixtures for KnowledgeService tests
@pytest.fixture
def mock_knowledge_manager():
    """Mock KnowledgeManager"""
    manager = Mock(spec=KnowledgeManager)
    manager.knowledge_points = []
    manager.get_statistics.return_value = {
        "total_points": 10,
        "categories": {"SYSTEMATIC": 5, "INDIVIDUAL": 3, "IMPROVEMENT": 2}
    }
    manager.get_knowledge_point.return_value = None
    manager.update_knowledge_point.return_value = True
    manager.get_review_candidates.return_value = []
    manager.save_mistake.return_value = None
    manager.add_review_success.return_value = None
    manager._save_knowledge.return_value = None
    return manager

@pytest.fixture
def mock_knowledge_repository():
    """Mock KnowledgeRepository"""
    repo = Mock(spec=KnowledgeRepository)
    repo.get_statistics.return_value = {
        "file_size": 1024,
        "last_updated": datetime.now().isoformat()
    }
    return repo

@pytest.fixture
def mock_error_processing_service():
    """Mock ErrorProcessingService"""
    service = Mock()
    service.process_errors.return_value = [
        {"key_point": "過去式動詞錯誤"}
    ]
    return service

@pytest.fixture
def mock_practice_record_service():
    """Mock PracticeRecordService"""
    service = Mock()
    service.record_practice.return_value = {
        "timestamp": datetime.now().isoformat(),
        "practice_mode": "new",
        "is_correct": False
    }
    return service

@pytest.fixture
def knowledge_service(
    mock_knowledge_manager,
    mock_knowledge_repository,
    mock_error_processing_service,
    mock_practice_record_service
):
    """創建 KnowledgeService 實例"""
    return KnowledgeService(
        knowledge_manager=mock_knowledge_manager,
        knowledge_repository=mock_knowledge_repository,
        error_processing_service=mock_error_processing_service,
        practice_record_service=mock_practice_record_service
    )

@pytest.fixture
def sample_mistake_request():
    """樣本錯誤保存請求"""
    return SaveMistakeRequest(
        chinese_sentence="我昨天去了學校",
        user_answer="I go to school yesterday",
        feedback={
            "is_generally_correct": False,
            "error_analysis": [
                {
                    "key_point_summary": "過去式動詞錯誤",
                    "original_phrase": "go",
                    "correction": "went",
                    "explanation": "過去式應該用 went"
                }
            ],
            "overall_suggestion": "I went to school yesterday"
        },
        practice_mode="new"
    )

@pytest.fixture
def sample_knowledge_point():
    """樣本知識點"""
    from core.knowledge import OriginalError
    original_error = OriginalError(
        chinese_sentence="我昨天去了學校",
        user_answer="I go to school yesterday",
        correct_answer="I went to school yesterday",
        timestamp=datetime.now().isoformat()
    )
    
    return KnowledgePoint(
        id=1,
        key_point="過去式動詞錯誤",
        category=ErrorCategory.SYSTEMATIC,
        subtype="verb_tense",
        explanation="過去式應該用 went",
        original_phrase="go",
        correction="went",
        original_error=original_error,
        mastery_level=0.3,
        mistake_count=3,
        correct_count=1,
        created_at=datetime.now().isoformat(),
        last_seen=datetime.now().isoformat(),
        next_review=datetime.now().isoformat()
    )


class TestKnowledgeService:
    """KnowledgeService 測試類別"""


class TestSaveMistake:
    """測試 save_mistake 方法"""

    def test_save_mistake_success_with_errors(
        self, 
        knowledge_service, 
        sample_mistake_request,
        mock_knowledge_manager
    ):
        """測試成功保存錯誤（含錯誤分析）"""
        # 設置 Mock 返回值
        mock_knowledge_manager.save_mistake.return_value = None
        
        # 執行測試
        result = knowledge_service.save_mistake(sample_mistake_request)
        
        # 驗證結果
        assert result.success is True
        assert result.message == "錯誤記錄保存完成"
        assert result.data["is_correct"] is False
        assert result.data["practice_mode"] == "new"
        assert len(result.data["knowledge_points_created"]) > 0

    def test_save_mistake_success_correct_answer(
        self, 
        knowledge_service, 
        sample_mistake_request
    ):
        """測試成功保存正確答案"""
        # 修改請求為正確答案
        sample_mistake_request.feedback["is_generally_correct"] = True
        
        # 執行測試
        result = knowledge_service.save_mistake(sample_mistake_request)
        
        # 驗證結果
        assert result.success is True
        assert result.data["is_correct"] is True
        assert result.data["knowledge_points_created"] == []

    def test_save_mistake_validation_error_empty_chinese(
        self, 
        knowledge_service, 
        sample_mistake_request
    ):
        """測試中文句子為空的驗證錯誤"""
        sample_mistake_request.chinese_sentence = ""
        
        result = knowledge_service.save_mistake(sample_mistake_request)
        
        assert result.success is False
        assert result.error_code == "EMPTY_CHINESE_SENTENCE"
        assert "中文句子不能為空" in result.message

    def test_save_mistake_validation_error_empty_answer(
        self, 
        knowledge_service, 
        sample_mistake_request
    ):
        """測試用戶答案為空的驗證錯誤"""
        sample_mistake_request.user_answer = ""
        
        result = knowledge_service.save_mistake(sample_mistake_request)
        
        assert result.success is False
        assert result.error_code == "EMPTY_USER_ANSWER"

    def test_save_mistake_validation_error_invalid_feedback(
        self, 
        knowledge_service, 
        sample_mistake_request
    ):
        """測試回饋格式錯誤"""
        sample_mistake_request.feedback = "invalid"
        
        result = knowledge_service.save_mistake(sample_mistake_request)
        
        assert result.success is False
        assert result.error_code == "INVALID_FEEDBACK_FORMAT"

    def test_save_mistake_review_mode_with_target_points(
        self, 
        knowledge_service, 
        sample_mistake_request,
        mock_knowledge_manager
    ):
        """測試複習模式且答對時的掌握度更新"""
        # 設置複習模式
        sample_mistake_request.practice_mode = "review"
        sample_mistake_request.target_point_ids = ["1", "2"]
        sample_mistake_request.feedback["is_generally_correct"] = True
        
        # 執行測試
        result = knowledge_service.save_mistake(sample_mistake_request)
        
        # 驗證結果
        assert result.success is True
        assert result.data["practice_mode"] == "review"
        
        # 驗證 add_review_success 被調用
        assert mock_knowledge_manager.add_review_success.call_count == 2

    def test_save_mistake_exception_handling(
        self, 
        mock_knowledge_manager,
        mock_knowledge_repository,
        sample_mistake_request
    ):
        """測試異常處理"""
        # 創建沒有錯誤處理服務的KnowledgeService來測試內建邏輯
        service = KnowledgeService(
            knowledge_manager=mock_knowledge_manager,
            knowledge_repository=mock_knowledge_repository,
            error_processing_service=None,  # 不使用錯誤處理服務
            practice_record_service=None
        )
        
        # 設置 Mock 拋出異常
        mock_knowledge_manager.save_mistake.side_effect = Exception("Test error")
        
        # 執行測試
        result = service.save_mistake(sample_mistake_request)
        
        # 驗證仍然成功，但knowledge_points_created為空
        assert result.success is True
        assert result.data["knowledge_points_created"] == []


class TestGetKnowledgePoints:
    """測試 get_knowledge_points 方法"""

    def test_get_knowledge_points_success(
        self, 
        knowledge_service, 
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試成功獲取知識點列表"""
        mock_knowledge_manager.knowledge_points = [sample_knowledge_point]
        
        result = knowledge_service.get_knowledge_points()
        
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["id"] == 1
        assert result.data[0]["key_point"] == "過去式動詞錯誤"

    def test_get_knowledge_points_with_category_filter(
        self, 
        knowledge_service, 
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試按類別篩選知識點"""
        mock_knowledge_manager.knowledge_points = [sample_knowledge_point]
        
        result = knowledge_service.get_knowledge_points(category="systematic")
        
        assert result.success is True
        assert len(result.data) == 1

    def test_get_knowledge_points_invalid_category(
        self, 
        knowledge_service,
        mock_knowledge_manager
    ):
        """測試無效類別"""
        mock_knowledge_manager.knowledge_points = []
        
        result = knowledge_service.get_knowledge_points(category="invalid_category")
        
        assert result.success is False
        assert result.error_code == "INVALID_CATEGORY"

    def test_get_knowledge_points_with_limit(
        self, 
        knowledge_service,
        mock_knowledge_manager
    ):
        """測試限制返回數量"""
        from core.knowledge import OriginalError
        # 創建多個知識點
        points = []
        for i in range(1, 6):
            original_error = OriginalError(
                chinese_sentence=f"測試句子{i}",
                user_answer=f"test answer {i}",
                correct_answer=f"correct answer {i}",
                timestamp=datetime.now().isoformat()
            )
            points.append(KnowledgePoint(
                id=i,
                key_point=f"知識點{i}",
                category=ErrorCategory.SYSTEMATIC,
                subtype="test",
                explanation=f"解釋{i}",
                original_phrase=f"phrase{i}",
                correction=f"correction{i}",
                original_error=original_error
            ))
        mock_knowledge_manager.knowledge_points = points
        
        result = knowledge_service.get_knowledge_points(limit=3)
        
        assert result.success is True
        assert len(result.data) == 3


class TestGetKnowledgePointById:
    """測試 get_knowledge_point_by_id 方法"""

    def test_get_knowledge_point_by_id_success(
        self, 
        knowledge_service, 
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試成功根據ID獲取知識點"""
        mock_knowledge_manager.get_knowledge_point.return_value = sample_knowledge_point
        
        result = knowledge_service.get_knowledge_point_by_id("1")
        
        assert result.success is True
        assert result.data["id"] == 1
        assert result.data["key_point"] == "過去式動詞錯誤"

    def test_get_knowledge_point_by_id_not_found(
        self, 
        knowledge_service,
        mock_knowledge_manager
    ):
        """測試知識點不存在"""
        mock_knowledge_manager.get_knowledge_point.return_value = None
        
        result = knowledge_service.get_knowledge_point_by_id("999")
        
        assert result.success is False
        assert result.error_code == "KNOWLEDGE_POINT_NOT_FOUND"
        assert "找不到ID為 999 的知識點" in result.message


class TestUpdateMastery:
    """測試 update_mastery 方法"""

    def test_update_mastery_success(
        self, 
        knowledge_service, 
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試成功更新掌握度"""
        mock_knowledge_manager.update_knowledge_point.return_value = True
        mock_knowledge_manager.get_knowledge_point.return_value = sample_knowledge_point
        
        result = knowledge_service.update_mastery("1", True)
        
        assert result.success is True
        assert result.data["point_id"] == "1"
        assert result.data["is_correct"] is True
        assert result.data["new_mastery_level"] == 0.3

    def test_update_mastery_failure(
        self, 
        knowledge_service,
        mock_knowledge_manager
    ):
        """測試更新掌握度失敗"""
        mock_knowledge_manager.update_knowledge_point.return_value = False
        
        result = knowledge_service.update_mastery("1", True)
        
        assert result.success is False
        assert result.error_code == "MASTERY_UPDATE_FAILED"

    def test_update_mastery_with_review_context(
        self, 
        knowledge_service, 
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試帶複習上下文的掌握度更新"""
        mock_knowledge_manager.update_knowledge_point.return_value = True
        mock_knowledge_manager.get_knowledge_point.return_value = sample_knowledge_point
        
        review_context = {"review_session_id": "123", "difficulty": "hard"}
        
        result = knowledge_service.update_mastery("1", True, review_context)
        
        assert result.success is True
        assert result.data["review_context"] == review_context


class TestGetReviewQueue:
    """測試 get_review_queue 方法"""

    def test_get_review_queue_success(
        self, 
        knowledge_service, 
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試成功獲取複習佇列"""
        mock_knowledge_manager.get_review_candidates.return_value = [sample_knowledge_point]
        
        result = knowledge_service.get_review_queue(max_points=5)
        
        assert result.success is True
        assert len(result.data) == 1
        assert "priority_score" in result.data[0]
        assert "is_due" in result.data[0]

    def test_get_review_queue_empty(
        self, 
        knowledge_service,
        mock_knowledge_manager
    ):
        """測試空的複習佇列"""
        mock_knowledge_manager.get_review_candidates.return_value = []
        
        result = knowledge_service.get_review_queue()
        
        assert result.success is True
        assert len(result.data) == 0
        assert "獲取 0 個待複習知識點" in result.message

    def test_get_review_queue_priority_calculation(
        self, 
        knowledge_service,
        mock_knowledge_manager
    ):
        """測試複習優先級計算"""
        from core.knowledge import OriginalError
        # 創建不同掌握度的知識點
        original_error = OriginalError(
            chinese_sentence="低掌握度測試句子",
            user_answer="test answer",
            correct_answer="correct answer",
            timestamp=datetime.now().isoformat()
        )
        low_mastery_point = KnowledgePoint(
            id=1,
            key_point="低掌握度知識點",
            category=ErrorCategory.SYSTEMATIC,
            subtype="test",
            explanation="測試解釋",
            original_phrase="test phrase",
            correction="corrected phrase",
            original_error=original_error,
            mastery_level=0.1,
            mistake_count=5,
            next_review=datetime.now().isoformat()
        )
        
        mock_knowledge_manager.get_review_candidates.return_value = [low_mastery_point]
        
        result = knowledge_service.get_review_queue()
        
        assert result.success is True
        priority_score = result.data[0]["priority_score"]
        assert priority_score > 0


class TestGetKnowledgeStatistics:
    """測試 get_knowledge_statistics 方法"""

    def test_get_knowledge_statistics_success(
        self, 
        knowledge_service,
        mock_knowledge_manager,
        mock_knowledge_repository
    ):
        """測試成功獲取統計資訊"""
        result = knowledge_service.get_knowledge_statistics()
        
        assert result.success is True
        assert "total_points" in result.data
        assert "service_stats" in result.data
        assert "repository_stats" in result.data
        
        # 驗證服務統計包含必要字段
        service_stats = result.data["service_stats"]
        assert "mistakes_saved" in service_stats
        assert "knowledge_points_created" in service_stats
        assert "mastery_updates" in service_stats

    def test_get_knowledge_statistics_repository_error(
        self, 
        knowledge_service,
        mock_knowledge_manager,
        mock_knowledge_repository
    ):
        """測試Repository統計獲取失敗"""
        mock_knowledge_repository.get_statistics.side_effect = Exception("DB Error")
        
        result = knowledge_service.get_knowledge_statistics()
        
        assert result.success is True  # 服務仍能成功，只是Repository統計為空
        assert result.data["repository_stats"] == {}


class TestPrivateMethods:
    """測試私有方法"""

    def test_validate_mistake_request_all_valid(
        self, 
        knowledge_service, 
        sample_mistake_request
    ):
        """測試請求驗證 - 全部有效"""
        result = knowledge_service._validate_mistake_request(sample_mistake_request)
        
        assert result.success is True
        assert result.data is True

    def test_format_knowledge_point(
        self, 
        knowledge_service, 
        sample_knowledge_point
    ):
        """測試知識點格式化"""
        formatted = knowledge_service._format_knowledge_point(sample_knowledge_point)
        
        assert formatted["id"] == 1
        assert formatted["key_point"] == "過去式動詞錯誤"
        assert formatted["category"] == "systematic"
        assert formatted["mastery_level"] == 0.3
        assert "examples_count" in formatted

    def test_calculate_review_priority(
        self, 
        knowledge_service, 
        sample_knowledge_point
    ):
        """測試複習優先級計算"""
        priority = knowledge_service._calculate_review_priority(sample_knowledge_point)
        
        assert isinstance(priority, float)
        assert priority > 0

    def test_update_operation_stats(
        self, 
        knowledge_service
    ):
        """測試操作統計更新"""
        initial_saved = knowledge_service._operation_stats["mistakes_saved"]
        
        knowledge_service._update_operation_stats("mistakes_saved", 2)
        
        assert knowledge_service._operation_stats["mistakes_saved"] == initial_saved + 1
        assert knowledge_service._operation_stats["knowledge_points_created"] == 2
        assert knowledge_service._operation_stats["last_operation"] is not None


class TestServiceInfo:
    """測試服務資訊"""

    def test_get_service_info(
        self, 
        knowledge_service
    ):
        """測試獲取服務資訊"""
        info = knowledge_service.get_service_info()
        
        assert info["service_name"] == "KnowledgeService"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        assert "statistics" in info
        assert "dependencies" in info
        assert "initialized" in info
        
        # 驗證能力列表
        capabilities = info["capabilities"]
        assert "錯誤記錄保存" in capabilities
        assert "知識點資訊獲取" in capabilities
        assert "掌握度更新管理" in capabilities


class TestEdgeCases:
    """測試邊界情況"""

    def test_empty_knowledge_points_list(
        self, 
        knowledge_service,
        mock_knowledge_manager
    ):
        """測試空知識點列表"""
        mock_knowledge_manager.knowledge_points = []
        
        result = knowledge_service.get_knowledge_points()
        
        assert result.success is True
        assert len(result.data) == 0

    def test_large_knowledge_points_list(
        self, 
        knowledge_service,
        mock_knowledge_manager
    ):
        """測試大量知識點列表"""
        from core.knowledge import OriginalError
        # 創建大量知識點
        points = []
        for i in range(1000):
            original_error = OriginalError(
                chinese_sentence=f"大量測試句子{i}",
                user_answer=f"test answer {i}",
                correct_answer=f"correct answer {i}",
                timestamp=datetime.now().isoformat()
            )
            points.append(KnowledgePoint(
                id=i,
                key_point=f"知識點{i}",
                category=ErrorCategory.SYSTEMATIC,
                subtype="test",
                explanation=f"大量測試解釋{i}",
                original_phrase=f"phrase{i}",
                correction=f"correction{i}",
                original_error=original_error
            ))
        mock_knowledge_manager.knowledge_points = points
        
        result = knowledge_service.get_knowledge_points(limit=10)
        
        assert result.success is True
        assert len(result.data) == 10

    def test_concurrent_operations_simulation(
        self, 
        knowledge_service, 
        sample_mistake_request
    ):
        """模擬並發操作"""
        # 模擬多個並發保存操作
        results = []
        for i in range(5):
            result = knowledge_service.save_mistake(sample_mistake_request)
            results.append(result)
        
        # 驗證所有操作都有唯一的request_id
        request_ids = [r.request_id for r in results]
        assert len(set(request_ids)) == 5  # 所有ID都應該是唯一的


@pytest.mark.integration
class TestKnowledgeServiceIntegration:
    """整合測試"""

    def test_full_workflow_new_mistake(
        self, 
        knowledge_service, 
        sample_mistake_request,
        mock_knowledge_manager
    ):
        """測試完整的新錯誤處理流程"""
        # 1. 保存錯誤
        save_result = knowledge_service.save_mistake(sample_mistake_request)
        assert save_result.success is True
        
        # 2. 獲取統計
        stats_result = knowledge_service.get_knowledge_statistics()
        assert stats_result.success is True
        
        # 3. 獲取複習佇列
        queue_result = knowledge_service.get_review_queue()
        assert queue_result.success is True

    def test_review_workflow(
        self, 
        knowledge_service, 
        sample_mistake_request,
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試複習流程"""
        # 設置複習模式
        sample_mistake_request.practice_mode = "review"
        sample_mistake_request.target_point_ids = ["1"]
        sample_mistake_request.feedback["is_generally_correct"] = True
        
        # 設置 Mock 知識點
        mock_knowledge_manager.get_knowledge_point.return_value = sample_knowledge_point
        
        # 1. 保存複習結果
        save_result = knowledge_service.save_mistake(sample_mistake_request)
        assert save_result.success is True
        
        # 2. 更新掌握度
        mastery_result = knowledge_service.update_mastery("1", True)
        assert mastery_result.success is True
        
        # 3. 獲取知識點詳情
        detail_result = knowledge_service.get_knowledge_point_by_id("1")
        assert detail_result.success is True