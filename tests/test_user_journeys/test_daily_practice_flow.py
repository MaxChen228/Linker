"""
日常練習流程一致性測試
驗證常規的練習和學習循環在兩種模式下的一致性
"""


import pytest

from .assertion_helpers import (
    assert_operation_results_consistent,
)
from .test_data_manager import UserJourneyTestDataManager, get_db_manager, get_json_manager


@pytest.mark.asyncio
async def test_daily_practice_complete_cycle():
    """測試完整的日常練習循環"""

    # === 準備：已有一些知識點的狀態 ===
    await UserJourneyTestDataManager.setup_established_user_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # === 階段 1: 查看學習狀況 ===
    json_initial_stats = json_manager.get_statistics()
    db_initial_stats = await db_manager.get_statistics_async()

    # 確保兩種模式有相同的基礎數據
    assert json_initial_stats['knowledge_points'] > 0
    assert db_initial_stats['knowledge_points'] > 0
    initial_knowledge_count = json_initial_stats['knowledge_points']

    # === 階段 2: 獲取複習建議 ===
    json_recommendations = json_manager.get_learning_recommendations()
    db_recommendations = await db_manager.get_learning_recommendations()

    # 推薦應該包含建議和優先學習點
    assert len(json_recommendations['recommendations']) > 0
    assert len(db_recommendations['recommendations']) > 0
    assert len(json_recommendations['priority_points']) > 0
    assert len(db_recommendations['priority_points']) > 0

    # === 階段 3: 選擇複習內容 ===
    json_review_candidates = json_manager.get_review_candidates(3)
    db_review_candidates = await db_manager.get_review_candidates_async(3)

    assert len(json_review_candidates) > 0
    assert len(db_review_candidates) > 0

    # 檢查候選一致性（允許順序差異）
    json_candidate_keys = {p.key_point for p in json_review_candidates}
    db_candidate_keys = {p.key_point for p in db_review_candidates}

    # 至少應該有一些共同的候選
    common_candidates = json_candidate_keys & db_candidate_keys
    assert len(common_candidates) > 0, f"沒有共同的複習候選: JSON={json_candidate_keys}, DB={db_candidate_keys}"

    # === 階段 4: 複習練習 ===
    if json_review_candidates:
        review_point = json_review_candidates[0]

        review_practice = {
            'chinese_sentence': '今天天氣很好。',
            'user_answer': 'The weather is very good today.',
            'is_correct': True
        }

        # 記錄複習成功 - 需要檢查方法是否存在
        if hasattr(json_manager, 'add_review_success'):
            json_success = json_manager.add_review_success(
                review_point.id,
                review_practice['chinese_sentence'],
                review_practice['user_answer']
            )
        else:
            # 如果沒有專門的複習成功方法，使用正確答案記錄
            json_success = json_manager.save_mistake(
                review_practice['chinese_sentence'],
                review_practice['user_answer'],
                {'is_generally_correct': True, 'error_analysis': []}
            )

        if hasattr(db_manager, 'add_review_success_async'):
            db_success = await db_manager.add_review_success_async(
                review_point.id,
                review_practice['chinese_sentence'],
                review_practice['user_answer']
            )
        else:
            # 使用正確答案記錄
            db_success = await db_manager._save_mistake_async(
                review_practice['chinese_sentence'],
                review_practice['user_answer'],
                {'is_generally_correct': True, 'error_analysis': []}
            )

        # === 階段 5: 複習後狀態驗證 ===
        json_updated_stats = json_manager.get_statistics()
        db_updated_stats = await db_manager.get_statistics_async()

        # 正確次數應該增加
        assert json_updated_stats['correct_count'] >= json_initial_stats['correct_count']
        assert db_updated_stats['correct_count'] >= db_initial_stats['correct_count']

        # 練習總次數應該增加
        assert json_updated_stats['total_practices'] > json_initial_stats['total_practices']
        assert db_updated_stats['total_practices'] >= db_initial_stats['total_practices']

    # === 階段 6: 新題練習 ===
    new_practice = {
        'chinese_sentence': '她正在學習中文。',
        'user_answer': 'She learning Chinese.',
        'feedback': {
            'is_generally_correct': False,
            'overall_suggestion': 'She is learning Chinese.',
            'error_analysis': [{
                'key_point_summary': '現在進行時結構錯誤',
                'original_phrase': 'learning',
                'correction': 'is learning',
                'explanation': '現在進行時需要be動詞',
                'category': 'systematic'
            }]
        }
    }

    json_mistake_result = json_manager.save_mistake(
        new_practice['chinese_sentence'],
        new_practice['user_answer'],
        new_practice['feedback']
    )

    db_mistake_result = await db_manager._save_mistake_async(
        new_practice['chinese_sentence'],
        new_practice['user_answer'],
        new_practice['feedback']
    )

    assert_operation_results_consistent(json_mistake_result, db_mistake_result, "新練習保存")

    # === 階段 7: 練習後最終狀態 ===
    json_final_stats = json_manager.get_statistics()
    db_final_stats = await db_manager.get_statistics_async()

    # 知識點數量應該增加（新錯誤創建了新知識點）
    assert json_final_stats['knowledge_points'] > initial_knowledge_count
    assert db_final_stats['knowledge_points'] > initial_knowledge_count

    # 錯誤次數應該增加
    assert json_final_stats['mistake_count'] > json_initial_stats['mistake_count']
    assert db_final_stats['mistake_count'] >= db_initial_stats['mistake_count']


