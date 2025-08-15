"""
修復後的資料庫連線管理 - 解決記憶體洩漏問題
提供 PostgreSQL 連線池管理和健康檢查

關鍵修復：
1. 修正類變數/實例變數混用問題
2. 改進 Singleton 實現
3. 完善資源清理機制
4. 增強異常處理
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

# TASK-34: 引入統一數據庫配置管理系統，消除硬編碼
try:
    from core.settings.database import get_database_config
    _database_config_available = True
except ImportError:
    _database_config_available = False


class DatabaseSettings:
    """資料庫設定管理"""

    def __init__(self):
        # 載入 .env 檔案
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        # TASK-34: 基本連線設定 - 使用統一配置系統，消除硬編碼默認值
        if _database_config_available:
            try:
                db_config = get_database_config()
                self.DATABASE_URL = db_config.get_url() if db_config.is_configured() else None
            except Exception as e:
                print(f"⚠️  數據庫配置載入失敗: {e}")
                self.DATABASE_URL = None
        else:
            # 向後兼容：直接從環境變數讀取，不提供不安全的硬編碼默認值
            self.DATABASE_URL = os.getenv("DATABASE_URL")
        
        # 如果沒有配置URL，拋出明確的錯誤
        if not self.DATABASE_URL:
            raise ValueError(
                "數據庫連接URL未配置。請設置 DATABASE_URL 環境變數。\n"
                "示例：DATABASE_URL=postgresql://user:password@host:5432/database"
            )

        # 連線池設定
        self.DB_POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
        self.DB_POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
        self.DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "10"))

        # 遷移開關
        self.USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() == "true"
        self.ENABLE_DUAL_WRITE = os.getenv("ENABLE_DUAL_WRITE", "false").lower() == "true"

        # 連線重試設定
        self.DB_MAX_RETRIES = int(os.getenv("DB_MAX_RETRIES", "3"))
        self.DB_RETRY_DELAY = float(os.getenv("DB_RETRY_DELAY", "1.0"))


class DatabaseConnection:
    """資料庫連線管理器

    修復後的實現：
    1. 正確的 Singleton 模式
    2. 實例變數避免記憶體洩漏
    3. 完善的資源清理機制
    4. 線程安全的實現
    """

    _instances = weakref.WeakValueDictionary()
    _lock = threading.Lock()

    def __new__(cls):
        # 線程安全的 Singleton 實現
        with cls._lock:
            if "main" not in cls._instances:
                instance = super().__new__(cls)
                cls._instances["main"] = instance
                instance._initialized = False
            return cls._instances["main"]

    def __init__(self):
        # 防止重複初始化
        if self._initialized:
            return

        # 實例變數（避免類變數記憶體洩漏）
        self._pool: Optional[asyncpg.Pool] = None
        self._settings = DatabaseSettings()
        self._logger = get_module_logger(self.__class__.__name__)
        self._cleanup_lock = asyncio.Lock() if hasattr(asyncio, "current_task") else None
        self._is_shutting_down = False

        self._initialized = True

    async def _ensure_cleanup_lock(self) -> asyncio.Lock:
        """延遲創建清理鎖"""
        if self._cleanup_lock is None:
            self._cleanup_lock = asyncio.Lock()
        return self._cleanup_lock

    @property
    def pool(self) -> Optional[asyncpg.Pool]:
        """獲取連線池"""
        return self._pool

    @property
    def is_connected(self) -> bool:
        """檢查是否已連線"""
        return self._pool is not None and not self._pool._closed and not self._is_shutting_down

    async def connect(self) -> Optional[asyncpg.Pool]:
        """建立資料庫連線池（線程安全版本）

        Returns:
            連線池物件，如果未啟用資料庫則返回 None
        """
        if not self._settings.USE_DATABASE:
            self._logger.info("資料庫功能未啟用")
            return None

        if self._is_shutting_down:
            self._logger.warning("連線管理器正在關閉，無法建立新連線")
            return None

        if self._pool and not self._pool._closed:
            self._logger.debug("資料庫連線池已存在")
            return self._pool

        cleanup_lock = await self._ensure_cleanup_lock()
        async with cleanup_lock:
            # 雙重檢查模式
            if self._pool and not self._pool._closed:
                return self._pool

            try:
                self._logger.info("正在建立資料庫連線池...")

                self._pool = await asyncpg.create_pool(
                    dsn=self._settings.DATABASE_URL,
                    min_size=self._settings.DB_POOL_MIN_SIZE,
                    max_size=self._settings.DB_POOL_MAX_SIZE,
                    server_settings={"application_name": "linker_app", "timezone": "UTC"},
                    command_timeout=self._settings.DB_POOL_TIMEOUT,
                    # 增加連線池健康檢查
                    max_inactive_connection_lifetime=300.0,  # 5分鐘
                )

                # 測試連線
                async with self._pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")

                self._logger.info(
                    f"資料庫連線池建立成功 "
                    f"(min: {self._settings.DB_POOL_MIN_SIZE}, "
                    f"max: {self._settings.DB_POOL_MAX_SIZE})"
                )

                return self._pool

            except Exception as e:
                # 分類異常並提供具體的錯誤訊息
                classified_error = classify_database_error(e)
                self._logger.error(f"建立資料庫連線池失敗: {classified_error}")
                await self._cleanup_failed_pool()
                raise classified_error from e

    async def disconnect(self) -> None:
        """安全關閉資料庫連線池"""
        cleanup_lock = await self._ensure_cleanup_lock()
        async with cleanup_lock:
            self._is_shutting_down = True

            if self._pool and not self._pool._closed:
                try:
                    # 等待所有活躍連線完成
                    await asyncio.wait_for(
                        self._pool.close(), timeout=self._settings.DB_POOL_TIMEOUT
                    )
                    self._logger.info("資料庫連線池已安全關閉")
                except asyncio.TimeoutError:
                    self._logger.warning("連線池關閉超時，強制終止")
                    await self._force_close_pool()
                except Exception as e:
                    self._logger.error(f"關閉資料庫連線池失敗: {e}")
                    await self._force_close_pool()
                finally:
                    self._pool = None

    async def _cleanup_failed_pool(self) -> None:
        """清理失敗的連線池（改進版本）"""
        if self._pool:
            try:
                # 嘗試優雅關閉
                await asyncio.wait_for(self._pool.close(), timeout=5.0)
                self._logger.debug("失敗的連線池已清理")
            except asyncio.TimeoutError:
                self._logger.warning("清理超時，強制終止連線池")
                await self._force_close_pool()
            except Exception as cleanup_error:
                self._logger.warning(f"清理失敗的連線池時發生錯誤: {cleanup_error}")
                await self._force_close_pool()
            finally:
                self._pool = None

    async def _force_close_pool(self) -> None:
        """強制關閉連線池"""
        if self._pool:
            try:
                # 強制終止所有連線
                await self._pool.terminate()
                self._logger.warning("連線池已強制終止")
            except Exception as e:
                self._logger.error(f"強制終止連線池失敗: {e}")
            finally:
                self._pool = None

    async def health_check(self) -> dict[str, Any]:
        """執行健康檢查（增強版本）

        Returns:
            健康檢查結果
        """
        if not self._settings.USE_DATABASE:
            return {"status": "disabled", "message": "資料庫功能未啟用"}

        if self._is_shutting_down:
            return {"status": "shutting_down", "message": "連線管理器正在關閉"}

        if not self.is_connected:
            return {"status": "disconnected", "message": "資料庫未連線"}

        try:
            # Python 3.9 兼容的超時實現
            async def _do_health_check():
                async with self._pool.acquire() as conn:
                    # 測試查詢
                    result = await conn.fetchval("SELECT 1")

                    # 獲取連線池狀態
                    pool_status = {
                        "size": self._pool.get_size(),
                        "min_size": self._pool._minsize,
                        "max_size": self._pool._maxsize,
                        "idle_connections": self._pool.get_idle_size(),
                    }

                    return {
                        "status": "healthy",
                        "message": "資料庫連線正常",
                        "pool_status": pool_status,
                        "test_query_result": result,
                    }

            return await asyncio.wait_for(
                _do_health_check(), timeout=self._settings.DB_POOL_TIMEOUT
            )

        except asyncio.TimeoutError:
            self._logger.error("資料庫健康檢查超時")
            return {"status": "timeout", "message": "資料庫連線超時"}
        except Exception as e:
            self._logger.error(f"資料庫健康檢查失敗: {e}")
            return {"status": "unhealthy", "message": f"資料庫連線異常: {str(e)}"}

    @asynccontextmanager
    async def get_connection(self) -> Any:
        """獲取資料庫連線的上下文管理器（增強版本）

        使用方式：
        async with db.get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
        """
        if self._is_shutting_down:
            raise RuntimeError("連線管理器正在關閉")

        if not self.is_connected:
            await self.connect()

        if not self._pool:
            raise RuntimeError("資料庫連線池未初始化")

        try:
            # 直接使用連線池的 acquire 方法
            async with self._pool.acquire() as conn:
                yield conn
        except asyncio.TimeoutError:
            self._logger.error("獲取資料庫連線超時")
            raise DatabaseTimeoutError("資料庫連線超時") from None
        except Exception as e:
            self._logger.error(f"資料庫操作失敗: {e}")
            raise

    async def execute_script(self, script_path: str) -> None:
        """執行 SQL 腳本檔案（增強版本）

        Args:
            script_path: SQL 腳本檔案路徑
        """
        if self._is_shutting_down:
            raise RuntimeError("連線管理器正在關閉")

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
        """異步上下文管理器支援"""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: Optional[Any], exc_val: Optional[Any], exc_tb: Optional[Any]
    ) -> None:
        """異步上下文管理器清理"""
        await self.disconnect()


# 線程安全的全域實例管理，使用弱引用避免記憶體洩漏
_db_connection_lock = threading.Lock()
_db_connection_ref: Optional[weakref.ReferenceType] = None


def get_database_connection() -> DatabaseConnection:
    """獲取資料庫連線管理器實例（線程安全版本，支援記憶體回收）"""
    global _db_connection_ref

    # 檢查現有弱引用是否仍然有效
    current_connection = _db_connection_ref() if _db_connection_ref else None

    if current_connection is None:
        with _db_connection_lock:
            # 雙重檢查模式
            current_connection = _db_connection_ref() if _db_connection_ref else None
            if current_connection is None:
                new_connection = DatabaseConnection()
                _db_connection_ref = weakref.ref(new_connection)
                return new_connection

    return current_connection


def clear_database_connection() -> None:
    """清理資料庫連線實例（測試和關閉時使用）"""
    global _db_connection_ref
    with _db_connection_lock:
        if _db_connection_ref:
            connection = _db_connection_ref()
            if connection:
                # 觸發清理，但讓 weakref 自然失效
                pass
            _db_connection_ref = None


async def get_db_pool() -> Optional[asyncpg.Pool]:
    """獲取資料庫連線池（向後兼容）"""
    db_conn = get_database_connection()
    if not db_conn.is_connected:
        await db_conn.connect()
    return db_conn.pool


async def initialize_database() -> bool:
    """初始化資料庫連線（改進版本）

    Returns:
        是否成功初始化
    """
    try:
        db_conn = get_database_connection()
        await db_conn.connect()

        # 執行健康檢查
        health = await db_conn.health_check()
        if health["status"] in ["healthy", "disabled"]:
            return True
        else:
            db_conn._logger.error(f"資料庫健康檢查失敗: {health}")
            return False

    except Exception as e:
        logger = get_module_logger("initialize_database")
        logger.error(f"初始化資料庫失敗: {e}")
        return False


async def cleanup_database() -> None:
    """清理資料庫連線（改進版本，使用弱引用）"""
    global _db_connection_ref

    # 取得當前連線實例
    current_connection = _db_connection_ref() if _db_connection_ref else None

    if current_connection:
        try:
            await current_connection.disconnect()
            logger = get_module_logger("cleanup_database")
            logger.info("資料庫連線清理成功")
        except Exception as e:
            logger = get_module_logger("cleanup_database")
            logger.error(f"清理資料庫連線失敗: {e}")

    # 清理弱引用
    clear_database_connection()


# 應用生命週期支援
async def startup_database() -> bool:
    """應用啟動時初始化資料庫"""
    success = await initialize_database()
    if success:
        logger = get_module_logger("startup_database")
        logger.info("資料庫連線初始化成功")
    return success


async def shutdown_database() -> None:
    """應用關閉時清理資料庫"""
    await cleanup_database()
    logger = get_module_logger("shutdown_database")
    logger.info("資料庫連線清理完成")
