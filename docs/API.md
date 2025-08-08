# API 文檔

## 核心模組 API

### AIService 類別

位置：`core/ai_service.py`

#### 初始化

```python
from core.ai_service import AIService

service = AIService(api_key="your_api_key", model="gemini-2.0-flash-exp")
```

#### 方法

##### check_translation(chinese, english)

檢查英文翻譯的正確性。

**參數：**
- `chinese` (str): 中文句子
- `english` (str): 用戶的英文翻譯

**返回：**
```python
{
    "is_correct": bool,
    "feedback": {
        "score": int,  # 0-100
        "errors": [
            {
                "type": str,  # systematic/isolated/enhancement/other
                "description": str,
                "correction": str,
                "severity": str  # high/medium/low
            }
        ],
        "correct_answer": str,
        "explanation": str,
        "suggestions": [str]
    },
    "knowledge_points": [
        {
            "key_point": str,
            "category": str,
            "subtype": str,
            "explanation": str,
            "examples": [str]
        }
    ]
}
```

**異常：**
- `GeminiAPIException`: API 調用失敗
- `ValidationException`: 參數驗證失敗

**範例：**
```python
result = service.check_translation(
    chinese="他每天跑步",
    english="He run every day"
)

if not result["is_correct"]:
    print(f"Score: {result['feedback']['score']}")
    for error in result['feedback']['errors']:
        print(f"- {error['description']}")
```

##### analyze_errors(errors)

分析錯誤並提取知識點。

**參數：**
- `errors` (list): 錯誤列表

**返回：**
```python
{
    "summary": str,
    "priority_errors": [str],
    "learning_focus": str,
    "practice_suggestions": [str]
}
```

### KnowledgeManager 類別

位置：`core/knowledge.py`

#### 初始化

```python
from core.knowledge import KnowledgeManager

manager = KnowledgeManager(data_path="data/knowledge.json")
```

#### 方法

##### add_knowledge_point(knowledge_data)

添加新的知識點。

**參數：**
```python
knowledge_data = {
    "key_point": str,
    "category": str,  # systematic/isolated/enhancement/other
    "subtype": str,
    "explanation": str,
    "examples": [dict]
}
```

**返回：**
- `int`: 新知識點的 ID

**異常：**
- `ValidationException`: 數據格式錯誤
- `DataException`: 數據保存失敗

##### update_mastery(point_id, is_correct)

更新知識點的掌握度。

**參數：**
- `point_id` (int): 知識點 ID
- `is_correct` (bool): 是否答對

**返回：**
```python
{
    "new_mastery": float,  # 0.0-1.0
    "change": float,
    "next_review": str  # ISO 格式日期
}
```

##### get_review_items(limit=10)

獲取需要複習的知識點。

**參數：**
- `limit` (int): 最大返回數量

**返回：**
```python
[
    {
        "id": int,
        "key_point": str,
        "category": str,
        "mastery_level": float,
        "last_review": str,
        "priority": int
    }
]
```

##### get_statistics()

獲取學習統計數據。

**返回：**
```python
{
    "total_points": int,
    "by_category": {
        "systematic": int,
        "isolated": int,
        "enhancement": int,
        "other": int
    },
    "mastery_distribution": {
        "beginner": int,     # < 0.3
        "intermediate": int,  # 0.3-0.5
        "advanced": int,     # 0.5-0.7
        "expert": int        # > 0.7
    },
    "total_practices": int,
    "correct_rate": float,
    "recent_progress": float  # 最近7天的進步率
}
```

### ErrorClassifier 類別

位置：`core/error_classifier.py`

#### 初始化

```python
from core.error_classifier import ErrorClassifier

classifier = ErrorClassifier()
```

#### 方法

##### classify(error_description)

分類錯誤類型。

**參數：**
- `error_description` (str): 錯誤描述

**返回：**
```python
{
    "category": str,  # systematic/isolated/enhancement/other
    "subtype": str,
    "confidence": float,  # 0.0-1.0
    "reasoning": str
}
```

##### get_priority(error_type)

獲取錯誤類型的優先級。

**參數：**
- `error_type` (str): 錯誤類型

**返回：**
- `int`: 優先級（1最高，4最低）

### Logger API

位置：`core/logger.py`

#### 獲取日誌器

```python
from core.logger import get_logger

logger = get_logger("module_name")
```

#### 日誌級別

```python
logger.debug("調試信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("錯誤信息")
logger.critical("嚴重錯誤")
```

#### 結構化日誌

```python
logger.info("Processing translation", extra={
    "user_id": 123,
    "sentence_id": 456,
    "difficulty": 2
})
```

#### 函數裝飾器

```python
from core.logger import log_function_call

@log_function_call(logger)
def my_function(param1, param2):
    # 自動記錄函數調用和執行時間
    return result
```

### 異常 API

位置：`core/exceptions.py`

#### 基礎異常

```python
from core.exceptions import LinkerException

try:
    # 代碼
except LinkerException as e:
    print(f"Error Code: {e.error_code}")
    print(f"Message: {e.message}")
    print(f"Details: {e.details}")
```

#### 特定異常

