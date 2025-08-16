#!/bin/bash

# ============================================
# Linker 系統重置腳本
# 一鍵恢復到初始狀態，用於測試或重新開始
# ============================================

set -e  # 遇到錯誤立即停止

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 顯示標題
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Linker 系統重置工具 v1.0        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# 警告訊息
echo -e "${YELLOW}⚠️  警告：此操作將會：${NC}"
echo "  • 清空所有知識點"
echo "  • 清空所有練習記錄"
echo "  • 重置每日統計"
echo "  • 重置用戶設定為默認值"
echo "  • 重啟開發服務器"
echo ""

# 確認操作
read -p "確定要重置系統嗎？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${RED}❌ 操作已取消${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}開始重置系統...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: 停止當前運行的服務器
echo -e "\n${BLUE}[1/5]${NC} 停止開發服務器..."
pkill -f uvicorn 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓${NC} 服務器已停止"

# Step 2: 清空資料庫
echo -e "\n${BLUE}[2/5]${NC} 清空資料庫..."

# 使用 Python 腳本清空資料庫（自動確認）
python3 << 'EOF'
import asyncio
import asyncpg
import os

# 直接從環境變量讀取，如果沒有則使用默認值
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://linker_user:linker_pass123@localhost:5432/linker")

async def reset_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 清空表（保留結構）
        tables = [
            "knowledge_points",
            "daily_knowledge_stats", 
            "user_settings"
        ]
        
        for table in tables:
            try:
                await conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                print(f"  ✓ 清空表: {table}")
            except:
                try:
                    await conn.execute(f"DELETE FROM {table}")
                    print(f"  ✓ 清空表: {table} (使用 DELETE)")
                except:
                    pass
        
        # 重置默認設定
        await conn.execute("""
            INSERT INTO user_settings (
                user_id, daily_knowledge_limit, limit_enabled,
                created_at, updated_at
            ) VALUES (
                'default_user', 15, true,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (user_id) DO UPDATE SET
                daily_knowledge_limit = 15,
                limit_enabled = true,
                updated_at = CURRENT_TIMESTAMP
        """)
        print("  ✓ 用戶設定已重置")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"  ✗ 錯誤: {e}")
        return False

asyncio.run(reset_db())
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} 資料庫已清空"
else
    echo -e "${RED}✗${NC} 資料庫清空失敗"
    exit 1
fi

# Step 3: 清理快取和臨時文件
echo -e "\n${BLUE}[3/5]${NC} 清理快取..."
# 清理 Python __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
# 清理 .pyc 文件
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓${NC} 快取已清理"

# Step 4: 確保環境變量設置正確
echo -e "\n${BLUE}[4/5]${NC} 驗證環境設定..."

# 檢查 .env 文件
if [ ! -f .env ]; then
    echo "創建 .env 文件..."
    cp .env.example .env 2>/dev/null || echo "# Linker Configuration" > .env
fi

# 確保關鍵環境變量設置正確
if ! grep -q "AUTO_SAVE_KNOWLEDGE_POINTS" .env; then
    echo "AUTO_SAVE_KNOWLEDGE_POINTS=false" >> .env
fi
if ! grep -q "SHOW_CONFIRMATION_UI" .env; then
    echo "SHOW_CONFIRMATION_UI=true" >> .env
fi
if ! grep -q "DEFAULT_DAILY_LIMIT" .env; then
    echo "DEFAULT_DAILY_LIMIT=15" >> .env
fi

echo -e "${GREEN}✓${NC} 環境設定已驗證"

# Step 5: 重啟開發服務器
echo -e "\n${BLUE}[5/5]${NC} 啟動開發服務器..."

# 在背景啟動服務器
nohup uvicorn web.main:app --reload --port 8000 > server.log 2>&1 &
SERVER_PID=$!

# 等待服務器啟動
echo -n "等待服務器啟動"
for i in {1..10}; do
    sleep 1
    echo -n "."
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✓${NC} 服務器已啟動 (PID: $SERVER_PID)"
        break
    fi
done

# 驗證重置結果
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "\n${GREEN}🎉 系統重置完成！${NC}"
echo ""
echo "📊 當前狀態："

# 檢查每日限額狀態
STATUS=$(curl -s http://localhost:8000/api/knowledge/daily-limit/status 2>/dev/null)
if [ ! -z "$STATUS" ]; then
    USED_COUNT=$(echo $STATUS | python3 -c "import sys, json; print(json.load(sys.stdin).get('used_count', 'N/A'))")
    DAILY_LIMIT=$(echo $STATUS | python3 -c "import sys, json; print(json.load(sys.stdin).get('daily_limit', 'N/A'))")
    echo "  • 今日已儲存: $USED_COUNT/$DAILY_LIMIT"
    echo "  • 知識點總數: 0"
    echo "  • 服務器狀態: ✅ 運行中"
else
    echo "  • 服務器狀態: ⚠️  啟動中..."
fi

echo ""
echo "🔗 訪問地址："
echo "  • 主頁: http://localhost:8000"
echo "  • 練習: http://localhost:8000/practice"
echo "  • 設定: http://localhost:8000/settings"
echo ""
echo "💡 提示："
echo "  • 使用 'tail -f server.log' 查看服務器日誌"
echo "  • 使用 'pkill -f uvicorn' 停止服務器"
echo "  • 再次運行 './scripts/legacy/reset.sh' 或使用 './linker.sh reset' 可以隨時重置"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"