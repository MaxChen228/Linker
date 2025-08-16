"""
自訂異常處理模組

此模組定義了應用程式中所有自訂的異常類別和相關的錯誤處理工具。
它建立了一個結構化的異常體系，便於捕捉、分類和處理不同類型的錯誤。

主要功能：
- `LinkerError`: 所有自訂異常的基礎類別，包含錯誤碼、類別、嚴重性等結構化資訊。
- 專門的異常類別：為資料庫、API、檔案操作、資料驗證等常見錯誤場景定義了具體的異常類。
- `UnifiedError`: 新一代的統一錯誤類別，用於標準化的錯誤處理流程。
- 錯誤處理裝飾器：提供 `with_retry` 和 `with_async_retry` 等裝飾器，簡化重試邏輯。
"""

import asyncio
import functools
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from core.log_config import get_module_logger

logger = get_module_logger(__name__)


class ErrorSeverity(Enum):
    """定義錯誤的嚴重性級別。"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INFO = "info"  # 用於非錯誤性但需要注意的資訊


class ErrorCategory(Enum):
    """定義錯誤的宏觀分類，用於錯誤路由和處理。"""

    SYSTEM = "system"
    DATABASE = "database"
    FILE_IO = "file_io"
    NETWORK = "network"
    VALIDATION = "validation"
    BUSINESS = "business"
    CONCURRENCY = "concurrency"
    UNKNOWN = "unknown"


class LinkerError(Exception):
    """
    應用程式所有自訂異常的基礎類別。
    提供結構化的錯誤資訊，包括錯誤碼、類別、嚴重性、詳細資訊和給使用者的建議。
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.recovery_suggestions = recovery_suggestions or []
        self.timestamp = datetime.now().isoformat()

    def _generate_user_message(self) -> str:
        """根據錯誤類別生成對使用者友善的預設錯誤訊息。"""
        return {
            ErrorCategory.DATABASE: "資料庫暫時無法連線，請稍後再試。",
            ErrorCategory.FILE_IO: "檔案操作失敗，請檢查檔案權限或路徑。",
            ErrorCategory.NETWORK: "網路連線異常，請檢查您的網路設定。",
            ErrorCategory.VALIDATION: "您輸入的資料格式不正確，請檢查後再試。",
            ErrorCategory.BUSINESS: "您的操作不符合業務規則。",
            ErrorCategory.CONCURRENCY: "系統忙碌中，請稍後再試。",
            ErrorCategory.SYSTEM: "系統發生非預期錯誤，請聯繫管理員。",
        }.get(self.category, "系統發生未知錯誤，請稍後再試。")

    def to_dict(self) -> dict[str, Any]:
        """將異常物件序列化為字典，方便日誌記錄或 API 回應。"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "recovery_suggestions": self.recovery_suggestions,
            "timestamp": self.timestamp,
        }

    def __str__(self):
        return f"[{self.error_code}] {self.message}" + (
            f" - Details: {self.details}" if self.details else ""
        )


# --- 特定領域的異常類別 ---


class APIError(LinkerError):
    """表示與外部 API 互動時發生的錯誤。"""

    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
    ):
        super().__init__(
            message,
            error_code="API_ERROR",
            category=ErrorCategory.NETWORK,
            details={
                "api_name": api_name,
                "status_code": status_code,
                "response": str(response)[:500] if response else None,
            },
        )


class GeminiAPIError(APIError):
    """表示與 Gemini API 互動時的特定錯誤。"""

    def __init__(self, message: str, model: Optional[str] = None, prompt: Optional[str] = None):
        super().__init__(message, api_name="Gemini")
        self.details.update({"model": model, "prompt_preview": prompt[:200] if prompt else None})


class DataError(LinkerError):
    """表示資料處理或格式相關的錯誤。"""

    def __init__(
        self, message: str, data_type: Optional[str] = None, file_path: Optional[str] = None
    ):
        super().__init__(
            message,
            error_code="DATA_ERROR",
            category=ErrorCategory.VALIDATION,
            details={"data_type": data_type, "file_path": file_path},
        )


class ValidationError(LinkerError):
    """表示資料驗證失敗的錯誤。"""

    def __init__(self, message: str, field: str, value: Any, expected_type: Optional[str] = None):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            details={"field": field, "value": str(value), "expected_type": expected_type},
        )


class ConfigError(LinkerError):
    """表示應用程式配置錯誤。"""

    def __init__(self, message: str, config_key: str, config_file: Optional[str] = None):
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            details={"config_key": config_key, "config_file": config_file},
        )


class FileOperationError(LinkerError):
    """表示檔案系統操作（讀、寫、刪除）失敗。"""

    def __init__(
        self,
        message: str,
        operation: str,
        file_path: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message,
            error_code="FILE_OPERATION_ERROR",
            category=ErrorCategory.FILE_IO,
            details={
                "operation": operation,
                "file_path": file_path,
                "original_error": str(original_error),
            },
        )


class ParseError(LinkerError):
    """表示解析資料（如 JSON、XML）失敗。"""

    def __init__(
        self,
        message: str,
        parse_type: str,
        content: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message,
            error_code="PARSE_ERROR",
            category=ErrorCategory.VALIDATION,
            details={
                "parse_type": parse_type,
                "content_preview": content[:100] if content else None,
                "original_error": str(original_error),
            },
        )


class UserInputError(LinkerError):
    """表示使用者輸入無效。"""

    def __init__(
        self, message: str, input_type: str, user_input: Any, valid_options: Optional[list] = None
    ):
        super().__init__(
            message,
            error_code="USER_INPUT_ERROR",
            category=ErrorCategory.BUSINESS,
            severity=ErrorSeverity.LOW,
            details={
                "input_type": input_type,
                "user_input": str(user_input),
                "valid_options": valid_options,
            },
        )


class KnowledgeNotFoundError(LinkerError):
    """表示找不到指定的知識點。"""

    def __init__(self, point_id: Any, message: Optional[str] = None):
        super().__init__(
            message or f"知識點 ID '{point_id}' 不存在。",
            error_code="KNOWLEDGE_NOT_FOUND",
            category=ErrorCategory.BUSINESS,
            details={"point_id": point_id},
        )


# --- 資料庫和遷移相關異常 ---


class DatabaseError(LinkerError):
    """表示資料庫操作相關的錯誤。"""

    def __init__(
        self, message: str, operation: str, original_error: Optional[Exception] = None, **kwargs
    ):
        super().__init__(
            message,
            error_code="DATABASE_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            details={"operation": operation, "original_error": str(original_error), **kwargs},
        )


class MigrationError(LinkerError):
    """表示資料庫遷移失敗。"""

    def __init__(
        self, message: str, migration_step: str, original_error: Optional[Exception] = None
    ):
        super().__init__(
            message,
            error_code="MIGRATION_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.CRITICAL,
            details={"migration_step": migration_step, "original_error": str(original_error)},
        )


# --- 異步和重試相關異常 ---


class AsyncOperationError(LinkerError):
    """表示異步操作失敗。"""

    def __init__(self, message: str, operation: str, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            error_code="ASYNC_OPERATION_ERROR",
            category=ErrorCategory.SYSTEM,
            details={"operation": operation, "original_error": str(original_error)},
        )


class RecoverableError(LinkerError):
    """表示一個可重試的、暫時性的錯誤。"""

    def __init__(self, message: str, retry_count: int, original_error: Optional[Exception] = None):
        super().__init__(
            message,
            error_code="RECOVERABLE_ERROR",
            category=ErrorCategory.CONCURRENCY,
            severity=ErrorSeverity.MEDIUM,
            details={"retry_count": retry_count, "original_error": str(original_error)},
        )


# --- 重試裝飾器 ---


def with_retry(
    max_retries: int = 3,
    backoff_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    exponential_backoff: bool = True,
):
    """
    一個同步函數的重試裝飾器，支援指數退避。
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise RecoverableError(
                            f"函數 {func.__name__} 在 {max_retries} 次重試後失敗。",
                            retry_count=attempt,
                            original_error=e,
                        ) from e
                    delay = backoff_delay * (2**attempt if exponential_backoff else 1)
                    logger.warning(
                        f"函數 {func.__name__} 發生錯誤，將在 {delay:.2f} 秒後重試 (第 {attempt + 1} 次): {e}"
                    )
                    time.sleep(delay)
            return None

        return wrapper

    return decorator