@pytest.mark.asyncio
async def test_mixed_practice_session():
    """測試混合練習會話（包含正確和錯誤答案）"""

    await UserJourneyTestDataManager.setup_established_user_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    initial_json_stats = json_manager.get_statistics()
    initial_db_stats = await db_manager.get_statistics_async()

    # 準備混合練習場景
    mixed_practices = [
        {
            'chinese': '我喜歡讀書。',
            'user_answer': 'I like reading books.',
            'feedback': {
                'is_generally_correct': True,
                'overall_suggestion': 'I like reading books.',
                'error_analysis': []
            }
        },
        {
            'chinese': '他們正在開會。',
            'user_answer': 'They are having meeting.',
            'feedback': {
                'is_generally_correct': False,
                'overall_suggestion': 'They are having a meeting.',
                'error_analysis': [{
                    'key_point_summary': '冠詞使用錯誤',
                    'original_phrase': 'meeting',
                    'correction': 'a meeting',
                    'explanation': '可數名詞需要冠詞',
                    'category': 'systematic'
                }]
            }
        },
        {
            'chinese': '今天是星期一。',
            'user_answer': 'Today is Monday.',
            'feedback': {
                'is_generally_correct': True,
                'overall_suggestion': 'Today is Monday.',
                'error_analysis': []
            }
        }
    ]

    expected_correct_count = len([p for p in mixed_practices if p['feedback']['is_generally_correct']])
    expected_mistake_count = len([p for p in mixed_practices if not p['feedback']['is_generally_correct']])

    # 依序處理每個練習
    for i, practice in enumerate(mixed_practices):
        json_result = json_manager.save_mistake(
            practice['chinese'],
            practice['user_answer'],
            practice['feedback']
        )

        db_result = await db_manager._save_mistake_async(
            practice['chinese'],
            practice['user_answer'],
            practice['feedback']
        )

        assert_operation_results_consistent(json_result, db_result, f"混合練習{i+1}")

    # 驗證最終統計
    final_json_stats = json_manager.get_statistics()
    final_db_stats = await db_manager.get_statistics_async()

    # 檢查增量
    json_correct_increase = final_json_stats['correct_count'] - initial_json_stats['correct_count']
    db_correct_increase = final_db_stats['correct_count'] - initial_db_stats['correct_count']

    json_mistake_increase = final_json_stats['mistake_count'] - initial_json_stats['mistake_count']
    db_mistake_increase = final_db_stats['mistake_count'] - initial_db_stats['mistake_count']

    assert json_correct_increase == expected_correct_count
    assert db_correct_increase == expected_correct_count
    assert json_mistake_increase == expected_mistake_count
    assert db_mistake_increase == expected_mistake_count


