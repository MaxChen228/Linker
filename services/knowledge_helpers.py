"""
知識點管理輔助方法模組
提供知識點管理的所有工具函數 - 純函數實現，易於測試
"""

import re
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from core.error_types import ErrorCategory, ErrorTypeSystem


@dataclass
class KnowledgePointData:
    """知識點數據結構（用於驗證）"""
    key_point: str
    category: str
    explanation: str
    original_phrase: str
    correction: str
    mastery_level: float = 0.0
    mistake_count: int = 1
    correct_count: int = 0


def _find_knowledge_point(
    knowledge_points: List[Any],
    key_point: str,
    original_phrase: str = "",
    correction: str = ""
) -> Optional[Any]:
    """使用複合鍵查找知識點

    Args:
        knowledge_points: 知識點列表
        key_point: 知識點描述
        original_phrase: 原始短語
        correction: 修正內容

    Returns:
        匹配的知識點或None
    """
    for point in knowledge_points:
        # 使用複合鍵匹配：key_point + original_phrase + correction
        if (point.key_point == key_point
                and point.original_phrase == original_phrase
                and point.correction == correction):
            return point
    return None


def _calculate_next_review(
    mastery_level: float,
    category: ErrorCategory,
    base_intervals: Dict[str, int]
) -> str:
    """計算下次複習時間（間隔重複算法）

    Args:
        mastery_level: 掌握度 (0.0-1.0)
        category: 錯誤類別
        base_intervals: 基礎間隔配置

    Returns:
        下次複習的ISO時間戳
    """
    # 根據掌握度決定基礎天數
    if mastery_level < 0.3:
        base_days = base_intervals.get("immediate", 1)
    elif mastery_level < 0.5:
        base_days = base_intervals.get("short", 3)
    elif mastery_level < 0.7:
        base_days = base_intervals.get("medium", 7)
    elif mastery_level < 0.9:
        base_days = base_intervals.get("long", 14)
    else:
        base_days = base_intervals.get("mastered", 30)

    # 根據錯誤類別調整
    multiplier = category.get_review_multiplier()
    days = max(1, int(base_days * multiplier))

    next_date = datetime.now() + timedelta(days=days)
    return next_date.isoformat()


def _get_next_id(knowledge_points: List[Any]) -> int:
    """獲取下一個可用的知識點ID

    Args:
        knowledge_points: 現有知識點列表

    Returns:
        下一個可用的ID
    """
    if not knowledge_points:
        return 1
    return max(p.id for p in knowledge_points) + 1


def _group_knowledge_points(knowledge_points: List[Any]) -> Dict[str, List[Any]]:
    """按類別分組知識點

    Args:
        knowledge_points: 知識點列表

    Returns:
        按類別分組的字典
    """
    groups = {}
    for point in knowledge_points:
        category_name = point.category.to_chinese()
        if category_name not in groups:
            groups[category_name] = []
        groups[category_name].append(point)
    return groups


def _calculate_mastery_level(correct_count: int, mistake_count: int) -> float:
    """計算掌握度

    Args:
        correct_count: 正確次數
        mistake_count: 錯誤次數

    Returns:
        掌握度 (0.0-1.0)
    """
    total_attempts = correct_count + mistake_count
    if total_attempts == 0:
        return 0.0

    # 基於正確率，但給予錯誤更高權重
    correct_ratio = correct_count / total_attempts

    # 應用權重：錯誤影響更大
    adjusted_ratio = max(0.0, correct_ratio - (mistake_count * 0.1))
    return min(1.0, adjusted_ratio)


def _merge_duplicate_points(knowledge_points: List[Any]) -> List[Any]:
    """合併重複知識點

    Args:
        knowledge_points: 原始知識點列表

    Returns:
        合併後的知識點列表
    """
    unique_points = []
    seen_identifiers = set()

    for point in knowledge_points:
        identifier = point.unique_identifier
        if identifier not in seen_identifiers:
            unique_points.append(point)
            seen_identifiers.add(identifier)
        else:
            # 找到重複的點並合併統計信息
            existing = next(p for p in unique_points
                            if p.unique_identifier == identifier)
            existing.mistake_count += point.mistake_count
            existing.correct_count += point.correct_count
            existing.mastery_level = _calculate_mastery_level(
                existing.correct_count, existing.mistake_count
            )

    return unique_points


def generate_unique_identifier(
    key_point: str,
    original_phrase: str,
    correction: str
) -> str:
    """生成知識點唯一標識

    Args:
        key_point: 知識點描述
        original_phrase: 原始短語
        correction: 修正內容

    Returns:
        唯一標識字符串
    """
    # 使用複合鍵生成標識
    composite_key = f"{key_point}|{original_phrase}|{correction}"

    # 生成短hash作為備用標識
    hash_suffix = hashlib.md5(composite_key.encode('utf-8')).hexdigest()[:8]

    return f"{composite_key}#{hash_suffix}"


