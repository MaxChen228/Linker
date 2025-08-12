"""
全局測試配置和 fixtures
提供測試環境設置、數據隔離和通用測試工具
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

import pytest
from freezegun import freeze_time

from core.knowledge import KnowledgePoint, OriginalError, ReviewExample
from core.ai_service import AIService
from core.response import APIResponse
from core.repositories.knowledge_repository import KnowledgeRepository
from core.repositories.practice_repository import PracticeRepository


@pytest.fixture(scope="session")
def event_loop():
    """創建事件循環 - session 級別，避免異步測試問題"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_data_dir():
    """創建臨時數據目錄，測試完成後自動清理"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # 創建必要的子目錄
        (temp_path / "backups").mkdir(exist_ok=True)
        yield temp_path


@pytest.fixture
def mock_settings(temp_data_dir):
    """Mock 設置，使用臨時目錄避免污染真實數據"""
    mock_settings = Mock()
    mock_settings.DATA_DIR = temp_data_dir
    mock_settings.KNOWLEDGE_FILE = temp_data_dir / "knowledge.json"
    mock_settings.PRACTICE_LOG_FILE = temp_data_dir / "practice_log.json"
    mock_settings.GRAMMAR_PATTERNS_FILE = temp_data_dir / "grammar_patterns.json"
    
    # 初始化空文件
    for file_path in [mock_settings.KNOWLEDGE_FILE, 
                      mock_settings.PRACTICE_LOG_FILE,
                      mock_settings.GRAMMAR_PATTERNS_FILE]:
        if not file_path.exists():
            file_path.write_text("{}")
    
    with patch("settings.settings", mock_settings):
        yield mock_settings


@pytest.fixture
def sample_knowledge_point():
    """創建標準的知識點測試數據"""
    from core.error_types import ErrorCategory
    
    original_error = OriginalError(
        chinese_sentence="我昨天去了圖書館。",
        user_answer="I go to library yesterday.",
        correct_answer="I went to the library yesterday.",
        timestamp="2024-01-01T10:00:00"
    )
    
    return KnowledgePoint(
        id=1,
        key_point="過去式時態錯誤: go -> went",
        category=ErrorCategory.SYSTEMATIC,
        subtype="verb_tense",
        explanation="動詞時態不一致，應該使用過去式",
        original_phrase="I go to library yesterday",
        correction="I went to the library yesterday",
        original_error=original_error,
        review_examples=[],
        correct_count=0,
        mistake_count=1,
        mastery_level=0.0,
        created_at="2024-01-01T10:00:00",
        last_seen="2024-01-01T10:00:00",
        next_review="2024-01-02T10:00:00"
    )


@pytest.fixture
def sample_review_example():
    """創建複習例句測試數據"""
    return ReviewExample(
        chinese_sentence="他上週完成了作業。",
        user_answer="He finished his homework last week.",
        correct_answer="He finished his homework last week.",
        timestamp="2024-01-02T15:00:00",
        is_correct=True
    )


@pytest.fixture 
def mock_ai_service():
    """Mock AI 服務，避免實際 API 調用"""
    ai_service = Mock(spec=AIService)
    
    # 設置常見的返回值
    ai_service.generate_practice_question.return_value = {
        "chinese_sentence": "我每天早上六點起床。",
        "knowledge_points": ["daily_routine", "time_expression"]
    }
    
    ai_service.grade_translation.return_value = {
        "is_correct": False,
        "feedback": "時態使用錯誤",
        "knowledge_points": [{
            "title": "現在式時態",
            "description": "描述習慣性動作應使用現在式",
            "error_category": "systematic"
        }]
    }
    
    ai_service.generate_review_question.return_value = {
        "chinese_sentence": "我昨天買了一本書。",
        "target_knowledge_points": ["past_tense"]
    }
    
    return ai_service


@pytest.fixture
def mock_knowledge_repository(mock_settings, sample_knowledge_point):
    """Mock 知識點 repository"""
    repo = Mock(spec=KnowledgeRepository)
    
    # 模擬存儲
    repo._knowledge_points = {"test_kp_001": sample_knowledge_point}
    
    # 設置方法行為
    repo.load_all.return_value = [sample_knowledge_point]
    repo.get_by_id.return_value = sample_knowledge_point
    repo.save.return_value = APIResponse(success=True, message="保存成功")
    repo.delete.return_value = APIResponse(success=True, message="刪除成功")
    
    return repo


@pytest.fixture
def mock_practice_repository(mock_settings):
    """Mock 練習記錄 repository"""
    repo = Mock(spec=PracticeRepository)
    
    # 模擬練習記錄
    sample_record = {
        "id": "practice_001",
        "chinese_sentence": "我喜歡讀書。",
        "user_answer": "I like read books.",
        "correct_answer": "I like reading books.",
        "is_correct": False,
        "timestamp": "2024-01-01T12:00:00",
        "knowledge_points": ["gerund_usage"]
    }
    
    repo.load_all.return_value = [sample_record]
    repo.save_record.return_value = APIResponse(success=True, message="記錄保存成功")
    
    return repo


@pytest.fixture
def frozen_time():
    """凍結時間到固定時間點，確保測試結果一致"""
    with freeze_time("2024-01-01T10:00:00"):
        yield


@pytest.fixture
def clean_environment():
    """清理環境變數，避免測試間相互影響"""
    original_env = os.environ.copy()
    
    # 清理可能影響測試的環境變數
    test_env_vars = [
        "GEMINI_API_KEY",
        "GEMINI_GENERATE_MODEL", 
        "GEMINI_GRADE_MODEL"
    ]
    
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # 恢復原始環境變數
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_ai_response():
    """標準的 AI 服務回應格式"""
    return {
        "chinese_sentence": "我明天要去上班。",
        "knowledge_points": ["future_tense", "work_vocabulary"],
        "difficulty": "medium",
        "explanation": "This sentence uses future tense with '要' to express intention."
    }


@pytest.fixture
def sample_grading_response():
    """標準的批改回應格式"""
    return {
        "is_correct": False,
        "score": 75,
        "feedback": "Grammar needs improvement",
        "knowledge_points": [{
            "title": "Article Usage",
            "description": "Missing definite article before 'office'",
            "error_category": "systematic",
            "examples": ["the office", "the school", "the hospital"]
        }],
        "suggestions": ["Add 'the' before 'office'", "Review article usage rules"]
    }


# 測試標記的便利函數
def pytest_configure(config):
    """pytest 配置鉤子，註冊自定義標記"""
    config.addinivalue_line("markers", "unit: 單元測試")
    config.addinivalue_line("markers", "integration: 整合測試") 
    config.addinivalue_line("markers", "ai: 涉及 AI 服務的測試")
    config.addinivalue_line("markers", "mock: 使用 mock 的測試")
    config.addinivalue_line("markers", "slow: 慢速測試")


# 測試數據工廠的輔助函數
def create_knowledge_points(count: int = 3) -> list[KnowledgePoint]:
    """創建多個知識點用於測試"""
    knowledge_points = []
    
    for i in range(count):
        original_error = OriginalError(
            chinese_sentence=f"測試中文句子 {i+1}",
            user_answer=f"Test user answer {i+1}",
            correct_answer=f"Test correct answer {i+1}",
            timestamp=f"2024-01-0{i+1}T10:00:00"
        )
        
        kp = KnowledgePoint(
            knowledge_point_id=f"test_kp_{i+1:03d}",
            title=f"測試知識點 {i+1}",
            description=f"測試描述 {i+1}",
            error_category="systematic" if i % 2 == 0 else "singular", 
            original_error=original_error,
            review_examples=[],
            correct_count=i,
            incorrect_count=i+1,
            mastery_level=float(i) / (i+1),
            last_review_date=None,
            next_review_date=f"2024-01-0{i+2}T10:00:00",
            version="3.0",
            tags=[f"tag_{i+1}", "grammar"],
            created_at=f"2024-01-0{i+1}T10:00:00",
            updated_at=f"2024-01-0{i+1}T10:00:00"
        )
        knowledge_points.append(kp)
    
    return knowledge_points