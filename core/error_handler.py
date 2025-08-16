"""
統一錯誤處理器模組

提供一個集中式的錯誤處理機制，旨在將各種原始異常轉換為統一的、
結構化的錯誤格式 (`UnifiedError`)，並提供一致的處理流程。

主要功能：
1.  **錯誤轉換**：將標準 Python 異常和自訂的 `LinkerError` 轉換為 `UnifiedError`。
2.  **錯誤分類**：根據錯誤類型自動推斷其類別 (`ErrorCategory`) 和嚴重性 (`ErrorSeverity`)。
3.  **日誌記錄**：根據錯誤的嚴重性，使用結構化的 JSON 格式記錄詳細的錯誤日誌。
4.  **降級策略**：判斷錯誤是否適用於降級處理（例如，從資料庫操作降級到使用快取）。
5.  **恢復建議**：為常見的錯誤類型提供對使用者或開發者友善的恢復建議。
6.  **裝飾器**：提供 `with_error_handling` 裝飾器，方便在函數或方法層級應用統一的錯誤處理邏輯。
"""

import asyncio
from functools import wraps
from typing import Any, Callable

from core.exceptions import (
    ErrorCategory,
    ErrorSeverity,
    LinkerError,
    UnifiedError,
)
from core.log_config import get_module_logger


class ErrorHandler:
    """統一錯誤處理器，負責轉換、記錄和處理應用程式中的異常。"""

    def __init__(self, mode: str = "database"):
        """
        初始化錯誤處理器。

        Args:
            mode: 當前的運行模式（例如 "database"），主要用於日誌記錄。
        """
        self.mode = mode
        self.logger = get_module_logger(self.__class__.__name__)
        self._fallback_enabled = True

    def handle_error(
        self, error: Exception, operation: str = "unknown", fallback_result: Any = None
    ) -> dict[str, Any]:
        """
        核心的錯誤處理方法。

        接收一個原始異常，將其轉換、記錄，並決定是否應觸發降級策略。

        Args:
            error: 捕獲到的原始異常。
            operation: 發生錯誤的操作名稱。
            fallback_result: 如果觸發降級，應返回的備用結果。

        Returns:
            一個包含結構化錯誤資訊和處理狀態的字典。
        """
        # 1. 將各種異常轉換為統一的 UnifiedError 格式
        unified_error = self._to_unified_error(error)

        # 2. 根據嚴重性記錄結構化日誌
        self._log_error(unified_error, operation)

        # 3. 判斷是否應觸發降級
        should_fallback = self._should_fallback(unified_error)

        error_response = {
            "success": False,
            "error": unified_error.to_dict(),
            "operation": operation,
            "mode": self.mode,
            "fallback_available": should_fallback and self._fallback_enabled,
        }

        if should_fallback and fallback_result is not None:
            error_response["fallback_result"] = fallback_result
            error_response["fallback_used"] = True
            self.logger.info(f"操作 '{operation}' 觸發降級並成功返回備用結果。")
        else:
            error_response["fallback_used"] = False

        return error_response

    def _to_unified_error(self, error: Exception) -> UnifiedError:
        """將任何異常轉換為 UnifiedError。"""
        if isinstance(error, UnifiedError):
            return error
        if isinstance(error, LinkerError):
            return self._convert_linker_error(error)
        return self._convert_standard_error(error)

    def _convert_linker_error(self, error: LinkerError) -> UnifiedError:
        """將自訂的 LinkerError 轉換為 UnifiedError。"""
        return UnifiedError(
            message=error.message,
            error_code=error.error_code,
            category=error.category,
            severity=error.severity,
            details=error.details,
            user_message=getattr(error, "user_message", None),
            recovery_suggestions=getattr(error, "recovery_suggestions", []),
        )

    def _convert_standard_error(self, error: Exception) -> UnifiedError:
        """將標準 Python 異常轉換為 UnifiedError。"""
        error_mappings = {
            ConnectionError: (ErrorCategory.DATABASE, "DB_CONNECTION_ERROR", ErrorSeverity.HIGH),
            FileNotFoundError: (ErrorCategory.FILE_IO, "FILE_NOT_FOUND", ErrorSeverity.MEDIUM),
            PermissionError: (ErrorCategory.FILE_IO, "PERMISSION_DENIED", ErrorSeverity.MEDIUM),
            ValueError: (ErrorCategory.VALIDATION, "INVALID_VALUE", ErrorSeverity.LOW),
            TypeError: (ErrorCategory.VALIDATION, "TYPE_ERROR", ErrorSeverity.LOW),
            OSError: (ErrorCategory.SYSTEM, "OS_ERROR", ErrorSeverity.HIGH),
            asyncio.TimeoutError: (ErrorCategory.NETWORK, "TIMEOUT_ERROR", ErrorSeverity.MEDIUM),
            KeyError: (ErrorCategory.VALIDATION, "KEY_ERROR", ErrorSeverity.LOW),
            IndexError: (ErrorCategory.VALIDATION, "INDEX_ERROR", ErrorSeverity.LOW),
            AttributeError: (ErrorCategory.SYSTEM, "ATTRIBUTE_ERROR", ErrorSeverity.MEDIUM),
            ImportError: (ErrorCategory.SYSTEM, "IMPORT_ERROR", ErrorSeverity.HIGH),
            MemoryError: (ErrorCategory.SYSTEM, "MEMORY_ERROR", ErrorSeverity.CRITICAL),
        }
        error_type = type(error)
        category, code, severity = error_mappings.get(error_type, (ErrorCategory.UNKNOWN, "UNKNOWN_ERROR", ErrorSeverity.MEDIUM))

        return UnifiedError(
            message=str(error),
            error_code=code,
            category=category,
            severity=severity,
            details={"original_type": error_type.__name__, "original_message": str(error)},
            recovery_suggestions=self._get_recovery_suggestions(category),
        )

    def _get_recovery_suggestions(self, category: ErrorCategory) -> list[str]:
        """根據錯誤類別提供通用的恢復建議。"""
        suggestions = {
            ErrorCategory.DATABASE: ["檢查資料庫服務是否正在運行", "確認資料庫連接配置是否正確", "稍後重試"],
            ErrorCategory.FILE_IO: ["檢查文件路徑和權限", "確認磁碟空間是否充足"],
            ErrorCategory.NETWORK: ["檢查您的網路連線", "確認遠端服務是否可用", "檢查防火牆或代理設定"],
            ErrorCategory.VALIDATION: ["檢查輸入的資料格式和內容是否符合要求"],
            ErrorCategory.CONCURRENCY: ["系統忙碌，請稍後重試", "避免同時提交重複的操作"],
        }
        return suggestions.get(category, ["請檢查日誌以獲取更多資訊。"])

    def _should_fallback(self, error: UnifiedError) -> bool:
        """根據錯誤的類別和嚴重性，判斷是否應觸發降級策略。"""
        fallback_categories = {ErrorCategory.DATABASE, ErrorCategory.NETWORK, ErrorCategory.CONCURRENCY, ErrorCategory.SYSTEM}
        fallback_severities = {ErrorSeverity.HIGH, ErrorSeverity.MEDIUM}
        return error.category in fallback_categories and error.severity in fallback_severities and self._fallback_enabled

    def _log_error(self, error: UnifiedError, operation: str) -> None:
        """根據錯誤的嚴重性，選擇合適的日誌級別來記錄錯誤。"""
        log_level_mapping = {
            ErrorSeverity.CRITICAL: self.logger.critical,
            ErrorSeverity.HIGH: self.logger.error,
            ErrorSeverity.MEDIUM: self.logger.warning,
            ErrorSeverity.LOW: self.logger.info,
            ErrorSeverity.INFO: self.logger.debug,
        }
        log_func = log_level_mapping.get(error.severity, self.logger.error)
        log_message = f"操作 '{operation}' 發生錯誤: {error.message}"
        log_func(log_message, extra=error.to_dict())

    def enable_fallback(self):
        """啟用降級策略。"""
        self._fallback_enabled = True
        self.logger.info("降級策略已啟用。")

    def disable_fallback(self):
        """禁用降級策略。"""
        self._fallback_enabled = False
        self.logger.info("降級策略已禁用。")


