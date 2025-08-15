"""
統一快取管理系統
提供線程安全的快取管理，支援異步和同步操作
"""

import threading
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Callable, Union, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """快取條目"""

    value: Any
    timestamp: datetime
    ttl: int  # 存活時間（秒）
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """檢查是否過期"""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)


class UnifiedCacheManager:
    """統一的快取管理器

    提供線程安全的快取操作，支援：
    - 異步和同步操作
    - TTL 自動過期
    - 快取統計
    - 模式匹配失效
    """

    def __init__(self, default_ttl: int = 300):
        """初始化快取管理器

        Args:
            default_ttl: 預設存活時間（秒），預設5分鐘
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = threading.RLock()
        self._default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "refreshes": 0}

    def get(self, key: str, default: Any = None) -> Any:
        """線程安全的快取獲取

        Args:
            key: 快取鍵
            default: 預設值

        Returns:
            快取值或預設值
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
        """線程安全的快取設置

        Args:
            key: 快取鍵
            value: 快取值
            ttl: 存活時間（秒），None 使用預設值
        """
        with self._cache_lock:
            ttl = ttl or self._default_ttl
            self._cache[key] = CacheEntry(value=value, timestamp=datetime.now(), ttl=ttl)
            logger.debug(f"快取設置: {key}, TTL: {ttl}s")

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """快取失效，支援模式匹配

        Args:
            pattern: 匹配模式，None 表示清除所有快取

        Returns:
            清除的快取數量
        """
        with self._cache_lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"清除所有快取: {count} 個")
                return count

            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]

            if keys_to_remove:
                logger.info(f"按模式清除快取 '{pattern}': {len(keys_to_remove)} 個")
            return len(keys_to_remove)

    def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
        ttl: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Any:
        """獲取或計算快取值（同步版本）

        Args:
            key: 快取鍵
            compute_func: 計算函數
            ttl: 存活時間
            force_refresh: 強制重新計算

        Returns:
            快取或計算的值
        """
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                return cached

        # 計算新值
        try:
            value = compute_func()
            self.set(key, value, ttl)
            self._stats["refreshes"] += 1
            logger.debug(f"快取計算: {key}")
            return value
        except Exception as e:
            logger.error(f"快取計算失敗 {key}: {e}")
            raise

    async def get_or_compute_async(
        self,
        key: str,
        compute_func: Callable,
        ttl: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Any:
        """獲取或計算快取值（異步版本）

        Args:
            key: 快取鍵
            compute_func: 計算函數（可以是異步或同步）
            ttl: 存活時間
            force_refresh: 強制重新計算

        Returns:
            快取或計算的值
        """
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                return cached

        # 異步計算新值
        try:
            if asyncio.iscoroutinefunction(compute_func):
                value = await compute_func()
            else:
                value = compute_func()

            self.set(key, value, ttl)
            self._stats["refreshes"] += 1
            logger.debug(f"異步快取計算: {key}")
            return value
        except Exception as e:
            logger.error(f"異步快取計算失敗 {key}: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """獲取快取統計

        Returns:
            快取統計資訊
        """
        with self._cache_lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                **self._stats,
                "cache_size": len(self._cache),
                "hit_rate": round(hit_rate, 4),
                "total_requests": total_requests,
            }

    def cleanup_expired(self) -> int:
        """清理過期快取

        Returns:
            清理的快取數量
        """
        with self._cache_lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(f"清理過期快取: {len(expired_keys)} 個")

            return len(expired_keys)


class CacheCategories:
    """快取分類定義"""

    STATISTICS = "stats"
    KNOWLEDGE_POINTS = "knowledge"
    REVIEW_CANDIDATES = "review"
    SEARCH_RESULTS = "search"
    USER_PREFERENCES = "preferences"


class LayeredCacheManager(UnifiedCacheManager):
    """分層快取管理器

    根據不同數據類型設置不同的 TTL
    """

    def __init__(self):
        super().__init__()
        self._layer_ttls = {
            CacheCategories.STATISTICS: 60,  # 1分鐘
            CacheCategories.KNOWLEDGE_POINTS: 300,  # 5分鐘
            CacheCategories.REVIEW_CANDIDATES: 120,  # 2分鐘
            CacheCategories.SEARCH_RESULTS: 180,  # 3分鐘
            CacheCategories.USER_PREFERENCES: 600,  # 10分鐘
        }

    def set_with_category(self, category: str, key: str, value: Any) -> None:
        """按分類設置快取

        Args:
            category: 快取分類
            key: 快取鍵
            value: 快取值
        """
        full_key = f"{category}:{key}"
        ttl = self._layer_ttls.get(category, self._default_ttl)
        self.set(full_key, value, ttl)

    def get_with_category(self, category: str, key: str, default: Any = None) -> Any:
        """按分類獲取快取

        Args:
            category: 快取分類
            key: 快取鍵
            default: 預設值

        Returns:
            快取值或預設值
        """
        full_key = f"{category}:{key}"
        return self.get(full_key, default)

    def invalidate_category(self, category: str) -> int:
        """失效整個分類的快取

        Args:
            category: 快取分類

        Returns:
            清除的快取數量
        """
        return self.invalidate(f"{category}:")


class CacheSyncManager:
    """快取同步管理器

    用於保持多個快取實例之間的一致性
    """

    def __init__(self, json_cache: UnifiedCacheManager, db_cache: UnifiedCacheManager):
        self.json_cache = json_cache
        self.db_cache = db_cache

    def sync_statistics(self) -> bool:
        """同步統計快取

        Returns:
            同步是否成功
        """
        try:
            # 獲取兩種模式的統計
            json_stats = self.json_cache.get("statistics_sync")
            db_stats = self.db_cache.get("statistics_sync")

            if json_stats and db_stats:
                # 比較關鍵指標
                if self._are_stats_consistent(json_stats, db_stats):
                    return True
                else:
                    # 快取不一致，清除所有統計快取
                    self.json_cache.invalidate("statistics")
                    self.db_cache.invalidate("statistics")
                    logger.warning("統計快取不一致，已清除")
                    return False
            return True

        except Exception as e:
            logger.error(f"快取同步失敗: {e}")
            return False

    def _are_stats_consistent(self, json_stats: dict, db_stats: dict) -> bool:
        """檢查統計是否一致

        Args:
            json_stats: JSON 模式統計
            db_stats: Database 模式統計

        Returns:
            是否一致
        """
        key_fields = ["total_practices", "correct_count", "knowledge_points"]

        for field in key_fields:
            json_val = json_stats.get(field, 0)
            db_val = db_stats.get(field, 0)

            # 允許 1% 的誤差
            if json_val > 0:
                diff_rate = abs(json_val - db_val) / json_val
                if diff_rate > 0.01:  # 1% 閾值
                    logger.debug(f"統計不一致 {field}: JSON={json_val}, DB={db_val}")
                    return False
        return True

    def get_consistency_report(self) -> dict:
        """獲取一致性報告

        Returns:
            一致性狀態報告
        """
        json_stats_cache = self.json_cache.get_stats()
        db_stats_cache = self.db_cache.get_stats()

        return {
            "json_cache": json_stats_cache,
            "db_cache": db_stats_cache,
            "sync_status": self.sync_statistics(),
        }
