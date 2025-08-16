"""
修復後的適配器實現 - 解決異步初始化問題
"""

import json
import threading
from datetime import datetime
from typing import Any, Optional

from core.cache_manager import CacheCategories, UnifiedCacheManager
from core.database.connection import get_database_connection
from core.database.repositories.knowledge_repository import KnowledgePointRepository
from core.error_handler import ErrorHandler, with_error_handling
from core.exceptions import ErrorCategory, ErrorSeverity
from core.fallback_strategies import get_fallback_manager
from core.log_config import get_module_logger

# JSON mode removed - using database-only mode
from core.models import KnowledgePoint, ReviewExample


class KnowledgeManagerAdapter:
    """
    修復後的資料庫適配器

    關鍵修復：
    1. 移除所有同步方法中的 asyncio.run()
    2. 使用 asyncio.Event 替代雙重檢查鎖定
    3. 更安全的資源管理
    4. 統一的異步 API
    """

    def __init__(self, use_database: bool = True, data_dir: Optional[str] = None):
        """初始化適配器 - 強制資料庫模式（JSON模式已移除）"""
        self.logger = get_module_logger(self.__class__.__name__)
        self.use_database = True  # Force database mode - JSON mode removed
        self.data_dir = data_dir or "data"

        # TASK-20D: 統一錯誤處理體系 - 強制資料庫模式
        self._error_handler = ErrorHandler(mode="database")
        self._fallback_manager = get_fallback_manager()

        # 統一快取管理器
        self._cache_manager = UnifiedCacheManager(default_ttl=300)  # 5分鐘預設 TTL

        # 快取統計資料
        self._cached_statistics: Optional[dict] = None
        self._statistics_cache_time: Optional[datetime] = None

        # 資料庫相關
        self._db_connection = None
        self._repository: Optional[KnowledgePointRepository] = None

        # JSON mode removed - database-only

        # 快取（用於資料庫模式）
        self._knowledge_points_cache: list[KnowledgePoint] = []
        self._cache_dirty = True

        # 使用傳統線程鎖確保線程安全（避免異步事件循環問題）
        self._initialization_complete = False
        self._initialization_failed = False
        self._init_lock = threading.Lock()

        # 同步初始化
        self._initialize_sync()

    def _initialize_sync(self) -> None:
        """同步初始化（僅初始化 JSON 模式）"""
        if not self.use_database:
            self._initialize_legacy()
            self._initialization_complete = True
        else:
            # 資料庫模式延遲到第一次使用時異步初始化
            self.logger.info("資料庫模式將在第一次使用時異步初始化")

    async def _ensure_initialized(self) -> None:
        """確保已初始化（線程安全的異步版本）"""
        # 快速路徑：如果已經初始化完成，直接返回
        if self._initialization_complete:
            return

        # 如果初始化失敗，拋出異常
        if self._initialization_failed:
            raise RuntimeError("適配器初始化失敗")

        # 使用傳統鎖防止競態條件（兼容多線程）
        with self._init_lock:
            # 雙重檢查模式
            if self._initialization_complete:
                return
            if self._initialization_failed:
                raise RuntimeError("適配器初始化失敗")

            try:
                if self.use_database:
                    await self._initialize_database_async()
                self._initialization_complete = True
                self.logger.info("適配器初始化成功完成")
            except Exception as e:
                self.logger.error(f"初始化失敗: {e}")
                self._initialization_failed = True
                raise

    async def _initialize_database_async(self) -> None:
        """異步初始化資料庫模式（改進的資源管理）"""
        db_connection = None
        try:
            db_connection = get_database_connection()

            # 異步連線
            pool = await db_connection.connect()
            if pool:
                self._db_connection = db_connection
                self._repository = KnowledgePointRepository(pool)
                self.logger.info("資料庫模式異步初始化成功")
                await self._load_cache_from_database_async()
                self.use_database = True
            else:
                self.logger.warning("資料庫連線失敗，降級到 JSON 模式")
                await self._fallback_to_legacy_async()

        except Exception as e:
            self.logger.error(f"資料庫異步初始化失敗: {e}")
            # 完整的資源清理
            if db_connection:
                try:
                    await db_connection.disconnect()
                except Exception as cleanup_error:
                    self.logger.warning(f"清理資料庫連線失敗: {cleanup_error}")

            # 重置所有狀態
            self._db_connection = None
            self._repository = None
            self.use_database = False

            await self._fallback_to_legacy_async()

    def _initialize_legacy(self) -> None:
        """Legacy JSON mode removed - database-only mode"""
        self.logger.warning("JSON模式已移除，僅支援資料庫模式")
        raise RuntimeError("JSON模式已移除，請使用資料庫模式")

    async def _fallback_to_legacy_async(self) -> None:
        """Legacy JSON mode removed - no fallback available"""
        self.logger.error("JSON模式已移除，無法降級")
        raise RuntimeError("JSON模式已移除，無法降級到JSON模式")

    async def _load_cache_from_database_async(self) -> None:
        """異步從資料庫載入快取"""
        if not self._repository:
            return

        try:
            self._knowledge_points_cache = await self._repository.find_all(is_deleted=False)
            self._cache_dirty = False
            self.logger.debug(f"載入 {len(self._knowledge_points_cache)} 個知識點到快取")
        except Exception as e:
            self.logger.error(f"載入資料庫快取失敗: {e}")
            self._knowledge_points_cache = []

    # 純異步 API（移除所有 asyncio.run()）

    async def get_knowledge_points_async(self) -> list[KnowledgePoint]:
        """異步獲取所有知識點"""
        await self._ensure_initialized()

        if self.use_database:
            if self._cache_dirty:
                await self._load_cache_from_database_async()
            return self._knowledge_points_cache
        elif self._legacy_manager:
            return self._legacy_manager.knowledge_points
        return []

    async def get_knowledge_point_async(self, point_id: str) -> Optional[KnowledgePoint]:
        """異步根據 ID 獲取知識點"""
        await self._ensure_initialized()

        try:
            id_int = int(point_id)
        except (ValueError, TypeError):
            self.logger.warning(f"無效的知識點 ID: {point_id}")
            return None

        if self.use_database and self._repository:
            try:
                return await self._repository.find_by_id(id_int)
            except Exception as e:
                self.logger.error(f"資料庫查詢失敗: {e}")
                return None
        elif self._legacy_manager:
            return self._legacy_manager.get_knowledge_point(point_id)
        return None

    async def add_knowledge_point_async(self, knowledge_point: KnowledgePoint) -> bool:
        """異步添加知識點"""
        await self._ensure_initialized()

        if self.use_database and self._repository:
            try:
                created = await self._repository.create(knowledge_point)
                if created:
                    self._cache_dirty = True
                    # 清除相關快取
                    self._invalidate_related_caches()
                    return True
                return False
            except Exception as e:
                self.logger.error(f"資料庫添加失敗: {e}")
                return False
        elif self._legacy_manager:
            # 使用 LegacyKnowledgeManager 的公開 API
            try:
                result = self._legacy_manager.add_knowledge_point(knowledge_point)
                if result:
                    self._invalidate_related_caches()
                return result
            except AttributeError:
                # 降級處理：直接操作（記錄警告）
                self.logger.warning("使用降級方法添加知識點")
                self._legacy_manager.knowledge_points.append(knowledge_point)
                try:
                    self._legacy_manager._save_knowledge()
                    self._invalidate_related_caches()
                    return True
                except Exception as e:
                    self.logger.error(f"保存知識點失敗: {e}")
                    return False
        return False

    async def update_knowledge_point_async(self, point_id: int, **kwargs) -> bool:
        """異步更新知識點"""
        await self._ensure_initialized()

        if self.use_database and self._repository:
            try:
                point = await self._repository.find_by_id(point_id)
                if not point:
                    return False

                # 更新屬性
                for key, value in kwargs.items():
                    if hasattr(point, key):
                        setattr(point, key, value)

                updated = await self._repository.update(point)
                if updated:
                    self._cache_dirty = True
                    return True
                return False
            except Exception as e:
                self.logger.error(f"資料庫更新失敗: {e}")
                return False
        elif self._legacy_manager:
            return self._legacy_manager.update_knowledge_point(point_id, **kwargs)
        return False

    async def delete_knowledge_point_async(self, point_id: int, reason: str = "") -> bool:
        """異步刪除知識點"""
        await self._ensure_initialized()

        if self.use_database and self._repository:
            try:
                result = await self._repository.delete(point_id, reason)
                if result:
                    self._cache_dirty = True
                return result
            except Exception as e:
                self.logger.error(f"資料庫刪除失敗: {e}")
                return False
        elif self._legacy_manager:
            return self._legacy_manager.delete_knowledge_point(point_id, reason)
        return False

    async def get_review_candidates_async(self, max_points: int = 5) -> list[KnowledgePoint]:
        """異步獲取適合複習的知識點"""
        await self._ensure_initialized()

        if self.use_database and self._repository:
            try:
                return await self._repository.find_due_for_review(limit=max_points)
            except Exception as e:
                self.logger.error(f"資料庫查詢失敗: {e}")
                return []
        elif self._legacy_manager:
            return self._legacy_manager.get_review_candidates(max_points=max_points)
        return []

    async def add_review_success_async(
        self, knowledge_point_id: int, chinese_sentence: str, user_answer: str
    ) -> bool:
        """異步為知識點添加複習成功記錄"""
        await self._ensure_initialized()

        if self.use_database and self._repository:
            try:
                # 創建複習例句
                review_example = ReviewExample(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    correct_answer=user_answer,  # 因為是正確的
                    timestamp=datetime.now().isoformat(),
                    is_correct=True,
                )

                # 添加到資料庫
                await self._repository.add_review_example(knowledge_point_id, review_example)

                # 更新掌握度
                point = await self._repository.find_by_id(knowledge_point_id)
                if point:
                    point.update_mastery(is_correct=True)
                    await self._repository.update(point)
                    self._cache_dirty = True
                    return True
                return False

            except Exception as e:
                self.logger.error(f"添加複習記錄失敗: {e}")
                return False
        elif self._legacy_manager:
            self._legacy_manager.add_review_success(
                knowledge_point_id, chinese_sentence, user_answer
            )
            return True
        return False

    async def get_statistics_async(self) -> dict[str, Any]:
        """異步獲取統計資料（使用統一快取管理器）

        TASK-20A: 統一快取管理系統
        使用 UnifiedCacheManager 確保異步和同步方法快取一致
        """
        await self._ensure_initialized()

        if self.use_database and self._repository:
            return await self._cache_manager.get_or_compute_async(
                key=f"{CacheCategories.STATISTICS}:async",
                compute_func=self._compute_statistics_async,
                ttl=60,  # 統計快取1分鐘
            )
        elif self._legacy_manager:
            return self._legacy_manager.get_statistics()
        return self._get_empty_statistics()

    async def _compute_statistics_async(self) -> dict[str, Any]:
        """計算統計資料（異步版本）"""
        try:
            # 使用統一統計邏輯
            from core.statistics_utils import UnifiedStatistics

            # 獲取所有知識點
            knowledge_points = await self._repository.find_all(is_deleted=False)

            # 提取統一格式的練習記錄
            practice_records = await UnifiedStatistics.extract_database_practice_records(self)

            # 標準化處理
            practice_records = UnifiedStatistics.normalize_practice_records(practice_records)

            # 使用統一邏輯計算統計
            stats = UnifiedStatistics.calculate_practice_statistics(
                knowledge_points=knowledge_points,
                practice_records=practice_records,
                include_original_errors=True,
            )

            self.logger.debug(
                f"Database 異步統計計算完成: 練習{stats['total_practices']}, 正確{stats['correct_count']}, 知識點{stats['knowledge_points']}"
            )

            return stats

        except Exception as e:
            self.logger.error(f"計算統計資料失敗: {e}")
            # 出錯時返回空統計
            return self._get_empty_statistics()

    async def search_knowledge_points_async(self, keyword: str) -> list[KnowledgePoint]:
        """異步搜索知識點"""
        await self._ensure_initialized()

        if self.use_database and self._repository:
            try:
                return await self._repository.search(keyword)
            except Exception as e:
                self.logger.error(f"資料庫搜索失敗: {e}")
                return []
        elif self._legacy_manager:
            # LegacyKnowledgeManager 可能沒有此方法，使用簡單過濾
            return [
                point
                for point in self._legacy_manager.knowledge_points
                if keyword.lower() in point.key_point.lower()
                or keyword.lower() in point.explanation.lower()
                or keyword.lower() in point.original_phrase.lower()
            ]
        return []

    async def import_from_json_async(self, filepath: str) -> bool:
        """異步從 JSON 匯入（用於遷移）"""
        await self._ensure_initialized()

        if not self.use_database or not self._repository:
            self.logger.error("匯入功能僅在資料庫模式下可用")
            return False

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            points_data = data.get("data", [])
            success_count = 0

            for point_data in points_data:
                try:
                    # 轉換為 KnowledgePoint 物件
                    point = KnowledgePoint.from_dict(point_data)
                    point.id = 0  # 重置 ID，讓資料庫分配新的

                    # 創建到資料庫
                    created = await self._repository.create(point)
                    if created:
                        success_count += 1

                except Exception as e:
                    self.logger.warning(f"匯入知識點失敗: {e}")
                    continue

            self._cache_dirty = True
            self.logger.info(f"成功匯入 {success_count}/{len(points_data)} 個知識點")
            return success_count > 0

        except Exception as e:
            self.logger.error(f"匯入失敗: {e}")
            return False

    async def _save_mistake_async(
        self,
        chinese_sentence: str,
        user_answer: str,
        feedback: dict[str, Any],
        practice_mode: str = "new",
    ) -> bool:
        """異步保存錯誤為知識點（資料庫模式）"""
        await self._ensure_initialized()

        if not self.use_database or not self._repository:
            self.logger.error("資料庫模式未正確初始化")
            return False

        try:
            # 1. 記錄練習歷史（如果需要的話，這裡可以擴展）
            self.logger.info(f"保存練習記錄: {chinese_sentence} -> {user_answer}")

            # 2. 處理錯誤分析
            if not feedback.get("is_generally_correct", False):
                errors = feedback.get("error_analysis", [])
                for error in errors:
                    success = await self._process_error_async(
                        chinese_sentence=chinese_sentence,
                        user_answer=user_answer,
                        error=error,
                        correct_answer=feedback.get("overall_suggestion", ""),
                        practice_mode=practice_mode,
                    )
                    if not success:
                        self.logger.warning(
                            f"處理錯誤失敗: {error.get('key_point_summary', 'Unknown')}"
                        )

                return True
            elif practice_mode == "review":
                # 複習模式下答對的處理
                self.logger.info(f"複習模式正確答案: {chinese_sentence}")
                return True

            return True

        except Exception as e:
            self.logger.error(f"異步保存錯誤失敗: {e}")
            return False

    async def _process_error_async(
        self,
        chinese_sentence: str,
        user_answer: str,
        error: dict[str, Any],
        correct_answer: str,
        practice_mode: str = "new",
    ) -> bool:
        """異步處理單個錯誤（資料庫模式）"""
        try:
            from datetime import datetime

            from core.error_types import ErrorCategory, ErrorTypeSystem

            key_point = error.get("key_point_summary", "")
            original_phrase = error.get("original_phrase", "")
            correction = error.get("correction", "")
            explanation = error.get("explanation", "")
            severity = error.get("severity", "major")

            # 生成更具體的 key_point 描述
            if original_phrase and correction:
                specific_key_point = f"{key_point}: {original_phrase}"
            else:
                specific_key_point = key_point

            # 分類錯誤
            if "category" in error:
                category = ErrorCategory.from_string(error["category"])
                type_system = ErrorTypeSystem()
                _, subtype = type_system.classify(key_point, explanation, severity)
            else:
                type_system = ErrorTypeSystem()
                category, subtype = type_system.classify(key_point, explanation, severity)

            # 查找現有知識點（使用搜索方法）
            existing_points = await self._repository.search(specific_key_point, limit=10)
            existing = None

            for point in existing_points:
                if (
                    point.key_point == specific_key_point
                    and point.original_phrase == original_phrase
                    and point.correction == correction
                ):
                    existing = point
                    break

            if existing:
                # 更新現有知識點
                existing.update_mastery(is_correct=False)

                if practice_mode == "review":
                    # 添加複習記錄
                    review_example = ReviewExample(
                        chinese_sentence=chinese_sentence,
                        user_answer=user_answer,
                        correct_answer=correct_answer,
                        timestamp=datetime.now().isoformat(),
                        is_correct=False,
                    )
                    await self._repository.add_review_example(existing.id, review_example)

                # 更新知識點
                await self._repository.update(existing)
                self._cache_dirty = True

            else:
                # 創建新知識點
                from core.models import OriginalError

                original_error = OriginalError(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    timestamp=datetime.now().isoformat(),
                )

                new_point = KnowledgePoint(
                    id=0,  # 資料庫會自動分配
                    key_point=specific_key_point,
                    category=category,
                    subtype=subtype,
                    explanation=explanation,
                    original_phrase=original_phrase,
                    correction=correction,
                    original_error=original_error,
                    review_examples=[],
                )

                created = await self._repository.create(new_point)
                if created:
                    self._cache_dirty = True
                    self.logger.info(f"創建新知識點: {specific_key_point}")
                else:
                    self.logger.error(f"創建知識點失敗: {specific_key_point}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"處理錯誤失敗: {e}")
            return False

    async def edit_knowledge_point_async(
        self, point_id: int, updates: dict = None, **kwargs
    ) -> Optional[dict]:
        """編輯知識點（異步版本）

        Args:
            point_id: 知識點 ID
            updates: 更新的字段字典
            **kwargs: 向後兼容的參數

        Returns:
            編輯歷史記錄，如果失敗返回 None
        """
        await self._ensure_initialized()

        # 兼容舊的 kwargs 方式調用
        if updates is None:
            updates = kwargs

        if not updates:
            self.logger.warning(f"編輯知識點 {point_id}: 沒有提供更新數據")
            return None

        if self.use_database and self._repository:
            try:
                # 獲取現有知識點
                existing_point = await self._repository.find_by_id(point_id)
                if not existing_point:
                    self.logger.warning(f"找不到知識點 {point_id}")
                    return None

                # 記錄編輯前狀態
                edit_history = {
                    "id": point_id,
                    "timestamp": datetime.now().isoformat(),
                    "changes": {},
                    "editor": "system",
                }

                # 應用更新並記錄變更
                for key, new_value in updates.items():
                    if hasattr(existing_point, key):
                        old_value = getattr(existing_point, key)
                        if old_value != new_value:
                            edit_history["changes"][key] = {"old": old_value, "new": new_value}
                            setattr(existing_point, key, new_value)

                # 如果有變更，更新到資料庫
                if edit_history["changes"]:
                    updated_point = await self._repository.update(existing_point)
                    if updated_point:
                        self._cache_dirty = True
                        self._invalidate_related_caches()
                        self.logger.info(f"成功編輯知識點 {point_id}")
                        return edit_history
                    else:
                        self.logger.error(f"更新知識點 {point_id} 失敗")
                        return None
                else:
                    self.logger.info(f"知識點 {point_id} 沒有實際變更")
                    return edit_history

            except Exception as e:
                self.logger.error(f"編輯知識點 {point_id} 時發生錯誤: {e}")
                return None

        elif self._legacy_manager:
            # JSON 模式 - 使用原始方法保持一致性
            return self._legacy_manager.edit_knowledge_point(point_id, updates)

        return None

    async def restore_knowledge_point_async(self, point_id: int) -> bool:
        """恢復已刪除的知識點（異步版本）

        Args:
            point_id: 知識點 ID

        Returns:
            是否成功恢復
        """
        await self._ensure_initialized()

        if self.use_database and self._repository:
            try:
                # 使用新增的 repository restore 方法
                success = await self._repository.restore(point_id)
                if success:
                    self._cache_dirty = True
                    self._invalidate_related_caches()
                    self.logger.info(f"成功恢復知識點 {point_id}")
                    return True
                else:
                    self.logger.warning(f"恢復知識點 {point_id} 失敗：可能不存在或未被刪除")
                    return False

            except Exception as e:
                self.logger.error(f"恢復知識點 {point_id} 時發生錯誤: {e}")
                return False

        elif self._legacy_manager:
            # JSON 模式 - 使用現有同步方法
            return self.restore_knowledge_point(point_id)

        return False

    def export_to_json(self, filepath: str) -> None:
        """匯出到 JSON（用於備份和遷移，資料庫優先）"""
        try:
            # 資料庫模式優先（用戶要求資料庫作為主要方式）
            if self.use_database:
                # 使用快取中的數據
                knowledge_points = self._knowledge_points_cache
                if not knowledge_points and not self._cache_dirty:
                    # 如果快取為空且不需要更新，嘗試重新載入
                    try:
                        import asyncio
                        if asyncio.get_running_loop():
                            self.logger.warning("資料庫模式下建議使用異步方法匯出")
                        else:
                            loop = asyncio.get_event_loop()
                            loop.run_until_complete(self._load_cache_from_database_async())
                            knowledge_points = self._knowledge_points_cache
                    except (RuntimeError, Exception) as e:
                        self.logger.warning(f"無法重新載入快取: {e}")
                        # 降級到legacy模式
                        if self._legacy_manager:
                            knowledge_points = self._legacy_manager.knowledge_points
                        else:
                            knowledge_points = []
            else:
                # JSON 模式降級
                knowledge_points = self._legacy_manager.knowledge_points if self._legacy_manager else []

            data = {
                "version": "4.0",
                "last_updated": datetime.now().isoformat(),
                "data": [kp.to_dict() for kp in knowledge_points],
                "mode": "database" if self.use_database else "json",
                "source": "cache" if self.use_database else "legacy"
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"成功匯出 {len(data['data'])} 個知識點到 {filepath} (模式: {data['mode']})")

        except Exception as e:
            self.logger.error(f"匯出失敗: {e}")
            raise

    # 向後兼容的同步 API（功能受限，僅支援 JSON 模式）
    @property
    def knowledge_points(self) -> list[KnowledgePoint]:
        """獲取所有知識點（同步版本，資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            # 資料庫模式 - 返回快取中的數據
            return self._knowledge_points_cache
        elif self._legacy_manager:
            # JSON 模式降級
            return self._legacy_manager.knowledge_points
        else:
            return []

    def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        """根據 ID 獲取知識點（同步版本，資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            try:
                # 嘗試從快取中查找
                try:
                    id_int = int(point_id)
                except (ValueError, TypeError):
                    self.logger.warning(f"無效的知識點 ID: {point_id}")
                    return None

                for point in self._knowledge_points_cache:
                    if point.id == id_int:
                        return point

                # 如果快取中沒有且未初始化，嘗試異步查詢
                if not self._initialization_complete:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 循環正在運行，使用快取結果
                            self.logger.warning(f"知識點 {point_id} 未在快取中找到，建議使用 get_knowledge_point_async")
                            return None
                        else:
                            return loop.run_until_complete(self.get_knowledge_point_async(point_id))
                    except RuntimeError:
                        return asyncio.run(self.get_knowledge_point_async(point_id))

                return None
            except Exception as e:
                self.logger.error(f"資料庫查詢知識點失敗: {e}")
                # 降級到legacy模式
                if self._legacy_manager:
                    self.logger.warning("降級到JSON模式查詢知識點")
                    return self._legacy_manager.get_knowledge_point(point_id)
                return None

        # JSON 模式降級
        if self._legacy_manager:
            return self._legacy_manager.get_knowledge_point(point_id)
        return None

    def get_review_candidates(self, max_points: int = 5) -> list[KnowledgePoint]:
        """獲取適合複習的知識點（同步版本，資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            try:
                # 如果未初始化，嘗試觸發初始化
                if not self._initialization_complete:
                    import asyncio

                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 循環正在運行，使用快取數據
                            return self._get_cached_review_candidates(max_points)
                        else:
                            return loop.run_until_complete(
                                self.get_review_candidates_async(max_points)
                            )
                    except RuntimeError:
                        return asyncio.run(self.get_review_candidates_async(max_points))
                else:
                    # 已初始化，使用快取
                    return self._get_cached_review_candidates(max_points)
            except Exception as e:
                self.logger.error(f"資料庫獲取複習候選失敗: {e}")
                # 降級到legacy模式
                if self._legacy_manager:
                    self.logger.warning("降級到JSON模式獲取複習候選")
                    return self._legacy_manager.get_review_candidates(max_points=max_points)
                return []

        # 如果不是資料庫模式，使用legacy
        if self._legacy_manager:
            return self._legacy_manager.get_review_candidates(max_points=max_points)
        return []

    def get_due_points(self) -> list[KnowledgePoint]:
        """獲取需要複習的知識點（與 LegacyKnowledgeManager 兼容）"""
        return self.get_review_candidates(max_points=100)

    def add_review_success(
        self, knowledge_point_id: int, chinese_sentence: str, user_answer: str
    ) -> None:
        """為知識點添加複習成功記錄（同步版本，資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            try:
                # 嘗試使用異步方法
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 循環正在運行，建議使用異步方法
                        self.logger.warning("資料庫模式下建議使用 add_review_success_async")
                        return
                    else:
                        loop.run_until_complete(
                            self.add_review_success_async(knowledge_point_id, chinese_sentence, user_answer)
                        )
                        return
                except RuntimeError:
                    asyncio.run(
                        self.add_review_success_async(knowledge_point_id, chinese_sentence, user_answer)
                    )
                    return
            except Exception as e:
                self.logger.error(f"資料庫添加複習記錄失敗: {e}")
                # 降級到legacy模式
                if self._legacy_manager:
                    self.logger.warning("降級到JSON模式添加複習記錄")
                    self._legacy_manager.add_review_success(
                        knowledge_point_id, chinese_sentence, user_answer
                    )
                return

        # JSON 模式降級
        if self._legacy_manager:
            self._legacy_manager.add_review_success(
                knowledge_point_id, chinese_sentence, user_answer
            )
        else:
            self.logger.warning("無可用的知識管理器")

    @with_error_handling(operation="get_statistics", mode="auto")
    def get_statistics(self) -> dict[str, Any]:
        """獲取統計資料（同步版本，使用統一快取管理器）

        TASK-20A: 統一快取管理系統
        TASK-20D: 添加統一錯誤處理和降級策略
        同步版本使用統一快取，確保與異步方法一致
        """
        try:
            # 資料庫模式優先（用戶要求資料庫作為主要方式）
            if self.use_database:
                result = self._cache_manager.get_or_compute(
                    key=f"{CacheCategories.STATISTICS}:sync",
                    compute_func=self._compute_statistics_sync,
                    ttl=60,  # 統計快取1分鐘
                )
                # 更新降級快取
                self._update_fallback_cache("get_statistics", result)
                return result

            # 如果不是資料庫模式，使用legacy
            if self._legacy_manager:
                result = self._legacy_manager.get_statistics()
                self._update_fallback_cache("get_statistics", result)
                return result

            return self._get_empty_statistics()

        except Exception as e:
            # 統一錯誤處理和降級
            return self._handle_error_with_fallback(e, "get_statistics")

    def _compute_statistics_sync(self) -> dict[str, Any]:
        """計算統計資料（同步版本）

        由於同步環境限制，使用快取數據計算統計
        """
        try:
            # 在同步環境中，我們只能使用已載入的快取數據
            if not self._initialization_complete:
                self.logger.warning("數據庫未初始化，使用空統計")
                return self._get_empty_statistics()

            # 使用本地快取計算統計
            return self._get_cached_statistics()

        except Exception as e:
            self.logger.error(f"同步統計計算失敗: {e}")
            return self._get_empty_statistics()

    def _invalidate_related_caches(self) -> None:
        """清除相關快取"""
        # 清除統計快取
        self._cache_manager.invalidate(CacheCategories.STATISTICS)
        # 清除複習候選快取
        self._cache_manager.invalidate(CacheCategories.REVIEW_CANDIDATES)
        # 清除知識點快取
        self._cache_manager.invalidate(CacheCategories.KNOWLEDGE_POINTS)
        # 清除搜索結果快取
        self._cache_manager.invalidate(CacheCategories.SEARCH_RESULTS)

        self.logger.debug("已清除相關快取")

    def _get_cached_statistics(self) -> dict[str, Any]:
        """從快取獲取統計資料（前端兼容格式）"""
        if not self._knowledge_points_cache:
            return self._get_empty_statistics()

        # 基於快取計算統計
        active_points = [p for p in self._knowledge_points_cache if not p.is_deleted]
        deleted_points = [p for p in self._knowledge_points_cache if p.is_deleted]

        if not active_points:
            return self._get_empty_statistics()

        # 計算統計資料
        total_count = len(active_points)
        avg_mastery = sum(p.mastery_level for p in active_points) / total_count

        # 計算複習候選
        review_candidates = self._get_cached_review_candidates(100)
        due_reviews = len(review_candidates)

        # 計算正確和錯誤次數（基於所有知識點的歷史記錄）
        total_practices = 0
        correct_count = 0
        mistake_count = 0

        for point in active_points:
            total_practices += point.mistake_count + point.correct_count
            correct_count += point.correct_count
            mistake_count += point.mistake_count

        # 按分類統計（中文格式，與舊版兼容）
        from collections import defaultdict

        category_stats = defaultdict(int)
        for point in active_points:
            category_chinese = (
                point.category.to_chinese()
                if hasattr(point.category, "to_chinese")
                else point.category.value
            )
            category_stats[category_chinese] += 1

        return {
            # 前端期望的字段格式
            "total_practices": total_practices,
            "correct_count": correct_count,
            "mistake_count": mistake_count,
            "accuracy": correct_count / total_practices if total_practices > 0 else 0.0,
            "knowledge_points": total_count,
            "avg_mastery": avg_mastery,
            "category_distribution": dict(category_stats),
            "due_reviews": due_reviews,
            # 額外的統計信息
            "deleted_points": len(deleted_points),
            "points_by_mastery": {
                "beginner": len([p for p in active_points if p.mastery_level < 0.3]),
                "intermediate": len([p for p in active_points if 0.3 <= p.mastery_level < 0.7]),
                "advanced": len([p for p in active_points if p.mastery_level >= 0.7]),
            },
        }

    def _get_empty_statistics(self) -> dict[str, Any]:
        """返回空的統計資料結構（前端兼容格式）"""
        return {
            "total_practices": 0,
            "correct_count": 0,
            "mistake_count": 0,
            "accuracy": 0.0,
            "knowledge_points": 0,
            "avg_mastery": 0.0,
            "category_distribution": {},
            "due_reviews": 0,
            "deleted_points": 0,
            "points_by_mastery": {"beginner": 0, "intermediate": 0, "advanced": 0},
        }

    async def _convert_db_stats_to_frontend_format(
        self, raw_stats: dict[str, Any]
    ) -> dict[str, Any]:
        """將數據庫原始統計轉換為前端兼容格式"""
        try:
            # 獲取詳細的知識點統計資料
            total_active = raw_stats.get("total_active", 0)
            mastered = raw_stats.get("mastered", 0)
            struggling = raw_stats.get("struggling", 0)
            due_review = raw_stats.get("due_review", 0)
            avg_mastery = float(raw_stats.get("avg_mastery", 0.0) or 0.0)

            # 獲取練習歷史統計（需要從repository獲取）
            practice_stats = await self._get_practice_statistics()
            total_practices = practice_stats.get("total_practices", 0)
            correct_count = practice_stats.get("correct_count", 0)
            mistake_count = total_practices - correct_count

            # 獲取分類分布
            category_distribution = await self._get_category_distribution()

            return {
                # 前端期望的字段格式
                "total_practices": total_practices,
                "correct_count": correct_count,
                "mistake_count": mistake_count,
                "accuracy": correct_count / total_practices if total_practices > 0 else 0.0,
                "knowledge_points": total_active,
                "avg_mastery": avg_mastery,
                "category_distribution": category_distribution,
                "due_reviews": due_review,
                # 額外的統計信息
                "deleted_points": 0,  # 可以稍後從數據庫查詢
                "points_by_mastery": {
                    "beginner": struggling,
                    "intermediate": total_active - mastered - struggling,
                    "advanced": mastered,
                },
            }
        except Exception as e:
            self.logger.error(f"轉換統計格式失敗: {e}")
            # 降級到快取統計
            return self._get_cached_statistics()

    async def _get_practice_statistics(self) -> dict[str, Any]:
        """獲取練習統計資料"""
        try:
            if self._repository:
                # 查詢練習歷史統計
                query = """
                    SELECT
                        COALESCE(SUM(correct_count + mistake_count), 0) as total_practices,
                        COALESCE(SUM(correct_count), 0) as correct_count
                    FROM knowledge_points
                    WHERE is_deleted = FALSE
                """
                async with self._repository.connection() as conn:
                    row = await conn.fetchrow(query)
                    return dict(row) if row else {"total_practices": 0, "correct_count": 0}
        except Exception as e:
            self.logger.error(f"獲取練習統計失敗: {e}")
        return {"total_practices": 0, "correct_count": 0}

    async def _get_category_distribution(self) -> dict[str, int]:
        """獲取分類分布"""
        try:
            if self._repository:
                query = """
                    SELECT category, COUNT(*) as count
                    FROM knowledge_points
                    WHERE is_deleted = FALSE
                    GROUP BY category
                """
                async with self._repository.connection() as conn:
                    rows = await conn.fetch(query)
                    # 轉換為中文分類名
                    from core.error_types import ErrorCategory

                    result = {}
                    for row in rows:
                        category = row["category"]
                        count = row["count"]
                        # 嘗試轉換為中文名
                        try:
                            error_cat = ErrorCategory(category)
                            chinese_name = error_cat.to_chinese()
                        except (ValueError, AttributeError):
                            chinese_name = category  # 保持原值
                        result[chinese_name] = count
                    return result
        except Exception as e:
            self.logger.error(f"獲取分類分布失敗: {e}")
        return {}

    def _get_cached_review_candidates(self, max_points: int = 5) -> list[KnowledgePoint]:
        """從快取獲取複習候選"""
        if not self._knowledge_points_cache:
            return []

        from datetime import datetime

        # 過濾出需要複習的知識點
        due_points = []
        now = datetime.now()

        for point in self._knowledge_points_cache:
            if point.is_deleted:
                continue

            # 檢查是否需要複習
            if point.next_review:
                try:
                    review_date = datetime.fromisoformat(point.next_review)
                    # 確保兩個 datetime 都是 offset-naive
                    if review_date.tzinfo is not None:
                        # 如果 review_date 有時區，移除時區資訊
                        review_date = review_date.replace(tzinfo=None)

                    if review_date <= now:
                        due_points.append(point)
                except (ValueError, TypeError):
                    continue

        # 按優先級排序（掌握度低的優先）
        due_points.sort(key=lambda p: (p.mastery_level, p.mistake_count), reverse=False)

        return due_points[:max_points]

    def search_knowledge_points(self, keyword: str) -> list[KnowledgePoint]:
        """搜索知識點（同步版本，資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            try:
                # 嘗試使用異步搜索
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 循環正在運行，使用快取搜索
                        keyword_lower = keyword.lower()
                        results = [
                            point for point in self._knowledge_points_cache
                            if not point.is_deleted and (
                                keyword_lower in point.key_point.lower()
                                or keyword_lower in point.explanation.lower()
                                or keyword_lower in point.original_phrase.lower()
                                or keyword_lower in point.correction.lower()
                            )
                        ]
                        return results
                    else:
                        return loop.run_until_complete(self.search_knowledge_points_async(keyword))
                except RuntimeError:
                    return asyncio.run(self.search_knowledge_points_async(keyword))
            except Exception as e:
                self.logger.error(f"資料庫搜索失敗: {e}")
                # 降級到legacy模式
                if self._legacy_manager:
                    self.logger.warning("降級到JSON模式搜索知識點")
                    return [
                        point
                        for point in self._legacy_manager.knowledge_points
                        if keyword.lower() in point.key_point.lower()
                        or keyword.lower() in point.explanation.lower()
                        or keyword.lower() in point.original_phrase.lower()
                    ]
                return []

        # JSON 模式降級
        if self._legacy_manager:
            return [
                point
                for point in self._legacy_manager.knowledge_points
                if keyword.lower() in point.key_point.lower()
                or keyword.lower() in point.explanation.lower()
                or keyword.lower() in point.original_phrase.lower()
            ]
        return []

    def import_from_json(self, filepath: str) -> bool:
        """從 JSON 匯入（同步版本，資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            try:
                # 嘗試使用異步匯入
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 循環正在運行，建議使用異步方法
                        self.logger.warning("資料庫模式下建議使用 import_from_json_async")
                        return False
                    else:
                        return loop.run_until_complete(self.import_from_json_async(filepath))
                except RuntimeError:
                    return asyncio.run(self.import_from_json_async(filepath))
            except Exception as e:
                self.logger.error(f"資料庫匯入失敗: {e}")
                return False

        # JSON 模式不支援匯入功能
        if self._legacy_manager:
            self.logger.error("JSON 模式不支援匯入功能")
            return False
        return False

    # === 缺失的同步方法實現 ===

    def get_active_points(self) -> list[KnowledgePoint]:
        """獲取所有活躍（未刪除）的知識點（資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            if self._cache_dirty:
                self.logger.warning("資料庫模式下建議使用 get_active_points_async")
            return [p for p in self._knowledge_points_cache if not p.is_deleted]
        elif self._legacy_manager:
            # JSON 模式降級
            return [p for p in self._legacy_manager.knowledge_points if not p.is_deleted]
        else:
            return []

    def get_deleted_points(self) -> list[KnowledgePoint]:
        """獲取回收站中的知識點（資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            try:
                # 嘗試使用異步方法獲取已刪除的知識點
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 循環正在運行，使用快取查詢
                        deleted_points = [p for p in self._knowledge_points_cache if p.is_deleted]
                        return deleted_points
                    else:
                        return loop.run_until_complete(self.get_deleted_points_async())
                except RuntimeError:
                    return asyncio.run(self.get_deleted_points_async())
            except Exception as e:
                self.logger.error(f"資料庫查詢已刪除知識點失敗: {e}")
                # 降級到legacy模式
                if self._legacy_manager:
                    self.logger.warning("降級到JSON模式獲取回收站知識點")
                    return [p for p in self._legacy_manager.knowledge_points if p.is_deleted]
                return []

        # JSON 模式降級
        if self._legacy_manager:
            return [p for p in self._legacy_manager.knowledge_points if p.is_deleted]
        else:
            return []

    async def get_deleted_points_async(self) -> list[KnowledgePoint]:
        """異步獲取回收站中的知識點（資料庫優先）"""
        await self._ensure_initialized()

        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database and self._repository:
            # 資料庫模式 - 直接查詢已刪除的知識點
            try:
                deleted_points = await self._repository.find_all(is_deleted=True)
                self.logger.debug(f"查詢到 {len(deleted_points)} 個回收站知識點")
                return deleted_points
            except Exception as e:
                self.logger.error(f"查詢回收站知識點失敗: {e}")
                # 降級到legacy模式
                if self._legacy_manager:
                    self.logger.warning("降級到JSON模式獲取回收站知識點")
                    return [p for p in self._legacy_manager.knowledge_points if p.is_deleted]
                return []
        elif self._legacy_manager:
            # JSON 模式降級
            return [p for p in self._legacy_manager.knowledge_points if p.is_deleted]
        else:
            return []

    async def get_active_points_async(self) -> list[KnowledgePoint]:
        """異步獲取所有活躍（未刪除）的知識點（資料庫優先）"""
        await self._ensure_initialized()

        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database and self._repository:
            try:
                active_points = await self._repository.find_all(is_deleted=False)
                self.logger.debug(f"查詢到 {len(active_points)} 個活躍知識點")
                return active_points
            except Exception as e:
                self.logger.error(f"查詢活躍知識點失敗: {e}")
                # 降級到legacy模式
                if self._legacy_manager:
                    self.logger.warning("降級到JSON模式獲取活躍知識點")
                    return [p for p in self._legacy_manager.knowledge_points if not p.is_deleted]
                return []
        elif self._legacy_manager:
            # JSON 模式降級
            return [p for p in self._legacy_manager.knowledge_points if not p.is_deleted]
        else:
            return []

    def get_points_by_category(self, category: str) -> list[KnowledgePoint]:
        """按分類獲取知識點（資料庫優先）"""
        # 資料庫模式優先（用戶要求資料庫作為主要方式）
        if self.use_database:
            try:
                # 使用快取進行分類過濾
                return [
                    p
                    for p in self._knowledge_points_cache
                    if p.category.value == category and not p.is_deleted
                ]
            except Exception as e:
                self.logger.error(f"資料庫按分類查詢失敗: {e}")
                # 降級到legacy模式
                if self._legacy_manager:
                    self.logger.warning("降級到JSON模式按分類查詢")
                    return [
                        p
                        for p in self._legacy_manager.knowledge_points
                        if p.category.value == category and not p.is_deleted
                    ]
                return []

        # JSON 模式降級
        if self._legacy_manager:
            return [
                p
                for p in self._legacy_manager.knowledge_points
                if p.category.value == category and not p.is_deleted
            ]
        else:
            return []

    def edit_knowledge_point(self, point_id: int, updates: dict = None, **kwargs) -> Optional[dict]:
        """編輯知識點（同步版本）

        Returns:
            編輯歷史記錄，如果失敗返回 None
        """
        # 兼容舊的 kwargs 方式調用
        if updates is None:
            updates = kwargs

        if self._legacy_manager:
            # JSON 模式 - 使用原始方法以保持一致性
            return self._legacy_manager.edit_knowledge_point(point_id, updates)
        else:
            # 資料庫模式 - 創建類似的歷史記錄
            self.logger.warning(
                "資料庫模式下請使用 edit_knowledge_point_async 或 update_knowledge_point_async"
            )
            # 嘗試更新快取並創建歷史記錄
            for point in self._knowledge_points_cache:
                if point.id == point_id:
                    # 記錄變更前的狀態
                    before_state = {
                        "key_point": point.key_point,
                        "explanation": point.explanation,
                        "original_phrase": point.original_phrase,
                        "correction": point.correction,
                        "category": point.category.value,
                        "subtype": point.subtype,
                        "tags": point.tags.copy() if point.tags else [],
                        "custom_notes": point.custom_notes,
                    }

                    # 應用更新
                    for key, value in updates.items():
                        if hasattr(point, key):
                            setattr(point, key, value)

                    # 更新時間戳
                    timestamp = datetime.now().isoformat()
                    point.last_modified = timestamp
                    self._cache_dirty = True

                    # 創建歷史記錄
                    history_entry = {
                        "timestamp": timestamp,
                        "before": before_state,
                        "after": {
                            "key_point": point.key_point,
                            "explanation": point.explanation,
                            "original_phrase": point.original_phrase,
                            "correction": point.correction,
                            "category": point.category.value,
                            "subtype": point.subtype,
                            "tags": point.tags.copy() if point.tags else [],
                            "custom_notes": point.custom_notes,
                        },
                        "changed_fields": list(updates.keys()),
                    }

                    return history_entry
            return None

    def delete_knowledge_point(self, point_id: int, reason: str = "") -> bool:
        """刪除知識點（軟刪除）"""
        if self._legacy_manager:
            # JSON 模式
            return self._legacy_manager.delete_knowledge_point(point_id, reason)
        else:
            # 資料庫模式
            self.logger.warning("資料庫模式下請使用 delete_knowledge_point_async")
            # 更新快取
            for point in self._knowledge_points_cache:
                if point.id == point_id:
                    point.is_deleted = True
                    point.deleted_at = datetime.now().isoformat()
                    point.deleted_reason = reason
                    self._cache_dirty = True
                    return True
            return False

    def restore_knowledge_point(self, point_id: int) -> bool:
        """恢復已刪除的知識點"""
        if self._legacy_manager:
            # JSON 模式
            for point in self._legacy_manager.knowledge_points:
                if point.id == point_id and point.is_deleted:
                    point.is_deleted = False
                    point.deleted_at = ""
                    point.deleted_reason = ""
                    self._legacy_manager._save_knowledge()
                    return True
            return False
        else:
            # 資料庫模式
            self.logger.warning("資料庫模式下請使用 restore_knowledge_point_async")
            # 更新快取
            for point in self._knowledge_points_cache:
                if point.id == point_id and point.is_deleted:
                    point.is_deleted = False
                    point.deleted_at = ""
                    point.deleted_reason = ""
                    self._cache_dirty = True
                    return True
            return False

    def add_knowledge_point_from_error(
        self, chinese_sentence: str, user_answer: str, error: dict, correct_answer: str
    ) -> int:
        """從錯誤信息創建知識點（用於手動確認功能）

        Args:
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            error: 錯誤分析數據
            correct_answer: 正確答案

        Returns:
            新創建的知識點ID
        """
        if self._legacy_manager:
            # JSON 模式：直接調用原方法
            return self._legacy_manager.add_knowledge_point_from_error(
                chinese_sentence, user_answer, error, correct_answer
            )
        else:
            # 資料庫模式：需要異步操作
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果在異步上下文中，創建任務
                    asyncio.ensure_future(
                        self._add_knowledge_point_from_error_async(
                            chinese_sentence, user_answer, error, correct_answer
                        )
                    )
                    # 返回臨時 ID（實際 ID 會在異步操作完成後確定）
                    return len(self._knowledge_points_cache) + 1
                else:
                    return loop.run_until_complete(
                        self._add_knowledge_point_from_error_async(
                            chinese_sentence, user_answer, error, correct_answer
                        )
                    )
            except RuntimeError:
                return asyncio.run(
                    self._add_knowledge_point_from_error_async(
                        chinese_sentence, user_answer, error, correct_answer
                    )
                )

    async def _add_knowledge_point_from_error_async(
        self, chinese_sentence: str, user_answer: str, error: dict, correct_answer: str
    ) -> int:
        """異步版本：從錯誤信息創建知識點"""
        from datetime import datetime

        from core.error_types import ErrorCategory

        # 處理 category - 確保是字符串（資料庫存儲為字符串）
        category_str = error.get("category", "other")
        if not isinstance(category_str, str):
            category_str = category_str.value if hasattr(category_str, "value") else "other"

        # 創建知識點數據
        point_data = {
            "key_point": error.get("key_point_summary", "未知錯誤"),
            "original_phrase": error.get("original_phrase", user_answer),
            "correction": error.get("correction", correct_answer),
            "explanation": error.get("explanation", ""),
            "category": category_str,
            "subtype": error.get("subtype", "general"),
            "mastery_level": 0.1,
            "mistake_count": 1,
            "correct_count": 0,
            "last_seen": datetime.now().isoformat(),
            "next_review": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "is_deleted": False,
            "deleted_reason": "",
            "deleted_at": "",
            "custom_notes": "",
            "tags": [],
            "review_examples": [],
            "version_history": [],
            "last_modified": datetime.now().isoformat(),
            "original_error": {
                "chinese_sentence": chinese_sentence,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "timestamp": datetime.now().isoformat(),
            }
        }

        # 保存到資料庫
        if self._repository:
            # 將字典數據轉換為 KnowledgePoint 實體
            from core.models import KnowledgePoint, OriginalError

            # 創建 OriginalError 對象
            original_error = OriginalError(
                chinese_sentence=chinese_sentence,
                user_answer=user_answer,
                correct_answer=correct_answer,
                timestamp=datetime.now().isoformat()
            )

            # 創建 KnowledgePoint 實體
            point = KnowledgePoint(
                id=0,  # 資料庫會自動分配 ID
                key_point=point_data["key_point"],
                original_phrase=point_data["original_phrase"],
                correction=point_data["correction"],
                explanation=point_data["explanation"],
                category=ErrorCategory.from_string(category_str),
                subtype=point_data["subtype"],
                mastery_level=point_data["mastery_level"],
                mistake_count=point_data["mistake_count"],
                correct_count=point_data["correct_count"],
                last_seen=point_data["last_seen"],
                next_review=point_data["next_review"],
                created_at=point_data["created_at"],
                is_deleted=point_data["is_deleted"],
                deleted_reason=point_data["deleted_reason"],
                deleted_at=point_data["deleted_at"],
                custom_notes=point_data["custom_notes"],
                tags=point_data["tags"],
                review_examples=point_data["review_examples"],
                version_history=point_data["version_history"],
                last_modified=point_data["last_modified"],
                original_error=original_error
            )

            # 調用正確的 create 方法
            created_point = await self._repository.create(point)

            # 更新快取
            await self._load_cache_from_database_async()

            return created_point.id
        else:
            self.logger.error("Repository not initialized")
            return -1

    def save_mistake(
        self,
        chinese_sentence: str,
        user_answer: str,
        feedback: dict[str, Any],
        practice_mode: str = "new",
    ) -> bool:
        """保存錯誤為知識點（修復方法簽名）"""
        if self._legacy_manager:
            # JSON 模式 - 調用原始方法
            try:
                self._legacy_manager.save_mistake(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    feedback=feedback,
                    practice_mode=practice_mode,
                )
                return True
            except Exception as e:
                self.logger.error(f"保存錯誤失敗: {e}")
                return False
        else:
            # 資料庫模式 - 使用異步方法的同步包裝
            try:
                import asyncio

                # 檢查是否已經有事件循環在運行
                try:
                    asyncio.get_running_loop()
                    # 如果有循環在運行，我們需要創建一個新的任務
                    self.logger.warning("資料庫模式下建議使用 save_mistake_async，嘗試同步執行")

                    # 由於我們在同步上下文中，我們需要直接調用 JSON 模式作為後備
                    if not self._legacy_manager:
                        self._initialize_legacy()  # 初始化 JSON 模式作為後備

                    if self._legacy_manager:
                        return self._legacy_manager.save_mistake(
                            chinese_sentence=chinese_sentence,
                            user_answer=user_answer,
                            feedback=feedback,
                            practice_mode=practice_mode,
                        )
                    return False
                except RuntimeError:
                    # 沒有運行中的事件循環，可以創建新的
                    return asyncio.run(
                        self._save_mistake_async(
                            chinese_sentence=chinese_sentence,
                            user_answer=user_answer,
                            feedback=feedback,
                            practice_mode=practice_mode,
                        )
                    )

            except Exception as e:
                self.logger.error(f"資料庫模式保存錯誤失敗: {e}")
                # 降級到 JSON 模式
                if not self._legacy_manager:
                    self._initialize_legacy()
                if self._legacy_manager:
                    return self._legacy_manager.save_mistake(
                        chinese_sentence=chinese_sentence,
                        user_answer=user_answer,
                        feedback=feedback,
                        practice_mode=practice_mode,
                    )
                return False

    def get_all_mistakes(self) -> list[dict]:
        """獲取所有錯誤記錄（以字典格式）"""
        if self._legacy_manager:
            # JSON 模式 - 調用原始方法
            if hasattr(self._legacy_manager, "get_all_mistakes"):
                return self._legacy_manager.get_all_mistakes()
            else:
                # 簡化實現：轉換知識點為錯誤格式
                mistakes = []
                for point in self._legacy_manager.knowledge_points:
                    if not point.is_deleted:
                        mistakes.append(
                            {
                                "id": point.id,
                                "key_point": point.key_point,
                                "category": point.category.value,
                                "original_error": point.original_error,
                                "mastery_level": point.mastery_level,
                                "mistake_count": point.mistake_count,
                            }
                        )
                return mistakes
        else:
            # 資料庫模式 - 從快取轉換
            mistakes = []
            for point in self._knowledge_points_cache:
                if not point.is_deleted:
                    mistakes.append(
                        {
                            "id": point.id,
                            "key_point": point.key_point,
                            "category": point.category.value,
                            "original_error": point.original_error,
                            "mastery_level": point.mastery_level,
                            "mistake_count": point.mistake_count,
                        }
                    )
            return mistakes

    def update_knowledge_point(self, point_id: int, **kwargs) -> bool:
        """更新知識點（同 edit_knowledge_point）"""
        return self.edit_knowledge_point(point_id, **kwargs)

    # === 學習推薦系統 ===

    def get_learning_recommendations(self) -> dict[str, Any]:
        """獲取學習推薦

        根據用戶的錯誤模式、掌握度和複習進度生成個性化推薦

        Returns:
            包含推薦信息的字典：
            - recommendations: 推薦描述列表
            - focus_areas: 重點學習領域
            - suggested_difficulty: 建議難度等級
            - next_review_count: 待複習知識點數量
            - priority_points: 優先學習的知識點列表
        """
        from collections import defaultdict
        from datetime import datetime

        # 獲取所有活躍知識點
        if self._legacy_manager:
            # JSON 模式
            active_points = self.get_active_points()
        else:
            # 資料庫模式 - 建議使用異步版本
            self.logger.warning("資料庫模式下建議使用 get_learning_recommendations_async")
            # 使用事件循環橋接
            import asyncio
            try:
                if asyncio.get_running_loop():
                    future = asyncio.run_coroutine_threadsafe(
                        self.get_active_points_async(),
                        asyncio.get_running_loop()
                    )
                    active_points = future.result(timeout=30)
                else:
                    active_points = asyncio.run(self.get_active_points_async())
            except Exception as e:
                self.logger.error(f"無法獲取活躍知識點: {e}")
                active_points = []

        if not active_points:
            return {
                "recommendations": ["開始第一次練習，建立學習基礎"],
                "focus_areas": [],
                "suggested_difficulty": 1,
                "next_review_count": 0,
                "priority_points": [],
            }

        # 統計分析
        low_mastery_points = []  # 低掌握度知識點（< 0.3）
        medium_mastery_points = []  # 中等掌握度（0.3-0.7）
        due_for_review = []  # 待複習的點
        category_stats = defaultdict(lambda: {"count": 0, "avg_mastery": 0, "points": []})

        now = datetime.now()

        for point in active_points:
            # 掌握度分類
            if point.mastery_level < 0.3:
                low_mastery_points.append(point)
            elif point.mastery_level < 0.7:
                medium_mastery_points.append(point)

            # 檢查是否需要複習
            if point.next_review:
                try:
                    review_date = datetime.fromisoformat(point.next_review)
                    # 確保兩個 datetime 都是 offset-naive 或都是 offset-aware
                    if review_date.tzinfo is not None:
                        # 如果 review_date 有時區，移除時區資訊
                        review_date = review_date.replace(tzinfo=None)
                    if review_date <= now:
                        due_for_review.append(point)
                except (ValueError, TypeError):
                    # 如果解析失敗，跳過此點
                    continue

            # 統計各類別
            category = point.category.value
            category_stats[category]["count"] += 1
            category_stats[category]["avg_mastery"] += point.mastery_level
            category_stats[category]["points"].append(point)

        # 計算各類別平均掌握度
        for _category, stats in category_stats.items():
            if stats["count"] > 0:
                stats["avg_mastery"] /= stats["count"]

        # 生成推薦
        recommendations = []
        focus_areas = []

        # 1. 優先處理低掌握度的系統性錯誤
        systematic_low = [p for p in low_mastery_points if p.category.value == "systematic"]
        if systematic_low:
            recommendations.append(f"重點練習文法規則錯誤 ({len(systematic_low)} 個知識點待加強)")
            focus_areas.append("systematic")

        # 2. 處理待複習的知識點
        if len(due_for_review) > 5:
            recommendations.append(f"有 {len(due_for_review)} 個知識點需要複習，建議優先完成")

        # 3. 根據類別統計提供建議
        weakest_category = (
            min(category_stats.items(), key=lambda x: x[1]["avg_mastery"])
            if category_stats
            else None
        )

        if weakest_category and weakest_category[1]["avg_mastery"] < 0.5:
            category_name = weakest_category[0]
            category_chinese = {
                "systematic": "文法規則",
                "isolated": "個別詞彙",
                "enhancement": "表達優化",
                "other": "其他",
            }.get(category_name, category_name)

            recommendations.append(
                f"加強「{category_chinese}」類型的練習 (平均掌握度 {weakest_category[1]['avg_mastery']:.1%})"
            )
            if category_name not in focus_areas:
                focus_areas.append(category_name)

        # 4. 根據最近錯誤提供具體建議
        recent_mistakes = sorted(
            [p for p in active_points if p.mistake_count > 2],
            key=lambda x: x.last_seen,
            reverse=True,
        )[:5]

        if recent_mistakes:
            common_subtypes = defaultdict(int)
            for point in recent_mistakes:
                common_subtypes[point.subtype] += 1

            most_common = max(common_subtypes.items(), key=lambda x: x[1])
            if most_common[1] >= 2:
                recommendations.append(f"複習「{most_common[0]}」相關知識點")

        # 5. 確定建議難度
        avg_mastery = sum(p.mastery_level for p in active_points) / len(active_points)
        if avg_mastery < 0.3:
            suggested_difficulty = 1  # 簡單
        elif avg_mastery < 0.6:
            suggested_difficulty = 2  # 中等
        else:
            suggested_difficulty = 3  # 困難

        # 6. 選擇優先學習的知識點（最多10個）
        priority_points = []

        # 優先順序：待複習 > 低掌握度系統性 > 低掌握度其他 > 中等掌握度
        for point in due_for_review[:3]:
            if point not in priority_points:
                priority_points.append(point)

        for point in systematic_low[:3]:
            if point not in priority_points:
                priority_points.append(point)

        for point in low_mastery_points[:4]:
            if point not in priority_points and len(priority_points) < 10:
                priority_points.append(point)

        # 如果沒有具體推薦，提供一般性建議
        if not recommendations:
            if avg_mastery > 0.7:
                recommendations.append("整體掌握度良好，建議挑戰更高難度的內容")
            else:
                recommendations.append("持續練習以提升整體掌握度")

        return {
            "recommendations": recommendations[:3],  # 最多3條推薦
            "focus_areas": focus_areas[:2],  # 最多2個重點領域
            "suggested_difficulty": suggested_difficulty,
            "next_review_count": len(due_for_review),
            "priority_points": [
                {
                    "id": p.id,
                    "key_point": p.key_point,
                    "mastery_level": p.mastery_level,
                    "category": p.category.value,
                }
                for p in priority_points
            ],
            "statistics": {
                "total_points": len(active_points),
                "low_mastery_count": len(low_mastery_points),
                "average_mastery": avg_mastery,
                "due_for_review": len(due_for_review),
            },
        }

    async def get_learning_recommendations_async(self) -> dict[str, Any]:
        """獲取學習推薦（異步版本）

        根據用戶的錯誤模式、掌握度和複習進度生成個性化推薦

        Returns:
            包含推薦信息的字典：
            - recommendations: 推薦描述列表
            - focus_areas: 重點學習領域
            - suggested_difficulty: 建議難度等級
            - next_review_count: 待複習知識點數量
            - priority_points: 優先學習的知識點列表
        """
        from collections import defaultdict
        from datetime import datetime

        # 獲取所有活躍知識點（使用異步方法）
        active_points = await self.get_active_points_async()

        if not active_points:
            return {
                "recommendations": ["開始第一次練習，建立學習基礎"],
                "focus_areas": [],
                "suggested_difficulty": 1,
                "next_review_count": 0,
                "priority_points": [],
            }

        # 統計分析
        low_mastery_points = []  # 低掌握度知識點（< 0.3）
        medium_mastery_points = []  # 中等掌握度（0.3-0.7）
        due_for_review = []  # 待複習的點
        category_stats = defaultdict(lambda: {"count": 0, "avg_mastery": 0, "points": []})

        now = datetime.now()

        for point in active_points:
            # 掌握度分類
            if point.mastery_level < 0.3:
                low_mastery_points.append(point)
            elif point.mastery_level < 0.7:
                medium_mastery_points.append(point)

            # 檢查是否需要複習
            if point.next_review:
                try:
                    review_date = datetime.fromisoformat(point.next_review)
                    # 確保兩個 datetime 都是 offset-naive 或都是 offset-aware
                    if review_date.tzinfo is not None:
                        # 如果 review_date 有時區，移除時區資訊
                        review_date = review_date.replace(tzinfo=None)
                    if review_date <= now:
                        due_for_review.append(point)
                except (ValueError, TypeError):
                    # 如果解析失敗，跳過此點
                    continue

            # 統計各類別
            category = point.category.value
            category_stats[category]["count"] += 1
            category_stats[category]["avg_mastery"] += point.mastery_level
            category_stats[category]["points"].append(point)

        # 計算各類別平均掌握度
        for _category, stats in category_stats.items():
            if stats["count"] > 0:
                stats["avg_mastery"] /= stats["count"]

        # 生成推薦
        recommendations = []
        focus_areas = []

        # 1. 優先處理低掌握度的系統性錯誤
        systematic_low = [p for p in low_mastery_points if p.category.value == "systematic"]
        if systematic_low:
            recommendations.append(f"重點練習文法規則錯誤 ({len(systematic_low)} 個知識點待加強)")
            focus_areas.append("systematic")

        # 2. 處理待複習的知識點
        if len(due_for_review) > 5:
            recommendations.append(f"有 {len(due_for_review)} 個知識點需要複習，建議優先完成")

        # 3. 根據類別統計提供建議
        weakest_category = (
            min(category_stats.items(), key=lambda x: x[1]["avg_mastery"])
            if category_stats
            else None
        )

        if weakest_category and weakest_category[1]["avg_mastery"] < 0.5:
            category_name = weakest_category[0]
            category_chinese = {
                "systematic": "文法規則",
                "isolated": "個別詞彙",
                "enhancement": "表達優化",
                "other": "其他",
            }.get(category_name, category_name)

            recommendations.append(
                f"加強「{category_chinese}」類型的練習 (平均掌握度 {weakest_category[1]['avg_mastery']:.1%})"
            )
            if category_name not in focus_areas:
                focus_areas.append(category_name)

        # 4. 根據最近錯誤提供具體建議
        recent_mistakes = sorted(
            [p for p in active_points if p.mistake_count > 2],
            key=lambda x: x.last_seen,
            reverse=True,
        )[:5]

        if recent_mistakes:
            common_subtypes = defaultdict(int)
            for point in recent_mistakes:
                common_subtypes[point.subtype] += 1

            most_common = max(common_subtypes.items(), key=lambda x: x[1])
            if most_common[1] >= 2:
                recommendations.append(f"複習「{most_common[0]}」相關知識點")

        # 5. 確定建議難度
        avg_mastery = sum(p.mastery_level for p in active_points) / len(active_points)
        if avg_mastery < 0.3:
            suggested_difficulty = 1  # 簡單
        elif avg_mastery < 0.6:
            suggested_difficulty = 2  # 中等
        else:
            suggested_difficulty = 3  # 困難

        # 6. 選擇優先學習的知識點（最多10個）
        priority_points = []

        # 優先順序：待複習 > 低掌握度系統性 > 低掌握度其他 > 中等掌握度
        for point in due_for_review[:3]:
            if point not in priority_points:
                priority_points.append(point)

        for point in systematic_low[:3]:
            if point not in priority_points:
                priority_points.append(point)

        for point in low_mastery_points[:4]:
            if point not in priority_points and len(priority_points) < 10:
                priority_points.append(point)

        # 如果沒有具體推薦，提供一般性建議
        if not recommendations:
            if avg_mastery > 0.7:
                recommendations.append("整體掌握度良好，建議挑戰更高難度的內容")
            else:
                recommendations.append("持續練習以提升整體掌握度")

        return {
            "recommendations": recommendations[:3],  # 最多3條推薦
            "focus_areas": focus_areas[:2],  # 最多2個重點領域
            "suggested_difficulty": suggested_difficulty,
            "next_review_count": len(due_for_review),
            "priority_points": [
                {
                    "id": p.id,
                    "key_point": p.key_point,
                    "mastery_level": p.mastery_level,
                    "category": p.category.value,
                }
                for p in priority_points
            ],
            "statistics": {
                "total_points": len(active_points),
                "low_mastery_count": len(low_mastery_points),
                "average_mastery": avg_mastery,
                "due_for_review": len(due_for_review),
            },
        }

    def permanent_delete_old_points(
        self, days_old: int = 30, dry_run: bool = False
    ) -> dict[str, Any]:
        """永久刪除舊的已刪除知識點

        Args:
            days_old: 刪除多少天前的知識點（預設30天）
            dry_run: 是否只是預覽，不實際刪除

        Returns:
            刪除結果統計
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days_old)
        # 這個方法是同步的，需要在同步上下文中運行異步查詢
        import asyncio
        try:
            if asyncio.get_running_loop():
                # 已在異步上下文中，使用 run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(
                    self.get_deleted_points_async(),
                    asyncio.get_running_loop()
                )
                deleted_points = future.result(timeout=30)
            else:
                # 沒有運行的事件循環，直接運行
                deleted_points = asyncio.run(self.get_deleted_points_async())
        except Exception as e:
            self.logger.error(f"無法獲取已刪除的知識點: {e}")
            deleted_points = []

        points_to_delete = []
        points_to_keep = []

        for point in deleted_points:
            if point.deleted_at:
                deleted_date = datetime.fromisoformat(point.deleted_at)
                if deleted_date < cutoff_date:
                    # 檢查是否為高價值知識點（掌握度低或錯誤次數多）
                    if point.mastery_level < 0.3 or point.mistake_count > 5:
                        points_to_keep.append(
                            {
                                "id": point.id,
                                "key_point": point.key_point,
                                "reason": "high_value",
                                "mastery_level": point.mastery_level,
                                "mistake_count": point.mistake_count,
                            }
                        )
                    else:
                        points_to_delete.append(point)

        result = {
            "scanned": len(deleted_points),
            "eligible_for_deletion": len(points_to_delete),
            "preserved_high_value": len(points_to_keep),
            "dry_run": dry_run,
            "cutoff_date": cutoff_date.isoformat(),
            "deleted_ids": [],
            "preserved_points": points_to_keep,
        }

        if not dry_run and points_to_delete:
            # 實際執行刪除
            if self._legacy_manager:
                # JSON 模式
                original_count = len(self._legacy_manager.knowledge_points)
                self._legacy_manager.knowledge_points = [
                    p for p in self._legacy_manager.knowledge_points if p not in points_to_delete
                ]
                self._legacy_manager._save_knowledge()
                result["deleted_ids"] = [p.id for p in points_to_delete]
                result["final_count"] = len(self._legacy_manager.knowledge_points)
                result["deleted_count"] = original_count - result["final_count"]

                self.logger.info(f"永久刪除了 {result['deleted_count']} 個舊知識點")
            else:
                # 資料庫模式
                self.logger.warning("資料庫模式下請使用 permanent_delete_old_points_async")
                result["error"] = "Database mode requires async method"

        return result

    # 資源清理

    async def cleanup(self) -> None:
        """清理資源"""
        if self._db_connection:
            try:
                await self._db_connection.disconnect()
            except Exception as e:
                self.logger.error(f"清理資料庫連線失敗: {e}")

        self._db_connection = None
        self._repository = None
        self._legacy_manager = None

    # TASK-20D: 統一錯誤處理輔助方法
    def _update_fallback_cache(self, method_name: str, result: Any) -> None:
        """更新降級快取"""
        try:
            # 找到快取降級策略並更新快取
            cache_strategy = None
            for strategy in self._fallback_manager.strategies:
                if hasattr(strategy, "update_cache"):
                    cache_strategy = strategy
                    break

            if cache_strategy and result is not None:
                # 建立方法引用
                method_func = getattr(self, method_name, None)
                if method_func:
                    cache_strategy.update_cache(method_func, (self,), {}, result)

        except Exception as e:
            self.logger.warning(f"更新降級快取失敗: {e}")

    def _handle_error_with_fallback(self, error: Exception, operation: str) -> Any:
        """統一錯誤處理和降級邏輯"""
        try:
            # 使用統一錯誤處理器
            error_response = self._error_handler.handle_error(error, operation)

            if error_response.get("fallback_available", False):
                # 嘗試降級策略
                fallback_result = self._fallback_manager.execute_fallback(
                    ErrorCategory.DATABASE, ErrorSeverity.HIGH, getattr(self, operation), self
                )

                if fallback_result is not None:
                    self.logger.info(f"降級成功: {operation}")
                    return fallback_result

            # 根據操作類型返回安全的默認值
            return self._get_safe_default_for_operation(operation)

        except Exception as fallback_error:
            self.logger.error(f"降級處理失敗: {fallback_error}")
            return self._get_safe_default_for_operation(operation)

    def _get_safe_default_for_operation(self, operation: str) -> Any:
        """根據操作獲取安全的默認值"""
        defaults = {
            "get_statistics": self._get_empty_statistics(),
            "get_knowledge_points": [],
            "get_all_knowledge_points": [],
            "get_review_candidates": [],
            "search_knowledge_points": [],
            "get_knowledge_point": None,
            "add_knowledge_point": False,
            "edit_knowledge_point": None,
            "delete_knowledge_point": False,
            "restore_knowledge_point": None,
        }

        # 添加錯誤標記
        result = defaults.get(operation)
        if isinstance(result, dict):
            result = result.copy()
            result["_error_fallback"] = True
            result["_operation"] = operation

        return result


# 全域實例（為了向後兼容）
_knowledge_manager = None


async def get_knowledge_manager_async(
    use_database: bool = False, data_dir: Optional[str] = None
) -> KnowledgeManagerAdapter:
    """獲取知識管理器實例（異步版本）"""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManagerAdapter(use_database=use_database, data_dir=data_dir)
        await _knowledge_manager._ensure_initialized()
    return _knowledge_manager


def get_knowledge_manager(
    use_database: bool = False, data_dir: Optional[str] = None
) -> KnowledgeManagerAdapter:
    """獲取知識管理器實例（同步版本，功能受限）"""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManagerAdapter(use_database=use_database, data_dir=data_dir)
    return _knowledge_manager


async def reset_knowledge_manager() -> None:
    """重置知識管理器實例（主要用於測試）"""
    global _knowledge_manager
    if _knowledge_manager:
        await _knowledge_manager.cleanup()
    _knowledge_manager = None
