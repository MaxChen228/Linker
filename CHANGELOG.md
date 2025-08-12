# 變更日誌

所有重要的專案變更都將記錄在此文件中。

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
並且本專案遵循 [語意化版本](https://semver.org/lang/zh-TW/)。

## [2.6.0] - 2025-01-12

### 文字系統深度改造

實現完整的三層文字系統架構，大幅提升設計一致性和開發效率。

### 新增
- **完整的文字系統**：
  - 12 個字體大小變數 (10px - 60px)
  - 9 個字重選項 (100 - 900)
  - 4 個行高變數 (1.25 - 2.0)
  - 3 個字距選項
  - 2 個字體系列 (Sans, Mono)
- **三層架構設計**：
  - 原始值層：基礎文字令牌
  - 語義組合層：有意義的文字組合
  - 組件應用層：特定組件樣式
- **測試工具**：
  - 完整的文字系統測試頁面
  - 中英混排測試
  - 響應式文字效果展示
  - 系統統計和改進建議

### 改進
- **系統重構**：
  - 替換 80+ 個硬編碼文字值
  - 統一 47 個檔案的文字樣式
  - 變數使用率從 66.7% 提升至 95%+
  - 建立統一的設計語言
- **開發體驗**：
  - 新增文字系統使用指南
  - 提供最佳實踐建議
  - 創建遷移指南
  - 包含響應式設計範例

### 文檔
- 新增 `docs/TYPOGRAPHY_SYSTEM_GUIDE.md` 完整使用指南
- 創建 `test_typography_system.html` 視覺測試頁面
- 更新設計系統文檔
- 提供中文優化建議

### 技術改進
- 支援響應式文字 (clamp() 函數)
- 優化中文顯示效果
- 提升可讀性和無障礙性
- 改善設計系統成熟度

## [2.5.1] - 2025-08-08

### 專案深度清理

本次更新執行深度清理，優化專案結構和文檔系統，同時保留所有新功能。

### 改進
- **文檔系統重組**：
  - 精簡 README.md 從 431 行至約 200 行
  - 創建 `docs/QUICK_START.md` 快速開始指南
  - 更新架構文檔以反映雙模型系統
  - 重構部署文檔，提供清晰的三層方案
- **代碼清理**：
  - 統一日誌輸出，移除 print 調試語句
  - 刪除過時的 `web/templates/reviews.html`
  - 移除測試腳本 `test_ai_format.py`
- **配置優化**：
  - 標準化環境變數命名
  - 統一部署配置文件格式

### 文檔
- 新增 `CLEANUP_SUMMARY.md` 清理總結報告
- 更新版本號至 2.5.1 反映清理工作

## [2.5.0] - 2025-08-08

### 新功能發布

實現雙模型系統和智能複習功能。

### 新增
- **雙模型架構**：
  - Gemini 2.5 Flash 負責快速出題
  - Gemini 2.5 Pro 負責精準批改
- **智能複習模式**：
  - 自動識別薄弱知識點
  - 針對性生成複習題目
  - 動態調整複習頻率
- **簡約 Web 界面**：
  - 響應式設計支援移動設備
  - 簡化的用戶交互流程
- **集中日誌監控**：
  - 統一的日誌管理系統
  - HTTP 訪問日誌記錄

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