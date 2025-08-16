"""
基礎異步服務類 - TASK-31
定義所有服務的共同介面和行為
"""

from abc import ABC, abstractmethod
from typing import Any

from core.log_config import get_module_logger


class BaseAsyncService(ABC):
    """異步服務基類

    所有服務都應繼承此類，確保統一的介面和錯誤處理
    """

    def __init__(self, service_name: str):
        """初始化服務

        Args:
            service_name: 服務名稱，用於日誌和監控
        """
        self.service_name = service_name
        self.logger = get_module_logger(f"services.{service_name}")
        self._initialized = False

    async def initialize(self) -> None:
        """初始化服務資源"""
        if self._initialized:
            return

        self.logger.info(f"初始化服務: {self.service_name}")
        await self._initialize_resources()
        self._initialized = True

    @abstractmethod
    async def _initialize_resources(self) -> None:
        """初始化服務特定資源（子類實現）"""
        pass

    async def cleanup(self) -> None:
        """清理服務資源"""
        if not self._initialized:
            return

        self.logger.info(f"清理服務: {self.service_name}")
        await self._cleanup_resources()
        self._initialized = False

    @abstractmethod
    async def _cleanup_resources(self) -> None:
        """清理服務特定資源（子類實現）"""
        pass

    async def health_check(self) -> dict[str, Any]:
        """健康檢查

        Returns:
            包含服務狀態的字典
        """
        return {
            "service": self.service_name,
            "status": "healthy" if self._initialized else "not_initialized",
            "initialized": self._initialized,
        }
