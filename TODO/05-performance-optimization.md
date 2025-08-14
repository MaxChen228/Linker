# 05. 性能優化計劃

## 優先級: LOW
## 預估時間: 12+ 小時
## 狀態: ⏳ PENDING

### 背景
優化系統性能，提升查詢速度和響應時間，減少資源消耗。

### 子任務清單

#### A. 查詢性能分析 (3小時)
- [ ] 建立性能基準
  - [ ] 記錄當前查詢時間
  - [ ] 識別最慢的10個查詢
  - [ ] 分析查詢執行計劃

- [ ] EXPLAIN ANALYZE 分析
  ```sql
  -- 分析知識點查詢
  EXPLAIN (ANALYZE, BUFFERS) 
  SELECT * FROM knowledge_points 
  WHERE category = 'systematic' 
  AND is_deleted = FALSE 
  ORDER BY mastery_level ASC;
  ```

- [ ] 識別性能瓶頸
  - [ ] N+1 查詢問題
  - [ ] 缺失索引
  - [ ] 不必要的全表掃描

#### B. 查詢優化實施 (4小時)
- [ ] 優化 Repository 查詢
  - [ ] 實現批量查詢
  ```python
  async def get_points_with_details(self, point_ids: list[int]):
      # 一次查詢獲取所有相關數據
      query = """
          SELECT kp.*, 
                 array_agg(re.*) as review_examples,
                 array_agg(oe.*) as original_errors
          FROM knowledge_points kp
          LEFT JOIN review_examples re ON kp.id = re.knowledge_point_id
          LEFT JOIN original_errors oe ON kp.id = oe.knowledge_point_id
          WHERE kp.id = ANY($1)
          GROUP BY kp.id
      """
      return await self.connection.fetch(query, point_ids)
  ```

- [ ] 實現查詢結果快取
  - [ ] 使用 Redis 或內存快取
  - [ ] 設置合理的 TTL
  - [ ] 實現快取失效策略

- [ ] 優化分頁查詢
  - [ ] 使用游標分頁替代 OFFSET
  - [ ] 實現無限滾動支持
  - [ ] 減少每頁數據量

#### C. 連線池優化 (2小時)
- [ ] 調整連線池參數
  ```python
  POOL_CONFIG = {
      'min_size': 5,      # 根據負載調整
      'max_size': 20,     # 避免過多連線
      'max_queries': 50000,  # 連線生命週期
      'max_inactive_connection_lifetime': 300.0,
      'command_timeout': 10.0,
      'server_settings': {
          'application_name': 'linker',
          'jit': 'off'  # 對小查詢關閉 JIT
      }
  }
  ```

- [ ] 實現連線池監控
  - [ ] 追蹤活躍連線數
  - [ ] 記錄連線等待時間
  - [ ] 監控連線錯誤率

#### D. 前端性能優化 (2小時)
- [ ] API 請求優化
  - [ ] 實現請求去重
  - [ ] 添加請求快取
  - [ ] 使用 debounce/throttle

- [ ] 資源加載優化
  ```javascript
  // 懶加載非關鍵資源
  const loadKnowledgeDetails = async (id) => {
      // 只在需要時加載詳細信息
      if (!cache.has(id)) {
          const data = await fetch(`/api/knowledge/${id}`);
          cache.set(id, data);
      }
      return cache.get(id);
  };
  ```

- [ ] 渲染性能優化
  - [ ] 使用虛擬滾動
  - [ ] 減少 DOM 操作
  - [ ] 優化重繪和重排

#### E. 資料庫索引優化 (1.5小時)
- [ ] 創建複合索引
  ```sql
  -- 優化常見查詢模式
  CREATE INDEX idx_kp_composite 
  ON knowledge_points(category, mastery_level, next_review) 
  WHERE is_deleted = FALSE;
  
  -- 優化排序查詢
  CREATE INDEX idx_kp_sort 
  ON knowledge_points(created_at DESC, id DESC);
  ```

- [ ] 移除冗餘索引
  - [ ] 分析索引使用情況
  - [ ] 識別重複索引
  - [ ] 安全移除未使用索引

#### F. 監控與基準測試 (1.5小時)
- [ ] 建立性能監控
  - [ ] 使用 Prometheus + Grafana
  - [ ] 追蹤關鍵指標
  - [ ] 設置性能告警

- [ ] 自動化性能測試
  ```python
  @pytest.mark.benchmark
  async def test_query_performance():
      start = time.time()
      points = await repository.get_all_points()
      duration = time.time() - start
      assert duration < 0.1  # 100ms 內完成
  ```

### 性能目標
| 操作 | 當前 | 目標 | 改善 |
|------|------|------|------|
| 獲取知識點列表 | 150ms | 50ms | -67% |
| 單點查詢 | 80ms | 20ms | -75% |
| 搜索操作 | 200ms | 100ms | -50% |
| 批量更新 | 500ms | 200ms | -60% |

### 測試計劃
```bash
# 負載測試
locust -f tests/load_test.py --host=http://localhost:8000

# 基準測試
pytest tests/benchmarks/ --benchmark-only

# 資料庫查詢分析
psql -d linker -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### 驗收標準
1. P95 響應時間 < 100ms
2. 查詢性能提升 > 50%
3. 資料庫 CPU 使用率 < 30%
4. 前端 FCP < 1.5s

### 相關工具
- pgBadger - PostgreSQL 日誌分析
- pg_stat_statements - 查詢統計
- Apache JMeter - 負載測試
- Lighthouse - 前端性能審計