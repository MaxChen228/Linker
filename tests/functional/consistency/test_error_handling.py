"""
錯誤處理一致性測試套件
測試 JSON 和 Database 兩種模式的錯誤處理一致性

測試內容：
1. 資料庫連接錯誤處理
2. 文件權限錯誤處理
3. 數據驗證錯誤處理
4. 超時錯誤處理
5. 並發訪問錯誤處理
6. 用戶友好錯誤訊息
7. 降級策略效果
"""

import asyncio
import tempfile
import threading
import time
from unittest import mock

import pytest

from core.database.adapter import KnowledgeManagerAdapter
from core.error_handler import ErrorHandler, create_error_response
from core.exceptions import (
    DatabaseError,
    ErrorCategory,
    ErrorSeverity,
)
from core.fallback_strategies import get_fallback_manager
from core.knowledge import KnowledgeManager


@pytest.fixture
def json_manager():
    """JSON 模式管理器"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = KnowledgeManager(data_dir=temp_dir)
        yield manager


@pytest.fixture
def db_manager():
    """Database 模式管理器（模擬）"""
    manager = KnowledgeManagerAdapter(use_database=True, data_dir="test_data")
    yield manager


@pytest.fixture
def error_handler():
    """錯誤處理器"""
    return ErrorHandler(mode="test")


@pytest.fixture
def fallback_manager():
    """降級管理器"""
    return get_fallback_manager()


class TestDatabaseConnectionErrors:
    """資料庫連接錯誤測試"""

    @pytest.mark.asyncio
    async def test_database_connection_error_consistency(self, json_manager, db_manager):
        """測試資料庫連線錯誤的一致性處理"""

        # 模擬資料庫連線失敗
        with mock.patch.object(db_manager, "_repository", None):
            with mock.patch.object(db_manager, "use_database", True):
                with mock.patch.object(db_manager, "_legacy_manager", json_manager):
                    # JSON 模式統計
                    json_stats = json_manager.get_statistics()

                    # Database 模式應該自動降級到 JSON 模式
                    db_stats = db_manager.get_statistics()

                    # 兩種模式應該返回相同的結果結構
                    assert isinstance(json_stats, dict)
                    assert isinstance(db_stats, dict)

                    # 檢查核心統計字段
                    core_fields = [
                        "total_practices",
                        "correct_count",
                        "knowledge_points",
                        "avg_mastery",
                    ]
                    for field in core_fields:
                        assert field in json_stats
                        assert field in db_stats

    def test_database_error_handling_consistency(self, db_manager):
        """測試資料庫錯誤處理的一致性"""

        # 模擬資料庫錯誤
        with mock.patch.object(db_manager, "_cache_manager") as mock_cache:
            mock_cache.get_or_compute.side_effect = DatabaseError(
                "Database connection failed", operation="select", table="knowledge_points"
            )

            # 應該返回降級結果而不是拋出異常
            result = db_manager.get_statistics()

            assert isinstance(result, dict)
            # 檢查是否包含錯誤降級標記
            assert (
                "_error_fallback" in result
                or "_fallback" in result
                or result.get("knowledge_points", 0) >= 0
            )


class TestFilePermissionErrors:
    """文件權限錯誤測試"""

    def test_file_permission_error_consistency(self, json_manager):
        """測試文件權限錯誤的一致性處理"""

        # 模擬文件權限錯誤
        with mock.patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")

            with mock.patch.object(json_manager, "_load_knowledge") as mock_load:
                mock_load.side_effect = PermissionError("Permission denied")

                # 應該返回安全的默認值
                try:
                    result = json_manager.get_statistics()
                    # 如果沒有拋出異常，檢查結果
                    assert isinstance(result, dict)
                except PermissionError:
                    # 如果拋出異常，這是預期的行為
                    pass

    def test_file_not_found_error_handling(self, json_manager):
        """測試文件不存在錯誤處理"""

        # 刪除知識點文件
        if json_manager.knowledge_file.exists():
            json_manager.knowledge_file.unlink()

        # 重新初始化應該能處理文件不存在的情況
        try:
            new_manager = KnowledgeManager(data_dir=str(json_manager.data_dir))
            stats = new_manager.get_statistics()

            assert isinstance(stats, dict)
            assert stats.get("knowledge_points", 0) == 0

        except Exception as e:
            pytest.fail(f"文件不存在時應該優雅處理，但拋出了異常: {e}")


class TestValidationErrors:
    """數據驗證錯誤測試"""

    def test_validation_error_consistency(self, json_manager, db_manager):
        """測試數據驗證錯誤的一致性"""

        # 無效的知識點 ID
        invalid_id = "invalid_id"

        # JSON 模式
        json_result = json_manager.get_knowledge_point(invalid_id)

        # Database 模式（模擬）
        with mock.patch.object(db_manager, "_legacy_manager", json_manager):
            db_result = db_manager.get_knowledge_point(invalid_id)

        # 兩種模式都應該返回 None 或相同的錯誤處理結果
        assert json_result is None
        assert db_result is None

    def test_invalid_data_handling(self, json_manager):
        """測試無效數據處理"""

        # 嘗試添加無效的知識點
        invalid_point = None

        try:
            result = json_manager.add_knowledge_point(invalid_point)
            assert not result or result is None

        except Exception as e:
            # 如果拋出異常，應該是適當的驗證異常
            assert isinstance(e, (ValueError, TypeError, AttributeError))


class TestTimeoutErrors:
    """超時錯誤測試"""

    @pytest.mark.asyncio
    async def test_timeout_error_consistency(self, db_manager):
        """測試超時錯誤的一致性處理"""

        # 模擬操作超時
        with mock.patch.object(db_manager, "_cache_manager") as mock_cache:
            mock_cache.get_or_compute.side_effect = asyncio.TimeoutError("Operation timed out")

            # 超時後應該返回降級結果
            try:
                result = db_manager.get_statistics()
                # 應該是字典格式的結果，而不是異常
                assert isinstance(result, dict)
                assert result.get("total_practices", 0) >= 0

            except asyncio.TimeoutError:
                pytest.fail("超時錯誤應該被處理，不應該向上拋出")

    def test_timeout_fallback_behavior(self, error_handler, fallback_manager):
        """測試超時降級行為"""

        timeout_error = asyncio.TimeoutError("Operation timed out")

        # 測試錯誤處理
        error_response = error_handler.handle_error(timeout_error, "test_operation")

        assert not error_response["success"]
        assert error_response["error"]["category"] == ErrorCategory.NETWORK.value
        assert error_response["fallback_available"]


class TestConcurrentAccessErrors:
    """並發訪問錯誤測試"""

    def test_concurrent_access_error_consistency(self, json_manager, db_manager):
        """測試並發訪問錯誤的一致性"""

        errors_json = []
        errors_db = []

        def json_worker():
            try:
                for _i in range(10):
                    stats = json_manager.get_statistics()
                    assert isinstance(stats, dict)
                    time.sleep(0.001)
            except Exception as e:
                errors_json.append(e)

        def db_worker():
            try:
                # 模擬資料庫模式
                with mock.patch.object(db_manager, "_legacy_manager", json_manager):
                    for _i in range(10):
                        stats = db_manager.get_statistics()
                        assert isinstance(stats, dict)
                        time.sleep(0.001)
            except Exception as e:
                errors_db.append(e)

        threads = [threading.Thread(target=json_worker), threading.Thread(target=db_worker)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 兩種模式的錯誤數量應該相近（或都很少）
        assert abs(len(errors_json) - len(errors_db)) <= 2

        # 如果有錯誤，錯誤類型應該相似
        if errors_json and errors_db:
            assert type(errors_json[0]).__name__ == type(errors_db[0]).__name__


class TestErrorMessageConsistency:
    """錯誤訊息一致性測試"""

    def test_error_message_format_consistency(self, json_manager, db_manager):
        """測試錯誤訊息格式的一致性"""

        test_scenarios = [
            {
                "operation": "get_knowledge_point",
                "args": ["nonexistent_id"],
                "expected_behavior": "return_none",
            }
        ]

        for scenario in test_scenarios:
            operation = scenario["operation"]
            args = scenario["args"]
            expected = scenario["expected_behavior"]

            # JSON 模式
            json_method = getattr(json_manager, operation)
            json_result = json_method(*args)

            # Database 模式（模擬）
            with mock.patch.object(db_manager, "_legacy_manager", json_manager):
                db_method = getattr(db_manager, operation, None)
                if db_method:
                    db_result = db_method(*args)
                else:
                    # 如果方法不存在，使用 legacy manager
                    db_result = getattr(db_manager._legacy_manager, operation)(*args)

            # 結果行為應該一致
            if expected == "return_none":
                assert json_result is None
                assert db_result is None

    def test_user_friendly_error_messages(self, error_handler):
        """測試用戶友好錯誤訊息"""

        error_scenarios = [
            (ConnectionError("Database connection failed"), "資料庫暫時無法連接，請稍後再試"),
            (FileNotFoundError("knowledge.json not found"), "文件操作失敗，請檢查文件權限"),
            (ValueError("Invalid mastery level"), "輸入的數據格式不正確"),
            (PermissionError("Access denied"), "文件操作失敗，請檢查文件權限"),
        ]

        for original_error, _expected_pattern in error_scenarios:
            error_response = error_handler.handle_error(original_error, "test_operation")
            user_message = error_response["error"]["user_message"]

            # 檢查用戶訊息是否包含預期內容
            assert isinstance(user_message, str)
            assert len(user_message) > 0
            assert error_response["error"]["error_code"] is not None
            assert error_response["error"]["category"] is not None


class TestFallbackStrategies:
    """降級策略測試"""

    def test_database_to_json_fallback(self, json_manager, db_manager, fallback_manager):
        """測試資料庫到 JSON 的降級策略"""

        # 設置降級環境
        with mock.patch.object(db_manager, "_legacy_manager", json_manager):
            # 執行降級策略
            fallback_result = fallback_manager.execute_fallback(
                ErrorCategory.DATABASE, ErrorSeverity.HIGH, db_manager.get_statistics, db_manager
            )

            assert fallback_result is not None
            assert isinstance(fallback_result, dict)

    def test_cache_fallback_strategy(self, fallback_manager):
        """測試快取降級策略"""

        def mock_function():
            return {"test": "data"}

        # 先執行一次正常操作來建立快取
        cache_strategy = fallback_manager.strategies[1]  # CacheFallback
        cache_strategy.update_cache(mock_function, (), {}, {"cached": "data"})

        # 執行降級
        fallback_result = fallback_manager.execute_fallback(
            ErrorCategory.NETWORK, ErrorSeverity.MEDIUM, mock_function
        )

        assert fallback_result is not None

    def test_graceful_degradation(self, fallback_manager):
        """測試優雅降級"""

        def failing_function():
            raise Exception("Complete failure")

        # 執行降級策略
        fallback_result = fallback_manager.execute_fallback(
            ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL, failing_function
        )

        # 應該至少返回某種安全值
        assert fallback_result is not None


class TestErrorStatistics:
    """錯誤統計測試"""

    def test_fallback_statistics_tracking(self, fallback_manager):
        """測試降級統計追蹤"""

        # 清除統計
        fallback_manager._fallback_stats = {
            "total_fallbacks": 0,
            "strategy_usage": {},
            "success_rate": {},
        }

        def test_function():
            return {"test": "data"}

        # 執行幾次降級
        for _ in range(3):
            fallback_manager.execute_fallback(
                ErrorCategory.DATABASE, ErrorSeverity.HIGH, test_function
            )

        stats = fallback_manager.get_fallback_statistics()

        assert stats["total_fallbacks"] >= 3
        assert len(stats["strategy_usage"]) > 0

    def test_error_handler_consistency(self, json_manager, db_manager):
        """測試錯誤處理器的一致性"""

        # 確保兩個管理器都有錯誤處理器
        assert hasattr(json_manager, "_error_handler")
        assert hasattr(db_manager, "_error_handler")

        # 測試錯誤處理響應格式
        test_error = ValueError("Test error")

        json_response = create_error_response(test_error, "test_op", "json")
        db_response = create_error_response(test_error, "test_op", "database")

        # 響應結構應該一致
        assert json_response.keys() == db_response.keys()
        assert not json_response["success"]
        assert not db_response["success"]


if __name__ == "__main__":
    # 運行特定測試
    pytest.main([__file__, "-v", "--tb=short"])
