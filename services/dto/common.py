"""
共用數據傳輸對象定義

包含系統中各模組共用的基礎數據結構。
所有數據結構都使用 dataclass 提供類型安全和驗證功能。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json


@dataclass
class KnowledgePointData:
    """知識點資料結構"""
    id: str
    name: str
    category: str
    description: str = ""
    examples: List[str] = field(default_factory=list)
    correct_count: int = 0
    error_count: int = 0
    mastery_level: float = 0.0
    last_practiced: Optional[datetime] = None
    next_review: Optional[datetime] = None
    difficulty: str = "medium"  # easy, medium, hard
    tags: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """驗證知識點數據的有效性"""
        if not self.id or not self.name or not self.category:
            return False
        if self.mastery_level < 0 or self.mastery_level > 1:
            return False
        if self.correct_count < 0 or self.error_count < 0:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式，用於序列化"""
        data = {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "examples": self.examples,
            "correct_count": self.correct_count,
            "error_count": self.error_count,
            "mastery_level": self.mastery_level,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }
        if self.last_practiced:
            data["last_practiced"] = self.last_practiced.isoformat()
        if self.next_review:
            data["next_review"] = self.next_review.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgePointData":
        """從字典創建知識點對象"""
        last_practiced = None
        if data.get("last_practiced"):
            last_practiced = datetime.fromisoformat(data["last_practiced"])
        
        next_review = None
        if data.get("next_review"):
            next_review = datetime.fromisoformat(data["next_review"])
        
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            description=data.get("description", ""),
            examples=data.get("examples", []),
            correct_count=data.get("correct_count", 0),
            error_count=data.get("error_count", 0),
            mastery_level=data.get("mastery_level", 0.0),
            last_practiced=last_practiced,
            next_review=next_review,
            difficulty=data.get("difficulty", "medium"),
            tags=data.get("tags", []),
        )


@dataclass
class PracticeRecordData:
    """練習記錄資料結構"""
    id: str
    timestamp: datetime
    chinese_sentence: str
    user_answer: str
    correct_answer: str = ""
    practice_mode: str = "new"  # new, review
    is_correct: bool = False
    score: float = 0.0
    duration_seconds: int = 0
    errors_found: List[str] = field(default_factory=list)
    knowledge_points_used: List[str] = field(default_factory=list)
    feedback: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """驗證練習記錄的有效性"""
        if not self.id or not self.chinese_sentence or not self.user_answer:
            return False
        if self.score < 0 or self.score > 100:
            return False
        if self.duration_seconds < 0:
            return False
        if self.practice_mode not in ["new", "review"]:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "chinese_sentence": self.chinese_sentence,
            "user_answer": self.user_answer,
            "correct_answer": self.correct_answer,
            "practice_mode": self.practice_mode,
            "is_correct": self.is_correct,
            "score": self.score,
            "duration_seconds": self.duration_seconds,
            "errors_found": self.errors_found,
            "knowledge_points_used": self.knowledge_points_used,
            "feedback": self.feedback,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PracticeRecordData":
        """從字典創建練習記錄對象"""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            chinese_sentence=data["chinese_sentence"],
            user_answer=data["user_answer"],
            correct_answer=data.get("correct_answer", ""),
            practice_mode=data.get("practice_mode", "new"),
            is_correct=data.get("is_correct", False),
            score=data.get("score", 0.0),
            duration_seconds=data.get("duration_seconds", 0),
            errors_found=data.get("errors_found", []),
            knowledge_points_used=data.get("knowledge_points_used", []),
            feedback=data.get("feedback", {}),
        )


@dataclass
class ErrorData:
    """錯誤資料結構"""
    id: str
    type: str  # 錯誤類型，如 grammar, vocabulary, spelling 等
    category: str  # 錯誤分類，如 systematic, individual, improvement, other
    description: str
    user_text: str
    correct_text: str
    explanation: str = ""
    severity: str = "medium"  # low, medium, high
    context: str = ""
    confidence: float = 1.0
    knowledge_point_id: Optional[str] = None
    
    def validate(self) -> bool:
        """驗證錯誤數據的有效性"""
        if not self.id or not self.type or not self.description:
            return False
        if not self.user_text or not self.correct_text:
            return False
        if self.confidence < 0 or self.confidence > 1:
            return False
        if self.severity not in ["low", "medium", "high"]:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "id": self.id,
            "type": self.type,
            "category": self.category,
            "description": self.description,
            "user_text": self.user_text,
            "correct_text": self.correct_text,
            "explanation": self.explanation,
            "severity": self.severity,
            "context": self.context,
            "confidence": self.confidence,
            "knowledge_point_id": self.knowledge_point_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorData":
        """從字典創建錯誤對象"""
        return cls(
            id=data["id"],
            type=data["type"],
            category=data["category"],
            description=data["description"],
            user_text=data["user_text"],
            correct_text=data["correct_text"],
            explanation=data.get("explanation", ""),
            severity=data.get("severity", "medium"),
            context=data.get("context", ""),
            confidence=data.get("confidence", 1.0),
            knowledge_point_id=data.get("knowledge_point_id"),
        )


