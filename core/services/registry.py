"""
服務註冊中心 - TASK-31
管理所有異步服務的生命週期和依賴注入
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Optional

from core.log_config import get_module_logger
from core.services.base import BaseAsyncService


class ServiceRegistry:
    """服務註冊中心

    管理所有異步服務的註冊、初始化和清理
    支援依賴注入和生命週期管理
    """

    def __init__(self):
        """初始化註冊中心"""
        self.logger = get_module_logger("services.registry")
        self._services: dict[str, BaseAsyncService] = {}
        self._service_classes: dict[str, type[BaseAsyncService]] = {}
        self._initialized = False
        self._lock = asyncio.Lock()

    def register_class(self, name: str, service_class: type[BaseAsyncService]) -> None:
        """註冊服務類

        Args:
            name: 服務名稱
            service_class: 服務類
        """
        if name in self._service_classes:
            self.logger.warning(f"服務類 {name} 已註冊，將被覆蓋")

        self._service_classes[name] = service_class
        self.logger.info(f"註冊服務類: {name}")

    async def get_service(self, name: str) -> Optional[BaseAsyncService]:
        """獲取服務實例

        Args:
            name: 服務名稱

        Returns:
            服務實例，如果不存在則返回 None
        """
        async with self._lock:
            # 如果服務已經實例化，直接返回
            if name in self._services:
                return self._services[name]

            # 如果服務類已註冊，創建實例
            if name in self._service_classes:
                service_class = self._service_classes[name]
                service = service_class()
                await service.initialize()
                self._services[name] = service
                self.logger.info(f"創建並初始化服務: {name}")
                return service

            self.logger.error(f"服務 {name} 未註冊")
            return None

    async def initialize_all(self) -> None:
        """初始化所有已註冊的服務"""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            self.logger.info("開始初始化所有服務")

            for name, service_class in self._service_classes.items():
                if name not in self._services:
                    service = service_class()
                    await service.initialize()
                    self._services[name] = service
                    self.logger.info(f"初始化服務: {name}")

            self._initialized = True
            self.logger.info("所有服務初始化完成")

    async def cleanup_all(self) -> None:
        """清理所有服務"""
        async with self._lock:
            self.logger.info("開始清理所有服務")

            for name, service in list(self._services.items()):
                try:
                    await service.cleanup()
                    self.logger.info(f"清理服務: {name}")
                except Exception as e:
                    self.logger.error(f"清理服務 {name} 時發生錯誤: {e}")
                finally:
                    del self._services[name]

            self._initialized = False
            self.logger.info("所有服務清理完成")

    async def health_check(self) -> dict[str, Any]:
        """執行健康檢查

        Returns:
            所有服務的健康狀態
        """
        results = {
            "registry": {
                "initialized": self._initialized,
                "registered_classes": list(self._service_classes.keys()),
                "active_services": list(self._services.keys()),
            },
            "services": {}
        }

        for name, service in self._services.items():
            try:
                results["services"][name] = await service.health_check()
            except Exception as e:
                results["services"][name] = {
                    "status": "error",
                    "error": str(e)
                }

        return results

    @asynccontextmanager
    async def service_scope(self, *service_names: str):
        """服務作用域上下文管理器

        在上下文中自動初始化和清理指定的服務

        Args:
            *service_names: 需要的服務名稱

        Yields:
            包含服務實例的字典
        """
        services = {}

        try:
            # 獲取並初始化服務
            for name in service_names:
                service = await self.get_service(name)
                if service:
                    services[name] = service
                else:
                    raise ValueError(f"服務 {name} 不可用")

            yield services

        finally:
            # 這裡不需要清理，因為服務由註冊中心管理
            pass


# 全局註冊中心實例
_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """獲取全局服務註冊中心

    Returns:
        服務註冊中心實例
    """
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()

        # 註冊默認服務
        from core.services.async_knowledge_service import AsyncKnowledgeService
        _registry.register_class("knowledge", AsyncKnowledgeService)

    return _registry


async def initialize_services() -> None:
    """初始化所有服務（應用啟動時調用）"""
    registry = get_service_registry()
    await registry.initialize_all()


async def cleanup_services() -> None:
    """清理所有服務（應用關閉時調用）"""
    registry = get_service_registry()
    await registry.cleanup_all()
