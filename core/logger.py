"""
日誌系統模組
提供統一的日誌記錄和管理功能
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """彩色日誌格式化器（用於終端輸出）"""

    # ANSI顏色碼
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 綠色
        "WARNING": "\033[33m",  # 黃色
        "ERROR": "\033[31m",  # 紅色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record):
        # 添加顏色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON格式化器（用於文件輸出）"""

    SENSITIVE_KEYS = {"authorization", "api_key", "password", "token"}

    def _mask_value(self, key: str, value: str) -> str:
        if key.lower() in self.SENSITIVE_KEYS:
            return "***"
        # 基礎遮罩：像 API key 這類長字串
        if isinstance(value, str) and len(value) > 32:
            return value[:6] + "***" + value[-4:]
        return value

    def _sanitize(self, data):
        if isinstance(data, dict):
            return {
                k: self._sanitize(self._mask_value(k, v) if isinstance(v, str) else v)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self._sanitize(v) for v in data]
        return data

    def format(self, record):
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加異常信息
        """
日誌系統核心模組

提供一個功能豐富且可配置的日誌系統，支援多種輸出格式和處理方式。
此模組旨在為應用程式提供統一、結構化且易於管理的日誌記錄功能。

主要功能：
- **多格式輸出**：支援純文字（帶顏色）和 JSON 格式的日誌輸出。
- **多目標輸出**：可同時將日誌輸出到控制台和檔案。
- **日誌輪轉**：支援基於檔案大小或時間的日誌輪轉，防止日誌檔案無限增長。
- **敏感資訊過濾**：自動遮蔽日誌中的敏感關鍵字（如 `api_key`, `password`）。
- **結構化日誌**：JSON 格式的日誌包含豐富的上下文資訊（如時間戳、模組、行號）。
- **單例模式**：確保每個模組獲取到的 logger 實例是唯一的，避免重複配置。
- **便捷的記錄方法**：提供 `log_exception`, `log_api_call` 等高階方法，簡化特定場景的日誌記錄。
"""

import logging
import logging.handlers


class ColoredFormatter(logging.Formatter):
    """為終端輸出提供帶有 ANSI 顏色的日誌格式化器。"""
    COLORS = {
        "DEBUG": "\033[36m",    # 青色
        "INFO": "\033[32m",     # 綠色
        "WARNING": "\033[33m",  # 黃色
        "ERROR": "\033[31m",    # 紅色
        "CRITICAL": "\033[35m", # 紫色
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname)
        if log_color:
            record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """
    將日誌記錄轉換為 JSON 格式，適用於結構化日誌系統（如 ELK, Splunk）。
    同時包含敏感資訊過濾功能。
    """
    SENSITIVE_KEYS = {"authorization", "api_key", "password", "token"}

    def _mask_value(self, key: str, value: Any) -> Any:
        """如果鍵是敏感的，則遮蔽其值。"""
        if isinstance(key, str) and key.lower() in self.SENSITIVE_KEYS:
            return "***MASKED***"
        if isinstance(value, str) and len(value) > 40:  # 對疑似金鑰的長字串進行部分遮蔽
            return f"{value[:8]}...{value[-4:]}"
        return value

    def _sanitize(self, data: Any) -> Any:
        """遞歸地清理字典或列表中的敏感資訊。"""
        if isinstance(data, dict):
            return {k: self._sanitize(self._mask_value(k, v)) for k, v in data.items()}
        if isinstance(data, list):
            return [self._sanitize(item) for item in data]
        return data

    def format(self, record):
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            log_obj["extra"] = self._sanitize(record.extra_data)
        return json.dumps(log_obj, ensure_ascii=False)


