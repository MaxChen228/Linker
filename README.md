# Linker - 智能英文翻譯學習系統

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基於 AI 的智能翻譯學習平台，使用 Google Gemini AI 提供即時批改、錯誤分析和個人化學習追蹤。

## 核心特色

### 🚀 最新功能 (v2.5)
- **雙模型系統** - Gemini 2.5 Flash 出題 + 2.5 Pro 精準批改
- **智能複習** - 自動識別薄弱知識點並生成針對性題目
- **簡約 Web 界面** - 響應式設計，支援手機/平板訪問
- **集中監控** - 統一日誌系統，實時追蹤學習進度

### 📚 學習功能
- **智能錯誤分類** - 四級錯誤分類系統（系統性/單一性/優化/其他）
- **知識點管理** - 自動提取、追蹤掌握度、智能排程複習
- **分級練習** - 5個難度等級，3種句子長度
- **即時反饋** - 詳細錯誤分析與改進建議

## 快速開始

### 方式一：Web 界面（推薦）

```bash
# 1. 克隆專案
git clone <repository-url>
cd linker-cli

# 2. 設置 API Key
export GEMINI_API_KEY="your-api-key"

# 3. 啟動 Web 服務
./run.sh
# 訪問 http://localhost:8000
```

### 方式二：Docker 部署

```bash
# 1. 構建並啟動
docker-compose up -d

# 2. 訪問 http://localhost:8000
```

### 方式三：命令行界面

```bash
# 啟動 CLI 版本
./start.sh
```

## 系統架構

```
linker/
├── web/                   # Web 界面
│   ├── main.py           # FastAPI 應用
│   ├── static/           # 靜態資源
│   └── templates/        # HTML 模板
├── core/                 # 核心模組
│   ├── ai_service.py     # 雙模型 AI 服務
│   ├── knowledge.py      # 知識點管理
│   ├── error_types.py    # 錯誤分類系統
│   └── logger.py         # 統一日誌
├── data/                 # 數據存儲
│   ├── knowledge.json    # 知識點數據
│   └── practice_log.json # 練習記錄
├── docker-compose.yml    # Docker 配置
├── render.yaml          # Render 部署配置
└── requirements.txt     # 依賴清單
```

## 環境配置

### 必要條件
- Python 3.8+ 或 Docker
- Gemini API Key（[申請地址](https://makersuite.google.com/app/apikey)）

### 環境變數

創建 `.env` 文件：

```bash
# AI 模型配置
GEMINI_API_KEY=your-api-key
GEMINI_GENERATE_MODEL=gemini-2.5-flash  # 出題模型
GEMINI_GRADE_MODEL=gemini-2.5-pro       # 批改模型

# 日誌配置
LOG_LEVEL=INFO
LOG_TO_FILE=true
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

## 核心功能

### 1. 智能出題系統
- **新題模式**: Gemini 2.5 Flash 根據難度生成練習題
- **複習模式**: 針對薄弱知識點生成強化練習
- **難度分級**: 5個級別（國中基礎到高階挑戰）
- **句長選擇**: 短句、中句、長句

### 2. 精準批改系統
- **Pro 級批改**: Gemini 2.5 Pro 提供專業級錯誤分析
- **四級分類**: 系統性/單一性/優化建議/其他錯誤
- **即時反饋**: 詳細說明每個錯誤並提供改進建議
- **知識點提取**: 自動識別並記錄學習要點

### 3. 知識管理系統
- **自動追蹤**: 記錄所有錯誤並建立知識圖譜
- **掌握度計算**: 基於答題表現動態調整
- **複習排程**: 依據艾賓浩斯遺忘曲線安排
- **群組分析**: 系統性錯誤自動分組展示

### 4. 學習分析
- **統計儀表板**: 練習次數、正確率、進步趨勢
- **錯誤熱圖**: 識別高頻錯誤類型
- **複習佇列**: 顯示待複習和已到期知識點
- **即時日誌**: 集中監控所有學習活動

## 部署選項

### 局域網部署
```bash
# 讓其他設備訪問
./run-network.sh
# 手機/平板訪問: http://192.168.x.x:8000
```

### 雲端部署

#### Render (推薦)
1. Fork 專案到 GitHub
2. 在 [Render](https://render.com) 連接倉庫
3. 添加環境變數 `GEMINI_API_KEY`
4. 自動部署完成

#### Railway
1. 安裝 Railway CLI
2. 執行 `railway up`
3. 設置環境變數

#### Docker
```bash
docker-compose up -d
```

## 技術特色

### 雙模型架構
- **出題模型**: Gemini 2.5 Flash - 快速、創意、低成本
- **批改模型**: Gemini 2.5 Pro - 精準、專業、高品質
- **智能切換**: 根據任務自動選擇最適合的模型

### 響應式設計
- **跨平台**: 支援桌面、平板、手機
- **簡約 UI**: 專注學習，減少干擾
- **即時更新**: Ajax 無刷新交互

### 數據持久化
- **本地存儲**: JSON 格式，易於備份
- **自動保存**: 每次練習自動記錄
- **隱私保護**: 數據完全本地化

## 常見問題

### API Key 相關
**Q**: 如何獲取 Gemini API Key？  
**A**: 訪問 [Google AI Studio](https://makersuite.google.com/app/apikey) 免費申請

### 部署相關
**Q**: 其他設備無法訪問？  
**A**: 檢查防火牆設置，確保 8000 端口開放

### 數據備份
**Q**: 如何備份學習數據？  
**A**: 複製 `data/` 目錄即可，包含所有知識點和練習記錄

## 📖 文檔

完整文檔請訪問 [文檔中心](docs/index.md)：

- [安裝指南](docs/getting-started/installation.md)
- [配置指南](docs/getting-started/configuration.md)
- [快速開始](docs/getting-started/quick-start.md)
- [API 文檔](docs/API.md)
- [架構設計](docs/ARCHITECTURE.md)
- [開發指南](docs/DEVELOPMENT.md)
- [部署指南](docs/DEPLOYMENT.md)
- [設計系統](docs/DESIGN-SYSTEM-COMPLETE.md)

## 🤝 貢獻

歡迎貢獻！請查看 [開發指南](docs/DEVELOPMENT.md) 了解詳情。

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 發起 Pull Request

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE) 文件

## 🔗 連結

- [問題回報](https://github.com/yourusername/linker-cli/issues)
- [討論區](https://github.com/yourusername/linker-cli/discussions)
- [變更日誌](CHANGELOG.md)

## 🙏 致謝

- Google Gemini API - AI 能力支援
- FastAPI - Web 框架
- Python 社群 - 開源生態

---

<p align="center">
  <strong>版本</strong>: 2.5.0 | 
  <strong>最後更新</strong>: 2025-08-11 | 
  <strong>作者</strong>: Linker Team
</p>
<p align="center">Made with ❤️ by Linker Team</p>