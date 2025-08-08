# Linker CLI - 智能英文翻譯學習系統

一個基於 AI 的終端翻譯學習工具，提供智能錯誤分析、知識點管理和個人化學習追蹤。

## 主要特色

- 🎯 **智能錯誤分類** - 基於學習策略的科學分類系統
- 🤖 **AI 即時批改** - 使用 Gemini API 提供詳細反饋
- 📊 **完整學習追蹤** - 記錄進度、掌握度和複習排程
- 🛡️ **健壯錯誤處理** - 統一異常處理和日誌系統
- ⚙️ **靈活配置管理** - 集中化配置，易於客製化
- 📝 **結構化日誌** - 支援控制台和文件輸出，JSON 格式可選

## 系統架構

### 專案結構

```
linker-cli/
├── linker_cli.py          # 主程式入口
├── settings.py            # 統一配置管理
├── config.py              # 舊版配置（向後兼容）
├── core/                  # 核心模組
│   ├── __init__.py
│   ├── ai_service.py      # Gemini API 整合
│   ├── knowledge.py       # 知識點管理系統
│   ├── error_classifier.py # 錯誤分類引擎
│   ├── error_types.py     # 錯誤類型定義
│   ├── exceptions.py      # 統一異常處理
│   └── logger.py          # 日誌系統
├── tests/                 # 單元測試
│   ├── __init__.py
│   ├── test_config.py     # 配置測試
│   ├── test_exceptions.py # 異常處理測試
│   ├── test_logger.py     # 日誌系統測試
│   └── test_settings.py   # 設定測試
├── data/                  # 數據存儲
│   ├── knowledge.json     # 知識點數據庫
│   ├── practice_log.json  # 練習記錄
│   ├── examples.json      # 例句庫
│   └── grammar.json       # 文法句型庫
├── logs/                  # 日誌文件（自動生成）
├── pyproject.toml         # 專案配置（Ruff、pytest）
├── requirements.txt       # 依賴清單
├── start.sh              # 快速啟動腳本
└── .gitignore            # Git 忽略配置
```

### 核心模組說明

#### 配置管理 (settings.py)
- **DisplaySettings**: 顯示相關配置（項目數量、分隔符等）
- **LearningSettings**: 學習參數（掌握度、複習間隔、閾值）
- **CacheSettings**: 緩存配置（TTL、大小限制）
- **APISettings**: API 設定（模型、超時、重試）
- **LogSettings**: 日誌配置（級別、格式、輸出）
- **DataSettings**: 數據路徑配置

#### 異常處理 (core/exceptions.py)
```
LinkerException (基礎異常)
├── APIException (API 調用異常)
│   └── GeminiAPIException (Gemini 特定異常)
├── DataException (數據處理異常)
├── ValidationException (數據驗證異常)
├── ConfigException (配置錯誤)
├── FileOperationException (文件操作異常)
├── ParseException (解析錯誤)
└── UserInputException (用戶輸入異常)
```

#### 日誌系統 (core/logger.py)
- 支援控制台彩色輸出
- 文件輸出（純文本或 JSON 格式）
- 自動日誌輪轉
- 函數調用裝飾器
- 性能監控

## 快速開始

### 安裝要求

- Python 3.8+
- pip 套件管理器

### 安裝步驟

1. **克隆專案**
```bash
git clone <repository-url>
cd linker-cli
```

2. **創建虛擬環境**（建議）
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安裝依賴**
```bash
pip install -r requirements.txt
```

4. **設定 API Key**
```bash
export GEMINI_API_KEY=your_api_key_here
```

5. **運行程式**
```bash
python linker_cli.py
# 或使用啟動腳本
./start.sh
```

## 配置說明

### 環境變數

| 變數名 | 說明 | 預設值 |
|--------|------|--------|
| GEMINI_API_KEY | Gemini API 金鑰 | 必須設定 |
| GEMINI_MODEL | 使用的模型 | gemini-2.0-flash-exp |
| LOG_LEVEL | 日誌級別 | INFO |
| LOG_TO_FILE | 是否寫入日誌文件 | true |
| LOG_TO_CONSOLE | 是否輸出到控制台 | true |
| LOG_FORMAT | 日誌格式 (text/json) | text |

