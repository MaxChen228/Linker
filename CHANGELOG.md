# 變更日誌

所有重要的專案變更都將記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
並且本專案遵循 [語意化版本](https://semver.org/lang/zh-TW/)。

## [2.0.0] - 2025-08-08

### 重大重構版本

本次更新為專案的重大重構版本，大幅改善了代碼品質、可維護性和系統穩定性。

### 新增功能

#### 配置管理系統
- 創建 `settings.py` 統一管理所有配置項
- 實現配置類別：
  - `DisplaySettings` - 顯示相關配置
  - `LearningSettings` - 學習參數配置
  - `CacheSettings` - 緩存配置
  - `APISettings` - API 設定
  - `LogSettings` - 日誌配置
  - `DataSettings` - 數據路徑配置
- 消除所有魔術數字，提升代碼可讀性
- 支援環境變數覆蓋配置

#### 異常處理系統
- 創建 `core/exceptions.py` 實現統一異常處理
- 設計異常層級結構：
  - `LinkerException` - 基礎異常類
  - `APIException` - API 調用異常
  - `GeminiAPIException` - Gemini 特定異常
  - `DataException` - 數據處理異常
  - `ValidationException` - 數據驗證異常
  - `ConfigException` - 配置錯誤
  - `FileOperationException` - 文件操作異常
  - `ParseException` - 解析錯誤
  - `UserInputException` - 用戶輸入異常
- 每個異常都包含錯誤碼、詳細信息和上下文

#### 日誌系統
- 創建 `core/logger.py` 實現完整日誌功能
- 功能特性：
  - 控制台彩色輸出（ColoredFormatter）
  - 文件輸出支援純文本和 JSON 格式
  - 自動日誌輪轉（按日期分割）
  - 函數調用裝飾器（@log_function_call）
  - 性能監控功能
  - 支援多個日誌級別（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 日誌配置可通過環境變數調整

### 改進功能

#### 代碼重構
- **函數拆分**：
  - 將 `practice_translation` 拆分為多個小函數
  - 分離 `display_feedback` 函數處理反饋顯示
  - 改善單一職責原則
- **模組化改進**：
  - 統一導入方式
  - 減少模組間耦合
  - 提升代碼重用性

#### 錯誤處理改進
- 所有 API 調用都加入異常捕獲
- 提供更詳細的錯誤信息
- 實現優雅的錯誤恢復機制
- 避免程式因異常而崩潰

#### 性能優化
- 改進緩存機制
- 優化數據載入流程
- 減少不必要的 API 調用

### 文檔更新

- 全面更新 README.md，新增：
  - 系統架構說明
  - 配置管理指南
  - 異常處理說明
  - 日誌系統使用
  - 故障排除指南
  - 開發指南
- 創建 CHANGELOG.md（本文件）
- 添加 .gitignore 文件

### 破壞性變更

- 配置管理方式改變：
  - 舊版直接使用 `config.py` 中的常數
  - 新版需要通過 `settings` 物件訪問配置
  - 例如：`Config.CACHE_TTL` → `settings.cache.CACHE_TTL_SECONDS`

- 日誌輸出格式改變：
  - 新增結構化日誌格式
  - 日誌文件位置改為 `logs/` 目錄
  - 文件命名格式改為 `{logger_name}_{date}.log`

### 技術債清理

- 消除所有魔術數字
- 統一錯誤處理方式
- 改善代碼註釋和文檔
- 提升類型提示覆蓋率
- 清理未使用的導入和變數

### 已知問題

- 批量練習模式尚未實現（計劃在下個版本）
- 匯出功能尚未實現（計劃在下個版本）

### 遷移指南

從 1.x 版本升級到 2.0.0：

1. **更新環境變數**：
   ```bash
   # 新增的環境變數
   export LOG_LEVEL=INFO
   export LOG_TO_FILE=true
   export LOG_TO_CONSOLE=true
   export LOG_FORMAT=text  # 或 json
   ```

2. **更新配置引用**：
   ```python
   # 舊版
   from config import Config
   cache_ttl = Config.CACHE_TTL
   
   # 新版
   from settings import settings
   cache_ttl = settings.cache.CACHE_TTL_SECONDS
   ```

3. **更新異常處理**：
   ```python
   # 舊版
   try:
       # code
   except Exception as e:
       print(f"Error: {e}")
   
   # 新版
   from core.exceptions import LinkerException
   try:
       # code
   except LinkerException as e:
       logger.error(f"Application error: {e}")
   ```

4. **清理舊日誌文件**：
   - 刪除舊的日誌文件
   - 新日誌將存儲在 `logs/` 目錄

## [1.0.0] - 2024-12-01

### 初始版本

- 基本翻譯練習功能
- 簡單的錯誤分類
- 基礎知識點管理
- Gemini API 整合
- JSON 數據存儲

---

## 版本規劃

### [2.1.0] - 計劃中

預計新增功能：
- 批量練習模式
- 學習報告匯出（CSV, JSON, PDF）
- 視覺化統計圖表
- 自定義 AI 提示詞
- 知識點匯入/匯出

### [2.2.0] - 計劃中

預計新增功能：
- 網頁界面（可選）
- 多用戶支援
- 雲端同步
- 更多語言支援
- 語音輸入/輸出

---

**維護者**: [您的名字]  
**專案連結**: [GitHub Repository URL]