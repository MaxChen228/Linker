# 04. 錯誤處理與恢復機制

## 優先級: MEDIUM
## 預估時間: 6-8 小時
## 狀態: ⏳ PENDING

### 背景
增強系統的錯誤處理能力，實現優雅降級和自動恢復機制。

### 子任務清單

#### A. 連線池錯誤處理 (2小時)
- [ ] 實現連線重試機制
  - [ ] 定義重試策略（exponential backoff）
  - [ ] 設置最大重試次數（預設3次）
  - [ ] 實現重試間隔計算
  ```python
  async def _connect_with_retry(self, max_retries=3):
      for attempt in range(max_retries):
          try:
              return await self._create_pool()
          except Exception as e:
              wait_time = 2 ** attempt  # 1, 2, 4 seconds
              await asyncio.sleep(wait_time)
      raise ConnectionPoolError("無法建立連線池")
  ```

- [ ] 連線池健康檢查
  - [ ] 實現定期 ping 機制
  - [ ] 自動移除失效連線
  - [ ] 監控連線池狀態

#### B. 優雅降級機制 (2.5小時)
- [ ] 資料庫到 JSON 自動切換
  - [ ] 檢測資料庫不可用
  - [ ] 自動切換到 JSON 模式
  - [ ] 記錄降級事件
  - [ ] 通知用戶當前模式

- [ ] 實現降級策略
  ```python
  class GracefulDegradation:
      async def execute_with_fallback(self, db_operation, json_operation):
          if self.use_database:
              try:
                  return await db_operation()
              except DatabaseError:
                  self.logger.warning("資料庫操作失敗，降級到 JSON")
                  self.use_database = False
                  return json_operation()
          return json_operation()
  ```

- [ ] 降級後的數據同步
  - [ ] 記錄降級期間的操作
  - [ ] 實現數據補償機制
  - [ ] 恢復後的數據合併

#### C. 死鎖檢測與處理 (1.5小時)
- [ ] 實現死鎖檢測
  - [ ] 設置查詢超時
  - [ ] 識別死鎖模式
  - [ ] 記錄死鎖信息

- [ ] 死鎖恢復策略
  ```python
  async def handle_deadlock(self, operation):
      max_retries = 3
      for attempt in range(max_retries):
          try:
              return await operation()
          except DeadlockError:
              # 隨機延遲避免再次死鎖
              delay = random.uniform(0.1, 0.5) * (attempt + 1)
              await asyncio.sleep(delay)
      raise
  ```

#### D. 錯誤日誌與監控 (2小時)
- [ ] 結構化錯誤日誌
  - [ ] 定義錯誤日誌格式
  - [ ] 包含上下文信息
  - [ ] 錯誤分類和標籤
  ```python
  {
      "timestamp": "2024-01-01T10:00:00",
      "error_type": "DatabaseConnectionError",
      "severity": "HIGH",
      "component": "connection_pool",
      "context": {
          "user_id": null,
          "operation": "connect",
          "retry_count": 3
      },
      "stack_trace": "..."
  }
  ```

- [ ] 錯誤指標收集
  - [ ] 錯誤頻率統計
  - [ ] 錯誤類型分布
  - [ ] 響應時間監控

- [ ] 告警機制
  - [ ] 定義告警閾值
  - [ ] 實現通知機制（日誌/郵件）
  - [ ] 錯誤趨勢分析

### 測試場景

#### 連線失敗測試
```python
async def test_connection_failure():
    # 模擬資料庫不可用
    with patch('asyncpg.create_pool', side_effect=Exception):
        adapter = KnowledgeManagerAdapter(use_database=True)
        # 應該自動降級到 JSON
        points = adapter.get_active_points()
        assert points is not None
```

#### 死鎖模擬測試
```python
async def test_deadlock_recovery():
    # 創建並發事務
    tasks = [
        update_point(1, lock_order=[1, 2]),
        update_point(2, lock_order=[2, 1])
    ]
    # 應該自動重試並恢復
    results = await asyncio.gather(*tasks)
    assert all(results)
```

### 監控儀表板需求
- 實時錯誤率圖表
- 錯誤類型分布餅圖
- 降級事件時間線
- 連線池狀態指示器

### 驗收標準
1. 資料庫故障時自動降級到 JSON
2. 死鎖自動檢測並恢復
3. 所有錯誤都有結構化日誌
4. 錯誤率 < 0.1%

### 相關文件
- `/Users/chenliangyu/Desktop/linker/core/database/connection.py`
- `/Users/chenliangyu/Desktop/linker/core/database/exceptions.py`
- `/Users/chenliangyu/Desktop/linker/core/exceptions.py`