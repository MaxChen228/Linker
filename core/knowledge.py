"""
知識點管理模組 (V3.0 - 純資料庫架構)

此模組是應用程式中知識點管理的核心，負責處理所有與知識點相關的業務邏輯。
它作為服務層，封裝了底層的資料庫操作，並向上層提供一致的 API。

主要特點：
- **純資料庫架構**：已完全移除對 JSON 檔案的依賴，所有資料都儲存在資料庫中。
- **異步優先**：所有方法均為異步 (`async`)，以支援高併發和非阻塞操作。
- **倉儲模式 (Repository Pattern)**：透過 `KnowledgePointRepository` 與資料庫互動，實現了業務邏輯與資料存取的解耦。
- **快取機制**：整合 `UnifiedCacheManager`，對常用查詢進行快取，以提高效能。
- **錯誤處理**：整合了統一的錯誤處理和日誌記錄機制。
"""

import os
import sys
from datetime import datetime
from typing import Any, Optional

# 確保專案根目錄在 Python 路徑中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cache_manager import CacheCategories, UnifiedCacheManager
from core.database.connection import get_database_connection
from core.database.repositories.know_repo import KnowledgePointRepository
from core.error_handler import ErrorHandler, with_error_handling
from core.error_types import ErrorCategory, ErrorTypeSystem
from core.exceptions import DatabaseError
from core.log_config import get_module_logger
from core.models import KnowledgePoint, OriginalError
from scripts.settings import settings