class Logger:
    """統一的日誌管理器類別。"""
    _instances = {}

    def __init__(self, name: str, log_dir: str, log_level: str, console_output: bool, file_output: bool, json_format: bool):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level.upper())
        self.logger.handlers.clear()  # 防止重複添加 handler

        if console_output:
            self._setup_console_handler(log_level)
        if file_output:
            self._setup_file_handler(log_dir, log_level, json_format)

    def _setup_console_handler(self, log_level: str):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level.upper())
        formatter = ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _setup_file_handler(self, log_dir: str, log_level: str, json_format: bool):
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        log_file = log_path / f"{self.name}.log"

        if os.getenv("LOG_ROTATE_DAILY", "false").lower() == "true":
            file_handler = logging.handlers.TimedRotatingFileHandler(log_file, when="midnight", backupCount=7, encoding="utf-8")
        else:
            file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        
        file_handler.setLevel(log_level.upper())
        formatter = JsonFormatter() if json_format else logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, name: str, **kwargs) -> "Logger":
        """獲取或創建一個 logger 實例（單例模式）。"""
        if name not in cls._instances:
            cls._instances[name] = cls(name, **kwargs)
        return cls._instances[name]

    def _log(self, level: int, message: str, **kwargs):
        """內部日誌記錄方法，處理額外資料。"""
        self.logger.log(level, message, extra={"extra_data": kwargs} if kwargs else None)

    def debug(self, message: str, **kwargs): self._log(logging.DEBUG, message, **kwargs)
    def info(self, message: str, **kwargs): self._log(logging.INFO, message, **kwargs)
    def warning(self, message: str, **kwargs): self._log(logging.WARNING, message, **kwargs)
    def error(self, message: str, exc_info=False, **kwargs): self.logger.error(message, exc_info=exc_info, extra={"extra_data": kwargs} if kwargs else None)
    def critical(self, message: str, exc_info=True, **kwargs): self.logger.critical(message, exc_info=exc_info, extra={"extra_data": kwargs} if kwargs else None)

    def log_exception(self, exception: Exception, context: Optional[dict] = None):
        """以結構化格式記錄一個異常的詳細資訊。"""
        error_data = {"exception_type": type(exception).__name__, "exception_message": str(exception), "context": context or {}}
        if hasattr(exception, "to_dict") and callable(exception.to_dict):
            error_data.update(exception.to_dict())
        self.error(f"發生異常: {type(exception).__name__}", exc_info=True, **error_data)

    def log_api_call(self, api_name: str, method: str, params: dict, response: Optional[dict] = None, error: Optional[Exception] = None, duration: Optional[float] = None):
        """記錄一次 API 調用的詳細資訊。"""
        log_data = {"api_name": api_name, "method": method, "params": params, "duration_ms": duration * 1000 if duration else None}
        if error:
            log_data["error"] = str(error)
            self.error(f"API 調用失敗: {api_name}.{method}", **log_data)
        else:
            log_data["response_preview"] = str(response)[:200] if response else None
            self.info(f"API 調用成功: {api_name}.{method}", **log_data)

    def log_user_action(self, action: str, user_input: Optional[str] = None, result: Optional[str] = None):
        """記錄一次使用者操作。"""
        self.info(f"使用者操作: {action}", action=action, user_input=user_input, result=result)

    def log_performance(self, operation: str, duration: float, details: Optional[dict] = None):
        """記錄一個操作的性能數據。"""
        log_data = {"operation": operation, "duration_ms": duration * 1000, **(details or {})}
        if duration > 1.0:
            self.warning(f"慢操作警告: {operation} 耗時 {duration:.2f} 秒", **log_data)
        else:
            self.debug(f"性能日誌: {operation} 耗時 {duration:.3f} 秒", **log_data)


