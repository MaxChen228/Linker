"""
基礎 Repository 抽象層 - 第一階段準備
遵循 Repository Pattern，提供統一的資料存取介面
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Generic, Optional, TypeVar

import asyncpg

from core.log_config import get_module_logger

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """基礎 Repository 抽象類

    提供統一的資料存取介面，所有具體的 Repository 都應該繼承此類
    """

    def __init__(self, connection_pool: asyncpg.Pool):
        """初始化 Repository

        Args:
            connection_pool: 資料庫連線池
        """
        self.pool = connection_pool
        self.logger = get_module_logger(self.__class__.__name__)

    @asynccontextmanager
    async def transaction(self) -> Any:
        """事務管理器

        使用方式：
        async with repo.transaction() as conn:
            # 在這裡執行資料庫操作
            await conn.execute("...")
        """
        async with self.pool.acquire() as conn, conn.transaction():
            self.logger.debug("開始事務")
            try:
                yield conn
                self.logger.debug("事務提交成功")
            except Exception as e:
                self.logger.error(f"事務回滾: {e}")
                raise

    @asynccontextmanager
    async def connection(self) -> Any:
        """連線管理器

        用於不需要事務的查詢操作
        """
        async with self.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                self.logger.error(f"連線操作失敗: {e}")
                raise

    # 抽象方法 - 子類必須實作

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[T]:
        """根據 ID 查詢單個實體

        Args:
            id: 實體 ID

        Returns:
            找到的實體，如果不存在則返回 None
        """
        pass

    @abstractmethod
    async def find_all(self, **filters) -> list[T]:
        """查詢所有實體（支援過濾）

        Args:
            **filters: 過濾條件

        Returns:
            符合條件的實體列表
        """
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """創建新實體

        Args:
            entity: 要創建的實體

        Returns:
            創建後的實體（包含分配的 ID）
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新實體

        Args:
            entity: 要更新的實體

        Returns:
            更新後的實體
        """
        pass

    @abstractmethod
    async def delete(self, id: int) -> bool:
        """刪除實體

        Args:
            id: 要刪除的實體 ID

        Returns:
            是否成功刪除
        """
        pass

    # 通用輔助方法

    async def exists(self, id: int) -> bool:
        """檢查實體是否存在

        Args:
            id: 實體 ID

        Returns:
            是否存在
        """
        entity = await self.find_by_id(id)
        return entity is not None

    async def count(self, **filters) -> int:
        """統計實體數量

        Args:
            **filters: 過濾條件

        Returns:
            符合條件的實體數量
        """
        entities = await self.find_all(**filters)
        return len(entities)

    def _build_where_clause(self, filters: dict[str, Any]) -> tuple[str, list]:
        """構建 WHERE 子句

        Args:
            filters: 過濾條件字典

        Returns:
            (where_clause, parameters) 元組
        """
        if not filters:
            return "", []

        conditions = []
        parameters = []
        param_count = 1

        for key, value in filters.items():
            if value is None:
                conditions.append(f"{key} IS NULL")
            elif isinstance(value, list):
                # IN 查詢
                placeholders = ",".join([f"${param_count + i}" for i in range(len(value))])
                conditions.append(f"{key} IN ({placeholders})")
                parameters.extend(value)
                param_count += len(value)
            else:
                conditions.append(f"{key} = ${param_count}")
                parameters.append(value)
                param_count += 1

        where_clause = " AND ".join(conditions)
        return f"WHERE {where_clause}", parameters

    def _handle_database_error(self, error: Exception, operation: str) -> None:
        """處理資料庫錯誤

        Args:
            error: 資料庫錯誤
            operation: 執行的操作名稱
        """
        if isinstance(error, asyncpg.UniqueViolationError):
            self.logger.warning(f"{operation} 失敗 - 唯一性約束違反: {error}")
        elif isinstance(error, asyncpg.ForeignKeyViolationError):
            self.logger.warning(f"{operation} 失敗 - 外鍵約束違反: {error}")
        elif isinstance(error, asyncpg.ConnectionDoesNotExistError):
            self.logger.error(f"{operation} 失敗 - 資料庫連線不存在: {error}")
        else:
            self.logger.error(f"{operation} 失敗 - 未知錯誤: {error}")


class BaseCRUDRepository(BaseRepository[T]):
    """基礎 CRUD Repository

    提供標準的 CRUD 操作實作，減少子類的重複程式碼
    """

    def __init__(self, connection_pool: asyncpg.Pool, table_name: str):
        """初始化 CRUD Repository

        Args:
            connection_pool: 資料庫連線池
            table_name: 資料表名稱
        """
        super().__init__(connection_pool)
        self.table_name = table_name

    async def find_by_id(self, id: int) -> Optional[T]:
        """根據 ID 查詢實體"""
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"

        async with self.connection() as conn:
            try:
                row = await conn.fetchrow(query, id)
                if row:
                    return self._row_to_entity(row)
                return None
            except Exception as e:
                self._handle_database_error(e, f"find_by_id({id})")
                raise

    async def find_all(self, **filters) -> list[T]:
        """查詢所有實體"""
        base_query = f"SELECT * FROM {self.table_name}"
        where_clause, parameters = self._build_where_clause(filters)

        query = f"{base_query} {where_clause}" if where_clause else base_query

        async with self.connection() as conn:
            try:
                rows = await conn.fetch(query, *parameters)
                return [self._row_to_entity(row) for row in rows]
            except Exception as e:
                self._handle_database_error(e, f"find_all({filters})")
                raise

    async def delete(self, id: int) -> bool:
        """刪除實體"""
        query = f"DELETE FROM {self.table_name} WHERE id = $1"

        async with self.transaction() as conn:
            try:
                result = await conn.execute(query, id)
                deleted_count = int(result.split()[-1])
                return deleted_count > 0
            except Exception as e:
                self._handle_database_error(e, f"delete({id})")
                raise

    # 抽象方法 - 子類必須實作

    @abstractmethod
    def _row_to_entity(self, row: asyncpg.Record) -> T:
        """將資料庫記錄轉換為實體物件

        Args:
            row: 資料庫記錄

        Returns:
            實體物件
        """
        pass

    @abstractmethod
    def _entity_to_dict(self, entity: T) -> dict[str, Any]:
        """將實體物件轉換為字典

        Args:
            entity: 實體物件

        Returns:
            字典表示
        """
        pass


class DatabaseHealthCheck:
    """資料庫健康檢查工具"""

    def __init__(self, connection_pool: asyncpg.Pool):
        self.pool = connection_pool
        self.logger = get_module_logger(self.__class__.__name__)

    async def check_connection(self) -> bool:
        """檢查資料庫連線"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"資料庫連線檢查失敗: {e}")
            return False

    async def check_tables_exist(self, required_tables: list[str]) -> dict[str, bool]:
        """檢查必要的資料表是否存在"""
        results = {}

        try:
            async with self.pool.acquire() as conn:
                for table in required_tables:
                    query = """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_name = $1
                        )
                    """
                    exists = await conn.fetchval(query, table)
                    results[table] = exists
        except Exception as e:
            self.logger.error(f"檢查資料表失敗: {e}")
            for table in required_tables:
                results[table] = False

        return results

    async def get_pool_status(self) -> dict[str, Any]:
        """獲取連線池狀態"""
        return {
            "size": self.pool.get_size(),
            "min_size": self.pool._minsize,
            "max_size": self.pool._maxsize,
            "free_connections": len(self.pool._queue._queue) if hasattr(self.pool, "_queue") else 0,
        }
