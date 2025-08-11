# 快速開始指南

## 🚀 快速啟動

```bash
# 1. 設置環境
export GEMINI_API_KEY="your-api-key"

# 2. 啟動服務
./run.sh

# 3. 訪問應用
http://localhost:8000
```

## 📚 10 秒鐘開始使用

### 方式一：Web 界面（推薦）
```bash
# 1. 設置 API Key
export GEMINI_API_KEY="your-api-key"

# 2. 啟動服務
./run.sh

# 3. 打開瀏覽器訪問 http://localhost:8000
```

### 方式二：命令行界面
```bash
# 1. 設置 API Key
export GEMINI_API_KEY="your-api-key"

# 2. 啟動 CLI
./scripts/start-cli.sh
```

## 🔑 獲取 API Key

1. 訪問 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 點擊「Create API Key」
3. 複製生成的密鑰

## 💻 環境要求

- Python 3.8+ 或 Docker
- 穩定的網路連接
- 支援的瀏覽器（Chrome/Safari/Firefox）

## 📂 項目結構

```
linker/
├── web/           # Web 介面
│   ├── main.py        # FastAPI 主程式
│   ├── templates/     # HTML 模板
│   └── static/        # 靜態資源
├── core/          # 核心模組
│   ├── ai_service.py  # AI 服務
│   ├── knowledge.py   # 知識點管理
│   └── error_types.py # 錯誤分類
├── data/          # 數據存儲
│   ├── knowledge.json # 知識點數據
│   └── practice_log.json # 練習記錄
├── logs/          # 日誌文件
└── docs/          # 文檔
```

## 🎮 第一次練習

### Web 界面
1. 打開瀏覽器訪問服務
2. 點擊「練習」
3. 選擇難度和長度
4. 點擊「出題」
5. 輸入翻譯並提交

### CLI 界面
1. 從主選單選擇「1. 開始翻譯練習」
2. 選擇難度等級
3. 輸入翻譯
4. 查看批改結果

## 🔧 常用命令

### 開發環境
```bash
# 安裝依賴
pip install -r requirements.txt

# 開發模式啟動
uvicorn web.main:app --reload --port 8000

# 局域網訪問
./scripts/run-network.sh
```

### Docker 部署
```bash
# 構建並啟動
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 測試和檢查
```bash
# Lint 檢查
ruff check .

# 型別檢查
mypy .

# 運行測試
pytest tests/
```

## 🔍 API 端點速查

| 方法 | 端點 | 用途 |
|------|------|------|
| GET | `/` | 首頁 |
| GET | `/practice` | 練習頁面 |
| GET | `/knowledge` | 知識點頁面 |
| GET | `/patterns` | 文法句型頁面 |
| POST | `/api/generate` | 生成練習題 |
| POST | `/api/submit` | 提交答案 |
| GET | `/api/knowledge` | 獲取知識點 |
| POST | `/api/review` | 生成複習題 |

## 🆘 問題排查

### 常見問題和解決方案

| 問題 | 可能原因 | 解決方案 |
|------|---------|----------|
| API Key 錯誤 | 環境變數未設置 | 檢查 `GEMINI_API_KEY` |
| CSS 未載入 | 緩存問題 | 清除瀏覽器緩存 |
| 知識點不保存 | 權限問題 | 檢查 `data/` 目錄權限 |
| 服務無法啟動 | 端口佔用 | 改用其他端口或釋放 8000 |

### 日誌查看
```bash
# 查看最新日誌
tail -f logs/web.log

# 查看錯誤
grep ERROR logs/*.log

# 查看 AI 調用
tail -f logs/ai.log
```

## 🔗 相關連結

- [完整文檔](../index.md)
- [安裝指南](installation.md)
- [配置說明](configuration.md)
- [開發指南](../DEVELOPMENT.md)

## 📖 下一步

- 閱讀[完整文檔](../index.md)了解所有功能
- 查看[配置指南](configuration.md)自定義設置
- 參考[部署指南](../DEPLOYMENT.md)進行生產部署

---

**版本**: 2.5.0 | **更新**: 2025-08-11