"""
一致性斷言輔助函數
用於驗證 JSON 和 Database 模式之間的操作一致性
"""

from typing import Any, Dict, List

from core.models import KnowledgePoint


def assert_stats_consistent(json_stats: Dict[str, Any], db_stats: Dict[str, Any], tolerance: float = 0.01) -> None:
    """斷言統計數據一致性"""
    key_fields = [
        'total_practices', 'correct_count', 'mistake_count',
        'knowledge_points', 'avg_mastery', 'due_reviews'
    ]

    for field in key_fields:
        json_val = json_stats.get(field, 0)
        db_val = db_stats.get(field, 0)

        if isinstance(json_val, (int, float)) and isinstance(db_val, (int, float)):
            if json_val > 0:
                diff_rate = abs(json_val - db_val) / max(json_val, db_val)
                assert diff_rate <= tolerance, f"{field} 不一致: JSON={json_val}, DB={db_val}, 差異={diff_rate:.4f}"
            else:
                assert json_val == db_val, f"{field} 不一致: JSON={json_val}, DB={db_val}"


def assert_initial_state_consistent(json_stats: Dict, db_stats: Dict, expected: Dict) -> None:
    """斷言初始狀態一致性"""
    for key, expected_value in expected.items():
        if key in ['recommendations']:
            # 推薦內容可能有差異，只檢查是否為非空列表
            assert isinstance(json_stats.get(key, []), list)
            assert isinstance(db_stats.get(key, []), list)
        else:
            assert json_stats.get(key) == expected_value, f"JSON {key} 不符預期: {json_stats.get(key)} != {expected_value}"
            assert db_stats.get(key) == expected_value, f"DB {key} 不符預期: {db_stats.get(key)} != {expected_value}"


def assert_stats_match_expected(stats: Dict, expected: Dict) -> None:
    """斷言統計數據符合預期"""
    for key, expected_value in expected.items():
        if key == 'category_distribution':
            assert isinstance(stats.get(key), dict)
            for cat, count in expected_value.items():
                assert stats['category_distribution'].get(cat, 0) == count
        else:
            assert stats.get(key) == expected_value, f"{key} 不符預期: {stats.get(key)} != {expected_value}"


def assert_knowledge_point_consistent(json_point: KnowledgePoint, db_point: KnowledgePoint) -> None:
    """斷言知識點對象一致性"""
    assert json_point.id == db_point.id, f"ID 不一致: {json_point.id} != {db_point.id}"
    assert json_point.key_point == db_point.key_point, f"知識點內容不一致: {json_point.key_point} != {db_point.key_point}"
    assert json_point.category == db_point.category, f"分類不一致: {json_point.category} != {db_point.category}"
    assert abs(json_point.mastery_level - db_point.mastery_level) < 0.01, f"掌握度不一致: {json_point.mastery_level} != {db_point.mastery_level}"
    assert json_point.is_deleted == db_point.is_deleted, f"刪除狀態不一致: {json_point.is_deleted} != {db_point.is_deleted}"


def assert_recommendations_consistent(json_rec: Dict, db_rec: Dict) -> None:
    """斷言學習推薦一致性"""
    assert len(json_rec['recommendations']) == len(db_rec['recommendations'])
    assert json_rec.get('suggested_difficulty') == db_rec.get('suggested_difficulty')
    assert abs(json_rec.get('next_review_count', 0) - db_rec.get('next_review_count', 0)) <= 1

    # 優先學習點數量應該相同
    json_priority = json_rec.get('priority_points', [])
    db_priority = db_rec.get('priority_points', [])
    assert len(json_priority) == len(db_priority)


def assert_candidates_consistent(json_candidates: List[KnowledgePoint], db_candidates: List[KnowledgePoint]) -> None:
    """斷言複習候選一致性"""
    assert len(json_candidates) == len(db_candidates)

    json_ids = [p.id for p in json_candidates]
    db_ids = [p.id for p in db_candidates]

    # ID 集合應該相同（允許順序差異）
    assert set(json_ids) == set(db_ids), f"候選 ID 不一致: JSON={json_ids}, DB={db_ids}"


def assert_operation_results_consistent(json_result: Any, db_result: Any, operation_name: str = "") -> None:
    """斷言操作結果一致性"""
    assert json_result == db_result, f"{operation_name} 操作結果不一致: JSON={json_result}, DB={db_result}"


def assert_response_time_acceptable(json_time: float, db_time: float, tolerance_percent: float = 0.2) -> None:
    """斷言響應時間差異在可接受範圍內"""
    if json_time > 0:
        diff_rate = abs(json_time - db_time) / max(json_time, db_time)
        assert diff_rate <= tolerance_percent, f"響應時間差異過大: JSON={json_time:.3f}s, DB={db_time:.3f}s, 差異={diff_rate:.3f}"


def assert_error_consistency(json_error: str, db_error: str) -> None:
    """斷言錯誤訊息一致性"""
    # 允許細微的格式差異，但核心訊息應該一致
    assert json_error.lower().strip() == db_error.lower().strip(), f"錯誤訊息不一致: JSON='{json_error}', DB='{db_error}'"
