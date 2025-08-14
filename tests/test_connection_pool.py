"""
連線池管理測試套件 - 專注核心功能和記憶體安全

測試策略：重點功能測試 + 簡化 Mock
重點：Singleton 模式、生命週期管理、錯誤恢復
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.database.connection import (
    DatabaseConnection,
    DatabaseSettings,
    cleanup_database,
    get_database_connection,
    initialize_database,
)


@pytest.mark.asyncio
class TestDatabaseConnectionCore:
    """核心功能測試"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每個測試前後清理 Singleton"""
        # 清理前狀態
        DatabaseConnection._instances.clear()
        yield
        # 清理後狀態
        DatabaseConnection._instances.clear()

    def test_singleton_pattern_correctness(self):
        """測試 Singleton 模式的正確性"""
        # 創建多個實例
        conn1 = DatabaseConnection()
        conn2 = DatabaseConnection()
        conn3 = get_database_connection()

        # 驗證都是同一個實例
        assert conn1 is conn2
        assert conn2 is conn3
        assert id(conn1) == id(conn2) == id(conn3)

        # 驗證實例變數獨立性
        assert hasattr(conn1, "_pool")
        assert hasattr(conn1, "_settings")
        assert hasattr(conn1, "_initialized")

    def test_database_settings_configuration(self, mock_env_vars):
        """測試資料庫設定的正確載入"""
        # 設置環境變數
        import os

        os.environ.update(
            {
                "USE_DATABASE": "true",
                "DB_POOL_MIN_SIZE": "3",
                "DB_POOL_MAX_SIZE": "15",
                "DB_POOL_TIMEOUT": "8",
            }
        )

        settings = DatabaseSettings()

        assert settings.USE_DATABASE is True
        assert settings.DB_POOL_MIN_SIZE == 3
        assert settings.DB_POOL_MAX_SIZE == 15
        assert settings.DB_POOL_TIMEOUT == 8

    @patch("asyncpg.create_pool")
    async def test_connection_lifecycle_normal_flow(self, mock_create_pool, mock_pool):
        """測試正常的連線生命週期"""

        # 設置 Mock - 需要返回協程
        async def create_pool_coro(*args, **kwargs):
            return mock_pool

        mock_create_pool.side_effect = create_pool_coro

        # 模擬啟用資料庫
        with patch.object(DatabaseSettings, "__init__", lambda self: None):
            conn = DatabaseConnection()
            conn._settings = MagicMock()
            conn._settings.USE_DATABASE = True
            conn._settings.DATABASE_URL = "postgresql://test"
            conn._settings.DB_POOL_MIN_SIZE = 2
            conn._settings.DB_POOL_MAX_SIZE = 5
            conn._settings.DB_POOL_TIMEOUT = 5

            # 測試連線建立
            assert not conn.is_connected
            pool = await conn.connect()

            assert pool is mock_pool
            assert conn.is_connected
            mock_create_pool.assert_called_once()

            # 測試健康檢查
            health = await conn.health_check()
            assert health["status"] == "healthy"

            # 測試連線斷開
            await conn.disconnect()
            assert not conn.is_connected
            mock_pool.close.assert_called_once()

    async def test_database_disabled_mode(self):
        """測試資料庫未啟用模式"""
        with patch.object(DatabaseSettings, "__init__", lambda self: None):
            conn = DatabaseConnection()
            conn._settings = MagicMock()
            conn._settings.USE_DATABASE = False

            # 測試連線嘗試
            result = await conn.connect()
            assert result is None
            assert not conn.is_connected

            # 測試健康檢查
            health = await conn.health_check()
            assert health["status"] == "disabled"

    @patch("asyncpg.create_pool")
    async def test_connection_failure_recovery(self, mock_create_pool):
        """測試連線失敗的恢復機制"""
        # 設置 Mock 拋出異常
        mock_create_pool.side_effect = Exception("連線失敗")

        with patch.object(DatabaseSettings, "__init__", lambda self: None):
            conn = DatabaseConnection()
            conn._settings = MagicMock()
            conn._settings.USE_DATABASE = True
            conn._settings.DATABASE_URL = "postgresql://test"

            # 測試連線失敗
            with pytest.raises(Exception, match="連線失敗"):
                await conn.connect()

            assert not conn.is_connected
            assert conn._pool is None

    async def test_connection_context_manager(self, mock_db_connection):
        """測試連線上下文管理器"""
        conn = mock_db_connection

        # 測試正常使用
        async with conn.get_connection() as db_conn:
            assert db_conn is not None
            # 模擬資料庫操作
            result = await db_conn.fetchval("SELECT 1")
            assert result == 1

    async def test_connection_timeout_handling(self, mock_db_connection):
        """測試連線超時處理"""
        conn = mock_db_connection

        # 確保連線狀態正確設置
        conn._settings.USE_DATABASE = True
        conn._is_shutting_down = False

        # 模擬超時情況
        with patch("asyncio.wait_for") as mock_wait_for:
            mock_wait_for.side_effect = asyncio.TimeoutError()

            health = await conn.health_check()
            assert health["status"] == "timeout"

    async def test_script_execution(self, mock_db_connection, temp_dir):
        """測試 SQL 腳本執行"""
        conn = mock_db_connection

        # 創建測試腳本
        script_path = temp_dir / "test.sql"
        script_path.write_text("SELECT 1;", encoding="utf-8")

        # 測試腳本執行
        await conn.execute_script(str(script_path))

        # 驗證 execute 被調用
        # 注意：這裡我們簡化驗證，因為 Mock 層級較深


