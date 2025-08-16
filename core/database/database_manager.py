"""
純資料庫知識點管理器 - TASK-30D
替代原有的 DatabaseAdapter，移除所有 JSON 降級邏輯
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

from core.cache_manager import UnifiedCacheManager
from core.database.connection import get_database_connection
from core.database.exceptions import DatabaseError
from core.database.repositories.knowledge_repository import KnowledgePointRepository
from core.error_handler import ErrorHandler
from core.error_types import ErrorCategory
from core.log_config import get_module_logger
from core.models import KnowledgePoint, OriginalError, ReviewExample


class DatabaseKnowledgeManager:
    """純資料庫版本的知識點管理器

    移除所有 JSON 降級邏輯，完全依賴資料庫
    這是 TASK-30D 的核心實現
    """

    def __init__(self):
        """初始化純資料庫管理器"""
        self.logger = get_module_logger(__name__)
        self._error_handler = ErrorHandler(mode="database")
        self._cache_manager = UnifiedCacheManager(default_ttl=300)

        # 資料庫連線
        self._db_connection = get_database_connection()
        self._repository: Optional[KnowledgePointRepository] = None
        self._initialized = False
        self._init_lock = asyncio.Lock()

        self.logger.info("初始化純資料庫知識管理器")

    async def _ensure_initialized(self):
        """確保資料庫連線已初始化"""
        if not self._initialized:
            async with self._init_lock:
                if not self._initialized:
                    try:
                        pool = await self._db_connection.connect()
                        if not pool:
                            raise DatabaseError("無法建立資料庫連線")

                        self._repository = KnowledgePointRepository(pool)
                        self._initialized = True
                        self.logger.info("資料庫連線初始化成功")
                    except Exception as e:
                        self.logger.error(f"資料庫初始化失敗: {e}")
                        raise DatabaseError(f"資料庫初始化失敗: {e}")

    @asynccontextmanager
    async def _db_operation(self, operation_name: str):
        """資料庫操作上下文管理器"""
        await self._ensure_initialized()
        try:
            yield self._repository
        except Exception as e:
            self.logger.error(f"{operation_name} 失敗: {e}")
            raise DatabaseError(f"{operation_name} 失敗: {e}")

    # ========== 核心 CRUD 操作 ==========

    async def add_knowledge_point(
        self,
        error_info: dict,
        analysis: dict,
        chinese_sentence: str,
        user_answer: str,
        correct_answer: str,
    ) -> Optional[KnowledgePoint]:
        """添加新知識點"""
        cache_key = f"add_{error_info.get('error_pattern', '')}_{chinese_sentence}"

        async def _add():
            async with self._db_operation("添加知識點") as repo:
                # 創建知識點物件
                original_error = OriginalError(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    timestamp=datetime.now().isoformat(),
                )

                knowledge_point = KnowledgePoint(
                    id=0,  # 將由資料庫分配
                    key_point=error_info.get("error_pattern", ""),
                    category=ErrorCategory.from_string(error_info.get("category", "other")),
                    subtype=error_info.get("subtype", ""),
                    explanation=analysis.get("explanation", ""),
                    original_phrase=error_info.get("error_phrase", ""),
                    correction=error_info.get("correction", ""),
                    original_error=original_error,
                    review_examples=[],
                    mastery_level=0.0,
                    mistake_count=1,
                    correct_count=0,
                    created_at=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    next_review="",
                )

                # 計算下次複習時間
                knowledge_point.next_review = knowledge_point._calculate_next_review()

                # 儲存到資料庫
                result = await repo.create(knowledge_point)

                if result:
                    # 清除相關快取
                    self._cache_manager.invalidate("all_points_False")  # 清除主頁面緩存
                    self._cache_manager.invalidate("all_points_True")   # 清除回收站緩存
                    self._cache_manager.invalidate("statistics")  # 清除統計緩存

                return result

        return await self._cache_manager.get_or_compute_async(
            cache_key, _add, ttl=60
        )

    async def get_knowledge_point(self, point_id: int) -> Optional[KnowledgePoint]:
        """獲取知識點"""
        cache_key = f"point_{point_id}"

        async def _get():
            async with self._db_operation("獲取知識點") as repo:
                return await repo.find_by_id(point_id)

        return await self._cache_manager.get_or_compute_async(
            cache_key, _get, ttl=300
        )

    async def get_all_knowledge_points(self, include_deleted: bool = False) -> list[KnowledgePoint]:
        """獲取所有知識點"""
        cache_key = f"all_points_{include_deleted}"

        async def _get_all():
            async with self._db_operation("獲取所有知識點") as repo:
                if include_deleted:
                    # 明確指示要包含已刪除記錄
                    filters = {"include_deleted": True}
                else:
                    # 只查詢未刪除記錄
                    filters = {"is_deleted": False}
                return await repo.find_all(**filters)

        return await self._cache_manager.get_or_compute_async(
            cache_key, _get_all, ttl=60
        )

    async def update_knowledge_point(self, point: KnowledgePoint) -> bool:
        """更新知識點"""
        try:
            async with self._db_operation("更新知識點") as repo:
                await repo.update(point)

                # 清除相關快取
                self._cache_manager.invalidate(f"point_{point.id}")  # 清除單個知識點緩存
                self._cache_manager.invalidate("all_points_False")  # 清除主頁面緩存
                self._cache_manager.invalidate("all_points_True")   # 清除回收站緩存
                self._cache_manager.invalidate("statistics")  # 清除統計緩存

                return True
        except Exception as e:
            self.logger.error(f"更新知識點失敗: {e}")
            return False

    async def delete_knowledge_point(self, point_id: int, reason: str = "") -> bool:
        """軟刪除知識點"""
        try:
            async with self._db_operation("刪除知識點") as repo:
                result = await repo.delete(point_id, reason)

                if result:
                    # 清除相關快取
                    self._cache_manager.invalidate(f"point_{point_id}")  # 清除單個知識點緩存
                    self._cache_manager.invalidate("all_points_False")  # 清除主頁面緩存
                    self._cache_manager.invalidate("all_points_True")   # 清除回收站緩存
                    self._cache_manager.invalidate("statistics")  # 清除統計緩存

                return result
        except Exception as e:
            self.logger.error(f"刪除知識點失敗: {e}")
            return False

    async def restore_knowledge_point(self, point_id: int) -> bool:
        """恢復已刪除的知識點"""
        try:
            async with self._db_operation("恢復知識點") as repo:
                result = await repo.restore(point_id)

                if result:
                    # 清除相關快取
                    self._cache_manager.invalidate(f"point_{point_id}")  # 清除單個知識點緩存
                    self._cache_manager.invalidate("all_points_False")  # 清除主頁面緩存
                    self._cache_manager.invalidate("all_points_True")   # 清除回收站緩存
                    self._cache_manager.invalidate("statistics")  # 清除統計緩存

                return result
        except Exception as e:
            self.logger.error(f"恢復知識點失敗: {e}")
            return False

    # ========== 查詢操作 ==========

    async def search_knowledge_points(self, keyword: str, limit: int = 50) -> list[KnowledgePoint]:
        """搜尋知識點"""
        cache_key = f"search_{keyword}_{limit}"

        async def _search():
            async with self._db_operation("搜尋知識點") as repo:
                return await repo.search(keyword, limit)

        return await self._cache_manager.get_or_compute_async(
            cache_key, _search, ttl=180
        )

    async def get_review_candidates(self, limit: int = 20) -> list[KnowledgePoint]:
        """獲取待複習的知識點"""
        cache_key = f"review_candidates_{limit}"

        async def _get_candidates():
            async with self._db_operation("獲取複習候選") as repo:
                return await repo.find_due_for_review(limit)

        return await self._cache_manager.get_or_compute_async(
            cache_key, _get_candidates, ttl=120
        )

    async def get_knowledge_by_category(
        self, category: str, subtype: Optional[str] = None
    ) -> list[KnowledgePoint]:
        """根據類別獲取知識點"""
        cache_key = f"category_{category}_{subtype}"

        async def _get_by_category():
            async with self._db_operation("按類別獲取") as repo:
                return await repo.find_by_category(category, subtype)

        return await self._cache_manager.get_or_compute_async(
            cache_key, _get_by_category, ttl=300
        )

    # ========== 統計操作 ==========

    async def get_statistics(self) -> dict[str, Any]:
        """獲取統計資料"""
        cache_key = "statistics"

        async def _get_stats():
            async with self._db_operation("獲取統計") as repo:
                return await repo.get_statistics()

        return await self._cache_manager.get_or_compute_async(
            cache_key, _get_stats, ttl=60
        )

    # ========== 學習記錄操作 ==========

    async def update_mastery(self, point_id: int, is_correct: bool) -> bool:
        """更新掌握度"""
        try:
            point = await self.get_knowledge_point(point_id)
            if not point:
                return False

            # 更新掌握度
            point.update_mastery(is_correct)

            # 儲存更新
            return await self.update_knowledge_point(point)
        except Exception as e:
            self.logger.error(f"更新掌握度失敗: {e}")
            return False

    async def add_review_example(
        self,
        point_id: int,
        chinese_sentence: str,
        user_answer: str,
        correct_answer: str,
        is_correct: bool,
    ) -> bool:
        """添加複習例句"""
        try:
            async with self._db_operation("添加複習例句") as repo:
                example = ReviewExample(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    timestamp=datetime.now().isoformat(),
                    is_correct=is_correct,
                )

                result = await repo.add_review_example(point_id, example)

                # 清除相關快取
                cache_key = f"point_{point_id}"
                self._cache_manager.invalidate(cache_key)
                self._cache_manager.invalidate("all_points_False")  # 清除主頁面緩存
                self._cache_manager.invalidate("all_points_True")   # 清除回收站緩存
                self._cache_manager.invalidate("statistics")  # 清除統計緩存

                return result
        except Exception as e:
            self.logger.error(f"添加複習例句失敗: {e}")
            return False

    # ========== 編輯操作 ==========

    async def edit_knowledge_point(
        self, point_id: int, updates: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """編輯知識點"""
        try:
            point = await self.get_knowledge_point(point_id)
            if not point:
                return None

            # 執行編輯
            history = point.edit(updates)

            # 儲存更新
            if await self.update_knowledge_point(point):
                return history
            return None
        except Exception as e:
            self.logger.error(f"編輯知識點失敗: {e}")
            return None

    # ========== 同步相容方法（供舊程式碼使用）==========

    def get_active_points(self) -> list[KnowledgePoint]:
        """同步獲取活躍知識點（相容舊 API）

        ⚠️ 已廢棄：此方法使用 asyncio.new_event_loop() 會導致事件循環衝突。
        請使用異步版本 get_all_knowledge_points(include_deleted=False)。
        """
        import warnings
        warnings.warn(
            "get_active_points() 已廢棄。"
            "請使用異步方法 get_all_knowledge_points(include_deleted=False)。"
            "原因：同步方法中的 asyncio.new_event_loop() 導致事件循環衝突。",
            DeprecationWarning,
            stacklevel=2
        )

        # 嘗試在現有事件循環中執行
        try:
            loop = asyncio.get_running_loop()
            # 如果有運行中的循環，無法直接執行異步代碼
            self.logger.error("無法在異步上下文中調用同步方法 get_active_points()")
            return []
        except RuntimeError:
            # 沒有運行中的循環，創建新的（僅用於相容性，不推薦）
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(self.get_all_knowledge_points(include_deleted=False))
            except Exception as e:
                self.logger.error(f"同步獲取活躍知識點失敗: {e}")
                return []
            finally:
                loop.close()

    # ========== 資源管理 ==========

    async def close(self):
        """關閉資料庫連線"""
        if self._db_connection:
            await self._db_connection.disconnect()
            self.logger.info("資料庫連線已關閉")

    def __del__(self):
        """清理資源

        注意：__del__ 方法中處理異步清理是複雜的，
        應該依賴應用程式的正常關閉流程來調用 close()。
        """
        if hasattr(self, "_db_connection") and self._db_connection:
            # 記錄警告，提醒使用正確的清理方式
            if hasattr(self, "logger"):
                self.logger.warning(
                    "DatabaseKnowledgeManager 正在通過 __del__ 清理。"
                    "建議在應用關閉時顯式調用 await close()。"
                )

            # 嘗試安全地清理資源
            try:
                # 檢查是否有運行中的事件循環
                loop = asyncio.get_running_loop()
                # 如果有，創建清理任務
                loop.create_task(self.close())
            except RuntimeError:
                # 沒有運行中的循環，無法執行異步清理
                # 資源將在進程結束時由系統回收
                pass
            except Exception:
                # 忽略其他異常，避免在 __del__ 中拋出錯誤
                pass

    # ========== TASK-32: 每日知識點限額功能 - 資料庫版本 ==========

    async def get_user_settings(self, user_id: str = "default_user") -> dict:
        """獲取用戶設定（資料庫版本）

        Args:
            user_id: 用戶ID

        Returns:
            用戶設定字典
        """
        cache_key = f"user_settings:{user_id}"

        async def _get_settings():
            await self._ensure_initialized()

            try:
                pool = await self._db_connection.connect()
                async with pool.acquire() as conn:
                    query = """
                    SELECT daily_knowledge_limit, limit_enabled, created_at, updated_at
                    FROM user_settings WHERE user_id = $1
                    """
                    row = await conn.fetchrow(query, user_id)

                    if row:
                        return {
                            "user_id": user_id,
                            "daily_knowledge_limit": row["daily_knowledge_limit"],
                            "limit_enabled": row["limit_enabled"],
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                        }
                    else:
                        # 創建默認設定
                        default_settings = {
                            "user_id": user_id,
                            "daily_knowledge_limit": 15,
                            "limit_enabled": False,
                        }

                        insert_query = """
                        INSERT INTO user_settings (user_id, daily_knowledge_limit, limit_enabled)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (user_id) DO NOTHING
                        RETURNING created_at, updated_at
                        """
                        result = await conn.fetchrow(
                            insert_query,
                            user_id,
                            default_settings["daily_knowledge_limit"],
                            default_settings["limit_enabled"]
                        )

                        if result:
                            default_settings["created_at"] = result["created_at"].isoformat()
                            default_settings["updated_at"] = result["updated_at"].isoformat()

                        return default_settings

            except Exception as e:
                self.logger.error(f"獲取用戶設定失敗: {e}")
                # 返回默認設定
                return {
                    "user_id": user_id,
                    "daily_knowledge_limit": 15,
                    "limit_enabled": False,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

        return await self._cache_manager.get_or_compute_async(
            cache_key, _get_settings, ttl=1800  # 30分鐘緩存
        )

    async def update_user_settings(
        self,
        user_id: str = "default_user",
        daily_limit: Optional[int] = None,
        limit_enabled: Optional[bool] = None
    ) -> bool:
        """更新用戶設定（資料庫版本）

        Args:
            user_id: 用戶ID
            daily_limit: 每日限額 (1-50)
            limit_enabled: 是否啟用限額

        Returns:
            是否更新成功
        """
        try:
            await self._ensure_initialized()

            # 驗證參數
            if daily_limit is not None and not (1 <= daily_limit <= 50):
                self.logger.error(f"限額數量超出範圍: {daily_limit}")
                return False

            pool = await self._db_connection.connect()
            async with pool.acquire() as conn:
                # 使用 UPSERT 語句
                query = """
                INSERT INTO user_settings (user_id, daily_knowledge_limit, limit_enabled, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    daily_knowledge_limit = COALESCE($2, user_settings.daily_knowledge_limit),
                    limit_enabled = COALESCE($3, user_settings.limit_enabled),
                    updated_at = CURRENT_TIMESTAMP
                """
                await conn.execute(query, user_id, daily_limit, limit_enabled)

                # 清除緩存
                cache_key = f"user_settings:{user_id}"
                self._cache_manager.invalidate(cache_key)

                # 清除限額狀態緩存
                from datetime import date
                today = date.today().isoformat()
                limit_cache_key = f"limit_status:{user_id}:{today}"
                self._cache_manager.invalidate(limit_cache_key)

                self.logger.info(f"用戶設定更新成功: user_id={user_id}")
                return True

        except Exception as e:
            self.logger.error(f"更新用戶設定失敗: {e}")
            return False

    async def get_daily_stats(self, user_id: str = "default_user", target_date: Optional[str] = None) -> dict:
        """獲取每日統計數據（資料庫版本）

        Args:
            user_id: 用戶ID
            target_date: 目標日期 (YYYY-MM-DD)，默認為今天

        Returns:
            每日統計字典
        """
        if target_date is None:
            from datetime import date
            target_date = date.today().isoformat()

        # 確保 target_date 是字符串格式給 cache_key 使用
        date_str = target_date if isinstance(target_date, str) else target_date.isoformat()
        cache_key = f"daily_stats:{user_id}:{date_str}"

        # 轉換為 date 對象供資料庫使用
        if isinstance(target_date, str):
            from datetime import datetime
            target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        else:
            target_date_obj = target_date

        async def _get_stats():
            await self._ensure_initialized()

            try:
                pool = await self._db_connection.connect()
                async with pool.acquire() as conn:
                    query = """
                    SELECT date, isolated_count, enhancement_count, created_at, updated_at
                    FROM daily_knowledge_stats
                    WHERE user_id = $1 AND date = $2
                    """
                    row = await conn.fetchrow(query, user_id, target_date_obj)

                    if row:
                        return {
                            "date": row["date"].isoformat(),
                            "user_id": user_id,
                            "isolated_count": row["isolated_count"],
                            "enhancement_count": row["enhancement_count"],
                            "total_count": row["isolated_count"] + row["enhancement_count"],
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                        }
                    else:
                        # 返回空統計
                        return {
                            "date": date_str,
                            "user_id": user_id,
                            "isolated_count": 0,
                            "enhancement_count": 0,
                            "total_count": 0,
                        }

            except Exception as e:
                self.logger.error(f"獲取每日統計失敗: {e}")
                return {
                    "date": date_str,
                    "user_id": user_id,
                    "isolated_count": 0,
                    "enhancement_count": 0,
                    "total_count": 0,
                }

        return await self._cache_manager.get_or_compute_async(
            cache_key, _get_stats, ttl=300  # 5分鐘緩存
        )

    async def increment_daily_stats(
        self,
        user_id: str = "default_user",
        error_type: str = "isolated",
        target_date: Optional[str] = None
    ) -> bool:
        """增加每日統計數據（資料庫版本）

        Args:
            user_id: 用戶ID
            error_type: 錯誤類型 (isolated, enhancement)
            target_date: 目標日期 (YYYY-MM-DD)，默認為今天

        Returns:
            是否更新成功
        """
        if target_date is None:
            from datetime import date
            target_date = date.today()
        else:
            # 如果 target_date 是字符串，轉換為 date 對象
            if isinstance(target_date, str):
                from datetime import datetime
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        # 只處理限制類型
        if error_type not in {"isolated", "enhancement"}:
            return True

        try:
            await self._ensure_initialized()

            pool = await self._db_connection.connect()
            async with pool.acquire() as conn:
                # 使用 UPSERT 增加計數
                isolated_increment = 1 if error_type == "isolated" else 0
                enhancement_increment = 1 if error_type == "enhancement" else 0

                query = """
                INSERT INTO daily_knowledge_stats (date, user_id, isolated_count, enhancement_count, updated_at)
                VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
                ON CONFLICT (date, user_id) DO UPDATE SET
                    isolated_count = daily_knowledge_stats.isolated_count + $3,
                    enhancement_count = daily_knowledge_stats.enhancement_count + $4,
                    updated_at = CURRENT_TIMESTAMP
                """
                await conn.execute(
                    query,
                    target_date,
                    user_id,
                    isolated_increment,
                    enhancement_increment
                )

                # 清除相關緩存
                cache_key = f"daily_stats:{user_id}:{target_date}"
                self._cache_manager.invalidate(cache_key)

                # 清除限額狀態緩存
                limit_cache_key = f"limit_status:{user_id}:{target_date}"
                self._cache_manager.invalidate(limit_cache_key)

                self.logger.info(f"每日統計更新成功: {error_type} for {user_id} on {target_date}")
                return True

        except Exception as e:
            self.logger.error(f"更新每日統計失敗: {e}")
            return False

    async def check_daily_limit(self, user_id: str = "default_user", error_type: str = "isolated") -> dict:
        """檢查每日限額狀態（資料庫版本）

        Args:
            user_id: 用戶ID
            error_type: 錯誤類型

        Returns:
            限額狀態字典
        """
        from datetime import date
        today = date.today().isoformat()

        # 快速路徑：非限制類型直接通過
        if error_type not in {"isolated", "enhancement"}:
            return {
                "can_add": True,
                "can_add_more": True,
                "reason": "type_not_limited",
                "error_type": error_type,
                "date": today,
            }

        cache_key = f"limit_status:{user_id}:{today}"

        async def _check_limit():
            try:
                # 獲取用戶設定
                settings = await self.get_user_settings(user_id)

                # 如果未啟用限額功能
                if not settings.get("limit_enabled", False):
                    return {
                        "can_add": True,
                        "can_add_more": True,
                        "reason": "limit_disabled",
                        "limit_enabled": False,
                        "daily_limit": settings.get("daily_knowledge_limit", 15),
                        "used_count": 0,
                        "remaining": settings.get("daily_knowledge_limit", 15),
                        "date": today,
                        "status": "normal"
                    }

                # 獲取今日統計
                today_stats = await self.get_daily_stats(user_id, today)

                # 計算當前使用量
                used_count = today_stats.get("isolated_count", 0) + today_stats.get("enhancement_count", 0)
                daily_limit = settings.get("daily_knowledge_limit", 15)

                can_add = used_count < daily_limit

                return {
                    "can_add": can_add,
                    "can_add_more": can_add,
                    "reason": "within_limit" if can_add else "limit_exceeded",
                    "limit_enabled": True,
                    "daily_limit": daily_limit,
                    "used_count": used_count,
                    "remaining": max(0, daily_limit - used_count),
                    "breakdown": {
                        "isolated": today_stats.get("isolated_count", 0),
                        "enhancement": today_stats.get("enhancement_count", 0)
                    },
                    "date": today,
                    "status": "normal" if can_add else "limit_reached"
                }

            except Exception as e:
                self.logger.error(f"檢查每日限額失敗: {e}")
                return {
                    "can_add": True,
                    "can_add_more": True,
                    "reason": "error_fallback",
                    "error": str(e),
                    "date": today,
                    "status": "error"
                }

        return await self._cache_manager.get_or_compute_async(
            cache_key, _check_limit, ttl=60  # 1分鐘緩存
        )

    async def get_daily_stats_history(self, user_id: str = "default_user", days: int = 7) -> dict:
        """獲取每日統計歷史（資料庫版本）

        Args:
            user_id: 用戶ID
            days: 查詢天數

        Returns:
            統計歷史數據
        """
        cache_key = f"stats_history:{user_id}:{days}"

        async def _get_history():
            try:
                await self._ensure_initialized()

                # 獲取用戶設定
                settings = await self.get_user_settings(user_id)
                current_limit = settings.get("daily_knowledge_limit", 15)

                pool = await self._db_connection.connect()
                async with pool.acquire() as conn:
                    # 獲取最近N天的數據
                    query = f"""
                    SELECT date, isolated_count, enhancement_count, created_at, updated_at
                    FROM daily_knowledge_stats
                    WHERE user_id = $1 AND date >= CURRENT_DATE - INTERVAL '{days} days'
                    ORDER BY date DESC
                    LIMIT $2
                    """

                    rows = await conn.fetch(query, user_id, days)

                    # 填充缺失的日期
                    from datetime import date, timedelta
                    stats_list = []

                    for i in range(days):
                        target_date = date.today() - timedelta(days=i)
                        target_date_str = target_date.isoformat()

                        # 查找該日期的數據
                        row_data = None
                        for row in rows:
                            if row["date"].isoformat() == target_date_str:
                                row_data = row
                                break

                        if row_data:
                            day_stats = {
                                "date": target_date_str,
                                "user_id": user_id,
                                "isolated_count": row_data["isolated_count"],
                                "enhancement_count": row_data["enhancement_count"],
                                "total_count": row_data["isolated_count"] + row_data["enhancement_count"],
                                "limit": current_limit,
                                "created_at": row_data["created_at"].isoformat() if row_data["created_at"] else None,
                                "updated_at": row_data["updated_at"].isoformat() if row_data["updated_at"] else None,
                            }
                        else:
                            day_stats = {
                                "date": target_date_str,
                                "user_id": user_id,
                                "isolated_count": 0,
                                "enhancement_count": 0,
                                "total_count": 0,
                                "limit": current_limit,
                            }

                        stats_list.append(day_stats)

                    # 計算總結
                    total_usage = sum(s["total_count"] for s in stats_list)
                    avg_daily_usage = total_usage / days if days > 0 else 0

                    return {
                        "stats": list(reversed(stats_list)),  # 按時間正序
                        "summary": {
                            "days_queried": days,
                            "total_usage": total_usage,
                            "avg_daily_usage": round(avg_daily_usage, 1),
                            "current_limit": current_limit,
                            "limit_enabled": settings.get("limit_enabled", False)
                        }
                    }

            except Exception as e:
                self.logger.error(f"獲取統計歷史失敗: {e}")
                return {
                    "stats": [],
                    "summary": {
                        "days_queried": days,
                        "total_usage": 0,
                        "avg_daily_usage": 0.0,
                        "current_limit": 15,
                        "limit_enabled": False
                    }
                }

        return await self._cache_manager.get_or_compute_async(
            cache_key, _get_history, ttl=300  # 5分鐘緩存
        )

    async def save_knowledge_point_with_limit(
        self,
        error_info: dict,
        analysis: dict,
        chinese_sentence: str,
        user_answer: str,
        correct_answer: str,
        user_id: str = "default_user"
    ) -> dict:
        """帶限額檢查的知識點保存（事務性，資料庫版本）

        Args:
            error_info: 錯誤資訊
            analysis: 分析結果
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            correct_answer: 正確答案
            user_id: 用戶ID

        Returns:
            保存結果字典
        """
        error_type = error_info.get("subtype", "other")

        try:
            await self._ensure_initialized()
            pool = await self._db_connection.connect()

            async with pool.acquire() as conn:
                async with conn.transaction():
                    # 1. 檢查限額
                    limit_status = await self.check_daily_limit(user_id, error_type)

                    if not limit_status["can_add"]:
                        return {
                            "success": False,
                            "reason": "daily_limit_exceeded",
                            "message": f"今日知識點儲存已達上限 ({limit_status['used_count']}/{limit_status['daily_limit']})",
                            "limit_status": limit_status,
                            "suggestion": "請先完成今日的複習任務，或在設定中調整每日上限"
                        }

                    # 2. 保存知識點
                    result = await self.add_knowledge_point(
                        error_info, analysis, chinese_sentence, user_answer, correct_answer
                    )

                    if not result:
                        return {
                            "success": False,
                            "reason": "save_failed",
                            "message": "知識點保存失敗"
                        }

                    # 3. 更新統計（在同一事務中）
                    await self.increment_daily_stats(user_id, error_type)

                    # 4. 獲取更新後的限額狀態
                    updated_status = await self.check_daily_limit(user_id, error_type)

                    return {
                        "success": True,
                        "message": "知識點儲存成功",
                        "knowledge_point_id": result.id if result else None,
                        "limit_status": updated_status
                    }

        except Exception as e:
            self.logger.error(f"事務性保存知識點失敗: {e}")
            return {
                "success": False,
                "reason": "database_error",
                "message": f"保存過程中發生錯誤: {str(e)}"
            }


# 工廠函數，供外部使用
async def create_database_manager() -> DatabaseKnowledgeManager:
    """創建並初始化資料庫管理器"""
    manager = DatabaseKnowledgeManager()
    await manager._ensure_initialized()
    return manager
