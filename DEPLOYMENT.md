# Linker 部署指南

## 快速部署選項

### 方案一：本地部署（開發測試）

最簡單的部署方式，適合個人使用和開發測試。

```bash
# 1. 設置環境變數
export GEMINI_API_KEY="your-api-key"

# 2. 啟動服務
./run.sh
```

訪問：http://localhost:8000

### 方案二：局域網部署（家庭/辦公室）

讓同一網路內的其他設備可以訪問。

```bash
# 啟動網路服務
./run-network.sh
```

服務會自動顯示訪問地址：
- 本機：http://localhost:8000
- 其他設備：http://192.168.x.x:8000（實際IP會顯示）

**注意事項**：
- 確保防火牆允許 8000 端口
- Windows 需要在防火牆設置中允許 Python
- macOS 可能需要在系統偏好設定中允許連接

### 方案三：Docker 部署（生產環境）

使用容器化部署，適合長期穩定運行。

#### 前置要求
- 安裝 [Docker](https://docs.docker.com/get-docker/)
- 安裝 [Docker Compose](https://docs.docker.com/compose/install/)

#### 部署步驟

1. **創建環境配置**
```bash
cat > .env << EOF
GEMINI_API_KEY=your-api-key
GEMINI_GENERATE_MODEL=gemini-2.5-flash
GEMINI_GRADE_MODEL=gemini-2.5-pro
EOF
```

2. **啟動服務**
```bash
# 構建並後台運行
docker-compose up -d

# 查看運行狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

3. **管理服務**
```bash
# 停止服務
docker-compose stop

# 重啟服務
docker-compose restart

# 完全清理
docker-compose down
```

#### 數據備份
數據自動掛載到 `./data` 目錄，定期備份此目錄即可。

## 雲端部署

### Render 部署（推薦）

Render 提供免費套餐，適合個人項目。

1. **準備工作**
   - Fork 專案到你的 GitHub
   - 註冊 [Render](https://render.com) 帳號

2. **創建 Web Service**
   - 連接 GitHub 倉庫
   - 選擇 Python 環境
   - 設置環境變數：
     - `GEMINI_API_KEY`: 你的 API Key
     - `PYTHON_VERSION`: 3.11.0

3. **自動部署**
   - Render 會自動使用 `render.yaml` 配置
   - 首次部署約需 5-10 分鐘

### Railway 部署

Railway 提供簡單的部署流程。

```bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入並部署
railway login
railway up

# 設置環境變數
railway variables set GEMINI_API_KEY="your-key"
```

### Fly.io 部署

適合需要全球部署的場景。

```bash
# 安裝 Fly CLI
curl -L https://fly.io/install.sh | sh

# 初始化應用
fly launch

# 設置密鑰
fly secrets set GEMINI_API_KEY="your-key"

# 部署
fly deploy
```

## 進階配置

### 自定義配置

#### 更改端口
```bash
# 環境變數方式
PORT=3000 ./run.sh

# Docker 方式
# 修改 docker-compose.yml
ports:
  - "3000:8000"
```

#### 配置 HTTPS

使用 Nginx 反向代理：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 生產環境優化

#### 使用 Gunicorn
```bash
# 安裝 Gunicorn
pip install gunicorn

# 啟動（4個工作進程）
gunicorn web.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### 使用 Supervisor
```ini
# /etc/supervisor/conf.d/linker.conf
[program:linker]
command=/usr/bin/gunicorn web.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
directory=/opt/linker
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/linker.log
environment=GEMINI_API_KEY="your-key"
```

## 移動設備訪問

### 設置步驟

1. **啟動局域網服務**
```bash
./run-network.sh
# 會顯示類似：📱 其他設備請訪問: http://192.168.1.100:8000
```

2. **手機/平板訪問**
   - 確保與電腦在同一 WiFi
   - 在瀏覽器輸入顯示的地址
   - 建議使用 Chrome 或 Safari

3. **添加到主屏幕**
   - iOS：Safari > 分享 > 加到主畫面
   - Android：Chrome > 選單 > 加到主畫面

### 故障排除

如果無法訪問：
1. 檢查防火牆是否允許 8000 端口
2. 確認設備在同一網段
3. 嘗試關閉電腦防火牆測試
4. 手動獲取 IP：
   - Windows: `ipconfig | findstr IPv4`
   - macOS: `ifconfig | grep "inet " | grep -v 127.0.0.1`
   - Linux: `ip addr show | grep inet`

## 安全建議

### 基本安全措施

1. **API Key 管理**
   - 使用環境變數或 .env 文件
   - 絕不提交到版本控制
   - 定期輪換密鑰

2. **網路安全**
   - 局域網：僅供信任的網路使用
   - 公網：必須使用 HTTPS
   - 考慮使用 VPN 或內網穿透

3. **訪問控制**
   - 可添加 Basic Auth 認證
   - 限制 IP 訪問範圍
   - 使用防火牆規則

### 添加基本認證

```python
# 在 web/main.py 添加
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "your-password")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )
    return credentials.username

# 在需要保護的路由添加依賴
@app.get("/practice", dependencies=[Depends(verify_credentials)])
```

## 常見問題

### 部署相關

**Q: 部署後無法訪問？**
- 檢查服務是否正常啟動：`docker-compose ps` 或 `ps aux | grep uvicorn`
- 檢查端口是否被佔用：`lsof -i:8000` (macOS/Linux) 或 `netstat -ano | findstr :8000` (Windows)
- 查看錯誤日誌：`docker-compose logs` 或查看 `logs/` 目錄

**Q: 如何更新部署？**
```bash
# Docker 部署
git pull
docker-compose down
docker-compose up -d --build

# 普通部署
git pull
pip install -r requirements.txt
# 重啟服務
```

### 數據管理

**Q: 如何遷移數據？**
1. 備份舊環境的 `data/` 目錄
2. 在新環境還原到相同位置
3. 確保文件權限正確

**Q: 如何清理數據？**
- 清理日誌：刪除 `logs/` 目錄下的舊文件
- 重置學習記錄：刪除 `data/practice_log.json`
- 重置知識點：刪除 `data/knowledge.json`

### 性能優化

**Q: 響應速度慢？**
- 檢查網路延遲
- 考慮使用更快的 Gemini 模型
- 增加服務器資源（CPU/內存）
- 使用 CDN 加速靜態資源

## 資源鏈接

### 文檔
- [系統架構](docs/ARCHITECTURE.md)
- [配置指南](docs/CONFIGURATION.md)
- [開發文檔](docs/DEVELOPMENT.md)
- [API 文檔](docs/API.md)

### 獲取幫助
- 提交 [GitHub Issue](https://github.com/your-repo/issues)
- 查看 [FAQ](docs/FAQ.md)
- 聯繫開發團隊

### 相關工具
- [Gemini API](https://makersuite.google.com/app/apikey) - 獲取 API Key
- [Docker Desktop](https://www.docker.com/products/docker-desktop) - 容器化部署
- [Render](https://render.com) - 雲端託管

---

**最後更新**: 2025-08-08  
**版本**: 2.5.0