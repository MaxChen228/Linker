# 快取管理系統文檔

## 概述

Linker 項目實現了統一的快取管理系統，解決了 JSON 和 Database 雙模式下的快取一致性問題，提供線程安全的快取操作和智能過期管理。

## 系統架構

### 核心組件

#### UnifiedCacheManager
主要的快取管理器，提供：
- 線程安全的快取操作（讀取/寫入/失效）
- TTL（生存時間）自動過期機制
- 快取統計和監控功能
- 異步和同步操作支持

#### LayeredCacheManager
分層快取管理器，基於 UnifiedCacheManager 擴展：
- 按數據類型分類的快取策略
- 不同分類使用不同的 TTL 設置
- 分類級別的快取失效控制

#### CacheSyncManager
多快取實例一致性管理器：
- 確保 JSON 和 Database 模式快取的一致性
- 自動檢測和處理快取不一致問題
- 提供一致性狀態報告

### 數據分類

```python
class CacheCategories:
    STATISTICS = "stats"           # 統計數據
    KNOWLEDGE_POINTS = "knowledge" # 知識點數據
    REVIEW_CANDIDATES = "review"   # 複習候選
    SEARCH_RESULTS = "search"      # 搜索結果
    USER_PREFERENCES = "preferences" # 用戶偏好
```

### TTL 策略

| 分類 | TTL | 說明 |
|------|-----|------|
| 統計數據 | 60秒 | 變化頻繁，需要較新的數據 |
| 知識點 | 300秒 | 相對穩定，可以緩存較長時間 |
| 複習候選 | 120秒 | 中等變化頻率 |
| 搜索結果 | 180秒 | 搜索結果相對穩定 |
| 用戶偏好 | 600秒 | 變化很少，可以長期緩存 |

## 實現細節

### 線程安全

使用 `threading.RLock()` 實現可重入鎖，確保：
- 多線程環境下的數據一致性
- 避免死鎖問題
- 支持同一線程多次獲取鎖

```python
def get(self, key: str, default: Any = None) -> Any:
    with self._cache_lock:
        # 線程安全的快取操作
        entry = self._cache.get(key)
        if entry and not entry.is_expired:
            entry.hit_count += 1
            self._stats['hits'] += 1
            return entry.value
        return default
```

### 自動過期機制

快取項目包含時間戳和 TTL 信息：
- 讀取時自動檢查是否過期
- 過期項目自動清除並返回預設值
- 定期清理過期項目

```python
@dataclass
class CacheEntry:
    value: Any
    timestamp: datetime
    ttl: int
    hit_count: int = 0
    
    @property 
    def is_expired(self) -> bool:
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)
```

### 計算快取模式

支持懶加載計算模式：
- 快取存在且未過期：直接返回
- 快取不存在或過期：執行計算函數並緩存結果
- 支持強制刷新模式

```python
def get_or_compute(self, key: str, compute_func: Callable, 
                  ttl: Optional[int] = None, 
                  force_refresh: bool = False) -> Any:
    if not force_refresh:
        cached = self.get(key)
        if cached is not None:
            return cached
    
    # 計算新值並緩存
    value = compute_func()
    self.set(key, value, ttl)
    return value
```

## 使用方式

### 基本用法

```python
from core.cache_manager import UnifiedCacheManager

# 創建快取管理器
cache = UnifiedCacheManager(default_ttl=300)

# 基本操作
cache.set("user:123", user_data, ttl=600)
user = cache.get("user:123", default_user)

# 計算快取
stats = cache.get_or_compute(
    key="statistics", 
    compute_func=calculate_stats,
    ttl=60
)
```

### 分類快取

```python
from core.cache_manager import LayeredCacheManager, CacheCategories

# 使用分層快取
cache = LayeredCacheManager()

# 設置不同分類的數據
cache.set_with_category(CacheCategories.STATISTICS, "json", stats_data)
cache.set_with_category(CacheCategories.KNOWLEDGE_POINTS, "active", points)

# 按分類清除快取
cache.invalidate_category(CacheCategories.STATISTICS)
```

### 異步支持

```python
# 異步計算快取
async def async_compute():
    return await expensive_async_operation()

result = await cache.get_or_compute_async(
    key="async_result",
    compute_func=async_compute,
    ttl=120
)
```

## 整合說明

### JSON 模式整合

