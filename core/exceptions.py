"""
異常處理模組
提供統一的異常類型和錯誤處理機制
"""

from typing import Any, Optional


class LinkerError(Exception):
    """
    Linker 應用基礎異常類
    所有自定義異常都應該繼承此類
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"[{self.error_code}] {self.message} - Details: {self.details}"
        return f"[{self.error_code}] {self.message}"


class APIException(LinkerError):
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


class GeminiAPIException(APIException):
    """Gemini API 特定異常"""

    def __init__(self, message: str, model: Optional[str] = None, prompt: Optional[str] = None):
        super().__init__(message=message, api_name="Gemini")
        # 添加額外的詳細信息
        self.details.update({"model": model, "prompt_preview": prompt[:100] if prompt else None})


class DataException(LinkerError):
    """數據處理相關異常"""

    def __init__(
        self, message: str, data_type: Optional[str] = None, file_path: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="DATA_ERROR",
            details={"data_type": data_type, "file_path": file_path},
        )


class ValidationException(LinkerError):
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


class ConfigException(LinkerError):
    """配置相關異常"""

    def __init__(
        self, message: str, config_key: Optional[str] = None, config_file: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details={"config_key": config_key, "config_file": config_file},
        )


class FileOperationException(LinkerError):
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


class ParseException(LinkerError):
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


class UserInputException(LinkerError):
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


# 錯誤處理工具函數


def handle_api_error(func):
    """
    API錯誤處理裝飾器
    自動捕獲並轉換API相關異常
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException:
            raise  # 直接重新拋出已經是APIException的異常
        except Exception as e:
            # 將其他異常轉換為APIException
            raise APIException(message=f"API調用失敗: {str(e)}", api_name=func.__name__) from e

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
            except FileOperationException:
                raise  # 直接重新拋出
            except OSError as e:
                # 嘗試從參數中提取文件路徑
                file_path = kwargs.get("file_path", "")
                if not file_path and args:
                    # 假設第一個參數可能是self，第二個是file_path
                    file_path = args[1] if len(args) > 1 else str(args[0])

                raise FileOperationException(
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
        raise ParseException(
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
        raise ValidationException(
            message=f"{field_name}類型錯誤",
            field=field_name,
            value=value,
            expected_type=value_type.__name__,
        )

    # 選項檢查
    if valid_options is not None and value not in valid_options:
        raise ValidationException(
            message=f"{field_name}不在有效選項中",
            field=field_name,
            value=value,
            expected_type=f"one of {valid_options}",
        )

    # 範圍檢查
    if min_value is not None and value < min_value:
        raise ValidationException(
            message=f"{field_name}小於最小值",
            field=field_name,
            value=value,
            expected_type=f">= {min_value}",
        )

    if max_value is not None and value > max_value:
        raise ValidationException(
            message=f"{field_name}大於最大值",
            field=field_name,
            value=value,
            expected_type=f"<= {max_value}",
        )

    return value
