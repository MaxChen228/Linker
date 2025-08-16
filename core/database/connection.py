"""
資料庫連線管理模組

提供一個強健、線程安全的 PostgreSQL 連線池管理器。
此模組經過重構，解決了先前版本可能存在的記憶體洩漏問題，並增強了穩定性。

主要功能：
- 使用 `asyncpg` 提供高效的異步資料庫操作。
- 透過 Singleton 和弱引用 (`weakref`) 模式管理全域唯一的連線實例，確保資源有效利用和回收。
- 從環境變數安全地載入資料庫配置，避免硬編碼。
- 提供優雅的連線池建立、關閉和清理機制。
- 包含詳細的健康檢查功能，監控連線池狀態。
- 提供異步上下文管理器 (`asynccontextmanager`)，簡化連線的獲取和釋放。
- 整合應用生命週期事件（啟動和關閉）。
"""

import asyncio
import os
import threading
import weakref
from contextlib import asynccontextmanager
from typing import Any, Optional

import asyncpg

from core.database.exceptions import (
    DatabaseTimeoutError,
    classify_database_error,
)
from core.log_config import get_module_logger

# 引入統一的資料庫配置管理系統
try:
    from core.settings.database import get_database_config

    _database_config_available = True
except ImportError:
    _database_config_available = False


class DatabaseSettings:
    """從環境變數載入資料庫相關設定。"""

    def __init__(self):
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        if _database_config_available:
            try:
                db_config = get_database_config()
                self.DATABASE_URL = db_config.get_url() if db_config.is_configured() else None
            except Exception as e:
                print(f"⚠️  資料庫配置載入失敗: {e}")
                self.DATABASE_URL = None
        else:
            self.DATABASE_URL = os.getenv("DATABASE_URL")

        if not self.DATABASE_URL:
            raise ValueError(
                "資料庫連接 URL 未配置。請設定 DATABASE_URL 環境變數。\n"
                "範例: DATABASE_URL=postgresql://user:password@host:5432/database"
            )

        self.DB_POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
        self.DB_POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
        self.DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "10"))
        self.USE_DATABASE = os.getenv("USE_DATABASE", "true").lower() == "true"


