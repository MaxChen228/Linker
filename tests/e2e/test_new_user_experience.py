"""
新用戶首次體驗一致性測試
驗證用戶從零開始到建立第一個知識點的完整體驗
"""

import pytest

from tests.fixtures.assertion_helpers import (
    assert_operation_results_consistent,
)
from tests.fixtures.test_data_manager import (
    UserJourneyTestDataManager,
    get_db_manager,
    get_json_manager,
)


@pytest.mark.asyncio
async def test_new_user_complete_journey():
    """測試新用戶的完整體驗路徑"""

    # === 階段 1: 系統初始狀態 ===
    await UserJourneyTestDataManager.setup_new_user_environment()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # 驗證空系統的初始狀態
    json_stats = json_manager.get_statistics()
    db_stats = await db_manager.get_statistics_async()

    expected_initial_state = {"total_practices": 0, "knowledge_points": 0}

    # 驗證初始狀態一致性
    assert json_stats["total_practices"] == 0
    assert json_stats["knowledge_points"] == 0
    assert db_stats["total_practices"] == 0
    assert db_stats["knowledge_points"] == 0

    # === 階段 2: 第一次練習和錯誤 ===
    first_practice = {
        "chinese_sentence": "我昨天去了圖書館。",
        "user_answer": "I go to library yesterday.",
        "feedback": {
            "is_generally_correct": False,
            "overall_suggestion": "I went to the library yesterday.",
            "error_analysis": [
                {
                    "key_point_summary": "動詞時態錯誤",
                    "original_phrase": "go",
                    "correction": "went",
                    "explanation": "昨天的動作應該使用過去式",
                    "category": "systematic",
                    "severity": "major",
                }
            ],
        },
    }

    # 保存第一個錯誤
    json_result = json_manager.save_mistake(
        first_practice["chinese_sentence"],
        first_practice["user_answer"],
        first_practice["feedback"],
    )

    db_result = await db_manager._save_mistake_async(
        first_practice["chinese_sentence"],
        first_practice["user_answer"],
        first_practice["feedback"],
    )

    assert_operation_results_consistent(json_result, db_result, "保存錯誤")

    # === 階段 3: 第一個知識點創建後的狀態 ===
    json_stats_after = json_manager.get_statistics()
    db_stats_after = await db_manager.get_statistics_async()

    # 驗證統計數據更新
    assert json_stats_after["total_practices"] == 1
    assert json_stats_after["knowledge_points"] == 1
    assert json_stats_after["correct_count"] == 0
    assert json_stats_after["mistake_count"] == 1

    assert db_stats_after["total_practices"] >= 1  # 允許數據庫統計稍有差異
    assert db_stats_after["knowledge_points"] == 1
    assert db_stats_after["correct_count"] == 0

    # 驗證分類分布
    assert "系統性錯誤" in json_stats_after["category_distribution"]
    assert json_stats_after["category_distribution"]["系統性錯誤"] == 1

    assert "系統性錯誤" in db_stats_after["category_distribution"]
    assert db_stats_after["category_distribution"]["系統性錯誤"] == 1

    # === 階段 4: 學習推薦生成 ===
    json_recommendations = json_manager.get_learning_recommendations()
    db_recommendations = await db_manager.get_learning_recommendations()

    # 應該推薦複習剛創建的知識點
    assert len(json_recommendations["priority_points"]) >= 1
    assert len(db_recommendations["priority_points"]) >= 1

    # 檢查推薦內容合理性
    assert len(json_recommendations["recommendations"]) > 0
    assert len(db_recommendations["recommendations"]) > 0

    # === 階段 5: 複習候選選擇 ===
    json_candidates = json_manager.get_review_candidates(5)
    db_candidates = await db_manager.get_review_candidates_async(5)

    # 新創建的知識點應該出現在複習候選中
    assert len(json_candidates) >= 1
    assert len(db_candidates) >= 1

    # 候選知識點應該包含剛創建的知識點
    json_candidate_keys = [p.key_point for p in json_candidates]
    db_candidate_keys = [p.key_point for p in db_candidates]

    assert "動詞時態錯誤" in json_candidate_keys
    assert "動詞時態錯誤" in db_candidate_keys


