"""
統一錯誤處理器
提供 JSON 和 Database 模式的統一錯誤處理機制

包含功能：
1. 統一錯誤轉換和格式化
2. 錯誤嚴重性評估
3. 降級策略判斷
4. 用戶友好的錯誤訊息
5. 錯誤日誌記錄
6. 錯誤處理裝飾器
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
    """統一錯誤處理器"""

    def __init__(self, mode: str = "json"):
        """
        初始化錯誤處理器

        Args:
            mode: 運行模式 "json" 或 "database"
        """
        self.mode = mode
        self.logger = get_module_logger(self.__class__.__name__)
        self._fallback_enabled = True

    def handle_error(
        self, error: Exception, operation: str = "unknown", fallback_result: Any = None
    ) -> dict[str, Any]:
        """
        統一錯誤處理邏輯

        Args:
            error: 原始錯誤
            operation: 操作名稱
            fallback_result: 降級結果

        Returns:
            統一格式的錯誤響應
        """

        # 轉換為統一錯誤格式
        if isinstance(error, UnifiedError):
            unified_error = error
        elif isinstance(error, LinkerError):
            unified_error = self._convert_linker_error(error)
        else:
            unified_error = self._convert_to_unified_error(error)

        # 記錄錯誤日誌
        self._log_error(unified_error, operation)

        # 決定降級策略
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
            self.logger.info(f"錯誤降級成功: {operation}")
        else:
            error_response["fallback_used"] = False

        return error_response

    def _convert_linker_error(self, error: LinkerError) -> UnifiedError:
        """轉換 LinkerError 為 UnifiedError"""
        # 如果 LinkerError 已經有 category 和 severity，直接使用
        if hasattr(error, "category") and hasattr(error, "severity"):
            return UnifiedError(
                message=error.message,
                error_code=error.error_code,
                category=error.category,
                severity=error.severity,
                details=error.details,
                user_message=getattr(error, "user_message", None),
                recovery_suggestions=getattr(error, "recovery_suggestions", []),
            )

        # 根據錯誤類型推斷 category 和 severity
        category_mapping = {
            "DatabaseError": ErrorCategory.DATABASE,
            "FileOperationError": ErrorCategory.FILE_IO,
            "ValidationError": ErrorCategory.VALIDATION,
            "ConfigError": ErrorCategory.SYSTEM,
            "APIError": ErrorCategory.NETWORK,
            "ParseError": ErrorCategory.VALIDATION,
            "UserInputError": ErrorCategory.BUSINESS,
            "KnowledgeNotFoundError": ErrorCategory.BUSINESS,
            "MigrationError": ErrorCategory.DATABASE,
            "AsyncOperationError": ErrorCategory.SYSTEM,
        }

        error_class = error.__class__.__name__
        category = category_mapping.get(error_class, ErrorCategory.UNKNOWN)

        severity_mapping = {
            ErrorCategory.DATABASE: ErrorSeverity.HIGH,
            ErrorCategory.SYSTEM: ErrorSeverity.CRITICAL,
            ErrorCategory.FILE_IO: ErrorSeverity.MEDIUM,
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION: ErrorSeverity.LOW,
            ErrorCategory.BUSINESS: ErrorSeverity.LOW,
        }
        severity = severity_mapping.get(category, ErrorSeverity.MEDIUM)

        return UnifiedError(
            message=error.message,
            error_code=error.error_code,
            category=category,
            severity=severity,
            details=error.details,
        )

    def _convert_to_unified_error(self, error: Exception) -> UnifiedError:
        """轉換標準異常為統一錯誤格式"""
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
        category, error_code, severity = error_mappings.get(
            error_type, (ErrorCategory.UNKNOWN, "UNKNOWN_ERROR", ErrorSeverity.MEDIUM)
        )

        # 針對特定錯誤類型提供恢復建議
        recovery_suggestions = self._get_recovery_suggestions(category, error_type, str(error))

        return UnifiedError(
            message=str(error),
            error_code=error_code,
            category=category,
            severity=severity,
            details={"original_type": error_type.__name__, "original_message": str(error)},
            recovery_suggestions=recovery_suggestions,
        )

    def _get_recovery_suggestions(
        self, category: ErrorCategory, error_type: type, error_message: str
    ) -> list[str]:
        """根據錯誤類型提供恢復建議"""
        suggestions = []

        if category == ErrorCategory.DATABASE:
            suggestions.extend(
                [
                    "檢查資料庫連接是否正常",
                    "確認資料庫服務正在運行",
                    "檢查連接池配置",
                    "嘗試重新連接資料庫",
                ]
            )
        elif category == ErrorCategory.FILE_IO:
            suggestions.extend(
                [
                    "檢查文件是否存在",
                    "確認文件權限設置正確",
                    "檢查磁碟空間是否充足",
                    "確認路徑是否正確",
                ]
            )
        elif category == ErrorCategory.NETWORK:
            suggestions.extend(
                ["檢查網路連接", "確認 API 端點可訪問", "檢查防火牆設置", "稍後重試操作"]
            )
        elif category == ErrorCategory.VALIDATION:
            suggestions.extend(
                [
                    "檢查輸入數據格式",
                    "確認必需字段已填寫",
                    "驗證數據類型是否正確",
                    "參考 API 文檔格式要求",
                ]
            )
        elif category == ErrorCategory.CONCURRENCY:
            suggestions.extend(
                ["稍後重試操作", "檢查是否有重複操作", "確認系統負載正常", "避免高頻率請求"]
            )

        return suggestions

    def _should_fallback(self, error: UnifiedError) -> bool:
        """判斷是否應該降級"""
        # 支持降級的錯誤類別
        fallback_categories = {
            ErrorCategory.DATABASE,
            ErrorCategory.NETWORK,
            ErrorCategory.CONCURRENCY,
            ErrorCategory.SYSTEM,
        }

        # 支持降級的嚴重性級別
        fallback_severities = {ErrorSeverity.HIGH, ErrorSeverity.MEDIUM}

        return (
            error.category in fallback_categories
            and error.severity in fallback_severities
            and self._fallback_enabled
        )

    def _log_error(self, error: UnifiedError, operation: str) -> None:
        """統一錯誤日誌記錄"""
        log_level_mapping = {
            ErrorSeverity.CRITICAL: self.logger.critical,
            ErrorSeverity.HIGH: self.logger.error,
            ErrorSeverity.MEDIUM: self.logger.warning,
            ErrorSeverity.LOW: self.logger.info,
            ErrorSeverity.INFO: self.logger.debug,
        }

        log_func = log_level_mapping.get(error.severity, self.logger.error)

        log_message = f"[{self.mode.upper()}] {operation}: {error.message}"
        log_func(
            log_message,
            extra={
                "error_code": error.error_code,
                "category": error.category.value,
                "severity": error.severity.value,
                "details": error.details,
                "operation": operation,
                "mode": self.mode,
                "timestamp": error.timestamp,
            },
        )

    def enable_fallback(self):
        """啟用降級策略"""
        self._fallback_enabled = True
        self.logger.info(f"[{self.mode.upper()}] 降級策略已啟用")

    def disable_fallback(self):
        """禁用降級策略"""
        self._fallback_enabled = False
        self.logger.info(f"[{self.mode.upper()}] 降級策略已禁用")


def with_error_handling(
    operation: str = "",
    fallback_result: Any = None,
    mode: str = "auto",
    enable_fallback: bool = True,
):
    """
    錯誤處理裝飾器

    Args:
        operation: 操作名稱
        fallback_result: 降級結果
        mode: 運行模式，"auto" 自動檢測
        enable_fallback: 是否啟用降級
    """

    def decorator(func: Callable):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 自動檢測模式
                detected_mode = mode
                if mode == "auto":
                    # 根據類名或參數檢測模式
                    if args:
                        instance_name = str(type(args[0])).lower()
                        if "adapter" in instance_name or "database" in instance_name:
                            detected_mode = "database"
                        else:
                            detected_mode = "json"
                    else:
                        detected_mode = "unknown"

                handler = ErrorHandler(detected_mode)
                if not enable_fallback:
                    handler.disable_fallback()

                error_response = handler.handle_error(
                    e, operation or func.__name__, fallback_result
                )

                # 如果有降級結果，返回降級結果
                if error_response.get("fallback_used", False):
                    return error_response["fallback_result"]

                # 否則拋出統一錯誤
                error_info = error_response["error"]
                raise UnifiedError(
                    message=f"{operation or func.__name__} 失敗: {error_info['message']}",
                    error_code=error_info["error_code"],
                    category=ErrorCategory(error_info["category"]),
                    severity=ErrorSeverity(error_info["severity"]),
                )

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # 自動檢測模式
                detected_mode = mode
                if mode == "auto":
                    if args:
                        instance_name = str(type(args[0])).lower()
                        if "adapter" in instance_name or "database" in instance_name:
                            detected_mode = "database"
                        else:
                            detected_mode = "json"
                    else:
                        detected_mode = "unknown"

                handler = ErrorHandler(detected_mode)
                if not enable_fallback:
                    handler.disable_fallback()

                error_response = handler.handle_error(
                    e, operation or func.__name__, fallback_result
                )

                # 如果有降級結果，返回降級結果
                if error_response.get("fallback_used", False):
                    return error_response["fallback_result"]

                # 否則拋出統一錯誤
                error_info = error_response["error"]
                raise UnifiedError(
                    message=f"{operation or func.__name__} 失敗: {error_info['message']}",
                    error_code=error_info["error_code"],
                    category=ErrorCategory(error_info["category"]),
                    severity=ErrorSeverity(error_info["severity"]),
                )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def create_error_response(
    error: Exception, operation: str = "unknown", mode: str = "unknown"
) -> dict[str, Any]:
    """
    創建統一格式的錯誤響應

    Args:
        error: 錯誤對象
        operation: 操作名稱
        mode: 運行模式

    Returns:
        統一格式的錯誤響應
    """
    handler = ErrorHandler(mode)
    return handler.handle_error(error, operation)


def log_error_with_context(
    error: Exception, context: dict[str, Any], operation: str = "unknown", mode: str = "unknown"
) -> None:
    """
    記錄帶上下文的錯誤日誌

    Args:
        error: 錯誤對象
        context: 上下文信息
        operation: 操作名稱
        mode: 運行模式
    """
    handler = ErrorHandler(mode)

    # 如果是統一錯誤，添加上下文到詳細信息
    if isinstance(error, UnifiedError):
        error.details.update({"context": context})

    handler._log_error(
        handler._convert_to_unified_error(error) if not isinstance(error, UnifiedError) else error,
        operation,
    )
