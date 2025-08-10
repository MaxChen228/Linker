# Linker 專案文檔

## 專案概述
Linker 是一個英文翻譯練習系統，使用 Gemini API 進行智能出題和批改。系統採用 FastAPI + Jinja2 模板的 SSR 架構。

> **完整交接文檔**: 請參閱 [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md) 獲取詳細的專案交接資訊  
> **設計系統文檔**: 請參閱 [docs/DESIGN-SYSTEM-COMPLETE.md](docs/DESIGN-SYSTEM-COMPLETE.md) 了解 UI 設計規範

## 系統架構

### 後端核心模組
- **web/main.py**: FastAPI 主程式，處理路由和請求
- **core/ai_service.py**: AI 服務封裝，管理 Gemini API 調用
- **core/knowledge.py**: 知識點管理系統，處理錯誤追蹤和複習排程
- **core/error_types.py**: 錯誤分類系統定義

### 前端頁面
- **練習頁面** (/practice): 主要練習介面，支援新題和複習兩種模式
- **知識點頁面** (/knowledge): 查看所有錯誤知識點，分類展示
- **文法句型頁面** (/patterns): 文法資料庫瀏覽

## 核心功能

### 1. 智能出題系統
- **新題模式**: 使用 Gemini 2.5-flash 動態生成練習題
- **複習模式**: 基於錯誤知識點智能生成複習題
- 根據句子長度自動決定知識點數量：
  - 短/中句：1個知識點
  - 長句：2個知識點

### 2. 批改系統
- 使用 Gemini 2.5-pro 進行高品質批改
- 四級錯誤分類：
  - 系統性錯誤：文法規則類
  - 單一性錯誤：需個別記憶
  - 可以更好：表達優化建議
  - 其他錯誤：其他類型

### 3. 知識點管理
- 自動提取和分類錯誤知識點
- 掌握度追蹤（基於正確/錯誤次數）
- 智能複習排程（間隔重複算法）
- 複習優先級排序

### 4. LLM 調試功能
- 查看完整的 AI 對話內容
- 顯示輸入 prompt 和輸出 response
- 模型配置參數展示
- 一鍵複製功能

## 技術特點

### AI 優化策略
1. **Token 優化**: Python 端預處理，減少傳給 AI 的資訊量
2. **隨機性控制**: 在程式端控制隨機選擇，不依賴 AI
3. **溫度調整**: 生成模型使用 temperature=1.0 增加創意
4. **簡化 Prompt**: 清晰簡潔的指令，避免冗餘

### 前端互動
- 即時搜尋和篩選
- 平滑的動畫效果
- 響應式設計
- 自動草稿儲存

## 開發指引

### 環境變數
```bash
GEMINI_API_KEY=your_api_key
GEMINI_GENERATE_MODEL=gemini-2.5-flash  # 可選，預設值
GEMINI_GRADE_MODEL=gemini-2.5-pro       # 可選，預設值
```

### 啟動專案
```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動開發伺服器
uvicorn web.main:app --reload --port 8000
```

### 測試指令
```bash
# 執行 lint 檢查
ruff check .

# 執行型別檢查
mypy .
```

## 最近更新 (2024-12)

### 複習功能整合
- 整合複習模式到練習頁面
- 智能選擇待複習知識點
- 知識點連結功能，可跳轉查看詳情

### AI 互動優化
- 改進知識點選擇邏輯
- 減少 token 消耗
- 提升出題變化性

### 調試工具
- 新增 LLM 對話查看功能
- 完整的 prompt/response 展示
- 便利的複製和分析工具

## 注意事項
- 所有錯誤資料儲存在本地 `data/` 目錄
- 知識點資料會自動持久化
- API 調用有快取機制（部分功能）