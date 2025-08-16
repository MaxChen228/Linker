"""
基礎異步服務類 (TASK-31)

此模組定義了所有異步服務的抽象基礎類別 `BaseAsyncService`。
它為應用程式中的所有服務提供了一個統一的生命週期管理介面，
包括初始化、資源清理和健康檢查。

設計目標：
- **統一介面**：確保所有服務都有 `initialize`, `cleanup`, `health_check` 等標準方法。
- **生命週期管理**：由服務註冊中心 (`ServiceRegistry`) 調用，管理服務的啟動和關閉。
- **可擴充性**：子類別只需實現 `_initialize_resources` 和 `_cleanup_resources` 方法，
  即可專注於自身的業務邏輯，而無需關心通用的生命週期管理。
"""

from abc import ABC, abstractmethod
from typing import Any

from core.log_config import get_module_logger


class BaseAsyncService(ABC):
    """
    異步服務的抽象基礎類別。

    所有具體的服務都應繼承此類，以確保它們能被服務註冊中心正確管理。
    """

    def __init__(self, service_name: str):
        """
        初始化基礎服務。

        Args:
            service_name: 服務的唯一名稱，主要用於日誌記錄和監控。
        """
        self.service_name = service_name
        self.logger = get_module_logger(f"services.{service_name}")
        self._initialized = False

    async def initialize(self) -> None:
        """公共方法，用於初始化服務。防止重複初始化。"""
        if self._initialized:
            return
        self.logger.info(f"正在初始化服務: {self.service_name}...")
        await self._initialize_resources()
        self._initialized = True
        self.logger.info(f"服務 {self.service_name} 初始化成功。")

    @abstractmethod
    async def _initialize_resources(self) -> None:
        """抽象方法，子類別必須實現此方法來初始化其特定資源（如資料庫連線、API 客戶端等）。"""
        pass

    async def cleanup(self) -> None:
        """公共方法，用於清理服務資源。防止在未初始化時進行清理。"""
        if not self._initialized:
            return
        self.logger.info(f"正在清理服務: {self.service_name}...")
        await self._cleanup_resources()
        self._initialized = False
        self.logger.info(f"服務 {self.service_name} 清理完成。")

    @abstractmethod
    async def _cleanup_resources(self) -> None:
        """抽象方法，子類別必須實現此方法來釋放其佔用的資源。"""
        pass

    async def health_check(self) -> dict[str, Any]:
        """
        執行服務的健康檢查。

        Returns:
            一個包含服務名稱和初始化狀態的字典。
        """
        return {
            "service": self.service_name,
            "status": "healthy" if self._initialized else "uninitialized",
            "initialized": self._initialized,
        }
