# 快速配置指南

## 快速開始

### 1. 設置 API Key（必需）

```bash
# 方法一：使用環境變數
export GEMINI_API_KEY="your_api_key_here"

# 方法二：創建 .env 檔案
echo 'GEMINI_API_KEY=your_api_key_here' > .env
```

### 2. 基本配置範例

創建 `.env` 檔案：

```env
# 必需：API 金鑰
GEMINI_API_KEY=your_key_here

# 可選：環境設定
ENV=development
PORT=8000

# 可選：日誌設定
LOG_LEVEL=INFO
LOG_TO_CONSOLE=true
```

### 3. 驗證配置

```bash
# 測試配置是否正確
python -c "from settings import settings; print('配置載入成功')"

# 測試 API 連接
python -c "from core.ai_service import AIService; print('API 連接成功')"
```

## 常用環境變數

| 變數名 | 必需 | 預設值 | 說明 |
|--------|------|--------|------|
| `GEMINI_API_KEY` | ✅ | - | Google Gemini API 金鑰 |
| `GEMINI_GENERATE_MODEL` | ❌ | `gemini-2.5-flash` | 生成模型 |
| `GEMINI_GRADE_MODEL` | ❌ | `gemini-2.5-pro` | 批改模型 |
| `PORT` | ❌ | `8000` | Web 服務端口 |
| `LOG_LEVEL` | ❌ | `INFO` | 日誌級別 |

## 不同環境的配置

### 開發環境
```env
ENV=development
LOG_LEVEL=DEBUG
LOG_TO_CONSOLE=true
```

### 生產環境
```env
ENV=production
LOG_LEVEL=WARNING
LOG_TO_FILE=true
LOG_FORMAT=json
```

### Docker 部署
```env
GEMINI_API_KEY=${GEMINI_API_KEY}
ENV=production
PORT=8000
HOST=0.0.0.0
```

## 故障排除

### API Key 無效
```bash
# 確保沒有多餘空格
export GEMINI_API_KEY="your_actual_key"
```

### Port 已被佔用
```bash
# 使用其他端口
export PORT=8001
```

### 日誌不顯示
```bash
export LOG_LEVEL=DEBUG
export LOG_TO_CONSOLE=true
```

## 詳細配置文檔

需要更詳細的配置說明？請參閱：
- 📖 **[完整配置指南](../CONFIGURATION.md)** - 所有配置項的詳細說明
- 🔧 **[settings.py 結構](../CONFIGURATION.md#配置結構)** - 配置類別詳解
- 🎯 **[進階配置](../CONFIGURATION.md#配置最佳實踐)** - 最佳實踐與技巧

## 相關文檔

- [安裝指南](installation.md)
- [快速上手](quick-start.md)
- [部署指南](../DEPLOYMENT.md)

---

> ⚠️ **重要**: 不要將包含真實 API Key 的 `.env` 檔案提交到版本控制系統。