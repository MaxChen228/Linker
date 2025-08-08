#!/usr/bin/env bash
set -euo pipefail

# Network deployment script for Linker
# 讓局域網內的其他電腦可以訪問

# 獲取本機 IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

if [ -z "$LOCAL_IP" ]; then
    echo "⚠️  無法獲取本機 IP，使用 0.0.0.0"
    LOCAL_IP="0.0.0.0"
fi

echo "🌐 本機 IP: $LOCAL_IP"
echo "📱 其他設備請訪問: http://$LOCAL_IP:8000"
echo ""

# 設定環境變數並啟動
export HOST="0.0.0.0"
export PORT="8000"

# 執行原本的啟動腳本
./run.sh