class KnowledgeManager:
    """知識點管理器 - 純資料庫版本 (V3.0)"""

    def __init__(self):
        """初始化知識管理器。"""
        self.logger = get_module_logger(__name__)
        self.settings = settings
        self._error_handler = ErrorHandler(mode="database")
        self._cache_manager = UnifiedCacheManager(default_ttl=300)  # 5分鐘預設 TTL
        self._db_connection = None
        self._repository: Optional[KnowledgePointRepository] = None
        self.type_system = ErrorTypeSystem()
        self._initialize_database()

    def _initialize_database(self) -> None:
        """初始化資料庫連線管理器。"""
        try:
            self._db_connection = get_database_connection()
            self.logger.info("資料庫知識管理器初始化完成。")
        except Exception as e:
            self.logger.error(f"資料庫初始化失敗: {e}")
            raise DatabaseError(
                "知識管理器資料庫初始化失敗", operation="initialize", details={"error": str(e)}
            ) from e

    async def _ensure_repository(self) -> KnowledgePointRepository:
        """確保 `KnowledgePointRepository` 已被初始化。如果未初始化，則建立它。"""
        if self._repository is None:
            if self._db_connection is None:
                self._initialize_database()
            pool = await self._db_connection.connect()
            self._repository = KnowledgePointRepository(pool)
        return self._repository

    async def get_knowledge_points(self) -> list[KnowledgePoint]:
        """異步獲取所有未被刪除的知識點。"""
        repo = await self._ensure_repository()
        return await repo.find_all(is_deleted=False)

    async def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        """根據 ID 異步獲取單個知識點。"""
        try:
            repo = await self._ensure_repository()
            return await repo.find_by_id(int(point_id))
        except (ValueError, TypeError):
            self.logger.warning(f"無效的知識點 ID 格式: {point_id}")
            return None

    async def get_active_points(self) -> list[KnowledgePoint]:
        """異步獲取所有活躍（未刪除）的知識點。"""
        repo = await self._ensure_repository()
        return await repo.find_all(is_deleted=False)

    async def get_due_points(self) -> list[KnowledgePoint]:
        """異步獲取所有已到期需要複習的知識點。"""
        repo = await self._ensure_repository()
        all_points = await repo.find_all(is_deleted=False)
        now = datetime.now()
        due_points = []
        for p in all_points:
            if p.next_review:
                try:
                    review_date = datetime.fromisoformat(p.next_review).replace(tzinfo=None)
                    if review_date <= now:
                        due_points.append(p)
                except (ValueError, TypeError):
                    continue
        return due_points

    async def add_knowledge_point_from_error(
        self, chinese_sentence: str, user_answer: str, error: dict, correct_answer: str
    ) -> int:
        """
        從 AI 的錯誤分析結果中創建一個新的知識點。

        Args:
            chinese_sentence: 中文原句。
            user_answer: 使用者的答案。
            error: AI 分析的錯誤資訊字典。
            correct_answer: 建議的正確答案。

        Returns:
            新創建的知識點的 ID。
        """
        repo = await self._ensure_repository()
        category = ErrorCategory.from_string(error.get("category", "other"))
        point = KnowledgePoint(
            id=0,  # ID 由資料庫自動生成
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
                timestamp=datetime.now().isoformat(),
            ),
        )
        created_point = await repo.create(point)
        self._invalidate_caches()
        return created_point.id

    async def edit_knowledge_point(self, point_id: int, updates: dict) -> Optional[dict]:
        """
        異步編輯一個已有的知識點。

        Args:
            point_id: 要編輯的知識點 ID。
            updates: 一個包含要更新欄位和新值的字典。

        Returns:
            如果成功，返回一個包含變更歷史的字典；否則返回 None。
        """
        repo = await self._ensure_repository()
        point = await repo.find_by_id(point_id)
        if point and not point.is_deleted:
            history = point.edit(updates)
            await repo.update(point)
            self._invalidate_caches()
            self.logger.info(f"已編輯知識點 {point_id}: {list(updates.keys())}")
            return history
        self.logger.warning(f"嘗試編輯一個不存在或已刪除的知識點: ID={point_id}")
        return None

    async def delete_point(self, point_id: int, reason: str = "") -> bool:
        """
        異步軟刪除一個知識點。

        Args:
            point_id: 要刪除的知識點 ID。
            reason: 刪除原因。

        Returns:
            如果成功刪除，返回 True。
        """
        repo = await self._ensure_repository()
        point = await repo.find_by_id(point_id)
        if point and not point.is_deleted:
            point.soft_delete(reason)
            await repo.update(point)
            self._invalidate_caches()
            self.logger.info(f"已軟刪除知識點 {point_id}，原因: {reason}")
            return True
        self.logger.warning(f"嘗試刪除一個不存在或已被刪除的知識點: ID={point_id}")
        return False

    async def restore_point(self, point_id: int) -> bool:
        """
        異步恢復一個被軟刪除的知識點。

        Args:
            point_id: 要恢復的知識點 ID。

        Returns:
            如果成功恢復，返回 True。
        """
        repo = await self._ensure_repository()
        point = await repo.find_by_id(point_id)
        if point and point.is_deleted:
            point.restore()
            await repo.update(point)
            self._invalidate_caches()
            self.logger.info(f"已恢復知識點 {point_id}")
            return True
        self.logger.warning(f"嘗試恢復一個不存在或未被刪除的知識點: ID={point_id}")
        return False

    @with_error_handling(operation="get_statistics", mode="database")
    async def get_statistics(self) -> dict[str, Any]:
        """異步獲取全系統的統計資料，並進行快取。"""
        try:
            return await self._cache_manager.get_or_compute_async(
                key=f"{CacheCategories.STATISTICS}:database",
                compute_func=self._compute_statistics,
                ttl=60,  # 統計快取1分鐘
            )
        except Exception as e:
            self.logger.error(f"獲取統計資料失敗: {e}")
            return self._get_safe_default_for_operation("get_statistics")

    async def _compute_statistics(self) -> dict[str, Any]:
        """內部方法，從資料庫計算統計資料。"""
        from core.statistics_utils import UnifiedStatistics

        repo = await self._ensure_repository()
        knowledge_points = await repo.find_all(is_deleted=False)
        # TODO: 未來應從資料庫獲取獨立的練習記錄
        practice_records = []
        stats = UnifiedStatistics.calculate_practice_statistics(
            knowledge_points=knowledge_points,
            practice_records=practice_records,
            include_original_errors=True,
        )
        self.logger.debug(f"資料庫統計計算完成: {len(knowledge_points)} 個知識點")
        return stats

    def _invalidate_caches(self) -> None:
        """在資料變更後，清除所有相關的快取。"""
        categories_to_invalidate = [
            CacheCategories.STATISTICS,
            CacheCategories.REVIEW_CANDIDATES,
            CacheCategories.KNOWLEDGE_POINTS,
            CacheCategories.SEARCH_RESULTS,
        ]
        for category in categories_to_invalidate:
            self._cache_manager.invalidate(category)
        self.logger.debug(f"已清除快取: {categories_to_invalidate}")

    def _get_safe_default_for_operation(self, operation: str) -> Any:
        """在操作失敗時，提供一個安全的預設回傳值。"""
        defaults = {
            "get_statistics": {
                "total_practices": 0,
                "correct_count": 0,
                "knowledge_points": 0,
                "avg_mastery": 0.0,
                "due_reviews": 0,
            },
            "get_knowledge_points": [],
            "get_all_knowledge_points": [],
            "get_review_candidates": [],
            "search_knowledge_points": [],
            "get_knowledge_point": None,
            "add_knowledge_point": False,
            "edit_knowledge_point": None,
            "delete_point": False,
            "restore_point": None,
        }
        result = defaults.get(operation)
        if isinstance(result, dict):
            return {**result, "_database_error_fallback": True, "_operation": operation}
        return result
