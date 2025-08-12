"""
自定義測試斷言
提供領域特定的斷言方法，使測試更具表達性和可讀性
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

import pytest
from core.knowledge import KnowledgePoint, OriginalError, ReviewExample
from core.response import APIResponse


def assert_knowledge_point_valid(kp: KnowledgePoint, strict: bool = True):
    """斷言知識點數據有效"""
    from core.error_types import ErrorCategory
    
    # 基本字段檢查
    assert kp.id > 0, "id must be positive"
    assert kp.key_point, "key_point cannot be empty" 
    assert kp.explanation, "explanation cannot be empty"
    assert isinstance(kp.category, ErrorCategory), f"Invalid category type: {type(kp.category)}"
    assert kp.subtype, "subtype cannot be empty"
    assert kp.original_phrase, "original_phrase cannot be empty"
    assert kp.correction, "correction cannot be empty"
    
    # 統計字段檢查
    assert kp.correct_count >= 0, "correct_count must be non-negative"
    assert kp.mistake_count >= 0, "mistake_count must be non-negative"
    assert 0.0 <= kp.mastery_level <= 1.0, f"mastery_level must be between 0-1: {kp.mastery_level}"
    
    # 掌握度計算檢查
    if strict and (kp.correct_count + kp.mistake_count) > 0:
        expected_mastery = kp.correct_count / (kp.correct_count + kp.mistake_count)
        assert abs(kp.mastery_level - expected_mastery) < 0.01, \
            f"Mastery level mismatch: expected {expected_mastery}, got {kp.mastery_level}"
    
    # 原始錯誤檢查
    assert isinstance(kp.original_error, OriginalError), "original_error must be OriginalError instance"
    assert kp.original_error.chinese_sentence, "original error chinese_sentence cannot be empty"
    assert kp.original_error.user_answer, "original error user_answer cannot be empty"
    assert kp.original_error.correct_answer, "original error correct_answer cannot be empty"
    assert kp.original_error.timestamp, "original error timestamp cannot be empty"
    
    # 時間戳格式檢查
    for timestamp_field in ["created_at", "last_seen", "next_review"]:
        timestamp = getattr(kp, timestamp_field, None)
        if timestamp:
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid timestamp format in {timestamp_field}: {timestamp}")


def assert_review_example_valid(example: ReviewExample):
    """斷言複習例句有效"""
    assert example.chinese_sentence, "chinese_sentence cannot be empty"
    assert example.user_answer, "user_answer cannot be empty" 
    assert example.correct_answer, "correct_answer cannot be empty"
    assert example.timestamp, "timestamp cannot be empty"
    assert isinstance(example.is_correct, bool), "is_correct must be boolean"
    
    # 時間戳格式檢查
    try:
        datetime.fromisoformat(example.timestamp.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {example.timestamp}")


def assert_practice_record_valid(record: Dict[str, Any]):
    """斷言練習記錄有效"""
    required_fields = ["chinese_sentence", "user_answer", "is_correct", "timestamp"]
    
    for field in required_fields:
        assert field in record, f"Missing required field: {field}"
        assert record[field] is not None, f"Field {field} cannot be None"
    
    # 類型檢查
    assert isinstance(record["is_correct"], bool), "is_correct must be boolean"
    assert isinstance(record["chinese_sentence"], str), "chinese_sentence must be string"
    assert isinstance(record["user_answer"], str), "user_answer must be string"
    
    # 分數檢查（如果存在）
    if "score" in record:
        score = record["score"]
        assert isinstance(score, (int, float)), "score must be numeric"
        assert 0 <= score <= 100, f"score must be between 0-100: {score}"
    
    # 時間戳檢查
    try:
        datetime.fromisoformat(record["timestamp"].replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {record['timestamp']}")


def assert_ai_response_valid(response: Dict[str, Any], response_type: str = "grading"):
    """斷言 AI 回應格式有效"""
    if response_type == "grading":
        # 批改回應檢查
        assert "is_correct" in response, "Missing is_correct field"
        assert "feedback" in response, "Missing feedback field"
        assert isinstance(response["is_correct"], bool), "is_correct must be boolean"
        assert isinstance(response["feedback"], str), "feedback must be string"
        
        # 知識點檢查（如果存在）
        if "knowledge_points" in response:
            assert isinstance(response["knowledge_points"], list), "knowledge_points must be list"
            for kp in response["knowledge_points"]:
                assert "title" in kp, "Knowledge point missing title"
                assert "error_category" in kp, "Knowledge point missing error_category"
                assert kp["error_category"] in ["systematic", "singular", "better", "other"]
    
    elif response_type == "generation":
        # 題目生成回應檢查
        assert "chinese_sentence" in response, "Missing chinese_sentence field"
        assert "knowledge_points" in response, "Missing knowledge_points field"
        assert isinstance(response["chinese_sentence"], str), "chinese_sentence must be string"
        assert isinstance(response["knowledge_points"], list), "knowledge_points must be list"
        assert len(response["knowledge_points"]) > 0, "knowledge_points cannot be empty"


def assert_response_success(response: APIResponse, 
                          expected_message: Optional[str] = None):
    """斷言回應成功"""
    assert response.success, f"Expected successful response, got error: {response.message}"
    
    if expected_message:
        assert expected_message in (response.message or ""), \
            f"Expected message to contain '{expected_message}', got '{response.message}'"


def assert_response_error(response: APIResponse, 
                         expected_message: Optional[str] = None):
    """斷言回應錯誤"""
    assert not response.success, f"Expected error response, got success: {response.message}"
    
    if expected_message:
        assert expected_message in (response.message or ""), \
            f"Expected error message to contain '{expected_message}', got '{response.message}'"


def assert_json_file_valid(file_path: Union[str, Path], expected_schema: Optional[Dict] = None):
    """斷言 JSON 文件格式有效"""
    file_path = Path(file_path)
    assert file_path.exists(), f"JSON file does not exist: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON format in {file_path}: {e}")
    
    if expected_schema:
        # 簡單的 schema 檢查
        for key, expected_type in expected_schema.items():
            if key in data:
                assert isinstance(data[key], expected_type), \
                    f"Expected {key} to be {expected_type.__name__}, got {type(data[key]).__name__}"


def assert_knowledge_points_equal(kp1: KnowledgePoint, kp2: KnowledgePoint, 
                                ignore_fields: Optional[List[str]] = None):
    """斷言兩個知識點相等"""
    ignore_fields = ignore_fields or ["updated_at"]
    
    kp1_dict = kp1.__dict__.copy()
    kp2_dict = kp2.__dict__.copy()
    
    # 移除忽略的字段
    for field in ignore_fields:
        kp1_dict.pop(field, None)
        kp2_dict.pop(field, None)
    
    # 特殊處理 original_error 和 review_examples
    if hasattr(kp1.original_error, '__dict__') and hasattr(kp2.original_error, '__dict__'):
        kp1_dict['original_error'] = kp1.original_error.__dict__
        kp2_dict['original_error'] = kp2.original_error.__dict__
    
    if kp1.review_examples and kp2.review_examples:
        kp1_dict['review_examples'] = [ex.__dict__ for ex in kp1.review_examples]
        kp2_dict['review_examples'] = [ex.__dict__ for ex in kp2.review_examples]
    
    assert kp1_dict == kp2_dict, "Knowledge points are not equal"


def assert_list_contains_knowledge_point(knowledge_points: List[KnowledgePoint], 
                                       target_id: int):
    """斷言列表包含指定 ID 的知識點"""
    found = any(kp.id == target_id for kp in knowledge_points)
    assert found, f"Knowledge point {target_id} not found in list"


def assert_mastery_level_in_range(kp: KnowledgePoint, min_level: float, max_level: float):
    """斷言掌握度在指定範圍內"""
    assert min_level <= kp.mastery_level <= max_level, \
        f"Mastery level {kp.mastery_level} not in range [{min_level}, {max_level}]"


def assert_timestamp_recent(timestamp: str, max_age_seconds: float = 60.0):
    """斷言時間戳是最近的"""
    try:
        timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now()
        age = (now - timestamp_dt.replace(tzinfo=None)).total_seconds()
        
        assert age <= max_age_seconds, \
            f"Timestamp {timestamp} is too old: {age}s > {max_age_seconds}s"
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {timestamp}")


def assert_subtype_valid(kp: KnowledgePoint, expected_subtype: str):
    """斷言知識點子類型有效"""
    assert kp.subtype == expected_subtype, f"Expected subtype '{expected_subtype}', got '{kp.subtype}'"


def assert_error_category_valid(category):
    """斷言錯誤分類有效"""
    from core.error_types import ErrorCategory
    assert isinstance(category, ErrorCategory), \
        f"Invalid error category type: {type(category)}. Must be ErrorCategory enum"


def assert_practice_statistics_valid(stats: Dict[str, Any]):
    """斷言練習統計數據有效"""
    required_fields = ["total_questions", "correct_answers", "accuracy"]
    
    for field in required_fields:
        assert field in stats, f"Missing required statistics field: {field}"
    
    total = stats["total_questions"]
    correct = stats["correct_answers"]
    accuracy = stats["accuracy"]
    
    assert total >= 0, "total_questions must be non-negative"
    assert correct >= 0, "correct_answers must be non-negative"
    assert correct <= total, "correct_answers cannot exceed total_questions"
    
    if total > 0:
        expected_accuracy = correct / total
        assert abs(accuracy - expected_accuracy) < 0.01, \
            f"Accuracy mismatch: expected {expected_accuracy}, got {accuracy}"
    else:
        assert accuracy == 0.0, "Accuracy should be 0.0 when total_questions is 0"


def assert_file_backup_created(backup_dir: Union[str, Path], original_file: str):
    """斷言備份文件已創建"""
    backup_dir = Path(backup_dir)
    assert backup_dir.exists(), f"Backup directory does not exist: {backup_dir}"
    
    # 查找匹配的備份文件
    file_stem = Path(original_file).stem
    backup_files = list(backup_dir.glob(f"{file_stem}_backup_*.json"))
    
    assert len(backup_files) > 0, f"No backup files found for {original_file} in {backup_dir}"
    
    # 檢查最新的備份文件
    latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)
    assert latest_backup.exists(), f"Latest backup file does not exist: {latest_backup}"


# 自定義斷言錯誤類
class KnowledgePointAssertionError(AssertionError):
    """知識點斷言錯誤"""
    pass


class PracticeRecordAssertionError(AssertionError):
    """練習記錄斷言錯誤"""
    pass


class AIResponseAssertionError(AssertionError):
    """AI 回應斷言錯誤"""
    pass