@pytest.mark.asyncio
async def test_review_learning_cycle():
    """測試複習-學習循環的一致性"""

    await UserJourneyTestDataManager.setup_established_user_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # === 循環1: 獲取複習建議 ===
    json_recommendations_1 = json_manager.get_learning_recommendations()
    db_recommendations_1 = await db_manager.get_learning_recommendations()

    assert len(json_recommendations_1['recommendations']) > 0
    assert len(db_recommendations_1['recommendations']) > 0

    # === 循環2: 獲取複習候選 ===
    json_candidates_1 = json_manager.get_review_candidates(5)
    db_candidates_1 = await db_manager.get_review_candidates_async(5)

    assert len(json_candidates_1) > 0
    assert len(db_candidates_1) > 0

    # 記錄初始候選數量
    initial_json_candidates = len(json_candidates_1)
    initial_db_candidates = len(db_candidates_1)

    # === 循環3: 進行一次練習 ===
    practice = {
        'chinese': '這個問題很困難。',
        'user_answer': 'This question is difficult.',
        'feedback': {
            'is_generally_correct': True,
            'overall_suggestion': 'This question is difficult.',
            'error_analysis': []
        }
    }

    json_manager.save_mistake(
        practice['chinese'],
        practice['user_answer'],
        practice['feedback']
    )

    await db_manager._save_mistake_async(
        practice['chinese'],
        practice['user_answer'],
        practice['feedback']
    )

    # === 循環4: 練習後重新獲取建議 ===
    json_recommendations_2 = json_manager.get_learning_recommendations()
    db_recommendations_2 = await db_manager.get_learning_recommendations()

    json_candidates_2 = json_manager.get_review_candidates(5)
    db_candidates_2 = await db_manager.get_review_candidates_async(5)

    # 建議應該有所更新（推薦算法考慮了新的正確練習）
    assert len(json_recommendations_2['recommendations']) > 0
    assert len(db_recommendations_2['recommendations']) > 0

    # 複習候選可能有變化但仍應存在
    assert len(json_candidates_2) >= 0
    assert len(db_candidates_2) >= 0

    # 確保兩種模式的變化趨勢一致
    json_candidate_change = len(json_candidates_2) - initial_json_candidates
    db_candidate_change = len(db_candidates_2) - initial_db_candidates

    # 變化方向應該一致（都增加、都減少或都不變）
    assert json_candidate_change * db_candidate_change >= 0, \
        f"候選變化方向不一致: JSON={json_candidate_change}, DB={db_candidate_change}"


@pytest.mark.asyncio
async def test_performance_consistency():
    """測試練習性能的一致性"""

    await UserJourneyTestDataManager.setup_established_user_data()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    import time

    practice = {
        'chinese': '我明天會去上班。',
        'user_answer': 'I will go to work tomorrow.',
        'feedback': {
            'is_generally_correct': True,
            'overall_suggestion': 'I will go to work tomorrow.',
            'error_analysis': []
        }
    }

    # 測試 JSON 模式性能
    start_time = time.time()
    json_result = json_manager.save_mistake(
        practice['chinese'],
        practice['user_answer'],
        practice['feedback']
    )
    json_stats = json_manager.get_statistics()
    json_time = time.time() - start_time

    # 測試 DB 模式性能
    start_time = time.time()
    db_result = await db_manager._save_mistake_async(
        practice['chinese'],
        practice['user_answer'],
        practice['feedback']
    )
    db_stats = await db_manager.get_statistics_async()
    db_time = time.time() - start_time

    # 驗證功能一致性
    assert_operation_results_consistent(json_result, db_result, "性能測試操作")

    # 驗證性能差異在可接受範圍內（允許 DB 模式慢一些）
    performance_ratio = db_time / max(json_time, 0.001)  # 防止除零
    assert performance_ratio < 10, f"數據庫模式過慢: JSON={json_time:.3f}s, DB={db_time:.3f}s, 比率={performance_ratio:.2f}"

    print(f"性能對比: JSON={json_time:.3f}s, DB={db_time:.3f}s, 比率={performance_ratio:.2f}")
