"""
Dependency injection and shared services for the Linker web application.
"""
from pathlib import Path
from fastapi.templating import Jinja2Templates
from core.ai_service import AIService
from core.config import DATA_DIR
from core.knowledge import KnowledgeManager
from core.knowledge_assets import KnowledgeAssets
from core.log_config import get_module_logger

# 初始化模組 logger
logger = get_module_logger(__name__)

# 路徑配置
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 初始化服務（單例）
templates = Jinja2Templates(directory=TEMPLATES_DIR)
assets = KnowledgeAssets()
knowledge = KnowledgeManager(data_dir=str(DATA_DIR))
ai = AIService()

def get_templates():
    """獲取模板服務"""
    return templates

def get_ai_service():
    """獲取 AI 服務"""
    return ai

def get_knowledge_manager():
    """獲取知識管理器"""
    return knowledge

def get_knowledge_assets():
    """獲取知識資產"""
    return assets

def get_logger():
    """獲取 logger"""
    return logger