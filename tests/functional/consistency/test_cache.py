"""
快取一致性測試套件

測試統一快取管理系統的功能和一致性
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest

from core.cache_manager import (
    CacheCategories,
    CacheSyncManager,
    LayeredCacheManager,
    UnifiedCacheManager,
)


class TestUnifiedCacheManager:
    """統一快取管理器測試"""

    def test_basic_cache_operations(self):
        """測試基本快取操作"""
        cache = UnifiedCacheManager(default_ttl=60)

        # 測試設置和獲取
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # 測試預設值
        assert cache.get("nonexistent", "default") == "default"

        # 測試清除
        cache.invalidate()
        assert cache.get("test_key") is None

    def test_cache_ttl_and_expiration(self):
        """測試快取過期機制"""
        cache = UnifiedCacheManager(default_ttl=1)  # 1秒過期

        cache.set("expire_test", "value")
        assert cache.get("expire_test") == "value"

        # 等待過期
        time.sleep(1.1)
        assert cache.get("expire_test") is None

    def test_cache_pattern_invalidation(self):
        """測試模式匹配失效"""
        cache = UnifiedCacheManager()

        cache.set("stats:json", {"type": "json"})
        cache.set("stats:db", {"type": "db"})
        cache.set("knowledge:active", [])
        cache.set("other:data", "other")

        # 按模式清除
        cleared = cache.invalidate("stats")
        assert cleared == 2

        # 驗證清除結果
        assert cache.get("stats:json") is None
        assert cache.get("stats:db") is None
        assert cache.get("knowledge:active") == []
        assert cache.get("other:data") == "other"

    def test_get_or_compute_sync(self):
        """測試同步獲取或計算"""
        cache = UnifiedCacheManager()
        compute_count = 0

        def compute_func():
            nonlocal compute_count
            compute_count += 1
            return f"computed_{compute_count}"

        # 第一次計算
        result1 = cache.get_or_compute("compute_test", compute_func)
        assert result1 == "computed_1"
        assert compute_count == 1

        # 第二次使用快取
        result2 = cache.get_or_compute("compute_test", compute_func)
        assert result2 == "computed_1"
        assert compute_count == 1  # 沒有再次計算

        # 強制重新計算
        result3 = cache.get_or_compute("compute_test", compute_func, force_refresh=True)
        assert result3 == "computed_2"
        assert compute_count == 2

    @pytest.mark.asyncio
    async def test_get_or_compute_async(self):
        """測試異步獲取或計算"""
        cache = UnifiedCacheManager()
        compute_count = 0

        async def async_compute_func():
            nonlocal compute_count
            compute_count += 1
            await asyncio.sleep(0.01)  # 模擬異步操作
            return f"async_computed_{compute_count}"

        def sync_compute_func():
            nonlocal compute_count
            compute_count += 1
            return f"sync_computed_{compute_count}"

        # 測試異步函數
        result1 = await cache.get_or_compute_async("async_test", async_compute_func)
        assert result1 == "async_computed_1"

        # 測試同步函數
        result2 = await cache.get_or_compute_async("sync_test", sync_compute_func)
        assert result2 == "sync_computed_2"

    def test_cache_statistics(self):
        """測試快取統計功能"""
        cache = UnifiedCacheManager()

        # 初始統計
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["cache_size"] == 0
        assert stats["hit_rate"] == 0

        # 快取未命中
        cache.get("nonexistent")
        stats = cache.get_stats()
        assert stats["misses"] == 1

        # 快取命中
        cache.set("test", "value")
        cache.get("test")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["cache_size"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 0.5

    def test_cache_thread_safety(self):
        """測試快取線程安全性"""
        cache = UnifiedCacheManager()
        results = []
        errors = []

        def worker(worker_id: int):
            try:
                for i in range(100):
                    key = f"test_key_{i % 10}"
                    value = f"worker_{worker_id}_value_{i}"

                    # 設置值
                    cache.set(key, value)

                    # 獲取值
                    retrieved = cache.get(key)

                    # 記錄結果（由於並發，值可能被其他線程覆蓋）
                    results.append(retrieved is not None)

                    time.sleep(0.001)  # 短暫等待增加並發機會
            except Exception as e:
                errors.append(e)

        # 啟動多個線程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待完成
        for thread in threads:
            thread.join()

        # 檢查結果
        assert not errors, f"線程安全測試出現錯誤: {errors}"
        assert all(results), "所有操作都應該成功"
        assert len(results) == 500  # 5個線程 * 100次操作

    def test_cache_cleanup_expired(self):
        """測試清理過期快取"""
        cache = UnifiedCacheManager(default_ttl=1)

        # 添加一些快取
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3", ttl=2)  # 較長過期時間

        assert cache.get_stats()["cache_size"] == 3

        # 等待部分過期
        time.sleep(1.1)

        # 清理過期快取
        cleaned = cache.cleanup_expired()
        assert cleaned == 2  # key1 和 key2 過期

        # 驗證剩餘快取
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"


class TestLayeredCacheManager:
    """分層快取管理器測試"""

    def test_category_based_caching(self):
        """測試基於分類的快取"""
        cache = LayeredCacheManager()

        # 設置不同分類的快取
        cache.set_with_category(CacheCategories.STATISTICS, "json", {"stats": "json_data"})
        cache.set_with_category(CacheCategories.KNOWLEDGE_POINTS, "active", [1, 2, 3])
        cache.set_with_category(CacheCategories.SEARCH_RESULTS, "test", ["result1"])

        # 獲取快取
        json_stats = cache.get_with_category(CacheCategories.STATISTICS, "json")
        assert json_stats == {"stats": "json_data"}

        active_points = cache.get_with_category(CacheCategories.KNOWLEDGE_POINTS, "active")
        assert active_points == [1, 2, 3]

        # 按分類清除快取
        cleared = cache.invalidate_category(CacheCategories.STATISTICS)
        assert cleared == 1

        # 驗證分類清除
        assert cache.get_with_category(CacheCategories.STATISTICS, "json") is None
        assert cache.get_with_category(CacheCategories.KNOWLEDGE_POINTS, "active") == [1, 2, 3]

    def test_category_ttl_differences(self):
        """測試不同分類的 TTL 設置"""
        cache = LayeredCacheManager()

        # 統計分類 TTL 為 60 秒
        cache.set_with_category(CacheCategories.STATISTICS, "test", "stats_value")

        # 知識點分類 TTL 為 300 秒
        cache.set_with_category(CacheCategories.KNOWLEDGE_POINTS, "test", "points_value")

        # 檢查 TTL 設置（通過檢查內部快取項目）
        stats_key = f"{CacheCategories.STATISTICS}:test"
        points_key = f"{CacheCategories.KNOWLEDGE_POINTS}:test"

        stats_entry = cache._cache[stats_key]
        points_entry = cache._cache[points_key]

        assert stats_entry.ttl == 60
        assert points_entry.ttl == 300


@pytest.mark.integration
class TestCacheConsistency:
    """快取一致性測試"""

    @pytest.mark.asyncio
    async def test_async_sync_cache_consistency(self):
        """測試異步和同步方法的快取一致性"""
        from core.database.adapter import KnowledgeManagerAdapter

        # 創建資料庫模式適配器（使用模擬）
        adapter = KnowledgeManagerAdapter(use_database=False)  # JSON 模式用於測試

        # 清除所有快取
        adapter._cache_manager.invalidate()

        # 同步獲取統計
        sync_stats = adapter.get_statistics()

        # 檢查快取是否建立
        cache_stats = adapter._cache_manager.get_stats()
        assert cache_stats["cache_size"] > 0

        # 再次同步獲取（應該使用快取）
        sync_stats2 = adapter.get_statistics()
        assert sync_stats == sync_stats2

    def test_cache_invalidation_consistency(self):
        """測試快取失效一致性"""
        from core.knowledge import KnowledgeManager

        # 創建 JSON 模式管理器
        manager = KnowledgeManager("data")  # 使用現有數據

        # 獲取初始統計（建立快取）
        initial_stats = manager.get_statistics()

        # 檢查快取
        cache_stats = manager._cache_manager.get_stats()
        initial_cache_size = cache_stats["cache_size"]

        # 模擬保存錯誤（會觸發快取失效）
        feedback = {
            "is_generally_correct": False,
            "error_analysis": [
                {
                    "key_point_summary": "測試錯誤",
                    "category": "systematic",
                    "original_phrase": "test phrase",
                    "correction": "corrected phrase",
                    "explanation": "test explanation",
                    "severity": "major",
                }
            ],
            "overall_suggestion": "test correction",
        }

        manager.save_mistake("測試句子", "錯誤答案", feedback)

        # 檢查快取是否被清除
        cache_stats_after = manager._cache_manager.get_stats()
        assert (
            cache_stats_after["cache_size"] < initial_cache_size or cache_stats_after["misses"] > 0
        )

    def test_cache_sync_manager(self):
        """測試快取同步管理器"""
        json_cache = UnifiedCacheManager()
        db_cache = UnifiedCacheManager()

        sync_manager = CacheSyncManager(json_cache, db_cache)

        # 設置一致的統計資料
        consistent_stats = {"total_practices": 100, "correct_count": 80, "knowledge_points": 20}

        json_cache.set("statistics_sync", consistent_stats)
        db_cache.set("statistics_sync", consistent_stats)

        # 測試同步成功
        assert sync_manager.sync_statistics() == True

        # 設置不一致的統計資料
        inconsistent_stats = {
            "total_practices": 50,  # 不同的值
            "correct_count": 40,
            "knowledge_points": 10,
        }

        json_cache.set("statistics_sync", consistent_stats)
        db_cache.set("statistics_sync", inconsistent_stats)

        # 測試同步失敗並清除快取
        assert sync_manager.sync_statistics() == False
        assert json_cache.get("statistics_sync") is None
        assert db_cache.get("statistics_sync") is None

    def test_cache_consistency_report(self):
        """測試一致性報告"""
        json_cache = UnifiedCacheManager()
        db_cache = UnifiedCacheManager()

        sync_manager = CacheSyncManager(json_cache, db_cache)

        # 添加一些快取數據
        json_cache.set("test1", "value1")
        json_cache.get("test1")  # 增加命中
        json_cache.get("nonexistent")  # 增加未命中

        db_cache.set("test2", "value2")
        db_cache.get("test2")

        # 獲取一致性報告
        report = sync_manager.get_consistency_report()

        assert "json_cache" in report
        assert "db_cache" in report
        assert "sync_status" in report

        assert report["json_cache"]["hits"] == 1
        assert report["json_cache"]["misses"] == 1
        assert report["db_cache"]["hits"] == 1


class TestCachePerformance:
    """快取性能測試"""

    def test_cache_set_performance(self):
        """測試快取設置性能"""
        cache = UnifiedCacheManager()

        start_time = time.time()
        for i in range(1000):
            cache.set(f"perf_key_{i}", f"value_{i}")
        set_time = time.time() - start_time

        # 1000次設置應該在1秒內完成
        assert set_time < 1.0, f"設置性能過慢: {set_time:.3f}s"

    def test_cache_get_performance(self):
        """測試快取獲取性能"""
        cache = UnifiedCacheManager()

        # 先設置數據
        for i in range(1000):
            cache.set(f"perf_key_{i}", f"value_{i}")

        start_time = time.time()
        for i in range(1000):
            cache.get(f"perf_key_{i}")
        get_time = time.time() - start_time

        # 1000次獲取應該在1秒內完成
        assert get_time < 1.0, f"獲取性能過慢: {get_time:.3f}s"

        # 檢查命中率
        stats = cache.get_stats()
        assert stats["hit_rate"] == 1.0, "應該100%命中"

    def test_cache_concurrent_performance(self):
        """測試並發性能"""
        cache = UnifiedCacheManager()
        results = []

        def concurrent_worker():
            start = time.time()
            for i in range(100):
                cache.set(f"concurrent_{threading.current_thread().ident}_{i}", f"value_{i}")
                cache.get(f"concurrent_{threading.current_thread().ident}_{i}")
            end = time.time()
            results.append(end - start)

        # 啟動10個並發線程
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=concurrent_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 所有線程都應該在合理時間內完成
        max_time = max(results)
        assert max_time < 2.0, f"並發性能過慢: {max_time:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
