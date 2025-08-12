"""
服務層模組
提供統一的業務邏輯處理介面
"""

from .base_service import BaseService, ServiceResult
from .practice_service import PracticeService
from .knowledge_service import KnowledgeService, SaveMistakeRequest
from .error_processing_service import ErrorProcessingService
from .practice_record_service import PracticeRecordService

# 知識點管理輔助函數
from . import knowledge_helpers

__all__ = [
    'BaseService',
    'ServiceResult', 
    'PracticeService',
    'KnowledgeService',
    'SaveMistakeRequest',
    'ErrorProcessingService',
    'PracticeRecordService',
    'knowledge_helpers',
]