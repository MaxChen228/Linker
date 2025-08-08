# 快速開始指南

## 10 秒鐘開始使用

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
./start.sh
```

## 獲取 API Key

1. 訪問 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 點擊「Create API Key」
3. 複製生成的密鑰

## 環境要求

- Python 3.8+ 或 Docker
- 穩定的網路連接
- 支援的瀏覽器（Chrome/Safari/Firefox）

## 第一次練習

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

## 常見問題

**Q: 無法啟動服務？**
- 檢查 Python 版本：`python3 --version`
- 確認 API Key 已設置：`echo $GEMINI_API_KEY`

**Q: 其他設備如何訪問？**
- 使用 `./run-network.sh` 啟動
- 會顯示局域網地址供其他設備訪問

**Q: 如何查看學習進度？**
- Web：點擊「知識點」頁面
- CLI：選擇「查看知識點」選項

## 下一步

- 閱讀[完整文檔](README.md)了解所有功能
- 查看[配置指南](CONFIGURATION.md)自定義設置
- 參考[部署指南](../DEPLOYMENT.md)進行生產部署