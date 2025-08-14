# 06. 監控與健康檢查系統

## 優先級: LOW
## 預估時間: 8-10 小時
## 狀態: ⏳ PENDING

### 背景
建立完整的監控系統，實現健康檢查、性能監控和自動告警。

### 子任務清單

#### A. 健康檢查端點 (2小時)
- [ ] 實現 `/health` 端點
  ```python
  @router.get("/health")
  async def health_check():
      checks = {
          "status": "healthy",
          "timestamp": datetime.utcnow(),
          "checks": {
              "database": await check_database(),
              "ai_service": await check_ai_service(),
              "storage": check_storage_space(),
              "memory": check_memory_usage()
          }
      }
      return checks
  ```

- [ ] 資料庫健康檢查
  - [ ] 測試連線池狀態
  - [ ] 執行簡單查詢
  - [ ] 檢查響應時間

- [ ] AI 服務健康檢查
  - [ ] 驗證 API key
  - [ ] 測試 Gemini 連線
  - [ ] 檢查配額狀態

#### B. 性能指標收集 (2.5小時)
- [ ] 實現指標收集器
  ```python
  class MetricsCollector:
      def __init__(self):
          self.request_count = Counter('requests_total')
          self.request_duration = Histogram('request_duration_seconds')
          self.active_connections = Gauge('db_connections_active')
          self.error_rate = Counter('errors_total')
      
      async def record_request(self, endpoint, duration, status):
          self.request_count.labels(endpoint=endpoint, status=status).inc()
          self.request_duration.labels(endpoint=endpoint).observe(duration)
  ```

- [ ] 業務指標
  - [ ] 知識點創建率
  - [ ] 練習完成數
  - [ ] 用戶活躍度
  - [ ] 錯誤分類分布

- [ ] 系統指標
  - [ ] CPU 使用率
  - [ ] 記憶體使用
  - [ ] 磁碟 I/O
  - [ ] 網路流量

#### C. Prometheus 集成 (2小時)
- [ ] 配置 Prometheus
  ```yaml
  # prometheus.yml
  scrape_configs:
    - job_name: 'linker'
      static_configs:
        - targets: ['localhost:8000']
      metrics_path: '/metrics'
      scrape_interval: 15s
  ```

- [ ] 實現 `/metrics` 端點
  - [ ] 暴露 Prometheus 格式指標
  - [ ] 添加自定義標籤
  - [ ] 實現指標聚合

- [ ] 創建 Grafana 儀表板
  - [ ] 系統概覽面板
  - [ ] API 性能面板
  - [ ] 資料庫監控面板
  - [ ] 錯誤追蹤面板

#### D. 日誌聚合系統 (1.5小時)
- [ ] 結構化日誌格式
  ```python
  import structlog
  
  logger = structlog.get_logger()
  logger.info("request_processed",
              user_id=user_id,
              endpoint=endpoint,
              duration_ms=duration,
              status_code=status)
  ```

- [ ] 日誌級別管理
  - [ ] 動態日誌級別調整
  - [ ] 按模組配置級別
  - [ ] 敏感信息過濾

- [ ] 日誌輪轉策略
  - [ ] 按大小輪轉
  - [ ] 按時間輪轉
  - [ ] 壓縮歸檔

#### E. 告警規則配置 (2小時)
- [ ] 定義告警規則
  ```yaml
  # alerts.yml
  groups:
    - name: linker_alerts
      rules:
        - alert: HighErrorRate
          expr: rate(errors_total[5m]) > 0.05
          for: 5m
          annotations:
            summary: "高錯誤率告警"
            
        - alert: DatabaseDown
          expr: up{job="postgresql"} == 0
          for: 1m
          annotations:
            summary: "資料庫離線"
            
        - alert: SlowResponse
          expr: histogram_quantile(0.95, request_duration_seconds) > 1
          for: 10m
          annotations:
            summary: "響應時間過慢"
  ```

- [ ] 告警通知配置
  - [ ] Email 通知
  - [ ] Slack 集成
  - [ ] 日誌記錄

- [ ] 告警升級策略
  - [ ] 分級告警
  - [ ] 值班排程
  - [ ] 自動升級

### 監控儀表板設計

#### 系統總覽
```
┌─────────────────────────────────────┐
│ 系統狀態: ✅ 健康                    │
│ 運行時間: 15d 3h 24m                 │
│ 活躍用戶: 42                         │
└─────────────────────────────────────┘

┌──────────┬──────────┬──────────┐
│ QPS      │ P95延遲   │ 錯誤率   │
│ 125      │ 87ms     │ 0.02%    │
└──────────┴──────────┴──────────┘
```

#### 性能趨勢圖
- 請求量時間序列圖
- 響應時間分布圖
- 錯誤率趨勢圖
- 資源使用率圖表

### 測試計劃
```python
async def test_health_endpoint():
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]

async def test_metrics_collection():
    # 發送測試請求
    await client.get("/api/knowledge/points")
    # 檢查指標
    metrics = await client.get("/metrics")
    assert "requests_total" in metrics.text
```

### 驗收標準
1. 健康檢查端點響應 < 100ms
2. 所有關鍵指標被收集
3. Grafana 儀表板正常顯示
4. 告警規則正確觸發

### 相關文件
- `/Users/chenliangyu/Desktop/linker/web/routers/utils.py`
- Prometheus 文檔: https://prometheus.io/docs/
- Grafana 文檔: https://grafana.com/docs/