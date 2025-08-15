"""
純資料庫知識點管理器 - TASK-30D
替代原有的 DatabaseAdapter，移除所有 JSON 降級邏輯
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

from core.cache_manager import CacheCategories, UnifiedCacheManager
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
                
                # 清除相關快取
                # TODO: 實現 clear_category 方法
                
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
                filters = {} if include_deleted else {"is_deleted": False}
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
                # TODO: 實現 clear_category 方法
                
                return True
        except Exception as e:
            self.logger.error(f"更新知識點失敗: {e}")
            return False
    
    async def delete_knowledge_point(self, point_id: int, reason: str = "") -> bool:
        """軟刪除知識點"""
        try:
            async with self._db_operation("刪除知識點") as repo:
                result = await repo.delete(point_id, reason)
                
                # 清除相關快取
                # TODO: 實現 clear_category 方法
                
                return result
        except Exception as e:
            self.logger.error(f"刪除知識點失敗: {e}")
            return False
    
    async def restore_knowledge_point(self, point_id: int) -> bool:
        """恢復已刪除的知識點"""
        try:
            async with self._db_operation("恢復知識點") as repo:
                result = await repo.restore(point_id)
                
                # 清除相關快取
                # TODO: 實現 clear_category 方法
                
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
                self._cache_manager.delete(cache_key)
                
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
        """同步獲取活躍知識點（相容舊 API）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_all_knowledge_points(include_deleted=False))
        except Exception as e:
            self.logger.error(f"同步獲取活躍知識點失敗: {e}")
            return []
    
    # ========== 資源管理 ==========
    
    async def close(self):
        """關閉資料庫連線"""
        if self._db_connection:
            await self._db_connection.disconnect()
            self.logger.info("資料庫連線已關閉")
    
    def __del__(self):
        """清理資源"""
        if hasattr(self, "_db_connection") and self._db_connection:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except:
                pass


# 工廠函數，供外部使用
async def create_database_manager() -> DatabaseKnowledgeManager:
    """創建並初始化資料庫管理器"""
    manager = DatabaseKnowledgeManager()
    await manager._ensure_initialized()
    return manager