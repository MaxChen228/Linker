"""
降級策略模組

提供在系統主要功能（如資料庫、網路請求）失敗時的備用處理方案，
以增強系統的穩定性和使用者體驗。

主要功能：
- 定義了多種降級策略，如快取降級、網路重試、優雅降級等。
- `FallbackManager` 統一管理和執行這些策略。
- 策略可以根據錯誤的類別和嚴重性被觸發。

注意：隨著架構演進，原有的 `DatabaseToJsonFallback` 已被移除，
因為系統現在是純資料庫架構。
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from core.exceptions import ErrorCategory, ErrorSeverity
from core.log_config import get_module_logger


class FallbackStrategy:
    """所有降級策略的抽象基礎類別。"""

    def __init__(self):
        self.logger = get_module_logger(self.__class__.__name__)

    def can_handle(self, error_category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """判斷此策略是否能處理特定類別和嚴重性的錯誤。"""
        raise NotImplementedError

    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """執行降級邏輯。"""
        raise NotImplementedError

    def get_strategy_name(self) -> str:
        """返回策略的名稱。"""
        return self.__class__.__name__


class CacheFallback(FallbackStrategy):
    """
    快取降級策略。

    當主要資料來源（如資料庫）不可用時，嘗試從記憶體快取中返回舊的、
    可能稍微過時的資料，以維持系統的基本可用性。
    """

    def __init__(self):
        super().__init__()
        self._cache: dict[str, Any] = {}
        self._cache_timestamps: dict[str, datetime] = {}
        self._default_ttl = timedelta(minutes=5)

    def can_handle(self, error_category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """此策略可以處理資料庫、網路、並發和系統錯誤。"""
        return error_category in [
            ErrorCategory.DATABASE,
            ErrorCategory.NETWORK,
            ErrorCategory.CONCURRENCY,
            ErrorCategory.SYSTEM,
        ]

    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """嘗試從快取中獲取資料，如果快取無效則返回安全的預設值。"""
        try:
            cache_key = self._generate_cache_key(original_func, args, kwargs)
            if self._is_cache_valid(cache_key):
                cached_result = self._cache[cache_key]
                self.logger.info(f"成功執行快取降級 for {original_func.__name__}")
                if isinstance(cached_result, dict):
                    return {**cached_result, "_fallback_strategy": self.get_strategy_name()}
                return cached_result
            return self._get_safe_default(original_func.__name__)
        except Exception as e:
            self.logger.error(f"快取降級執行失敗: {e}")
            return self._get_safe_default(original_func.__name__)

    def update_cache(self, func: Callable, args: tuple, kwargs: dict, result: Any) -> None:
        """在正常操作成功後，更新快取內容。"""
        try:
            cache_key = self._generate_cache_key(func, args, kwargs)
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()
            self._cleanup_expired_cache()
        except Exception as e:
            self.logger.warning(f"更新快取失敗: {e}")

    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """根據函數和參數生成一個唯一的快取鍵。"""
        # 簡化鍵的生成，只包含關鍵資訊以提高命中率
        key_parts = [func.__name__]
        if args:
            key_parts.append(type(args[0]).__name__)
        key_parts.extend(f"{k}={v}" for k, v in kwargs.items() if k in ["limit", "category"])
        return ":".join(key_parts)

    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查快取是否存在且未過期。"""
        if cache_key not in self._cache or cache_key not in self._cache_timestamps:
            return False
        return datetime.now() - self._cache_timestamps[cache_key] < self._default_ttl

    def _cleanup_expired_cache(self) -> None:
        """清理所有已過期的快取條目以釋放記憶體。"""
        expired_keys = [k for k, ts in self._cache_timestamps.items() if datetime.now() - ts > self._default_ttl]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        if expired_keys:
            self.logger.debug(f"已清理 {len(expired_keys)} 個過期快取項目。")

    def _get_safe_default(self, method_name: str) -> Any:
        """根據方法名稱提供一個安全的預設回傳值。"""
        defaults = {
            "statistics": {"total_practices": 0, "correct_count": 0, "knowledge_points": 0, "avg_mastery": 0.0, "due_reviews": 0},
            "points": [],
            "candidates": [],
            "search": [],
            "get_knowledge_point": None,
            "add": False, "edit": False, "delete": False, "restore": False,
        }
        key = next((k for k in defaults if k in method_name), None)
        if key:
            default_value = defaults[key]
            if isinstance(default_value, dict):
                return {**default_value, "_fallback_strategy": self.get_strategy_name(), "_cache_miss": True}
            return default_value
        return None


