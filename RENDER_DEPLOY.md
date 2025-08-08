# 📦 Render 部署指南

## 🚀 快速部署步驟

### 1. 準備 GitHub 倉庫
首先將你的代碼推送到 GitHub：
```bash
git init
git add .
git commit -m "Initial commit for Render deployment"
git remote add origin https://github.com/你的用戶名/linker-cli.git
git push -u origin main
```

### 2. 註冊 Render 帳號
前往 [Render](https://render.com) 註冊免費帳號

### 3. 創建新的 Web Service

1. 登入 Render Dashboard
2. 點擊 **"New +"** → **"Web Service"**
3. 連接你的 GitHub 帳號
4. 選擇 `linker-cli` 倉庫
5. 填寫服務設定：
   - **Name**: `linker-translator`（或你喜歡的名稱）
   - **Region**: Singapore（離台灣較近）
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start.py`
   - **Instance Type**: Free

### 4. 設定環境變數

在 "Environment" 區域添加：
- **Key**: `GEMINI_API_KEY`
- **Value**: 你的 Gemini API Key

獲取 API Key：
1. 前往 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 點擊 "Create API Key"
3. 複製 API Key

### 5. 添加持久化儲存（可選但建議）

1. 在服務設定頁面，找到 "Disks" 區域
2. 點擊 "Add Disk"
3. 設定：
   - **Name**: `linker-data`
   - **Mount Path**: `/data`
   - **Size**: 1 GB（免費方案）

### 6. 部署

點擊 **"Create Web Service"** 開始部署

## 📊 監控與管理

### 查看日誌
在 Render Dashboard 中點擊你的服務，選擇 "Logs" 標籤

### 重新部署
- **手動**: Dashboard → "Manual Deploy" → "Deploy latest commit"
- **自動**: 每次推送到 GitHub 會自動部署（可在設定中關閉）

### 訪問你的網站
部署成功後，Render 會提供一個 URL：
```
https://linker-translator.onrender.com
```

## 🛠️ 故障排除

### 問題：部署失敗
檢查：
1. Build logs 中的錯誤訊息
2. `requirements.txt` 是否完整
3. Python 版本是否正確

### 問題：網站無法訪問
檢查：
1. 服務是否正在運行（查看 Dashboard）
2. Start Command 是否正確
3. Port 綁定是否正確（使用 `$PORT` 環境變數）

### 問題：API 無法使用
檢查：
1. GEMINI_API_KEY 環境變數是否設定
2. API Key 是否有效
3. 查看 Logs 中的錯誤訊息

### 問題：數據丟失
確保：
1. 已添加 Disk（持久化儲存）
2. 數據路徑正確（`/data`）
3. 代碼中使用正確的路徑

## 🔄 更新部署

### 更新代碼
```bash
git add .
git commit -m "Update features"
git push origin main
```
Render 會自動重新部署

### 更新環境變數
1. Dashboard → Environment
2. 修改或添加變數
3. 點擊 "Save Changes"
4. 服務會自動重啟

## 💰 費用說明

### 免費方案限制
- 750 小時/月的運行時間
- 服務會在 15 分鐘無活動後休眠
- 首次訪問可能需要等待啟動（約 30 秒）
- 100 GB 頻寬/月

### 升級選項
如需 24/7 運行不休眠：
- Starter: $7/月
- 包含：不休眠、自定義域名、更多資源

## 📝 注意事項

1. **資料備份**：定期下載 `/data` 目錄的內容
2. **API Key 安全**：不要在代碼中硬編碼 API Key
3. **性能優化**：免費方案資源有限，避免大量並發請求
4. **域名設定**：可在 Settings → Custom Domain 添加自己的域名

## 🆘 需要幫助？

- [Render 文檔](https://render.com/docs)
- [Render 社群論壇](https://community.render.com)
- [項目 Issues](https://github.com/你的用戶名/linker-cli/issues)

---

恭喜！你的 Linker 翻譯練習網站已經上線了！🎉