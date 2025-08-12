"""
業務邏輯測試示例
展示如何使用測試框架測試核心業務功能
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock

from core.knowledge import KnowledgePoint, KnowledgeManager
from core.ai_service import AIService
from core.response import APIResponse

from tests.factories import (
    KnowledgePointFactory,
    create_knowledge_points_for_review,
    create_failed_grading_response
)
from tests.mocks import (
    MockAIService,
    create_mock_knowledge_repository,
    FileOperationMockContext
)
from tests.utils import (
    assert_knowledge_point_valid,
    assert_response_success,
    test_environment,
    mock_environment_variables,
    create_test_environment_vars
)


class TestKnowledgeManager:
    """知識點管理器業務邏輯測試"""

    @pytest.fixture
    def knowledge_manager(self, mock_settings):
        """創建知識點管理器實例"""
        with FileOperationMockContext() as file_ctx:
            # 初始化測試數據
            file_ctx.json_handler.write_json(
                str(mock_settings.KNOWLEDGE_FILE),
                {
                    "version": "3.0",
                    "knowledge_points": []
                }
            )
            
            manager = KnowledgeManager(str(mock_settings.KNOWLEDGE_FILE))
            yield manager
    
    @pytest.mark.unit
    def test_add_knowledge_point(self, knowledge_manager):
        """測試添加知識點"""
        # 準備測試數據
        kp = KnowledgePointFactory.build()
        
        # 執行操作
        response = knowledge_manager.add_knowledge_point(kp)
        
        # 驗證結果
        assert_response_success(response)
        
        # 驗證知識點已添加
        added_kp = knowledge_manager.get_knowledge_point(kp.knowledge_point_id)
        assert added_kp is not None
        assert added_kp.knowledge_point_id == kp.knowledge_point_id
    
    @pytest.mark.unit
    def test_update_mastery_level(self, knowledge_manager):
        """測試掌握度更新"""
        # 添加測試知識點
        kp = KnowledgePointFactory.build(correct_count=2, incorrect_count=3)
        knowledge_manager.add_knowledge_point(kp)
        
        # 模擬正確答案
        response = knowledge_manager.update_mastery_level(
            kp.knowledge_point_id, 
            is_correct=True
        )
        
        # 驗證結果
        assert_response_success(response)
        
        # 檢查掌握度更新
        updated_kp = knowledge_manager.get_knowledge_point(kp.knowledge_point_id)
        assert updated_kp.correct_count == 3
        assert updated_kp.mastery_level == 3/6  # 3正確 / (3正確 + 3錯誤)
    
    @pytest.mark.integration
    def test_get_review_candidates(self, knowledge_manager):
        """測試獲取複習候選知識點"""
        # 添加需要複習的知識點
        review_kps = create_knowledge_points_for_review(5)
        for kp in review_kps:
            knowledge_manager.add_knowledge_point(kp)
        
        # 獲取複習候選
        candidates = knowledge_manager.get_review_candidates(limit=3)
        
        # 驗證結果
        assert len(candidates) <= 3
        for candidate in candidates:
            assert_knowledge_point_valid(candidate)
            # 驗證確實需要複習（掌握度較低）
            assert candidate.mastery_level < 0.7


class TestAIServiceIntegration:
    """AI 服務整合測試"""
    
    @pytest.fixture
    def ai_service_with_mock_api(self):
        """使用 Mock API 的 AI 服務"""
        from tests.mocks import ExternalAPIMockContext, create_mock_gemini_api
        
        mock_gemini = create_mock_gemini_api("normal")
        
        with ExternalAPIMockContext(mock_gemini) as api_ctx:
            with mock_environment_variables(create_test_environment_vars()):
                service = AIService()
                yield service
    
    @pytest.mark.asyncio
    @pytest.mark.ai
    async def test_generate_practice_question(self, ai_service_with_mock_api):
        """測試生成練習題目"""
        ai_service = ai_service_with_mock_api
        
        # 生成題目
        result = await ai_service.generate_practice_question(
            difficulty="medium"
        )
        
        # 驗證結果格式
        assert "chinese_sentence" in result
        assert "knowledge_points" in result
        assert isinstance(result["knowledge_points"], list)
        assert len(result["knowledge_points"]) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.ai
    async def test_grade_translation_with_errors(self, ai_service_with_mock_api):
        """測試包含錯誤的翻譯批改"""
        ai_service = ai_service_with_mock_api
        
        # 批改明顯錯誤的翻譯
        result = await ai_service.grade_translation(
            chinese_sentence="我昨天去了圖書館。",
            user_answer="I go to library yesterday.",  # 時態和冠詞錯誤
            correct_answer="I went to the library yesterday."
        )
        
        # 驗證批改結果
        assert "is_correct" in result
        assert "feedback" in result
        
        # 應該檢測出錯誤
        if not result["is_correct"]:
            assert "knowledge_points" in result
            assert len(result["knowledge_points"]) > 0


class TestEndToEndWorkflow:
    """端到端工作流程測試"""
    
    @pytest.fixture
    def complete_test_environment(self, mock_settings):
        """完整的測試環境設置"""
        with test_environment() as cleaner:
            # 設置文件系統
            with FileOperationMockContext() as file_ctx:
                file_ctx.json_handler.write_json(
                    str(mock_settings.KNOWLEDGE_FILE),
                    {"version": "3.0", "knowledge_points": []}
                )
                
                file_ctx.json_handler.write_json(
                    str(mock_settings.PRACTICE_LOG_FILE),
                    {"version": "1.0", "records": []}
                )
                
                # 創建管理器實例
                knowledge_manager = KnowledgeManager(str(mock_settings.KNOWLEDGE_FILE))
                
                # 創建 Mock AI 服務
                ai_service = MockAIService(failure_rate=0.0)
                
                yield {
                    "knowledge_manager": knowledge_manager,
                    "ai_service": ai_service,
                    "cleaner": cleaner
                }
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_practice_flow(self, complete_test_environment):
        """測試完整的練習流程"""
        env = complete_test_environment
        knowledge_manager = env["knowledge_manager"]
        ai_service = env["ai_service"]
        
        # 1. 生成練習題目
        question_result = await ai_service.generate_practice_question(
            difficulty="easy"
        )
        
        chinese_sentence = question_result["chinese_sentence"]
        expected_knowledge_points = question_result["knowledge_points"]
        
        # 2. 模擬用戶錯誤答案
        user_answer = "I go library yesterday."  # 故意錯誤
        correct_answer = "I went to the library yesterday."
        
        # 3. AI 批改
        grading_result = await ai_service.grade_translation(
            chinese_sentence=chinese_sentence,
            user_answer=user_answer,
            correct_answer=correct_answer
        )
        
        # 4. 如果有錯誤，添加知識點
        if not grading_result["is_correct"] and "knowledge_points" in grading_result:
            for kp_data in grading_result["knowledge_points"]:
                # 創建知識點
                kp = KnowledgePointFactory.build(
                    title=kp_data["title"],
                    error_category=kp_data["error_category"],
                    tags=expected_knowledge_points
                )
                
                # 添加到管理器
                add_response = knowledge_manager.add_knowledge_point(kp)
                assert_response_success(add_response)
        
        # 5. 驗證工作流程完成
        all_kps = knowledge_manager.get_all_knowledge_points()
        if not grading_result["is_correct"]:
            assert len(all_kps) > 0
            
            # 驗證知識點質量
            for kp in all_kps:
                assert_knowledge_point_valid(kp)
    
    @pytest.mark.integration 
    def test_review_cycle(self, complete_test_environment):
        """測試複習周期"""
        env = complete_test_environment
        knowledge_manager = env["knowledge_manager"]
        
        # 1. 添加一些需要複習的知識點
        review_kps = create_knowledge_points_for_review(3)
        for kp in review_kps:
            knowledge_manager.add_knowledge_point(kp)
        
        # 2. 獲取複習候選
        candidates = knowledge_manager.get_review_candidates(limit=2)
        assert len(candidates) == 2
        
        # 3. 模擬複習練習（正確答案）
        for candidate in candidates:
            update_response = knowledge_manager.update_mastery_level(
                candidate.knowledge_point_id,
                is_correct=True
            )
            assert_response_success(update_response)
        
        # 4. 驗證掌握度提升
        for candidate in candidates:
            updated_kp = knowledge_manager.get_knowledge_point(candidate.knowledge_point_id)
            assert updated_kp.correct_count > candidate.correct_count
            assert updated_kp.mastery_level > candidate.mastery_level


class TestErrorHandling:
    """錯誤處理測試"""
    
    @pytest.mark.unit
    def test_file_not_found_handling(self):
        """測試文件不存在的處理"""
        # 嘗試載入不存在的文件
        with pytest.raises(FileNotFoundError):
            KnowledgeManager("non_existent_file.json")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ai_service_error_handling(self):
        """測試 AI 服務錯誤處理"""
        # 創建容易出錯的 Mock AI 服務
        ai_service = MockAIService(failure_rate=1.0, enable_api_errors=True)
        
        # 驗證錯誤處理
        with pytest.raises(Exception):
            await ai_service.generate_practice_question()
    
    @pytest.mark.integration
    def test_data_corruption_recovery(self, mock_settings):
        """測試數據損壞恢復"""
        with FileOperationMockContext() as file_ctx:
            # 寫入損壞的 JSON
            file_ctx.fs.write_file(
                str(mock_settings.KNOWLEDGE_FILE),
                "invalid json content"
            )
            
            # 驗證適當的錯誤處理
            with pytest.raises((ValueError, json.JSONDecodeError)):
                KnowledgeManager(str(mock_settings.KNOWLEDGE_FILE))


if __name__ == "__main__":
    print("Example business logic tests created!")
    print("Run with: pytest tests/example_business_logic_test.py -v")