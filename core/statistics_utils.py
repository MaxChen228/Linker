"""
統一統計計算工具模組

提供 JSON 和 Database 模式統一的統計計算邏輯，確保兩種模式結果一致。
TASK-19D: 統一統計計算邏輯
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.error_types import ErrorCategory
from core.log_config import get_module_logger


@dataclass
class PracticeRecord:
    """統一的練習記錄格式"""

    chinese_sentence: str
    user_answer: str
    correct_answer: str
    timestamp: str
    is_correct: bool
    record_type: str  # 'original_error', 'review_example', 'practice_history'


class UnifiedStatistics:
    """統一的統計計算邏輯

    此類提供標準化的統計計算方法，確保 JSON 和 Database 模式使用相同的邏輯。
    根據 TASK-19D 分析結果設計，解決練習次數不一致問題。
    """

    def __init__(self):
        self.logger = get_module_logger(self.__class__.__name__)

    @staticmethod
    def calculate_practice_statistics(
        knowledge_points: list,
        practice_records: list[PracticeRecord],
        include_original_errors: bool = True,
    ) -> dict[str, Any]:
        """統一計算練習統計數據

        統一標準：
        1. 總練習次數 = 所有練習記錄的總和
        2. 正確次數 = is_correct=True 的記錄總數
        3. 知識點數量 = 未軟刪除的知識點數量
        4. 平均掌握度 = 所有知識點掌握度的平均值

        Args:
            knowledge_points: 知識點列表
            practice_records: 統一格式的練習記錄列表
            include_original_errors: 是否包含原始錯誤在練習統計中

        Returns:
            統計結果字典
        """
        logger = get_module_logger("UnifiedStatistics")

        # 基礎統計計算
        total_practices = len(practice_records)
        correct_count = sum(1 for record in practice_records if record.is_correct)
        mistake_count = total_practices - correct_count

        # 知識點統計
        active_points = [
            point for point in knowledge_points if not getattr(point, "is_deleted", False)
        ]
        total_knowledge_points = len(active_points)

        # 平均掌握度計算
        if active_points:
            mastery_levels = [getattr(point, "mastery_level", 0.0) for point in active_points]
            avg_mastery = sum(mastery_levels) / len(mastery_levels)
        else:
            avg_mastery = 0.0

        # 分類分布統計（使用統一順序）
        category_stats = {
            ErrorCategory.SYSTEMATIC: 0,
            ErrorCategory.ISOLATED: 0,
            ErrorCategory.ENHANCEMENT: 0,
            ErrorCategory.OTHER: 0,
        }

        for point in active_points:
            category = getattr(point, "category", ErrorCategory.OTHER)
            if category in category_stats:
                category_stats[category] += 1

        # 轉換為中文並按統一順序排列
        category_distribution = {}
        category_order = [
            ErrorCategory.SYSTEMATIC,  # 系統性錯誤
            ErrorCategory.ISOLATED,  # 單一性錯誤
            ErrorCategory.ENHANCEMENT,  # 可以更好
            ErrorCategory.OTHER,  # 其他錯誤
        ]

        for category in category_order:
            count = category_stats[category]
            if count > 0:
                category_distribution[category.to_chinese()] = count

        # 子類型分布統計
        subtype_stats = {}
        for point in active_points:
            subtype = getattr(point, "subtype", "unknown")
            subtype_stats[subtype] = subtype_stats.get(subtype, 0) + 1

        # 待複習知識點統計
        due_reviews = 0
        for point in active_points:
            if hasattr(point, "is_due_for_review") and callable(point.is_due_for_review):
                if point.is_due_for_review():
                    due_reviews += 1
            elif hasattr(point, "next_review"):
                try:
                    next_review = point.next_review
                    if isinstance(next_review, str):
                        next_review = datetime.fromisoformat(next_review.replace("Z", "+00:00"))
                    if next_review <= datetime.now(
                        next_review.tzinfo
                        if hasattr(next_review, "tzinfo") and next_review.tzinfo
                        else None
                    ):
                        due_reviews += 1
                except Exception:
                    pass

        # 準確率計算
        accuracy = correct_count / total_practices if total_practices > 0 else 0.0

        logger.debug(
            f"統計計算完成: 練習{total_practices}, 正確{correct_count}, 知識點{total_knowledge_points}"
        )

        return {
            "total_practices": total_practices,
            "correct_count": correct_count,
            "mistake_count": mistake_count,
            "accuracy": accuracy,
            "knowledge_points": total_knowledge_points,
            "avg_mastery": round(avg_mastery, 6),
            "category_distribution": category_distribution,
            "subtype_distribution": subtype_stats,
            "due_reviews": due_reviews,
        }

    @staticmethod
    def extract_json_practice_records(knowledge_manager) -> list[PracticeRecord]:
        """從 JSON 模式的 KnowledgeManager 提取統一格式的練習記錄

        統一策略：使用與 Database 模式相同的數據來源
        - original_errors: 來自知識點的原始錯誤
        - review_examples: 來自知識點的複習例句
        - 忽略 practice_history，因為 Database 模式沒有此表

        Args:
            knowledge_manager: JSON 模式的 KnowledgeManager 實例

        Returns:
            統一格式的練習記錄列表
        """
        records = []

        # 採用與 Database 模式相同的數據來源：只從知識點中提取記錄
        for point in knowledge_manager.knowledge_points:
            # 1. 原始錯誤記錄
            if hasattr(point, "original_error") and point.original_error:
                record = PracticeRecord(
                    chinese_sentence=point.original_error.chinese_sentence,
                    user_answer=point.original_error.user_answer,
                    correct_answer=point.original_error.correct_answer,
                    timestamp=point.original_error.timestamp,
                    is_correct=False,  # 原始錯誤總是錯誤的
                    record_type="original_error",
                )
                records.append(record)

            # 2. 複習例句記錄
            if hasattr(point, "review_examples"):
                for example in point.review_examples:
                    record = PracticeRecord(
                        chinese_sentence=example.chinese_sentence,
                        user_answer=example.user_answer,
                        correct_answer=example.correct_answer,
                        timestamp=example.timestamp,
                        is_correct=example.is_correct,
                        record_type="review_example",
                    )
                    records.append(record)

        return records

    @staticmethod
    async def extract_database_practice_records(adapter) -> list[PracticeRecord]:
        """從 Database 模式的適配器提取統一格式的練習記錄

        Args:
            adapter: Database 模式的 KnowledgeManagerAdapter 實例

        Returns:
            統一格式的練習記錄列表
        """
        records = []

        try:
            await adapter._ensure_initialized()

            if hasattr(adapter, "_repository") and adapter._repository:
                async with adapter._repository.connection() as conn:
                    # 1. 提取 original_errors
                    original_rows = await conn.fetch("""
                        SELECT oe.*, kp.is_deleted
                        FROM original_errors oe
                        JOIN knowledge_points kp ON oe.knowledge_point_id = kp.id
                        WHERE kp.is_deleted = FALSE
                        ORDER BY oe.timestamp
                    """)

                    for row in original_rows:
                        record = PracticeRecord(
                            chinese_sentence=row["chinese_sentence"],
                            user_answer=row["user_answer"],
                            correct_answer=row["correct_answer"],
                            timestamp=row["timestamp"].isoformat() if row["timestamp"] else "",
                            is_correct=False,  # 原始錯誤總是錯誤的
                            record_type="original_error",
                        )
                        records.append(record)

                    # 2. 提取 review_examples
                    review_rows = await conn.fetch("""
                        SELECT re.*, kp.is_deleted
                        FROM review_examples re
                        JOIN knowledge_points kp ON re.knowledge_point_id = kp.id
                        WHERE kp.is_deleted = FALSE
                        ORDER BY re.timestamp
                    """)

                    for row in review_rows:
                        record = PracticeRecord(
                            chinese_sentence=row["chinese_sentence"],
                            user_answer=row["user_answer"],
                            correct_answer=row["correct_answer"],
                            timestamp=row["timestamp"].isoformat() if row["timestamp"] else "",
                            is_correct=row["is_correct"],
                            record_type="review_example",
                        )
                        records.append(record)

        except Exception as e:
            logger = get_module_logger("UnifiedStatistics")
            logger.error(f"提取數據庫練習記錄失敗: {e}")

        return records

    @staticmethod
    def normalize_practice_records(records: list[PracticeRecord]) -> list[PracticeRecord]:
        """標準化練習記錄，移除重複並排序

        Args:
            records: 原始練習記錄列表

        Returns:
            標準化後的練習記錄列表
        """
        # 去重：基於內容和時間戳
        seen = set()
        unique_records = []

        for record in records:
            key = (
                record.chinese_sentence,
                record.user_answer,
                record.timestamp,
                record.record_type,
            )
            if key not in seen:
                seen.add(key)
                unique_records.append(record)

        # 按時間戳排序
        import contextlib
        
        with contextlib.suppress(Exception):
            unique_records.sort(
                key=lambda r: datetime.fromisoformat(r.timestamp.replace("Z", "+00:00"))
                if r.timestamp
                else datetime.min
            )

        return unique_records