def with_async_retry(
    max_retries: int = 3,
    backoff_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    exponential_backoff: bool = True,
):
    """
    一個異步函數的重試裝飾器，支援指數退避。
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise AsyncOperationError(
                            f"異步函數 {func.__name__} 在 {max_retries} 次重試後失敗。",
                            operation=func.__name__,
                            original_error=e,
                        ) from e
                    delay = backoff_delay * (2**attempt if exponential_backoff else 1)
                    logger.warning(
                        f"異步函數 {func.__name__} 發生錯誤，將在 {delay:.2f} 秒後重試 (第 {attempt + 1} 次): {e}"
                    )
                    await asyncio.sleep(delay)
            return None

        return wrapper

    return decorator


# --- 新一代統一錯誤類別 ---


class UnifiedError(LinkerError):
    """新一代的統一錯誤類別，建議所有新的錯誤處理都使用此類別或其子類。"""

    pass


class SystemError(UnifiedError):
    """表示嚴重的系統級錯誤。"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="SYSTEM_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            **kwargs,
        )


class FileIOError(UnifiedError):
    """表示檔案 I/O 錯誤。"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_code="FILE_IO_ERROR", category=ErrorCategory.FILE_IO, **kwargs
        )


class NetworkError(UnifiedError):
    """表示網路相關錯誤。"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_code="NETWORK_ERROR", category=ErrorCategory.NETWORK, **kwargs
        )


class BusinessLogicError(UnifiedError):
    """表示違反業務邏輯的錯誤。"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            error_code="BUSINESS_LOGIC_ERROR",
            category=ErrorCategory.BUSINESS,
            severity=ErrorSeverity.LOW,
            **kwargs,
        )


class ConcurrencyError(UnifiedError):
    """表示並發相關的錯誤，例如資源鎖定失敗。"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, error_code="CONCURRENCY_ERROR", category=ErrorCategory.CONCURRENCY, **kwargs
        )
