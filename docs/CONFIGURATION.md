# 配置指南

## 概述

Linker CLI 使用分層配置系統，支援多種配置方式：

1. **預設配置** - 在 `settings.py` 中定義
2. **環境變數** - 覆蓋預設配置
3. **運行時配置** - 程式執行時動態修改

## 配置結構

### Settings 類別結構

```python
Settings
├── display: DisplaySettings      # 顯示相關
├── learning: LearningSettings    # 學習參數
├── cache: CacheSettings          # 緩存設定
├── api: APISettings              # API 配置
├── log: LogSettings              # 日誌設定
└── data: DataSettings            # 數據路徑
```

## 詳細配置項

### 顯示配置 (DisplaySettings)

| 配置項 | 預設值 | 說明 |
|--------|--------|------|
| MAX_DISPLAY_ITEMS | 10 | 列表最大顯示項目數 |
| MAX_EXAMPLES_PER_POINT | 5 | 每個知識點最多顯示例句數 |
| SEPARATOR_WIDTH | 50 | 分隔線寬度 |
| SEPARATOR_CHAR | "-" | 普通分隔符 |
| WIDE_SEPARATOR_CHAR | "=" | 寬分隔符 |

**使用範例：**
```python
from settings import settings

# 調整顯示項目數
settings.display.MAX_DISPLAY_ITEMS = 20

# 使用分隔線
print(settings.display.SEPARATOR_LINE)  # 50個 "-"
print(settings.display.WIDE_SEPARATOR_LINE)  # 50個 "="
```

### 學習配置 (LearningSettings)

#### 掌握度提升幅度

| 錯誤類型 | 預設值 | 說明 |
|----------|--------|------|
| systematic | 0.25 | 系統性錯誤答對時的提升 |
| isolated | 0.20 | 單一性錯誤答對時的提升 |
| enhancement | 0.15 | 可以更好類型答對時的提升 |
| other | 0.15 | 其他錯誤答對時的提升 |

#### 掌握度下降幅度

| 錯誤類型 | 預設值 | 說明 |
|----------|--------|------|
| systematic | 0.15 | 系統性錯誤答錯時的下降 |
| isolated | 0.10 | 單一性錯誤答錯時的下降 |
| other | 0.10 | 其他錯誤答錯時的下降 |

#### 複習間隔（天）

| 級別 | 預設值 | 說明 |
|------|--------|------|
| immediate | 1 | 立即複習 |
| short | 3 | 短期記憶 |
| medium | 7 | 中期記憶 |
| long | 14 | 長期記憶 |
| mastered | 30 | 已掌握 |

#### 掌握度閾值

| 級別 | 預設值 | 說明 |
|------|--------|------|
| beginner | 0.3 | 初學者 |
| intermediate | 0.5 | 中級 |
| advanced | 0.7 | 高級 |
| expert | 0.9 | 專家 |

**使用範例：**
```python
from settings import settings

# 獲取掌握度提升值
increment = settings.learning.MASTERY_INCREMENTS["systematic"]

# 判斷掌握級別
mastery = 0.65
if mastery >= settings.learning.MASTERY_THRESHOLDS["advanced"]:
    level = "高級"
elif mastery >= settings.learning.MASTERY_THRESHOLDS["intermediate"]:
    level = "中級"
else:
    level = "初級"

# 獲取複習間隔
if mastery < 0.3:
    days = settings.learning.REVIEW_INTERVALS["immediate"]
elif mastery < 0.5:
    days = settings.learning.REVIEW_INTERVALS["short"]
else:
    days = settings.learning.REVIEW_INTERVALS["medium"]
```

### 緩存配置 (CacheSettings)

| 配置項 | 預設值 | 說明 |
|--------|--------|------|
| CACHE_TTL_SECONDS | 300 | 緩存存活時間（秒） |
| MAX_CACHE_SIZE | 100 | 最大緩存項目數 |
| CACHE_KEY_LENGTH | 50 | 緩存鍵截取長度 |

**使用範例：**
```python
from settings import settings
from functools import lru_cache
from datetime import datetime, timedelta

# 使用緩存配置
@lru_cache(maxsize=settings.cache.MAX_CACHE_SIZE)
def expensive_operation(key):
    return compute_result(key)

# 檢查緩存是否過期
def is_cache_valid(timestamp):
    age = (datetime.now() - timestamp).seconds
    return age < settings.cache.CACHE_TTL_SECONDS
```

### API 配置 (APISettings)

| 配置項 | 預設值 | 說明 |
|--------|--------|------|
| DEFAULT_MODEL | gemini-2.0-flash-exp | 預設 AI 模型 |
| REQUEST_TIMEOUT | 30 | 請求超時時間（秒） |
| MAX_RETRIES | 3 | 最大重試次數 |
| RESPONSE_MIME_TYPE | application/json | 響應格式 |

