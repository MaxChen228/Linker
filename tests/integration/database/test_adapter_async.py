"""
KnowledgeManagerAdapter 異步初始化測試
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from core.database.adapter import KnowledgeManagerAdapter
from core.knowledge import ErrorCategory, KnowledgePoint, OriginalError
from tests.unit.core.test_mock_helpers import create_mock_database_connection


class TestKnowledgeManagerAdapter:
    """測試適配器的異步初始化邏輯"""

    @pytest.mark.asyncio
    async def test_json_mode_initialization(self):
        """測試 JSON 模式初始化"""
        adapter = KnowledgeManagerAdapter(use_database=False, data_dir="test_data")

        # 應該已經同步初始化完成
        # 兼容 bool 和 Event 兩種類型
        init_complete = adapter._initialization_complete
        assert (isinstance(init_complete, bool) and init_complete) or (
            hasattr(init_complete, "is_set") and init_complete.is_set()
        )
        assert adapter._legacy_manager is not None

        # 確保初始化檢查不會阻塞
        await adapter._ensure_initialized()

    @pytest.mark.asyncio
    async def test_database_mode_lazy_initialization(self):
        """測試資料庫模式延遲初始化"""
        with (
            patch("core.database.adapter.get_database_connection") as mock_get_conn,
            patch("core.database.adapter.KnowledgePointRepository") as mock_repo_class,
        ):
            mock_conn, mock_pool, mock_db_conn = create_mock_database_connection()
            mock_get_conn.return_value = mock_conn

            # Mock repository 實例
            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            adapter = KnowledgeManagerAdapter(use_database=True)

            # 初始狀態：未初始化
            # 兼容 bool 和 Event 兩種類型
            init_complete = adapter._initialization_complete
            if hasattr(init_complete, "is_set"):
                assert not init_complete.is_set()
            else:
                assert not init_complete
            assert adapter._repository is None

            # 觸發初始化
            await adapter._ensure_initialized()

            # 驗證初始化完成
            # 檢查初始化完成
            init_complete = adapter._initialization_complete
            assert (isinstance(init_complete, bool) and init_complete) or (
                hasattr(init_complete, "is_set") and init_complete.is_set()
            )
            assert adapter._repository is not None
            mock_conn.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_initialization_failure_fallback(self):
        """測試資料庫初始化失敗時的降級機制"""
        with patch("core.database.adapter.get_database_connection") as mock_get_conn:
            mock_conn = AsyncMock()
            mock_conn.connect.side_effect = Exception("Connection failed")
            mock_get_conn.return_value = mock_conn

            adapter = KnowledgeManagerAdapter(use_database=True)

            # 觸發初始化（應該降級到 JSON 模式）
            await adapter._ensure_initialized()

            # 驗證降級成功
            # 檢查初始化完成
            init_complete = adapter._initialization_complete
            assert (isinstance(init_complete, bool) and init_complete) or (
                hasattr(init_complete, "is_set") and init_complete.is_set()
            )
            assert not adapter.use_database
            assert adapter._legacy_manager is not None

    @pytest.mark.asyncio
    async def test_concurrent_initialization(self):
        """測試並發初始化的安全性"""
        with (
            patch("core.database.adapter.get_database_connection") as mock_get_conn,
            patch("core.database.adapter.KnowledgePointRepository") as mock_repo_class,
        ):
            mock_conn, mock_pool, mock_db_conn = create_mock_database_connection()
            mock_get_conn.return_value = mock_conn

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            adapter = KnowledgeManagerAdapter(use_database=True)

            # 模擬多個並發初始化請求
            tasks = [adapter._ensure_initialized() for _ in range(10)]

            # 所有任務都應該成功完成
            await asyncio.gather(*tasks)

            # 驗證只進行了一次初始化
            # 檢查初始化完成
            init_complete = adapter._initialization_complete
            assert (isinstance(init_complete, bool) and init_complete) or (
                hasattr(init_complete, "is_set") and init_complete.is_set()
            )
            mock_conn.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_asyncio_run_in_async_methods(self):
        """測試異步方法中不使用 asyncio.run()"""
        adapter = KnowledgeManagerAdapter(use_database=False)

        # 模擬知識點
        knowledge_point = KnowledgePoint(
            id=1,
            key_point="Test",
            category=ErrorCategory.OTHER,
            subtype="test",
            explanation="test",
            original_phrase="test",
            correction="test",
            original_error=OriginalError(
                chinese_sentence="test",
                user_answer="test",
                correct_answer="test",
                timestamp="2024-01-01T00:00:00",
            ),
        )

        # 這些調用在異步上下文中不應該拋出 RuntimeError
        result = await adapter.add_knowledge_point_async(knowledge_point)
        assert result is True

        points = await adapter.get_knowledge_points_async()
        assert len(points) > 0

        found_point = await adapter.get_knowledge_point_async("1")
        assert found_point is not None

    @pytest.mark.asyncio
    async def test_initialization_timeout(self):
        """測試初始化超時處理"""
        with patch("core.database.adapter.get_database_connection") as mock_get_conn:
            mock_conn = AsyncMock()

            # 模擬連接掛起 - 使用協程包裝 sleep
            async def hanging_connect():
                await asyncio.sleep(60)
                return None

            mock_conn.connect.side_effect = hanging_connect
            mock_get_conn.return_value = mock_conn

            adapter = KnowledgeManagerAdapter(use_database=True)

            # 應該在超時後降級到 JSON 模式（我們新的安全行為）
            # 而不是拋出異常，因為我們有自動降級機制
            await adapter._ensure_initialized()

            # 驗證降級到 JSON 模式
            # 檢查初始化完成
            init_complete = adapter._initialization_complete
            assert (isinstance(init_complete, bool) and init_complete) or (
                hasattr(init_complete, "is_set") and init_complete.is_set()
            )
            assert not adapter.use_database  # 應該降級到 JSON 模式
            assert adapter._legacy_manager is not None

    @pytest.mark.asyncio
    async def test_resource_cleanup(self):
        """測試資源清理"""
        with (
            patch("core.database.adapter.get_database_connection") as mock_get_conn,
            patch("core.database.adapter.KnowledgePointRepository") as mock_repo_class,
        ):
            mock_conn, mock_pool, mock_db_conn = create_mock_database_connection()
            mock_get_conn.return_value = mock_conn

            mock_repo = AsyncMock()
            mock_repo_class.return_value = mock_repo

            adapter = KnowledgeManagerAdapter(use_database=True)
            await adapter._ensure_initialized()

            # 確保資源已分配
            assert adapter._db_connection is not None
            assert adapter._repository is not None

            # 清理資源
            await adapter.cleanup()

            # 驗證資源已清理
            assert adapter._db_connection is None
            assert adapter._repository is None
            mock_conn.disconnect.assert_called_once()

    def test_sync_methods_limitations(self):
        """測試同步方法的功能限制"""
        adapter = KnowledgeManagerAdapter(use_database=True)

        # 資料庫模式下，同步方法應該有功能限制
        result = adapter.get_knowledge_point("1")
        assert result is None  # 應該返回 None 並記錄警告

        # JSON 模式下，同步方法應該正常工作
        adapter_json = KnowledgeManagerAdapter(use_database=False)
        points = adapter_json.knowledge_points
        assert isinstance(points, list)
