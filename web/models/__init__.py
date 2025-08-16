"""
Web API 模型包
包含所有 API 請求和響應的 Pydantic 模型
"""

from .validation import (
    BatchReq,
    CompleteReviewRequest,
    ConfirmKnowledgeRequest,
    DeleteKnowReq,
    DeleteOldPointsRequest,
    EditKnowReq,
    GenerateQuestionRequest,
    GradeAnswerRequest,
    NotesRequest,
    PendingKnowledgePoint,
    TagsRequest,
)

__all__ = [
    "BatchReq",
    "CompleteReviewRequest",
    "ConfirmKnowledgeRequest",
    "DeleteKnowReq",
    "DeleteOldPointsRequest",
    "EditKnowReq",
    "GenerateQuestionRequest",
    "GradeAnswerRequest",
    "NotesRequest",
    "PendingKnowledgePoint",
    "TagsRequest",
]
