"""
測試增強異常處理模組
針對 core/exceptions_enhanced.py 進行全面測試覆蓋
"""

import asyncio
import time
from unittest.mock import patch

import pytest

from core.exceptions import (
    AsyncOperationError,
    ConnectionPoolError,
    DatabaseError,
    ErrorSeverity,
    ExceptionMonitor,
    LinkerError,
    MigrationError,
    RecoverableError,
    database_operation,
    exception_monitor,
    monitor_exceptions,
    resilient_api_call,
    with_async_retry,
    with_database_error_handling,
    with_fallback,
    with_retry,
    with_timeout,
)


class TestExceptionEnhancedHierarchy:
    """測試增強異常類層級"""

    def test_error_severity_enum(self):
        """測試錯誤嚴重性枚舉"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_database_error(self):
        """測試數據庫異常"""
        original_error = Exception("Connection failed")
        exc = DatabaseError(
            message="Database operation failed",
            operation="select",
            table="users",
            query="SELECT * FROM users WHERE id = ?",
            connection_info={"host": "localhost", "port": 5432},
            original_error=original_error,
        )

        assert exc.message == "Database operation failed"
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.operation == "select"
        assert exc.table == "users"
        assert exc.original_error == original_error
        assert exc.details["operation"] == "select"
        assert exc.details["table"] == "users"
        assert "SELECT * FROM users WHERE id = ?" in exc.details["query"]
        assert exc.details["connection_info"]["host"] == "localhost"

    def test_database_error_query_truncation(self):
        """測試數據庫異常查詢截斷功能"""
        long_query = "SELECT * FROM users WHERE " + "a" * 300
        exc = DatabaseError(
            message="Long query failed",
            query=long_query,
        )
        # 查詢應被截斷到200字符
        assert len(exc.details["query"]) == 200
        assert exc.details["query"].endswith("a" * 100)

    def test_connection_pool_error(self):
        """測試連接池異常"""
        pool_status = {"active": 5, "idle": 3, "total": 8}
        original_error = Exception("Pool exhausted")

        exc = ConnectionPoolError(
            message="Connection pool error",
            pool_status=pool_status,
            original_error=original_error,
        )

        assert exc.message == "Connection pool error"
        assert exc.error_code == "CONNECTION_POOL_ERROR"
        assert exc.details["operation"] == "connection_pool"
        assert exc.details["pool_status"] == pool_status
        assert exc.original_error == original_error

    def test_migration_error(self):
        """測試數據遷移異常"""
        original_error = Exception("Migration step failed")
        exc = MigrationError(
            message="Migration failed",
            migration_step="create_tables",
            data_source="json",
            target_source="postgresql",
            records_processed=1500,
            original_error=original_error,
        )

        assert exc.message == "Migration failed"
        assert exc.error_code == "MIGRATION_ERROR"
        assert exc.details["migration_step"] == "create_tables"
        assert exc.details["data_source"] == "json"
        assert exc.details["target_source"] == "postgresql"
        assert exc.details["records_processed"] == 1500
        assert "Migration step failed" in exc.details["original_error"]

    def test_async_operation_error(self):
        """測試異步操作異常"""
        original_error = asyncio.TimeoutError("Operation timed out")
        exc = AsyncOperationError(
            message="Async operation failed",
            operation="fetch_data",
            timeout=30.0,
            original_error=original_error,
        )

        assert exc.message == "Async operation failed"
        assert exc.error_code == "ASYNC_OPERATION_ERROR"
        assert exc.details["operation"] == "fetch_data"
        assert exc.details["timeout"] == 30.0
        assert "Operation timed out" in exc.details["original_error"]

    def test_recoverable_error(self):
        """測試可恢復異常"""
        original_error = Exception("Temporary failure")
        exc = RecoverableError(
            message="Recoverable error occurred",
            retry_count=2,
            max_retries=5,
            backoff_delay=2.0,
            original_error=original_error,
        )

        assert exc.message == "Recoverable error occurred"
        assert exc.error_code == "RECOVERABLE_ERROR"
        assert exc.retry_count == 2
        assert exc.max_retries == 5
        assert exc.backoff_delay == 2.0
        assert exc.details["retry_count"] == 2
        assert exc.details["max_retries"] == 5
        assert exc.details["backoff_delay"] == 2.0
        assert "Temporary failure" in exc.details["original_error"]


class TestRetryDecorators:
    """測試重試裝飾器"""

    def test_with_retry_success(self):
        """測試重試裝飾器成功情況"""
        call_count = 0

        @with_retry(max_retries=3, backoff_delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_with_retry_max_retries_exceeded(self):
        """測試重試裝飾器達到最大重試次數"""
        call_count = 0

        @with_retry(max_retries=2, backoff_delay=0.01)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Error #{call_count}")

        with pytest.raises(RecoverableError) as exc_info:
            always_failing_function()

        assert call_count == 3  # 初始調用 + 2次重試
        assert exc_info.value.retry_count == 2
        assert exc_info.value.max_retries == 2
        assert "always_failing_function 重試 2 次後仍然失敗" in exc_info.value.message

    def test_with_retry_specific_exceptions(self):
        """測試重試裝飾器特定異常類型"""

        @with_retry(max_retries=2, exceptions=(ValueError,))
        def function_with_different_errors():
            raise TypeError("This should not be retried")

        # TypeError 不在重試範圍內，應該直接拋出
        with pytest.raises(TypeError):
            function_with_different_errors()

    def test_with_retry_exponential_backoff(self):
        """測試重試裝飾器指數退避"""
        call_times = []

        @with_retry(max_retries=2, backoff_delay=0.1, exponential_backoff=True)
        def timed_function():
            call_times.append(time.time())
            raise ValueError("Retry me")

        with pytest.raises(RecoverableError):
            timed_function()

        # 檢查時間間隔是否符合指數退避 (0.1, 0.2)
        assert len(call_times) == 3
        if len(call_times) >= 2:
            first_delay = call_times[1] - call_times[0]
            assert 0.08 <= first_delay <= 0.15  # 允許一些時間誤差
        if len(call_times) >= 3:
            second_delay = call_times[2] - call_times[1]
            assert 0.18 <= second_delay <= 0.25

    @pytest.mark.asyncio
    async def test_with_async_retry_success(self):
        """測試異步重試裝飾器成功情況"""
        call_count = 0

        @with_async_retry(max_retries=3, backoff_delay=0.01)
        async def async_flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary async error")
            return "async success"

        result = await async_flaky_function()
        assert result == "async success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_with_async_retry_max_retries_exceeded(self):
        """測試異步重試裝飾器達到最大重試次數"""
        call_count = 0

        @with_async_retry(max_retries=2, backoff_delay=0.01)
        async def always_failing_async_function():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Async error #{call_count}")

        with pytest.raises(AsyncOperationError) as exc_info:
            await always_failing_async_function()

        assert call_count == 3  # 初始調用 + 2次重試
        assert "always_failing_async_function 重試 2 次後仍然失敗" in exc_info.value.message
        assert exc_info.value.operation == "always_failing_async_function"


class TestDatabaseErrorHandling:
    """測試數據庫錯誤處理裝飾器"""

    @pytest.mark.asyncio
    async def test_with_database_error_handling_async_success(self):
        """測試異步數據庫錯誤處理成功情況"""

        @with_database_error_handling("select", "users")
        async def successful_db_operation():
            return "query result"

        result = await successful_db_operation()
        assert result == "query result"

    @pytest.mark.asyncio
    async def test_with_database_error_handling_async_connection_error(self):
        """測試異步數據庫連接錯誤"""

        @with_database_error_handling("select", "users")
        async def failing_connection():
            raise Exception("connection timeout")

        with pytest.raises(ConnectionPoolError) as exc_info:
            await failing_connection()

        assert "數據庫連接失敗" in exc_info.value.message
        assert "connection timeout" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_with_database_error_handling_async_database_error(self):
        """測試異步數據庫操作錯誤"""

        @with_database_error_handling("insert", "products")
        async def failing_db_operation():
            raise Exception("syntax error")

        with pytest.raises(DatabaseError) as exc_info:
            await failing_db_operation()

        assert exc_info.value.operation == "insert"
        assert exc_info.value.table == "products"
        assert "數據庫insert操作失敗" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_with_database_error_handling_async_preserves_database_error(self):
        """測試異步數據庫錯誤處理保留原有DatabaseError"""
        original_error = DatabaseError("Original error", operation="update")

        @with_database_error_handling("select", "users")
        async def function_with_database_error():
            raise original_error

        with pytest.raises(DatabaseError) as exc_info:
            await function_with_database_error()

        # 應該直接重新拋出原始的DatabaseError
        assert exc_info.value is original_error

    def test_with_database_error_handling_sync_success(self):
        """測試同步數據庫錯誤處理成功情況"""

        @with_database_error_handling("select", "users")
        def successful_sync_db_operation():
            return "sync query result"

        result = successful_sync_db_operation()
        assert result == "sync query result"

    def test_with_database_error_handling_sync_database_error(self):
        """測試同步數據庫操作錯誤"""

        @with_database_error_handling("delete", "orders")
        def failing_sync_db_operation():
            raise Exception("constraint violation")

        with pytest.raises(DatabaseError) as exc_info:
            failing_sync_db_operation()

        assert exc_info.value.operation == "delete"
        assert exc_info.value.table == "orders"
        assert "數據庫delete操作失敗" in exc_info.value.message


class TestTimeoutHandling:
    """測試超時處理裝飾器"""

    @pytest.mark.asyncio
    async def test_with_timeout_success(self):
        """測試超時裝飾器成功情況"""

        @with_timeout(1.0)
        async def quick_operation():
            await asyncio.sleep(0.1)
            return "completed"

        result = await quick_operation()
        assert result == "completed"

    @pytest.mark.asyncio
    async def test_with_timeout_exceeded(self):
        """測試超時情況"""

        @with_timeout(0.1)
        async def slow_operation():
            await asyncio.sleep(0.5)
            return "should not complete"

        with pytest.raises(AsyncOperationError) as exc_info:
            await slow_operation()

        assert "slow_operation 執行超時" in exc_info.value.message
        assert exc_info.value.operation == "slow_operation"
        assert exc_info.value.timeout == 0.1


class TestFallbackHandling:
    """測試降級處理裝飾器"""

    @pytest.mark.asyncio
    async def test_with_fallback_async_success(self):
        """測試異步降級處理成功情況"""

        async def fallback_func(*args, **kwargs):
            return "fallback result"

        @with_fallback(fallback_func)
        async def successful_operation():
            return "primary result"

        result = await successful_operation()
        assert result == "primary result"

    @pytest.mark.asyncio
    async def test_with_fallback_async_fallback_triggered(self):
        """測試異步降級處理觸發"""

        async def async_fallback(*args, **kwargs):
            return "async fallback result"

        @with_fallback(async_fallback, exceptions=(ValueError,))
        async def failing_operation():
            raise ValueError("Primary operation failed")

        result = await failing_operation()
        assert result == "async fallback result"

    @pytest.mark.asyncio
    async def test_with_fallback_async_sync_fallback(self):
        """測試異步主函數使用同步降級函數"""

        def sync_fallback(*args, **kwargs):
            return "sync fallback result"

        @with_fallback(sync_fallback)
        async def failing_async_operation():
            raise RuntimeError("Async operation failed")

        result = await failing_async_operation()
        assert result == "sync fallback result"

    @pytest.mark.asyncio
    async def test_with_fallback_async_fallback_also_fails(self):
        """測試異步降級函數也失敗的情況"""

        async def failing_fallback(*args, **kwargs):
            raise RuntimeError("Fallback also failed")

        @with_fallback(failing_fallback)
        async def failing_operation():
            raise ValueError("Primary failed")

        with pytest.raises(LinkerError) as exc_info:
            await failing_operation()

        assert "主要功能和降級功能都失敗" in exc_info.value.message
        assert exc_info.value.error_code == "FALLBACK_FAILED"
        assert "Primary failed" in exc_info.value.details["original_error"]
        assert "Fallback also failed" in exc_info.value.details["fallback_error"]

    def test_with_fallback_sync_success(self):
        """測試同步降級處理成功情況"""

        def fallback_func(*args, **kwargs):
            return "sync fallback result"

        @with_fallback(fallback_func)
        def successful_sync_operation():
            return "sync primary result"

        result = successful_sync_operation()
        assert result == "sync primary result"

    def test_with_fallback_sync_fallback_triggered(self):
        """測試同步降級處理觸發"""

        def sync_fallback(*args, **kwargs):
            return "sync fallback result"

        @with_fallback(sync_fallback, exceptions=(ValueError,))
        def failing_sync_operation():
            raise ValueError("Sync primary operation failed")

        result = failing_sync_operation()
        assert result == "sync fallback result"

    def test_with_fallback_sync_fallback_also_fails(self):
        """測試同步降級函數也失敗的情況"""

        def failing_sync_fallback(*args, **kwargs):
            raise RuntimeError("Sync fallback also failed")

        @with_fallback(failing_sync_fallback)
        def failing_sync_operation():
            raise ValueError("Sync primary failed")

        with pytest.raises(LinkerError) as exc_info:
            failing_sync_operation()

        assert "主要功能和降級功能都失敗" in exc_info.value.message
        assert exc_info.value.error_code == "FALLBACK_FAILED"
        assert "Sync primary failed" in exc_info.value.details["original_error"]
        assert "Sync fallback also failed" in exc_info.value.details["fallback_error"]


class TestExceptionMonitor:
    """測試異常監控器"""

    def setup_method(self):
        """每個測試前重設監控器狀態"""
        self.monitor = ExceptionMonitor()

    def test_exception_monitor_initialization(self):
        """測試異常監控器初始化"""
        assert self.monitor.error_counts == {}
        assert self.monitor.error_rates == {}
        assert self.monitor.last_alert_time == {}
        assert self.monitor.alert_threshold == 10
        assert self.monitor.alert_cooldown == 300

    def test_record_exception_basic(self):
        """測試基本異常記錄"""
        exc = ValueError("Test error")
        context = {"user_id": 123, "action": "login"}

        self.monitor.record_exception(exc, ErrorSeverity.MEDIUM, context)

        assert "ValueError" in self.monitor.error_counts
        records = self.monitor.error_counts["ValueError"]
        assert len(records) == 1
        assert records[0]["severity"] == ErrorSeverity.MEDIUM
        assert records[0]["message"] == "Test error"
        assert records[0]["context"] == context

    def test_record_exception_multiple_types(self):
        """測試記錄多種異常類型"""
        self.monitor.record_exception(ValueError("Value error"), ErrorSeverity.LOW)
        self.monitor.record_exception(TypeError("Type error"), ErrorSeverity.HIGH)
        self.monitor.record_exception(ValueError("Another value error"), ErrorSeverity.MEDIUM)

        assert len(self.monitor.error_counts) == 2
        assert len(self.monitor.error_counts["ValueError"]) == 2
        assert len(self.monitor.error_counts["TypeError"]) == 1

    def test_record_exception_cleanup_old_records(self):
        """測試清理過期記錄"""
        # Mock time.time 來模擬時間流逝
        with patch("core.exceptions.time.time") as mock_time:
            # 設置初始時間
            mock_time.return_value = 1000.0

            # 記錄第一個異常
            self.monitor.record_exception(ValueError("Old error"), ErrorSeverity.LOW)

            # 設置2小時後的時間
            mock_time.return_value = 1000.0 + 7200  # 2小時後

            # 記錄新異常，應該觸發清理
            self.monitor.record_exception(ValueError("New error"), ErrorSeverity.LOW)

            # 檢查舊記錄是否被清理
            records = self.monitor.error_counts["ValueError"]
            assert len(records) == 1
            assert records[0]["message"] == "New error"

    def test_get_error_statistics(self):
        """測試獲取錯誤統計"""
        # 記錄不同嚴重性的異常
        self.monitor.record_exception(ValueError("Error 1"), ErrorSeverity.LOW)
        self.monitor.record_exception(ValueError("Error 2"), ErrorSeverity.MEDIUM)
        self.monitor.record_exception(TypeError("Error 3"), ErrorSeverity.HIGH)

        stats = self.monitor.get_error_statistics()

        assert "ValueError" in stats
        assert "TypeError" in stats
        assert stats["ValueError"]["total_count"] == 2
        assert stats["ValueError"]["recent_hour_count"] == 2
        assert stats["TypeError"]["total_count"] == 1

        # 檢查嚴重性分佈
        value_error_severity = stats["ValueError"]["severity_distribution"]
        assert value_error_severity["low"] == 1
        assert value_error_severity["medium"] == 1

    def test_alert_threshold_checking(self):
        """測試告警閾值檢查"""
        with patch.object(self.monitor, "_trigger_alert") as mock_trigger:
            # 記錄足夠多的CRITICAL錯誤來觸發告警
            for i in range(3):  # CRITICAL閾值是3，第3次時觸發
                self.monitor.record_exception(
                    RuntimeError(f"Critical error {i}"), ErrorSeverity.CRITICAL
                )

            # 應該觸發告警
            mock_trigger.assert_called_once()
            call_args = mock_trigger.call_args[0]
            assert call_args[0] == "RuntimeError"
            assert call_args[1] == 3  # 錯誤計數
            assert call_args[2] == ErrorSeverity.CRITICAL

    def test_alert_cooldown(self):
        """測試告警冷卻期"""
        with (
            patch.object(self.monitor, "_trigger_alert") as mock_trigger,
            patch("core.exceptions.time.time") as mock_time,
        ):
            mock_time.return_value = 1000.0

            # 記錄足夠多的錯誤觸發告警
            for i in range(3):
                self.monitor.record_exception(RuntimeError(f"Error {i}"), ErrorSeverity.CRITICAL)

            # 第一次應該觸發告警
            assert mock_trigger.call_count == 1

            # 在冷卻期內再次記錄錯誤
            mock_time.return_value = 1100.0  # 100秒後（小於300秒冷卻期）
            self.monitor.record_exception(RuntimeError("Another error"), ErrorSeverity.CRITICAL)

            # 不應該再次觸發告警
            assert mock_trigger.call_count == 1

            # 超過冷卻期後記錄錯誤
            mock_time.return_value = 1400.0  # 400秒後（超過300秒冷卻期）
            for i in range(3):
                self.monitor.record_exception(
                    RuntimeError(f"Error after cooldown {i}"), ErrorSeverity.CRITICAL
                )

            # 應該再次觸發告警
            assert mock_trigger.call_count == 2

    @patch("core.exceptions.logger")
    def test_trigger_alert_logging(self, mock_logger):
        """測試觸發告警的日誌記錄"""
        self.monitor._trigger_alert("ValueError", 15, ErrorSeverity.HIGH)

        # 檢查是否記錄了critical級別的日誌
        mock_logger.critical.assert_called_once()
        call_args = mock_logger.critical.call_args

        assert "告警: ValueError 異常頻率過高" in call_args[0][0]
        assert "15 次" in call_args[0][0]
        assert "high" in call_args[0][0]

        # 檢查extra參數
        extra = call_args[1]["extra"]
        assert extra["alert_type"] == "high_error_rate"
        assert extra["exception_type"] == "ValueError"
        assert extra["error_count"] == 15
        assert extra["severity"] == "high"


class TestMonitorExceptionsDecorator:
    """測試異常監控裝飾器"""

    def setup_method(self):
        """每個測試前重設監控器"""
        # 清空全域監控器
        exception_monitor.error_counts.clear()
        exception_monitor.error_rates.clear()
        exception_monitor.last_alert_time.clear()

    def test_monitor_exceptions_sync_success(self):
        """測試同步異常監控成功情況"""

        @monitor_exceptions(ErrorSeverity.MEDIUM)
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"
        assert len(exception_monitor.error_counts) == 0

    def test_monitor_exceptions_sync_with_exception(self):
        """測試同步異常監控捕獲異常"""

        @monitor_exceptions(ErrorSeverity.HIGH)
        def failing_function():
            raise ValueError("Test exception")

        with pytest.raises(ValueError):
            failing_function()

        # 檢查異常是否被記錄
        assert "ValueError" in exception_monitor.error_counts
        records = exception_monitor.error_counts["ValueError"]
        assert len(records) == 1
        assert records[0]["severity"] == ErrorSeverity.HIGH
        assert records[0]["message"] == "Test exception"

    @pytest.mark.asyncio
    async def test_monitor_exceptions_async_success(self):
        """測試異步異常監控成功情況"""

        @monitor_exceptions(ErrorSeverity.LOW)
        async def successful_async_function():
            return "async success"

        result = await successful_async_function()
        assert result == "async success"
        assert len(exception_monitor.error_counts) == 0

    @pytest.mark.asyncio
    async def test_monitor_exceptions_async_with_exception(self):
        """測試異步異常監控捕獲異常"""

        @monitor_exceptions(ErrorSeverity.CRITICAL)
        async def failing_async_function():
            raise RuntimeError("Async test exception")

        with pytest.raises(RuntimeError):
            await failing_async_function()

        # 檢查異常是否被記錄
        assert "RuntimeError" in exception_monitor.error_counts
        records = exception_monitor.error_counts["RuntimeError"]
        assert len(records) == 1
        assert records[0]["severity"] == ErrorSeverity.CRITICAL
        assert records[0]["message"] == "Async test exception"

    def test_monitor_exceptions_with_context_function(self):
        """測試帶上下文函數的異常監控"""

        def extract_context(*args, **kwargs):
            return {"args": list(args), "kwargs": kwargs}

        @monitor_exceptions(ErrorSeverity.MEDIUM, context_func=extract_context)
        def function_with_context(user_id, action="login"):
            raise ValueError("Context test error")

        with pytest.raises(ValueError):
            function_with_context(123, action="logout")

        # 檢查上下文是否被正確記錄
        records = exception_monitor.error_counts["ValueError"]
        assert len(records) == 1
        context = records[0]["context"]
        assert context["args"] == [123]
        assert context["kwargs"] == {"action": "logout"}


class TestCombinedDecorators:
    """測試組合裝飾器"""

    @pytest.mark.asyncio
    async def test_database_operation_decorator_success(self):
        """測試數據庫操作組合裝飾器成功情況"""

        @database_operation("select", "users", max_retries=2, timeout=5.0)
        async def successful_db_query():
            await asyncio.sleep(0.1)
            return "query result"

        result = await successful_db_query()
        assert result == "query result"

    @pytest.mark.asyncio
    async def test_database_operation_decorator_with_retry(self):
        """測試數據庫操作裝飾器重試機制"""
        call_count = 0

        @database_operation("insert", "products", max_retries=2, timeout=5.0)
        async def flaky_db_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary DB error")
            return "insert successful"

        result = await flaky_db_operation()
        assert result == "insert successful"
        assert call_count == 3  # 初始調用 + 2次重試

    @pytest.mark.asyncio
    async def test_database_operation_decorator_timeout(self):
        """測試數據庫操作裝飾器超時處理"""

        @database_operation("select", "users", timeout=0.1)
        async def slow_db_operation():
            await asyncio.sleep(0.5)
            return "should not complete"

        with pytest.raises(AsyncOperationError) as exc_info:
            await slow_db_operation()

        assert "slow_db_operation 執行超時" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_resilient_api_call_decorator_success(self):
        """測試彈性API調用裝飾器成功情況"""

        @resilient_api_call("external_api", max_retries=2, timeout=5.0)
        async def successful_api_call():
            await asyncio.sleep(0.1)
            return "api response"

        result = await successful_api_call()
        assert result == "api response"

    @pytest.mark.asyncio
    async def test_resilient_api_call_decorator_with_fallback(self):
        """測試彈性API調用裝飾器降級處理"""

        async def api_fallback(*args, **kwargs):
            return "fallback response"

        @resilient_api_call("external_api", max_retries=1, timeout=5.0, fallback_func=api_fallback)
        async def failing_api_call():
            raise Exception("API unavailable")

        result = await failing_api_call()
        assert result == "fallback response"

    @pytest.mark.asyncio
    async def test_resilient_api_call_decorator_timeout(self):
        """測試彈性API調用裝飾器超時處理"""

        @resilient_api_call("slow_api", timeout=0.1)
        async def slow_api_call():
            await asyncio.sleep(0.5)
            return "should timeout"

        with pytest.raises(AsyncOperationError) as exc_info:
            await slow_api_call()

        assert "執行超時" in exc_info.value.message
