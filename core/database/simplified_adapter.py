"""
簡化的資料庫適配器 - TASK-30D [已廢棄]
純資料庫實現，移除所有 JSON 相關邏輯
提供與原 KnowledgeManagerAdapter 相同的公開 API

⚠️ 警告：此類已廢棄 (TASK-31)
原因：同步方法中使用 asyncio.new_event_loop() 導致事件循環衝突
替代方案：使用 core.services.AsyncKnowledgeService
"""

import asyncio
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.cache_manager import UnifiedCacheManager
from core.database.database_manager import DatabaseKnowledgeManager, create_database_manager
from core.log_config import get_module_logger
from core.models import KnowledgePoint


class SimplifiedDatabaseAdapter:
    """簡化的資料庫適配器 [已廢棄]

    這是 TASK-30D 的核心實現，提供與原 KnowledgeManagerAdapter 相同的 API，
    但內部完全使用資料庫，移除所有 JSON 降級邏輯。

    ⚠️ 已廢棄：使用 core.services.AsyncKnowledgeService 替代
    問題：同步方法使用 asyncio.new_event_loop() 導致 FastAPI 事件循環衝突
    """

    def __init__(self, use_database: bool = True, data_dir: Optional[str] = None):
        """初始化適配器

        Args:
            use_database: 保留參數以維持 API 兼容性（始終使用資料庫）
            data_dir: 保留參數以維持 API 兼容性（不再使用）
        """
        # 發出廢棄警告
        warnings.warn(
            "SimplifiedDatabaseAdapter 已廢棄 (TASK-31)。"
            "請使用 core.services.AsyncKnowledgeService 替代。"
            "原因：同步方法中的 asyncio.new_event_loop() 導致事件循環衝突。",
            DeprecationWarning,
            stacklevel=2
        )

        self.logger = get_module_logger(__name__)
        self._db_manager: Optional[DatabaseKnowledgeManager] = None
        self._cache_manager = UnifiedCacheManager(default_ttl=300)
        self._initialized = False
        self._init_lock = asyncio.Lock()

        # 快取知識點列表（供同步 API 使用）
        self._knowledge_points_cache: list[KnowledgePoint] = []
        self._cache_dirty = True

        self.logger.warning("初始化簡化資料庫適配器 [已廢棄]")

    # ========== 初始化方法 ==========

    async def _ensure_initialized(self) -> None:
        """確保資料庫管理器已初始化"""
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            try:
                self._db_manager = await create_database_manager()
                self._initialized = True
                self.logger.info("資料庫管理器初始化成功")
            except Exception as e:
                self.logger.error(f"資料庫管理器初始化失敗: {e}")
                raise

    def _get_sync_manager(self) -> DatabaseKnowledgeManager:
        """獲取同步管理器（用於同步方法）"""
        if not self._db_manager:
            # 在同步上下文中創建管理器
            self._db_manager = DatabaseKnowledgeManager()
        return self._db_manager

    # ========== 異步 API ==========

    async def get_knowledge_points_async(self) -> list[KnowledgePoint]:
        """異步獲取所有知識點"""
        await self._ensure_initialized()
        return await self._db_manager.get_all_knowledge_points(include_deleted=False)

    async def get_knowledge_point_async(self, point_id: str) -> Optional[KnowledgePoint]:
        """異步獲取單個知識點"""
        await self._ensure_initialized()
        try:
            pid = int(point_id)
            return await self._db_manager.get_knowledge_point(pid)
        except (ValueError, TypeError):
            self.logger.error(f"無效的知識點 ID: {point_id}")
            return None

    async def add_knowledge_point_async(self, knowledge_point: KnowledgePoint) -> bool:
        """異步添加知識點"""
        await self._ensure_initialized()
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
        """異步更新知識點"""
        await self._ensure_initialized()
        try:
            point = await self._db_manager.get_knowledge_point(point_id)
            if not point:
                return False

            # 更新屬性
            for key, value in kwargs.items():
                if hasattr(point, key):
                    setattr(point, key, value)

            return await self._db_manager.update_knowledge_point(point)
        except Exception as e:
            self.logger.error(f"更新知識點失敗: {e}")
            return False

    async def delete_knowledge_point_async(self, point_id: int, reason: str = "") -> bool:
        """異步刪除知識點"""
        await self._ensure_initialized()
        return await self._db_manager.delete_knowledge_point(point_id, reason)

    async def restore_knowledge_point_async(self, point_id: int) -> bool:
        """異步恢復知識點"""
        await self._ensure_initialized()
        return await self._db_manager.restore_knowledge_point(point_id)

    async def get_review_candidates_async(self, max_points: int = 5) -> list[KnowledgePoint]:
        """異步獲取複習候選"""
        await self._ensure_initialized()
        return await self._db_manager.get_review_candidates(limit=max_points)

    async def add_review_success_async(
        self,
        point_id: int,
        chinese_sentence: str,
        user_answer: str,
        correct_answer: str,
        is_correct: bool = True,
    ) -> bool:
        """異步添加複習成功記錄"""
        await self._ensure_initialized()
        success = await self._db_manager.add_review_example(
            point_id, chinese_sentence, user_answer, correct_answer, is_correct
        )
        if success and is_correct:
            await self._db_manager.update_mastery(point_id, is_correct)
        return success

    async def get_statistics_async(self) -> dict[str, Any]:
        """異步獲取統計資料"""
        await self._ensure_initialized()
        return await self._db_manager.get_statistics()

    async def search_knowledge_points_async(self, keyword: str) -> list[KnowledgePoint]:
        """異步搜尋知識點"""
        await self._ensure_initialized()
        return await self._db_manager.search_knowledge_points(keyword)

    async def edit_knowledge_point_async(
        self, point_id: int, updates: dict = None, **kwargs
    ) -> Optional[dict]:
        """異步編輯知識點"""
        await self._ensure_initialized()
        all_updates = updates or {}
        all_updates.update(kwargs)
        return await self._db_manager.edit_knowledge_point(point_id, all_updates)

    async def get_active_points_async(self) -> list[KnowledgePoint]:
        """異步獲取活躍知識點"""
        await self._ensure_initialized()
        return await self._db_manager.get_all_knowledge_points(include_deleted=False)

    async def get_deleted_points_async(self) -> list[KnowledgePoint]:
        """異步獲取已刪除知識點"""
        await self._ensure_initialized()
        all_points = await self._db_manager.get_all_knowledge_points(include_deleted=True)
        return [p for p in all_points if p.is_deleted]

    async def get_learning_recommendations_async(self) -> dict[str, Any]:
        """異步獲取學習建議"""
        await self._ensure_initialized()

        # 獲取統計資料
        stats = await self._db_manager.get_statistics()

        # 獲取需要複習的知識點
        review_candidates = await self._db_manager.get_review_candidates(limit=10)

        # 獲取掌握度較低的知識點
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

    async def import_from_json_async(self, filepath: str) -> bool:
        """異步從 JSON 導入（用於資料遷移）"""
        await self._ensure_initialized()
        try:
            path = Path(filepath)
            if not path.exists():
                self.logger.error(f"檔案不存在: {filepath}")
                return False

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # 處理不同的 JSON 格式
            if isinstance(data, dict) and "data" in data:
                points_data = data["data"]
            elif isinstance(data, dict) and "knowledge_points" in data:
                points_data = data["knowledge_points"]
            elif isinstance(data, list):
                points_data = data
            else:
                self.logger.error("無法識別的 JSON 格式")
                return False

            # 導入每個知識點
            success_count = 0
            for point_data in points_data:
                try:
                    # 轉換為 KnowledgePoint
                    point = KnowledgePoint.from_dict(point_data)

                    # 添加到資料庫
                    result = await self._db_manager.add_knowledge_point(
                        error_info={
                            "error_pattern": point.key_point,
                            "category": point.category.value,
                            "subtype": point.subtype,
                            "error_phrase": point.original_phrase,
                            "correction": point.correction,
                        },
                        analysis={"explanation": point.explanation},
                        chinese_sentence=point.original_error.chinese_sentence,
                        user_answer=point.original_error.user_answer,
                        correct_answer=point.original_error.correct_answer,
                    )

                    if result:
                        success_count += 1
                except Exception as e:
                    self.logger.error(f"導入知識點失敗: {e}")
                    continue

            self.logger.info(f"成功導入 {success_count}/{len(points_data)} 個知識點")
            return success_count > 0

        except Exception as e:
            self.logger.error(f"導入 JSON 失敗: {e}")
            return False

    async def cleanup(self) -> None:
        """清理資源"""
        if self._db_manager:
            await self._db_manager.close()

    # ========== 同步 API（向後兼容）==========

    @property
    def knowledge_points(self) -> list[KnowledgePoint]:
        """獲取所有知識點（同步屬性）"""
        if self._cache_dirty:
            self._update_cache()
        return self._knowledge_points_cache

    def _update_cache(self) -> None:
        """更新快取（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._knowledge_points_cache = loop.run_until_complete(
                self.get_knowledge_points_async()
            )
            self._cache_dirty = False
        except Exception as e:
            self.logger.error(f"更新快取失敗: {e}")
            self._knowledge_points_cache = []

    def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        """獲取單個知識點（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_knowledge_point_async(point_id))
        except Exception as e:
            self.logger.error(f"獲取知識點失敗: {e}")
            return None

    def get_review_candidates(self, max_points: int = 5) -> list[KnowledgePoint]:
        """獲取複習候選（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_review_candidates_async(max_points))
        except Exception as e:
            self.logger.error(f"獲取複習候選失敗: {e}")
            return []

    def get_due_points(self) -> list[KnowledgePoint]:
        """獲取到期複習的知識點（同步）"""
        return self.get_review_candidates(max_points=20)

    def add_review_success(
        self,
        point_id: int,
        chinese_sentence: str,
        user_answer: str,
        correct_answer: str,
    ) -> None:
        """添加複習成功記錄（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.add_review_success_async(
                    point_id, chinese_sentence, user_answer, correct_answer, True
                )
            )
            self._cache_dirty = True
        except Exception as e:
            self.logger.error(f"添加複習成功記錄失敗: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """獲取統計資料（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_statistics_async())
        except Exception as e:
            self.logger.error(f"獲取統計資料失敗: {e}")
            return {}

    def search_knowledge_points(self, keyword: str) -> list[KnowledgePoint]:
        """搜尋知識點（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.search_knowledge_points_async(keyword))
        except Exception as e:
            self.logger.error(f"搜尋知識點失敗: {e}")
            return []

    def import_from_json(self, filepath: str) -> bool:
        """從 JSON 導入（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.import_from_json_async(filepath))
        except Exception as e:
            self.logger.error(f"導入 JSON 失敗: {e}")
            return False

    def export_to_json(self, filepath: str) -> None:
        """導出到 JSON（同步）"""
        try:
            points = self.knowledge_points

            # 構建導出資料
            export_data = {
                "version": "4.0",
                "exported_at": datetime.now().isoformat(),
                "total_points": len(points),
                "data": [p.to_dict() for p in points],
            }

            # 寫入檔案
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"成功導出 {len(points)} 個知識點到 {filepath}")

        except Exception as e:
            self.logger.error(f"導出 JSON 失敗: {e}")

    def get_active_points(self) -> list[KnowledgePoint]:
        """獲取活躍知識點（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_active_points_async())
        except Exception as e:
            self.logger.error(f"獲取活躍知識點失敗: {e}")
            return []

    def get_deleted_points(self) -> list[KnowledgePoint]:
        """獲取已刪除知識點（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_deleted_points_async())
        except Exception as e:
            self.logger.error(f"獲取已刪除知識點失敗: {e}")
            return []

    def get_points_by_category(self, category: str) -> list[KnowledgePoint]:
        """根據類別獲取知識點（同步）"""
        manager = self._get_sync_manager()
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                manager.get_knowledge_by_category(category)
            )
        except Exception as e:
            self.logger.error(f"根據類別獲取知識點失敗: {e}")
            return []

    def edit_knowledge_point(self, point_id: int, updates: dict = None, **kwargs) -> Optional[dict]:
        """編輯知識點（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.edit_knowledge_point_async(point_id, updates, **kwargs)
            )
            self._cache_dirty = True
            return result
        except Exception as e:
            self.logger.error(f"編輯知識點失敗: {e}")
            return None

    def delete_knowledge_point(self, point_id: int, reason: str = "") -> bool:
        """刪除知識點（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.delete_knowledge_point_async(point_id, reason)
            )
            self._cache_dirty = True
            return result
        except Exception as e:
            self.logger.error(f"刪除知識點失敗: {e}")
            return False

    def restore_knowledge_point(self, point_id: int) -> bool:
        """恢復知識點（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.restore_knowledge_point_async(point_id)
            )
            self._cache_dirty = True
            return result
        except Exception as e:
            self.logger.error(f"恢復知識點失敗: {e}")
            return False

    def add_knowledge_point_from_error(
        self,
        chinese_sentence: str,
        user_answer: str,
        error: dict,
        correct_answer: str,
    ) -> int:
        """從錯誤添加知識點（保持向後兼容的簽名）

        Args:
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            error: 錯誤分析數據（包含 key_point_summary, original_phrase, correction, explanation, category, subtype）
            correct_answer: 正確答案

        Returns:
            新創建的知識點ID
        """
        # 從 error dict 提取信息
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

        # 在同步方法中，我們需要在新的線程中運行異步操作
        import threading

        result_container = [None]
        exception_container = [None]

        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                manager = DatabaseKnowledgeManager()
                result = loop.run_until_complete(
                    manager.add_knowledge_point(
                        error_info, analysis, chinese_sentence, user_answer, correct_answer
                    )
                )
                result_container[0] = result
            except Exception as e:
                exception_container[0] = e

        thread = threading.Thread(target=run_async)
        thread.start()
        thread.join(timeout=10)  # 10秒超時

        if exception_container[0]:
            self.logger.error(f"從錯誤添加知識點失敗: {exception_container[0]}")
            return 0

        result = result_container[0]
        self._cache_dirty = True
        return result.id if result else 0

    async def _save_mistake_async(
        self,
        chinese_sentence: str,
        user_answer: str,
        feedback: dict[str, Any],
        practice_mode: str = "new",
    ) -> bool:
        """異步保存錯誤"""
        # 從 feedback 提取錯誤信息
        if not feedback.get("has_errors", False):
            return False

        # 提取第一個錯誤（如果有多個）
        errors = feedback.get("errors", [])
        if not errors:
            return False

        error = errors[0] if isinstance(errors, list) else errors

        # 確保已初始化
        await self._ensure_initialized()

        # 調用資料庫管理器
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

    def save_mistake(
        self,
        chinese_sentence: str,
        user_answer: str,
        feedback: dict[str, Any],
        practice_mode: str = "new",
    ) -> bool:
        """保存錯誤（保持向後兼容的簽名）

        Args:
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            feedback: AI 反饋數據（包含錯誤分析）
            practice_mode: 練習模式

        Returns:
            是否成功保存
        """
        # 從 feedback 提取錯誤信息
        if not feedback.get("has_errors", False):
            return False

        # 提取第一個錯誤（如果有多個）
        errors = feedback.get("errors", [])
        if not errors:
            return False

        error = errors[0] if isinstance(errors, list) else errors

        # 調用 add_knowledge_point_from_error
        result = self.add_knowledge_point_from_error(
            chinese_sentence=chinese_sentence,
            user_answer=user_answer,
            error=error,
            correct_answer=feedback.get("correct_answer", "")
        )
        return result > 0

    def get_all_mistakes(self) -> list[dict]:
        """獲取所有錯誤（同步）"""
        points = self.get_active_points()
        return [
            {
                "id": p.id,
                "error_pattern": p.key_point,
                "category": p.category.value,
                "explanation": p.explanation,
                "mastery_level": p.mastery_level,
                "mistake_count": p.mistake_count,
                "correct_count": p.correct_count,
            }
            for p in points
        ]

    def update_knowledge_point(self, point_id: int, **kwargs) -> bool:
        """更新知識點（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.update_knowledge_point_async(point_id, **kwargs)
            )
            self._cache_dirty = True
            return result
        except Exception as e:
            self.logger.error(f"更新知識點失敗: {e}")
            return False

    def get_learning_recommendations(self) -> dict[str, Any]:
        """獲取學習建議（同步）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.get_learning_recommendations_async())
        except Exception as e:
            self.logger.error(f"獲取學習建議失敗: {e}")
            return {}

    def permanent_delete_old_points(
        self, days_threshold: int = 30, min_mastery: float = 0.8
    ) -> tuple[int, list[str]]:
        """永久刪除舊知識點（同步）"""
        # 這個功能在純資料庫模式下暫不實現
        self.logger.warning("永久刪除功能暫未實現")
        return 0, []

    # ========== 輔助方法 ==========

    def _generate_recommendation(
        self,
        stats: dict,
        review_candidates: list[KnowledgePoint],
        struggling_points: list[KnowledgePoint],
    ) -> str:
        """生成學習建議"""
        recommendations = []

        # 基於統計資料的建議
        if stats.get("due_review", 0) > 10:
            recommendations.append(f"您有 {stats['due_review']} 個知識點需要複習")

        if stats.get("avg_mastery", 0) < 0.5:
            recommendations.append("整體掌握度偏低，建議增加練習頻率")

        # 基於複習候選的建議
        if review_candidates:
            categories = {}
            for point in review_candidates:
                cat = point.category.value
                categories[cat] = categories.get(cat, 0) + 1

            most_common = max(categories, key=categories.get)
            recommendations.append(f"近期需要重點複習 {most_common} 類型的錯誤")

        # 基於掙扎知識點的建議
        if len(struggling_points) > 5:
            recommendations.append(f"有 {len(struggling_points)} 個知識點掌握度較低，需要重點關注")

        return " | ".join(recommendations) if recommendations else "保持當前學習節奏"


# 工廠函數
async def get_knowledge_manager_async(use_database: bool = True) -> SimplifiedDatabaseAdapter:
    """異步獲取知識管理器"""
    adapter = SimplifiedDatabaseAdapter(use_database=use_database)
    await adapter._ensure_initialized()
    return adapter


# 向後兼容別名
KnowledgeManagerAdapter = SimplifiedDatabaseAdapter
