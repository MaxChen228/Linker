"""
全局錯誤處理器模組
提供統一的異常處理和響應轉換機制
"""

from __future__ import annotations

import traceback
from functools import wraps
from typing import Any, Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from core.exceptions import (
    APIException,
    ConfigException,
    DataException,
    FileOperationException,
    GeminiAPIException,
    LinkerError,
    ParseException,
    UserInputException,
    ValidationException,
)
from core.log_config import get_module_logger
from core.response import APIResponse

logger = get_module_logger(__name__)


class GlobalErrorHandler:
    """
    全局錯誤處理器

    負責將各種異常轉換為統一的API響應格式
    """

    # 異常類型映射字典
    EXCEPTION_MAPPING: dict[type[Exception], dict[str, Any]] = {
        # Linker自定義異常
        DataException: {
            "error_type": "數據錯誤",
            "default_message": "資料處理失敗",
            "log_level": "error"
        },
        ValidationException: {
            "error_type": "驗證錯誤",
            "default_message": "資料驗證失敗",
            "log_level": "warning"
        },
        APIException: {
            "error_type": "API錯誤",
            "default_message": "API調用失敗",
            "log_level": "error"
        },
        GeminiAPIException: {
            "error_type": "AI服務錯誤",
            "default_message": "AI服務不可用",
            "log_level": "error"
        },
        ConfigException: {
            "error_type": "配置錯誤",
            "default_message": "系統配置錯誤",
            "log_level": "error"
        },
        FileOperationException: {
            "error_type": "文件操作錯誤",
            "default_message": "文件操作失敗",
            "log_level": "error"
        },
        ParseException: {
            "error_type": "解析錯誤",
            "default_message": "資料解析失敗",
            "log_level": "warning"
        },
        UserInputException: {
            "error_type": "輸入錯誤",
            "default_message": "用戶輸入無效",
            "log_level": "info"
        },

        # Python標準異常
        ValueError: {
            "error_type": "數值錯誤",
            "default_message": "無效的參數值",
            "log_level": "warning"
        },
        TypeError: {
            "error_type": "類型錯誤",
            "default_message": "資料類型錯誤",
            "log_level": "warning"
        },
        KeyError: {
            "error_type": "缺少必要參數",
            "default_message": "缺少必要的資料欄位",
            "log_level": "warning"
        },
        FileNotFoundError: {
            "error_type": "文件不存在",
            "default_message": "指定的文件不存在",
            "log_level": "warning"
        },
        PermissionError: {
            "error_type": "權限錯誤",
            "default_message": "沒有足夠的權限執行此操作",
            "log_level": "error"
        },
        ConnectionError: {
            "error_type": "連接錯誤",
            "default_message": "網絡連接失敗",
            "log_level": "error"
        },
        TimeoutError: {
            "error_type": "超時錯誤",
            "default_message": "操作超時",
            "log_level": "warning"
        },

        # HTTP異常
        HTTPException: {
            "error_type": "HTTP錯誤",
            "default_message": "HTTP請求處理失敗",
            "log_level": "warning"
        },
    }

    @classmethod
    def handle(
        cls,
        exception: Exception,
        request_id: str | None = None,
        include_details: bool = False
    ) -> APIResponse:
        """
        處理異常並轉換為統一響應格式

        Args:
            exception: 要處理的異常
            request_id: 請求ID
            include_details: 是否包含詳細的錯誤信息（開發模式用）

        Returns:
            APIResponse: 統一格式的錯誤響應
        """

        # 獲取異常類型
        exc_type = type(exception)

        # 查找映射配置
        config = cls._find_exception_config(exc_type)

        # 提取錯誤信息
        # 對於LinkerError，使用原始message；對於其他異常，使用str(exception)
        if isinstance(exception, LinkerError):
            error_message = exception.message or config["default_message"]
        else:
            error_message = str(exception) or config["default_message"]
        error_type = config["error_type"]
        error_code = getattr(exception, 'error_code', exc_type.__name__.upper())

        # 記錄日誌
        cls._log_exception(exception, config["log_level"], request_id)

        # 構建響應資料
        response_data = None
        if include_details:
            response_data = {
                "exception_type": exc_type.__name__,
                "traceback": traceback.format_exc(),
            }

            # 添加LinkerError的詳細信息
            if isinstance(exception, LinkerError):
                response_data["details"] = exception.details

            # 添加HTTPException的狀態碼
            if isinstance(exception, HTTPException):
                response_data["status_code"] = exception.status_code

        return APIResponse.error(
            message=error_message,
            error_type=error_type,
            error_code=error_code,
            data=response_data,
            request_id=request_id,
        )

    @classmethod
    def _find_exception_config(cls, exc_type: type[Exception]) -> dict[str, Any]:
        """
        查找異常配置

        Args:
            exc_type: 異常類型

        Returns:
            異常配置字典
        """
        # 直接匹配
        if exc_type in cls.EXCEPTION_MAPPING:
            return cls.EXCEPTION_MAPPING[exc_type]

        # 基類匹配
        for mapped_type, config in cls.EXCEPTION_MAPPING.items():
            if issubclass(exc_type, mapped_type):
                return config

        # 默認配置
        return {
            "error_type": "未知錯誤",
            "default_message": "系統發生未預期的錯誤",
            "log_level": "error"
        }

    @classmethod
    def _log_exception(
        cls,
        exception: Exception,
        log_level: str,
        request_id: str | None = None
    ):
        """
        記錄異常日誌

        Args:
            exception: 異常物件
            log_level: 日誌級別
            request_id: 請求ID
        """
        context = {"request_id": request_id} if request_id else {}

        if log_level == "error":
            logger.log_exception(exception, context=context)
        elif log_level == "warning":
            logger.warning(f"Warning: {str(exception)}", extra=context)
        elif log_level == "info":
            logger.info(f"Info: {str(exception)}", extra=context)


