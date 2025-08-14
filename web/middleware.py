"""
Middleware configurations for the Linker web application.
"""

import logging
import time
from uuid import uuid4

from fastapi import Request

from core.log_config import get_module_logger

# 初始化模組 logger
logger = get_module_logger(__name__)


class IgnoreFaviconFilter(logging.Filter):
    """過濾掉 favicon.ico 的 404 錯誤日誌"""

    def filter(self, record):
        # 檢查是否是 favicon.ico 的 404 錯誤
        message = record.getMessage()
        return not ("favicon.ico" in message and "404" in message)


def configure_logging():
    """配置日誌過濾器"""
    # 為 uvicorn.access logger 添加過濾器
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.addFilter(IgnoreFaviconFilter())


async def access_log_middleware(request: Request, call_next):
    """HTTP 訪問日誌中間件"""
    start = time.time()
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = None

    # 過濾 Chrome DevTools 和其他開發工具的探測請求
    skip_logging = any(
        [
            "/.well-known/appspecific" in str(request.url.path),
            "/favicon.ico" in str(request.url.path),
            "/__vite_" in str(request.url.path),
        ]
    )

    try:
        return await call_next(request)
    except Exception as e:
        if not skip_logging:
            logger.log_exception(
                e,
                context={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
        raise
    finally:
        elapsed = time.time() - start
        if response and not skip_logging:
            logger.debug(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {elapsed:.3f}s",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code if response else 500,
                    "duration_ms": int(elapsed * 1000),
                },
            )
