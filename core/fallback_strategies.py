"""
降級策略模組
提供各種錯誤情況下的降級處理策略

包含功能：
1. 快取降級策略
2. 網路錯誤降級策略
3. 並發錯誤降級策略
4. 降級管理器
5. 降級結果驗證

注意：DatabaseToJsonFallback 已在 TASK-30B 中移除（純資料庫架構）
"""

from typing import Any, Optional, Callable, Dict
import asyncio
from datetime import datetime, timedelta

from core.exceptions import ErrorCategory, ErrorSeverity, UnifiedError
from core.log_config import get_module_logger


class FallbackStrategy:
    """降級策略基類"""

    def __init__(self):
        self.logger = get_module_logger(self.__class__.__name__)

    def can_handle(self, error_category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """判斷是否可以處理此錯誤"""
        raise NotImplementedError

    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """執行降級策略"""
        raise NotImplementedError

    def get_strategy_name(self) -> str:
        """獲取策略名稱"""
        return self.__class__.__name__


# TASK-30B: DatabaseToJsonFallback removed - pure database architecture
# No longer fallback to JSON mode since JSON backend is completely removed


class CacheFallback(FallbackStrategy):
    """快取降級策略"""

    def __init__(self):
        super().__init__()
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._default_ttl = timedelta(minutes=5)  # 快取過期時間

    def can_handle(self, error_category: ErrorCategory, severity: ErrorSeverity) -> bool:
        return error_category in [
            ErrorCategory.DATABASE,
            ErrorCategory.NETWORK,
            ErrorCategory.CONCURRENCY,
            ErrorCategory.SYSTEM,
        ]

    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """使用快取數據執行"""
        try:
            # 生成快取鍵
            cache_key = self._generate_cache_key(original_func, args, kwargs)

            # 檢查快取是否存在且未過期
            if self._is_cache_valid(cache_key):
                cached_result = self._cache[cache_key]
                self.logger.info(f"快取降級成功: {original_func.__name__}")

                # 如果是字典，添加快取命中標記
                if isinstance(cached_result, dict):
                    result = cached_result.copy()
                    result["_cache_hit"] = True
                    result["_fallback"] = True
                    result["_fallback_strategy"] = self.get_strategy_name()
                    return result

                return cached_result

            # 快取未命中或已過期，返回安全默認值
            return self._get_safe_default(original_func.__name__)

        except Exception as e:
            self.logger.error(f"快取降級失敗: {e}")
            return self._get_safe_default(original_func.__name__)

    def update_cache(self, func: Callable, args: tuple, kwargs: dict, result: Any) -> None:
        """更新快取"""
        try:
            cache_key = self._generate_cache_key(func, args, kwargs)
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()

            # 清理過期快取
            self._cleanup_expired_cache()

        except Exception as e:
            self.logger.warning(f"快取更新失敗: {e}")

    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """生成快取鍵"""
        try:
            # 簡化的快取鍵生成策略
            func_name = func.__name__

            # 只使用部分參數作為鍵，避免過於複雜
            key_parts = [func_name]

            # 添加實例類型信息
            if args:
                instance_type = type(args[0]).__name__
                key_parts.append(instance_type)

            # 添加重要的關鍵字參數
            important_kwargs = ["limit", "offset", "category", "search_term"]
            for key in important_kwargs:
                if key in kwargs:
                    key_parts.append(f"{key}={kwargs[key]}")

            return ":".join(key_parts)

        except Exception:
            # 如果生成鍵失敗，使用函數名作為鍵
            return func.__name__

    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查快取是否有效"""
        if cache_key not in self._cache:
            return False

        if cache_key not in self._cache_timestamps:
            return False

        cache_time = self._cache_timestamps[cache_key]
        return datetime.now() - cache_time < self._default_ttl

    def _cleanup_expired_cache(self) -> None:
        """清理過期快取"""
        try:
            current_time = datetime.now()
            expired_keys = [
                key
                for key, timestamp in self._cache_timestamps.items()
                if current_time - timestamp > self._default_ttl
            ]

            for key in expired_keys:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)

            if expired_keys:
                self.logger.debug(f"清理了 {len(expired_keys)} 個過期快取項目")

        except Exception as e:
            self.logger.warning(f"快取清理失敗: {e}")

    def _get_safe_default(self, method_name: str) -> Any:
        """安全的默認返回值"""
        if "statistics" in method_name or "stats" in method_name:
            return {
                "total_practices": 0,
                "correct_count": 0,
                "knowledge_points": 0,
                "avg_mastery": 0.0,
                "category_distribution": {},
                "due_reviews": 0,
                "_cache_miss": True,
                "_fallback": True,
                "_fallback_strategy": self.get_strategy_name(),
            }
        elif any(keyword in method_name for keyword in ["points", "candidates", "search"]):
            return []
        elif "get_knowledge_point" == method_name.replace("async_", "").replace("_async", ""):
            return None
        elif any(keyword in method_name for keyword in ["add", "edit", "delete", "restore"]):
            return False
        else:
            return None


class NetworkRetryFallback(FallbackStrategy):
    """網路錯誤重試降級策略"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def can_handle(self, error_category: ErrorCategory, severity: ErrorSeverity) -> bool:
        return error_category == ErrorCategory.NETWORK

    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """網路錯誤重試策略"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"網路操作重試 {attempt + 1}/{self.max_retries}: {original_func.__name__}"
                )

                if asyncio.iscoroutinefunction(original_func):
                    # 異步函數需要特殊處理
                    return self._execute_async_retry(original_func, args, kwargs, attempt)
                else:
                    return original_func(*args, **kwargs)

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    import time

                    retry_delay = self.retry_delay * (2**attempt)  # 指數退避
                    self.logger.warning(f"網路操作失敗，{retry_delay}秒後重試: {e}")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"網路操作重試 {self.max_retries} 次後仍失敗: {e}")

        # 所有重試都失敗，返回默認值
        return self._get_network_default(original_func.__name__)

    def _execute_async_retry(self, func: Callable, args: tuple, kwargs: dict, attempt: int) -> Any:
        """執行異步重試"""
        # 這個方法本身不是異步的，所以需要特殊處理
        # 在實際使用中，這需要在異步上下文中調用
        self.logger.warning("異步重試需要在異步上下文中處理")
        return self._get_network_default(func.__name__)

    def _get_network_default(self, method_name: str) -> Any:
        """獲取網路錯誤的默認值"""
        return {
            "_network_error": True,
            "_fallback": True,
            "_fallback_strategy": self.get_strategy_name(),
            "message": "網路連接異常，請稍後重試",
        }


class GracefulDegradationFallback(FallbackStrategy):
    """優雅降級策略 - 提供基本功能"""

    def can_handle(self, error_category: ErrorCategory, severity: ErrorSeverity) -> bool:
        # 這是最後的降級策略，可以處理所有錯誤
        return True

    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """優雅降級執行"""
        try:
            method_name = original_func.__name__

            # 根據方法類型提供基本功能
            if "statistics" in method_name or "stats" in method_name:
                return self._get_minimal_statistics()
            elif any(keyword in method_name for keyword in ["points", "candidates", "search"]):
                return []
            elif method_name in ["get_knowledge_point"]:
                return None
            elif any(keyword in method_name for keyword in ["add", "edit", "delete", "restore"]):
                return False
            else:
                return None

        except Exception as e:
            self.logger.error(f"優雅降級執行失敗: {e}")
            return None

    def _get_minimal_statistics(self) -> dict:
        """獲取最小統計信息"""
        return {
            "total_practices": 0,
            "correct_count": 0,
            "knowledge_points": 0,
            "avg_mastery": 0.0,
            "category_distribution": {},
            "due_reviews": 0,
            "_graceful_degradation": True,
            "_fallback": True,
            "_fallback_strategy": self.get_strategy_name(),
            "message": "系統正在降級模式運行，功能受限",
        }


class FallbackManager:
    """降級管理器"""

    def __init__(self):
        self.strategies = [
            # DatabaseToJsonFallback removed - pure database architecture
            CacheFallback(),
            NetworkRetryFallback(),
            GracefulDegradationFallback(),  # 最後的降級策略
        ]
        self.logger = get_module_logger(self.__class__.__name__)
        self._fallback_stats = {"total_fallbacks": 0, "strategy_usage": {}, "success_rate": {}}

    def execute_fallback(
        self,
        error_category: ErrorCategory,
        severity: ErrorSeverity,
        original_func: Callable,
        *args,
        **kwargs,
    ) -> Optional[Any]:
        """執行適當的降級策略"""
        self._fallback_stats["total_fallbacks"] += 1

        for strategy in self.strategies:
            if strategy.can_handle(error_category, severity):
                strategy_name = strategy.get_strategy_name()

                try:
                    result = strategy.execute(original_func, *args, **kwargs)

                    # 更新統計信息
                    self._update_strategy_stats(strategy_name, success=True)

                    self.logger.info(f"降級策略成功: {strategy_name} for {original_func.__name__}")
                    return result

                except Exception as e:
                    self._update_strategy_stats(strategy_name, success=False)
                    self.logger.warning(f"降級策略失敗 {strategy_name}: {e}")
                    continue

        self.logger.error(f"所有降級策略都失敗，錯誤類別: {error_category}")
        return None

    def _update_strategy_stats(self, strategy_name: str, success: bool) -> None:
        """更新策略統計信息"""
        if strategy_name not in self._fallback_stats["strategy_usage"]:
            self._fallback_stats["strategy_usage"][strategy_name] = 0
            self._fallback_stats["success_rate"][strategy_name] = {"success": 0, "total": 0}

        self._fallback_stats["strategy_usage"][strategy_name] += 1
        self._fallback_stats["success_rate"][strategy_name]["total"] += 1

        if success:
            self._fallback_stats["success_rate"][strategy_name]["success"] += 1

    def get_fallback_statistics(self) -> dict:
        """獲取降級統計信息"""
        stats = self._fallback_stats.copy()

        # 計算成功率
        for strategy_name in stats["success_rate"]:
            success_data = stats["success_rate"][strategy_name]
            if success_data["total"] > 0:
                success_rate = success_data["success"] / success_data["total"]
                success_data["rate"] = round(success_rate * 100, 2)
            else:
                success_data["rate"] = 0.0

        return stats

    def add_strategy(self, strategy: FallbackStrategy, priority: int = None) -> None:
        """添加新的降級策略"""
        if priority is None:
            # 添加到優雅降級策略之前
            self.strategies.insert(-1, strategy)
        else:
            self.strategies.insert(priority, strategy)

        self.logger.info(f"添加降級策略: {strategy.get_strategy_name()}")

    def remove_strategy(self, strategy_class: type) -> bool:
        """移除特定類型的降級策略"""
        for i, strategy in enumerate(self.strategies):
            if isinstance(strategy, strategy_class):
                removed_strategy = self.strategies.pop(i)
                self.logger.info(f"移除降級策略: {removed_strategy.get_strategy_name()}")
                return True
        return False

    def clear_cache(self) -> None:
        """清理所有快取"""
        for strategy in self.strategies:
            if isinstance(strategy, CacheFallback):
                strategy._cache.clear()
                strategy._cache_timestamps.clear()
                self.logger.info("快取已清理")
                break


# 全局降級管理器實例
fallback_manager = FallbackManager()


def get_fallback_manager() -> FallbackManager:
    """獲取全局降級管理器實例"""
    return fallback_manager
