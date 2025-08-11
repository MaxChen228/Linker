# 日誌系統文檔

## 概述

Linker 專案使用統一的日誌系統，提供 Python 後端和 JavaScript 前端的一致日誌記錄功能。

## Python 日誌系統

### 快速開始

```python
from core.log_config import get_module_logger

# 初始化模組 logger
logger = get_module_logger(__name__)

# 使用日誌
logger.debug("調試信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("錯誤信息", exc_info=True)  # 包含異常堆疊
logger.critical("嚴重錯誤")
```

### 專門的日誌方法

```python
# 記錄 API 調用
logger.log_api_call(
    api_name="gemini",
    method="generate",
    params={"prompt": "..."},
    response=response_data,
    duration=0.5
)

# 記錄異常
try:
    # 一些操作
except Exception as e:
    logger.log_exception(e, context={"user_id": 123})

# 記錄性能
logger.log_performance("database_query", duration=0.123)

# 記錄用戶操作
logger.log_user_action("submit_practice", user_input="...", result="success")
```

### 配置環境變數

```bash
# .env 檔案
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs            # 日誌目錄
LOG_TO_CONSOLE=true     # 是否輸出到控制台
LOG_TO_FILE=true        # 是否輸出到檔案
LOG_FORMAT=text         # text 或 json
ENV=development         # development 或 production

# 日誌輪轉設定
LOG_ROTATE_DAILY=false  # 是否按日輪轉
LOG_MAX_BYTES=10485760  # 檔案大小限制（預設 10MB）
LOG_BACKUP_COUNT=5      # 保留備份數量
```

### 日誌裝飾器

```python
from core.logger import log_function_call

@log_function_call()
def process_data(data):
    # 自動記錄函數調用、參數、返回值和異常
    return data
```

## JavaScript 日誌系統

### 快速開始

```javascript
// 獲取 logger
const logger = window.getLogger('module-name');

// 使用日誌
logger.debug('調試信息', { data: 'value' });
logger.info('一般信息');
logger.warning('警告信息');
logger.error('錯誤信息');
logger.critical('嚴重錯誤');
```

### 專門的日誌方法

```javascript
// 記錄 API 調用
logger.logApiCall('GET', '/api/data', options, response, error);

// 記錄用戶操作
logger.logUserAction('button_click', { 
    button: 'submit',
    form: 'practice'
});

// 記錄性能
const startTime = Date.now();
// ... 一些操作
logger.logPerformance('render_page', startTime);
```

### 配置選項

```javascript
// 創建自定義配置的 logger
const logger = window.getLogger('my-module', {
    logLevel: 'DEBUG',        // 日誌級別
    enableConsole: true,      // 輸出到控制台
    enableRemote: false,      // 發送到後端
    remoteEndpoint: '/api/logs',
    bufferSize: 10,          // 緩衝區大小
    flushInterval: 5000      // 刷新間隔（毫秒）
});
```

### 全局配置

```javascript
// 設置全局日誌級別
window.setLogLevel('WARNING');

// 啟用遠端日誌
window.enableRemoteLogging('/api/logs');
```

## 日誌級別

| 級別 | 數值 | 用途 |
|------|------|------|
| DEBUG | 10 | 詳細的調試信息 |
| INFO | 20 | 一般信息性消息 |
| WARNING | 30 | 警告但不影響功能 |
| ERROR | 40 | 錯誤但系統可恢復 |
| CRITICAL | 50 | 嚴重錯誤需立即處理 |

## 生產環境 vs 開發環境

### 開發環境（預設）
- 日誌級別：DEBUG
- 輸出到控制台：是
- 輸出到檔案：否
- 格式：文字（彩色）

### 生產環境
- 日誌級別：WARNING
- 輸出到控制台：否
- 輸出到檔案：是
- 格式：JSON
- 自動輪轉：啟用

## 日誌檔案結構

```
logs/
├── web.log          # Web 服務日誌
├── core.log         # 核心功能日誌
├── ai.log           # AI 服務日誌
├── practice.log     # 練習功能日誌
└── knowledge.log    # 知識點管理日誌
```

## 敏感信息處理

系統會自動遮罩以下敏感信息：
- API keys
- Passwords
- Tokens
- Authorization headers
- 超過 32 字元的字串（部分遮罩）

## 最佳實踐

### 1. 選擇適當的日誌級別

```python
# ❌ 錯誤：所有都用 info
logger.info("開始處理")
logger.info("發生錯誤")  # 應該用 error
logger.info("性能很慢")   # 應該用 warning

# ✅ 正確：使用適當級別
logger.debug("開始處理")
logger.error("發生錯誤", exc_info=True)
logger.warning("操作耗時過長", duration=5.2)
```

### 2. 提供有用的上下文

```python
# ❌ 錯誤：缺乏上下文
logger.error("失敗")

# ✅ 正確：包含上下文
logger.error("用戶登入失敗", 
    user_id=user_id, 
    reason="密碼錯誤",
    ip_address=request.client.host
)
```

### 3. 使用專門的方法

```python
# ❌ 錯誤：手動格式化
logger.info(f"API 調用: {api_name}, 耗時: {duration}")

# ✅ 正確：使用專門方法
logger.log_api_call(api_name, method, params, response, duration=duration)
```

### 4. 避免在循環中記錄

```python
# ❌ 錯誤：循環中記錄
for item in items:
    logger.info(f"處理項目: {item}")
    
# ✅ 正確：批量記錄或使用 debug
logger.info(f"開始處理 {len(items)} 個項目")
for item in items:
    logger.debug(f"處理項目: {item}")  # 只在 debug 模式顯示
```

## 故障排除

### 日誌沒有輸出
1. 檢查日誌級別設定
2. 確認環境變數正確載入
3. 檢查檔案權限

### 日誌檔案過大
1. 啟用日誌輪轉
2. 調整 LOG_MAX_BYTES
3. 減少 LOG_BACKUP_COUNT

### 性能影響
1. 在生產環境使用 WARNING 級別
2. 避免在熱路徑記錄
3. 使用異步日誌（如需要）

## 監控和分析

### 查看日誌統計

```bash
# 統計錯誤數量
grep ERROR logs/*.log | wc -l

# 查看最近的錯誤
tail -f logs/web.log | grep ERROR

# JSON 格式分析
cat logs/ai.log | jq '.level == "ERROR"'
```

### 日誌聚合

建議使用以下工具進行日誌聚合和分析：
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Grafana Loki
- CloudWatch (AWS)
- Stackdriver (GCP)

## 開發者工具

### Python 調試

```python
# 臨時調整日誌級別
from core.log_config import set_log_level
set_log_level("DEBUG")
```

### JavaScript 調試

```javascript
// 在瀏覽器控制台
setLogLevel('DEBUG');  // 設置日誌級別
enableRemoteLogging();  // 啟用遠端日誌

// 查看所有 logger
console.log(window.LogManager.loggers);
```

## 更新歷史

- 2024-12-11: 初始版本，統一 Python 和 JavaScript 日誌系統
- 支援彩色控制台輸出
- 支援 JSON 格式輸出
- 自動敏感信息遮罩
- 日誌輪轉和備份