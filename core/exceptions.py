"""
異常處理模組
提供統一的異常類型和錯誤處理機制

包含功能：
1. 基礎異常類型
2. 數據庫相關異常
3. 異步異常處理裝飾器
4. 自動重試機制
5. 降級處理策略
6. 異常監控和告警
"""

import asyncio
import functools
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

from core.log_config import get_module_logger

logger = get_module_logger(__name__)


class ErrorSeverity(Enum):
    """錯誤嚴重性級別"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    INFO = "info"  # 新增：僅信息性錯誤


class ErrorCategory(Enum):
    """錯誤分類 - 用於統一錯誤處理"""

    SYSTEM = "system"  # 系統錯誤
    DATABASE = "database"  # 資料庫錯誤
    FILE_IO = "file_io"  # 文件IO錯誤
    NETWORK = "network"  # 網路錯誤
    VALIDATION = "validation"  # 數據驗證錯誤
    BUSINESS = "business"  # 業務邏輯錯誤
    CONCURRENCY = "concurrency"  # 並發錯誤
    UNKNOWN = "unknown"  # 未知錯誤


class LinkerError(Exception):
    """
    Linker 應用基礎異常類
    所有自定義異常都應該繼承此類
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
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
        """生成用戶友好的錯誤訊息"""
        user_messages = {
            ErrorCategory.DATABASE: "資料庫暫時無法連接，請稍後再試",
            ErrorCategory.FILE_IO: "文件操作失敗，請檢查文件權限",
            ErrorCategory.NETWORK: "網路連接異常，請檢查網路設置",
            ErrorCategory.VALIDATION: "輸入的數據格式不正確",
            ErrorCategory.BUSINESS: "操作不符合業務規則",
            ErrorCategory.CONCURRENCY: "系統忙碌中，請稍後再試",
            ErrorCategory.SYSTEM: "系統發生錯誤，請聯繫管理員",
        }
        return user_messages.get(self.category, "系統發生未知錯誤")

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
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
        if self.details:
            return f"[{self.error_code}] {self.message} - Details: {self.details}"
        return f"[{self.error_code}] {self.message}"


class APIError(LinkerError):
    """API調用相關異常"""

    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            error_code="API_ERROR",
            details={
                "api_name": api_name,
                "status_code": status_code,
                "response": str(response) if response else None,
            },
        )
        self.api_name = api_name
        self.status_code = status_code
        self.response = response


class GeminiAPIError(APIError):
    """Gemini API 特定異常"""

    def __init__(self, message: str, model: Optional[str] = None, prompt: Optional[str] = None):
        super().__init__(message=message, api_name="Gemini")
        # 添加額外的詳細信息
        self.details.update({"model": model, "prompt_preview": prompt[:100] if prompt else None})


class DataError(LinkerError):
    """數據處理相關異常"""

    def __init__(
        self, message: str, data_type: Optional[str] = None, file_path: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="DATA_ERROR",
            details={"data_type": data_type, "file_path": file_path},
        )


class ValidationError(LinkerError):
    """數據驗證異常"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected_type: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": str(value), "expected_type": expected_type},
        )


class ConfigError(LinkerError):
    """配置相關異常"""

    def __init__(
        self, message: str, config_key: Optional[str] = None, config_file: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details={"config_key": config_key, "config_file": config_file},
        )


class FileOperationError(LinkerError):
    """文件操作異常"""

    def __init__(
        self,
        message: str,
        operation: str,
        file_path: str,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code="FILE_OPERATION_ERROR",
            details={
                "operation": operation,
                "file_path": file_path,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.original_error = original_error


class ParseError(LinkerError):
    """解析異常（JSON、文本等）"""

    def __init__(
        self,
        message: str,
        parse_type: str,
        content: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code="PARSE_ERROR",
            details={
                "parse_type": parse_type,
                "content_preview": content[:100] if content else None,
                "original_error": str(original_error) if original_error else None,
            },
        )


class UserInputError(LinkerError):
    """用戶輸入異常"""

    def __init__(
        self,
        message: str,
        input_type: str,
        user_input: Optional[str] = None,
        valid_options: Optional[list] = None,
    ):
        super().__init__(
            message=message,
            error_code="USER_INPUT_ERROR",
            details={
                "input_type": input_type,
                "user_input": user_input,
                "valid_options": valid_options,
            },
        )


class KnowledgeNotFoundError(LinkerError):
    """知識點不存在異常"""

    def __init__(
        self,
        point_id: str,
        message: Optional[str] = None,
    ):
        if message is None:
            message = f"知識點ID '{point_id}' 不存在"
        super().__init__(
            message=message,
            error_code="KNOWLEDGE_NOT_FOUND",
            details={"point_id": point_id},
        )
        self.point_id = point_id


# 錯誤處理工具函數


def handle_api_error(func):
    """
    API錯誤處理裝飾器
    自動捕獲並轉換API相關異常
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError:
            raise  # 直接重新拋出已經是APIException的異常
        except Exception as e:
            # 將其他異常轉換為APIException
            raise APIError(message=f"API調用失敗: {str(e)}", api_name=func.__name__) from e

    return wrapper


