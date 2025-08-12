"""
知識點輔助函數測試
測試 services/knowledge_helpers.py 中的所有輔助函數
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from services.knowledge_helpers import (
    _find_knowledge_point,
    _calculate_next_review,
    _get_next_id,
    _group_knowledge_points,
    _calculate_mastery_level,
    _merge_duplicate_points,
    generate_unique_identifier,
    validate_knowledge_point_data,
    format_knowledge_point_display,
    calculate_review_priority,
    extract_tags_from_error,
    calculate_next_review_interval,
    get_learning_recommendations,
    filter_review_candidates,
    calculate_difficulty_score,
)
from core.error_types import ErrorCategory, ErrorTypeSystem


class TestKnowledgeHelpers:
    """知識點輔助函數測試類"""

    def test_generate_unique_identifier(self):
        """測試生成唯一標識符"""
        identifier = generate_unique_identifier("動詞變化", "go", "goes")
        assert "|" in identifier
        assert "#" in identifier
        assert "動詞變化" in identifier
        assert "go" in identifier
        assert "goes" in identifier

    def test_validate_knowledge_point_data_valid(self):
        """測試有效數據驗證"""
        data = {
            'key_point': '動詞變化錯誤',
            'category': 'systematic',
            'explanation': '需要加s',
            'original_phrase': 'go',
            'correction': 'goes',
            'mastery_level': 0.5,
            'mistake_count': 2,
            'correct_count': 1
        }
        is_valid, errors = validate_knowledge_point_data(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_knowledge_point_data_invalid(self):
        """測試無效數據驗證"""
        data = {
            'key_point': '',  # 缺少必需字段
            'mastery_level': 1.5,  # 超出範圍
            'mistake_count': -1,  # 負數
            'category': 'invalid'  # 無效類別
        }
        is_valid, errors = validate_knowledge_point_data(data)
        assert is_valid is False
        assert len(errors) > 0

    def test_calculate_mastery_level(self):
        """測試掌握度計算"""
        # 全部正確
        assert _calculate_mastery_level(5, 0) == 1.0
        
        # 全部錯誤
        assert _calculate_mastery_level(0, 5) == 0.0
        
        # 混合情況
        mastery = _calculate_mastery_level(3, 2)
        assert 0.0 <= mastery <= 1.0

    def test_calculate_next_review_interval(self):
        """測試複習間隔計算"""
        # 低掌握度應該有較短間隔
        interval1 = calculate_next_review_interval(0.2, 5, 1)
        
        # 高掌握度應該有較長間隔
        interval2 = calculate_next_review_interval(0.8, 1, 5)
        
        assert interval1 < interval2
        assert 1 <= interval1 <= 90
        assert 1 <= interval2 <= 90

    def test_extract_tags_from_error(self):
        """測試從錯誤提取標籤"""
        error_info = {
            'key_point_summary': '動詞時態錯誤',
            'explanation': '過去式動詞變化不正確',
            'category': 'systematic'
        }
        tags = extract_tags_from_error(error_info)
        
        assert '系統性' in tags
        assert '動詞' in tags
        assert '過去式' in tags
        assert len(tags) <= 10

    def test_get_next_id(self):
        """測試獲取下一個ID"""
        # 空列表
        assert _get_next_id([]) == 1
        
        # 有現有點的列表
        mock_points = [Mock(id=1), Mock(id=3), Mock(id=2)]
        assert _get_next_id(mock_points) == 4

    def test_calculate_review_priority(self):
        """測試複習優先級計算"""
        # 創建模擬知識點
        mock_point = Mock()
        mock_point.category = ErrorCategory.SYSTEMATIC
        mock_point.mastery_level = 0.2
        mock_point.mistake_count = 5
        mock_point.next_review = (datetime.now() - timedelta(days=1)).isoformat()
        
        level, score = calculate_review_priority(mock_point)
        
        assert 1 <= level <= 4
        assert score >= 0

    def test_calculate_difficulty_score(self):
        """測試難度分數計算"""
        mock_point = Mock()
        mock_point.category = ErrorCategory.SYSTEMATIC
        mock_point.mastery_level = 0.3
        mock_point.mistake_count = 3
        mock_point.correct_count = 1
        
        difficulty = calculate_difficulty_score(mock_point)
        
        assert 0.0 <= difficulty <= 10.0

    def test_format_knowledge_point_display(self):
        """測試知識點顯示格式化"""
        mock_point = Mock()
        mock_point.key_point = "動詞變化錯誤"
        mock_point.category.to_chinese.return_value = "系統性錯誤"
        mock_point.explanation = "需要加s"
        mock_point.original_phrase = "go"
        mock_point.correction = "goes"
        mock_point.mastery_level = 0.5
        mock_point.mistake_count = 2
        mock_point.correct_count = 1
        
        display = format_knowledge_point_display(mock_point)
        
        assert "📝" in display
        assert "動詞變化錯誤" in display
        assert "系統性錯誤" in display
        assert "50%" in display

    def test_group_knowledge_points(self):
        """測試知識點分組"""
        mock_point1 = Mock()
        mock_point1.category.to_chinese.return_value = "系統性錯誤"
        
        mock_point2 = Mock()
        mock_point2.category.to_chinese.return_value = "單一性錯誤"
        
        mock_point3 = Mock()
        mock_point3.category.to_chinese.return_value = "系統性錯誤"
        
        points = [mock_point1, mock_point2, mock_point3]
        groups = _group_knowledge_points(points)
        
        assert len(groups) == 2
        assert "系統性錯誤" in groups
        assert "單一性錯誤" in groups
        assert len(groups["系統性錯誤"]) == 2
        assert len(groups["單一性錯誤"]) == 1

    def test_filter_review_candidates(self):
        """測試複習候選篩選"""
        # 創建測試知識點
        mock_point1 = Mock()
        mock_point1.category = ErrorCategory.SYSTEMATIC
        mock_point1.mastery_level = 0.3
        mock_point1.mistake_count = 2
        
        mock_point2 = Mock()
        mock_point2.category = ErrorCategory.ISOLATED
        mock_point2.mastery_level = 0.8
        mock_point2.mistake_count = 1
        
        points = [mock_point1, mock_point2]
        
        # 篩選系統性錯誤
        candidates = filter_review_candidates(
            points, 
            categories=[ErrorCategory.SYSTEMATIC]
        )
        assert len(candidates) == 1
        assert candidates[0].category == ErrorCategory.SYSTEMATIC
        
        # 篩選低掌握度
        candidates = filter_review_candidates(
            points,
            max_mastery=0.5
        )
        assert len(candidates) == 1
        assert candidates[0].mastery_level <= 0.5

    def test_find_knowledge_point(self):
        """測試查找知識點"""
        # 創建模擬知識點
        mock_point1 = Mock()
        mock_point1.key_point = "動詞變化: go"
        mock_point1.original_phrase = "go"
        mock_point1.correction = "goes"
        
        mock_point2 = Mock()
        mock_point2.key_point = "拼寫錯誤: difficalt"
        mock_point2.original_phrase = "difficalt"
        mock_point2.correction = "difficult"
        
        points = [mock_point1, mock_point2]
        
        # 找到匹配的點
        found = _find_knowledge_point(points, "動詞變化: go", "go", "goes")
        assert found is mock_point1
        
        # 找不到匹配的點
        not_found = _find_knowledge_point(points, "不存在", "test", "test")
        assert not_found is None

    def test_calculate_next_review(self):
        """測試計算下次複習時間"""
        base_intervals = {
            "immediate": 1,
            "short": 3,
            "medium": 7,
            "long": 14,
            "mastered": 30
        }
        
        # 低掌握度應該有較短間隔
        review_time1 = _calculate_next_review(0.2, ErrorCategory.SYSTEMATIC, base_intervals)
        
        # 高掌握度應該有較長間隔
        review_time2 = _calculate_next_review(0.9, ErrorCategory.SYSTEMATIC, base_intervals)
        
        # 驗證返回的是有效的ISO時間戳
        datetime.fromisoformat(review_time1)
        datetime.fromisoformat(review_time2)

    def test_get_learning_recommendations(self):
        """測試獲取學習建議"""
        # 創建模擬知識點
        mock_point1 = Mock()
        mock_point1.category = ErrorCategory.SYSTEMATIC
        mock_point1.mastery_level = 0.3
        mock_point1.subtype = "verb_conjugation"
        
        mock_point2 = Mock()
        mock_point2.category = ErrorCategory.ISOLATED
        mock_point2.mastery_level = 0.7
        mock_point2.subtype = "vocabulary"
        
        points = [mock_point1, mock_point2]
        type_system = ErrorTypeSystem()
        
        recommendations = get_learning_recommendations(points, type_system)
        
        assert len(recommendations) >= 1
        assert all("category" in rec for rec in recommendations)
        assert all("advice" in rec for rec in recommendations)
        assert all("priority" in rec for rec in recommendations)

    def test_merge_duplicate_points(self):
        """測試合併重複知識點"""
        # 創建重複的知識點
        mock_point1 = Mock()
        mock_point1.unique_identifier = "test_id_1"
        mock_point1.mistake_count = 2
        mock_point1.correct_count = 1
        
        mock_point2 = Mock()
        mock_point2.unique_identifier = "test_id_1"  # 相同標識符
        mock_point2.mistake_count = 1
        mock_point2.correct_count = 2
        
        mock_point3 = Mock()
        mock_point3.unique_identifier = "test_id_2"  # 不同標識符
        mock_point3.mistake_count = 1
        mock_point3.correct_count = 0
        
        points = [mock_point1, mock_point2, mock_point3]
        merged = _merge_duplicate_points(points)
        
        assert len(merged) == 2  # 應該合併為2個唯一點
        
        # 檢查合併的統計信息
        merged_point = next(p for p in merged if p.unique_identifier == "test_id_1")
        assert merged_point.mistake_count == 3  # 2 + 1
        assert merged_point.correct_count == 3   # 1 + 2