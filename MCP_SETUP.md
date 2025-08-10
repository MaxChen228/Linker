# MCP-Playwright 設置指南

## 設置步驟

### 1. 安裝 mcp-playwright
```bash
npm install -g @executeautomation/playwright-mcp-server
```

### 2. 重啟 Claude Desktop
配置文件已創建在：
`~/Library/Application Support/Claude/claude_desktop_config.json`

請完全退出並重新啟動 Claude Desktop 應用程式。

### 3. 驗證設置
重啟後，我將能夠：
- 自動開啟瀏覽器測試你的 web 應用
- 填寫表單並提交
- 截圖並分析頁面
- 驗證功能是否正常

### 4. 運行測試腳本（可選）
```bash
# 先安裝 playwright
npm install playwright

# 運行測試
node test_linker.js
```

## 使用範例

設置完成後，你可以對我說：
- "測試練習頁面的提交功能"
- "檢查知識點頁面的搜尋是否正常"
- "驗證複習模式是否能正確載入"

我就能直接在瀏覽器中執行這些測試！

## 注意事項
- 確保你的 Linker 應用正在運行（http://localhost:8000）
- MCP 服務需要 Claude Desktop 重啟才能生效
- 首次使用可能需要下載 Playwright 瀏覽器驅動