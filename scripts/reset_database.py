#!/usr/bin/env python3
"""
重置資料庫 - 清空所有數據但保留表結構
用於測試目的，清除所有知識點和統計數據
"""

import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from core.config import DATABASE_URL


async def reset_database():
    """清空資料庫中的所有數據（保留表結構）"""
    
    if not DATABASE_URL:
        print("❌ 錯誤：DATABASE_URL 未設置")
        return False
    
    print("🗄️  連接到資料庫...")
    try:
        # 建立連接
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("🧹 開始清空資料表...")
        
        # 清空所有資料表（注意順序，避免外鍵約束問題）
        tables_to_clear = [
            "practice_history",        # 練習歷史
            "review_logs",             # 複習日誌
            "knowledge_points",        # 知識點
            "mistakes",                # 錯誤記錄
            "daily_knowledge_stats",  # 每日統計
            "user_settings",           # 用戶設定（可選）
        ]
        
        for table in tables_to_clear:
            try:
                # 使用 TRUNCATE 快速清空表，並重置自增ID
                await conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                print(f"  ✅ 清空表: {table}")
            except Exception as e:
                # 如果表不存在或其他錯誤，嘗試 DELETE
                try:
                    await conn.execute(f"DELETE FROM {table}")
                    print(f"  ✅ 清空表: {table} (使用 DELETE)")
                except Exception as e2:
                    print(f"  ⚠️  無法清空表 {table}: {e2}")
        
        # 重新初始化默認的用戶設定
        print("\n📝 重新初始化默認設定...")
        await conn.execute("""
            INSERT INTO user_settings (
                user_id, 
                daily_knowledge_limit, 
                limit_enabled,
                created_at,
                updated_at
            ) VALUES (
                'default_user',
                15,  -- 默認每日限額
                true,  -- 啟用限額
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (user_id) DO UPDATE SET
                daily_knowledge_limit = 15,
                limit_enabled = true,
                updated_at = CURRENT_TIMESTAMP
        """)
        print("  ✅ 用戶設定已重置為默認值")
        
        # 驗證清空結果
        print("\n📊 驗證清空結果:")
        for table in tables_to_clear:
            try:
                result = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                status = "✅ 空" if result == 0 else f"⚠️  還有 {result} 筆記錄"
                print(f"  {table}: {status}")
            except Exception as e:
                print(f"  {table}: ❌ 無法檢查 ({e})")
        
        # 關閉連接
        await conn.close()
        
        print("\n✨ 資料庫重置完成！")
        print("📌 注意事項：")
        print("  - 所有知識點已清除")
        print("  - 所有練習記錄已清除")
        print("  - 每日統計已重置")
        print("  - 每日限額設為 15（默認值）")
        print("  - 現在可以開始全新的測試")
        
        return True
        
    except asyncpg.PostgresError as e:
        print(f"❌ 資料庫錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 未預期的錯誤: {e}")
        return False


async def confirm_reset():
    """確認用戶真的要重置資料庫"""
    print("⚠️  警告：此操作將清空所有資料！")
    print("這包括：")
    print("  - 所有知識點")
    print("  - 所有練習記錄")
    print("  - 所有複習進度")
    print("  - 每日統計數據")
    print()
    
    response = input("確定要繼續嗎？輸入 'yes' 確認: ")
    return response.lower() == 'yes'


async def main():
    """主程式"""
    # 確認操作
    if not await confirm_reset():
        print("❌ 操作已取消")
        return
    
    # 執行重置
    success = await reset_database()
    
    if success:
        print("\n🎉 可以開始新的測試了！")
    else:
        print("\n❌ 重置失敗，請檢查錯誤訊息")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())