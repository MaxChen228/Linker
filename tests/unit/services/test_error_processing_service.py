"""
ErrorProcessingService 測試套件

測試錯誤處理服務的所有核心功能，包括錯誤分類、知識點創建、錯誤合併等
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List, Optional

from services.error_processing_service import ErrorProcessingService
from services.base_service import ServiceResult
from core.error_types import ErrorCategory, ErrorTypeSystem
from core.knowledge import KnowledgeManager, KnowledgePoint, OriginalError, ReviewExample
from core.repositories.knowledge_repository import KnowledgeRepository


# Global fixtures for ErrorProcessingService tests
@pytest.fixture
def mock_error_type_system():
    """Mock ErrorTypeSystem"""
    system = Mock(spec=ErrorTypeSystem)
    system.classify.return_value = (ErrorCategory.SYSTEMATIC, "verb_tense")
    return system

@pytest.fixture
def mock_knowledge_repository():
    """Mock KnowledgeRepository"""
    repo = Mock(spec=KnowledgeRepository)
    return repo

@pytest.fixture
def mock_knowledge_manager():
    """Mock KnowledgeManager"""
    manager = Mock(spec=KnowledgeManager)
    manager.knowledge_points = Mock()
    manager.knowledge_points.append = Mock()
    manager._find_knowledge_point = Mock(return_value=None)
    manager._get_next_id = Mock(return_value=1)
    manager._save_knowledge = Mock()
    return manager

@pytest.fixture
def error_processing_service(
    mock_error_type_system,
    mock_knowledge_repository,
    mock_knowledge_manager
):
    """創建 ErrorProcessingService 實例"""
    return ErrorProcessingService(
        error_type_system=mock_error_type_system,
        knowledge_repository=mock_knowledge_repository,
        knowledge_manager=mock_knowledge_manager
    )

@pytest.fixture
def sample_error_data():
    """樣本錯誤數據"""
    return {
        "key_point_summary": "過去式動詞錯誤",
        "original_phrase": "go",
        "correction": "went",
        "explanation": "過去式應該用 went，不是 go",
        "severity": "major"
    }

@pytest.fixture
def sample_feedback():
    """樣本AI回饋"""
    return {
        "is_generally_correct": False,
        "error_analysis": [
            {
                "key_point_summary": "過去式動詞錯誤",
                "original_phrase": "go",
                "correction": "went",
                "explanation": "過去式應該用 went"
            },
            {
                "key_point_summary": "介系詞使用錯誤",
                "original_phrase": "in school",
                "correction": "to school",
                "explanation": "go 後面應該用 to，不是 in"
            }
        ],
        "overall_suggestion": "I went to school yesterday"
    }

@pytest.fixture
def sample_knowledge_point():
    """樣本知識點 Mock"""
    point = Mock(spec=KnowledgePoint)
    point.id = 1
    point.key_point = "過去式動詞錯誤: go"
    point.category = ErrorCategory.SYSTEMATIC
    point.subtype = "verb_tense"
    point.explanation = "過去式應該用 went"
    point.original_phrase = "go"
    point.correction = "went"
    point.mastery_level = 0.3
    point.mistake_count = 2
    point.correct_count = 1
    point.review_examples = []
    point.update_mastery = Mock()
    return point


class TestErrorProcessingService:
    """ErrorProcessingService 測試類別"""


class TestServiceInitialization:
    """測試服務初始化"""

    def test_service_initialization_with_dependencies(
        self,
        mock_error_type_system,
        mock_knowledge_repository,
        mock_knowledge_manager
    ):
        """測試帶依賴的服務初始化"""
        service = ErrorProcessingService(
            error_type_system=mock_error_type_system,
            knowledge_repository=mock_knowledge_repository,
            knowledge_manager=mock_knowledge_manager
        )
        
        assert service.error_type_system == mock_error_type_system
        assert service.knowledge_repository == mock_knowledge_repository
        assert service.knowledge_manager == mock_knowledge_manager

    def test_service_initialization_with_defaults(self):
        """測試使用預設依賴的服務初始化"""
        service = ErrorProcessingService()
        
        assert service.error_type_system is not None
        assert service.knowledge_repository is not None
        assert service.knowledge_manager is not None

    def test_get_service_info(self, error_processing_service):
        """測試獲取服務資訊"""
        info = error_processing_service.get_service_info()
        
        assert info["name"] == "ErrorProcessingService"
        assert info["version"] == "1.0.0"
        assert "dependencies" in info
        assert "status" in info


class TestProcessErrors:
    """測試批量錯誤處理"""

    def test_process_errors_success(
        self,
        error_processing_service,
        sample_feedback
    ):
        """測試成功處理多個錯誤"""
        result = error_processing_service.process_errors(
            chinese_sentence="我昨天去了學校",
            user_answer="I go in school yesterday",
            feedback=sample_feedback,
            practice_mode="new"
        )
        
        assert result.success is True
        assert len(result.data) == 2  # 兩個錯誤
        assert "成功處理 2 個錯誤" in result.message

    def test_process_errors_empty_error_analysis(
        self,
        error_processing_service
    ):
        """測試空錯誤分析"""
        feedback = {
            "is_generally_correct": True,
            "error_analysis": [],
            "overall_suggestion": "Perfect!"
        }
        
        result = error_processing_service.process_errors(
            chinese_sentence="我昨天去了學校",
            user_answer="I went to school yesterday",
            feedback=feedback
        )
        
        assert result.success is True
        assert len(result.data) == 0
        assert "成功處理 0 個錯誤" in result.message

    def test_process_errors_partial_failure(
        self,
        error_processing_service,
        sample_feedback,
        mock_error_type_system
    ):
        """測試部分錯誤處理失敗"""
        # 設置第一個錯誤處理會失敗
        mock_error_type_system.classify.side_effect = [
            Exception("Classification error"),
            (ErrorCategory.SYSTEMATIC, "preposition")
        ]
        
        result = error_processing_service.process_errors(
            chinese_sentence="我昨天去了學校",
            user_answer="I go in school yesterday",
            feedback=sample_feedback
        )
        
        assert result.success is True
        assert len(result.data) == 1  # 只有一個成功處理


class TestProcessSingleError:
    """測試單個錯誤處理"""

    def test_process_single_error_new_knowledge_point(
        self,
        error_processing_service,
        sample_error_data,
        mock_knowledge_manager
    ):
        """測試創建新知識點"""
        # 確保找不到現有知識點
        mock_knowledge_manager._find_knowledge_point.return_value = None
        
        result = error_processing_service.process_single_error(
            chinese_sentence="我昨天去了學校",
            user_answer="I go to school yesterday",
            error=sample_error_data,
            correct_answer="I went to school yesterday",
            practice_mode="new"
        )
        
        assert result.success is True
        assert result.data["knowledge_point_id"] == 1
        assert result.data["category"] == "systematic"
        assert result.data["key_point"] == "過去式動詞錯誤: go"

    def test_process_single_error_existing_knowledge_point(
        self,
        error_processing_service,
        sample_error_data,
        mock_knowledge_manager
    ):
        """測試更新現有知識點"""
        # 創建Mock知識點
        mock_point = Mock()
        mock_point.id = 1
        mock_point.review_examples = []
        
        # 設置找到現有知識點
        mock_knowledge_manager._find_knowledge_point.return_value = mock_point
        
        result = error_processing_service.process_single_error(
            chinese_sentence="我昨天去了學校",
            user_answer="I go to school yesterday",
            error=sample_error_data,
            correct_answer="I went to school yesterday",
            practice_mode="new"
        )
        
        assert result.success is True
        assert result.data["knowledge_point_id"] == 1
        
        # 驗證掌握度被更新
        mock_point.update_mastery.assert_called_once_with(is_correct=False)

    def test_process_single_error_review_mode(
        self,
        error_processing_service,
        sample_error_data,
        mock_knowledge_manager
    ):
        """測試複習模式下的錯誤處理"""
        # 創建Mock知識點
        mock_point = Mock()
        mock_point.id = 1
        mock_point.review_examples = []
        
        # 設置找到現有知識點
        mock_knowledge_manager._find_knowledge_point.return_value = mock_point
        
        result = error_processing_service.process_single_error(
            chinese_sentence="我昨天去了學校",
            user_answer="I go to school yesterday",
            error=sample_error_data,
            correct_answer="I went to school yesterday",
            practice_mode="review"
        )
        
        assert result.success is True
        assert result.data["practice_mode"] == "review"
        
        # 驗證複習例句被添加
        assert len(mock_point.review_examples) > 0


class TestExtractErrorDetails:
    """測試錯誤詳細信息提取"""

    def test_extract_error_details_complete(
        self,
        error_processing_service,
        sample_error_data
    ):
        """測試完整錯誤信息提取"""
        details = error_processing_service.extract_error_details(sample_error_data)
        
        assert details["key_point"] == "過去式動詞錯誤"
        assert details["original_phrase"] == "go"
        assert details["correction"] == "went"
        assert details["explanation"] == "過去式應該用 went，不是 go"
        assert details["severity"] == "major"

    def test_extract_error_details_minimal(
        self,
        error_processing_service
    ):
        """測試最小錯誤信息提取"""
        minimal_error = {
            "key_point_summary": "基本錯誤"
        }
        
        details = error_processing_service.extract_error_details(minimal_error)
        
        assert details["key_point"] == "基本錯誤"
        assert details["original_phrase"] == ""
        assert details["correction"] == ""
        assert details["explanation"] == ""
        assert details["severity"] == "major"  # 預設值

    def test_extract_error_details_empty(
        self,
        error_processing_service
    ):
        """測試空錯誤信息"""
        details = error_processing_service.extract_error_details({})
        
        assert details["key_point"] == ""
        assert details["original_phrase"] == ""
        assert details["correction"] == ""
        assert details["explanation"] == ""
        assert details["severity"] == "major"


class TestClassifyError:
    """測試錯誤分類"""

    def test_classify_error_with_ai_category(
        self,
        error_processing_service,
        mock_error_type_system
    ):
        """測試使用AI提供的分類"""
        error_details = {
            "key_point": "過去式錯誤",
            "explanation": "動詞時態錯誤",
            "severity": "major",
            "category": "systematic"
        }
        
        # 設置分類系統的返回值
        mock_error_type_system.classify.return_value = (ErrorCategory.SYSTEMATIC, "verb_tense")
        
        category, subtype = error_processing_service.classify_error(error_details)
        
        assert category == ErrorCategory.SYSTEMATIC
        assert subtype == "verb_tense"

    def test_classify_error_automatic_classification(
        self,
        error_processing_service,
        mock_error_type_system
    ):
        """測試自動分類"""
        error_details = {
            "key_point": "不規則動詞錯誤",
            "explanation": "不規則動詞的過去式形式錯誤",
            "severity": "major"
        }
        
        mock_error_type_system.classify.return_value = (ErrorCategory.ISOLATED, "irregular_verb")
        
        category, subtype = error_processing_service.classify_error(error_details)
        
        assert category == ErrorCategory.ISOLATED
        assert subtype == "irregular_verb"
        
        # 驗證分類系統被調用
        mock_error_type_system.classify.assert_called_with(
            "不規則動詞錯誤",
            "不規則動詞的過去式形式錯誤",
            "major"
        )

    def test_classify_error_invalid_ai_category(
        self,
        error_processing_service,
        mock_error_type_system
    ):
        """測試無效的AI分類"""
        error_details = {
            "key_point": "語法錯誤",
            "explanation": "基本語法問題",
            "severity": "minor",
            "category": "invalid_category"
        }
        
        # ErrorCategory.from_string 會拋出異常
        with patch('core.error_types.ErrorCategory.from_string') as mock_from_string:
            mock_from_string.side_effect = ValueError("Invalid category")
            mock_error_type_system.classify.return_value = (ErrorCategory.SYSTEMATIC, "grammar")
            
            category, subtype = error_processing_service.classify_error(error_details)
            
            assert category == ErrorCategory.SYSTEMATIC
            assert subtype == "grammar"


class TestGenerateSpecificKeyPoint:
    """測試具體知識點描述生成"""

    def test_generate_specific_key_point_with_phrase(
        self,
        error_processing_service
    ):
        """測試帶原始短語的知識點描述"""
        error_details = {
            "key_point": "過去式動詞錯誤",
            "original_phrase": "go"
        }
        
        result = error_processing_service._generate_specific_key_point(error_details)
        
        assert result == "過去式動詞錯誤: go"

    def test_generate_specific_key_point_without_phrase(
        self,
        error_processing_service
    ):
        """測試沒有原始短語的知識點描述"""
        error_details = {
            "key_point": "語法結構錯誤",
            "original_phrase": ""
        }
        
        result = error_processing_service._generate_specific_key_point(error_details)
        
        assert result == "語法結構錯誤"

    def test_generate_specific_key_point_whitespace_phrase(
        self,
        error_processing_service
    ):
        """測試只有空白字符的原始短語"""
        error_details = {
            "key_point": "標點符號錯誤",
            "original_phrase": "   "
        }
        
        result = error_processing_service._generate_specific_key_point(error_details)
        
        assert result == "標點符號錯誤"


class TestFindOrUpdateExistingPoint:
    """測試查找或更新現有知識點"""

    def test_find_existing_point_new_mode(
        self,
        error_processing_service,
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試在新題模式下找到現有知識點"""
        mock_knowledge_manager._find_knowledge_point.return_value = sample_knowledge_point
        
        result = error_processing_service.find_or_update_existing_point(
            key_point="過去式動詞錯誤: go",
            original_phrase="go",
            correction="went",
            chinese_sentence="我昨天去了學校",
            user_answer="I go to school yesterday",
            correct_answer="I went to school yesterday",
            practice_mode="new"
        )
        
        assert result == sample_knowledge_point
        sample_knowledge_point.update_mastery.assert_called_once_with(is_correct=False)
        mock_knowledge_manager._save_knowledge.assert_called_once()

    def test_find_existing_point_review_mode(
        self,
        error_processing_service,
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試在複習模式下找到現有知識點"""
        mock_knowledge_manager._find_knowledge_point.return_value = sample_knowledge_point
        
        result = error_processing_service.find_or_update_existing_point(
            key_point="過去式動詞錯誤: go",
            original_phrase="go",
            correction="went",
            chinese_sentence="我昨天去了學校",
            user_answer="I go to school yesterday",
            correct_answer="I went to school yesterday",
            practice_mode="review"
        )
        
        assert result == sample_knowledge_point
        # 驗證複習例句被添加
        assert len(sample_knowledge_point.review_examples) > 0
        
        # 驗證最新添加的複習例句
        latest_example = sample_knowledge_point.review_examples[-1]
        assert latest_example.chinese_sentence == "我昨天去了學校"
        assert latest_example.user_answer == "I go to school yesterday"
        assert latest_example.is_correct is False

    def test_no_existing_point_found(
        self,
        error_processing_service,
        mock_knowledge_manager
    ):
        """測試沒有找到現有知識點"""
        mock_knowledge_manager._find_knowledge_point.return_value = None
        
        result = error_processing_service.find_or_update_existing_point(
            key_point="新的語法錯誤",
            original_phrase="new_phrase",
            correction="corrected_phrase",
            chinese_sentence="測試句子",
            user_answer="test answer",
            correct_answer="correct answer",
            practice_mode="new"
        )
        
        assert result is None


class TestCreateKnowledgePointFromError:
    """測試從錯誤創建知識點"""

    def test_create_knowledge_point_from_error(
        self,
        error_processing_service,
        mock_knowledge_manager
    ):
        """測試成功創建知識點"""
        error_details = {
            "key_point": "過去式動詞錯誤",
            "original_phrase": "go",
            "correction": "went",
            "explanation": "過去式應該用 went"
        }
        
        mock_knowledge_manager._get_next_id.return_value = 5
        
        result = error_processing_service.create_knowledge_point_from_error(
            error_details=error_details,
            category=ErrorCategory.SYSTEMATIC,
            subtype="verb_tense",
            specific_key_point="過去式動詞錯誤: go",
            chinese_sentence="我昨天去了學校",
            user_answer="I go to school yesterday",
            correct_answer="I went to school yesterday"
        )
        
        # 驗證知識點被創建
        assert result.id == 5
        assert result.key_point == "過去式動詞錯誤: go"
        assert result.category == ErrorCategory.SYSTEMATIC
        assert result.subtype == "verb_tense"
        assert result.explanation == "過去式應該用 went"
        assert result.original_phrase == "go"
        assert result.correction == "went"
        
        # 驗證原始錯誤被記錄
        assert result.original_error is not None
        assert result.original_error.chinese_sentence == "我昨天去了學校"
        assert result.original_error.user_answer == "I go to school yesterday"
        assert result.original_error.correct_answer == "I went to school yesterday"
        
        # 驗證知識點被添加到管理器
        mock_knowledge_manager.knowledge_points.append.assert_called_once_with(result)
        mock_knowledge_manager._save_knowledge.assert_called_once()


class TestEdgeCases:
    """測試邊界情況"""

    def test_empty_error_list(
        self,
        error_processing_service
    ):
        """測試空錯誤列表"""
        feedback = {
            "error_analysis": [],
            "overall_suggestion": "Perfect!"
        }
        
        result = error_processing_service.process_errors(
            chinese_sentence="完美句子",
            user_answer="Perfect sentence",
            feedback=feedback
        )
        
        assert result.success is True
        assert len(result.data) == 0

    def test_malformed_error_data(
        self,
        error_processing_service
    ):
        """測試格式錯誤的錯誤數據"""
        feedback = {
            "error_analysis": [
                {
                    # 缺少必要字段
                    "some_field": "some_value"
                }
            ]
        }
        
        result = error_processing_service.process_errors(
            chinese_sentence="測試句子",
            user_answer="test sentence",
            feedback=feedback
        )
        
        assert result.success is True
        # 應該能處理，但可能創建的知識點信息不完整

    def test_very_long_sentences(
        self,
        error_processing_service,
        sample_error_data
    ):
        """測試很長的句子"""
        long_sentence = "這是一個非常非常長的中文句子，" * 50
        long_answer = "This is a very very long English sentence, " * 50
        
        result = error_processing_service.process_single_error(
            chinese_sentence=long_sentence,
            user_answer=long_answer,
            error=sample_error_data,
            correct_answer=long_answer.replace("very", "extremely"),
            practice_mode="new"
        )
        
        assert result.success is True

    def test_unicode_characters(
        self,
        error_processing_service,
        sample_error_data
    ):
        """測試Unicode字符處理"""
        result = error_processing_service.process_single_error(
            chinese_sentence="我喜歡🍎和🍌",
            user_answer="I like 🍎 and 🍌",
            error=sample_error_data,
            correct_answer="I like apples and bananas",
            practice_mode="new"
        )
        
        assert result.success is True


@pytest.mark.integration
class TestErrorProcessingServiceIntegration:
    """整合測試"""

    def test_complete_error_processing_workflow(
        self,
        error_processing_service,
        sample_feedback,
        mock_knowledge_manager
    ):
        """測試完整的錯誤處理工作流程"""
        # 確保沒有現有知識點
        mock_knowledge_manager._find_knowledge_point.return_value = None
        mock_knowledge_manager._get_next_id.side_effect = [1, 2]
        
        # 處理錯誤
        result = error_processing_service.process_errors(
            chinese_sentence="我昨天去了學校",
            user_answer="I go in school yesterday",
            feedback=sample_feedback,
            practice_mode="new"
        )
        
        # 驗證結果
        assert result.success is True
        assert len(result.data) == 2
        
        # 驗證兩個知識點都被創建
        assert mock_knowledge_manager.knowledge_points.append.call_count == 2
        assert mock_knowledge_manager._save_knowledge.call_count == 2

    def test_mixed_new_and_existing_errors(
        self,
        error_processing_service,
        sample_feedback,
        sample_knowledge_point,
        mock_knowledge_manager
    ):
        """測試混合新舊錯誤的處理"""
        # 設置第一個錯誤找到現有知識點，第二個錯誤創建新知識點
        mock_knowledge_manager._find_knowledge_point.side_effect = [
            sample_knowledge_point,  # 第一個錯誤找到現有
            None  # 第二個錯誤沒找到
        ]
        mock_knowledge_manager._get_next_id.return_value = 3
        
        result = error_processing_service.process_errors(
            chinese_sentence="我昨天去了學校",
            user_answer="I go in school yesterday",
            feedback=sample_feedback,
            practice_mode="new"
        )
        
        assert result.success is True
        assert len(result.data) == 2
        
        # 驗證第一個知識點被更新
        sample_knowledge_point.update_mastery.assert_called_once()
        
        # 驗證第二個知識點被創建
        mock_knowledge_manager.knowledge_points.append.assert_called_once()

    def test_performance_with_many_errors(
        self,
        error_processing_service,
        mock_knowledge_manager
    ):
        """測試處理大量錯誤的性能"""
        # 創建大量錯誤
        many_errors = []
        for i in range(100):
            many_errors.append({
                "key_point_summary": f"錯誤{i}",
                "original_phrase": f"phrase{i}",
                "correction": f"corrected{i}",
                "explanation": f"解釋{i}"
            })
        
        feedback = {
            "error_analysis": many_errors,
            "overall_suggestion": "Many corrections needed"
        }
        
        mock_knowledge_manager._find_knowledge_point.return_value = None
        mock_knowledge_manager._get_next_id.side_effect = range(1, 101)
        
        result = error_processing_service.process_errors(
            chinese_sentence="複雜的測試句子",
            user_answer="Complex test sentence",
            feedback=feedback,
            practice_mode="new"
        )
        
        assert result.success is True
        assert len(result.data) == 100
        assert "成功處理 100 個錯誤" in result.message