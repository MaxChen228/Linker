"""
統一快取管理系統

提供一個線程安全的記憶體快取，支援同步和異步操作。
主要功能包括：
- TTL (Time-To-Live) 自動過期機制。
- 基於鍵模式的快取失效。
- 快取命中率、錯過率等統計。
- 分層快取管理，可為不同類型的數據設定不同的 TTL。
- 快取同步管理器，用於確保多個快取實例之間的一致性。
"""

import asyncio
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """表示一個快取條目的資料結構。"""

    value: Any
    timestamp: datetime
    ttl: int  # 存活時間（秒）
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """檢查此快取條目是否已過期。"""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)


class UnifiedCacheManager:
    """
    統一的記憶體快取管理器。

    提供線程安全的快取操作，支援 TTL、統計和模式匹配失效。
    """

    def __init__(self, default_ttl: int = 300):
        """
        初始化快取管理器。

        Args:
            default_ttl: 預設的快取存活時間（秒），預設為 5 分鐘。
        """
        self._cache: dict[str, CacheEntry] = {}
        self._cache_lock = threading.RLock()  # 使用可重入鎖，允許同一線程多次獲取
        self._default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "refreshes": 0}

    def get(self, key: str, default: Any = None) -> Any:
        """
        從快取中獲取一個值。

        如果快取不存在或已過期，則返回預設值。
        此操作是線程安全的。

        Args:
            key: 快取鍵。
            default: 如果找不到快取，返回的預設值。

        Returns:
            快取的值或預設值。
        """
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return default

            if entry.is_expired:
                del self._cache[key]
                self._stats["evictions"] += 1
                self._stats["misses"] += 1
                logger.debug(f"快取過期並清除: {key}")
                return default

            entry.hit_count += 1
            self._stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        在快取中設定一個值。

        Args:
            key: 快取鍵。
            value: 要快取的值。
            ttl: 存活時間（秒）。如果為 None，則使用預設 TTL。
        """
        with self._cache_lock:
            ttl = ttl or self._default_ttl
            self._cache[key] = CacheEntry(value=value, timestamp=datetime.now(), ttl=ttl)
            logger.debug(f"快取設定: {key}, TTL: {ttl}s")

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        使快取失效。

        支援基於模式的失效，例如，`invalidate("user:123")` 將清除所有包含 "user:123" 的鍵。

        Args:
            pattern: 要匹配的模式。如果為 None，則清除所有快取。

        Returns:
            被清除的快取條目數量。
        """
        with self._cache_lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"清除所有快取: {count} 個")
                return count

            keys_to_remove = [k for k in self._cache if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]

            if keys_to_remove:
                logger.info(f"按模式清除快取 '{pattern}': {len(keys_to_remove)} 個")
            return len(keys_to_remove)

    def get_or_compute(
        self,
        key: str,
        compute_func: Callable[[], Any],
        ttl: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Any:
        """
        獲取快取值，如果不存在則計算並存儲（同步版本）。

        這是一個常見的快取模式，避免了「快取穿透」問題。

        Args:
            key: 快取鍵。
            compute_func: 一個無參數的函數，用於在快取未命中時計算新值。
            ttl: 存活時間。
            force_refresh: 是否強制重新計算，忽略現有快取。

        Returns:
            快取或新計算的值。
        """
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                return cached

        try:
            value = compute_func()
            self.set(key, value, ttl)
            self._stats["refreshes"] += 1
            logger.debug(f"快取計算並儲存: {key}")
            return value
        except Exception as e:
            logger.error(f"快取計算失敗 {key}: {e}")
            raise

    async def get_or_compute_async(
        self,
        key: str,
        compute_func: Callable[[], Any],
        ttl: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Any:
        """
        獲取快取值，如果不存在則計算並存儲（異步版本）。

        Args:
            key: 快取鍵。
            compute_func: 一個同步或異步的無參數函數，用於計算新值。
            ttl: 存活時間。
            force_refresh: 是否強制重新計算。

        Returns:
            快取或新計算的值。
        """
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                return cached

        try:
            if asyncio.iscoroutinefunction(compute_func):
                value = await compute_func()
            else:
                value = compute_func()

            self.set(key, value, ttl)
            self._stats["refreshes"] += 1
            logger.debug(f"異步快取計算並儲存: {key}")
            return value
        except Exception as e:
            logger.error(f"異步快取計算失敗 {key}: {e}")
            raise

    def get_stats(self) -> dict[str, Any]:
        """
        獲取快取統計數據。

        Returns:
            一個包含快取大小、命中率等資訊的字典。
        """
        with self._cache_lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests) if total_requests > 0 else 0

            return {
                **self._stats,
                "cache_size": len(self._cache),
                "hit_rate": round(hit_rate, 4),
                "total_requests": total_requests,
            }

    def cleanup_expired(self) -> int:
        """
        手動清理所有過期的快取條目。

        Returns:
            被清理的快取條目數量。
        """
        with self._cache_lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self._stats["evictions"] += len(expired_keys)
                logger.info(f"手動清理過期快取: {len(expired_keys)} 個")

            return len(expired_keys)


class CacheCategories:
    """定義標準的快取分類，方便統一管理。"""

    STATISTICS = "stats"
    KNOWLEDGE_POINTS = "knowledge"
    REVIEW_CANDIDATES = "review"
    SEARCH_RESULTS = "search"
    USER_PREFERENCES = "preferences"


class LayeredCacheManager(UnifiedCacheManager):
    """
    分層快取管理器。

    繼承自 `UnifiedCacheManager`，允許根據不同的數據類型（分類）
    設定不同的 TTL，實現更精細的快取策略。
    """

    def __init__(self):
        super().__init__()
        self._layer_ttls = {
            CacheCategories.STATISTICS: 60,  # 統計數據：1分鐘
            CacheCategories.KNOWLEDGE_POINTS: 300,  # 知識點：5分鐘
            CacheCategories.REVIEW_CANDIDATES: 120,  # 複習候選：2分鐘
            CacheCategories.SEARCH_RESULTS: 180,  # 搜尋結果：3分鐘
            CacheCategories.USER_PREFERENCES: 600,  # 使用者偏好：10分鐘
        }

    def set_with_category(self, category: str, key: str, value: Any) -> None:
        """
        按分類設定快取，自動應用該分類的 TTL。

        Args:
            category: 快取分類，應使用 `CacheCategories` 中的常量。
            key: 快取鍵。
            value: 要快取的值。
        """
        full_key = f"{category}:{key}"
        ttl = self._layer_ttls.get(category, self._default_ttl)
        self.set(full_key, value, ttl)

    def get_with_category(self, category: str, key: str, default: Any = None) -> Any:
        """
        按分類獲取快取。

        Args:
            category: 快取分類。
            key: 快取鍵。
            default: 預設值。

        Returns:
            快取的值或預設值。
        """
        full_key = f"{category}:{key}"
        return self.get(full_key, default)

    def invalidate_category(self, category: str) -> int:
        """
        使整個分類的快取失效。

        Args:
            category: 要失效的快取分類。

        Returns:
            被清除的快取數量。
        """
        return self.invalidate(f"{category}:")


class CacheSyncManager:
    """
    快取同步管理器。

    用於在不同儲存模式（例如 JSON 和資料庫）之間保持快取的一致性。
    如果偵測到不一致，會清除相關快取以強制重新載入。
    """

    def __init__(self, json_cache: UnifiedCacheManager, db_cache: UnifiedCacheManager):
        self.json_cache = json_cache
        self.db_cache = db_cache

    def sync_statistics(self) -> bool:
        """
        同步統計快取。

        比較 JSON 和資料庫模式下的統計數據，如果不一致則清除雙方的統計快取。

        Returns:
            如果快取一致或同步成功，返回 True。
        """
        try:
            json_stats = self.json_cache.get("statistics_sync")
            db_stats = self.db_cache.get("statistics_sync")

            if json_stats and db_stats and not self._are_stats_consistent(json_stats, db_stats):
                self.json_cache.invalidate(CacheCategories.STATISTICS)
                self.db_cache.invalidate(CacheCategories.STATISTICS)
                logger.warning("偵測到統計快取不一致，已清除。")
                return False
            return True

        except Exception as e:
            logger.error(f"快取同步失敗: {e}")
            return False

    def _are_stats_consistent(self, json_stats: dict, db_stats: dict) -> bool:
        """
        內部方法，檢查兩組統計數據是否一致。

        Args:
            json_stats: JSON 模式的統計數據。
            db_stats: 資料庫模式的統計數據。

        Returns:
            如果關鍵指標在容許誤差範圍內，返回 True。
        """
        key_fields = ["total_practices", "correct_count", "knowledge_points"]

        for field in key_fields:
            json_val = json_stats.get(field, 0)
            db_val = db_stats.get(field, 0)

            # 允許 1% 的誤差範圍
            if json_val > 0:
                diff_rate = abs(json_val - db_val) / json_val
                if diff_rate > 0.01:  # 1% 閾值
                    logger.debug(f"統計不一致 {field}: JSON={json_val}, DB={db_val}")
                    return False
        return True

    def get_consistency_report(self) -> dict:
        """
        獲取一份詳細的一致性報告。

        Returns:
            包含兩個快取實例的統計數據和同步狀態的報告。
        """
        json_stats_cache = self.json_cache.get_stats()
        db_stats_cache = self.db_cache.get_stats()

        return {
            "json_cache": json_stats_cache,
            "db_cache": db_stats_cache,
            "sync_status": self.sync_statistics(),
        }
