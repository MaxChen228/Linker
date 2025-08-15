"""
Utility routes for the Linker web application.
"""

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# TASK-34: 引入統一API端點管理系統，消除硬編碼
from web.config.api_endpoints import API_ENDPOINTS
from web.dependencies import STATIC_DIR, TEMPLATES_DIR

# TASK-34: 引入端口配置系統
try:
    from core.settings.ports import get_port_config

    _port_config_available = True
except ImportError:
    _port_config_available = False

router = APIRouter()


@router.get(API_ENDPOINTS.HEALTHZ)
def healthz():
    """健康檢查端點"""
    # 簡易健康檢查：確保模板與資料夾存在
    ok = TEMPLATES_DIR.exists() and STATIC_DIR.exists()
    return {"status": "ok" if ok else "degraded"}


@router.get(API_ENDPOINTS.CONFIG)
def get_config():
    """獲取前端所需的配置信息

    Returns:
        配置信息，包括端口、環境等
    """
    config = {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }

    # 如果端口配置可用，添加端口信息
    if _port_config_available:
        port_config = get_port_config()
        config.update(
            {
                "app_port": port_config.APP_PORT,
                "app_host": port_config.APP_HOST,
                "dev_ports": list(port_config.DEV_PORTS),
                "is_production": os.getenv("ENVIRONMENT", "development") == "production",
            }
        )
    else:
        # 回退到默認值
        config.update(
            {
                "app_port": int(os.getenv("PORT", "8000")),
                "app_host": os.getenv("HOST", "127.0.0.1"),
                "dev_ports": ["8000", "8001", "3000", "5000"],
                "is_production": False,
            }
        )

    return JSONResponse(content=config)
