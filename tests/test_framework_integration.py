"""
測試框架整合驗證
驗證測試環境設置正確，與現有代碼相容
"""

import pytest
import asyncio
from unittest.mock import patch

# 測試工廠和 Mock 的導入
from tests.factories import (
    KnowledgePointFactory, 
    create_systematic_knowledge_point,
    create_successful_grading_response
)
from tests.mocks import (
    create_mock_ai_service,
    create_mock_knowledge_repository
)
from tests.utils import (
    assert_knowledge_point_valid,
    assert_response_success,
    test_environment
)


@pytest.mark.unit
def test_knowledge_point_factory():
    """測試知識點工廠功能"""
    # 使用工廠創建知識點
    kp = KnowledgePointFactory.build()
    
    # 驗證基本屬性
    assert kp.id > 0
    assert kp.key_point
    assert kp.explanation
    from core.error_types import ErrorCategory
    assert isinstance(kp.category, ErrorCategory)
    
    # 使用自定義斷言驗證
    assert_knowledge_point_valid(kp)


@pytest.mark.unit
def test_specialized_knowledge_point_creation():
    """測試專門化知識點創建"""
    # 創建系統性錯誤知識點
    systematic_kp = create_systematic_knowledge_point()
    
    from core.error_types import ErrorCategory
    assert systematic_kp.category == ErrorCategory.SYSTEMATIC
    assert "時態" in systematic_kp.key_point
    assert_knowledge_point_valid(systematic_kp)


@pytest.mark.unit
@pytest.mark.mock
def test_mock_repository_functionality():
    """測試 Mock Repository 功能"""
    # 創建 Mock Repository
    repo = create_mock_knowledge_repository("normal")
    
    # 測試載入功能
    knowledge_points = repo.load_all()
    assert len(knowledge_points) == 10  # "normal" 場景預設創建 10 個
    
    # 測試保存功能
    new_kp = KnowledgePointFactory.build()
    response = repo.save(new_kp)
    assert_response_success(response)
    
    # 驗證知識點已保存
    saved_kp = repo.get_by_id(new_kp.id)
    assert saved_kp is not None
    assert saved_kp.id == new_kp.id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_ai_service():
    """測試 Mock AI 服務"""
    ai_service = create_mock_ai_service("normal")
    
    # 測試生成題目
    response = await ai_service.generate_practice_question(
        difficulty="medium",
        knowledge_points=["past_tense"]
    )
    
    assert "chinese_sentence" in response
    assert "knowledge_points" in response
    assert "past_tense" in response["knowledge_points"]
    
    # 測試批改功能
    grading_response = await ai_service.grade_translation(
        chinese_sentence="我昨天去了圖書館。",
        user_answer="I go to library yesterday.",
        correct_answer="I went to the library yesterday."
    )
    
    assert "is_correct" in grading_response
    assert "feedback" in grading_response


@pytest.mark.unit
def test_environment_cleaner():
    """測試環境清理功能"""
    with test_environment() as cleaner:
        # 創建臨時文件
        from tests.utils import create_temp_file
        
        temp_file = create_temp_file("test content")
        cleaner.register_temp_file(temp_file)
        
        assert temp_file.exists()
        
        # 創建臨時目錄
        from tests.utils import create_temp_dir
        
        temp_dir = create_temp_dir()
        cleaner.register_temp_dir(temp_dir)
        
        assert temp_dir.exists()
    
    # 驗證清理成功
    assert not temp_file.exists()
    assert not temp_dir.exists()


@pytest.mark.unit
def test_ai_response_factory():
    """測試 AI 回應工廠"""
    # 測試成功回應
    success_response = create_successful_grading_response()
    
    assert success_response["is_correct"] is True
    assert isinstance(success_response["feedback"], str)
    assert success_response["score"] >= 85
    
    # 驗證回應格式
    from tests.utils import assert_ai_response_valid
    assert_ai_response_valid(success_response, "grading")


@pytest.mark.integration
def test_fixtures_integration(sample_knowledge_point, mock_ai_service):
    """測試 fixtures 整合"""
    # 驗證 fixture 提供的知識點
    assert_knowledge_point_valid(sample_knowledge_point)
    
    # 驗證 Mock AI 服務 fixture
    assert mock_ai_service.generate_practice_question.return_value is not None


@pytest.mark.unit
def test_test_utilities():
    """測試測試工具函數"""
    from tests.utils import random_string, deep_merge_dict
    
    # 測試隨機字符串生成
    random_str = random_string(10)
    assert len(random_str) == 10
    assert random_str.isalnum()
    
    # 測試字典深度合併
    dict1 = {"a": 1, "b": {"c": 2}}
    dict2 = {"b": {"d": 3}, "e": 4}
    
    merged = deep_merge_dict(dict1, dict2)
    
    assert merged["a"] == 1
    assert merged["b"]["c"] == 2
    assert merged["b"]["d"] == 3
    assert merged["e"] == 4


@pytest.mark.unit
def test_custom_assertions():
    """測試自定義斷言"""
    from tests.utils import assert_error_category_valid
    
    from core.error_types import ErrorCategory
    
    # 測試有效分類
    assert_error_category_valid(ErrorCategory.SYSTEMATIC)
    assert_error_category_valid(ErrorCategory.ISOLATED)
    
    # 測試無效分類會拋出異常
    with pytest.raises(AssertionError):
        assert_error_category_valid("invalid_category")


@pytest.mark.unit 
def test_mock_settings_fixture(mock_settings):
    """測試 Mock 設置 fixture"""
    # 驗證臨時目錄設置
    assert mock_settings.DATA_DIR.exists()
    assert mock_settings.KNOWLEDGE_FILE.exists()
    assert mock_settings.PRACTICE_LOG_FILE.exists()
    
    # 驗證文件內容為空 JSON
    import json
    with open(mock_settings.KNOWLEDGE_FILE) as f:
        data = json.load(f)
        assert data == {}


@pytest.mark.unit
@pytest.mark.slow  
def test_timing_assertion():
    """測試時間斷言"""
    from tests.utils import assert_timing
    import time
    
    @assert_timing(min_time=0.1, max_time=0.2)
    def slow_function():
        time.sleep(0.15)
        return "done"
    
    result = slow_function()
    assert result == "done"


def test_pytest_configuration():
    """測試 pytest 配置正確性"""
    import pytest
    
    # 驗證標記配置
    markers = pytest.mark.unit, pytest.mark.integration, pytest.mark.slow
    
    # 驗證異步模式
    assert hasattr(pytest, 'mark')
    assert hasattr(pytest.mark, 'asyncio')


if __name__ == "__main__":
    # 運行基本驗證
    print("Running basic framework integration tests...")
    
    # 測試工廠
    kp = KnowledgePointFactory.build()
    print(f"✓ Knowledge point factory: {kp.title}")
    
    # 測試 Mock
    repo = create_mock_knowledge_repository("empty")
    print(f"✓ Mock repository created with {len(repo.load_all())} items")
    
    print("Framework integration test completed successfully!")