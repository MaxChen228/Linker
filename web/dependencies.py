"""
Dependency injection and shared services for the Linker web application.
"""

import threading
from pathlib import Path

from fastapi.templating import Jinja2Templates

from core.ai_service import AIService
from core.config import DATA_DIR
# TASK-31: 舊的適配器已廢棄，不再導入
# from core.database.simplified_adapter import KnowledgeManagerAdapter, get_knowledge_manager_async
from core.knowledge_assets import KnowledgeAssets
from core.log_config import get_module_logger
from core.services import AsyncKnowledgeService, get_service_registry

# 初始化模組 logger
logger = get_module_logger(__name__)

# 路徑配置
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 全域變數儲存單例實例（線程安全）
_templates = None
_assets = None
_knowledge = None
_ai = None

# 初始化鎖保護
_templates_lock = threading.Lock()
_assets_lock = threading.Lock()
_knowledge_lock = threading.Lock()
_ai_lock = threading.Lock()


def get_templates():
    """獲取模板服務（線程安全）"""
    global _templates
    if _templates is None:
        with _templates_lock:
            # 雙重檢查鎖定模式
            if _templates is None:
                _templates = Jinja2Templates(directory=TEMPLATES_DIR)
                logger.debug("初始化 Jinja2Templates")
    return _templates


def get_ai_service():
    """獲取 AI 服務（線程安全）"""
    global _ai
    if _ai is None:
        with _ai_lock:
            # 雙重檢查鎖定模式
            if _ai is None:
                _ai = AIService()
                logger.debug("初始化 AIService")
    return _ai


def get_knowledge_manager():
    """獲取知識管理器（純資料庫模式，線程安全）

    ⚠️ 已廢棄 (TASK-31)：請使用 get_async_knowledge_service() 替代
    原因：依賴已廢棄的 SimplifiedDatabaseAdapter
    """
    import warnings
    warnings.warn(
        "get_knowledge_manager() 已廢棄。請使用 get_async_knowledge_service() 替代。",
        DeprecationWarning,
        stacklevel=2
    )
    raise RuntimeError("get_knowledge_manager() 已廢棄，請使用 get_async_knowledge_service() 替代")


async def get_knowledge_manager_async_dependency():
    """獲取知識管理器（異步版本，純資料庫模式）

    ⚠️ 已廢棄 (TASK-31)：請使用 get_async_knowledge_service() 替代
    原因：依賴已廢棄的 SimplifiedDatabaseAdapter
    """
    import warnings
    warnings.warn(
        "get_knowledge_manager_async_dependency() 已廢棄。請使用 get_async_knowledge_service() 替代。",
        DeprecationWarning,
        stacklevel=2
    )
    raise RuntimeError("get_knowledge_manager_async_dependency() 已廢棄，請使用 get_async_knowledge_service() 替代")


def get_knowledge_assets():
    """獲取知識資產（線程安全）"""
    global _assets
    if _assets is None:
        with _assets_lock:
            # 雙重檢查鎖定模式
            if _assets is None:
                _assets = KnowledgeAssets()
                logger.debug("初始化 KnowledgeAssets")
    return _assets


def get_logger():
    """獲取 logger"""
    return logger


async def get_async_knowledge_service():
    """獲取純異步知識服務 - TASK-31
    
    這是新的純異步服務層，用於替代 SimplifiedDatabaseAdapter。
    完全避免事件循環衝突問題，提供更好的性能和可維護性。
    
    Returns:
        AsyncKnowledgeService: 純異步知識服務實例
    """
    registry = get_service_registry()
    service = await registry.get_service("knowledge")
    
    if not service:
        logger.error("無法獲取異步知識服務")
        raise RuntimeError("異步知識服務不可用")
    
    return service
