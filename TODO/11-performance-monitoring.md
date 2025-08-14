# 11. 性能監控與追蹤系統

## 優先級: LOW 🟢
## 預估時間: 6-8 小時
## 狀態: ⏳ PENDING

### 背景
目前系統缺少性能監控機制，無法追蹤 API 響應時間、資料庫查詢效能和系統資源使用情況。

### 子任務清單

#### A. 應用性能監控 (APM) 整合 (2小時)
- [ ] 選擇監控方案
  - [ ] 評估 Prometheus + Grafana
  - [ ] 考慮 New Relic / DataDog (如果有預算)
  - [ ] 或使用開源方案 OpenTelemetry
  
- [ ] 實現度量收集
  ```python
  # core/monitoring.py
  from prometheus_client import Counter, Histogram, Gauge
  
  request_count = Counter('app_requests_total', 'Total requests')
  request_duration = Histogram('app_request_duration_seconds', 'Request duration')
  active_users = Gauge('app_active_users', 'Active users')
  ```
  
- [ ] 添加中間件
  - [ ] 請求計數中間件
  - [ ] 響應時間追蹤
  - [ ] 錯誤率統計

#### B. 資料庫性能追蹤 (2小時)
- [ ] 實現查詢性能記錄
  ```python
  # core/database/monitoring.py
  class QueryMonitor:
      def log_query(self, query, duration):
          # 記錄慢查詢
          if duration > 100:  # ms
              logger.warning(f"Slow query: {query}")
  ```
  
- [ ] 添加連線池監控
  - [ ] 活躍連線數
  - [ ] 等待時間
  - [ ] 連線錯誤率
  
- [ ] 實現查詢優化建議
  - [ ] 分析常見查詢模式
  - [ ] 識別 N+1 問題
  - [ ] 建議索引優化

#### C. AI API 使用追蹤 (1.5小時)
- [ ] Gemini API 調用監控
  - [ ] 記錄每次調用的 token 使用量
  - [ ] 追蹤響應時間
  - [ ] 計算成本估算
  
- [ ] 實現使用量限制
  ```python
  class GeminiUsageTracker:
      def __init__(self, daily_limit=10000):
          self.daily_limit = daily_limit
          self.usage = 0
      
      def check_limit(self):
          if self.usage >= self.daily_limit:
              raise APILimitExceeded()
  ```
  
- [ ] 創建使用報表
  - [ ] 每日/每週/每月統計
  - [ ] 按功能分類統計
  - [ ] 成本分析報告

#### D. 前端性能監控 (1.5小時)
- [ ] 實現 Web Vitals 追蹤
  ```javascript
  // web/static/js/monitoring.js
  import {getCLS, getFID, getFCP, getLCP, getTTFB} from 'web-vitals';
  
  function sendToAnalytics(metric) {
      // 發送到後端
      fetch('/api/metrics', {
          method: 'POST',
          body: JSON.stringify(metric)
      });
  }
  ```
  
- [ ] 添加錯誤追蹤
  - [ ] JavaScript 錯誤捕獲
  - [ ] API 請求失敗記錄
  - [ ] 用戶操作追蹤
  
- [ ] 實現性能預算
  - [ ] 設定載入時間目標
  - [ ] 監控包大小
  - [ ] 追蹤資源使用

#### E. 監控儀表板建立 (1小時)
- [ ] 創建 Grafana 儀表板
  - [ ] API 性能面板
  - [ ] 資料庫監控面板
  - [ ] 系統資源面板
  - [ ] 業務指標面板
  
- [ ] 設置告警規則
  - [ ] API 響應時間 > 1s
  - [ ] 錯誤率 > 1%
  - [ ] 資料庫連線池耗盡
  - [ ] AI API 配額接近上限

### 驗收標準
1. 能即時查看系統性能指標
2. 慢查詢自動記錄並告警
3. AI API 使用量可追蹤和限制
4. 前端性能數據可視化

### 測試計劃
```bash
# 啟動 Prometheus
docker run -p 9090:9090 -v prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

# 啟動 Grafana
docker run -p 3000:3000 grafana/grafana

# 產生測試負載
locust -f tests/load_test.py --host=http://localhost:8000

# 檢查指標端點
curl http://localhost:8000/metrics
```

### 相關文件
- Prometheus Python Client: https://github.com/prometheus/client_python
- FastAPI Monitoring: https://fastapi.tiangolo.com/tutorial/middleware/
- Web Vitals: https://web.dev/vitals/
- `/Users/chenliangyu/Desktop/linker/core/config.py` (添加監控配置)

### 預期效益
1. 及早發現性能問題
2. 優化資料庫查詢
3. 控制 AI API 成本
4. 提升用戶體驗