在 `KnowledgeManager` 中：
- 統計方法使用統一快取
- 數據變更時自動失效相關快取
- 保持向後兼容性

```python
def get_statistics(self) -> dict:
    return self._cache_manager.get_or_compute(
        key=f"{CacheCategories.STATISTICS}:json",
        compute_func=self._compute_statistics,
        ttl=60
    )

def save_mistake(self, ...):
    # 保存邏輯
    ...
    # 清除相關快取
    self._invalidate_caches()
```

### Database 模式整合

在 `KnowledgeManagerAdapter` 中：
- 異步和同步統計方法都使用統一快取
- 數據庫操作後自動失效快取
- 確保兩種模式快取行為一致

```python
async def get_statistics_async(self) -> dict:
    return await self._cache_manager.get_or_compute_async(
        key=f"{CacheCategories.STATISTICS}:async",
        compute_func=self._compute_statistics_async,
        ttl=60
    )

def get_statistics(self) -> dict:
    return self._cache_manager.get_or_compute(
        key=f"{CacheCategories.STATISTICS}:sync",
        compute_func=self._compute_statistics_sync,
        ttl=60
    )
```

## 性能指標

### 測試結果

根據完整測試套件的驗證：

- **設置性能**: 1000次操作 < 1秒
- **獲取性能**: 1000次操作 < 1秒，100% 命中率
- **線程安全**: 5線程 × 100操作 = 100% 成功率
- **並發性能**: 10線程並發 < 2秒完成
- **記憶體效率**: 自動清理過期項目

### 快取效果

實際運行中的效果：
- 統計計算快取命中率 > 50%
- 減少重複計算開銷
- 提升API響應速度
- 降低數據庫查詢頻率

## 監控和調試

### 快取統計

```python
stats = cache.get_stats()
print(f"快取大小: {stats['cache_size']}")
print(f"命中率: {stats['hit_rate']:.2%}")
print(f"總請求: {stats['total_requests']}")
print(f"命中數: {stats['hits']}")
print(f"未命中數: {stats['misses']}")
```

### 日誌記錄

快取操作會記錄詳細日誌：
- 快取設置/獲取操作
- 過期清理活動
- 快取失效事件
- 異常情況報告

```
21:55:48 - core.knowledge - DEBUG - JSON 統計計算完成: 練習39, 正確0, 知識點35
21:56:03 - core.knowledge - DEBUG - 已清除相關快取
```

## 最佳實踐

### 選擇合適的TTL

1. **頻繁變化的數據**（如統計）：較短TTL（60秒）
2. **相對穩定的數據**（如知識點）：中等TTL（5分鐘）
3. **很少變化的數據**（如配置）：較長TTL（10分鐘）

### 快取失效策略

1. **數據變更時立即失效**：確保一致性
2. **按分類失效**：避免過度清除
3. **定期清理**：防止記憶體洩漏

### 錯誤處理

1. **計算函數異常**：記錄錯誤，不緩存錯誤結果
2. **快取操作失敗**：降級到直接計算
3. **一致性檢查**：定期驗證快取正確性

## 故障排除

### 常見問題

1. **快取命中率低**
   - 檢查TTL設置是否合理
   - 確認快取失效策略
   - 檢查數據變更頻率

2. **記憶體使用過高**
   - 檢查TTL設置
   - 確認定期清理執行
   - 調整快取大小限制

3. **線程安全問題**
   - 檢查鎖的使用
   - 確認沒有死鎖情況
   - 檢查異步操作

### 調試技巧

1. 啟用詳細日誌記錄
2. 監控快取統計數據
3. 使用快取一致性檢查工具
4. 進行性能基準測試

## 未來擴展

### 可能的改進

1. **分散式快取**：支援Redis等外部快取
2. **快取預熱**：系統啟動時預載入熱數據
3. **智能TTL**：根據訪問模式動態調整TTL
4. **快取壓縮**：減少記憶體使用
5. **持久化快取**：系統重啟後保留部分快取

### 配置選項

考慮添加配置文件支持：
```yaml
cache:
  default_ttl: 300
  max_size: 10000
  cleanup_interval: 3600
  categories:
    statistics: 60
    knowledge: 300
    search: 180
```

這個統一快取管理系統為 Linker 項目提供了可靠、高效的快取解決方案，解決了多模式一致性問題，提升了系統整體性能。