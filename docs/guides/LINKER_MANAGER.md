# Linker 專案管理系統使用指南

## 🚀 快速開始

最簡單的啟動方式：
```bash
./linker.sh
```

這將開啟互動式管理介面，提供所有功能的圖形化選單。

## 📋 功能概覽

### 1. 快速啟動 (`./linker.sh start`)
- 自動檢查並安裝 Python 環境
- 建立虛擬環境
- 安裝所有依賴套件
- 載入環境變數
- 啟動 Web 服務器
- **適用場景**：日常開發、快速測試

### 2. 開發模式 (`./linker.sh dev`)
- 背景執行服務器
- 啟用自動重載（檔案變更自動重啟）
- DEBUG 級別日誌
- 日誌保存至 `server.log`
- **適用場景**：開發新功能、除錯

### 3. 系統重置 (`./linker.sh reset`)
- 停止所有服務
- 清空資料庫（知識點、統計、設定）
- 重置為預設配置
- 清理快取檔案
- **適用場景**：重新開始、測試初始狀態

### 4. 資料庫管理
提供完整的資料庫操作：
- **初始化結構**：建立所有必要的表格
- **備份**：匯出完整資料庫至 SQL 檔案
- **還原**：從備份檔案恢復資料
- **狀態檢查**：驗證連接和表格狀態
- **清空**：危險操作，完全清除資料

### 5. 停止服務 (`./linker.sh stop`)
- 優雅地關閉所有運行中的服務
- 清理進程

### 6. 程式碼品質檢查
使用 Ruff 進行：
- 程式碼風格檢查
- 潛在錯誤偵測
- 自動格式化
- 自動修復常見問題

### 7. 測試套件 (`./linker.sh test`)
多種測試選項：
- 所有測試（含覆蓋率報告）
- 單元測試
- 整合測試
- API 端點測試
- 資料庫連接測試

### 8. 環境設定
管理 `.env` 檔案：
- 設定 Gemini API Key
- 配置資料庫連接
- 調整每日限額
- 編輯環境變數

### 9. 快速連結
顯示所有重要的 URL：
- 網頁介面連結
- API 端點
- 開發工具命令

### 10. 系統資訊
查看：
- Python 版本
- 安裝的套件
- 專案統計
- 資料庫狀態

## 🔧 命令列模式

除了互動式介面，也支援直接命令：

```bash
# 快速啟動
./linker.sh start

# 開發模式
./linker.sh dev

# 停止服務
./linker.sh stop

# 重置系統
./linker.sh reset

# 執行測試
./linker.sh test

# 顯示說明
./linker.sh help
```

## 📁 檔案結構

```
linker/
├── linker.sh           # 主管理腳本
├── .env               # 環境變數設定
├── server.log         # 服務器日誌
├── venv/              # Python 虛擬環境
├── requirements.txt   # Python 依賴
├── web/              # Web 應用程式
├── core/             # 核心功能模組
├── scripts/          # 工具腳本
└── data/             # 資料目錄
    └── backups/      # 資料庫備份
```

## 🔑 環境變數設定

關鍵的環境變數（在 `.env` 檔案中設定）：

```bash
# Gemini AI API 金鑰（必須）
GEMINI_API_KEY=your_api_key_here

# 資料庫連接字串（必須）
DATABASE_URL=postgresql://user:password@localhost:5432/linker

# 每日知識點限額（選用，預設 15）
DEFAULT_DAILY_LIMIT=15

# 開發模式（選用）
DEV_MODE=false

# 日誌級別（選用）
LOG_LEVEL=INFO

# 自動儲存知識點（選用）
AUTO_SAVE_KNOWLEDGE_POINTS=false

# 顯示確認介面（選用）
SHOW_CONFIRMATION_UI=true
```

## 🚨 常見問題排除

### 1. Python 未安裝
```bash
# macOS
brew install python@3.9

# Ubuntu/Debian
sudo apt-get install python3.9

# CentOS/RHEL
sudo yum install python39
```

### 2. 資料庫連接失敗
檢查 PostgreSQL 是否運行：
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql
```

### 3. 權限問題
```bash
# 確保腳本可執行
chmod +x linker.sh

# 修復檔案權限
chmod -R 755 .
```

### 4. 虛擬環境問題
```bash
# 刪除並重建虛擬環境
rm -rf venv
python3 -m venv venv
```

### 5. 端口被佔用
```bash
# 查找佔用 8000 端口的進程
lsof -i :8000

# 使用不同端口
PORT=8001 ./linker.sh start
```

## 📊 系統狀態指示器

管理介面會即時顯示：
- ✅ **綠色**：正常運行
- ⚠️ **黃色**：需要注意（如未配置）
- ❌ **紅色**：錯誤或未運行

## 💡 最佳實踐

1. **日常開發流程**：
   ```bash
   ./linker.sh dev       # 啟動開發模式
   # 編寫程式碼...
   ./linker.sh           # 進入管理介面
   選擇 6                # 執行程式碼檢查
   選擇 7                # 執行測試
   ```

2. **部署前檢查**：
   ```bash
   ./linker.sh
   選擇 6  # 程式碼品質檢查
   選擇 7  # 完整測試
   選擇 4  # 備份資料庫
   ```

3. **問題排查**：
   ```bash
   ./linker.sh
   選擇 10  # 查看系統資訊
   選擇 4   # 檢查資料庫狀態
   選擇 8   # 驗證環境設定
   ```

## 🔄 版本更新

當更新專案時：
1. 停止服務 (`./linker.sh stop`)
2. 拉取最新程式碼 (`git pull`)
3. 更新依賴 (`./linker.sh` 選擇 1 會自動更新)
4. 執行資料庫遷移（如需要）
5. 重啟服務

## 📝 開發提示

- 使用 **開發模式** 進行日常開發，自動重載省時省力
- 定期執行 **程式碼品質檢查**，保持程式碼整潔
- 在提交前執行 **測試套件**，確保功能正常
- 使用 **資料庫備份** 功能保護重要資料
- 透過 **系統資訊** 監控專案狀態

## 🆘 需要幫助？

1. 執行 `./linker.sh help` 查看命令說明
2. 查看 `server.log` 了解詳細錯誤資訊
3. 檢查 `.env` 檔案確保配置正確
4. 參考專案 README.md 了解更多細節

---

**Linker 專案管理系統 v2.0** - 讓開發更簡單、更高效！