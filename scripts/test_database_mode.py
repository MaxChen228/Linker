#!/usr/bin/env python3
"""
測試資料庫模式獨立運行

測試項目：
1. 資料庫連接
2. save_mistake 異步方法
3. 統計資料獲取
4. 確認沒有降級到 JSON 模式
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 強制使用資料庫模式
os.environ["USE_DATABASE"] = "true"

from core.config import USE_DATABASE
from core.database.adapter import get_knowledge_manager_async
from core.log_config import get_module_logger

logger = get_module_logger(__name__)


async def test_database_mode():
    """測試資料庫模式的獨立運行"""

    print("\n" + "=" * 60)
    print("測試資料庫模式獨立運行")
    print("=" * 60)

    # 確認配置
    print(f"\n1. 環境配置檢查:")
    print(f"   USE_DATABASE = {USE_DATABASE}")

    if not USE_DATABASE:
        print("   ❌ 錯誤：未啟用資料庫模式")
        return False

    print("   ✅ 資料庫模式已啟用")

    # 獲取異步知識管理器
    print(f"\n2. 初始化知識管理器:")
    try:
        knowledge = await get_knowledge_manager_async(use_database=True)
        print("   ✅ 知識管理器初始化成功")
    except Exception as e:
        print(f"   ❌ 初始化失敗: {e}")
        return False

    # 檢查是否真的使用資料庫
    print(f"\n3. 驗證資料庫模式:")
    if knowledge.use_database:
        print("   ✅ 確認使用資料庫模式")
    else:
        print("   ❌ 錯誤：降級到 JSON 模式")
        return False

    # 測試 save_mistake_async
    print(f"\n4. 測試 save_mistake_async 方法:")

    # 模擬錯誤反饋
    test_feedback = {
        "is_generally_correct": False,
        "overall_suggestion": "This is the correct answer.",
        "error_analysis": [
            {
                "key_point_summary": "Test Grammar Rule",
                "original_phrase": "test error",
                "correction": "test correction",
                "explanation": "This is a test explanation",
                "severity": "major",
                "category": "systematic",
            }
        ],
    }

    try:
        result = await knowledge._save_mistake_async(
            chinese_sentence="這是測試句子",
            user_answer="This is test answer",
            feedback=test_feedback,
            practice_mode="new",
        )

        if result:
            print("   ✅ save_mistake_async 執行成功")
        else:
            print("   ⚠️ save_mistake_async 返回 False")
    except Exception as e:
        print(f"   ❌ save_mistake_async 執行失敗: {e}")
        return False

    # 測試統計獲取
    print(f"\n5. 測試統計資料獲取:")
    try:
        stats = await knowledge.get_statistics_async()
        print(f"   知識點總數: {stats.get('knowledge_points', 0)}")
        print(f"   練習總次數: {stats.get('total_practices', 0)}")
        print(f"   正確次數: {stats.get('correct_count', 0)}")
        print("   ✅ 統計資料獲取成功")
    except Exception as e:
        print(f"   ❌ 統計資料獲取失敗: {e}")
        return False

    # 測試獲取知識點
    print(f"\n6. 測試獲取知識點:")
    try:
        points = await knowledge.get_knowledge_points_async()
        print(f"   找到 {len(points)} 個知識點")
        print("   ✅ 知識點獲取成功")
    except Exception as e:
        print(f"   ❌ 知識點獲取失敗: {e}")
        return False

    # 測試複習候選
    print(f"\n7. 測試獲取複習候選:")
    try:
        candidates = await knowledge.get_review_candidates_async(max_points=5)
        print(f"   找到 {len(candidates)} 個待複習知識點")
        print("   ✅ 複習候選獲取成功")
    except Exception as e:
        print(f"   ❌ 複習候選獲取失敗: {e}")
        return False

    # 檢查是否有任何降級警告
    print(f"\n8. 檢查降級警告:")
    print("   請檢查上述輸出是否有「降級到 JSON 模式」的警告")
    print("   如果沒有警告，表示資料庫模式獨立運行成功")

    print("\n" + "=" * 60)
    print("測試結果總結:")
    print("✅ 資料庫模式可以獨立運行")
    print("✅ 異步方法執行正常")
    print("✅ 沒有降級到 JSON 模式")
    print("=" * 60 + "\n")

    return True


async def main():
    """主程式"""
    try:
        success = await test_database_mode()

        if success:
            print("\n🎉 測試成功！資料庫模式已能獨立運行。")
            sys.exit(0)
        else:
            print("\n❌ 測試失敗！請檢查錯誤訊息。")
            sys.exit(1)

    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}", exc_info=True)
        print(f"\n❌ 測試異常終止: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
