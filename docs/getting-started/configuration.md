# 配置指南

## 配置概述

Linker 使用分層配置系統，優先級從高到低：
1. 環境變數
2. `.env` 檔案
3. `settings.py` 預設值

## 環境變數配置

### 必需配置

| 變數名 | 說明 | 範例 |
|--------|------|------|
| `GEMINI_API_KEY` | Google Gemini API 金鑰 | `AIza...` |

### 可選配置

#### AI 模型設定
| 變數名 | 預設值 | 說明 |
|--------|--------|------|
| `GEMINI_GENERATE_MODEL` | `gemini-2.5-flash` | 生成模型 |
| `GEMINI_GRADE_MODEL` | `gemini-2.5-pro` | 批改模型 |
| `MAX_OUTPUT_TOKENS` | `3000` | 最大輸出 token 數 |
| `TEMPERATURE` | `0.7` | 生成溫度 (0-1) |

#### 日誌設定
| 變數名 | 預設值 | 說明 |
|--------|--------|------|
| `LOG_LEVEL` | `INFO` | 日誌級別 (DEBUG/INFO/WARNING/ERROR) |
| `LOG_DIR` | `logs` | 日誌目錄 |
| `LOG_TO_CONSOLE` | `true` | 是否輸出到控制台 |
| `LOG_TO_FILE` | `false` | 是否輸出到檔案 |
| `LOG_FORMAT` | `text` | 日誌格式 (text/json) |

#### 應用設定
| 變數名 | 預設值 | 說明 |
|--------|--------|------|
| `ENV` | `development` | 環境 (development/production) |
| `PORT` | `8000` | Web 服務端口 |
| `HOST` | `127.0.0.1` | 綁定地址 |

## 配置檔案

### .env 檔案範例

```env
# API Keys
GEMINI_API_KEY=your_key_here

# Environment
ENV=development
PORT=8000

# Logging
LOG_LEVEL=DEBUG
LOG_TO_FILE=true

# AI Models
GEMINI_GENERATE_MODEL=gemini-2.5-flash
TEMPERATURE=0.8
```

### settings.py 結構

```python
settings/
├── learning:      # 學習相關配置
│   ├── DIFFICULTY_LEVELS
│   ├── MASTERY_THRESHOLDS
│   └── REVIEW_INTERVALS
├── display:       # 顯示相關配置
│   ├── MAX_EXAMPLES_PER_POINT
│   └── SEPARATOR_LINE
└── api:          # API 相關配置
    ├── DEFAULT_TIMEOUT
    └── RETRY_COUNT
```

## 進階配置

### 生產環境配置

```env
ENV=production
LOG_LEVEL=WARNING
LOG_TO_FILE=true
LOG_TO_CONSOLE=false
LOG_FORMAT=json
```

### 開發環境配置

```env
ENV=development
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=true
LOG_FORMAT=text
```

### Docker 配置

```dockerfile
ENV GEMINI_API_KEY=${GEMINI_API_KEY}
ENV ENV=production
ENV PORT=8000
```

## 配置驗證

執行以下命令驗證配置：

```bash
# 檢查環境變數
python -c "from settings import settings; print(settings)"

# 測試 API 連接
python -c "from core.ai_service import AIService; AIService()"
```

## 故障排除

### 問題：API Key 無效
```bash
export GEMINI_API_KEY="your_actual_key"  # 確保沒有多餘空格
```

### 問題：日誌不顯示
```bash
export LOG_LEVEL=DEBUG
export LOG_TO_CONSOLE=true
```

### 問題：Port 已被佔用
```bash
export PORT=8001  # 使用其他端口
```

## 相關文檔

- [安裝指南](installation.md)
- [日誌系統](../reference/logging.md)
- [API 參考](../reference/api.md)

---

> ⚠️ **重要**: 不要將包含真實 API Key 的 `.env` 檔案提交到版本控制系統。