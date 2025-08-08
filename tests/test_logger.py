"""
測試日誌系統模組
"""

import json
import logging
import tempfile
from pathlib import Path

import pytest

from core.logger import (
    ColoredFormatter,
    JsonFormatter,
    Logger,
    get_logger,
    log_function_call,
)


class TestLogger:
    """測試Logger類"""

    def test_logger_creation(self):
        """測試創建日誌器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(name="test_logger", log_dir=tmpdir, log_level="INFO")

            assert logger.name == "test_logger"
            assert logger.log_level == logging.INFO
            assert logger.log_dir == Path(tmpdir)

    def test_singleton_pattern(self):
        """測試單例模式"""
        logger1 = Logger.get_logger("singleton_test")
        logger2 = Logger.get_logger("singleton_test")

        assert logger1 is logger2

    def test_log_levels(self):
        """測試不同日誌級別"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(name="level_test", log_dir=tmpdir, log_level="DEBUG")

            # 測試各級別日誌（不應拋出異常）
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

    def test_log_with_extra_data(self):
        """測試帶額外數據的日誌"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(name="extra_test", log_dir=tmpdir, json_format=True)

            logger.info("Test message", user_id=123, action="test")

            # 檢查日誌文件
            log_files = list(Path(tmpdir).glob("*.log"))
            assert len(log_files) == 1

    def test_log_exception(self):
        """測試異常日誌"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(name="exception_test", log_dir=tmpdir)

            try:
                raise ValueError("Test exception")
            except ValueError as e:
                logger.log_exception(e, context={"test": "data"})

    def test_log_api_call(self):
        """測試API調用日誌"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(name="api_test", log_dir=tmpdir)

            # 成功調用
            logger.log_api_call(
                api_name="test_api",
                method="GET",
                params={"id": 1},
                response={"status": "success"},
                duration=0.5,
            )

            # 失敗調用
            logger.log_api_call(
                api_name="test_api",
                method="POST",
                params={"data": "test"},
                error=Exception("API Error"),
                duration=1.0,
            )

    def test_log_performance(self):
        """測試性能日誌"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(name="perf_test", log_dir=tmpdir)

            # 快速操作
            logger.log_performance("fast_op", 0.1)

            # 慢操作
            logger.log_performance("slow_op", 2.0, details={"items": 1000})

    def test_file_output(self):
        """測試文件輸出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(
                name="file_test", log_dir=tmpdir, file_output=True, console_output=False
            )

            logger.info("Test message")

            # 檢查日誌文件是否創建
            log_files = list(Path(tmpdir).glob("*.log"))
            assert len(log_files) == 1

            # 檢查文件內容
            with open(log_files[0]) as f:
                content = f.read()
                assert "Test message" in content


class TestFormatters:
    """測試格式化器"""

    def test_json_formatter(self):
        """測試JSON格式化器"""
        formatter = JsonFormatter()

        # 創建日誌記錄
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["line"] == 10

    def test_colored_formatter(self):
        """測試彩色格式化器"""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")

        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=10,
            msg="Warning message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)

        # 應該包含ANSI顏色碼
        assert "\033[" in formatted
        assert "WARNING" in formatted
        assert "Warning message" in formatted


class TestLogDecorator:
    """測試日誌裝飾器"""

    def test_function_call_logging(self):
        """測試函數調用日誌"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(name="decorator_test", log_dir=tmpdir)

            @log_function_call(logger)
            def test_function(x, y):
                return x + y

            result = test_function(2, 3)
            assert result == 5

    def test_function_exception_logging(self):
        """測試函數異常日誌"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = Logger(name="exception_decorator_test", log_dir=tmpdir)

            @log_function_call(logger)
            def failing_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError):
                failing_function()

    def test_decorator_without_logger(self):
        """測試不指定logger的裝飾器"""

        @log_function_call()
        def simple_function(x):
            return x * 2

        result = simple_function(5)
        assert result == 10


class TestGetLogger:
    """測試get_logger便捷函數"""

    def test_get_logger_default(self):
        """測試默認logger獲取"""
        logger = get_logger()
        assert logger.name == "linker"
        assert isinstance(logger, Logger)

    def test_get_logger_custom_name(self):
        """測試自定義名稱"""
        logger = get_logger("custom")
        assert logger.name == "custom"

    def test_get_logger_singleton(self):
        """測試get_logger的單例行為"""
        logger1 = get_logger("test_singleton")
        logger2 = get_logger("test_singleton")
        assert logger1 is logger2
