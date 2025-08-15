"""
知識點管理模組 - 純數據庫版本 (V3.0)
移除所有 JSON 依賴，使用純數據庫架構
"""

import os
import sys
from datetime import datetime
from typing import Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import data models from separate file to avoid circular imports
from core.models import KnowledgePoint, OriginalError, ReviewExample
from core.cache_manager import UnifiedCacheManager, CacheCategories
from core.error_types import ErrorCategory, ErrorTypeSystem
from core.exceptions import DatabaseError
from core.log_config import get_module_logger
from core.error_handler import ErrorHandler, with_error_handling
from core.database.repositories.knowledge_repository import KnowledgePointRepository
from core.database.connection import get_database_connection
from settings import settings


class KnowledgeManager:
    """知識點管理器 - 純數據庫版本 (V3.0)"""

    def __init__(self):
        self.logger = get_module_logger(__name__)
        self.settings = settings

        # TASK-30B: 純數據庫錯誤處理體系
        self._error_handler = ErrorHandler(mode="database")

        # 統一快取管理器
        self._cache_manager = UnifiedCacheManager(default_ttl=300)  # 5分鐘預設 TTL

        # 數據庫連接和 repository
        self._db_connection = None
        self._repository: Optional[KnowledgePointRepository] = None
        
        # 錯誤類型系統
        self.type_system = ErrorTypeSystem()

        # 初始化數據庫連接
        self._initialize_database()

    def _initialize_database(self) -> None:
        """初始化數據庫連接"""
        try:
            self._db_connection = get_database_connection()
            # 注意：這裡使用同步初始化，實際使用時需要異步初始化
            self.logger.info("數據庫知識管理器初始化完成")
        except Exception as e:
            self.logger.error(f"數據庫初始化失敗: {e}")
            raise DatabaseError(
                "知識管理器數據庫初始化失敗",
                operation="initialize",
                details={"error": str(e)}
            ) from e
            
    async def _ensure_repository(self) -> KnowledgePointRepository:
        """確保 repository 已初始化"""
        if not self._repository:
            if not self._db_connection:
                self._initialize_database()
            pool = await self._db_connection.connect()
            self._repository = KnowledgePointRepository(pool)
        return self._repository

    async def get_knowledge_points(self) -> list[KnowledgePoint]:
        """獲取所有知識點"""
        repository = await self._ensure_repository()
        return await repository.find_all(is_deleted=False)

    async def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        """根據ID獲取知識點"""
        try:
            target_id = int(point_id)
            repository = await self._ensure_repository()
            return await repository.find_by_id(target_id)
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid point_id: {point_id}")
            return None

    async def get_active_points(self) -> list[KnowledgePoint]:
        """獲取所有未刪除的知識點"""
        repository = await self._ensure_repository()
        return await repository.find_all(is_deleted=False)

    async def get_due_points(self) -> list[KnowledgePoint]:
        """獲取需要複習的知識點"""
        repository = await self._ensure_repository()
        now = datetime.now()
        all_points = await repository.find_all(is_deleted=False)
        
        due_points = []
        for p in all_points:
            if p.next_review:
                try:
                    review_date = datetime.fromisoformat(p.next_review)
                    # 確保兩個 datetime 都是 offset-naive
                    if review_date.tzinfo is not None:
                        review_date = review_date.replace(tzinfo=None)
                    if review_date <= now:
                        due_points.append(p)
                except (ValueError, TypeError):
                    # 如果解析失敗，跳過此點
                    continue
        return due_points

    async def add_knowledge_point_from_error(
        self, chinese_sentence: str, user_answer: str, error: dict, correct_answer: str
    ) -> int:
        """從錯誤信息創建知識點

        Args:
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            error: 錯誤分析數據
            correct_answer: 正確答案
            
        Returns:
            新創建的知識點 ID
        """
        repository = await self._ensure_repository()
        
        # 處理 category - 確保是枚舉類型
        category_str = error.get("category", "other")
        try:
            category = ErrorCategory(category_str) if isinstance(category_str, str) else category_str
        except ValueError:
            category = ErrorCategory.OTHER
            
        point = KnowledgePoint(
            id=0,  # Repository 會自動分配 ID
            key_point=error.get("key_point_summary", "未知錯誤"),
            original_phrase=error.get("original_phrase", user_answer),
            correction=error.get("correction", correct_answer),
            explanation=error.get("explanation", ""),
            category=category,
            subtype=error.get("subtype", "general"),
            mastery_level=0.1,
            mistake_count=1,
            correct_count=0,
            last_seen=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            original_error=OriginalError(
                chinese_sentence=chinese_sentence,
                user_answer=user_answer,
                correct_answer=correct_answer,
                timestamp=datetime.now().isoformat()
            )
        )
        
        created_point = await repository.create(point)
        self._invalidate_caches()
        
        return created_point.id

    async def edit_knowledge_point(self, point_id: int, updates: dict) -> Optional[dict]:
        """編輯知識點

        Args:
            point_id: 知識點ID
            updates: 要更新的欄位

        Returns:
            編輯歷史記錄，如果失敗返回 None
        """
        repository = await self._ensure_repository()
        point = await repository.find_by_id(point_id)
        
        if point and not point.is_deleted:
            # 執行編輯
            history = point.edit(updates)

            # 保存變更
            await repository.update(point)
            self._invalidate_caches()

            self.logger.info(f"編輯知識點 {point_id}: {list(updates.keys())}")
            return history

        self.logger.warning(f"找不到知識點 {point_id} 或已被刪除")
        return None

    async def delete_knowledge_point(self, point_id: int, reason: str = "") -> bool:
        """軟刪除知識點

        Args:
            point_id: 知識點ID
            reason: 刪除原因

        Returns:
            是否成功刪除
        """
        repository = await self._ensure_repository()
        point = await repository.find_by_id(point_id)
        
        if point and not point.is_deleted:
            # 執行軟刪除
            point.soft_delete(reason)

            # 保存變更
            await repository.update(point)
            self._invalidate_caches()

            self.logger.info(f"軟刪除知識點 {point_id}，原因: {reason}")
            return True

        self.logger.warning(f"找不到知識點 {point_id} 或已被刪除")
        return False

    async def restore_knowledge_point(self, point_id: int) -> bool:
        """復原軟刪除的知識點

        Args:
            point_id: 知識點ID

        Returns:
            是否成功復原
        """
        repository = await self._ensure_repository()
        point = await repository.find_by_id(point_id)
        
        if point and point.is_deleted:
            # 執行復原
            point.restore()

            # 保存變更
            await repository.update(point)
            self._invalidate_caches()

            self.logger.info(f"復原知識點 {point_id}")
            return True

        self.logger.warning(f"找不到已刪除的知識點 {point_id}")
        return False

    @with_error_handling(operation="get_statistics", mode="database")
    async def get_statistics(self) -> dict[str, Any]:
        """獲取統計資料（純數據庫版本）"""
        try:
            result = await self._cache_manager.get_or_compute_async(
                key=f"{CacheCategories.STATISTICS}:database",
                compute_func=self._compute_statistics,
                ttl=60,  # 統計快取1分鐘
            )
            return result
        except Exception as e:
            self.logger.error(f"統計數據獲取失敗: {e}")
            return self._get_safe_default_for_operation("get_statistics")

    async def _compute_statistics(self) -> dict[str, Any]:
        """計算統計資料（數據庫模式）"""
        from core.statistics_utils import UnifiedStatistics

        repository = await self._ensure_repository()
        knowledge_points = await repository.find_all(is_deleted=False)

        # TODO: 從數據庫獲取練習記錄，而不是從內存
        practice_records = []  # 這需要新的數據庫表來存儲

        # 使用統一邏輯計算統計
        stats = UnifiedStatistics.calculate_practice_statistics(
            knowledge_points=knowledge_points,
            practice_records=practice_records,
            include_original_errors=True,
        )

        self.logger.debug(
            f"數據庫統計計算完成: 練習{stats['total_practices']}, 正確{stats['correct_count']}, 知識點{stats['knowledge_points']}"
        )

        return stats

    def _invalidate_caches(self) -> None:
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

    def _get_safe_default_for_operation(self, operation: str) -> Any:
        """根據操作獲取安全的默認值"""
        defaults = {
            "get_statistics": {
                "total_practices": 0,
                "correct_count": 0,
                "knowledge_points": 0,
                "avg_mastery": 0.0,
                "category_distribution": {},
                "due_reviews": 0,
                "_database_error_fallback": True,
                "_operation": operation,
            },
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

        result = defaults.get(operation, None)
        if isinstance(result, dict):
            result = result.copy()
            result["_database_error_fallback"] = True
            result["_operation"] = operation

        return result