def with_error_handling(
    operation: str = "", fallback_result: Any = None, mode: str = "auto", enable_fallback: bool = True
):
    """
    一個裝飾器，用於將統一的錯誤處理邏輯應用於同步或異步函數。

    Args:
        operation: 操作的描述性名稱。
        fallback_result: 在觸發降級時返回的預設值。
        mode: 錯誤處理器的模式，'auto' 會嘗試自動檢測。
        enable_fallback: 是否為此特定操作啟用降級。
    """
    def decorator(func: Callable):
        handler = ErrorHandler(mode)
        if not enable_fallback:
            handler.disable_fallback()

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_response = handler.handle_error(e, operation or func.__name__, fallback_result)
                if error_response.get("fallback_used"):
                    return error_response["fallback_result"]
                error_info = error_response["error"]
                raise UnifiedError(**error_info) from e

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_response = handler.handle_error(e, operation or func.__name__, fallback_result)
                if error_response.get("fallback_used"):
                    return error_response["fallback_result"]
                error_info = error_response["error"]
                raise UnifiedError(**error_info) from e

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def create_error_response(error: Exception, operation: str = "unknown", mode: str = "unknown") -> dict[str, Any]:
    """
    一個便捷函數，用於創建標準化的錯誤回應字典。

    Args:
        error: 原始異常。
        operation: 操作名稱。
        mode: 運行模式。

    Returns:
        一個包含結構化錯誤資訊的字典。
    """
    handler = ErrorHandler(mode)
    return handler.handle_error(error, operation)


def log_error_with_context(error: Exception, context: dict[str, Any], operation: str = "unknown", mode: str = "unknown") -> None:
    """
    記錄帶有額外上下文的錯誤日誌。

    Args:
        error: 原始異常。
        context: 要附加到日誌中的上下文資訊。
        operation: 操作名稱。
        mode: 運行模式。
    """
    handler = ErrorHandler(mode)
    unified_error = handler._to_unified_error(error)
    unified_error.details["context"] = context
    handler._log_error(unified_error, operation)
