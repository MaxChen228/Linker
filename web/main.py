"""
Linker Web Application - Main Entry Point
"""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.log_config import get_module_logger
from core.version_manager import VersionManager
from web.dependencies import STATIC_DIR
from web.middleware import access_log_middleware, configure_logging

# 載入 .env 文件中的環境變數
load_dotenv()

# 初始化模組 logger
logger = get_module_logger(__name__)


def check_and_migrate_versions():
    """啟動時執行版本檢查和遷移"""
    version_manager = VersionManager()
    logger.info("檢查資料檔案版本...")

    try:
        results = version_manager.check_and_migrate_all()
        migrated = [f for f, status in results.items() if status is True]
        if migrated:
            logger.info(f"已自動遷移 {len(migrated)} 個檔案到最新版本")
            for file in migrated:
                logger.info(f"  - {Path(file).name}")
    except Exception as e:
        logger.warning(f"版本遷移警告: {e}")
        logger.info("系統將繼續使用現有檔案")


def create_app() -> FastAPI:
    """建立並配置 FastAPI 應用"""
    # 執行版本檢查
    check_and_migrate_versions()

    # 配置日誌
    configure_logging()

    # 建立 FastAPI 應用
    app = FastAPI(title="Linker", docs_url=None, redoc_url=None)

    # 掛載靜態檔案
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # 註冊中間件
    app.middleware("http")(access_log_middleware)

    # 註冊路由
    from web.routers import api_knowledge, calendar, knowledge, pages, patterns, practice, utils, test_async

    app.include_router(pages.router)
    app.include_router(practice.router)
    app.include_router(knowledge.router)
    app.include_router(patterns.router)
    app.include_router(calendar.router)  # 學習日曆路由
    app.include_router(utils.router)
    app.include_router(api_knowledge.router)  # 新增知識點 API 路由
    app.include_router(test_async.router)  # TASK-31 測試異步服務層

    logger.info("Linker Web Application initialized successfully")

    return app


# 建立應用實例
app = create_app()
