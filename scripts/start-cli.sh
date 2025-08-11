#!/bin/bash

# Linker CLI 啟動腳本

# 檢查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 請先安裝 Python 3"
    exit 1
fi

# 創建虛擬環境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 創建虛擬環境..."
    python3 -m venv venv
fi

# 激活虛擬環境
echo "🔧 激活虛擬環境..."
source venv/bin/activate

# 安裝依賴
echo "📚 檢查依賴..."
pip install -q -r requirements.txt

# 檢查 API KEY
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  請設定 GEMINI_API_KEY 環境變數"
    echo "   export GEMINI_API_KEY=your_api_key"
    exit 1
fi

# 啟動程式
echo "🚀 啟動 Linker CLI..."
python3 linker_cli.py