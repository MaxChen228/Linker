#!/usr/bin/env python3
"""
測試句型批量擴充功能
使用少量句型進行測試，確認系統運作正常
"""

import asyncio
import json
from pathlib import Path
from core.pattern_enrichment import PatternEnrichmentService


async def test_enrichment():
    """測試批量擴充功能"""
    
    # 準備測試資料（選取前3個句型進行測試）
    test_patterns = [
        {
            "id": "GP001",
            "category": "強調用法",
            "pattern": "It is...that...",
            "explanation": "強調句型，用來強調句子中的某個部分",
            "example_zh": "就是他昨天打破了窗戶。",
            "example_en": "It was he who broke the window yesterday."
        },
        {
            "id": "GP002", 
            "category": "強調用法",
            "pattern": "It is...who/which...",
            "explanation": "強調句型，用來強調人或物",
            "example_zh": "是瑪麗昨天幫助了我。",
            "example_en": "It was Mary who helped me yesterday."
        },
        {
            "id": "GP003",
            "category": "比較用法",
            "pattern": "The more...the more...",
            "explanation": "表示「越...越...」的比較句型",
            "example_zh": "你越努力，你就會越成功。",
            "example_en": "The harder you work, the more successful you will be."
        }
    ]
    
    # 創建測試用的輸入檔案
    test_input_file = "data/test_patterns.json"
    test_output_file = "data/test_patterns_enriched.json"
    
    # 儲存測試資料
    Path("data").mkdir(exist_ok=True)
    with open(test_input_file, 'w', encoding='utf-8') as f:
        json.dump(test_patterns, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print("🧪 開始測試句型批量擴充功能")
    print("=" * 60)
    print(f"測試句型數量: {len(test_patterns)}")
    print(f"輸入檔案: {test_input_file}")
    print(f"輸出檔案: {test_output_file}")
    print("-" * 60)
    
    # 創建服務實例
    service = PatternEnrichmentService()
    
    # 重置進度（確保從頭開始測試）
    service.progress_tracker.checkpoint_file = Path('data/test_enrichment_progress.json')
    service.progress_tracker.reset()
    
    # 設定較小的批次大小和較短的延遲（加快測試）
    service.batch_size = 2  # 每批處理2個
    service.delay_between_batches = 1  # 批次間延遲1秒
    
    try:
        # 執行擴充
        print("\n📝 正在擴充句型...")
        result = await service.run_enrichment(
            input_file=test_input_file,
            output_file=test_output_file
        )
        
        print("\n" + "=" * 60)
        print("✅ 測試完成！")
        print("=" * 60)
        print(f"總共處理: {result['total_patterns']} 個句型")
        print(f"成功: {result['enrichment_summary']['completed']} 個")
        print(f"失敗: {result['enrichment_summary']['failed']} 個")
        
        # 顯示擴充結果範例
        if result['patterns']:
            print("\n" + "-" * 60)
            print("📋 擴充結果範例（第一個句型）:")
            print("-" * 60)
            
            first_pattern = result['patterns'][0]
            
            # 顯示基本資訊
            print(f"句型: {first_pattern.get('pattern', 'N/A')}")
            print(f"公式: {first_pattern.get('formula', 'N/A')}")
            print(f"分類: {first_pattern.get('category', 'N/A')}")
            print(f"難度: {first_pattern.get('difficulty', 'N/A')}")
            print(f"頻率: {first_pattern.get('frequency', 'N/A')}")
            
            # 顯示例句
            examples = first_pattern.get('examples', [])
            if examples:
                print(f"\n例句數量: {len(examples)}")
                print("\n前3個例句:")
                for i, ex in enumerate(examples[:3], 1):
                    print(f"\n例句 {i}:")
                    print(f"  中文: {ex.get('zh', 'N/A')}")
                    print(f"  英文: {ex.get('en', 'N/A')}")
                    print(f"  級別: {ex.get('level', 'N/A')}")
                    print(f"  重點: {ex.get('focus', 'N/A')}")
            
            # 顯示常見錯誤
            errors = first_pattern.get('common_errors', [])
            if errors:
                print(f"\n常見錯誤數量: {len(errors)}")
                if errors:
                    print("\n第一個常見錯誤:")
                    err = errors[0]
                    print(f"  錯誤: {err.get('error_pattern', 'N/A')}")
                    print(f"  正確: {err.get('correction', 'N/A')}")
                    print(f"  解釋: {err.get('explanation', 'N/A')}")
        
        print("\n" + "=" * 60)
        print(f"💾 擴充結果已儲存至: {test_output_file}")
        print("=" * 60)
        
        # 詢問是否要查看完整輸出
        print("\n是否要查看完整的 JSON 輸出？")
        print("提示：輸出檔案可能很大，建議直接開啟檔案查看")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主程式進入點"""
    print("\n" + "🚀" * 30)
    print("句型批量擴充測試程式")
    print("🚀" * 30 + "\n")
    
    # 檢查 API Key
    import os
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ 錯誤：請設定 GEMINI_API_KEY 環境變數")
        print("   export GEMINI_API_KEY='your-api-key'")
        return
    
    # 執行測試
    result = asyncio.run(test_enrichment())
    
    if result:
        print("\n✨ 所有測試完成！")
        print("   如果測試成功，可以執行完整的批量擴充：")
        print("   python -m core.pattern_enrichment")
    else:
        print("\n⚠️ 測試遇到問題，請檢查錯誤訊息")


if __name__ == "__main__":
    main()