class DatabaseConnection:
    """
    資料庫連線管理器 (Singleton 模式)。

    此類別管理 `asyncpg` 連線池的生命週期，確保在整個應用中只有一個實例。
    使用 `weakref` 來防止記憶體洩漏。
    """

    _instances = weakref.WeakValueDictionary()
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if "main" not in cls._instances:
                instance = super().__new__(cls)
                cls._instances["main"] = instance
                instance._initialized = False
            return cls._instances["main"]

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._pool: Optional[asyncpg.Pool] = None
        self._settings = DatabaseSettings()
        self._logger = get_module_logger(self.__class__.__name__)
        self._cleanup_lock: Optional[asyncio.Lock] = None
        self._is_shutting_down = False
        self._initialized = True

    async def _ensure_cleanup_lock(self) -> asyncio.Lock:
        """延遲創建異步鎖，確保在事件循環中創建。"""
        if self._cleanup_lock is None:
            self._cleanup_lock = asyncio.Lock()
        return self._cleanup_lock

    @property
    def pool(self) -> Optional[asyncpg.Pool]:
        """獲取當前的 `asyncpg` 連線池實例。"""
        return self._pool

    @property
    def is_connected(self) -> bool:
        """檢查連線池是否已建立且處於活動狀態。"""
        return self._pool is not None and not self._pool._closed and not self._is_shutting_down

    async def connect(self) -> Optional[asyncpg.Pool]:
        """
        建立資料庫連線池。

        如果連線池已存在，則直接返回。否則，創建一個新的連線池。
        此操作是線程安全的。

        Returns:
            一個 `asyncpg.Pool` 物件，如果 `USE_DATABASE` 為 False 則返回 None。
        """
        if not self._settings.USE_DATABASE:
            self._logger.info("資料庫功能未啟用，跳過連線。")
            return None

        if self._is_shutting_down:
            self._logger.warning("連線管理器正在關閉，無法建立新連線。 সন")
            return None

        if self.is_connected:
            return self._pool

        cleanup_lock = await self._ensure_cleanup_lock()
        async with cleanup_lock:
            if self.is_connected:
                return self._pool

            try:
                self._logger.info("正在建立資料庫連線池...")
                self._pool = await asyncpg.create_pool(
                    dsn=self._settings.DATABASE_URL,
                    min_size=self._settings.DB_POOL_MIN_SIZE,
                    max_size=self._settings.DB_POOL_MAX_SIZE,
                    server_settings={"application_name": "linker_app", "timezone": "UTC"},
                    command_timeout=self._settings.DB_POOL_TIMEOUT,
                    max_inactive_connection_lifetime=300.0,  # 5分鐘後回收閒置連線
                )
                async with self._pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                self._logger.info(
                    f"資料庫連線池建立成功 (min: {self._settings.DB_POOL_MIN_SIZE}, max: {self._settings.DB_POOL_MAX_SIZE})。"
                )
                return self._pool
            except Exception as e:
                classified_error = classify_database_error(e)
                self._logger.error(f"建立資料庫連線池失敗: {classified_error}")
                await self._cleanup_failed_pool()
                raise classified_error from e

    async def disconnect(self) -> None:
        """安全地關閉資料庫連線池，並等待所有連線釋放。"""
        cleanup_lock = await self._ensure_cleanup_lock()
        async with cleanup_lock:
            self._is_shutting_down = True
            if self._pool and not self._pool._closed:
                try:
                    await asyncio.wait_for(
                        self._pool.close(), timeout=self._settings.DB_POOL_TIMEOUT
                    )
                    self._logger.info("資料庫連線池已安全關閉。 সন")
                except asyncio.TimeoutError:
                    self._logger.warning("關閉連線池超時，將強制終止。 সন")
                    await self._force_close_pool()
                except Exception as e:
                    self._logger.error(f"關閉資料庫連線池時發生錯誤: {e}")
                    await self._force_close_pool()
                finally:
                    self._pool = None

    async def _cleanup_failed_pool(self) -> None:
        """在連線建立失敗後，清理可能部分初始化的連線池。"""
        if self._pool:
            try:
                await asyncio.wait_for(self._pool.close(), timeout=5.0)
            except Exception as e:
                self._logger.warning(f"清理失敗的連線池時發生錯誤: {e}，將強制終止。 সন")
                await self._force_close_pool()
            finally:
                self._pool = None

    async def _force_close_pool(self) -> None:
        """強制終止連線池中的所有連線。"""
        if self._pool:
            try:
                await self._pool.terminate()
                self._logger.warning("連線池已強制終止。 সন")
            except Exception as e:
                self._logger.error(f"強制終止連線池失敗: {e}")
            finally:
                self._pool = None

    async def health_check(self) -> dict[str, Any]:
        """
        執行詳細的健康檢查。

        Returns:
            一個包含連線狀態、連線池統計和測試查詢結果的字典。
        """
        if not self._settings.USE_DATABASE:
            return {"status": "disabled", "message": "資料庫功能未啟用。"}
        if self._is_shutting_down:
            return {"status": "shutting_down", "message": "連線管理器正在關閉。"}
        if not self.is_connected:
            return {"status": "disconnected", "message": "資料庫未連線。"}

        try:

            async def _do_health_check():
                async with self._pool.acquire() as conn:
                    result = await conn.fetchval("SELECT 1")
                    pool_status = {
                        "size": self._pool.get_size(),
                        "min_size": self._pool._minsize,
                        "max_size": self._pool._maxsize,
                        "idle_connections": self._pool.get_idle_size(),
                    }
                    return {
                        "status": "healthy",
                        "message": "資料庫連線正常。",
                        "pool_status": pool_status,
                        "test_query_result": result,
                    }

            return await asyncio.wait_for(
                _do_health_check(), timeout=self._settings.DB_POOL_TIMEOUT
            )
        except asyncio.TimeoutError:
            return {"status": "timeout", "message": "資料庫連線超時。"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"資料庫連線異常: {e}"}

    @asynccontextmanager
    async def get_connection(self) -> Any:
        """
        提供一個上下文管理器來獲取資料庫連線。

        使用範例:
        async with db.get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
        """
        if self._is_shutting_down:
            raise RuntimeError("連線管理器正在關閉，無法獲取新連線。 সন")
        if not self.is_connected:
            await self.connect()
        if not self._pool:
            raise RuntimeError("資料庫連線池未初始化。 সন")

        try:
            async with self._pool.acquire() as conn:
                yield conn
        except asyncio.TimeoutError as e:
            raise DatabaseTimeoutError("獲取資料庫連線超時。") from e
        except Exception as e:
            self._logger.error(f"資料庫操作失敗: {e}")
            raise

    async def execute_script(self, script_path: str) -> None:
        """
        執行一個 SQL 腳本檔案。

        Args:
            script_path: SQL 腳本的檔案路徑。
        """
        if self._is_shutting_down:
            raise RuntimeError("連線管理器正在關閉。 সন")
        if not self.is_connected:
            await self.connect()

        try:
            with open(script_path, encoding="utf-8") as f:
                script = f.read()
            async with self.get_connection() as conn:
                await conn.execute(script)
            self._logger.info(f"成功執行 SQL 腳本: {script_path}")
        except FileNotFoundError:
            self._logger.error(f"找不到 SQL 腳本檔案: {script_path}")
            raise
        except Exception as e:
            self._logger.error(f"執行 SQL 腳本失敗: {e}")
            raise

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


