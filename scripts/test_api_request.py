#!/usr/bin/env python3
"""
測試 API 請求，驗證資料庫模式下沒有警告
"""

import asyncio
import json
import httpx


async def test_grade_answer():
    """測試批改答案 API"""
    
    print("\n測試批改答案 API...")
    
    # 準備測試數據
    test_data = {
        "chinese": "我喜歡學習新的技術",
        "english": "I like learn new technology",  # 故意的錯誤: learn -> learning
        "mode": "new",
        "level": 2,
        "length": 1,
        "target_point_ids": []
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/grade-answer",
                json=test_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API 調用成功")
                print(f"   分數: {result.get('score', 0)}")
                print(f"   正確性: {result.get('is_generally_correct', False)}")
                print(f"   錯誤數: {len(result.get('error_analysis', []))}")
                
                # 檢查是否有錯誤被記錄
                if not result.get('is_generally_correct', False):
                    print(f"   💾 錯誤已保存到知識點")
                
                return True
            else:
                print(f"❌ API 返回錯誤: {response.status_code}")
                print(f"   {response.text}")
                return False
                
        except httpx.RequestError as e:
            print(f"❌ 請求失敗: {e}")
            print("   請確保應用程式正在運行 (USE_DATABASE=true uvicorn web.main:app --reload)")
            return False


async def test_generate_question():
    """測試生成題目 API"""
    
    print("\n測試生成題目 API...")
    
    test_data = {
        "mode": "new",
        "length": 1,
        "level": 2
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/generate-question",
                json=test_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API 調用成功")
                print(f"   生成句子: {result.get('chinese', '')[0:30]}...")
                return True
            else:
                print(f"❌ API 返回錯誤: {response.status_code}")
                return False
                
        except httpx.RequestError as e:
            print(f"❌ 請求失敗: {e}")
            return False


async def main():
    """主程式"""
    
    print("\n" + "="*60)
    print("測試 API 請求（資料庫模式）")
    print("="*60)
    
    print("\n請確保應用程式正在運行:")
    print("USE_DATABASE=true uvicorn web.main:app --reload --port 8000")
    print("\n按 Enter 繼續測試...")
    input()
    
    # 測試批改答案
    success1 = await test_grade_answer()
    
    # 測試生成題目
    success2 = await test_generate_question()
    
    print("\n" + "="*60)
    if success1 and success2:
        print("✅ 所有測試通過！")
        print("\n請檢查應用程式日誌:")
        print("1. 是否有「資料庫模式下建議使用 save_mistake_async」警告")
        print("2. 是否有「降級到 JSON 模式」的訊息")
        print("\n如果沒有這些警告，表示資料庫模式已成功獨立運行！")
    else:
        print("❌ 部分測試失敗")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())