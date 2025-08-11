# Linker 快速參考指南

## 快速啟動

```bash
# 1. 設置環境
export GEMINI_API_KEY="your-api-key"

# 2. 啟動服務
./run.sh

# 3. 訪問應用
http://localhost:8000
```

## 專案文檔導航

| 文檔 | 用途 | 路徑 |
|------|------|------|
| **主要指引** | 專案核心說明 | [CLAUDE.md](CLAUDE.md) |
| **完整交接** | 詳細交接文檔 | [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md) |
| **設計系統** | UI/UX 規範 | [docs/DESIGN-SYSTEM-COMPLETE.md](docs/DESIGN-SYSTEM-COMPLETE.md) |
| **待辦事項** | 開發任務清單 | [TODO.md](TODO.md) |
| **系統架構** | 技術架構詳解 | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **API 文檔** | 接口說明 | [docs/API.md](docs/API.md) |
| **MCP 設置** | 測試工具配置 | [MCP_SETUP.md](MCP_SETUP.md) |

## 核心文件路徑

### 後端核心
- `web/main.py` - FastAPI 主程式
- `core/ai_service.py` - AI 服務
- `core/knowledge.py` - 知識點管理
- `core/error_types.py` - 錯誤分類

### 前端文件
- `web/templates/` - HTML 模板
- `web/static/main.js` - 前端邏輯
- `web/static/css/design-system/` - 設計系統
- `web/static/css/pages/` - 頁面樣式

### 數據文件
- `data/knowledge.json` - 知識點數據
- `data/practice_log.json` - 練習記錄
- `data/grammar_patterns.json` - 文法庫

### 日誌文件
- `logs/web.log` - Web 應用日誌
- `logs/ai.log` - AI 服務日誌
- `logs/knowledge_manager.log` - 知識管理日誌

## 常用命令

### 開發環境
```bash
# 安裝依賴
pip install -r requirements.txt

# 開發模式啟動
uvicorn web.main:app --reload --port 8000

# 局域網訪問
./run-network.sh
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

### Git 操作
```bash
# 查看變更
git status

# 提交代碼
git add .
git commit -m "feat: 功能描述"

# 推送
git push origin main
```

## 環境變數配置

```bash
# 必須設置
GEMINI_API_KEY=your-api-key

# 可選設置
GEMINI_GENERATE_MODEL=gemini-2.5-flash
GEMINI_GRADE_MODEL=gemini-2.5-pro
LOG_LEVEL=INFO
LOG_TO_FILE=true
PORT=8000
```

## API 端點速查

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

## 設計系統速查

### 主要顏色
- **主色**: `--accent-500: #6366f1` (Indigo)
- **文字**: `--gray-700: #374151`
- **背景**: `--gray-50: #f9fafb`
- **邊框**: `--gray-200: #e5e7eb`

### 間距單位
- 基準: 8px grid
- 小間距: `--space-2: 0.5rem` (8px)
- 中間距: `--space-4: 1rem` (16px)
- 大間距: `--space-8: 2rem` (32px)

### 圓角
- 小: `--radius-sm: 0.25rem` (4px)
- 預設: `--radius-md: 0.5rem` (8px)
- 大: `--radius-lg: 0.75rem` (12px)

## 問題排查

### 常見問題和解決方案

| 問題 | 可能原因 | 解決方案 |
|------|---------|---------|
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

## 開發流程

1. **功能開發**
   - 查看 TODO.md 選擇任務
   - 創建功能分支
   - 編寫代碼和測試
   - 提交 PR

2. **UI 修改**
   - 遵循設計系統規範
   - 使用 CSS 變數
   - 測試響應式效果
   - 更新文檔

3. **部署上線**
   - 運行測試套件
   - 更新版本號
   - 打標籤
   - 部署到生產環境

## 聯繫和支援

- 主要文檔: [CLAUDE.md](CLAUDE.md)
- 交接文檔: [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md)
- 問題追蹤: GitHub Issues
- 版本歷史: [CHANGELOG.md](CHANGELOG.md)

---

**版本**: 2.5.0 | **更新**: 2025-08-10