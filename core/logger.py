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
            return {k: self._sanitize(self._mask_value(k, v) if isinstance(v, str) else v) for k, v in data.items()}
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
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # 添加額外字段
        if hasattr(record, "extra_data"):
            log_obj["extra"] = self._sanitize(record.extra_data)

        return json.dumps(log_obj, ensure_ascii=False)


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
                log_file, when="midnight", backupCount=int(os.getenv("LOG_BACKUP_COUNT", "7")), encoding="utf-8"
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
