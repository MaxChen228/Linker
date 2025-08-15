"""
Dependency injection and shared services for the Linker web application.
"""

import threading
from pathlib import Path

from fastapi.templating import Jinja2Templates

from core.ai_service import AIService
from core.config import DATA_DIR, USE_DATABASE
from core.knowledge import KnowledgeManager
from core.knowledge_assets import KnowledgeAssets
from core.log_config import get_module_logger

# 條件導入資料庫適配器
if USE_DATABASE:
    from core.database.adapter import KnowledgeManagerAdapter, get_knowledge_manager_async

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
    """獲取知識管理器（支援資料庫/JSON 雙模式，線程安全）
    
    注意：這是同步版本，資料庫模式下功能受限。
    建議使用 get_knowledge_manager_async_dependency() 用於異步路由。
    """
    global _knowledge
    if _knowledge is None:
        with _knowledge_lock:
            # 雙重檢查鎖定模式
            if _knowledge is None:
                if USE_DATABASE:
                    logger.info("使用資料庫模式初始化知識管理器")
                    _knowledge = KnowledgeManagerAdapter(use_database=True)
                else:
                    logger.info("使用 JSON 模式初始化知識管理器")
                    _knowledge = KnowledgeManager(data_dir=str(DATA_DIR))
    return _knowledge


async def get_knowledge_manager_async_dependency():
    """獲取知識管理器（異步版本，支援完整資料庫功能）
    
    用於 FastAPI 異步路由的依賴注入。
    確保資料庫模式下的完整功能支援。
    """
    global _knowledge
    if _knowledge is None:
        with _knowledge_lock:
            # 雙重檢查鎖定模式
            if _knowledge is None:
                if USE_DATABASE:
                    logger.info("使用資料庫模式異步初始化知識管理器")
                    _knowledge = await get_knowledge_manager_async(use_database=True)
                else:
                    logger.info("使用 JSON 模式初始化知識管理器")
                    _knowledge = KnowledgeManager(data_dir=str(DATA_DIR))
    
    # 確保資料庫模式已完全初始化
    if USE_DATABASE and hasattr(_knowledge, '_ensure_initialized'):
        await _knowledge._ensure_initialized()
    
    return _knowledge


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