### 配置文件

可以通過修改 `settings.py` 來調整系統行為：

```python
# 顯示設定
settings.display.MAX_DISPLAY_ITEMS = 10  # 最大顯示項目數

# 學習參數
settings.learning.MASTERY_INCREMENTS = {
    "systematic": 0.25,  # 系統性錯誤的掌握度提升
    "isolated": 0.20,    # 單一性錯誤的掌握度提升
}

# 緩存設定
settings.cache.CACHE_TTL_SECONDS = 300  # 緩存存活時間
```

## 功能詳解

### 1. 翻譯練習模式

- **難度選擇**: 初級、中級、高級三個等級
- **即時批改**: AI 分析翻譯並提供詳細反饋
- **錯誤分類**: 自動識別錯誤類型並記錄

### 2. 智能錯誤分類系統

| 類型 | 說明 | 優先級 | 學習策略 |
|------|------|--------|----------|
| 系統性錯誤 | 文法規則類錯誤 | 最高 | 需要系統學習規則 |
| 單一性錯誤 | 詞彙、搭配等 | 中等 | 需要個別記憶 |
| 可以更好 | 表達優化建議 | 較低 | 選擇性改進 |
| 其他錯誤 | 理解、漏譯等 | 中等 | 具體問題具體分析 |

### 3. 知識點管理

- **自動提取**: 從錯誤中自動提取知識點
- **掌握度追蹤**: 動態調整每個知識點的掌握程度
- **智能複習**: 根據遺忘曲線安排複習時間
- **分類管理**: 按錯誤類型和子類型組織

### 4. 學習統計

- 總練習次數和正確率
- 知識點分佈圖表
- 進步趨勢分析
- 高頻錯誤統計

### 5. 日誌系統

日誌文件位於 `logs/` 目錄，按日期自動分割：
- `linker_cli_YYYYMMDD.log` - 主程式日誌
- `knowledge_manager_YYYYMMDD.log` - 知識點管理日誌

## 數據格式規範

### 知識點格式 (knowledge.json)

```json
{
  "id": 1,
  "key_point": "主詞為第三人稱單數時，動詞需要加上 -s",
  "category": "systematic",
  "subtype": "verb_conjugation",
  "explanation": "詳細說明...",
  "mastery_level": 0.6,
  "mistake_count": 3,
  "correct_count": 2,
  "last_review": "2024-01-01T10:00:00",
  "next_review": "2024-01-04T10:00:00",
  "examples": [
    {
      "chinese": "他每天跑步",
      "correct": "He runs every day",
      "user_answer": "He run every day",
      "timestamp": "2024-01-01T10:00:00"
    }
  ]
}
```

### 練習記錄格式 (practice_log.json)

```json
{
  "session_id": "uuid",
  "timestamp": "2024-01-01T10:00:00",
  "difficulty": 2,
  "chinese_sentence": "他昨天去了圖書館",
  "user_answer": "He go to library yesterday",
  "correct_answer": "He went to the library yesterday",
  "is_correct": false,
  "errors": [
    {
      "type": "systematic",
      "description": "過去式動詞變化錯誤",
      "correction": "go → went"
    }
  ],
  "knowledge_points": [1, 2],
  "feedback": {
    "score": 60,
    "summary": "基本句意正確，但有文法錯誤",
    "suggestions": ["複習過去式動詞變化", "注意冠詞使用"]
  }
}
```

## 進階功能

### 自定義例句庫

編輯 `data/examples.json` 添加自己的練習句子：

```json
{
  "short": {
    "1": ["簡單句子1", "簡單句子2"],
    "2": ["中等句子1", "中等句子2"],
    "3": ["困難句子1", "困難句子2"]
  },
  "medium": {
    "1": ["中長句子1"],
    "2": ["中長句子2"],
    "3": ["中長句子3"]
  }
}
```