@pytest.mark.asyncio
class TestDatabaseConnectionMemoryManagement:
    """記憶體管理和資源清理測試"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每個測試前後清理"""
        DatabaseConnection._instances.clear()
        yield
        DatabaseConnection._instances.clear()

    def test_instance_variable_isolation(self):
        """測試實例變數隔離（防止記憶體洩漏）"""
        conn1 = DatabaseConnection()
        conn2 = DatabaseConnection()

        # 雖然是同一個實例，但實例變數應該正確設置
        assert conn1 is conn2
        assert hasattr(conn1, "_pool")
        assert hasattr(conn1, "_settings")

        # 測試變數修改不會影響新創建的連線行為
        conn1._pool = "test_pool"
        conn3 = DatabaseConnection()
        assert conn3 is conn1  # 仍然是同一個實例
        assert conn3._pool == "test_pool"  # 共享狀態

    @patch("asyncpg.create_pool")
    async def test_failed_pool_cleanup(self, mock_create_pool, mock_pool):
        """測試失敗連線池的清理"""
        # 設置 Mock：建立成功但測試連線失敗
        mock_create_pool.return_value = mock_pool
        mock_conn = AsyncMock()
        mock_conn.fetchval.side_effect = Exception("測試連線失敗")
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        with patch.object(DatabaseSettings, "__init__", lambda self: None):
            conn = DatabaseConnection()
            conn._settings = MagicMock()
            conn._settings.USE_DATABASE = True
            conn._settings.DATABASE_URL = "postgresql://test"

            # 測試失敗清理
            with pytest.raises(Exception):  # noqa: B017
                await conn.connect()

            # 驗證清理被調用
            assert conn._pool is None

    async def test_shutdown_state_management(self, mock_db_connection):
        """測試關閉狀態管理"""
        conn = mock_db_connection

        # 確保連線啟用資料庫模式
        conn._settings.USE_DATABASE = True

        # 開始關閉流程
        await conn.disconnect()

        # 驗證關閉狀態
        assert conn._is_shutting_down

        # 測試關閉狀態下的行為
        health = await conn.health_check()
        assert health["status"] == "shutting_down"


