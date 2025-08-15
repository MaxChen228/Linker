"""
純異步知識點服務 - TASK-31
替代 SimplifiedDatabaseAdapter，提供純異步 API
"""

from typing import Any, Optional
from datetime import datetime

from core.services.base import BaseAsyncService
from core.database.database_manager import DatabaseKnowledgeManager, create_database_manager
from core.cache_manager import UnifiedCacheManager
from core.models import KnowledgePoint, OriginalError
from core.error_types import ErrorCategory


class AsyncKnowledgeService(BaseAsyncService):
    """純異步知識點服務
    
    直接使用 DatabaseKnowledgeManager，無需同步包裝
    提供與 SimplifiedDatabaseAdapter 相同的 API 介面
    """
    
    def __init__(self):
        """初始化服務"""
        super().__init__("knowledge")
        self._db_manager: Optional[DatabaseKnowledgeManager] = None
        self._cache_manager = UnifiedCacheManager(default_ttl=300)
    
    async def _initialize_resources(self) -> None:
        """初始化資料庫連線"""
        self._db_manager = await create_database_manager()
        self.logger.info("異步知識服務資源初始化完成")
    
    async def _cleanup_resources(self) -> None:
        """清理資料庫連線"""
        if self._db_manager:
            await self._db_manager.close()
            self._db_manager = None
    
    # ========== 核心 CRUD 操作 ==========
    
    async def get_knowledge_points_async(self) -> list[KnowledgePoint]:
        """獲取所有知識點"""
        await self.initialize()
        return await self._db_manager.get_all_knowledge_points(include_deleted=False)
    
    async def get_knowledge_point_async(self, point_id: str) -> Optional[KnowledgePoint]:
        """獲取單個知識點"""
        await self.initialize()
        try:
            pid = int(point_id)
            return await self._db_manager.get_knowledge_point(pid)
        except (ValueError, TypeError):
            self.logger.error(f"無效的知識點 ID: {point_id}")
            return None
    
    async def add_knowledge_point_async(self, knowledge_point: KnowledgePoint) -> bool:
        """添加知識點"""
        await self.initialize()
        try:
            result = await self._db_manager.add_knowledge_point(
                error_info={
                    "error_pattern": knowledge_point.key_point,
                    "category": knowledge_point.category.value,
                    "subtype": knowledge_point.subtype,
                    "error_phrase": knowledge_point.original_phrase,
                    "correction": knowledge_point.correction,
                },
                analysis={"explanation": knowledge_point.explanation},
                chinese_sentence=knowledge_point.original_error.chinese_sentence,
                user_answer=knowledge_point.original_error.user_answer,
                correct_answer=knowledge_point.original_error.correct_answer,
            )
            return result is not None
        except Exception as e:
            self.logger.error(f"添加知識點失敗: {e}")
            return False
    
    async def update_knowledge_point_async(self, point_id: int, **kwargs) -> bool:
        """更新知識點"""
        await self.initialize()
        try:
            point = await self._db_manager.get_knowledge_point(point_id)
            if not point:
                return False
            
            for key, value in kwargs.items():
                if hasattr(point, key):
                    setattr(point, key, value)
            
            return await self._db_manager.update_knowledge_point(point)
        except Exception as e:
            self.logger.error(f"更新知識點失敗: {e}")
            return False
    
    async def delete_knowledge_point_async(self, point_id: int, reason: str = "") -> bool:
        """刪除知識點"""
        await self.initialize()
        return await self._db_manager.delete_knowledge_point(point_id, reason)
    
    async def restore_knowledge_point_async(self, point_id: int) -> bool:
        """恢復知識點"""
        await self.initialize()
        return await self._db_manager.restore_knowledge_point(point_id)
    
    # ========== 查詢操作 ==========
    
    async def get_review_candidates_async(self, max_points: int = 5) -> list[KnowledgePoint]:
        """獲取複習候選"""
        await self.initialize()
        return await self._db_manager.get_review_candidates(limit=max_points)
    
    async def search_knowledge_points_async(self, keyword: str) -> list[KnowledgePoint]:
        """搜尋知識點"""
        await self.initialize()
        return await self._db_manager.search_knowledge_points(keyword)
    
    async def get_active_points_async(self) -> list[KnowledgePoint]:
        """獲取活躍知識點"""
        await self.initialize()
        return await self._db_manager.get_all_knowledge_points(include_deleted=False)
    
    async def get_deleted_points_async(self) -> list[KnowledgePoint]:
        """獲取已刪除知識點"""
        await self.initialize()
        all_points = await self._db_manager.get_all_knowledge_points(include_deleted=True)
        return [p for p in all_points if p.is_deleted]
    
    # ========== 學習記錄操作 ==========
    
    async def add_review_success_async(
        self,
        knowledge_point_id: int = None,
        point_id: int = None,
        chinese_sentence: str = "",
        user_answer: str = "",
        correct_answer: str = "",
        is_correct: bool = True,
    ) -> bool:
        """添加複習成功記錄
        
        支援兩種參數名以保持向後相容：
        - knowledge_point_id: practice.py 使用的參數名
        - point_id: 內部使用的參數名
        """
        await self.initialize()
        
        # 支援兩種參數名
        pid = knowledge_point_id if knowledge_point_id is not None else point_id
        if pid is None:
            self.logger.error("未提供知識點 ID")
            return False
            
        success = await self._db_manager.add_review_example(
            pid, chinese_sentence, user_answer, correct_answer, is_correct
        )
        if success and is_correct:
            await self._db_manager.update_mastery(pid, is_correct)
        return success
    
    async def update_knowledge_point(self, point_id: int, is_correct: bool) -> bool:
        """更新知識點掌握度（用於複習模式）"""
        await self.initialize()
        return await self._db_manager.update_mastery(point_id, is_correct)
    
    # ========== 統計操作 ==========
    
    async def get_statistics_async(self) -> dict[str, Any]:
        """獲取統計資料"""
        await self.initialize()
        return await self._db_manager.get_statistics()
    
    async def get_learning_recommendations_async(self) -> dict[str, Any]:
        """獲取學習建議"""
        await self.initialize()
        
        stats = await self._db_manager.get_statistics()
        review_candidates = await self._db_manager.get_review_candidates(limit=10)
        all_points = await self._db_manager.get_all_knowledge_points()
        struggling_points = [p for p in all_points if p.mastery_level < 0.3]
        
        return {
            "statistics": stats,
            "review_candidates": [
                {
                    "id": p.id,
                    "key_point": p.key_point,
                    "mastery_level": p.mastery_level,
                    "last_seen": p.last_seen,
                }
                for p in review_candidates[:5]
            ],
            "focus_areas": [
                {
                    "id": p.id,
                    "key_point": p.key_point,
                    "mastery_level": p.mastery_level,
                    "mistake_count": p.mistake_count,
                }
                for p in struggling_points[:5]
            ],
            "recommendation": self._generate_recommendation(stats, review_candidates, struggling_points),
        }
    
    # ========== 編輯操作 ==========
    
    async def edit_knowledge_point_async(
        self, point_id: int, updates: dict = None, **kwargs
    ) -> Optional[dict]:
        """編輯知識點"""
        await self.initialize()
        all_updates = updates or {}
        all_updates.update(kwargs)
        return await self._db_manager.edit_knowledge_point(point_id, all_updates)
    
    # ========== 保存錯誤（從練習中）==========
    
    async def _save_mistake_async(
        self,
        chinese_sentence: str,
        user_answer: str,
        feedback: dict[str, Any],
        practice_mode: str = "new",
    ) -> bool:
        """保存錯誤記錄"""
        if not feedback.get("has_errors", False):
            return False
        
        errors = feedback.get("errors", [])
        if not errors:
            return False
        
        error = errors[0] if isinstance(errors, list) else errors
        
        await self.initialize()
        
        result = await self._db_manager.add_knowledge_point(
            error_info={
                "error_pattern": error.get("key_point_summary", "未知錯誤"),
                "error_phrase": error.get("original_phrase", user_answer),
                "correction": error.get("correction", feedback.get("correct_answer", "")),
                "category": error.get("category", "other"),
                "subtype": error.get("subtype", "general"),
            },
            analysis={"explanation": error.get("explanation", "")},
            chinese_sentence=chinese_sentence,
            user_answer=user_answer,
            correct_answer=feedback.get("correct_answer", "")
        )
        return result is not None
    
    async def add_knowledge_point_from_error(
        self,
        chinese_sentence: str,
        user_answer: str,
        error: dict,
        correct_answer: str,
    ) -> int:
        """從錯誤添加知識點"""
        await self.initialize()
        
        error_info = {
            "error_pattern": error.get("key_point_summary", "未知錯誤"),
            "error_phrase": error.get("original_phrase", user_answer),
            "correction": error.get("correction", correct_answer),
            "category": error.get("category", "other"),
            "subtype": error.get("subtype", "general"),
        }
        analysis = {
            "explanation": error.get("explanation", "")
        }
        
        result = await self._db_manager.add_knowledge_point(
            error_info, analysis, chinese_sentence, user_answer, correct_answer
        )
        
        return result.id if result else 0
    
    # ========== 複習候選（相容介面）==========
    
    async def get_review_candidates(self, max_points: int = 5) -> list[KnowledgePoint]:
        """獲取複習候選（相容介面）"""
        return await self.get_review_candidates_async(max_points)
    
    # ========== 輔助方法 ==========
    
    def _generate_recommendation(
        self,
        stats: dict,
        review_candidates: list[KnowledgePoint],
        struggling_points: list[KnowledgePoint],
    ) -> str:
        """生成學習建議"""
        recommendations = []
        
        if stats.get("due_review", 0) > 10:
            recommendations.append(f"您有 {stats['due_review']} 個知識點需要複習")
        
        if stats.get("avg_mastery", 0) < 0.5:
            recommendations.append("整體掌握度偏低，建議增加練習頻率")
        
        if review_candidates:
            categories = {}
            for point in review_candidates:
                cat = point.category.value
                categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                most_common = max(categories, key=categories.get)
                recommendations.append(f"近期需要重點複習 {most_common} 類型的錯誤")
        
        if len(struggling_points) > 5:
            recommendations.append(f"有 {len(struggling_points)} 個知識點掌握度較低，需要重點關注")
        
        return " | ".join(recommendations) if recommendations else "保持當前學習節奏"