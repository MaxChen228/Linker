"""
響應數據傳輸對象定義

包含系統中各種服務響應的數據結構。
所有響應對象都提供狀態檢查和序列化功能。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from .common import (
    KnowledgePointData,
    PracticeRecordData,
    ErrorData,
    FeedbackData,
    StatisticsData,
)


@dataclass
class BaseResponse:
    """基礎響應類別"""
    success: bool
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class SaveMistakeResponse(BaseResponse):
    """保存錯誤響應"""
    practice_record_id: Optional[str] = None
    knowledge_points_created: List[str] = field(default_factory=list)
    knowledge_points_updated: List[str] = field(default_factory=list)
    errors_processed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            "practice_record_id": self.practice_record_id,
            "knowledge_points_created": self.knowledge_points_created,
            "knowledge_points_updated": self.knowledge_points_updated,
            "errors_processed": self.errors_processed,
        })
        return base_dict


@dataclass
class KnowledgePointsResponse(BaseResponse):
    """知識點查詢響應"""
    knowledge_points: List[KnowledgePointData] = field(default_factory=list)
    total_count: int = 0
    page_info: Dict[str, Any] = field(default_factory=dict)
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.page_info:
            self.page_info = {
                "current_page": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            "knowledge_points": [kp.to_dict() for kp in self.knowledge_points],
            "total_count": self.total_count,
            "page_info": self.page_info,
            "filters_applied": self.filters_applied,
        })
        return base_dict


@dataclass
class PracticeStatisticsResponse(BaseResponse):
    """練習統計響應"""
    statistics: Optional[StatisticsData] = None
    trends: Dict[str, List[Any]] = field(default_factory=dict)
    comparisons: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "trends": self.trends,
            "comparisons": self.comparisons,
            "insights": self.insights,
            "recommendations": self.recommendations,
        })
        return base_dict


@dataclass
class ErrorProcessingResponse(BaseResponse):
    """錯誤處理響應"""
    errors_processed: List[ErrorData] = field(default_factory=list)
    knowledge_points_affected: List[str] = field(default_factory=list)
    new_knowledge_points: List[str] = field(default_factory=list)
    processing_summary: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.processing_summary:
            self.processing_summary = {
                "total_errors": len(self.errors_processed),
                "systematic_errors": 0,
                "individual_errors": 0,
                "improvement_suggestions": 0,
                "other_errors": 0,
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            "errors_processed": [error.to_dict() for error in self.errors_processed],
            "knowledge_points_affected": self.knowledge_points_affected,
            "new_knowledge_points": self.new_knowledge_points,
            "processing_summary": self.processing_summary,
        })
        return base_dict


@dataclass
class ReviewQueueResponse(BaseResponse):
    """複習佇列響應"""
    review_items: List[KnowledgePointData] = field(default_factory=list)
    queue_metadata: Dict[str, Any] = field(default_factory=dict)
    scheduling_info: Dict[str, Any] = field(default_factory=dict)
    priority_distribution: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.queue_metadata:
            self.queue_metadata = {
                "total_items": len(self.review_items),
                "due_today": 0,
                "overdue": 0,
                "upcoming": 0,
                "last_updated": datetime.now().isoformat(),
            }
        
        if not self.priority_distribution:
            self.priority_distribution = {
                "high": 0,
                "medium": 0,
                "low": 0,
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            "review_items": [item.to_dict() for item in self.review_items],
            "queue_metadata": self.queue_metadata,
            "scheduling_info": self.scheduling_info,
            "priority_distribution": self.priority_distribution,
        })
        return base_dict


@dataclass
class PracticeHistoryResponse(BaseResponse):
    """練習歷史響應"""
    practice_records: List[PracticeRecordData] = field(default_factory=list)
    total_count: int = 0
    page_info: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.page_info:
            self.page_info = {
                "current_page": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            }
        
        if not self.summary:
            self.summary = {
                "total_practices": len(self.practice_records),
                "correct_count": 0,
                "incorrect_count": 0,
                "average_score": 0.0,
                "total_time": 0,
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            "practice_records": [record.to_dict() for record in self.practice_records],
            "total_count": self.total_count,
            "page_info": self.page_info,
            "summary": self.summary,
            "filters_applied": self.filters_applied,
        })
        return base_dict


@dataclass
class BatchOperationResponse(BaseResponse):
    """批次操作響應"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    operation_results: List[Dict[str, Any]] = field(default_factory=list)
    error_details: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """計算成功率"""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "failed_operations": self.failed_operations,
            "success_rate": self.success_rate,
            "operation_results": self.operation_results,
            "error_details": self.error_details,
        })
        return base_dict


@dataclass
class ValidationResponse(BaseResponse):
    """驗證響應"""
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "warnings": self.warnings,
            "validated_data": self.validated_data,
        })
        return base_dict