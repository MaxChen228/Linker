"""
用戶操作路徑一致性快速驗證腳本
用於快速檢查核心用戶路徑的一致性
"""

import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到路徑  
sys.path.insert(0, str(Path(__file__).parent))

from core.knowledge import KnowledgeManager
from core.database.adapter import KnowledgeManagerAdapter


async def quick_user_journey_test():
    """快速用戶路徑一致性測試"""
    print("🚀 開始用戶操作路徑一致性快速驗證...")
    
    # 初始化管理器
    json_manager = KnowledgeManager()
    db_manager = KnowledgeManagerAdapter(use_database=True)
    
    try:
        # === 測試1: 基礎統計一致性 ===
        print("\n📊 測試1: 基礎統計一致性")
        
        json_stats = json_manager.get_statistics()
        db_stats = await db_manager.get_statistics_async()
        
        print(f"JSON 統計: {json_stats}")
        print(f"DB 統計: {db_stats}")
        
        # 檢查知識點數量
        json_count = json_stats.get('knowledge_points', 0)
        db_count = db_stats.get('knowledge_points', 0)
        
        if json_count == db_count:
            print(f"✅ 知識點數量一致: {json_count}")
        else:
            print(f"⚠️ 知識點數量不一致: JSON={json_count}, DB={db_count}")
        
        # 檢查分類分布
        json_categories = set(json_stats.get('category_distribution', {}).keys())
        db_categories = set(db_stats.get('category_distribution', {}).keys())
        
        if json_categories == db_categories:
            print(f"✅ 分類一致: {json_categories}")
        else:
            print(f"⚠️ 分類不一致: JSON={json_categories}, DB={db_categories}")
        
        # === 測試2: 新練習保存一致性 ===
        print("\n📝 測試2: 新練習保存一致性")
        
        test_practice = {
            'chinese_sentence': '這是測試句子。',
            'user_answer': 'This is test sentence.',
            'feedback': {
                'is_generally_correct': False,
                'overall_suggestion': 'This is a test sentence.',
                'error_analysis': [{
                    'key_point_summary': '冠詞使用錯誤',
                    'original_phrase': 'test sentence',
                    'correction': 'a test sentence',
                    'explanation': '可數名詞需要冠詞',
                    'category': 'systematic'
                }]
            }
        }
        
        # 記錄初始狀態
        json_initial = json_manager.get_statistics()
        db_initial = await db_manager.get_statistics_async()
        
        # 保存練習
        json_result = json_manager.save_mistake(
            test_practice['chinese_sentence'],
            test_practice['user_answer'],
            test_practice['feedback']
        )
        
        db_result = await db_manager._save_mistake_async(
            test_practice['chinese_sentence'],
            test_practice['user_answer'],
            test_practice['feedback']
        )
        
        print(f"JSON 保存結果: {json_result}")
        print(f"DB 保存結果: {db_result}")
        
        # 檢查保存後的統計變化
        json_after = json_manager.get_statistics()
        db_after = await db_manager.get_statistics_async()
        
        json_knowledge_increase = json_after['knowledge_points'] - json_initial['knowledge_points']
        db_knowledge_increase = db_after['knowledge_points'] - db_initial['knowledge_points']
        
        if json_knowledge_increase == db_knowledge_increase == 1:
            print("✅ 知識點創建一致")
        else:
            print(f"⚠️ 知識點創建不一致: JSON增加{json_knowledge_increase}, DB增加{db_knowledge_increase}")
        
        # === 測試3: 學習推薦一致性 ===
        print("\n🎯 測試3: 學習推薦一致性")
        
        json_recommendations = json_manager.get_learning_recommendations()
        db_recommendations = await db_manager.get_learning_recommendations()
        
        json_rec_count = len(json_recommendations.get('recommendations', []))
        db_rec_count = len(db_recommendations.get('recommendations', []))
        
        print(f"JSON 推薦數量: {json_rec_count}")
        print(f"DB 推薦數量: {db_rec_count}")
        
        if json_rec_count > 0 and db_rec_count > 0:
            print("✅ 兩種模式都有學習推薦")
        else:
            print("⚠️ 推薦生成可能有問題")
        
        # === 測試4: 複習候選一致性 ===
        print("\n🔄 測試4: 複習候選一致性")
        
        json_candidates = json_manager.get_review_candidates(5)
        db_candidates = await db_manager.get_review_candidates_async(5)
        
        print(f"JSON 複習候選: {len(json_candidates)}個")
        print(f"DB 複習候選: {len(db_candidates)}個")
        
        if len(json_candidates) > 0 and len(db_candidates) > 0:
            # 檢查是否有共同的候選
            json_keys = {p.key_point for p in json_candidates}
            db_keys = {p.key_point for p in db_candidates}
            common_keys = json_keys & db_keys
            
            if len(common_keys) > 0:
                print(f"✅ 有 {len(common_keys)} 個共同的複習候選")
            else:
                print("⚠️ 沒有共同的複習候選")
        
        # === 結果總結 ===
        print(f"\n{'='*50}")
        print("📋 快速驗證結果總結")
        print(f"{'='*50}")
        
        # 計算一致性分數（簡化評估）
        consistency_checks = [
            json_count == db_count,  # 知識點數量一致
            json_categories == db_categories,  # 分類一致
            json_result and db_result,  # 保存功能正常
            json_knowledge_increase == db_knowledge_increase,  # 知識點創建一致
            json_rec_count > 0 and db_rec_count > 0,  # 推薦功能正常
            len(json_candidates) > 0 and len(db_candidates) > 0  # 複習候選正常
        ]
        
        passed_checks = sum(consistency_checks)
        total_checks = len(consistency_checks)
        consistency_score = passed_checks / total_checks
        
        print(f"✅ 通過檢查: {passed_checks}/{total_checks}")
        print(f"🎯 一致性分數: {consistency_score:.1%}")
        
        if consistency_score >= 0.8:
            print("🎉 用戶操作路徑一致性良好！")
            return True
        else:
            print("⚠️ 用戶操作路徑一致性需要改進")
            return False
            
    except Exception as e:
        print(f"❌ 測試執行出錯: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函數"""
    success = await quick_user_journey_test()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)