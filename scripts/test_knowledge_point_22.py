#!/usr/bin/env python3
"""
測試知識點 ID 22 的查詢
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os  # noqa: E402

os.environ["USE_DATABASE"] = "true"

from core.database.adapter import get_knowledge_manager_async  # noqa: E402


async def test_knowledge_point_22():
    """測試知識點 ID 22 的查詢"""

    print("\n" + "=" * 60)
    print("測試知識點 ID 22 的查詢")
    print("=" * 60)

    try:
        # 獲取知識管理器
        print("\n1. 初始化知識管理器...")
        knowledge = await get_knowledge_manager_async(use_database=True)
        print("   ✅ 初始化成功")

        # 查詢知識點 22
        print("\n2. 查詢知識點 ID 22...")
        point = await knowledge.get_knowledge_point_async("22")

        if point:
            print("   ✅ 查詢成功！")
            print("\n   知識點詳情：")
            print(f"      ID: {point.id}")
            print(f"      Key Point: {point.key_point[:50]}...")
            print(f"      Category: {point.category}")
            print(f"      Mastery Level: {point.mastery_level}")
            print(f"      Created At: {point.created_at}")
            print(f"      Last Modified: {point.last_modified}")
            print(f"      Is Deleted: {point.is_deleted}")

            # 檢查原始錯誤
            if point.original_error:
                print("\n   原始錯誤：")
                print(f"      Chinese: {point.original_error.chinese_sentence[:30]}...")
                print(f"      User Answer: {point.original_error.user_answer[:30]}...")
                print(f"      Timestamp: {point.original_error.timestamp}")
            else:
                print("\n   ⚠️ 沒有原始錯誤記錄")
        else:
            print("   ❌ 找不到知識點 ID 22")

        # 測試訪問網頁
        print("\n3. 測試訪問知識點詳情頁...")
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/knowledge/22", follow_redirects=False, timeout=10.0
            )

            if response.status_code == 200:
                print("   ✅ 網頁訪問成功")
                # 檢查是否包含知識點內容
                if "動詞 go" in response.text or "goes school" in response.text:
                    print("   ✅ 網頁內容正確")
                else:
                    print("   ⚠️ 網頁內容可能不完整")
            elif response.status_code == 303:
                print("   ⚠️ 被重定向到知識點列表（可能知識點不存在）")
            else:
                print(f"   ❌ 訪問失敗 (HTTP {response.status_code})")

    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60 + "\n")


async def main():
    """主程式"""
    await test_knowledge_point_22()


if __name__ == "__main__":
    asyncio.run(main())
