"""
統一端口配置管理系統
TASK-34: 消除端口號硬編碼

提供集中化的端口配置，從環境變量讀取並提供默認值
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PortConfig:
    """端口配置類 - 所有端口配置的單一真相源"""

    # 應用程序端口
    APP_PORT: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    APP_HOST: str = field(default_factory=lambda: os.getenv("HOST", "127.0.0.1"))

    # 數據庫端口
    DB_PORT: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    DB_HOST: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))

    # 開發環境端口列表（用於環境檢測）
    DEV_PORTS: tuple = field(
        default_factory=lambda: ("8000", "8001", "3000", "5000", "5173", "3001")
    )

    # 測試環境端口
    TEST_PORT: int = field(default_factory=lambda: int(os.getenv("TEST_PORT", "8001")))

    @property
    def app_url(self) -> str:
        """獲取應用完整URL"""
        protocol = "https" if os.getenv("USE_HTTPS", "false").lower() == "true" else "http"
        if self.APP_PORT in (80, 443):
            return f"{protocol}://{self.APP_HOST}"
        return f"{protocol}://{self.APP_HOST}:{self.APP_PORT}"

    @property
    def database_url(self) -> str:
        """獲取數據庫連接URL（如果未設置DATABASE_URL）"""
        if db_url := os.getenv("DATABASE_URL"):
            return db_url

        # 構建默認數據庫URL
        db_user = os.getenv("DB_USER", "postgres")
        db_pass = os.getenv("DB_PASSWORD", "password")
        db_name = os.getenv("DB_NAME", "linker")

        return f"postgresql://{db_user}:{db_pass}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"

    def to_dict(self) -> dict:
        """轉換為字典格式（用於API響應）"""
        return {
            "app_port": self.APP_PORT,
            "app_host": self.APP_HOST,
            "app_url": self.app_url,
            "dev_ports": list(self.DEV_PORTS),
            "is_production": os.getenv("ENVIRONMENT", "development") == "production",
        }

    @classmethod
    def from_env(cls) -> "PortConfig":
        """從環境變量創建配置實例"""
        return cls()

    def validate(self) -> bool:
        """驗證端口配置是否有效"""
        # 檢查端口範圍
        if not (1 <= self.APP_PORT <= 65535):
            raise ValueError(f"Invalid APP_PORT: {self.APP_PORT}")

        if not (1 <= self.DB_PORT <= 65535):
            raise ValueError(f"Invalid DB_PORT: {self.DB_PORT}")

        # 檢查HOST格式（基本驗證）
        if not self.APP_HOST:
            raise ValueError("APP_HOST cannot be empty")

        return True


# 創建全局配置實例
_port_config: Optional[PortConfig] = None


def get_port_config() -> PortConfig:
    """獲取端口配置單例"""
    global _port_config
    if _port_config is None:
        _port_config = PortConfig.from_env()
        _port_config.validate()
    return _port_config


def reset_port_config() -> None:
    """重置端口配置（主要用於測試）"""
    global _port_config
    _port_config = None


# 便捷訪問函數
def get_app_port() -> int:
    """獲取應用端口"""
    return get_port_config().APP_PORT


def get_app_host() -> str:
    """獲取應用主機"""
    return get_port_config().APP_HOST


def get_db_port() -> int:
    """獲取數據庫端口"""
    return get_port_config().DB_PORT


def get_app_url() -> str:
    """獲取應用完整URL"""
    return get_port_config().app_url


# 導出配置
__all__ = [
    "PortConfig",
    "get_port_config",
    "reset_port_config",
    "get_app_port",
    "get_app_host",
    "get_db_port",
    "get_app_url",
]
