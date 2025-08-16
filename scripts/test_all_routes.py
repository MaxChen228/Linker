#!/usr/bin/env python3
"""
測試所有路由是否還有同步方法警告
"""

import asyncio

import httpx


async def test_routes():
    """測試各個路由"""

    routes_to_test = [
        ("GET", "/", "首頁"),
        ("GET", "/knowledge", "知識點列表"),
        ("GET", "/knowledge/1", "知識點詳情"),
        ("GET", "/knowledge/trash", "回收站"),
        ("GET", "/practice", "練習頁"),
        ("GET", "/api/knowledge/recommendations", "學習推薦API"),
    ]

    print("\n" + "=" * 60)
    print("測試所有路由（資料庫模式）")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        for method, path, description in routes_to_test:
            try:
                print(f"\n測試 {description} ({method} {path})...")

                if method == "GET":
                    response = await client.get(
                        f"http://localhost:8000{path}", follow_redirects=False, timeout=10.0
                    )

                # 檢查響應狀態
                if response.status_code in [200, 303, 307]:
                    print(f"  ✅ 成功 (HTTP {response.status_code})")
                else:
                    print(f"  ⚠️ 返回 HTTP {response.status_code}")

            except Exception as e:
                print(f"  ❌ 失敗: {e}")

    print("\n" + "=" * 60)
    print("測試完成！")
    print("\n請檢查伺服器日誌是否有以下警告：")
    print("1. 「資料庫模式下建議使用 xxx_async」")
    print("2. 「同步方法在資料庫模式下不支援」")
    print("3. 「降級到 JSON 模式」")
    print("\n如果沒有這些警告，表示所有路由都已正確使用異步方法！")
    print("=" * 60 + "\n")


async def main():
    """主程式"""
    await test_routes()


if __name__ == "__main__":
    asyncio.run(main())