### 批量練習模式

可以一次載入多個句子進行練習：

```python
# 在主程式中使用批量模式
python linker_cli.py --batch --count 10
```

### 匯出學習報告

系統支援匯出詳細的學習報告：

```python
# 匯出 CSV 格式報告
python linker_cli.py --export csv --output report.csv

# 匯出 JSON 格式報告
python linker_cli.py --export json --output report.json
```

## 故障排除

### 常見問題

1. **API Key 錯誤**
   - 確認環境變數已正確設定
   - 檢查 API Key 是否有效

2. **日誌文件無法創建**
   - 確認有 logs/ 目錄的寫入權限
   - 手動創建 logs/ 目錄

3. **JSON 解析錯誤**
   - 檢查 data/ 目錄下的 JSON 文件格式
   - 運行測試確認解析功能正常

### 診斷工具

運行單元測試進行系統診斷：

```bash
python3 -m pytest tests/ -v
```

這將檢查：
- 所有模組是否正確載入
- 配置管理是否正常運作
- 異常處理機制是否完善
- 日誌系統是否正確配置
- 設定的保存和載入功能

## 開發指南

### 開發工具

本專案已配置以下開發工具，確保代碼品質：

#### Ruff - 代碼檢查與格式化
- 整合了多個 linting 工具（flake8、isort、pyupgrade 等）
- 自動排序 import 語句
- 執行檢查：`ruff check .`
- 自動修復：`ruff check --fix .`
- 格式化代碼：`ruff format .`

#### pytest - 單元測試框架
- 完整的測試覆蓋率支援
- 執行所有測試：`python3 -m pytest tests/`
- 執行特定測試：`python3 -m pytest tests/test_logger.py`
- 顯示詳細輸出：`python3 -m pytest -v tests/`
- 測試覆蓋率報告：`python3 -m pytest --cov=core tests/`

### 測試指南

#### 運行測試
```bash
# 運行所有單元測試
python3 -m pytest tests/

# 運行特定測試文件
python3 -m pytest tests/test_settings.py

# 運行並顯示測試覆蓋率
python3 -m pytest --cov=core --cov-report=term-missing tests/

# 運行標記的測試
python3 -m pytest -m unit tests/
```

#### 測試結構
- `tests/test_config.py` - 測試配置載入和管理
- `tests/test_exceptions.py` - 測試異常處理機制
- `tests/test_logger.py` - 測試日誌系統功能
- `tests/test_settings.py` - 測試設定管理

### 添加新的錯誤類型

1. 在 `core/error_types.py` 中定義新類型
2. 在 `settings.py` 中添加相關配置
3. 更新 `core/error_classifier.py` 的分類邏輯

### 擴展日誌功能

```python
from core.logger import get_logger, log_function_call

logger = get_logger("module_name")

@log_function_call(logger)
def my_function():
    logger.info("執行中...")
    # 函數邏輯
```

### 添加新的異常類型

```python
from core.exceptions import LinkerException

class MyCustomException(LinkerException):
    def __init__(self, message, custom_field):
        super().__init__(
            message=message,
            error_code="CUSTOM_ERROR",
            details={"custom_field": custom_field}
        )
```

## 貢獻指南

歡迎貢獻代碼！請遵循以下步驟：

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 代碼規範

- 遵循 PEP 8 Python 代碼風格（使用 Ruff 自動檢查）
- 使用類型提示 (Type Hints)
- 撰寫清晰的文檔字串
- 添加適當的單元測試（使用 pytest）
- 在提交前運行 `ruff check .` 和 `python3 -m pytest tests/`

## 授權

本專案基於 MIT 授權。詳見 LICENSE 文件。

## 致謝

- 感謝 Google Gemini API 提供強大的 AI 能力
- 基於原始 Linker 專案的核心概念開發

## 聯絡方式

如有問題或建議，請通過以下方式聯絡：

- 提交 Issue
- 發送 Pull Request
- Email: [您的郵箱]

---

**版本**: 2.0.0  
**最後更新**: 2025-08-08