# 裝飾器函數

def handle_api_errors(
    include_details: bool = False,
    default_message: str | None = None
):
    """
    API錯誤處理裝飾器

    自動捕獲並處理函數中拋出的異常，轉換為統一的API響應格式

    Args:
        include_details: 是否包含詳細錯誤信息（調試用）
        default_message: 默認錯誤消息

    Returns:
        裝飾器函數
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                # 檢查是否為async函數
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                # 提取request_id（如果存在）
                request_id = None
                for arg in args:
                    if hasattr(arg, 'state') and hasattr(arg.state, 'request_id'):
                        request_id = arg.state.request_id
                        break

                # 使用全局錯誤處理器處理異常
                error_response = GlobalErrorHandler.handle(
                    e,
                    request_id=request_id,
                    include_details=include_details
                )

                # 如果提供了默認消息，覆蓋原消息
                if default_message:
                    error_response.message = default_message

                return error_response.to_fastapi_response()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # 提取request_id（如果存在）
                request_id = None
                for arg in args:
                    if hasattr(arg, 'state') and hasattr(arg.state, 'request_id'):
                        request_id = arg.state.request_id
                        break

                # 使用全局錯誤處理器處理異常
                error_response = GlobalErrorHandler.handle(
                    e,
                    request_id=request_id,
                    include_details=include_details
                )

                # 如果提供了默認消息，覆蓋原消息
                if default_message:
                    error_response.message = default_message

                return error_response.to_fastapi_response()

        # 檢查函數是否為協程函數
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def handle_validation_errors(func: Callable) -> Callable:
    """
    驗證錯誤專用處理裝飾器

    專門處理資料驗證相關的錯誤
    """
    return handle_api_errors(
        include_details=True,
        default_message="資料驗證失敗，請檢查輸入格式"
    )(func)


def handle_file_errors(func: Callable) -> Callable:
    """
    文件操作錯誤專用處理裝飾器

    專門處理文件相關的錯誤
    """
    return handle_api_errors(
        include_details=False,
        default_message="文件操作失敗，請稍後再試"
    )(func)


# FastAPI異常處理器

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    FastAPI全局異常處理器

    捕獲所有未處理的異常並返回統一格式響應
    """
    request_id = getattr(request.state, 'request_id', None)

    response = GlobalErrorHandler.handle(
        exc,
        request_id=request_id,
        include_details=False  # 生產環境不暴露詳細錯誤
    )

    return response.to_fastapi_response()


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    FastAPI HTTP異常處理器

    專門處理HTTPException
    """
    request_id = getattr(request.state, 'request_id', None)

    response = APIResponse.error(
        message=exc.detail,
        error_type="HTTP錯誤",
        error_code=f"HTTP_{exc.status_code}",
        request_id=request_id,
    )

    return response.to_fastapi_response(status_code=exc.status_code)
