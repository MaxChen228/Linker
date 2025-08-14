"""
異步依賴注入示例 - 正確的 FastAPI 集成方式
"""

from pathlib import Path

from fastapi.templating import Jinja2Templates

from core.ai_service import AIService
from core.config import DATA_DIR
from core.database.adapter_fixed import KnowledgeManagerAdapter, get_knowledge_manager_async
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
ai = AIService()

# 全域適配器實例
_knowledge_adapter: KnowledgeManagerAdapter = None


def get_templates():
    """獲取模板服務"""
    return templates


def get_ai_service():
    """獲取 AI 服務"""
    return ai


async def get_knowledge_manager() -> KnowledgeManagerAdapter:
    """獲取知識管理器（異步版本）"""
    global _knowledge_adapter
    if _knowledge_adapter is None:
        # 從環境變數決定是否使用資料庫
        import os

        use_database = os.getenv("USE_DATABASE", "false").lower() == "true"
        _knowledge_adapter = await get_knowledge_manager_async(
            use_database=use_database, data_dir=str(DATA_DIR)
        )
    return _knowledge_adapter


def get_knowledge_assets():
    """獲取知識資產"""
    return assets


def get_logger():
    """獲取 logger"""
    return logger


# 生命週期管理
async def startup_event():
    """應用啟動時初始化"""
    logger.info("正在初始化知識管理器...")
    await get_knowledge_manager()
    logger.info("知識管理器初始化完成")


async def shutdown_event():
    """應用關閉時清理資源"""
    global _knowledge_adapter
    if _knowledge_adapter:
        logger.info("正在清理知識管理器資源...")
        await _knowledge_adapter.cleanup()
        _knowledge_adapter = None
        logger.info("資源清理完成")
