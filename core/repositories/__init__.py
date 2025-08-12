"""
JSON 文件操作抽象層

提供統一的 JSON 文件操作接口，包含原子性操作、備份機制、版本遷移和並發控制。
"""

from .base_repository import JSONRepository
from .knowledge_repository import KnowledgeRepository  
from .practice_repository import PracticeRepository
from .composite_repository import CompositeRepository
from .validators import (
    ValidationEngine, ValidationResult, ValidationSeverity,
    KnowledgePointValidator, PracticeRecordValidator, DataMigrator,
    validation_engine
)

__all__ = [
    'JSONRepository',
    'KnowledgeRepository', 
    'PracticeRepository',
    'CompositeRepository',
    'ValidationEngine',
    'ValidationResult',
    'ValidationSeverity',
    'KnowledgePointValidator',
    'PracticeRecordValidator',
    'DataMigrator',
    'validation_engine'
]