**使用範例：**
```python
from settings import settings
import google.generativeai as genai

# 配置 AI 模型
model = genai.GenerativeModel(
    model_name=settings.api.DEFAULT_MODEL,
    generation_config={
        "response_mime_type": settings.api.RESPONSE_MIME_TYPE
    }
)

# 使用重試機制
for attempt in range(settings.api.MAX_RETRIES):
    try:
        response = make_api_call(timeout=settings.api.REQUEST_TIMEOUT)
        break
    except Exception as e:
        if attempt == settings.api.MAX_RETRIES - 1:
            raise
```

### 日誌配置 (LogSettings)

| 配置項 | 預設值 | 說明 |
|--------|--------|------|
| LEVEL | INFO | 日誌級別 |
| CONSOLE_OUTPUT | True | 是否輸出到控制台 |
| FILE_OUTPUT | True | 是否輸出到文件 |
| FILE_FORMAT | text | 文件格式 (text/json) |
| LOG_DIR | logs | 日誌目錄 |
| MAX_FILE_SIZE | 10485760 | 最大文件大小（10MB） |
| BACKUP_COUNT | 5 | 保留備份數量 |

**使用範例：**
```python
from settings import settings
from core.logger import get_logger

# 創建日誌器
logger = get_logger(
    name="my_module",
    log_dir=settings.log.LOG_DIR,
    log_level=settings.log.LEVEL,
    console_output=settings.log.CONSOLE_OUTPUT,
    file_output=settings.log.FILE_OUTPUT,
    json_format=(settings.log.FILE_FORMAT == "json")
)
```

### 數據配置 (DataSettings)

| 配置項 | 預設值 | 說明 |
|--------|--------|------|
| BASE_DIR | 專案根目錄 | 基礎目錄 |
| DATA_DIR | data | 數據目錄 |
| KNOWLEDGE_FILE | knowledge.json | 知識點文件 |
| PRACTICE_LOG_FILE | practice_log.json | 練習記錄文件 |
| GRAMMAR_PATTERNS_FILE | grammar_patterns.json | 文法句型文件 |
| EXAMPLES_MODULE | assets.py | 分級例句庫模組 |

**使用範例：**
```python
from settings import settings
import json

# 載入知識點數據
knowledge_path = settings.data.DATA_DIR / settings.data.KNOWLEDGE_FILE
with open(knowledge_path, 'r', encoding='utf-8') as f:
    knowledge_data = json.load(f)

# 保存練習記錄
log_path = settings.data.DATA_DIR / settings.data.PRACTICE_LOG_FILE
with open(log_path, 'w', encoding='utf-8') as f:
    json.dump(practice_data, f, ensure_ascii=False, indent=2)
```

## 環境變數配置

### 支援的環境變數

| 環境變數 | 對應配置 | 範例 |
|----------|----------|------|
| GEMINI_API_KEY | API 金鑰 | your_api_key |
| GEMINI_MODEL | API 模型 | gemini-2.0-flash-exp |
| LOG_LEVEL | 日誌級別 | DEBUG/INFO/WARNING/ERROR |
| LOG_TO_FILE | 是否寫文件 | true/false |
| LOG_TO_CONSOLE | 是否輸出控制台 | true/false |
| LOG_FORMAT | 日誌格式 | text/json |
| CACHE_TTL | 緩存時間 | 600 |
| MAX_DISPLAY_ITEMS | 顯示項目數 | 20 |

### 設定環境變數

#### Linux/Mac
```bash
# 臨時設定
export GEMINI_API_KEY="your_api_key"
export LOG_LEVEL="DEBUG"

# 永久設定（加入 ~/.bashrc 或 ~/.zshrc）
echo 'export GEMINI_API_KEY="your_api_key"' >> ~/.bashrc
echo 'export LOG_LEVEL="INFO"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows
```cmd
# 臨時設定
set GEMINI_API_KEY=your_api_key
set LOG_LEVEL=DEBUG

# 永久設定
setx GEMINI_API_KEY "your_api_key"
setx LOG_LEVEL "INFO"
```

### 使用 .env 文件（推薦）

創建 `.env` 文件：
```ini
# API 設定
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# 日誌設定
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_TO_CONSOLE=true
LOG_FORMAT=text

# 緩存設定
CACHE_TTL=300
MAX_CACHE_SIZE=100

# 顯示設定
MAX_DISPLAY_ITEMS=10
```

載入 .env 文件：
```python
from dotenv import load_dotenv
import os

# 載入 .env 文件
load_dotenv()

