"""
資料庫相關異常類別定義
提供分類明確的異常處理機制
"""


class DatabaseError(Exception):
    """資料庫操作基礎異常"""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class DatabaseConnectionError(DatabaseError):
    """資料庫連線相關異常"""

    pass


class DatabaseNotFoundError(DatabaseConnectionError):
    """資料庫不存在異常"""

    pass


class DatabaseAuthError(DatabaseConnectionError):
    """資料庫認證失敗異常"""

    pass


class DatabaseTimeoutError(DatabaseConnectionError):
    """資料庫連線超時異常"""

    pass


class DatabaseConstraintError(DatabaseError):
    """資料庫約束違反異常"""

    pass


class DatabaseUniqueViolationError(DatabaseConstraintError):
    """唯一性約束違反異常"""

    pass


class DatabaseForeignKeyViolationError(DatabaseConstraintError):
    """外鍵約束違反異常"""

    pass


class DatabaseMigrationError(DatabaseError):
    """資料庫遷移相關異常"""

    pass


class DatabaseInitializationError(DatabaseError):
    """資料庫初始化異常"""

    pass


def classify_database_error(error: Exception) -> DatabaseError:
    """
    將 asyncpg 異常分類為自定義異常

    Args:
        error: 原始異常

    Returns:
        分類後的自定義異常
    """
    import asyncpg

    error_message = str(error)

    if isinstance(error, asyncpg.InvalidCatalogNameError):
        return DatabaseNotFoundError("目標資料庫不存在", error)
    elif isinstance(error, asyncpg.InvalidPasswordError):
        return DatabaseAuthError("資料庫認證失敗", error)
    elif isinstance(error, asyncpg.ConnectionDoesNotExistError):
        return DatabaseConnectionError("無法建立資料庫連線", error)
    elif isinstance(error, asyncpg.ConnectionFailureError):
        return DatabaseConnectionError("資料庫連線失敗", error)
    elif isinstance(error, asyncpg.UniqueViolationError):
        return DatabaseUniqueViolationError("唯一性約束違反", error)
    elif isinstance(error, asyncpg.ForeignKeyViolationError):
        return DatabaseForeignKeyViolationError("外鍵約束違反", error)
    elif isinstance(error, asyncpg.PostgresError):
        return DatabaseError(f"PostgreSQL 錯誤: {error_message}", error)
    else:
        return DatabaseError(f"未知資料庫錯誤: {error_message}", error)
