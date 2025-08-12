"""
請求數據傳輸對象定義

包含系統中各種服務請求的數據結構。
所有請求對象都提供驗證方法和序列化功能。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SaveMistakeRequest:
    """保存錯誤請求"""
    chinese_sentence: str
    user_answer: str
    feedback: Dict[str, Any]
    practice_mode: str = "new"
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration_seconds: int = 0
    
    def __post_init__(self):
        """初始化後處理"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def validate(self) -> bool:
        """驗證請求數據的有效性"""
        if not self.chinese_sentence or not self.user_answer:
            return False
        if not isinstance(self.feedback, dict):
            return False
        if self.practice_mode not in ["new", "review"]:
            return False
        if self.duration_seconds < 0:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "chinese_sentence": self.chinese_sentence,
            "user_answer": self.user_answer,
            "feedback": self.feedback,
            "practice_mode": self.practice_mode,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class GetKnowledgePointsRequest:
    """獲取知識點請求"""
    category: Optional[str] = None
    difficulty: Optional[str] = None
    mastery_threshold: Optional[float] = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "mastery_level"  # mastery_level, last_practiced, error_count
    sort_order: str = "asc"  # asc, desc
    include_examples: bool = False
    tags: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """驗證請求數據的有效性"""
        if self.mastery_threshold is not None:
            if self.mastery_threshold < 0 or self.mastery_threshold > 1:
                return False
        
        if self.limit <= 0 or self.limit > 1000:
            return False
        
        if self.offset < 0:
            return False
        
        if self.sort_by not in ["mastery_level", "last_practiced", "error_count", "name"]:
            return False
        
        if self.sort_order not in ["asc", "desc"]:
            return False
        
        if self.difficulty and self.difficulty not in ["easy", "medium", "hard"]:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "category": self.category,
            "difficulty": self.difficulty,
            "mastery_threshold": self.mastery_threshold,
            "limit": self.limit,
            "offset": self.offset,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "include_examples": self.include_examples,
            "tags": self.tags,
        }


@dataclass
class UpdateMasteryRequest:
    """更新掌握度請求"""
    knowledge_point_id: str
    is_correct: bool
    confidence: float = 1.0
    context: str = ""
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def validate(self) -> bool:
        """驗證請求數據的有效性"""
        if not self.knowledge_point_id:
            return False
        if self.confidence < 0 or self.confidence > 1:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "knowledge_point_id": self.knowledge_point_id,
            "is_correct": self.is_correct,
            "confidence": self.confidence,
            "context": self.context,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class RecordPracticeRequest:
    """記錄練習請求"""
    chinese_sentence: str
    user_answer: str
    correct_answer: str
    practice_mode: str
    score: float
    is_correct: bool
    duration_seconds: int = 0
    errors_found: List[str] = field(default_factory=list)
    knowledge_points_used: List[str] = field(default_factory=list)
    feedback: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def validate(self) -> bool:
        """驗證請求數據的有效性"""
        if not all([self.chinese_sentence, self.user_answer, self.correct_answer]):
            return False
        if self.practice_mode not in ["new", "review"]:
            return False
        if self.score < 0 or self.score > 100:
            return False
        if self.duration_seconds < 0:
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "chinese_sentence": self.chinese_sentence,
            "user_answer": self.user_answer,
            "correct_answer": self.correct_answer,
            "practice_mode": self.practice_mode,
            "score": self.score,
            "is_correct": self.is_correct,
            "duration_seconds": self.duration_seconds,
            "errors_found": self.errors_found,
            "knowledge_points_used": self.knowledge_points_used,
            "feedback": self.feedback,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class ProcessErrorsRequest:
    """處理錯誤請求"""
    practice_record_id: str
    errors: List[Dict[str, Any]]
    auto_create_knowledge_points: bool = True
    confidence_threshold: float = 0.5
    session_id: Optional[str] = None
    
    def validate(self) -> bool:
        """驗證請求數據的有效性"""
        if not self.practice_record_id:
            return False
        if not isinstance(self.errors, list):
            return False
        if self.confidence_threshold < 0 or self.confidence_threshold > 1:
            return False
        
        # 驗證每個錯誤的必要欄位
        for error in self.errors:
            if not isinstance(error, dict):
                return False
            required_fields = ["type", "description", "user_text", "correct_text"]
            if not all(field in error for field in required_fields):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "practice_record_id": self.practice_record_id,
            "errors": self.errors,
            "auto_create_knowledge_points": self.auto_create_knowledge_points,
            "confidence_threshold": self.confidence_threshold,
            "session_id": self.session_id,
        }


@dataclass
class GetPracticeHistoryRequest:
    """獲取練習歷史請求"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    practice_mode: Optional[str] = None
    is_correct: Optional[bool] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    knowledge_point_ids: List[str] = field(default_factory=list)
    limit: int = 100
    offset: int = 0
    sort_by: str = "timestamp"  # timestamp, score, duration
    sort_order: str = "desc"  # asc, desc
    include_feedback: bool = False
    
    def validate(self) -> bool:
        """驗證請求數據的有效性"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                return False
        
        if self.practice_mode and self.practice_mode not in ["new", "review"]:
            return False
        
        if self.min_score is not None:
            if self.min_score < 0 or self.min_score > 100:
                return False
        
        if self.max_score is not None:
            if self.max_score < 0 or self.max_score > 100:
                return False
        
        if self.min_score and self.max_score:
            if self.min_score > self.max_score:
                return False
        
        if self.limit <= 0 or self.limit > 1000:
            return False
        
        if self.offset < 0:
            return False
        
        if self.sort_by not in ["timestamp", "score", "duration"]:
            return False
        
        if self.sort_order not in ["asc", "desc"]:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "practice_mode": self.practice_mode,
            "is_correct": self.is_correct,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "knowledge_point_ids": self.knowledge_point_ids,
            "limit": self.limit,
            "offset": self.offset,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "include_feedback": self.include_feedback,
        }