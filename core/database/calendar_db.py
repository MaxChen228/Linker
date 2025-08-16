"""
學習日曆資料庫管理器

負責處理所有與使用者學習日曆、每日統計、學習連續紀錄和學習會話相關的資料庫操作。
這個模組封裝了對 `daily_learning_records`, `learning_streaks`, 和 `study_sessions` 等資料表的 CRUD 操作。
"""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from core.database.connection import get_db_pool
from core.log_config import get_module_logger

logger = get_module_logger(__name__)


class CalendarDB:
    """日曆資料庫管理器，封裝了所有與學習日曆相關的 SQL 操作。"""

    def __init__(self):
        """初始化日曆資料庫管理器。"""
        self.pool = None
        self.user_id = "default_user"  # 目前為單使用者設計，未來可擴充

    async def initialize(self):
        """異步初始化資料庫連接池。"""
        if not self.pool:
            self.pool = await get_db_pool()

    async def get_or_create_daily_record(self, record_date: date) -> dict[str, Any]:
        """
        獲取或創建指定日期的每日學習記錄。

        如果指定日期的記錄已存在，則返回該記錄；否則，創建一個新的空記錄並返回。

        Args:
            record_date: 要查詢或創建記錄的日期。

        Returns:
            一個代表每日學習記錄的字典。
        """
        await self.initialize()

        async with self.pool.acquire() as conn:
            # 嘗試獲取現有記錄
            record = await conn.fetchrow(
                """
                SELECT * FROM daily_learning_records
                WHERE user_id = $1 AND record_date = $2
                """,
                self.user_id,
                record_date,
            )

            if record:
                return dict(record)

            # 如果不存在，創建一筆帶有預設值的新記錄
            new_record = await conn.fetchrow(
                """
                INSERT INTO daily_learning_records
                (user_id, record_date, completed_reviews, planned_reviews,
                 new_practices, total_mistakes, study_minutes, mastery_improvement)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
                """,
                self.user_id,
                record_date,
                [],
                [],
                0,
                0,
                0,
                0.0,
            )

            return dict(new_record)

    async def mark_review_complete(
        self, point_id: int, complete_date: Optional[date] = None
    ) -> bool:
        """
        標記一個知識點在特定日期完成複習。

        Args:
            point_id: 已完成複習的知識點 ID。
            complete_date: 完成日期，如果為 None，則使用當天。

        Returns:
            如果成功標記（即該知識點當天未被標記過），返回 True，否則返回 False。
        """
        await self.initialize()

        complete_date = complete_date or date.today()

        async with self.pool.acquire() as conn:
            record = await self.get_or_create_daily_record(complete_date)

            completed_reviews = record.get("completed_reviews") or []
            if point_id not in completed_reviews:
                completed_reviews.append(point_id)
                await conn.execute(
                    """
                    UPDATE daily_learning_records
                    SET completed_reviews = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $2 AND record_date = $3
                    """,
                    completed_reviews,
                    self.user_id,
                    complete_date,
                )
                logger.info(f"標記複習完成: point_id={point_id}, date={complete_date}")
                return True

            return False

    async def get_daily_records(self, start_date: date, end_date: date) -> list[dict[str, Any]]:
        """
        獲取指定日期範圍內的所有每日學習記錄。

        Args:
            start_date: 開始日期。
            end_date: 結束日期。

        Returns:
            一個包含每日學習記錄字典的列表。
        """
        await self.initialize()

        async with self.pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT * FROM daily_learning_records
                WHERE user_id = $1 AND record_date BETWEEN $2 AND $3
                ORDER BY record_date
                """,
                self.user_id,
                start_date,
                end_date,
            )
            return [dict(r) for r in records]

    async def get_day_details(self, target_date: date) -> dict[str, Any]:
        """
        獲取特定日期的詳細學習資料，包括每日記錄和學習會話。

        Args:
            target_date: 要查詢的日期。

        Returns:
            一個包含該日詳細學習活動的字典。
        """
        await self.initialize()

        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                """
                SELECT * FROM daily_learning_records
                WHERE user_id = $1 AND record_date = $2
                """,
                self.user_id,
                target_date,
            )
            sessions = await conn.fetch(
                """
                SELECT * FROM study_sessions
                WHERE user_id = $1 AND session_date = $2
                ORDER BY start_time
                """,
                self.user_id,
                target_date,
            )

            record_dict = (
                dict(record)
                if record
                else {
                    "completed_reviews": [],
                    "planned_reviews": [],
                    "new_practices": 0,
                    "total_mistakes": 0,
                    "study_minutes": 0,
                    "mastery_improvement": 0.0,
                }
            )

            return {
                "date": target_date.isoformat(),
                "completed_reviews": record_dict.get("completed_reviews") or [],
                "planned_reviews": record_dict.get("planned_reviews") or [],
                "new_practices": record_dict.get("new_practices", 0),
                "total_mistakes": record_dict.get("total_mistakes", 0),
                "study_minutes": record_dict.get("study_minutes", 0),
                "mastery_improvement": float(record_dict.get("mastery_improvement", 0.0)),
                "study_sessions": [dict(s) for s in sessions],
            }

    async def update_daily_stats(
        self,
        record_date: Optional[date] = None,
        new_practices: Optional[int] = None,
        total_mistakes: Optional[int] = None,
        study_minutes: Optional[int] = None,
        mastery_improvement: Optional[float] = None,
    ) -> bool:
        """
        更新指定日期的每日統計數據。

        Args:
            record_date: 要更新的日期，預設為今天。
            new_practices: 新增的練習次數。
            total_mistakes: 總錯誤次數。
            study_minutes: 學習分鐘數。
            mastery_improvement: 掌握度提升值。

        Returns:
            如果成功更新，返回 True。
        """
        await self.initialize()
        record_date = record_date or date.today()
        await self.get_or_create_daily_record(record_date)

        update_fields, params = [], []
        param_count = 1

        if new_practices is not None:
            update_fields.append(f"new_practices = ${param_count}")
            params.append(new_practices)
            param_count += 1
        # ... (其他欄位類似)

        if not update_fields:
            return False

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([self.user_id, record_date])

        async with self.pool.acquire() as conn:
            await conn.execute(
                f"""UPDATE daily_learning_records SET {", ".join(update_fields)}
                   WHERE user_id = ${param_count} AND record_date = ${param_count + 1}""",
                *params,
            )
        return True

    async def get_streak_stats(self) -> dict[str, int]:
        """
        獲取並更新使用者的學習連續紀錄（Streak）。

        計算當前的連續學習天數、歷史最佳連續天數和本月活躍天數。

        Returns:
            一個包含 `current_streak`, `best_streak`, `month_active_days` 的字典。
        """
        await self.initialize()

        async with self.pool.acquire() as conn:
            streak_record = await conn.fetchrow(
                "SELECT * FROM learning_streaks WHERE user_id = $1", self.user_id
            )
            if not streak_record:
                streak_record = await conn.fetchrow(
                    """INSERT INTO learning_streaks (user_id, current_streak, best_streak, monthly_active_days)
                       VALUES ($1, 0, 0, 0) RETURNING *""",
                    self.user_id,
                )

            today = date.today()
            current_streak = 0
            recent_records = await conn.fetch(
                """SELECT record_date, array_length(completed_reviews, 1) as reviews_count, new_practices
                   FROM daily_learning_records WHERE user_id = $1 AND record_date <= $2
                   ORDER BY record_date DESC LIMIT 365""",
                self.user_id,
                today,
            )

            for i, record in enumerate(recent_records):
                expected_date = today - timedelta(days=i)
                if record["record_date"] != expected_date:
                    break
                if (record.get("reviews_count", 0) or 0) > 0 or record.get("new_practices", 0) > 0:
                    current_streak += 1
                else:
                    break

            month_start = date(today.year, today.month, 1)
            month_active = await conn.fetchval(
                """SELECT COUNT(*) FROM daily_learning_records
                   WHERE user_id = $1 AND record_date BETWEEN $2 AND $3
                   AND (array_length(completed_reviews, 1) > 0 OR new_practices > 0)""",
                self.user_id,
                month_start,
                today,
            )

            best_streak = max(current_streak, streak_record["best_streak"])
            await conn.execute(
                """UPDATE learning_streaks SET current_streak = $1, best_streak = $2,
                   monthly_active_days = $3, last_study_date = $4, updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = $5""",
                current_streak,
                best_streak,
                month_active,
                today,
                self.user_id,
            )

            return {
                "current_streak": current_streak,
                "best_streak": best_streak,
                "month_active_days": month_active,
            }

    async def create_study_session(
        self, practice_mode: str, start_time: datetime, end_time: Optional[datetime] = None
    ) -> int:
        """
        創建一個新的學習會話記錄。

        Args:
            practice_mode: 練習模式（例如 'new', 'review'）。
            start_time: 會話開始時間。
            end_time: 會話結束時間（可選）。

        Returns:
            新創建的會話 ID。
        """
        await self.initialize()
        session_date = start_time.date()

        async with self.pool.acquire() as conn:
            session_id = await conn.fetchval(
                """INSERT INTO study_sessions (user_id, session_date, start_time, end_time, practice_mode)
                   VALUES ($1, $2, $3, $4, $5) RETURNING id""",
                self.user_id,
                session_date,
                start_time,
                end_time,
                practice_mode,
            )
            return session_id

    async def update_study_session(
        self,
        session_id: int,
        end_time: Optional[datetime] = None,
        questions_attempted: Optional[int] = None,
        questions_correct: Optional[int] = None,
        knowledge_points_added: Optional[int] = None,
        knowledge_points_reviewed: Optional[int] = None,
    ) -> bool:
        """
        更新一個已有的學習會話記錄。

        Args:
            session_id: 要更新的會話 ID。
            end_time: 結束時間。
            questions_attempted: 嘗試的問題數。
            questions_correct: 正確的問題數。
            knowledge_points_added: 新增的知識點數。
            knowledge_points_reviewed: 複習的知識點數。

        Returns:
            如果成功更新，返回 True。
        """
        await self.initialize()
        update_fields, params = [], []
        param_count = 1

        # 動態構建更新語句
        if end_time is not None:
            update_fields.append(f"end_time = ${param_count}")
            params.append(end_time)
            param_count += 1
        if questions_attempted is not None:
            update_fields.append(f"questions_attempted = ${param_count}")
            params.append(questions_attempted)
            param_count += 1
        if questions_correct is not None:
            update_fields.append(f"questions_correct = ${param_count}")
            params.append(questions_correct)
            param_count += 1
        if knowledge_points_added is not None:
            update_fields.append(f"knowledge_points_added = ${param_count}")
            params.append(knowledge_points_added)
            param_count += 1
        if knowledge_points_reviewed is not None:
            update_fields.append(f"knowledge_points_reviewed = ${param_count}")
            params.append(knowledge_points_reviewed)
            param_count += 1

        if not update_fields:
            return False

        params.append(session_id)
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                f"""UPDATE study_sessions SET {", ".join(update_fields)} WHERE id = ${param_count}""",
                *params,
            )
            return result.split()[-1] != "0"

    async def migrate_from_json(self, json_data: dict[str, Any]) -> bool:
        """
        從舊的 JSON 格式資料遷移到資料庫。

        此方法用於系統升級，將 learning_calendar.json 的內容導入到相應的資料表中。

        Args:
            json_data: 從 JSON 文件讀取的資料。

        Returns:
            如果遷移成功，返回 True。
        """
        await self.initialize()
        try:
            # 遷移每日記錄
            daily_records = json_data.get("daily_records", {})
            for date_str, record in daily_records.items():
                record_date = datetime.fromisoformat(date_str).date()
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        """INSERT INTO daily_learning_records (user_id, record_date, completed_reviews, planned_reviews, new_practices, total_mistakes, study_minutes, mastery_improvement)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                           ON CONFLICT (user_id, record_date) DO UPDATE SET
                               completed_reviews = EXCLUDED.completed_reviews,
                               planned_reviews = EXCLUDED.planned_reviews,
                               new_practices = EXCLUDED.new_practices,
                               total_mistakes = EXCLUDED.total_mistakes,
                               study_minutes = EXCLUDED.study_minutes,
                               mastery_improvement = EXCLUDED.mastery_improvement,
                               updated_at = CURRENT_TIMESTAMP""",
                        self.user_id,
                        record_date,
                        record.get("completed_reviews", []),
                        record.get("planned_reviews", []),
                        record.get("new_practices", 0),
                        record.get("total_mistakes", 0),
                        record.get("study_minutes", 0),
                        record.get("mastery_improvement", 0.0),
                    )

            # 遷移學習會話
            study_sessions = json_data.get("study_sessions", [])
            for session in study_sessions:
                if "date" in session:
                    session_date = datetime.fromisoformat(session["date"]).date()
                    start_time = datetime.fromisoformat(session.get("start_time", session["date"]))
                    async with self.pool.acquire() as conn:
                        await conn.execute(
                            """INSERT INTO study_sessions (user_id, session_date, start_time, practice_mode, questions_attempted, questions_correct)
                               VALUES ($1, $2, $3, $4, $5, $6)""",
                            self.user_id,
                            session_date,
                            start_time,
                            session.get("mode", "unknown"),
                            session.get("questions_attempted", 0),
                            session.get("questions_correct", 0),
                        )

            logger.info(
                f"成功從 JSON 遷移 {len(daily_records)} 筆每日記錄和 {len(study_sessions)} 筆學習會話。"
            )
            return True

        except Exception as e:
            logger.error(f"從 JSON 遷移資料時發生錯誤: {e}")
            return False