def validate_knowledge_point_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """驗證知識點數據

    Args:
        data: 知識點數據字典

    Returns:
        (是否有效, 錯誤訊息列表)
    """
    errors = []

    # 必需字段檢查
    required_fields = [
        'key_point', 'category', 'explanation', 'original_phrase', 'correction'
    ]
    for field in required_fields:
        if not data.get(field):
            errors.append(f"缺少必需字段: {field}")

    # 數值字段檢查
    mastery_level = data.get('mastery_level', 0.0)
    if not isinstance(mastery_level, (int, float)) or not (0.0 <= mastery_level <= 1.0):
        errors.append("mastery_level 必須在 0.0-1.0 之間")

    mistake_count = data.get('mistake_count', 1)
    if not isinstance(mistake_count, int) or mistake_count < 0:
        errors.append("mistake_count 必須為非負整數")

    correct_count = data.get('correct_count', 0)
    if not isinstance(correct_count, int) or correct_count < 0:
        errors.append("correct_count 必須為非負整數")

    # 類別有效性檢查
    category = data.get('category')
    valid_categories = ['systematic', 'isolated', 'enhancement', 'other']
    if category and category not in valid_categories:
        errors.append(f"無效的錯誤類別: {category}")

    return len(errors) == 0, errors


def format_knowledge_point_display(point: Any, include_stats: bool = True) -> str:
    """格式化知識點顯示

    Args:
        point: 知識點對象
        include_stats: 是否包含統計信息

    Returns:
        格式化的顯示字符串
    """
    lines = []

    # 基本信息
    lines.append(f"📝 {point.key_point}")
    lines.append(f"   類別: {point.category.to_chinese()}")
    lines.append(f"   說明: {point.explanation}")

    if point.original_phrase:
        lines.append(f"   原文: {point.original_phrase}")
    if point.correction:
        lines.append(f"   修正: {point.correction}")

    # 統計信息
    if include_stats:
        mastery_percent = int(point.mastery_level * 100)
        lines.append(f"   掌握度: {mastery_percent}%")
        lines.append(f"   錯誤/正確: {point.mistake_count}/{point.correct_count}")

    return '\n'.join(lines)


def calculate_review_priority(
    point: Any,
    current_time: Optional[datetime] = None
) -> Tuple[int, float]:
    """計算複習優先級

    Args:
        point: 知識點對象
        current_time: 當前時間（用於測試）

    Returns:
        (優先級等級, 優先級分數) - 數字越小優先級越高
    """
    if current_time is None:
        current_time = datetime.now()

    # 基礎優先級（類別決定）
    base_priority = point.category.get_priority()

    # 是否已到期
    next_review = datetime.fromisoformat(point.next_review)
    is_due = next_review <= current_time
    due_penalty = 0 if is_due else 10  # 未到期的優先級降低

    # 掌握度因子（掌握度越低優先級越高）
    mastery_factor = (1.0 - point.mastery_level) * 5

    # 錯誤頻率因子
    error_factor = min(point.mistake_count * 0.1, 2.0)

    # 計算最終分數
    priority_score = base_priority + due_penalty + mastery_factor + error_factor

    # 優先級等級分類
    if is_due and point.mastery_level < 0.3:
        level = 1  # 緊急
    elif is_due and point.mastery_level < 0.7:
        level = 2  # 重要
    elif not is_due and point.mastery_level < 0.5:
        level = 3  # 一般
    else:
        level = 4  # 可延後

    return level, priority_score


def extract_tags_from_error(error_info: Dict[str, Any]) -> List[str]:
    """從錯誤中提取標籤

    Args:
        error_info: 錯誤信息字典

    Returns:
        標籤列表
    """
    tags = []

    # 從key_point提取標籤
    key_point = error_info.get('key_point_summary', '')
    if key_point:
        # 提取關鍵詞
        keywords = re.findall(r'[a-zA-Z]+|[\u4e00-\u9fff]+', key_point)
        tags.extend(keywords)

    # 從說明提取標籤
    explanation = error_info.get('explanation', '')
    if explanation:
        # 提取文法術語
        grammar_terms = re.findall(
            r'(時態|語態|動詞|名詞|形容詞|副詞|介詞|主詞|受詞|單數|複數|過去式|現在式|完成式)',
            explanation
        )
        tags.extend(grammar_terms)

    # 添加類別標籤
    category = error_info.get('category', '')
    if category:
        category_map = {
            'systematic': '系統性',
            'isolated': '單一性',
            'enhancement': '可改善',
            'other': '其他'
        }
        tags.append(category_map.get(category, category))

    # 去重並過濾短標籤
    unique_tags = list(set(tag for tag in tags if len(tag) > 1))

    return unique_tags[:10]  # 最多返回10個標籤