def get_logger(name: str = "linker") -> Logger:
    """
    獲取 logger 的便捷工廠函數。
    從環境變數讀取配置並返回一個 `Logger` 實例。
    """
    return Logger.get_logger(
        name=name,
        log_dir=os.getenv("LOG_DIR", "logs"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        console_output=os.getenv("LOG_TO_CONSOLE", "true").lower() == "true",
        file_output=os.getenv("LOG_TO_FILE", "true").lower() == "true",
        json_format=(os.getenv("LOG_FORMAT", "text").lower() == "json"),
    )


def log_function_call(logger: Optional[Logger] = None):
    """
    一個裝飾器，用於自動記錄函數的調用、返回和異常。
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log = logger or get_logger(func.__module__)
            start_time = time.time()
            try:
                log.debug(f"調用函數: {func.__name__}", args=str(args)[:100], kwargs=str(kwargs)[:100])
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log.debug(f"函數 {func.__name__} 返回", duration=f"{duration:.4f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                log.log_exception(e, context={"function": func.__name__, "duration": f"{duration:.4f}s"})
                raise
        return wrapper
    return decorator


__all__ = ["Logger", "get_logger", "log_function_call", "ColoredFormatter", "JsonFormatter"]


class Logger:
    """統一的日誌管理器"""

    _instances = {}  # 存儲logger實例

    def __init__(
        self,
        name: str,
        log_dir: str = "logs",
        log_level: str = "INFO",
        console_output: bool = True,
        file_output: bool = True,
        json_format: bool = False,
    ):
        """
        初始化日誌器

        Args:
            name: 日誌器名稱
            log_dir: 日誌目錄
            log_level: 日誌級別
            console_output: 是否輸出到控制台
            file_output: 是否輸出到文件
            json_format: 文件是否使用JSON格式
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)

        # 清除現有的處理器（避免重複）
        self.logger.handlers.clear()

        # 設置處理器
        if console_output:
            self._setup_console_handler()

        if file_output:
            self._setup_file_handler(json_format)

    def _setup_console_handler(self):
        """設置控制台處理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)

        # 使用彩色格式化器
        formatter = ColoredFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def _setup_file_handler(self, json_format: bool = False):
        """設置文件處理器"""
        import os

        # 創建日誌目錄
        self.log_dir.mkdir(exist_ok=True)

        # 檔名不帶日期，由輪轉器管理
        log_file = self.log_dir / f"{self.name}.log"

        # 輪轉策略：預設大小輪轉，可用 LOG_ROTATE_DAILY=true 切換為按日輪轉
        rotate_daily = os.getenv("LOG_ROTATE_DAILY", "false").lower() == "true"
        if rotate_daily:
            file_handler = logging.handlers.TimedRotatingFileHandler(
                log_file,
                when="midnight",
                backupCount=int(os.getenv("LOG_BACKUP_COUNT", "7")),
                encoding="utf-8",
            )
        else:
            max_bytes = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))  # 10MB
            backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
        file_handler.setLevel(self.log_level)

        # 選擇格式化器
        if json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls, name: str, **kwargs) -> "Logger":
        """
        獲取或創建日誌器實例（單例模式）

        Args:
            name: 日誌器名稱
            **kwargs: 其他參數

        Returns:
            Logger實例
        """
        if name not in cls._instances:
            cls._instances[name] = cls(name, **kwargs)
        return cls._instances[name]

    def debug(self, message: str, **kwargs):
        """記錄調試信息"""
        extra = {"extra_data": kwargs} if kwargs else None
        self.logger.debug(message, extra=extra)

    def info(self, message: str, **kwargs):
        """記錄一般信息"""
        extra = {"extra_data": kwargs} if kwargs else None
        self.logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs):
        """記錄警告信息"""
        extra = {"extra_data": kwargs} if kwargs else None
        self.logger.warning(message, extra=extra)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """
        記錄錯誤信息

        Args:
            message: 錯誤消息
            exc_info: 是否包含異常堆棧信息
            **kwargs: 額外數據
        """
        extra = {"extra_data": kwargs} if kwargs else None
        self.logger.error(message, exc_info=exc_info, extra=extra)

    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """記錄嚴重錯誤"""
        extra = {"extra_data": kwargs} if kwargs else None
        self.logger.critical(message, exc_info=exc_info, extra=extra)

    def log_exception(self, exception: Exception, context: Optional[dict] = None):
        """
        記錄異常詳情

        Args:
            exception: 異常對象
            context: 上下文信息
        """
        error_data = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "context": context or {},
        }

        # 如果是自定義異常，提取更多信息
        if hasattr(exception, "error_code"):
            error_data["error_code"] = exception.error_code
        if hasattr(exception, "details"):
            error_data["details"] = exception.details

        self.error(
            f"異常發生: {type(exception).__name__}: {str(exception)}", exc_info=True, **error_data
        )

    def log_api_call(
        self,
        api_name: str,
        method: str,
        params: dict,
        response: Optional[dict] = None,
        error: Optional[Exception] = None,
        duration: Optional[float] = None,
    ):
        """
        記錄API調用

        Args:
            api_name: API名稱
            method: 調用方法
            params: 參數
            response: 響應
            error: 錯誤（如果有）
            duration: 耗時（秒）
        """
        log_data = {"api_name": api_name, "method": method, "params": params, "duration": duration}

        if error:
            log_data["error"] = str(error)
            self.error(f"API調用失敗: {api_name}.{method}", **log_data)
        else:
            log_data["response_preview"] = str(response)[:200] if response else None
            self.info(f"API調用成功: {api_name}.{method}", **log_data)

    def log_user_action(
        self, action: str, user_input: Optional[str] = None, result: Optional[str] = None
    ):
        """
        記錄用戶操作

        Args:
            action: 操作類型
            user_input: 用戶輸入
            result: 操作結果
        """
        self.info(f"用戶操作: {action}", action=action, user_input=user_input, result=result)

    def log_performance(self, operation: str, duration: float, details: Optional[dict] = None):
        """
        記錄性能數據

        Args:
            operation: 操作名稱
            duration: 耗時（秒）
            details: 詳細信息
        """
        log_data = {
            "operation": operation,
            "duration_seconds": duration,
            "duration_ms": duration * 1000,
        }

        if details:
            log_data.update(details)

        if duration > 1.0:  # 超過1秒視為慢操作
            self.warning(f"慢操作: {operation} 耗時 {duration:.2f}秒", **log_data)
        else:
            self.debug(f"操作完成: {operation} 耗時 {duration:.3f}秒", **log_data)


# 創建默認日誌器
def get_logger(name: str = "linker") -> Logger:
    """
    獲取日誌器的便捷函數

    Args:
        name: 日誌器名稱

    Returns:
        Logger實例
    """
    # 從環境變量讀取配置
    import os

    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_dir = os.getenv("LOG_DIR", "logs")
    log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    log_format = os.getenv("LOG_FORMAT", "json").lower()

    return Logger.get_logger(
        name=name,
        log_dir=log_dir,
        log_level=log_level,
        console_output=log_to_console,
        file_output=log_to_file,
        json_format=(log_format == "json"),
    )


# 日誌裝飾器
def log_function_call(logger: Optional[Logger] = None):
    """
    函數調用日誌裝飾器

    Args:
        logger: 日誌器實例，如果為None則使用默認日誌器
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)

            # 記錄函數調用
            logger.debug(
                f"調用函數: {func.__name__}",
                function=func.__name__,
                args=str(args)[:100],
                kwargs=str(kwargs)[:100],
            )

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 記錄成功
                logger.debug(
                    f"函數返回: {func.__name__}", function=func.__name__, duration=duration
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                # 記錄異常
                logger.log_exception(
                    e,
                    context={
                        "function": func.__name__,
                        "duration": duration,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100],
                    },
                )
                raise

        return wrapper

    return decorator


# 導出常用功能
__all__ = ["Logger", "get_logger", "log_function_call", "ColoredFormatter", "JsonFormatter"]
