"""
知識點 Repository 實作 - 第一階段準備
提供完整的 KnowledgePoint 資料庫存取功能
"""

from datetime import datetime
from typing import Any, Optional

import asyncpg

from core.database.base import BaseRepository
from core.error_types import ErrorCategory
from core.knowledge import KnowledgePoint, OriginalError, ReviewExample


class KnowledgePointRepository(BaseRepository[KnowledgePoint]):
    """知識點資料庫操作層

    負責處理知識點相關的所有資料庫操作，包括：
    - 基本 CRUD 操作
    - 複雜查詢（如複習待辦、統計資料）
    - 關聯資料管理（原始錯誤、複習例句、標籤）
    """

    def _row_to_knowledge_point(self, row: asyncpg.Record) -> KnowledgePoint:
        """將資料庫記錄轉換為 KnowledgePoint 物件

        Args:
            row: 資料庫查詢結果記錄

        Returns:
            KnowledgePoint 物件
        """
        # 建構原始錯誤
        original_error = OriginalError(
            chinese_sentence=row.get("oe_chinese", ""),
            user_answer=row.get("oe_user_answer", ""),
            correct_answer=row.get("oe_correct_answer", ""),
            timestamp=row.get("oe_timestamp", datetime.now()).isoformat(),
        )

        # 建構複習例句列表
        review_examples = []
        if row.get("review_examples"):
            for example_data in row["review_examples"]:
                if example_data:  # 過濾掉 None
                    review_examples.append(
                        ReviewExample(
                            chinese_sentence=example_data["chinese_sentence"],
                            user_answer=example_data["user_answer"],
                            correct_answer=example_data["correct_answer"],
                            timestamp=example_data["timestamp"],
                            is_correct=example_data["is_correct"],
                        )
                    )

        # 建構知識點物件
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
            created_at=row["created_at"].isoformat() if row["created_at"] else "",
            last_seen=row["last_seen"].isoformat() if row["last_seen"] else "",
            next_review=row["next_review"].isoformat() if row["next_review"] else "",
            is_deleted=row["is_deleted"],
            deleted_at=row["deleted_at"].isoformat() if row.get("deleted_at") else "",
            deleted_reason=row.get("deleted_reason", "") or "",
            tags=row.get("tags", []) or [],
            custom_notes=row.get("custom_notes", "") or "",
            version_history=[],  # 需要時才載入
            last_modified=row["last_modified"].isoformat(),
        )

    async def find_by_id(self, id: int) -> Optional[KnowledgePoint]:
        """根據 ID 查詢知識點（包含所有關聯資料）

        Args:
            id: 知識點 ID

        Returns:
            完整的知識點物件，如果不存在則返回 None（包括已刪除的記錄）
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
            WHERE kp.id = $1 AND kp.is_deleted = FALSE
            GROUP BY kp.id, oe.chinese_sentence, oe.user_answer, oe.correct_answer, oe.timestamp
        """

        async with self.connection() as conn:
            try:
                row = await conn.fetchrow(query, id)
                if not row:
                    return None
                return self._row_to_knowledge_point(row)
            except Exception as e:
                self._handle_database_error(e, f"find_by_id({id})")
                raise

    async def find_all(self, **filters) -> list[KnowledgePoint]:
        """查詢所有知識點（支援過濾條件）

        Args:
            **filters: 過濾條件，支援的欄位包括：
                - category: 錯誤類別
                - subtype: 子類型
                - is_deleted: 是否已刪除（預設為 False）
                - mastery_level_min: 最小掌握度
                - mastery_level_max: 最大掌握度

        Returns:
            符合條件的知識點列表
        """
        # 設定預設過濾條件
        filters.setdefault("is_deleted", False)

        # 構建基礎查詢
        base_query = """
            SELECT id, key_point, category, subtype, explanation, original_phrase, correction,
                   mastery_level, mistake_count, correct_count, created_at, last_seen,
                   next_review, is_deleted, deleted_at, deleted_reason, custom_notes, last_modified
            FROM knowledge_points
        """

        # 構建 WHERE 子句
        where_clause, parameters = self._build_where_clause(filters)
        query = (
            f"{base_query} {where_clause} ORDER BY last_seen DESC"
            if where_clause
            else f"{base_query} ORDER BY last_seen DESC"
        )

        async with self.connection() as conn:
            try:
                rows = await conn.fetch(query, *parameters)
                # 簡化版本，不包含關聯資料以提升效能
                return [self._row_to_knowledge_point(row) for row in rows]
            except Exception as e:
                self._handle_database_error(e, f"find_all({filters})")
                raise

    async def create(self, entity: KnowledgePoint) -> KnowledgePoint:
        """創建新知識點（包含所有關聯資料）

        Args:
            entity: 要創建的知識點物件

        Returns:
            創建後的知識點物件（包含分配的 ID）
        """
        async with self.transaction() as conn:
            try:
                # 1. 插入主表
                kp_query = """
                    INSERT INTO knowledge_points
                    (key_point, category, subtype, explanation, original_phrase, correction,
                     mastery_level, mistake_count, correct_count, next_review, custom_notes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING id, created_at, last_seen, last_modified
                """

                kp_row = await conn.fetchrow(
                    kp_query,
                    entity.key_point,
                    entity.category.value,  # 儲存枚舉值
                    entity.subtype,
                    entity.explanation,
                    entity.original_phrase,
                    entity.correction,
                    entity.mastery_level,
                    entity.mistake_count,
                    entity.correct_count,
                    datetime.fromisoformat(entity.next_review) if entity.next_review else None,
                    entity.custom_notes,
                )

                # 更新實體的 ID 和時間戳
                entity.id = kp_row["id"]
                entity.created_at = (
                    kp_row["created_at"].isoformat() if kp_row["created_at"] else None
                )
                entity.last_seen = kp_row["last_seen"].isoformat() if kp_row["last_seen"] else None
                entity.last_modified = (
                    kp_row["last_modified"].isoformat() if kp_row["last_modified"] else None
                )

                # 2. 插入原始錯誤
                if entity.original_error:
                    oe_query = """
                        INSERT INTO original_errors
                        (
                            knowledge_point_id, chinese_sentence, user_answer,
                            correct_answer, timestamp
                        )
                        VALUES ($1, $2, $3, $4, $5)
                    """
                    await conn.execute(
                        oe_query,
                        entity.id,
                        entity.original_error.chinese_sentence,
                        entity.original_error.user_answer,
                        entity.original_error.correct_answer,
                        datetime.fromisoformat(entity.original_error.timestamp),
                    )

                # 3. 插入複習例句
                if entity.review_examples:
                    re_query = """
                        INSERT INTO review_examples
                        (
                            knowledge_point_id, chinese_sentence, user_answer,
                            correct_answer, is_correct, timestamp
                        )
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """
                    for example in entity.review_examples:
                        await conn.execute(
                            re_query,
                            entity.id,
                            example.chinese_sentence,
                            example.user_answer,
                            example.correct_answer,
                            example.is_correct,
                            datetime.fromisoformat(example.timestamp),
                        )

                # 4. 插入標籤
                if entity.tags:
                    for tag_name in entity.tags:
                        # 先確保標籤存在
                        tag_id = await conn.fetchval(
                            """
                            INSERT INTO tags (name) VALUES ($1)
                            ON CONFLICT (name) DO UPDATE SET name = $1 RETURNING id
                            """,
                            tag_name,
                        )
                        # 建立關聯
                        await conn.execute(
                            """
                            INSERT INTO knowledge_point_tags (knowledge_point_id, tag_id)
                            VALUES ($1, $2) ON CONFLICT DO NOTHING
                            """,
                            entity.id,
                            tag_id,
                        )

                self.logger.info(f"成功創建知識點 {entity.id}: {entity.key_point}")
                return entity

            except Exception as e:
                self._handle_database_error(e, f"create({entity.key_point})")
                raise

    async def update(self, entity: KnowledgePoint) -> KnowledgePoint:
        """更新知識點

        Args:
            entity: 要更新的知識點物件

        Returns:
            更新後的知識點物件
        """
        query = """
            UPDATE knowledge_points SET
                key_point = $2,
                category = $3,
                subtype = $4,
                explanation = $5,
                original_phrase = $6,
                correction = $7,
                mastery_level = $8,
                mistake_count = $9,
                correct_count = $10,
                last_seen = $11,
                next_review = $12,
                custom_notes = $13
            WHERE id = $1 AND is_deleted = FALSE
            RETURNING last_modified
        """

        async with self.connection() as conn:
            try:
                last_modified = await conn.fetchval(
                    query,
                    entity.id,
                    entity.key_point,
                    entity.category.value,
                    entity.subtype,
                    entity.explanation,
                    entity.original_phrase,
                    entity.correction,
                    entity.mastery_level,
                    entity.mistake_count,
                    entity.correct_count,
                    datetime.now(),
                    datetime.fromisoformat(entity.next_review) if entity.next_review else None,
                    entity.custom_notes,
                )

                if last_modified:
                    entity.last_modified = last_modified.isoformat()
                    self.logger.debug(f"成功更新知識點 {entity.id}")
                    return entity
                else:
                    raise ValueError(f"知識點 {entity.id} 不存在或已被刪除")

            except Exception as e:
                self._handle_database_error(e, f"update({entity.id})")
                raise

    async def delete(self, id: int, reason: str = "") -> bool:
        """軟刪除知識點

        Args:
            id: 知識點 ID
            reason: 刪除原因

        Returns:
            是否成功刪除
        """
        query = """
            UPDATE knowledge_points
            SET is_deleted = TRUE,
                deleted_at = $2,
                deleted_reason = $3
            WHERE id = $1 AND is_deleted = FALSE
            RETURNING id
        """

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

    async def find_due_for_review(self, limit: int = 20) -> list[KnowledgePoint]:
        """查詢需要複習的知識點

        Args:
            limit: 最大返回數量

        Returns:
            需要複習的知識點列表，按緊急程度排序
        """
        query = """
            SELECT id, key_point, category, subtype, explanation, original_phrase, correction,
                   mastery_level, mistake_count, correct_count, created_at, last_seen,
                   next_review, is_deleted, deleted_at, deleted_reason, custom_notes, last_modified
            FROM knowledge_points
            WHERE next_review <= $1
                AND is_deleted = FALSE
                AND mastery_level < 0.9
            ORDER BY next_review ASC, mastery_level ASC
            LIMIT $2
        """

        async with self.connection() as conn:
            try:
                rows = await conn.fetch(query, datetime.now(), limit)
                return [self._row_to_knowledge_point(row) for row in rows]
            except Exception as e:
                self._handle_database_error(e, f"find_due_for_review({limit})")
                raise

    async def find_by_category(
        self, category: str, subtype: Optional[str] = None
    ) -> list[KnowledgePoint]:
        """根據類別查詢知識點

        Args:
            category: 錯誤類別
            subtype: 子類型（可選）

        Returns:
            符合條件的知識點列表
        """
        if subtype:
            query = """
                SELECT id, key_point, category, subtype, explanation, original_phrase, correction,
                       mastery_level, mistake_count, correct_count, created_at, last_seen,
                       next_review, is_deleted, deleted_at, deleted_reason,
                       custom_notes, last_modified
                FROM knowledge_points
                WHERE category = $1 AND subtype = $2 AND is_deleted = FALSE
                ORDER BY created_at DESC
            """
            params = [category, subtype]
        else:
            query = """
                SELECT id, key_point, category, subtype, explanation, original_phrase, correction,
                       mastery_level, mistake_count, correct_count, created_at, last_seen,
                       next_review, is_deleted, deleted_at, deleted_reason,
                       custom_notes, last_modified
                FROM knowledge_points
                WHERE category = $1 AND is_deleted = FALSE
                ORDER BY created_at DESC
            """
            params = [category]

        async with self.connection() as conn:
            try:
                rows = await conn.fetch(query, *params)
                return [self._row_to_knowledge_point(row) for row in rows]
            except Exception as e:
                self._handle_database_error(e, f"find_by_category({category}, {subtype})")
                raise

    async def search(self, keyword: str, limit: int = 50) -> list[KnowledgePoint]:
        """全文搜索知識點

        Args:
            keyword: 搜索關鍵字
            limit: 最大返回數量

        Returns:
            匹配的知識點列表，按相關性排序
        """
        query = """
            SELECT id, key_point, category, subtype, explanation, original_phrase, correction,
                   mastery_level, mistake_count, correct_count, created_at, last_seen,
                   next_review, is_deleted, deleted_at, deleted_reason, custom_notes, last_modified
            FROM knowledge_points
            WHERE (
                key_point ILIKE $1
                OR explanation ILIKE $1
                OR original_phrase ILIKE $1
                OR correction ILIKE $1
            ) AND is_deleted = FALSE
            ORDER BY
                CASE
                    WHEN key_point ILIKE $1 THEN 1
                    WHEN original_phrase ILIKE $1 THEN 2
                    WHEN correction ILIKE $1 THEN 3
                    ELSE 4
                END,
                created_at DESC
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
        """為知識點添加複習例句

        Args:
            knowledge_point_id: 知識點 ID
            example: 複習例句

        Returns:
            是否成功添加
        """
        query = """
            INSERT INTO review_examples
            (
                knowledge_point_id, chinese_sentence, user_answer,
                correct_answer, is_correct, timestamp
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """

        async with self.connection() as conn:
            try:
                result = await conn.fetchval(
                    query,
                    knowledge_point_id,
                    example.chinese_sentence,
                    example.user_answer,
                    example.correct_answer,
                    example.is_correct,
                    datetime.fromisoformat(example.timestamp),
                )
                if result:
                    self.logger.debug(f"成功為知識點 {knowledge_point_id} 添加複習例句")
                    return True
                return False
            except Exception as e:
                self._handle_database_error(e, f"add_review_example({knowledge_point_id})")
                raise

    async def get_statistics(self) -> dict[str, Any]:
        """獲取知識點統計資料

        Returns:
            包含各項統計指標的字典
        """
        query = """
            SELECT
                COUNT(*) FILTER (WHERE is_deleted = FALSE) as total_active,
                COUNT(*) FILTER (WHERE mastery_level >= 0.8 AND is_deleted = FALSE) as mastered,
                COUNT(*) FILTER (WHERE mastery_level < 0.3 AND is_deleted = FALSE) as struggling,
                COUNT(*) FILTER (WHERE next_review <= NOW() AND is_deleted = FALSE) as due_review,
                AVG(mastery_level) FILTER (WHERE is_deleted = FALSE) as avg_mastery,
                COUNT(DISTINCT category) FILTER (WHERE is_deleted = FALSE) as categories_count
            FROM knowledge_points
        """

        async with self.connection() as conn:
            try:
                row = await conn.fetchrow(query)
                return dict(row) if row else {}
            except Exception as e:
                self._handle_database_error(e, "get_statistics")
                raise
