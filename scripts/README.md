# 啟動腳本說明

## 主要腳本（專案根目錄）

### 🌐 `run.sh` - Web 開發伺服器
**用途**: 本地開發時啟動 Web 介面  
**功能**:
- 自動創建虛擬環境
- 安裝依賴
- 載入 .env 設定
- 啟動 uvicorn 開發伺服器

```bash
./run.sh
# 訪問 http://localhost:8000
```

### 🚀 `start.py` - 生產環境啟動
**用途**: 部署到 Render 或其他雲端平台  
**功能**:
- 使用環境變數 PORT
- 綁定 0.0.0.0 允許外部訪問
- 適合容器化部署

```bash
python3 start.py
```

## 輔助腳本（scripts 目錄）

### 📱 `scripts/run-network.sh` - 局域網分享
**用途**: 讓同一網路的其他設備訪問  
**功能**:
- 自動獲取本機 IP
- 顯示分享連結
- 調用 run.sh 並開放網路訪問

```bash
./scripts/run-network.sh
# 其他設備訪問顯示的 IP 地址
```

### 💻 `scripts/start-cli.sh` - CLI 模式
**用途**: 運行命令列介面版本  
**功能**:
- 啟動 linker_cli.py
- 檢查 GEMINI_API_KEY
- 互動式練習模式

```bash
./scripts/start-cli.sh
```

## 使用建議

| 場景 | 推薦腳本 |
|------|----------|
| 本地開發 | `./run.sh` |
| 生產部署 | `python3 start.py` |
| 分享給朋友 | `./scripts/run-network.sh` |
| CLI 練習 | `./scripts/start-cli.sh` |

## 環境變數

所有腳本都支援以下環境變數：
- `GEMINI_API_KEY`: Gemini API 金鑰（必需）
- `HOST`: 綁定地址（預設 127.0.0.1）
- `PORT`: 埠號（預設 8000）

建議在專案根目錄創建 `.env` 檔案：
```env
GEMINI_API_KEY=your_api_key_here
```