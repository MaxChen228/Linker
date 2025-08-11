# 安裝指南

## 系統要求

- Python 3.9 或更高版本
- Git
- 至少 500MB 可用空間

## 安裝步驟

### 1. 克隆專案

```bash
git clone https://github.com/yourusername/linker-cli.git
cd linker-cli
```

### 2. 創建虛擬環境（推薦）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 4. 設置環境變數

創建 `.env` 檔案：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，設置必要的 API 金鑰：

```env
# Gemini API 設置 (必需)
GEMINI_API_KEY=your_api_key_here

# 可選配置
LOG_LEVEL=INFO
ENV=development
```

### 5. 驗證安裝

```bash
# 測試 CLI 模式
python linker_cli.py

# 測試 Web 模式
python -m web.main
# 訪問 http://localhost:8000
```

## 常見問題

### Q: 找不到 Python 3.9？
**A:** 請訪問 [Python 官網](https://python.org) 下載最新版本

### Q: pip install 失敗？
**A:** 嘗試升級 pip：
```bash
python -m pip install --upgrade pip
```

### Q: GEMINI_API_KEY 如何獲取？
**A:** 請訪問 [Google AI Studio](https://makersuite.google.com/app/apikey) 免費申請

## 下一步

安裝完成後，請參考：
- [配置指南](configuration.md) - 詳細配置選項
- [快速開始](quick-start.md) - 5 分鐘上手教程

---

> 📝 **注意**: 本文檔是所有安裝相關資訊的唯一來源。如發現其他檔案有重複內容，請以此為準。