class NetworkRetryFallback(FallbackStrategy):
    """
    網路錯誤重試降級策略。

    當發生網路相關錯誤時，自動進行重試，並採用指數退避策略避免對服務造成過大壓力。
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        super().__init__()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def can_handle(self, error_category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """此策略專門處理網路錯誤。"""
        return error_category == ErrorCategory.NETWORK

    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """執行網路重試邏輯。"""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"網路操作重試 {attempt + 1}/{self.max_retries}: {original_func.__name__}")
                if asyncio.iscoroutinefunction(original_func):
                    # 實際應用中，應由異步錯誤處理器調用異步重試邏輯
                    self.logger.warning("異步重試應在異步上下文中處理。")
                    break
                return original_func(*args, **kwargs)
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"網路操作失敗，將在 {delay:.2f} 秒後重試: {e}")
                    time.sleep(delay)
                else:
                    self.logger.error(f"網路操作在 {self.max_retries} 次重試後仍然失敗: {e}")
        return self._get_network_default(original_func.__name__)

    def _get_network_default(self, method_name: str) -> Any:
        """返回一個表示網路錯誤的標準化回應。"""
        return {"_fallback_strategy": self.get_strategy_name(), "_network_error": True, "message": "網路連線異常，請稍後重試。"}


class GracefulDegradationFallback(FallbackStrategy):
    """
    優雅降級策略。

    作為最後一道防線，當其他策略都失敗時，提供最基本但安全的預設回應，
    確保應用程式不會完全崩潰。
    """

    def can_handle(self, error_category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """此策略可以處理任何類型的錯誤，作為最終的降級手段。"""
        return True

    def execute(self, original_func: Callable, *args, **kwargs) -> Any:
        """根據方法名稱返回一個安全的、最小化的預設值。"""
        method_name = original_func.__name__
        if "statistics" in method_name or "stats" in method_name:
            return self._get_minimal_statistics()
        elif any(keyword in method_name for keyword in ["points", "candidates", "search"]):
            return []
        elif "get_knowledge_point" in method_name:
            return None
        elif any(keyword in method_name for keyword in ["add", "edit", "delete", "restore"]):
            return False
        return None

    def _get_minimal_statistics(self) -> dict:
        """返回一個最小化的統計數據結構。"""
        return {
            "total_practices": 0, "correct_count": 0, "knowledge_points": 0, "avg_mastery": 0.0, "due_reviews": 0,
            "_fallback_strategy": self.get_strategy_name(), "_graceful_degradation": True, "message": "系統功能受限，正在降級模式運行。"
        }


class FallbackManager:
    """
    降級管理器，負責協調和執行所有已註冊的降級策略。
    """

    def __init__(self):
        self.strategies = [CacheFallback(), NetworkRetryFallback(), GracefulDegradationFallback()]
        self.logger = get_module_logger(self.__class__.__name__)
        self._fallback_stats = {"total_fallbacks": 0, "strategy_usage": {}, "success_rate": {}}

    def execute_fallback(
        self, error_category: ErrorCategory, severity: ErrorSeverity, original_func: Callable, *args, **kwargs
    ) -> Optional[Any]:
        """根據錯誤類型，依序嘗試執行合適的降級策略。"""
        self._fallback_stats["total_fallbacks"] += 1
        for strategy in self.strategies:
            if strategy.can_handle(error_category, severity):
                strategy_name = strategy.get_strategy_name()
                try:
                    result = strategy.execute(original_func, *args, **kwargs)
                    self._update_strategy_stats(strategy_name, success=True)
                    self.logger.info(f"降級策略 '{strategy_name}' 成功執行 for {original_func.__name__}")
                    return result
                except Exception as e:
                    self._update_strategy_stats(strategy_name, success=False)
                    self.logger.warning(f"降級策略 '{strategy_name}' 執行失敗: {e}")
                    continue
        self.logger.error(f"所有降級策略均失敗 for error category: {error_category.value}")
        return None

    def _update_strategy_stats(self, strategy_name: str, success: bool) -> None:
        """更新降級策略的執行統計。"""
        usage = self._fallback_stats["strategy_usage"]
        rate = self._fallback_stats["success_rate"]
        usage[strategy_name] = usage.get(strategy_name, 0) + 1
        if strategy_name not in rate:
            rate[strategy_name] = {"success": 0, "total": 0}
        rate[strategy_name]["total"] += 1
        if success:
            rate[strategy_name]["success"] += 1

    def get_fallback_statistics(self) -> dict:
        """獲取降級操作的詳細統計數據。"""
        stats = self._fallback_stats.copy()
        for name, data in stats["success_rate"].items():
            data["rate"] = (data["success"] / data["total"] * 100) if data["total"] > 0 else 0
        return stats

    def add_strategy(self, strategy: FallbackStrategy, priority: Optional[int] = None) -> None:
        """動態添加一個新的降級策略。"""
        if priority is None:
            self.strategies.insert(-1, strategy)  # 插入到優雅降級策略之前
        else:
            self.strategies.insert(priority, strategy)
        self.logger.info(f"已添加新的降級策略: {strategy.get_strategy_name()}")

    def clear_cache(self) -> None:
        """手動清理所有快取策略中的快取。"""
        for strategy in self.strategies:
            if isinstance(strategy, CacheFallback):
                strategy._cache.clear()
                strategy._cache_timestamps.clear()
                self.logger.info("所有快取降級策略的快取已被清理。")
                break


# 提供一個全域的降級管理器實例
fallback_manager = FallbackManager()

def get_fallback_manager() -> FallbackManager:
    """獲取全域的降級管理器實例。"""
    return fallback_manager