_db_connection_lock = threading.Lock()
_db_connection_ref: Optional[weakref.ReferenceType] = None


def get_database_connection() -> DatabaseConnection:
    """獲取全域的資料庫連線管理器實例（線程安全且支援記憶體回收）。"""
    global _db_connection_ref
    current_connection = _db_connection_ref() if _db_connection_ref else None
    if current_connection is None:
        with _db_connection_lock:
            current_connection = _db_connection_ref() if _db_connection_ref else None
            if current_connection is None:
                new_connection = DatabaseConnection()
                _db_connection_ref = weakref.ref(new_connection)
                return new_connection
    return current_connection


def clear_database_connection() -> None:
    """清理資料庫連線實例，主要用於測試和應用關閉。"""
    global _db_connection_ref
    with _db_connection_lock:
        _db_connection_ref = None


async def get_db_pool() -> Optional[asyncpg.Pool]:
    """便捷函數，獲取資料庫連線池（主要為向後相容）。"""
    db_conn = get_database_connection()
    return await db_conn.connect()


async def initialize_database() -> bool:
    """
    初始化資料庫連線，並執行健康檢查。

    Returns:
        如果初始化和健康檢查成功，返回 True。
    """
    try:
        db_conn = get_database_connection()
        await db_conn.connect()
        health = await db_conn.health_check()
        if health["status"] in ["healthy", "disabled"]:
            return True
        db_conn._logger.error(f"資料庫健康檢查失敗: {health}")
        return False
    except Exception as e:
        get_module_logger("initialize_database").error(f"初始化資料庫失敗: {e}")
        return False


async def cleanup_database() -> None:
    """清理並關閉資料庫連線。"""
    current_connection = _db_connection_ref() if _db_connection_ref else None
    if current_connection:
        try:
            await current_connection.disconnect()
            get_module_logger("cleanup_database").info("資料庫連線清理成功。 সন")
        except Exception as e:
            get_module_logger("cleanup_database").error(f"清理資料庫連線時發生錯誤: {e}")
    clear_database_connection()


# --- 應用生命週期支援 ---


async def startup_database() -> bool:
    """在應用啟動時初始化資料庫。"""
    success = await initialize_database()
    if success:
        get_module_logger("startup_database").info("資料庫連線初始化成功。 সন")
    return success


async def shutdown_database() -> None:
    """在應用關閉時清理資料庫。"""
    await cleanup_database()
    get_module_logger("shutdown_database").info("資料庫連線清理完成。 সন")