def handle_file_operation(operation: str):
    """
    文件操作錯誤處理裝飾器

    Args:
        operation: 操作類型（read, write, delete等）
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileOperationError:
                raise  # 直接重新拋出
            except OSError as e:
                # 嘗試從參數中提取文件路徑
                file_path = kwargs.get("file_path", "")
                if not file_path and args:
                    # 假設第一個參數可能是self，第二個是file_path
                    file_path = args[1] if len(args) > 1 else str(args[0])

                raise FileOperationError(
                    message=f"文件{operation}操作失敗",
                    operation=operation,
                    file_path=str(file_path),
                    original_error=e,
                ) from e
            except Exception as e:
                raise LinkerError(
                    message=f"文件操作時發生未預期的錯誤: {str(e)}",
                    error_code="UNEXPECTED_FILE_ERROR",
                ) from e

        return wrapper

    return decorator


def safe_parse_json(content: str, default: Any = None) -> Any:
    """
    安全解析JSON

    Args:
        content: 要解析的JSON字符串
        default: 解析失敗時的默認值

    Returns:
        解析結果或默認值

    Raises:
        ParseException: 當default為None且解析失敗時
    """
    import json

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        if default is not None:
            return default
        raise ParseError(
            message="JSON解析失敗", parse_type="JSON", content=content, original_error=e
        ) from e


def validate_input(
    value: Any,
    valid_options: list = None,
    value_type: type = None,
    min_value: Any = None,
    max_value: Any = None,
    field_name: str = "input",
) -> Any:
    """
    驗證輸入值

    Args:
        value: 要驗證的值
        valid_options: 有效選項列表
        value_type: 期望的類型
        min_value: 最小值
        max_value: 最大值
        field_name: 字段名稱（用於錯誤消息）

    Returns:
        驗證後的值

    Raises:
        ValidationException: 驗證失敗時
    """
    # 類型檢查
    if value_type is not None and not isinstance(value, value_type):
        raise ValidationError(
            message=f"{field_name}類型錯誤",
            field=field_name,
            value=value,
            expected_type=value_type.__name__,
        )

    # 選項檢查
    if valid_options is not None and value not in valid_options:
        raise ValidationError(
            message=f"{field_name}不在有效選項中",
            field=field_name,
            value=value,
            expected_type=f"one of {valid_options}",
        )

    # 範圍檢查
    if min_value is not None and value < min_value:
        raise ValidationError(
            message=f"{field_name}小於最小值",
            field=field_name,
            value=value,
            expected_type=f">= {min_value}",
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            message=f"{field_name}大於最大值",
            field=field_name,
            value=value,
            expected_type=f"<= {max_value}",
        )

    return value


# 資料庫和遷移相關異常


class DatabaseError(LinkerError):
    """數據庫操作異常"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        query: Optional[str] = None,
        connection_info: Optional[dict] = None,
        original_error: Optional[Exception] = None,
        **kwargs,
    ):
        kwargs.setdefault("category", ErrorCategory.DATABASE)
        kwargs.setdefault("severity", ErrorSeverity.HIGH)
        kwargs.setdefault("error_code", "DATABASE_ERROR")

        details = kwargs.get("details", {})
        details.update(
            {
                "operation": operation,
                "table": table,
                "query": query[:200] if query else None,  # 限制查詢長度
                "connection_info": connection_info,
                "original_error": str(original_error) if original_error else None,
            }
        )
        kwargs["details"] = details

        super().__init__(message=message, **kwargs)
        self.operation = operation
        self.table = table
        self.original_error = original_error


class ConnectionPoolError(DatabaseError):
    """連接池異常"""

    def __init__(
        self,
        message: str,
        pool_status: Optional[dict] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            operation="connection_pool",
            original_error=original_error,
        )
        self.error_code = "CONNECTION_POOL_ERROR"
        self.details.update({"pool_status": pool_status})


class MigrationError(LinkerError):
    """數據遷移異常"""

    def __init__(
        self,
        message: str,
        migration_step: Optional[str] = None,
        data_source: Optional[str] = None,
        target_source: Optional[str] = None,
        records_processed: int = 0,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code="MIGRATION_ERROR",
            details={
                "migration_step": migration_step,
                "data_source": data_source,
                "target_source": target_source,
                "records_processed": records_processed,
                "original_error": str(original_error) if original_error else None,
            },
        )


