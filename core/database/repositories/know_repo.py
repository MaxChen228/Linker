"""
知識點 Repository 實作

此模組遵循 Repository 設計模式，提供一個抽象層來處理 `KnowledgePoint` 模型與資料庫之間的互動。
它封裝了所有 SQL 查詢邏輯，使得業務邏輯層（如 `DatabaseKnowledgeManager`）可以與資料庫解耦。

主要功能：
- 完整的 `KnowledgePoint` CRUD (Create, Read, Update, Delete) 操作。
- 處理與 `KnowledgePoint` 相關的資料，如 `OriginalError`, `ReviewExample`, 和 `Tag`。
- 執行複雜的查詢，例如獲取待複習的知識點、全文搜索和統計。
- 將資料庫記錄（row）與應用程式的資料模型（dataclass）進行轉換。
"""

from datetime import datetime
from typing import Any, Optional

import asyncpg

from core.database.base import BaseRepository
from core.error_types import ErrorCategory
from core.models import KnowledgePoint, OriginalError, ReviewExample


class KnowledgePointRepository(BaseRepository[KnowledgePoint]):
    """
    知識點資料庫操作層。

    負責處理 `knowledge_points` 表及相關聯資料表的所有資料庫操作。
    """

    def _row_to_knowledge_point(self, row: asyncpg.Record) -> KnowledgePoint:
        """
        將資料庫記錄（`asyncpg.Record`）轉換為 `KnowledgePoint` 資料模型物件。

        Args:
            row: 從資料庫查詢返回的一行記錄。

        Returns:
            一個填充了資料的 `KnowledgePoint` 物件。
        """
        # 安全地處理可能為 NULL 的時間戳，避免 `None.isoformat()` 錯誤
        oe_timestamp = row.get("oe_timestamp") or datetime.now()
        original_error = OriginalError(
            chinese_sentence=row.get("oe_chinese", ""),
            user_answer=row.get("oe_user_answer", ""),
            correct_answer=row.get("oe_correct_answer", ""),
            timestamp=oe_timestamp.isoformat(),
        )

        review_examples = []
        if row.get("review_examples"):
            for example_data in row["review_examples"]:
                if example_data:  # 過濾掉可能的 NULL 值
                    review_examples.append(ReviewExample(**example_data))

        return KnowledgePoint(
            id=row["id"],
            key_point=row["key_point"],
            category=ErrorCategory.from_string(row["category"]),
            subtype=row.get("subtype", ""),
            explanation=row["explanation"],
            original_phrase=row["original_phrase"],
            correction=row["correction"],
            original_error=original_error,
            review_examples=review_examples,
            mastery_level=float(row["mastery_level"]),
            mistake_count=row["mistake_count"],
            correct_count=row["correct_count"],
            created_at=row["created_at"].isoformat() if row.get("created_at") else "",
            last_seen=row["last_seen"].isoformat() if row.get("last_seen") else "",
            next_review=row["next_review"].isoformat() if row.get("next_review") else "",
            is_deleted=row["is_deleted"],
            deleted_at=row["deleted_at"].isoformat() if row.get("deleted_at") else "",
            deleted_reason=row.get("deleted_reason", ""),
            tags=row.get("tags") or [],
            custom_notes=row.get("custom_notes", ""),
            version_history=[],  # 版本歷史通常在需要時才另外載入，以提高效能
            last_modified=(row.get("last_modified") or row.get("created_at")).isoformat(),
        )

    async def find_by_id(self, id: int) -> Optional[KnowledgePoint]:
        """
        根據 ID 查詢單個知識點，並連接查詢其所有關聯資料。

        Args:
            id: 知識點的 ID。

        Returns:
            一個完整的 `KnowledgePoint` 物件，如果找不到則返回 None。
        """
        query = """
            SELECT
                kp.*,
                oe.chinese_sentence as oe_chinese,
                oe.user_answer as oe_user_answer,
                oe.correct_answer as oe_correct_answer,
                oe.timestamp as oe_timestamp,
                array_agg(
                    json_build_object(
                        'chinese_sentence', re.chinese_sentence,
                        'user_answer', re.user_answer,
                        'correct_answer', re.correct_answer,
                        'timestamp', re.timestamp,
                        'is_correct', re.is_correct
                    ) ORDER BY re.timestamp DESC
                ) FILTER (WHERE re.id IS NOT NULL) as review_examples,
                array_agg(DISTINCT t.name) FILTER (WHERE t.id IS NOT NULL) as tags
            FROM knowledge_points kp
            LEFT JOIN original_errors oe ON kp.id = oe.knowledge_point_id
            LEFT JOIN review_examples re ON kp.id = re.knowledge_point_id
            LEFT JOIN knowledge_point_tags kpt ON kp.id = kpt.knowledge_point_id
            LEFT JOIN tags t ON kpt.tag_id = t.id
            WHERE kp.id = $1
            GROUP BY kp.id, oe.id
        """
        async with self.connection() as conn:
            try:
                row = await conn.fetchrow(query, id)
                return self._row_to_knowledge_point(row) if row else None
            except Exception as e:
                self._handle_database_error(e, f"find_by_id({id})")
                raise

    async def find_all(self, **filters) -> list[KnowledgePoint]:
        """
        查詢所有知識點，支援多種過濾條件。
        為了效能，此查詢不包含詳細的關聯資料（如複習例句）。

        Args:
            **filters: 過濾條件字典，例如 `is_deleted=False`。

        Returns:
            符合條件的知識點列表。
        """
        include_deleted = filters.pop("include_deleted", False)
        if not include_deleted and "is_deleted" not in filters:
            filters["is_deleted"] = False

        base_query = "SELECT * FROM knowledge_points"
        where_clause, parameters = self._build_where_clause(filters)
        query = f"{base_query} {where_clause} ORDER BY last_seen DESC"

        async with self.connection() as conn:
            try:
                rows = await conn.fetch(query, *parameters)
                return [self._row_to_knowledge_point(row) for row in rows]
            except Exception as e:
                self._handle_database_error(e, f"find_all({filters})")
                raise

    async def create(self, entity: KnowledgePoint) -> KnowledgePoint:
        """
        在資料庫中創建一個新的知識點及其所有關聯資料（在一個事務中完成）。

        Args:
            entity: 要創建的 `KnowledgePoint` 物件。

        Returns:
            創建後並帶有新 ID 的 `KnowledgePoint` 物件。
        """
        async with self.transaction() as conn:
            try:
                kp_query = """
                    INSERT INTO knowledge_points (key_point, category, subtype, explanation, original_phrase, correction, mastery_level, mistake_count, correct_count, created_at, last_seen, next_review, custom_notes, last_modified)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) RETURNING id, created_at, last_modified
                """
                created_at = datetime.fromisoformat(entity.created_at) if entity.created_at else datetime.now()
                last_seen = datetime.fromisoformat(entity.last_seen) if entity.last_seen else datetime.now()
                next_review = datetime.fromisoformat(entity.next_review) if entity.next_review else None
                last_modified = datetime.fromisoformat(entity.last_modified) if entity.last_modified else created_at

                kp_row = await conn.fetchrow(kp_query, entity.key_point, entity.category.value, entity.subtype, entity.explanation, entity.original_phrase, entity.correction, entity.mastery_level, entity.mistake_count, entity.correct_count, created_at, last_seen, next_review, entity.custom_notes, last_modified)
                entity.id = kp_row["id"]
                entity.created_at = kp_row["created_at"].isoformat()
                entity.last_modified = kp_row["last_modified"].isoformat()

                if entity.original_error:
                    await conn.execute(
                        "INSERT INTO original_errors (knowledge_point_id, chinese_sentence, user_answer, correct_answer, timestamp) VALUES ($1, $2, $3, $4, $5)",
                        entity.id, entity.original_error.chinese_sentence, entity.original_error.user_answer, entity.original_error.correct_answer, datetime.fromisoformat(entity.original_error.timestamp)
                    )

                if entity.review_examples:
                    for example in entity.review_examples:
                        await conn.execute(
                            "INSERT INTO review_examples (knowledge_point_id, chinese_sentence, user_answer, correct_answer, is_correct, timestamp) VALUES ($1, $2, $3, $4, $5, $6)",
                            entity.id, example.chinese_sentence, example.user_answer, example.correct_answer, example.is_correct, datetime.fromisoformat(example.timestamp)
                        )

                if entity.tags:
                    for tag_name in entity.tags:
                        tag_id = await conn.fetchval("INSERT INTO tags (name) VALUES ($1) ON CONFLICT (name) DO UPDATE SET name = $1 RETURNING id", tag_name)
                        await conn.execute("INSERT INTO knowledge_point_tags (knowledge_point_id, tag_id) VALUES ($1, $2) ON CONFLICT DO NOTHING", entity.id, tag_id)

                self.logger.info(f"成功創建知識點 {entity.id}: {entity.key_point}")
                return entity
            except Exception as e:
                self._handle_database_error(e, f"create({entity.key_point})")
                raise

    async def update(self, entity: KnowledgePoint) -> KnowledgePoint:
        """
        更新一個已有的知識點。

        Args:
            entity: 包含更新後資料的 `KnowledgePoint` 物件。

        Returns:
            更新後的 `KnowledgePoint` 物件。
        """
        query = """
            UPDATE knowledge_points SET
                key_point = $2, category = $3, subtype = $4, explanation = $5, original_phrase = $6, correction = $7,
                mastery_level = $8, mistake_count = $9, correct_count = $10, last_seen = $11, next_review = $12, custom_notes = $13
            WHERE id = $1 AND is_deleted = FALSE RETURNING last_modified
        """
        async with self.connection() as conn:
            try:
                last_modified = await conn.fetchval(query, entity.id, entity.key_point, entity.category.value, entity.subtype, entity.explanation, entity.original_phrase, entity.correction, entity.mastery_level, entity.mistake_count, entity.correct_count, datetime.now(), datetime.fromisoformat(entity.next_review) if entity.next_review else None, entity.custom_notes)
                if last_modified:
                    entity.last_modified = last_modified.isoformat()
                    return entity
                raise ValueError(f"知識點 {entity.id} 不存在或已被刪除，無法更新。")
            except Exception as e:
                self._handle_database_error(e, f"update({entity.id})")
                raise

    async def delete(self, id: int, reason: str = "") -> bool:
        """
        軟刪除一個知識點（將 `is_deleted` 標記為 True）。

        Args:
            id: 要刪除的知識點 ID。
            reason: 刪除原因。

        Returns:
            如果成功刪除，返回 True。
        """
        query = "UPDATE knowledge_points SET is_deleted = TRUE, deleted_at = $2, deleted_reason = $3 WHERE id = $1 AND is_deleted = FALSE RETURNING id"
        async with self.connection() as conn:
            try:
                result = await conn.fetchval(query, id, datetime.now(), reason)
                if result:
                    self.logger.info(f"成功軟刪除知識點 {id}，原因: {reason}")
                    return True
                return False
            except Exception as e:
                self._handle_database_error(e, f"delete({id})")
                raise

    async def restore(self, id: int) -> bool:
        """
        恢復一個被軟刪除的知識點。

        Args:
            id: 要恢復的知識點 ID。

        Returns:
            如果成功恢復，返回 True。
        """
        query = "UPDATE knowledge_points SET is_deleted = FALSE, deleted_at = NULL, deleted_reason = '' WHERE id = $1 AND is_deleted = TRUE RETURNING id"
        async with self.connection() as conn:
            try:
                result = await conn.fetchval(query, id)
                if result:
                    self.logger.info(f"成功恢復知識點 {id}")
                    return True
                self.logger.warning(f"知識點 {id} 不存在或未被刪除，無法恢復。")
                return False
            except Exception as e:
                self._handle_database_error(e, f"restore({id})")
                raise

    async def find_due_for_review(self, limit: int = 20) -> list[KnowledgePoint]:
        """
        查詢到期需要複習的知識點。

        查詢條件：
        - `next_review` 時間已到或已過。
        - 未被刪除。
        - 掌握度低於 0.9。
        - 只包含 `isolated` 和 `enhancement` 類別。

        Args:
            limit: 返回的最大數量。

        Returns:
            需要複習的知識點列表，按複習時間和掌握度排序。
        """
        query = """
            SELECT * FROM knowledge_points
            WHERE next_review <= $1 AND is_deleted = FALSE AND mastery_level < 0.9 AND category IN ('isolated', 'enhancement')
            ORDER BY next_review ASC, mastery_level ASC LIMIT $2
        """
        async with self.connection() as conn:
            try:
                rows = await conn.fetch(query, datetime.now(), limit)
                return [self._row_to_knowledge_point(row) for row in rows]
            except Exception as e:
                self._handle_database_error(e, f"find_due_for_review({limit})")
                raise

    async def find_by_category(self, category: str, subtype: Optional[str] = None) -> list[KnowledgePoint]:
        """
        根據類別和子類別查詢知識點。

        Args:
            category: 錯誤類別。
            subtype: 子類別（可選）。

        Returns:
            符合條件的知識點列表。
        """
        params = [category]
        if subtype:
            query = "SELECT * FROM knowledge_points WHERE category = $1 AND subtype = $2 AND is_deleted = FALSE ORDER BY created_at DESC"
            params.append(subtype)
        else:
            query = "SELECT * FROM knowledge_points WHERE category = $1 AND is_deleted = FALSE ORDER BY created_at DESC"

        async with self.connection() as conn:
            try:
                rows = await conn.fetch(query, *params)
                return [self._row_to_knowledge_point(row) for row in rows]
            except Exception as e:
                self._handle_database_error(e, f"find_by_category({category}, {subtype})")
                raise

    async def search(self, keyword: str, limit: int = 50) -> list[KnowledgePoint]:
        """
        對知識點進行全文搜索。

        搜索範圍包括 `key_point`, `explanation`, `original_phrase`, `correction`。

        Args:
            keyword: 搜索關鍵字。
            limit: 返回的最大數量。

        Returns:
            匹配的知識點列表，按相關性排序。
        """
        query = """
            SELECT * FROM knowledge_points
            WHERE (key_point ILIKE $1 OR explanation ILIKE $1 OR original_phrase ILIKE $1 OR correction ILIKE $1) AND is_deleted = FALSE
            ORDER BY CASE WHEN key_point ILIKE $1 THEN 1 WHEN original_phrase ILIKE $1 THEN 2 WHEN correction ILIKE $1 THEN 3 ELSE 4 END, created_at DESC
            LIMIT $2
        """
        pattern = f"%{keyword}%"
        async with self.connection() as conn:
            try:
                rows = await conn.fetch(query, pattern, limit)
                return [self._row_to_knowledge_point(row) for row in rows]
            except Exception as e:
                self._handle_database_error(e, f"search({keyword})")
                raise

    async def add_review_example(self, knowledge_point_id: int, example: ReviewExample) -> bool:
        """
        為指定的知識點添加一個複習例句。

        Args:
            knowledge_point_id: 知識點的 ID。
            example: `ReviewExample` 物件。

        Returns:
            如果成功添加，返回 True。
        """
        query = "INSERT INTO review_examples (knowledge_point_id, chinese_sentence, user_answer, correct_answer, is_correct, timestamp) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id"
        async with self.connection() as conn:
            try:
                result = await conn.fetchval(query, knowledge_point_id, example.chinese_sentence, example.user_answer, example.correct_answer, example.is_correct, datetime.fromisoformat(example.timestamp))
                return bool(result)
            except Exception as e:
                self._handle_database_error(e, f"add_review_example({knowledge_point_id})")
                raise

    async def get_statistics(self) -> dict[str, Any]:
        """
        獲取全系統的統計資料。

        此方法執行多個匯總查詢來計算知識點和練習記錄的統計數據。

        Returns:
            一個包含多項統計指標的字典，欄位名已對應前端期望。
        """
        knowledge_query = """
            SELECT
                COUNT(*) FILTER (WHERE is_deleted = FALSE) as knowledge_points,
                COUNT(*) FILTER (WHERE mastery_level >= 0.8 AND is_deleted = FALSE) as mastered,
                COUNT(*) FILTER (WHERE mastery_level < 0.3 AND is_deleted = FALSE) as struggling,
                COUNT(*) FILTER (WHERE next_review <= NOW() AND is_deleted = FALSE) as due_reviews,
                CAST(AVG(mastery_level) FILTER (WHERE is_deleted = FALSE) AS FLOAT) as avg_mastery,
                COUNT(DISTINCT category) FILTER (WHERE is_deleted = FALSE) as categories_count
            FROM knowledge_points
        """
        practice_query = "SELECT COUNT(*) as total_practices, COUNT(*) FILTER (WHERE is_correct = TRUE) as correct_count FROM review_examples"

        async with self.connection() as conn:
            try:
                knowledge_row = await conn.fetchrow(knowledge_query)
                knowledge_stats = dict(knowledge_row) if knowledge_row else {}

                try:
                    practice_row = await conn.fetchrow(practice_query)
                    practice_stats = dict(practice_row) if practice_row else {"total_practices": 0, "correct_count": 0}
                except asyncpg.UndefinedTableError:
                    self.logger.warning("'review_examples' 表不存在，練習統計將為 0。")
                    practice_stats = {"total_practices": 0, "correct_count": 0}

                stats = {
                    "knowledge_points": knowledge_stats.get("knowledge_points", 0),
                    "total_practices": practice_stats.get("total_practices", 0),
                    "correct_count": practice_stats.get("correct_count", 0),
                    "due_reviews": knowledge_stats.get("due_reviews", 0),
                    "mastered": knowledge_stats.get("mastered", 0),
                    "struggling": knowledge_stats.get("struggling", 0),
                    "avg_mastery": round(knowledge_stats.get("avg_mastery") or 0.0, 2),
                    "categories_count": knowledge_stats.get("categories_count", 0),
                }
                return stats
            except Exception as e:
                self._handle_database_error(e, "get_statistics")
                raise
