"""
修復後的適配器實現 - 解決異步初始化問題
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Optional

from core.database.connection import get_database_connection
from core.database.repositories.knowledge_repository import KnowledgePointRepository
from core.knowledge import KnowledgeManager as LegacyKnowledgeManager
from core.knowledge import KnowledgePoint, ReviewExample
from core.log_config import get_module_logger


class KnowledgeManagerAdapter:
    """
    修復後的資料庫適配器

    關鍵修復：
    1. 移除所有同步方法中的 asyncio.run()
    2. 使用 asyncio.Event 替代雙重檢查鎖定
    3. 更安全的資源管理
    4. 統一的異步 API
    """

    def __init__(self, use_database: bool = False, data_dir: Optional[str] = None):
        """初始化適配器"""
        self.logger = get_module_logger(self.__class__.__name__)
        self.use_database = use_database
        self.data_dir = data_dir or "data"

        # 資料庫相關
        self._db_connection = None
        self._repository: Optional[KnowledgePointRepository] = None

        # 傳統 JSON 管理器
        self._legacy_manager: Optional[LegacyKnowledgeManager] = None

        # 快取（用於資料庫模式）
        self._knowledge_points_cache: list[KnowledgePoint] = []
        self._cache_dirty = True

        # 使用 asyncio.Event 和 Lock 確保線程安全
        self._initialization_complete = asyncio.Event()
        self._initialization_failed = asyncio.Event()
        self._init_lock = None  # 延遲創建

        # 同步初始化
        self._initialize_sync()

    def _initialize_sync(self) -> None:
        """同步初始化（僅初始化 JSON 模式）"""
        if not self.use_database:
            self._initialize_legacy()
            self._initialization_complete.set()
        else:
            # 資料庫模式延遲到第一次使用時異步初始化
            self.logger.info("資料庫模式將在第一次使用時異步初始化")

    async def _ensure_initialized(self) -> None:
        """確保已初始化（線程安全的異步版本）"""
        # 快速路徑：如果已經初始化完成，直接返回
        if self._initialization_complete.is_set():
            return

        # 如果初始化失敗，拋出異常
        if self._initialization_failed.is_set():
            raise RuntimeError("適配器初始化失敗")

        # 延遲創建鎖（避免在 __init__ 中創建）
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()

        # 使用鎖防止競態條件
        async with self._init_lock:
            # 雙重檢查模式
            if self._initialization_complete.is_set():
                return
            if self._initialization_failed.is_set():
                raise RuntimeError("適配器初始化失敗")

            try:
                if self.use_database:
                    await self._initialize_database_async()
                self._initialization_complete.set()
                self.logger.info("適配器初始化成功完成")
            except Exception as e:
                self.logger.error(f"初始化失敗: {e}")
                self._initialization_failed.set()
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
        """初始化 JSON 模式"""
        try:
            if not self._legacy_manager:
                self._legacy_manager = LegacyKnowledgeManager(data_dir=self.data_dir)
                self.logger.info("JSON 模式初始化成功")
        except Exception as e:
            self.logger.error(f"JSON 模式初始化失敗: {e}")
            raise

    async def _fallback_to_legacy_async(self) -> None:
        """異步降級到 JSON 模式"""
        self.use_database = False
        self._db_connection = None
        self._repository = None
        self._initialize_legacy()

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
                    return True
                return False
            except Exception as e:
                self.logger.error(f"資料庫添加失敗: {e}")
                return False
        elif self._legacy_manager:
            # 使用 LegacyKnowledgeManager 的公開 API
            try:
                return self._legacy_manager.add_knowledge_point(knowledge_point)
            except AttributeError:
                # 降級處理：直接操作（記錄警告）
                self.logger.warning("使用降級方法添加知識點")
                self._legacy_manager.knowledge_points.append(knowledge_point)
                try:
                    self._legacy_manager._save_knowledge()
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
        """異步獲取統計資料"""
        await self._ensure_initialized()

        if self.use_database and self._repository:
            try:
                return await self._repository.get_statistics()
            except Exception as e:
                self.logger.error(f"獲取統計資料失敗: {e}")
                return {}
        elif self._legacy_manager:
            return self._legacy_manager.get_statistics()
        return {}

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

    def export_to_json(self, filepath: str) -> None:
        """匯出到 JSON（用於備份和遷移）"""
        try:
            data = {
                "version": "4.0",
                "last_updated": datetime.now().isoformat(),
                "data": [kp.to_dict() for kp in self.knowledge_points],
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"成功匯出 {len(data['data'])} 個知識點到 {filepath}")

        except Exception as e:
            self.logger.error(f"匯出失敗: {e}")
            raise

    # 向後兼容的同步 API（功能受限，僅支援 JSON 模式）
    @property
    def knowledge_points(self) -> list[KnowledgePoint]:
        """獲取所有知識點（同步版本，僅用於向後兼容）"""
        if self._legacy_manager:
            return self._legacy_manager.knowledge_points
        elif self.use_database and self._repository:
            # 資料庫模式下，如果未初始化，返回快取
            return self._knowledge_points_cache
        return []

    def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        """根據 ID 獲取知識點（同步版本，僅用於向後兼容）"""
        if self._legacy_manager:
            return self._legacy_manager.get_knowledge_point(point_id)
        # 資料庫模式下不支援同步操作
        self.logger.warning("同步方法在資料庫模式下不支援，請使用異步版本")
        return None

    def get_review_candidates(self, max_points: int = 5) -> list[KnowledgePoint]:
        """獲取適合複習的知識點（同步版本，僅用於向後兼容）"""
        if self._legacy_manager:
            return self._legacy_manager.get_review_candidates(max_points=max_points)
        self.logger.warning("資料庫模式下請使用 get_review_candidates_async")
        return []

    def get_due_points(self) -> list[KnowledgePoint]:
        """獲取需要複習的知識點（與 LegacyKnowledgeManager 兼容）"""
        return self.get_review_candidates(max_points=100)

    def add_review_success(
        self, knowledge_point_id: int, chinese_sentence: str, user_answer: str
    ) -> None:
        """為知識點添加複習成功記錄（同步版本，僅用於向後兼容）"""
        if self._legacy_manager:
            self._legacy_manager.add_review_success(
                knowledge_point_id, chinese_sentence, user_answer
            )
        else:
            self.logger.warning("資料庫模式下請使用 add_review_success_async")

    def get_statistics(self) -> dict[str, Any]:
        """獲取統計資料（同步版本，僅用於向後兼容）"""
        if self._legacy_manager:
            return self._legacy_manager.get_statistics()
        self.logger.warning("資料庫模式下請使用 get_statistics_async")
        return {}

    def search_knowledge_points(self, keyword: str) -> list[KnowledgePoint]:
        """搜索知識點（同步版本，僅用於向後兼容）"""
        if self._legacy_manager:
            # LegacyKnowledgeManager 可能沒有此方法，使用簡單過濾
            return [
                point
                for point in self._legacy_manager.knowledge_points
                if keyword.lower() in point.key_point.lower()
                or keyword.lower() in point.explanation.lower()
                or keyword.lower() in point.original_phrase.lower()
            ]
        self.logger.warning("資料庫模式下請使用 search_knowledge_points_async")
        return []

    def import_from_json(self, filepath: str) -> bool:
        """從 JSON 匯入（同步版本，僅用於向後兼容）"""
        if self._legacy_manager:
            self.logger.error("JSON 模式不支援匯入功能")
            return False
        self.logger.warning("資料庫模式下請使用 import_from_json_async")
        return False

    # === 缺失的同步方法實現 ===

    def get_active_points(self) -> list[KnowledgePoint]:
        """獲取所有活躍（未刪除）的知識點"""
        if self._legacy_manager:
            # JSON 模式
            return [p for p in self._legacy_manager.knowledge_points if not p.is_deleted]
        else:
            # 資料庫模式 - 使用快取
            if self._cache_dirty:
                self.logger.warning("資料庫模式下建議使用 get_active_points_async")
            return [p for p in self._knowledge_points_cache if not p.is_deleted]

    def get_deleted_points(self) -> list[KnowledgePoint]:
        """獲取回收站中的知識點"""
        if self._legacy_manager:
            # JSON 模式
            return [p for p in self._legacy_manager.knowledge_points if p.is_deleted]
        else:
            # 資料庫模式 - 使用快取
            return [p for p in self._knowledge_points_cache if p.is_deleted]

    def get_points_by_category(self, category: str) -> list[KnowledgePoint]:
        """按分類獲取知識點"""
        if self._legacy_manager:
            # JSON 模式
            return [p for p in self._legacy_manager.knowledge_points
                   if p.category.value == category and not p.is_deleted]
        else:
            # 資料庫模式 - 使用快取
            return [p for p in self._knowledge_points_cache
                   if p.category.value == category and not p.is_deleted]

    def edit_knowledge_point(self, point_id: int, **kwargs) -> bool:
        """編輯知識點（同步版本）"""
        if self._legacy_manager:
            # JSON 模式
            for point in self._legacy_manager.knowledge_points:
                if point.id == point_id:
                    for key, value in kwargs.items():
                        if hasattr(point, key):
                            setattr(point, key, value)
                    point.last_modified = datetime.now().isoformat()
                    self._legacy_manager._save_knowledge()
                    return True
            return False
        else:
            # 資料庫模式 - 需要異步操作
            self.logger.warning("資料庫模式下請使用 edit_knowledge_point_async 或 update_knowledge_point_async")
            # 嘗試更新快取
            for point in self._knowledge_points_cache:
                if point.id == point_id:
                    for key, value in kwargs.items():
                        if hasattr(point, key):
                            setattr(point, key, value)
                    point.last_modified = datetime.now().isoformat()
                    self._cache_dirty = True
                    return True
            return False

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

    def save_mistake(self, feedback: dict) -> bool:
        """保存錯誤為知識點"""
        if self._legacy_manager:
            # JSON 模式
            return self._legacy_manager.save_mistake(feedback)
        else:
            # 資料庫模式 - 簡化實現
            self.logger.warning("資料庫模式下請使用 save_mistake_async")
            return False

    def get_all_mistakes(self) -> list[dict]:
        """獲取所有錯誤記錄（以字典格式）"""
        if self._legacy_manager:
            # JSON 模式 - 調用原始方法
            if hasattr(self._legacy_manager, 'get_all_mistakes'):
                return self._legacy_manager.get_all_mistakes()
            else:
                # 簡化實現：轉換知識點為錯誤格式
                mistakes = []
                for point in self._legacy_manager.knowledge_points:
                    if not point.is_deleted:
                        mistakes.append({
                            'id': point.id,
                            'key_point': point.key_point,
                            'category': point.category.value,
                            'original_error': point.original_error,
                            'mastery_level': point.mastery_level,
                            'mistake_count': point.mistake_count
                        })
                return mistakes
        else:
            # 資料庫模式 - 從快取轉換
            mistakes = []
            for point in self._knowledge_points_cache:
                if not point.is_deleted:
                    mistakes.append({
                        'id': point.id,
                        'key_point': point.key_point,
                        'category': point.category.value,
                        'original_error': point.original_error,
                        'mastery_level': point.mastery_level,
                        'mistake_count': point.mistake_count
                    })
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
        active_points = self.get_active_points()

        if not active_points:
            return {
                'recommendations': ['開始第一次練習，建立學習基礎'],
                'focus_areas': [],
                'suggested_difficulty': 1,
                'next_review_count': 0,
                'priority_points': []
            }

        # 統計分析
        low_mastery_points = []  # 低掌握度知識點（< 0.3）
        medium_mastery_points = []  # 中等掌握度（0.3-0.7）
        due_for_review = []  # 待複習的點
        category_stats = defaultdict(lambda: {'count': 0, 'avg_mastery': 0, 'points': []})

        now = datetime.now()

        for point in active_points:
            # 掌握度分類
            if point.mastery_level < 0.3:
                low_mastery_points.append(point)
            elif point.mastery_level < 0.7:
                medium_mastery_points.append(point)

            # 檢查是否需要複習
            if point.next_review:
                review_date = datetime.fromisoformat(point.next_review)
                if review_date <= now:
                    due_for_review.append(point)

            # 統計各類別
            category = point.category.value
            category_stats[category]['count'] += 1
            category_stats[category]['avg_mastery'] += point.mastery_level
            category_stats[category]['points'].append(point)

        # 計算各類別平均掌握度
        for _category, stats in category_stats.items():
            if stats['count'] > 0:
                stats['avg_mastery'] /= stats['count']

        # 生成推薦
        recommendations = []
        focus_areas = []

        # 1. 優先處理低掌握度的系統性錯誤
        systematic_low = [p for p in low_mastery_points if p.category.value == 'systematic']
        if systematic_low:
            recommendations.append(
                f'重點練習文法規則錯誤 ({len(systematic_low)} 個知識點待加強)'
            )
            focus_areas.append('systematic')

        # 2. 處理待複習的知識點
        if len(due_for_review) > 5:
            recommendations.append(
                f'有 {len(due_for_review)} 個知識點需要複習，建議優先完成'
            )

        # 3. 根據類別統計提供建議
        weakest_category = min(
            category_stats.items(),
            key=lambda x: x[1]['avg_mastery']
        ) if category_stats else None

        if weakest_category and weakest_category[1]['avg_mastery'] < 0.5:
            category_name = weakest_category[0]
            category_chinese = {
                'systematic': '文法規則',
                'isolated': '個別詞彙',
                'enhancement': '表達優化',
                'other': '其他'
            }.get(category_name, category_name)

            recommendations.append(
                f'加強「{category_chinese}」類型的練習 (平均掌握度 {weakest_category[1]["avg_mastery"]:.1%})'
            )
            if category_name not in focus_areas:
                focus_areas.append(category_name)

        # 4. 根據最近錯誤提供具體建議
        recent_mistakes = sorted(
            [p for p in active_points if p.mistake_count > 2],
            key=lambda x: x.last_seen,
            reverse=True
        )[:5]

        if recent_mistakes:
            common_subtypes = defaultdict(int)
            for point in recent_mistakes:
                common_subtypes[point.subtype] += 1

            most_common = max(common_subtypes.items(), key=lambda x: x[1])
            if most_common[1] >= 2:
                recommendations.append(f'複習「{most_common[0]}」相關知識點')

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
                recommendations.append('整體掌握度良好，建議挑戰更高難度的內容')
            else:
                recommendations.append('持續練習以提升整體掌握度')

        return {
            'recommendations': recommendations[:3],  # 最多3條推薦
            'focus_areas': focus_areas[:2],  # 最多2個重點領域
            'suggested_difficulty': suggested_difficulty,
            'next_review_count': len(due_for_review),
            'priority_points': [
                {
                    'id': p.id,
                    'key_point': p.key_point,
                    'mastery_level': p.mastery_level,
                    'category': p.category.value
                } for p in priority_points
            ],
            'statistics': {
                'total_points': len(active_points),
                'low_mastery_count': len(low_mastery_points),
                'average_mastery': avg_mastery,
                'due_for_review': len(due_for_review)
            }
        }

    def permanent_delete_old_points(self, days_old: int = 30, dry_run: bool = False) -> dict[str, Any]:
        """永久刪除舊的已刪除知識點

        Args:
            days_old: 刪除多少天前的知識點（預設30天）
            dry_run: 是否只是預覽，不實際刪除

        Returns:
            刪除結果統計
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_points = self.get_deleted_points()

        points_to_delete = []
        points_to_keep = []

        for point in deleted_points:
            if point.deleted_at:
                deleted_date = datetime.fromisoformat(point.deleted_at)
                if deleted_date < cutoff_date:
                    # 檢查是否為高價值知識點（掌握度低或錯誤次數多）
                    if point.mastery_level < 0.3 or point.mistake_count > 5:
                        points_to_keep.append({
                            'id': point.id,
                            'key_point': point.key_point,
                            'reason': 'high_value',
                            'mastery_level': point.mastery_level,
                            'mistake_count': point.mistake_count
                        })
                    else:
                        points_to_delete.append(point)

        result = {
            'scanned': len(deleted_points),
            'eligible_for_deletion': len(points_to_delete),
            'preserved_high_value': len(points_to_keep),
            'dry_run': dry_run,
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_ids': [],
            'preserved_points': points_to_keep
        }

        if not dry_run and points_to_delete:
            # 實際執行刪除
            if self._legacy_manager:
                # JSON 模式
                original_count = len(self._legacy_manager.knowledge_points)
                self._legacy_manager.knowledge_points = [
                    p for p in self._legacy_manager.knowledge_points
                    if p not in points_to_delete
                ]
                self._legacy_manager._save_knowledge()
                result['deleted_ids'] = [p.id for p in points_to_delete]
                result['final_count'] = len(self._legacy_manager.knowledge_points)
                result['deleted_count'] = original_count - result['final_count']

                self.logger.info(
                    f"永久刪除了 {result['deleted_count']} 個舊知識點"
                )
            else:
                # 資料庫模式
                self.logger.warning("資料庫模式下請使用 permanent_delete_old_points_async")
                result['error'] = "Database mode requires async method"

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