```python
from core.exceptions import (
    GeminiAPIException,
    DataException,
    ValidationException,
    ConfigException
)

# API 異常
raise GeminiAPIException(
    message="API call failed",
    model="gemini-2.0-flash-exp",
    prompt="..."
)

# 數據異常
raise DataException(
    message="Failed to load data",
    data_type="knowledge",
    file_path="data/knowledge.json"
)

# 驗證異常
raise ValidationException(
    message="Invalid input",
    field="email",
    value="invalid-email",
    expected="valid email format"
)

# 配置異常
raise ConfigException(
    message="Missing configuration",
    config_key="GEMINI_API_KEY",
    config_file="settings.py"
)
```

## 配置 API

位置：`settings.py`

### 訪問配置

```python
from settings import settings

# 顯示配置
max_items = settings.display.MAX_DISPLAY_ITEMS
separator = settings.display.SEPARATOR_LINE

# 學習配置
mastery_increment = settings.learning.MASTERY_INCREMENTS["systematic"]
review_interval = settings.learning.REVIEW_INTERVALS["short"]

# 緩存配置
cache_ttl = settings.cache.CACHE_TTL_SECONDS

# API 配置
model = settings.api.DEFAULT_MODEL
timeout = settings.api.REQUEST_TIMEOUT

# 日誌配置
log_level = settings.log.LEVEL
log_format = settings.log.FILE_FORMAT
```

### 動態修改配置

```python
from settings import settings

# 修改配置（僅在運行時有效）
settings.display.MAX_DISPLAY_ITEMS = 20
settings.cache.CACHE_TTL_SECONDS = 600
```

### 環境變數覆蓋

```python
import os

# 通過環境變數覆蓋配置
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["GEMINI_MODEL"] = "gemini-pro"
os.environ["CACHE_TTL"] = "600"
```

## 數據格式 API

### Knowledge Point

```python
knowledge_point = {
    "id": int,
    "key_point": str,
    "category": str,
    "subtype": str,
    "explanation": str,
    "mastery_level": float,  # 0.0-1.0
    "mistake_count": int,
    "correct_count": int,
    "last_review": str,  # ISO format
    "next_review": str,  # ISO format
    "examples": [
        {
            "chinese": str,
            "correct": str,
            "user_answer": str,
            "timestamp": str
        }
    ],
    "created_at": str,
    "updated_at": str
}
```

### Practice Log

```python
practice_log = {
    "session_id": str,
    "timestamp": str,
    "difficulty": int,  # 1-3
    "chinese_sentence": str,
    "user_answer": str,
    "correct_answer": str,
    "is_correct": bool,
    "errors": [
        {
            "type": str,
            "description": str,
            "correction": str,
            "severity": str
        }
    ],
    "knowledge_points": [int],  # IDs
    "feedback": {
        "score": int,
        "summary": str,
        "suggestions": [str]
    },
    "time_spent": int,  # seconds
    "attempt_count": int
}
```

## 錯誤碼參考

| 錯誤碼 | 說明 | 處理建議 |
|--------|------|----------|
| API_ERROR | API 調用失敗 | 檢查網絡和 API Key |
| DATA_ERROR | 數據處理錯誤 | 檢查文件格式和權限 |
| VALIDATION_ERROR | 輸入驗證失敗 | 檢查輸入格式 |
| CONFIG_ERROR | 配置錯誤 | 檢查配置文件 |
| FILE_ERROR | 文件操作錯誤 | 檢查文件權限 |
| PARSE_ERROR | 解析錯誤 | 檢查數據格式 |
| INPUT_ERROR | 用戶輸入錯誤 | 提示正確格式 |
| UNKNOWN_ERROR | 未知錯誤 | 查看詳細日誌 |

## 最佳實踐

### 錯誤處理

```python
from core.exceptions import LinkerException
from core.logger import get_logger

logger = get_logger(__name__)

def safe_operation():
    try:
        # 危險操作
        result = risky_operation()
        return result
    except LinkerException as e:
        logger.error(f"Known error: {e}")
        # 優雅處理
        return default_value
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        # 包裝為應用異常
        raise LinkerException(
            message="Operation failed",
            error_code="UNKNOWN_ERROR",
            details={"original_error": str(e)}
        )
```

### 日誌記錄

```python
from core.logger import get_logger, log_function_call

logger = get_logger(__name__)

@log_function_call(logger)
def process_data(data):
    logger.debug(f"Processing {len(data)} items")
    
    for i, item in enumerate(data):
        try:
            result = process_item(item)
            logger.debug(f"Item {i} processed successfully")
        except Exception as e:
            logger.error(f"Failed to process item {i}: {e}")
            
    logger.info(f"Completed processing {len(data)} items")
```

### 配置使用

```python
from settings import settings
from functools import lru_cache

@lru_cache(maxsize=settings.cache.MAX_CACHE_SIZE)
def expensive_operation(param):
    # 使用配置控制緩存大小
    return result

def display_results(results):
    # 使用配置控制顯示數量
    for i, result in enumerate(results[:settings.display.MAX_DISPLAY_ITEMS]):
        print(f"{i+1}. {result}")
    
    if len(results) > settings.display.MAX_DISPLAY_ITEMS:
        print(f"... 還有 {len(results) - settings.display.MAX_DISPLAY_ITEMS} 項")
```