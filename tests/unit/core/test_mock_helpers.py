"""
測試助手：提供正確配置的 AsyncMock 物件
"""

from unittest.mock import AsyncMock


def create_mock_asyncpg_pool():
    """創建正確配置的 asyncpg.Pool mock"""
    mock_pool = AsyncMock()

    # 配置 acquire() 上下文管理器
    mock_acquire_context = AsyncMock()
    mock_connection = AsyncMock()

    # 模擬異步上下文管理器行為
    mock_acquire_context.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_acquire_context.__aexit__ = AsyncMock(return_value=None)

    # 配置 pool.acquire() 返回上下文管理器
    mock_pool.acquire.return_value = mock_acquire_context

    # 配置其他常用屬性
    mock_pool._closed = False
    mock_pool.get_size.return_value = 5
    mock_pool.get_idle_size.return_value = 3
    mock_pool._minsize = 2
    mock_pool._maxsize = 10

    return mock_pool, mock_connection


def create_mock_database_connection():
    """創建正確配置的 DatabaseConnection mock"""
    mock_conn = AsyncMock()
    mock_pool, mock_db_conn = create_mock_asyncpg_pool()

    mock_conn.connect.return_value = mock_pool
    mock_conn.disconnect.return_value = None

    return mock_conn, mock_pool, mock_db_conn
