"""
知識點管理模組 - 使用系統性/單一性錯誤分類系統
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.error_types import ErrorCategory, ErrorTypeSystem
from core.exceptions import DataException, handle_file_operation
from core.logger import get_logger
from settings import settings


@dataclass
class KnowledgePoint:
    """知識點數據類"""

    id: int
    key_point: str
    category: ErrorCategory
    subtype: str
    explanation: str
    original_phrase: str
    correction: str
    mastery_level: float = 0.0
    mistake_count: int = 1
    correct_count: int = 0
    created_at: str = ""
    last_seen: str = ""
    next_review: str = ""
    examples: list[dict] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_seen:
            self.last_seen = datetime.now().isoformat()
        if not self.next_review:
            self.next_review = self._calculate_next_review()
        if self.examples is None:
            self.examples = []

    def _calculate_next_review(self) -> str:
        """計算下次複習時間"""
        # 從設定檔獲取複習間隔
        thresholds = settings.learning.MASTERY_THRESHOLDS
        intervals = settings.learning.REVIEW_INTERVALS

        # 根據掌握度決定基礎天數
        if self.mastery_level < thresholds["beginner"]:
            base_days = intervals["immediate"]
        elif self.mastery_level < thresholds["intermediate"]:
            base_days = intervals["short"]
        elif self.mastery_level < thresholds["advanced"]:
            base_days = intervals["medium"]
        elif self.mastery_level < thresholds["expert"]:
            base_days = intervals["long"]
        else:
            base_days = intervals["mastered"]

        # 根據錯誤類別調整
        multiplier = self.category.get_review_multiplier()
        days = max(1, int(base_days * multiplier))

        next_date = datetime.now() + timedelta(days=days)
        return next_date.isoformat()

    def update_mastery(self, is_correct: bool):
        """更新掌握度"""
        increments = settings.learning.MASTERY_INCREMENTS
        decrements = settings.learning.MASTERY_DECREMENTS

        if is_correct:
            self.correct_count += 1
            # 根據錯誤類別調整進步幅度
            category_key = self.category.value
            increment = increments.get(category_key, increments["other"])
            self.mastery_level = min(1.0, self.mastery_level + increment)
        else:
            self.mistake_count += 1
            # 錯誤時的懲罰
            category_key = self.category.value
            decrement = decrements.get(category_key, decrements["other"])
            self.mastery_level = max(0.0, self.mastery_level - decrement)

        self.last_seen = datetime.now().isoformat()
        self.next_review = self._calculate_next_review()

    def to_dict(self) -> dict:
        """轉換為字典（用於JSON存儲）"""
        return {
            "id": self.id,
            "key_point": self.key_point,
            "category": self.category.value,  # 存儲枚舉值
            "subtype": self.subtype,
            "explanation": self.explanation,
            "original_phrase": self.original_phrase,
            "correction": self.correction,
            "mastery_level": self.mastery_level,
            "mistake_count": self.mistake_count,
            "correct_count": self.correct_count,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "next_review": self.next_review,
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgePoint":
        """從字典創建實例"""
        # 轉換category字符串為枚舉
        data = data.copy()
        data["category"] = ErrorCategory.from_string(data.get("category", "other"))
        return cls(**data)


class KnowledgeManager:
    """知識點管理器 V2"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.knowledge_file = self.data_dir / "knowledge.json"
        self.practice_log = self.data_dir / "practice_log.json"

        self.logger = get_logger("knowledge_manager")
        self.settings = settings

        self.knowledge_points: list[KnowledgePoint] = self._load_knowledge()
        self.practice_history = self._load_practice_log()
        self.type_system = ErrorTypeSystem()

    @handle_file_operation("read")
    def _load_knowledge(self) -> list[KnowledgePoint]:
        """載入知識點"""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, encoding="utf-8") as f:
                    data = json.load(f)
                    points = [KnowledgePoint.from_dict(item) for item in data]
                    self.logger.info(f"載入 {len(points)} 個知識點")
                    return points
            except json.JSONDecodeError as e:
                self.logger.error(f"知識點文件解析失敗: {e}")
                raise DataException(
                    "知識點文件格式錯誤",
                    data_type="knowledge_points",
                    file_path=str(self.knowledge_file),
                ) from e
        return []

    @handle_file_operation("write")
    def _save_knowledge(self):
        """儲存知識點"""
        try:
            data = [point.to_dict() for point in self.knowledge_points]
            with open(self.knowledge_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"儲存 {len(data)} 個知識點")
        except Exception as e:
            self.logger.error(f"儲存知識點失敗: {e}", exc_info=True)
            raise

    def _load_practice_log(self) -> list[dict]:
        """載入練習記錄"""
        if self.practice_log.exists():
            with open(self.practice_log, encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_practice_log(self):
        """儲存練習記錄"""
        with open(self.practice_log, "w", encoding="utf-8") as f:
            json.dump(self.practice_history, f, ensure_ascii=False, indent=2)

    def save_mistake(self, chinese_sentence: str, user_answer: str, feedback: dict[str, Any]):
        """儲存錯誤記錄（使用新的分類系統）"""
        # 記錄練習歷史
        practice = {
            "timestamp": datetime.now().isoformat(),
            "chinese_sentence": chinese_sentence,
            "user_answer": user_answer,
            "is_correct": feedback.get("is_generally_correct", False),
            "feedback": feedback,
        }
        self.practice_history.append(practice)
        self._save_practice_log()

        # 提取並儲存知識點
        if not feedback.get("is_generally_correct", False):
            errors = feedback.get("error_analysis", [])
            for error in errors:
                self._process_error(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    error=error,
                    correct_answer=feedback.get("overall_suggestion", ""),
                )

    def _process_error(
        self, chinese_sentence: str, user_answer: str, error: dict[str, Any], correct_answer: str
    ):
        """處理單個錯誤"""
        key_point = error.get("key_point_summary", "")
        explanation = error.get("explanation", "")
        severity = error.get("severity", "major")

        # 優先使用AI返回的category，如果沒有則用分類系統推斷
        if "category" in error:
            category = ErrorCategory.from_string(error["category"])
            # 使用分類系統推斷subtype
            _, subtype = self.type_system.classify(key_point, explanation, severity)
        else:
            # 使用新的分類系統
            category, subtype = self.type_system.classify(key_point, explanation, severity)

        # 查找現有知識點
        existing = self._find_knowledge_point(key_point)

        if existing:
            # 更新現有知識點
            existing.update_mastery(is_correct=False)

            # 添加新例句（根據設定限制數量）
            if len(existing.examples) < self.settings.display.MAX_EXAMPLES_PER_POINT:
                existing.examples.append(
                    {
                        "chinese": chinese_sentence,
                        "user_answer": user_answer,
                        "correct": correct_answer,
                    }
                )
        else:
            # 創建新知識點
            new_point = KnowledgePoint(
                id=self._get_next_id(),
                key_point=key_point,
                category=category,
                subtype=subtype,
                explanation=explanation,
                original_phrase=error.get("original_phrase", ""),
                correction=error.get("correction", ""),
                examples=[
                    {
                        "chinese": chinese_sentence,
                        "user_answer": user_answer,
                        "correct": correct_answer,
                    }
                ],
            )
            self.knowledge_points.append(new_point)

        self._save_knowledge()

    def _find_knowledge_point(self, key_point: str) -> Optional[KnowledgePoint]:
        """查找知識點"""
        for point in self.knowledge_points:
            if point.key_point == key_point:
                return point
        return None

    def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        """根據ID獲取知識點"""
        try:
            target_id = int(point_id)
            for point in self.knowledge_points:
                if point.id == target_id:
                    return point
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid point_id: {point_id}")
        return None

    def _get_next_id(self) -> int:
        """獲取下一個ID"""
        if not self.knowledge_points:
            return 1
        return max(p.id for p in self.knowledge_points) + 1

    def get_points_by_category(self, category: ErrorCategory) -> list[KnowledgePoint]:
        """根據類別獲取知識點"""
        return [p for p in self.knowledge_points if p.category == category]
    
    def get_all_mistakes(self) -> list[dict]:
        """獲取所有錯誤記錄"""
        # 返回練習歷史中的錯誤記錄，並為每個記錄添加知識點信息
        mistakes = []
        for practice in self.practice_history:
            if not practice.get("is_correct", True):
                # 為每個錯誤記錄添加關聯的知識點
                mistake = practice.copy()
                # 從feedback中提取知識點信息
                if "feedback" in mistake and "error_analysis" in mistake["feedback"]:
                    knowledge_points = []
                    for error in mistake["feedback"]["error_analysis"]:
                        key_point = error.get("key_point", "")
                        point = self._find_knowledge_point(key_point)
                        if point:
                            knowledge_points.append({
                                "id": str(point.id),
                                "key_point": point.key_point,
                                "category": point.category.value
                            })
                    mistake["knowledge_points"] = knowledge_points
                mistakes.append(mistake)
        return mistakes

    def get_due_points(self) -> list[KnowledgePoint]:
        """獲取需要複習的知識點"""
        now = datetime.now().isoformat()
        return [p for p in self.knowledge_points if p.next_review <= now]
    
    def get_review_candidates(self, max_points: int = 5) -> list[KnowledgePoint]:
        """獲取適合複習的知識點（單一性錯誤和可以更好類別）
        
        Args:
            max_points: 最多返回的知識點數量
            
        Returns:
            需要複習的知識點列表，優先返回已到期的
        """
        # 篩選單一性錯誤和可以更好類別
        candidates = [
            p for p in self.knowledge_points 
            if p.category in [ErrorCategory.ISOLATED, ErrorCategory.ENHANCEMENT]
        ]
        
        if not candidates:
            return []
        
        # 按複習優先級排序：
        # 1. 已到期的（next_review <= now）
        # 2. 掌握度低的
        # 3. 錯誤次數多的
        now = datetime.now().isoformat()
        
        def sort_key(point: KnowledgePoint) -> tuple:
            is_due = point.next_review <= now
            return (
                not is_due,  # 到期的排前面
                point.mastery_level,  # 掌握度低的排前面
                -point.mistake_count  # 錯誤次數多的排前面
            )
        
        candidates.sort(key=sort_key)
        
        # 返回前max_points個最需要複習的
        return candidates[:max_points]
    
    def update_knowledge_point(self, point_id: int, is_correct: bool) -> bool:
        """更新指定知識點的掌握狀態
        
        Args:
            point_id: 知識點ID
            is_correct: 是否答對
            
        Returns:
            是否成功更新
        """
        for point in self.knowledge_points:
            if point.id == point_id:
                point.update_mastery(is_correct)
                self._save_knowledge()
                return True
        return False

    def get_statistics(self) -> dict[str, Any]:
        """獲取統計資料"""
        total_practices = len(self.practice_history)
        correct_count = sum(1 for p in self.practice_history if p.get("is_correct", False))

        # 分類統計
        category_stats = {
            ErrorCategory.SYSTEMATIC: 0,
            ErrorCategory.ISOLATED: 0,
            ErrorCategory.ENHANCEMENT: 0,
            ErrorCategory.OTHER: 0,
        }

        subtype_stats = {}

        for point in self.knowledge_points:
            category_stats[point.category] += 1
            if point.subtype not in subtype_stats:
                subtype_stats[point.subtype] = 0
            subtype_stats[point.subtype] += 1

        # 平均掌握度
        if self.knowledge_points:
            avg_mastery = sum(p.mastery_level for p in self.knowledge_points) / len(
                self.knowledge_points
            )
        else:
            avg_mastery = 0.0

        return {
            "total_practices": total_practices,
            "correct_count": correct_count,
            "mistake_count": total_practices - correct_count,
            "accuracy": correct_count / total_practices if total_practices > 0 else 0,
            "knowledge_points": len(self.knowledge_points),
            "avg_mastery": avg_mastery,
            "category_distribution": {
                cat.to_chinese(): count for cat, count in category_stats.items() if count > 0
            },
            "subtype_distribution": subtype_stats,
            "due_reviews": len(self.get_due_points()),
        }

    def get_learning_recommendations(self) -> list[dict]:
        """獲取學習建議"""
        recommendations = []

        # 分析各類別的知識點
        for category in ErrorCategory:
            points = self.get_points_by_category(category)
            if not points:
                continue

            # 計算該類別的平均掌握度
            avg_mastery = sum(p.mastery_level for p in points) / len(points)

            # 找出最常見的子類型
            subtype_counts = {}
            for point in points:
                if point.subtype not in subtype_counts:
                    subtype_counts[point.subtype] = 0
                subtype_counts[point.subtype] += 1

            if subtype_counts:
                most_common_subtype = max(subtype_counts.items(), key=lambda x: x[1])
                subtype_obj = self.type_system.get_subtype_by_name(most_common_subtype[0])

                recommendation = {
                    "category": category.to_chinese(),
                    "priority": category.get_priority(),
                    "point_count": len(points),
                    "avg_mastery": avg_mastery,
                    "focus_area": subtype_obj.chinese_name
                    if subtype_obj
                    else most_common_subtype[0],
                    "advice": self.type_system.get_learning_advice(
                        category, most_common_subtype[0]
                    ),
                }
                recommendations.append(recommendation)

        # 按優先級排序
        recommendations.sort(key=lambda x: x["priority"])

        return recommendations

    def migrate_from_v1(self, old_knowledge_file: Path):
        """從舊版本遷移數據"""
        if not old_knowledge_file.exists():
            return False

        with open(old_knowledge_file, encoding="utf-8") as f:
            old_data = json.load(f)

        migrated_count = 0
        for old_point in old_data:
            # 轉換舊的error_type到新的分類
            old_type = old_point.get("error_type", "")
            category = ErrorCategory.from_string(old_type)

            # 嘗試從key_point和explanation推斷subtype
            key_point = old_point.get("key_point", "")
            explanation = old_point.get("explanation", "")
            _, subtype = self.type_system.classify(key_point, explanation)

            # 創建新的知識點
            new_point = KnowledgePoint(
                id=old_point.get("id", self._get_next_id()),
                key_point=key_point,
                category=category,
                subtype=subtype,
                explanation=explanation,
                original_phrase=old_point.get("original_phrase", ""),
                correction=old_point.get("correction", ""),
                mastery_level=old_point.get("mastery_level", 0.0),
                mistake_count=old_point.get("mistake_count", 1),
                correct_count=old_point.get("correct_count", 0),
                created_at=old_point.get("created_at", datetime.now().isoformat()),
                last_seen=old_point.get("last_seen", datetime.now().isoformat()),
                next_review=old_point.get("next_review", ""),
                examples=old_point.get("examples", []),
            )

            if not new_point.next_review:
                new_point.next_review = new_point._calculate_next_review()

            self.knowledge_points.append(new_point)
            migrated_count += 1

        self._save_knowledge()
        print(f"✅ 成功遷移 {migrated_count} 個知識點")
        return True
