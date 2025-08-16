#!/usr/bin/env python3
"""
TASK-32: 每日知識點上限功能測試腳本
測試新增的API端點是否正常工作
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.services.async_knowledge_service import AsyncKnowledgeService


async def test_daily_limit_functions():
    """測試每日限額相關功能"""
    print("🧪 開始測試 TASK-32 每日限額功能...")

    # 初始化服務
    service = AsyncKnowledgeService()
    await service.initialize()

    try:
        # 1. 測試獲取用戶設定
        print("\n1️⃣ 測試獲取用戶設定")
        config = await service.get_daily_limit_config()
        print(f"   當前配置: {json.dumps(config, ensure_ascii=False, indent=2)}")

        # 2. 測試更新配置
        print("\n2️⃣ 測試更新配置")
        success = await service.update_daily_limit_config(daily_limit=20, limit_enabled=True)
        print(f"   更新配置結果: {success}")

        if success:
            updated_config = await service.get_daily_limit_config()
            print(f"   更新後配置: {json.dumps(updated_config, ensure_ascii=False, indent=2)}")

        # 3. 測試檢查限額狀態
        print("\n3️⃣ 測試檢查限額狀態")

        # 測試 isolated 類型
        isolated_status = await service.check_daily_limit("isolated")
        print(f"   isolated 類型狀態: {json.dumps(isolated_status, ensure_ascii=False, indent=2)}")

        # 測試 enhancement 類型
        enhancement_status = await service.check_daily_limit("enhancement")
        print(f"   enhancement 類型狀態: {json.dumps(enhancement_status, ensure_ascii=False, indent=2)}")

        # 測試非限制類型
        other_status = await service.check_daily_limit("other")
        print(f"   other 類型狀態: {json.dumps(other_status, ensure_ascii=False, indent=2)}")

        # 4. 測試更新統計
        print("\n4️⃣ 測試更新統計")

        for error_type in ["isolated", "enhancement", "systematic"]:
            result = await service.update_daily_stats(error_type)
            print(f"   更新 {error_type} 統計: {result}")

        # 5. 再次檢查狀態（應該有變化）
        print("\n5️⃣ 檢查更新後的狀態")
        updated_status = await service.check_daily_limit("isolated")
        print(f"   更新後 isolated 狀態: {json.dumps(updated_status, ensure_ascii=False, indent=2)}")

        # 6. 測試獲取統計數據
        print("\n6️⃣ 測試獲取統計數據")
        stats = await service.get_daily_limit_stats(7)
        print(f"   7天統計數據: {json.dumps(stats, ensure_ascii=False, indent=2)}")

        # 7. 測試達到上限的情況
        print("\n7️⃣ 測試達到上限的情況")

        # 先設定一個很低的上限
        await service.update_daily_limit_config(daily_limit=1, limit_enabled=True)

        # 多次更新統計，模擬達到上限
        for _i in range(3):
            await service.update_daily_stats("isolated")

        limit_exceeded_status = await service.check_daily_limit("isolated")
        print(f"   達到上限後狀態: {json.dumps(limit_exceeded_status, ensure_ascii=False, indent=2)}")

        print("\n✅ 所有測試完成！")

    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await service.cleanup()


def test_config_file_paths():
    """測試配置文件路徑是否正確"""
    print("\n📁 測試配置文件路徑...")

    service = AsyncKnowledgeService()

    settings_path = service._get_settings_file_path()
    stats_path = service._get_daily_stats_file_path()

    print(f"   用戶設定文件路徑: {settings_path}")
    print(f"   每日統計文件路徑: {stats_path}")

    # 確保目錄存在
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.parent.mkdir(parents=True, exist_ok=True)

    print("   目錄已準備好 ✅")


if __name__ == "__main__":
    print("🚀 TASK-32 每日知識點上限功能測試")
    print("=" * 50)

    # 測試文件路徑
    test_config_file_paths()

    # 運行異步測試
    asyncio.run(test_daily_limit_functions())

    print("\n🎯 測試腳本執行完成")