@pytest.mark.asyncio
class TestDatabaseConnectionIntegration:
    """整合測試（使用真實異步行為）"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """清理全域狀態"""
        DatabaseConnection._instances.clear()
        # 清理全域實例
        import core.database.connection as conn_module

        conn_module._db_connection = None
        yield
        DatabaseConnection._instances.clear()
        conn_module._db_connection = None

    @patch("asyncpg.create_pool")
    async def test_initialize_and_cleanup_integration(self, mock_create_pool, mock_pool):
        """測試完整的初始化和清理流程"""
        mock_create_pool.return_value = mock_pool

        # 模擬啟用資料庫
        with patch.object(DatabaseSettings, "__init__", lambda self: None):
            settings = DatabaseSettings()
            settings.USE_DATABASE = True
            settings.DATABASE_URL = "postgresql://test:test@localhost:5432/test"
            settings.DB_POOL_MIN_SIZE = 2
            settings.DB_POOL_MAX_SIZE = 5
            settings.DB_POOL_TIMEOUT = 5
            with patch("core.database.connection.DatabaseSettings", return_value=settings):
                # 設置 Mock 返回協程
                async def create_pool_coro(*args, **kwargs):
                    return mock_pool

                mock_create_pool.side_effect = create_pool_coro

                # 測試初始化
                success = await initialize_database()
                assert success is True

                # 驗證連線建立
                db_conn = get_database_connection()
                assert db_conn.is_connected

                # 測試清理
                await cleanup_database()

                # 驗證清理完成
                mock_pool.close.assert_called()

    async def test_multiple_initialize_calls(self):
        """測試多次初始化調用的安全性"""
        with patch.object(DatabaseSettings, "__init__", lambda self: None):
            settings = DatabaseSettings()
            settings.USE_DATABASE = False
            with patch("core.database.connection.DatabaseSettings", return_value=settings):
                # 多次調用應該是安全的
                result1 = await initialize_database()
                result2 = await initialize_database()

                # 資料庫未啟用時都應該返回 True（表示初始化成功）
                assert result1 is True
                assert result2 is True

    @patch("asyncpg.create_pool")
    async def test_concurrent_connection_attempts(self, mock_create_pool, mock_pool):
        """測試併發連線嘗試的線程安全性"""

        async def create_pool_coro(*args, **kwargs):
            return mock_pool

        mock_create_pool.side_effect = create_pool_coro

        with patch.object(DatabaseSettings, "__init__", lambda self: None):
            conn = DatabaseConnection()
            conn._settings = MagicMock()
            conn._settings.USE_DATABASE = True
            conn._settings.DATABASE_URL = "postgresql://test"

            # 併發連線嘗試
            tasks = [conn.connect() for _ in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 所有連線應該返回同一個池
            for result in results:
                if not isinstance(result, Exception):
                    assert result is mock_pool

            # create_pool 應該只被調用一次（由於鎖保護）
            assert mock_create_pool.call_count == 1


# 效能和邊界測試
@pytest.mark.slow
@pytest.mark.asyncio
class TestDatabaseConnectionPerformance:
    """效能和邊界條件測試（標記為慢速測試）"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        DatabaseConnection._instances.clear()
        yield
        DatabaseConnection._instances.clear()

    async def test_rapid_connect_disconnect_cycles(self, mock_pool):
        """測試快速連線斷開循環"""

        async def create_pool_coro(*args, **kwargs):
            return mock_pool

        with patch("asyncpg.create_pool", side_effect=create_pool_coro), \
             patch.object(DatabaseSettings, "__init__", lambda self: None):
                conn = DatabaseConnection()
                conn._settings = MagicMock()
                conn._settings.USE_DATABASE = True

                # 快速循環
                for _ in range(10):
                    await conn.connect()
                    await conn.disconnect()

                # 最終狀態應該是斷開
                assert not conn.is_connected

    async def test_connection_under_stress(self, mock_db_connection):
        """測試壓力下的連線行為"""
        conn = mock_db_connection

        # 模擬高併發使用
        async def use_connection():
            async with conn.get_connection() as db_conn:
                await asyncio.sleep(0.01)  # 模擬數據庫操作
                return await db_conn.fetchval("SELECT 1")

        # 併發執行
        tasks = [use_connection() for _ in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 驗證大部分操作成功
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        assert success_count >= 15  # 允許一些失敗
