"""
Dependency injection and shared services for the Linker web application.
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

from core.ai_service import AIService
from core.config import DATA_DIR, USE_DATABASE
from core.knowledge import KnowledgeManager
from core.knowledge_assets import KnowledgeAssets
from core.log_config import get_module_logger

# 條件導入資料庫適配器
if USE_DATABASE:
    from core.database.adapter import KnowledgeManagerAdapter

# 初始化模組 logger
logger = get_module_logger(__name__)

# 路徑配置
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 全域變數儲存單例實例
_templates = None
_assets = None
_knowledge = None
_ai = None


def get_templates():
    """獲取模板服務"""
    global _templates
    if _templates is None:
        _templates = Jinja2Templates(directory=TEMPLATES_DIR)
    return _templates


def get_ai_service():
    """獲取 AI 服務"""
    global _ai
    if _ai is None:
        _ai = AIService()
    return _ai


def get_knowledge_manager():
    """獲取知識管理器（支援資料庫/JSON 雙模式）"""
    global _knowledge
    if _knowledge is None:
        if USE_DATABASE:
            logger.info("使用資料庫模式初始化知識管理器")
            _knowledge = KnowledgeManagerAdapter(use_database=True)
        else:
            logger.info("使用 JSON 模式初始化知識管理器")
            _knowledge = KnowledgeManager(data_dir=str(DATA_DIR))
    return _knowledge


def get_knowledge_assets():
    """獲取知識資產"""
    global _assets
    if _assets is None:
        _assets = KnowledgeAssets()
    return _assets


def get_logger():
    """獲取 logger"""
    return logger
