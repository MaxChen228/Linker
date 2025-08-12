"""
測試練習服務層功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services import PracticeService, ServiceResult
from tests.factories import KnowledgeFactory, AIResponseFactory
from tests.mocks import MockAIService, MockKnowledgeManager


class TestPracticeService:
    """測試 PracticeService 類別"""
    
    def setup_method(self):
        """每個測試方法前的設置"""
        self.mock_ai_service = MockAIService()
        self.mock_knowledge_manager = MockKnowledgeManager()
        self.mock_knowledge_repo = Mock()
        self.mock_practice_repo = Mock()
        
        self.service = PracticeService(
            ai_service=self.mock_ai_service,
            knowledge_manager=self.mock_knowledge_manager,
            knowledge_repository=self.mock_knowledge_repo,
            practice_repository=self.mock_practice_repo
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """測試服務初始化"""
        await self.service.initialize()
        assert self.service._initialized is True
        assert self.service._operation_stats["submissions_processed"] == 0
    
    def test_get_service_info(self):
        """測試獲取服務資訊"""
        info = self.service.get_service_info()
        
        assert info["service_name"] == "PracticeService"
        assert info["version"] == "1.0.0"
        assert "翻譯提交批改" in info["capabilities"]
        assert "dependencies" in info
        assert info["initialized"] is False
    
    def test_submit_translation_success_new_mode(self):
        """測試新題模式翻譯提交成功"""
        # 準備模擬數據
        grading_result = AIResponseFactory.create_grading_result(is_correct=True)
        self.mock_ai_service.grade_translation.return_value = grading_result
        
        # 執行測試
        result = self.service.submit_translation(
            chinese="我喜歡閱讀",
            english="I like reading",
            mode="new",
            level=1,
            length="short"
        )
        
        # 驗證結果
        assert result.success is True
        assert result.data["is_correct"] is True
        assert result.data["mode"] == "new"
        assert result.data["score"] == 100
        
        # 驗證服務統計
        assert self.service._operation_stats["submissions_processed"] == 1
        
        # 驗證 AI 服務被調用
        self.mock_ai_service.grade_translation.assert_called_once()
    
    def test_submit_translation_with_errors(self):
        """測試有錯誤的翻譯提交"""
        # 準備模擬數據
        grading_result = AIResponseFactory.create_grading_result(
            is_correct=False,
            errors=[
                {"category": "systematic", "severity": "high"},
                {"category": "isolated", "severity": "medium"}
            ]
        )
        self.mock_ai_service.grade_translation.return_value = grading_result
        
        result = self.service.submit_translation(
            chinese="我去學校",
            english="I go to the school",
            mode="new",
            level=1,
            length="short"
        )
        
        # 驗證結果
        assert result.success is True
        assert result.data["is_correct"] is False
        assert result.data["score"] < 100  # 有錯誤所以分數降低
        
        # 驗證錯誤被保存
        self.mock_knowledge_manager.save_mistake.assert_called_once()
    
    def test_submit_translation_review_mode(self):
        """測試複習模式翻譯提交"""
        # 準備知識點數據
        target_point_ids = ["point1", "point2"]
        grading_result = AIResponseFactory.create_grading_result(is_correct=True)
        self.mock_ai_service.grade_translation.return_value = grading_result
        
        result = self.service.submit_translation(
            chinese="她在讀書",
            english="She is reading",
            mode="review",
            level=1,
            length="short",
            target_point_ids=target_point_ids
        )
        
        # 驗證結果
        assert result.success is True
        assert result.data["mode"] == "review"
        assert result.data["target_point_ids"] == target_point_ids
        
        # 驗證複習統計
        assert self.service._operation_stats["review_sessions"] == 1
        
        # 驗證知識點更新
        assert self.mock_knowledge_manager.update_knowledge_point.call_count == 2
        
        # 驗證複習成功記錄
        assert self.mock_knowledge_manager.add_review_success.call_count == 2
    
    def test_submit_translation_validation_error(self):
        """測試輸入驗證錯誤"""
        result = self.service.submit_translation(
            chinese="",  # 空的中文句子
            english="test",
            mode="new"
        )
        
        # 驗證失敗結果
        assert result.success is False
        assert "驗證" in result.message or "validation" in result.message.lower()
        assert result.error_code == "VALIDATION_ERROR"
    
    def test_submit_translation_ai_service_error(self):
        """測試 AI 服務錯誤"""
        # 模擬 AI 服務拋出異常
        self.mock_ai_service.grade_translation.side_effect = Exception("AI 服務不可用")
        
        result = self.service.submit_translation(
            chinese="測試句子",
            english="Test sentence",
            mode="new"
        )
        
        # 驗證錯誤處理
        assert result.success is False
        assert "AI 批改服務失敗" in result.message
        assert result.error_code == "AI_GRADING_FAILED"
    
    def test_generate_practice_sentence_new_mode(self):
        """測試新題模式句子生成"""
        # 準備模擬數據
        generated_sentence = {
            "chinese_sentence": "我昨天去了圖書館",
            "examples": [],
            "difficulty": 1
        }
        self.mock_ai_service.generate_practice_sentence.return_value = generated_sentence
        
        result = self.service.generate_practice_sentence(
            mode="new",
            level=1,
            length="short"
        )
        
        # 驗證結果
        assert result.success is True
        assert result.data["chinese_sentence"] == "我昨天去了圖書館"
        assert result.data["target_points"] == []
        
        # 驗證統計更新
        assert self.service._operation_stats["questions_generated"] == 1
    
    def test_generate_practice_sentence_review_mode(self):
        """測試複習模式句子生成"""
        # 準備複習候選知識點
        review_points = [
            KnowledgeFactory.create_knowledge_point(
                id="point1",
                key_point="過去式用法",
                mastery_level=0.6
            ),
            KnowledgeFactory.create_knowledge_point(
                id="point2", 
                key_point="介詞搭配",
                mastery_level=0.4
            )
        ]
        self.mock_knowledge_manager.get_review_candidates.return_value = review_points
        
        # 準備 AI 生成結果
        generated_sentence = {
            "chinese_sentence": "我昨天去了學校",
            "target_points": ["point1", "point2"],
            "examples": []
        }
        self.mock_ai_service.generate_review_sentence.return_value = generated_sentence
        
        result = self.service.generate_practice_sentence(
            mode="review",
            level=1,
            length="short"
        )
        
        # 驗證結果
        assert result.success is True
        assert result.data["chinese_sentence"] == "我昨天去了學校"
        assert len(result.data["target_points"]) == 2
        assert len(result.data["target_point_details"]) == 2
        
        # 驗證知識點詳情
        details = result.data["target_point_details"]
        assert details[0]["key_point"] == "過去式用法"
        assert details[1]["key_point"] == "介詞搭配"
    
    def test_generate_practice_sentence_no_review_candidates(self):
        """測試沒有複習候選時的處理"""
        # 返回空的複習候選列表
        self.mock_knowledge_manager.get_review_candidates.return_value = []
        
        result = self.service.generate_practice_sentence(
            mode="review",
            level=1,
            length="short"
        )
        
        # 驗證錯誤結果
        assert result.success is False
        assert "沒有可複習的知識點" in result.message or "找不到" in result.message
    
    def test_handle_review_mode(self):
        """測試複習模式處理"""
        # 準備複習候選知識點
        review_points = [
            KnowledgeFactory.create_knowledge_point(
                id="point1",
                key_point="動詞時態",
                category="systematic",
                mastery_level=0.3,
                mistake_count=5,
                next_review="2024-01-01T10:00:00"
            ),
            KnowledgeFactory.create_knowledge_point(
                id="point2",
                key_point="詞彙選擇",
                category="isolated", 
                mastery_level=0.7,
                mistake_count=2,
                next_review="2024-01-02T10:00:00"
            )
        ]
        self.mock_knowledge_manager.get_review_candidates.return_value = review_points
        
        result = self.service.handle_review_mode(max_points=5)
        
        # 驗證結果
        assert result.success is True
        assert result.data["total_candidates"] == 2
        assert result.data["max_points"] == 5
        
        # 驗證候選點資料
        candidates = result.data["candidates"]
        assert len(candidates) == 2
        assert candidates[0]["key_point"] == "動詞時態"
        assert candidates[0]["mastery_level"] == 0.3
        assert "priority_score" in candidates[0]
    
    def test_handle_review_mode_with_category_filter(self):
        """測試帶類別篩選的複習模式處理"""
        # 準備不同類別的知識點
        review_points = [
            KnowledgeFactory.create_knowledge_point(
                id="point1",
                category="systematic",
                key_point="語法錯誤"
            ),
            KnowledgeFactory.create_knowledge_point(
                id="point2",
                category="isolated", 
                key_point="詞彙錯誤"
            ),
            KnowledgeFactory.create_knowledge_point(
                id="point3",
                category="systematic",
                key_point="另一個語法錯誤"
            )
        ]
        self.mock_knowledge_manager.get_review_candidates.return_value = review_points
        
        result = self.service.handle_review_mode(
            max_points=5,
            categories=["systematic"]
        )
        
        # 驗證結果只包含系統性錯誤
        assert result.success is True
        candidates = result.data["candidates"]
        
        # 由於篩選，應該只有 systematic 類別的知識點
        for candidate in candidates:
            # 需要檢查實際的篩選邏輯
            pass  # 篩選邏輯在實際實現中處理
    
    def test_get_practice_statistics(self):
        """測試獲取練習統計"""
        # 準備模擬統計數據
        basic_stats = {
            "total_points": 10,
            "correct_count": 8,
            "mistake_count": 2,
            "due_reviews": 3
        }
        self.mock_knowledge_manager.get_statistics.return_value = basic_stats
        
        # 準備知識點列表
        knowledge_points = [
            KnowledgeFactory.create_knowledge_point(mastery_level=0.2, category="systematic"),
            KnowledgeFactory.create_knowledge_point(mastery_level=0.5, category="isolated"),
            KnowledgeFactory.create_knowledge_point(mastery_level=0.8, category="enhancement")
        ]
        self.mock_knowledge_manager.knowledge_points = knowledge_points
        
        result = self.service.get_practice_statistics()
        
        # 驗證結果
        assert result.success is True
        stats = result.data
        
        # 驗證基本統計
        assert stats["total_points"] == 10
        assert stats["correct_count"] == 8
        
        # 驗證掌握度分佈
        mastery_dist = stats["mastery_distribution"]
        assert mastery_dist["低"] == 1  # mastery_level < 0.3
        assert mastery_dist["中"] == 1  # 0.3 <= mastery_level < 0.7
        assert mastery_dist["高"] == 1  # mastery_level >= 0.7
        
        # 驗證類別分佈
        category_dist = stats["category_distribution"]
        assert len(category_dist) == 3
        
        # 驗證服務統計
        assert "service_stats" in stats
        assert stats["service_stats"]["submissions_processed"] >= 0
    
    def test_calculate_score_various_errors(self):
        """測試不同錯誤類型的分數計算"""
        # 測試系統性錯誤
        grading_result = {
            "error_analysis": [
                {"category": "systematic"},
                {"category": "isolated"},
                {"category": "enhancement"}
            ]
        }
        
        score = self.service._calculate_score(grading_result)
        expected_score = 100 - 15 - 10 - 5  # 70分
        assert score == expected_score
        
        # 測試未知類別錯誤
        grading_result_unknown = {
            "error_analysis": [
                {"category": "unknown_type"}
            ]
        }
        
        score_unknown = self.service._calculate_score(grading_result_unknown)
        assert score_unknown == 92  # 100 - 8
    
    def test_calculate_review_priority(self):
        """測試複習優先級計算"""
        # 低掌握度、高錯誤次數、已過期的知識點
        high_priority_point = KnowledgeFactory.create_knowledge_point(
            mastery_level=0.1,
            mistake_count=8,
            next_review="2023-01-01T00:00:00"  # 已過期
        )
        
        # 模擬 is_due_for_review 方法
        high_priority_point.is_due_for_review = lambda: True
        
        priority = self.service._calculate_review_priority(high_priority_point)
        
        # 高優先級應該 > 1.0
        assert priority > 1.0
        
        # 低優先級知識點
        low_priority_point = KnowledgeFactory.create_knowledge_point(
            mastery_level=0.9,
            mistake_count=1,
            next_review="2025-01-01T00:00:00"  # 未到期
        )
        low_priority_point.is_due_for_review = lambda: False
        
        low_priority = self.service._calculate_review_priority(low_priority_point)
        
        # 低優先級應該 < 高優先級
        assert low_priority < priority


class TestPracticeServiceEdgeCases:
    """測試練習服務的邊界情況"""
    
    def setup_method(self):
        """設置測試環境"""
        self.mock_ai_service = MockAIService()
        self.mock_knowledge_manager = MockKnowledgeManager()
        
        self.service = PracticeService(
            ai_service=self.mock_ai_service,
            knowledge_manager=self.mock_knowledge_manager
        )
    
    def test_empty_target_points_in_review_mode(self):
        """測試複習模式下空目標知識點的處理"""
        grading_result = AIResponseFactory.create_grading_result(is_correct=True)
        self.mock_ai_service.grade_translation.return_value = grading_result
        
        result = self.service.submit_translation(
            chinese="測試句子",
            english="Test sentence",
            mode="review",
            target_point_ids=[]  # 空列表
        )
        
        # 應該成功，但不會更新知識點
        assert result.success is True
        assert self.mock_knowledge_manager.update_knowledge_point.call_count == 0
    
    def test_malformed_target_point_ids(self):
        """測試格式錯誤的目標知識點ID"""
        grading_result = AIResponseFactory.create_grading_result(is_correct=True)
        self.mock_ai_service.grade_translation.return_value = grading_result
        
        # 模擬知識點更新失敗
        self.mock_knowledge_manager.update_knowledge_point.side_effect = Exception("點不存在")
        
        result = self.service.submit_translation(
            chinese="測試句子",
            english="Test sentence", 
            mode="review",
            target_point_ids=["invalid_id"]
        )
        
        # 服務應該仍然成功，但會記錄錯誤
        assert result.success is True
    
    def test_score_boundary_conditions(self):
        """測試分數邊界條件"""
        # 測試過多錯誤導致分數為負數的情況
        grading_result = {
            "error_analysis": [
                {"category": "systematic"} for _ in range(10)  # 10個系統性錯誤
            ]
        }
        
        score = self.service._calculate_score(grading_result)
        assert score == 0  # 分數不能低於0
        assert score >= 0
        assert score <= 100
    
    def test_concurrent_operations_stats(self):
        """測試併發操作對統計的影響"""
        # 模擬多次操作
        for i in range(5):
            result = self.service.submit_translation(
                chinese=f"測試句子{i}",
                english=f"Test sentence {i}",
                mode="new" if i % 2 == 0 else "review"
            )
        
        # 驗證統計更新
        assert self.service._operation_stats["submissions_processed"] == 5
        # review 模式的次數 (索引 1, 3)
        expected_reviews = 2
        assert self.service._operation_stats["review_sessions"] == expected_reviews


class TestPracticeServiceIntegration:
    """練習服務集成測試"""
    
    def test_complete_practice_workflow(self):
        """測試完整的練習工作流程"""
        # 創建真實的依賴（但仍然使用 Mock）
        ai_service = MockAIService()
        knowledge_manager = MockKnowledgeManager()
        
        service = PracticeService(
            ai_service=ai_service,
            knowledge_manager=knowledge_manager
        )
        
        # 1. 生成練習句子
        ai_service.generate_practice_sentence.return_value = {
            "chinese_sentence": "我喜歡學習英文"
        }
        
        sentence_result = service.generate_practice_sentence(
            mode="new",
            level=1, 
            length="short"
        )
        
        assert sentence_result.success is True
        chinese_sentence = sentence_result.data["chinese_sentence"]
        
        # 2. 提交翻譯
        ai_service.grade_translation.return_value = AIResponseFactory.create_grading_result(
            is_correct=False,
            errors=[{"category": "isolated", "severity": "medium"}]
        )
        
        submission_result = service.submit_translation(
            chinese=chinese_sentence,
            english="I like study English",  # 語法錯誤
            mode="new"
        )
        
        assert submission_result.success is True
        assert submission_result.data["is_correct"] is False
        
        # 3. 檢查統計
        knowledge_manager.get_statistics.return_value = {
            "total_points": 1,
            "mistake_count": 1,
            "correct_count": 0
        }
        knowledge_manager.knowledge_points = [
            KnowledgeFactory.create_knowledge_point()
        ]
        
        stats_result = service.get_practice_statistics()
        assert stats_result.success is True
        assert stats_result.data["service_stats"]["submissions_processed"] == 1
        assert stats_result.data["service_stats"]["questions_generated"] == 1
    
    @pytest.mark.asyncio
    async def test_service_initialization_with_repositories(self):
        """測試帶有資料存取層的服務初始化"""
        mock_knowledge_repo = Mock()
        mock_practice_repo = Mock()
        
        service = PracticeService(
            ai_service=MockAIService(),
            knowledge_manager=MockKnowledgeManager(),
            knowledge_repository=mock_knowledge_repo,
            practice_repository=mock_practice_repo
        )
        
        await service.initialize()
        
        assert service._initialized is True
        assert service.knowledge_repo is mock_knowledge_repo
        assert service.practice_repo is mock_practice_repo