def calculate_next_review_interval(
    mastery_level: float,
    mistake_count: int,
    correct_count: int
) -> int:
    """基於 SM-2 算法的簡化版本計算複習間隔

    Args:
        mastery_level: 當前掌握度 (0.0-1.0)
        mistake_count: 錯誤次數
        correct_count: 正確次數

    Returns:
        下次複習的天數間隔
    """
    # SM-2 算法參數
    base_interval = 1
    ease_factor = max(1.3, 2.5 - (mistake_count * 0.2))  # 容易度因子

    # 計算複習次數（成功的複習次數）
    review_count = correct_count

    if review_count == 0:
        interval = base_interval
    elif review_count == 1:
        interval = 6
    else:
        # SM-2 公式：I(n) = I(n-1) * EF
        previous_interval = max(1, int(6 * (ease_factor ** (review_count - 2))))
        interval = int(previous_interval * ease_factor)

    # 根據掌握度調整
    mastery_multiplier = 0.5 + mastery_level  # 0.5-1.5的調整範圍
    interval = max(1, int(interval * mastery_multiplier))

    # 設置上下限
    return min(max(interval, 1), 90)  # 最短1天，最長90天


def get_learning_recommendations(
    knowledge_points: List[Any],
    type_system: ErrorTypeSystem
) -> List[Dict[str, Any]]:
    """獲取學習建議

    Args:
        knowledge_points: 知識點列表
        type_system: 錯誤類型系統

    Returns:
        學習建議列表
    """
    recommendations = []

    # 分析各類別的知識點
    for category in ErrorCategory:
        points = [p for p in knowledge_points if p.category == category]
        if not points:
            continue

        # 計算該類別的平均掌握度
        avg_mastery = sum(p.mastery_level for p in points) / len(points)

        # 找出最常見的子類型
        subtype_counts = {}
        for point in points:
            subtype = getattr(point, 'subtype', 'unknown')
            subtype_counts[subtype] = subtype_counts.get(subtype, 0) + 1

        if subtype_counts:
            most_common_subtype = max(subtype_counts.items(), key=lambda x: x[1])
            subtype_obj = type_system.get_subtype_by_name(most_common_subtype[0])

            recommendation = {
                "category": category.to_chinese(),
                "priority": category.get_priority(),
                "point_count": len(points),
                "avg_mastery": avg_mastery,
                "focus_area": (subtype_obj.chinese_name if subtype_obj
                               else most_common_subtype[0]),
                "advice": type_system.get_learning_advice(
                    category, most_common_subtype[0]),
                "weak_points": [p for p in points if p.mastery_level < 0.5][:3]
            }
            recommendations.append(recommendation)

    # 按優先級排序
    recommendations.sort(key=lambda x: x["priority"])

    return recommendations


def filter_review_candidates(
    knowledge_points: List[Any],
    categories: Optional[List[ErrorCategory]] = None,
    max_mastery: float = 1.0,
    min_mistakes: int = 0
) -> List[Any]:
    """篩選複習候選知識點

    Args:
        knowledge_points: 知識點列表
        categories: 限制的類別列表
        max_mastery: 最大掌握度閾值
        min_mistakes: 最小錯誤次數

    Returns:
        篩選後的知識點列表
    """
    candidates = knowledge_points

    # 按類別篩選
    if categories:
        candidates = [p for p in candidates if p.category in categories]

    # 按掌握度篩選
    candidates = [p for p in candidates if p.mastery_level <= max_mastery]

    # 按錯誤次數篩選
    candidates = [p for p in candidates if p.mistake_count >= min_mistakes]

    return candidates


def calculate_difficulty_score(point: Any) -> float:
    """計算知識點難度分數

    Args:
        point: 知識點對象

    Returns:
        難度分數 (0.0-10.0)
    """
    # 基礎難度（基於類別）
    category_difficulty = {
        ErrorCategory.SYSTEMATIC: 4.0,
        ErrorCategory.ISOLATED: 3.0,
        ErrorCategory.ENHANCEMENT: 2.0,
        ErrorCategory.OTHER: 3.5
    }

    base_score = category_difficulty.get(point.category, 3.0)

    # 根據錯誤頻率調整
    total_attempts = max(point.mistake_count + point.correct_count, 1)
    error_ratio = point.mistake_count / total_attempts
    error_adjustment = error_ratio * 3.0  # 最多增加3分

    # 根據掌握度調整
    mastery_adjustment = (1.0 - point.mastery_level) * 2.0  # 最多增加2分

    total_score = base_score + error_adjustment + mastery_adjustment
    return min(10.0, max(0.0, total_score))