# 使用環境變數
api_key = os.getenv("GEMINI_API_KEY")
```

## 配置優先級

配置載入優先級（由高到低）：

1. **運行時修改** - 程式執行時直接修改
2. **環境變數** - 系統或 .env 文件設定
3. **配置文件** - settings.py 中的預設值

範例：
```python
# 1. 預設值（settings.py）
settings.display.MAX_DISPLAY_ITEMS = 10

# 2. 環境變數覆蓋
os.environ["MAX_DISPLAY_ITEMS"] = "20"
# 現在值為 20

# 3. 運行時修改
settings.display.MAX_DISPLAY_ITEMS = 30
# 現在值為 30
```

## 配置驗證

### 自動驗證

系統啟動時會自動驗證關鍵配置：

```python
def validate_config():
    """驗證配置完整性"""
    errors = []
    
    # 檢查 API Key
    if not os.getenv("GEMINI_API_KEY"):
        errors.append("Missing GEMINI_API_KEY")
    
    # 檢查數據目錄
    if not settings.data.DATA_DIR.exists():
        errors.append(f"Data directory not found: {settings.data.DATA_DIR}")
    
    # 檢查日誌目錄權限
    if not os.access(settings.log.LOG_DIR, os.W_OK):
        errors.append(f"No write permission for log directory: {settings.log.LOG_DIR}")
    
    if errors:
        raise ConfigException("Configuration validation failed", errors=errors)
```

### 手動驗證

```python
from settings import settings

# 檢查配置值
def check_settings():
    print("=== 配置檢查 ===")
    print(f"API Model: {settings.api.DEFAULT_MODEL}")
    print(f"Log Level: {settings.log.LEVEL}")
    print(f"Cache TTL: {settings.cache.CACHE_TTL_SECONDS}s")
    print(f"Data Dir: {settings.data.DATA_DIR}")
    
    # 驗證範圍
    assert 0 < settings.cache.CACHE_TTL_SECONDS <= 3600
    assert settings.display.MAX_DISPLAY_ITEMS > 0
    assert settings.api.MAX_RETRIES >= 1
```

## 配置最佳實踐

### 1. 使用環境變數保護敏感信息

```python
# 不要這樣做
API_KEY = "sk-1234567890abcdef"  # 硬編碼

# 應該這樣做
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ConfigException("GEMINI_API_KEY not set")
```

### 2. 提供合理的預設值

```python
# 設定預設值避免程式崩潰
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
```

### 3. 分組相關配置

```python
@dataclass
class DatabaseSettings:
    """數據庫相關配置"""
    host: str = "localhost"
    port: int = 5432
    name: str = "linker"
    pool_size: int = 10
```

### 4. 配置文檔化

```python
@dataclass
class APISettings:
    """
    API 相關配置
    
    Attributes:
        DEFAULT_MODEL: 預設使用的 Gemini 模型
        REQUEST_TIMEOUT: API 請求超時時間（秒）
        MAX_RETRIES: 失敗重試次數
    """
    DEFAULT_MODEL: str = "gemini-2.0-flash-exp"
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
```

### 5. 配置測試

```python
import pytest
from settings import settings

def test_default_settings():
    """測試預設配置"""
    assert settings.display.MAX_DISPLAY_ITEMS == 10
    assert settings.cache.CACHE_TTL_SECONDS == 300
    assert settings.api.MAX_RETRIES == 3

def test_env_override():
    """測試環境變數覆蓋"""
    os.environ["MAX_DISPLAY_ITEMS"] = "20"
    # 重新載入設定
    from settings import settings
    assert settings.display.MAX_DISPLAY_ITEMS == 20
```

## 常見問題

### Q1: 如何在不同環境使用不同配置？

創建環境特定的配置文件：

```python
# config/development.py
LOG_LEVEL = "DEBUG"
CACHE_TTL = 60

# config/production.py
LOG_LEVEL = "WARNING"
CACHE_TTL = 3600

# 主程式
import os
env = os.getenv("ENV", "development")
if env == "production":
    from config.production import *
else:
    from config.development import *
```

### Q2: 如何動態重載配置？

```python
def reload_config():
    """重新載入配置"""
    import importlib
    import settings
    importlib.reload(settings)
    return settings.settings
```

### Q3: 如何驗證用戶自定義配置？

```python
def validate_user_config(config_dict):
    """驗證用戶配置"""
    schema = {
        "display": {
            "MAX_DISPLAY_ITEMS": (int, lambda x: 1 <= x <= 100),
        },
        "cache": {
            "CACHE_TTL_SECONDS": (int, lambda x: 0 < x <= 3600),
        }
    }
    
    for section, items in schema.items():
        for key, (type_, validator) in items.items():
            value = config_dict.get(section, {}).get(key)
            if value is not None:
                if not isinstance(value, type_):
                    raise ValueError(f"{section}.{key} must be {type_}")
                if not validator(value):
                    raise ValueError(f"{section}.{key} validation failed")
```