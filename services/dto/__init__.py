"""
數據傳輸對象 (Data Transfer Objects) 模組

提供系統中各種請求、響應和共用數據結構的定義。
所有 DTO 類都使用 dataclass 裝飾器，提供類型安全和數據驗證功能。

模組結構:
- requests.py: 請求對象定義
- responses.py: 響應對象定義
- common.py: 共用數據結構定義
"""

from .common import (
    KnowledgePointData,
    PracticeRecordData,
    ErrorData,
    FeedbackData,
    StatisticsData,
)

from .requests import (
    SaveMistakeRequest,
    GetKnowledgePointsRequest,
    UpdateMasteryRequest,
    RecordPracticeRequest,
    ProcessErrorsRequest,
    GetPracticeHistoryRequest,
)

from .responses import (
    SaveMistakeResponse,
    KnowledgePointsResponse,
    PracticeStatisticsResponse,
    ErrorProcessingResponse,
    ReviewQueueResponse,
)

__all__ = [
    # Common DTOs
    "KnowledgePointData",
    "PracticeRecordData",
    "ErrorData",
    "FeedbackData",
    "StatisticsData",
    # Request DTOs
    "SaveMistakeRequest",
    "GetKnowledgePointsRequest",
    "UpdateMasteryRequest",
    "RecordPracticeRequest",
    "ProcessErrorsRequest",
    "GetPracticeHistoryRequest",
    # Response DTOs
    "SaveMistakeResponse",
    "KnowledgePointsResponse",
    "PracticeStatisticsResponse",
    "ErrorProcessingResponse",
    "ReviewQueueResponse",
]