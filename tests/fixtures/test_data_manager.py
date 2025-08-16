"""
用戶路徑測試數據管理器
提供各種測試場景的數據準備和管理功能
"""

import random
from datetime import datetime, timedelta
from typing import Any

from core.database.adapter import KnowledgeManagerAdapter
from core.error_types import ErrorCategory
from core.knowledge import KnowledgeManager, KnowledgePoint


class UserJourneyTestDataManager:
    """用戶路徑測試數據管理器"""

    @staticmethod
    async def reset_all_data() -> None:
        """重置所有數據到空狀態"""
        # 重置 JSON 模式
        json_manager = KnowledgeManager()
        json_manager.knowledge_points = []
        json_manager.practice_history = []
        # KnowledgeManager 是自動保存的，不需要手動保存
        # 數據會在修改時自動寫入檔案

        # 重置 Database 模式
        db_manager = get_db_manager()
        await db_manager._ensure_initialized()

        # 在測試模式下，db_manager 實際上是 JSON 模式
        # 所以不需要清空資料庫表
        if hasattr(db_manager, "_legacy_manager"):
            # JSON 模式：直接清空記憶體數據
            db_manager._legacy_manager.knowledge_points = []
            db_manager._legacy_manager.practice_history = []
        elif db_manager._repository:
            # 真實資料庫模式（僅在非測試環境）
            from core.database.connection import DatabaseConnection

            db_conn = DatabaseConnection()
            async with db_conn.get_connection() as conn:
                await conn.execute("DELETE FROM practice_history")
                await conn.execute("DELETE FROM knowledge_points")
                await conn.commit()

    @staticmethod
    async def setup_new_user_environment() -> None:
        """設置新用戶環境（空數據）"""
        await UserJourneyTestDataManager.reset_all_data()

    @staticmethod
    def create_test_knowledge_point(
        id: int,
        key_point: str,
        category: ErrorCategory,
        mastery_level: float = 0.1,
        mistake_count: int = 1,
        correct_count: int = 0,
        created_at: str = None,
    ) -> dict[str, Any]:
        """創建測試知識點數據"""
        if created_at is None:
            created_at = datetime.now().isoformat()

        return {
            "id": id,
            "key_point": key_point,
            "original_phrase": f"原始短語 {id}",
            "correction": f"修正 {id}",
            "explanation": f"解釋 {id}",
            "category": category,
            "subtype": "general",
            "mastery_level": mastery_level,
            "mistake_count": mistake_count,
            "correct_count": correct_count,
            "last_seen": created_at,
            "next_review": (
                datetime.fromisoformat(created_at.replace("Z", "+00:00")) + timedelta(days=1)
            ).isoformat(),
            "created_at": created_at,
            "is_deleted": False,
            "deleted_reason": "",
            "deleted_at": "",
            "custom_notes": "",
            "tags": [],
            "review_examples": [],
            "version_history": [],
            "last_modified": created_at,
            "original_error": {
                "chinese_sentence": f"中文句子 {id}",
                "user_answer": f"用戶回答 {id}",
                "correct_answer": f"正確答案 {id}",
                "timestamp": created_at,
            },
        }

    @staticmethod
    async def setup_established_user_data() -> None:
        """設置已有數據的用戶環境"""
        await UserJourneyTestDataManager.reset_all_data()

        # 創建10個知識點
        knowledge_points = []
        categories = list(ErrorCategory)

        for i in range(1, 11):
            category = categories[i % len(categories)]
            point = UserJourneyTestDataManager.create_test_knowledge_point(
                id=i,
                key_point=f"測試知識點 {i}",
                category=category,
                mastery_level=random.uniform(0.1, 0.9),
                mistake_count=random.randint(1, 5),
                correct_count=random.randint(0, 3),
                created_at=(datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            )
            knowledge_points.append(point)

        await UserJourneyTestDataManager.load_test_data_to_both_modes(knowledge_points)

    @staticmethod
    async def setup_diverse_knowledge_points() -> None:
        """設置多樣化的知識點數據用於搜索測試"""
        await UserJourneyTestDataManager.reset_all_data()

        test_points = [
            # 動詞相關
            {"key_point": "動詞時態錯誤", "category": ErrorCategory.SYSTEMATIC},
            {"key_point": "動詞語態使用錯誤", "category": ErrorCategory.SYSTEMATIC},
            {"key_point": "動詞不規則變化", "category": ErrorCategory.ISOLATED},
            # 語法相關
            {"key_point": "語法結構錯誤", "category": ErrorCategory.SYSTEMATIC},
            {"key_point": "Grammar pattern mistake", "category": ErrorCategory.ENHANCEMENT},
            # 其他
            {"key_point": "詞彙選擇問題", "category": ErrorCategory.OTHER},
            {"key_point": "標點符號使用", "category": ErrorCategory.ENHANCEMENT},
        ]

        knowledge_points = []
        for i, point_data in enumerate(test_points, 1):
            point = UserJourneyTestDataManager.create_test_knowledge_point(
                id=i,
                key_point=point_data["key_point"],
                category=point_data["category"],
                mastery_level=random.uniform(0.2, 0.8),
            )
            knowledge_points.append(point)

        await UserJourneyTestDataManager.load_test_data_to_both_modes(knowledge_points)

    @staticmethod
    async def setup_rich_statistical_data() -> None:
        """設置豐富的統計數據"""
        await UserJourneyTestDataManager.reset_all_data()

        categories = list(ErrorCategory)
        knowledge_points = []

        # 每個分類創建5個知識點
        for i, category in enumerate(categories):
            for j in range(5):
                point_id = i * 5 + j + 1
                point = UserJourneyTestDataManager.create_test_knowledge_point(
                    id=point_id,
                    key_point=f"{category.value} 知識點 {j + 1}",
                    category=category,
                    mastery_level=random.uniform(0, 1),
                    mistake_count=random.randint(1, 8),
                    correct_count=random.randint(0, 5),
                )
                knowledge_points.append(point)

        await UserJourneyTestDataManager.load_test_data_to_both_modes(knowledge_points)

    @staticmethod
    async def load_test_data_to_both_modes(knowledge_points: list[dict[str, Any]]) -> None:
        """將測試數據加載到兩種模式"""
        # 加載到 JSON 模式
        json_manager = KnowledgeManager()
        json_manager.knowledge_points = []

        for point_data in knowledge_points:
            kp = KnowledgePoint(**point_data)
            json_manager.knowledge_points.append(kp)

        # KnowledgeManager 是自動保存的，不需要手動保存
        # 數據會在修改時自動寫入檔案

        # 加載到 Database 模式（測試環境會自動使用 JSON 模式）
        db_manager = get_db_manager()
        await db_manager._ensure_initialized()

        if db_manager._repository:
            # 在測試環境下，我們使用 JSON 模式，所以不需要調用 repository
            # 如果是真實資料庫模式，才需要調用
            pass  # 測試模式下兩個 manager 實際上都是 JSON 模式

    @staticmethod
    async def create_practice_history(manager, count: int = 20) -> None:
        """創建練習歷史"""
        practice_scenarios = [
            {
                "chinese": "我喜歡吃蘋果。",
                "user_answer": "I like eat apple.",
                "correct": "I like eating apples.",
                "is_correct": False,
                "errors": [{"key_point": "動名詞用法", "category": "systematic"}],
            },
            {
                "chinese": "她很聰明。",
                "user_answer": "She is very smart.",
                "correct": "She is very smart.",
                "is_correct": True,
                "errors": [],
            },
            {
                "chinese": "昨天下雨了。",
                "user_answer": "Yesterday was rain.",
                "correct": "It rained yesterday.",
                "is_correct": False,
                "errors": [{"key_point": "動詞時態", "category": "systematic"}],
            },
        ]

        for _i in range(count):
            scenario = random.choice(practice_scenarios)

            feedback = {
                "is_generally_correct": scenario["is_correct"],
                "overall_suggestion": scenario["correct"],
                "error_analysis": scenario["errors"],
            }

            if hasattr(manager, "save_mistake"):
                manager.save_mistake(scenario["chinese"], scenario["user_answer"], feedback)
            else:
                await manager._save_mistake_async(
                    scenario["chinese"], scenario["user_answer"], feedback
                )


def get_json_manager() -> KnowledgeManager:
    """獲取 JSON 模式管理器"""
    return KnowledgeManager()


def get_db_manager() -> KnowledgeManagerAdapter:
    """獲取 Database 模式管理器

    在測試環境中應該使用 mock 或 JSON 模式，
    避免連接真實資料庫
    """
    import os

    # 在測試環境中強制使用 JSON 模式
    if os.environ.get("TESTING", "true").lower() == "true":
        return KnowledgeManagerAdapter(use_database=False)
    return KnowledgeManagerAdapter(use_database=True)