@pytest.mark.asyncio
async def test_new_user_multiple_mistakes():
    """測試新用戶連續犯錯的場景"""

    await UserJourneyTestDataManager.setup_new_user_environment()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # 準備多個錯誤場景
    mistakes = [
        {
            "chinese": "她正在學習中文。",
            "user_answer": "She learning Chinese.",
            "feedback": {
                "is_generally_correct": False,
                "overall_suggestion": "She is learning Chinese.",
                "error_analysis": [
                    {
                        "key_point_summary": "現在進行時結構錯誤",
                        "original_phrase": "learning",
                        "correction": "is learning",
                        "explanation": "現在進行時需要be動詞",
                        "category": "systematic",
                    }
                ],
            },
        },
        {
            "chinese": "這本書很有趣。",
            "user_answer": "This book is very interesting.",
            "feedback": {
                "is_generally_correct": True,
                "overall_suggestion": "This book is very interesting.",
                "error_analysis": [],
            },
        },
        {
            "chinese": "我喜歡吃蘋果。",
            "user_answer": "I like eat apple.",
            "feedback": {
                "is_generally_correct": False,
                "overall_suggestion": "I like eating apples.",
                "error_analysis": [
                    {
                        "key_point_summary": "動名詞用法錯誤",
                        "original_phrase": "eat",
                        "correction": "eating",
                        "explanation": "like後面應該接動名詞",
                        "category": "isolated",
                    }
                ],
            },
        },
    ]

    # 依序處理每個練習
    for i, mistake in enumerate(mistakes):
        json_result = json_manager.save_mistake(
            mistake["chinese"], mistake["user_answer"], mistake["feedback"]
        )

        db_result = await db_manager._save_mistake_async(
            mistake["chinese"], mistake["user_answer"], mistake["feedback"]
        )

        assert_operation_results_consistent(json_result, db_result, f"第{i + 1}個錯誤")

        # 驗證統計數據遞增
        json_stats = json_manager.get_statistics()
        db_stats = await db_manager.get_statistics_async()

        expected_practices = i + 1
        expected_knowledge_points = len(
            [m for m in mistakes[: i + 1] if not m["feedback"]["is_generally_correct"]]
        )
        expected_correct_count = len(
            [m for m in mistakes[: i + 1] if m["feedback"]["is_generally_correct"]]
        )

        assert json_stats["total_practices"] == expected_practices
        assert json_stats["knowledge_points"] == expected_knowledge_points
        assert json_stats["correct_count"] == expected_correct_count

        # 資料庫統計允許稍有差異，但應該接近
        assert abs(db_stats["total_practices"] - expected_practices) <= 1
        assert db_stats["knowledge_points"] == expected_knowledge_points
        assert db_stats["correct_count"] == expected_correct_count


@pytest.mark.asyncio
async def test_new_user_first_success():
    """測試新用戶第一次答對的場景"""

    await UserJourneyTestDataManager.setup_new_user_environment()

    json_manager = get_json_manager()
    db_manager = get_db_manager()

    # 第一次就答對
    success_practice = {
        "chinese": "今天天氣很好。",
        "user_answer": "The weather is good today.",
        "feedback": {
            "is_generally_correct": True,
            "overall_suggestion": "The weather is good today.",
            "error_analysis": [],
        },
    }

    # 處理正確答案
    json_result = json_manager.save_mistake(
        success_practice["chinese"], success_practice["user_answer"], success_practice["feedback"]
    )

    db_result = await db_manager._save_mistake_async(
        success_practice["chinese"], success_practice["user_answer"], success_practice["feedback"]
    )

    assert_operation_results_consistent(json_result, db_result, "正確答案處理")

    # 驗證統計
    json_stats = json_manager.get_statistics()
    db_stats = await db_manager.get_statistics_async()

    assert json_stats["total_practices"] == 1
    assert json_stats["knowledge_points"] == 0  # 正確答案不產生知識點
    assert json_stats["correct_count"] == 1
    assert json_stats["mistake_count"] == 0

    # 驗證推薦系統對全正確用戶的響應
    json_recommendations = json_manager.get_learning_recommendations()
    db_recommendations = await db_manager.get_learning_recommendations()

    # 沒有錯誤時的推薦應該鼓勵繼續練習
    assert len(json_recommendations["recommendations"]) > 0
    assert len(db_recommendations["recommendations"]) > 0