class AsyncOperationError(LinkerError):
    """異步操作異常"""

    def __init__(
        self,
        message: str,
        operation: str,
        timeout: Optional[float] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code="ASYNC_OPERATION_ERROR",
            details={
                "operation": operation,
                "timeout": timeout,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.operation = operation
        self.timeout = timeout


class RecoverableError(LinkerError):
    """可恢復的異常（支持自動重試）"""

    def __init__(
        self,
        message: str,
        retry_count: int = 0,
        max_retries: int = 3,
        backoff_delay: float = 1.0,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code="RECOVERABLE_ERROR",
            details={
                "retry_count": retry_count,
                "max_retries": max_retries,
                "backoff_delay": backoff_delay,
                "original_error": str(original_error) if original_error else None,
            },
        )
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.backoff_delay = backoff_delay


# 重試和恢復機制


def with_retry(
    max_retries: int = 3,
    backoff_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    exponential_backoff: bool = True,
):
    """
    重試裝飾器（同步版本）

    Args:
        max_retries: 最大重試次數
        backoff_delay: 初始延遲時間
        exceptions: 需要重試的異常類型
        exponential_backoff: 是否使用指數退避
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        # 最後一次重試失敗，拋出RecoverableException
                        raise RecoverableError(
                            message=f"函數 {func.__name__} 重試 {max_retries} 次後仍然失敗",
                            retry_count=attempt,
                            max_retries=max_retries,
                            backoff_delay=backoff_delay,
                            original_error=e,
                        ) from e

                    # 計算延遲時間
                    delay = backoff_delay * (2**attempt if exponential_backoff else 1)
                    logger.warning(
                        f"函數 {func.__name__} 第 {attempt + 1} 次嘗試失敗，"
                        f"{delay}秒後重試: {str(e)}"
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
    異步重試裝飾器

    Args:
        max_retries: 最大重試次數
        backoff_delay: 初始延遲時間
        exceptions: 需要重試的異常類型
        exponential_backoff: 是否使用指數退避
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
                            message=f"函數 {func.__name__} 重試 {max_retries} 次後仍然失敗",
                            operation=func.__name__,
                            original_error=e,
                        ) from e

                    delay = backoff_delay * (2**attempt if exponential_backoff else 1)
                    logger.warning(
                        f"異步函數 {func.__name__} 第 {attempt + 1} 次嘗試失敗，"
                        f"{delay}秒後重試: {str(e)}"
                    )
                    await asyncio.sleep(delay)

            return None

        return wrapper

    return decorator


# 統一錯誤處理體系的新異常類


class UnifiedError(LinkerError):
    """統一錯誤類 - 所有新的錯誤處理都應使用此類或其子類"""

    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_suggestions: Optional[list[str]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            category=category,
            severity=severity,
            user_message=user_message,
            recovery_suggestions=recovery_suggestions,
        )


class SystemError(UnifiedError):
    """系統錯誤"""

    def __init__(self, message: str, error_code: str = "SYSTEM_ERROR", **kwargs):
        kwargs.setdefault("category", ErrorCategory.SYSTEM)
        kwargs.setdefault("severity", ErrorSeverity.CRITICAL)
        super().__init__(message, error_code, **kwargs)


class FileIOError(UnifiedError):
    """文件IO錯誤"""

    def __init__(self, message: str, error_code: str = "FILE_ERROR", **kwargs):
        kwargs.setdefault("category", ErrorCategory.FILE_IO)
        kwargs.setdefault("severity", ErrorSeverity.MEDIUM)
        super().__init__(message, error_code, **kwargs)


class NetworkError(UnifiedError):
    """網路錯誤"""

    def __init__(self, message: str, error_code: str = "NETWORK_ERROR", **kwargs):
        kwargs.setdefault("category", ErrorCategory.NETWORK)
        kwargs.setdefault("severity", ErrorSeverity.MEDIUM)
        super().__init__(message, error_code, **kwargs)


class BusinessLogicError(UnifiedError):
    """業務邏輯錯誤"""

    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR", **kwargs):
        kwargs.setdefault("category", ErrorCategory.BUSINESS)
        kwargs.setdefault("severity", ErrorSeverity.LOW)
        super().__init__(message, error_code, **kwargs)


class ConcurrencyError(UnifiedError):
    """並發錯誤"""

    def __init__(self, message: str, error_code: str = "CONCURRENCY_ERROR", **kwargs):
        kwargs.setdefault("category", ErrorCategory.CONCURRENCY)
        kwargs.setdefault("severity", ErrorSeverity.MEDIUM)
        super().__init__(message, error_code, **kwargs)