@dataclass
class FeedbackData:
    """反饋資料結構"""
    overall_score: float
    is_correct: bool
    errors: List[ErrorData] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    correct_answer: str = ""
    explanation: str = ""
    improvement_tips: List[str] = field(default_factory=list)
    knowledge_points_covered: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """驗證反饋數據的有效性"""
        if self.overall_score < 0 or self.overall_score > 100:
            return False
        for error in self.errors:
            if not error.validate():
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "overall_score": self.overall_score,
            "is_correct": self.is_correct,
            "errors": [error.to_dict() for error in self.errors],
            "suggestions": self.suggestions,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "improvement_tips": self.improvement_tips,
            "knowledge_points_covered": self.knowledge_points_covered,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackData":
        """從字典創建反饋對象"""
        errors = [ErrorData.from_dict(error_data) for error_data in data.get("errors", [])]
        
        return cls(
            overall_score=data["overall_score"],
            is_correct=data["is_correct"],
            errors=errors,
            suggestions=data.get("suggestions", []),
            correct_answer=data.get("correct_answer", ""),
            explanation=data.get("explanation", ""),
            improvement_tips=data.get("improvement_tips", []),
            knowledge_points_covered=data.get("knowledge_points_covered", []),
        )


@dataclass
class StatisticsData:
    """統計資料結構"""
    total_practices: int = 0
    correct_practices: int = 0
    incorrect_practices: int = 0
    average_score: float = 0.0
    total_time_spent: int = 0  # 總練習時間（秒）
    knowledge_points_learned: int = 0
    current_streak: int = 0  # 連續正確次數
    best_streak: int = 0  # 最佳連續正確次數
    practices_by_mode: Dict[str, int] = field(default_factory=dict)
    scores_by_category: Dict[str, float] = field(default_factory=dict)
    weekly_progress: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    
    def validate(self) -> bool:
        """驗證統計數據的有效性"""
        if any(count < 0 for count in [
            self.total_practices, 
            self.correct_practices, 
            self.incorrect_practices,
            self.knowledge_points_learned,
            self.current_streak,
            self.best_streak,
            self.total_time_spent
        ]):
            return False
        
        if self.average_score < 0 or self.average_score > 100:
            return False
        
        if self.total_practices != (self.correct_practices + self.incorrect_practices):
            return False
        
        return True
    
    @property
    def accuracy_rate(self) -> float:
        """計算準確率"""
        if self.total_practices == 0:
            return 0.0
        return (self.correct_practices / self.total_practices) * 100
    
    @property
    def average_time_per_practice(self) -> float:
        """計算平均每次練習時間（秒）"""
        if self.total_practices == 0:
            return 0.0
        return self.total_time_spent / self.total_practices
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        data = {
            "total_practices": self.total_practices,
            "correct_practices": self.correct_practices,
            "incorrect_practices": self.incorrect_practices,
            "average_score": self.average_score,
            "total_time_spent": self.total_time_spent,
            "knowledge_points_learned": self.knowledge_points_learned,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "practices_by_mode": self.practices_by_mode,
            "scores_by_category": self.scores_by_category,
            "weekly_progress": self.weekly_progress,
            "accuracy_rate": self.accuracy_rate,
            "average_time_per_practice": self.average_time_per_practice,
        }
        if self.last_updated:
            data["last_updated"] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatisticsData":
        """從字典創建統計對象"""
        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])
        
        return cls(
            total_practices=data.get("total_practices", 0),
            correct_practices=data.get("correct_practices", 0),
            incorrect_practices=data.get("incorrect_practices", 0),
            average_score=data.get("average_score", 0.0),
            total_time_spent=data.get("total_time_spent", 0),
            knowledge_points_learned=data.get("knowledge_points_learned", 0),
            current_streak=data.get("current_streak", 0),
            best_streak=data.get("best_streak", 0),
            practices_by_mode=data.get("practices_by_mode", {}),
            scores_by_category=data.get("scores_by_category", {}),
            weekly_progress=data.get("weekly_progress", []),
            last_updated=last_updated,
        )