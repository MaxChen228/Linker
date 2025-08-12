"""
知識點服務層
負責統一處理知識點相關的業務邏輯，包括錯誤保存、知識點管理、複習佇列等
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_service import BaseService, ServiceResult
from core.knowledge import KnowledgeManager
from core.repositories import KnowledgeRepository


@dataclass
class SaveMistakeRequest:
    """保存錯誤請求"""
    chinese_sentence: str
    user_answer: str
    feedback: Dict[str, Any]
    practice_mode: str = "new"
    target_point_ids: Optional[List[str]] = None


class KnowledgeService(BaseService):
    """
    知識點服務
    
    統一的知識點業務邏輯處理，包含：
    - 錯誤記錄保存和處理
    - 知識點資訊獲取
    - 掌握度更新管理
    - 複習佇列管理
    - 知識點統計分析
    """
    
    def __init__(
        self,
        knowledge_manager: KnowledgeManager,
        knowledge_repository: KnowledgeRepository,
        error_processing_service=None,  # 預留依賴
        practice_record_service=None    # 預留依賴
    ):
        """
        初始化知識點服務
        
        Args:
            knowledge_manager: 知識點管理器
            knowledge_repository: 知識點數據存取層
            error_processing_service: 錯誤處理服務（預留）
            practice_record_service: 練習記錄服務（預留）
        """
        super().__init__()
        self.knowledge_manager = knowledge_manager
        self.knowledge_repo = knowledge_repository
        self.error_processing_service = error_processing_service
        self.practice_record_service = practice_record_service
        
        # 服務統計
        self._operation_stats = {
            "mistakes_saved": 0,
            "knowledge_points_created": 0,
            "mastery_updates": 0,
            "review_requests": 0,
            "last_operation": None
        }
    
    async def _setup_dependencies(self):
        """設置依賴項"""
        # 預留給未來的依賴注入
        if self.error_processing_service is None:
            self.logger.info("錯誤處理服務未提供，使用內建邏輯")
        
        if self.practice_record_service is None:
            self.logger.info("練習記錄服務未提供，使用知識管理器內建功能")
    
    def save_mistake(self, request: SaveMistakeRequest) -> ServiceResult[Dict[str, Any]]:
        """
        保存錯誤記錄並處理相關知識點
        
        主協調方法，負責整個錯誤處理流程的編排
        
        Args:
            request: 保存錯誤請求
            
        Returns:
            ServiceResult: 包含處理結果的服務結果
        """
        return self._execute_with_error_handling(
            "save_mistake",
            self._save_mistake_impl,
            request=request
        )
    
    def _save_mistake_impl(self, request: SaveMistakeRequest) -> ServiceResult[Dict[str, Any]]:
        """保存錯誤的實際實現"""
        start_time = time.time()
        
        # 1. 驗證輸入
        validation_result = self._validate_mistake_request(request)
        if not validation_result.success:
            return validation_result
        
        # 2. 記錄練習並處理錯誤
        practice_record = self._record_practice(request)
        is_correct = request.feedback.get("is_generally_correct", False)
        knowledge_points_created = [] if is_correct else self._process_errors(request)
        
        # 3. 處理複習模式的掌握度更新
        if request.practice_mode == "review" and is_correct and request.target_point_ids:
            self._update_review_mastery(request.target_point_ids, is_correct, request)
        
        # 4. 更新統計和記錄日誌
        self._update_operation_stats("mistakes_saved", len(knowledge_points_created))
        self._log_save_mistake_operation(start_time, is_correct, request.practice_mode, knowledge_points_created)
        
        return ServiceResult.success(
            data=self._create_save_mistake_response(is_correct, request.practice_mode, knowledge_points_created, practice_record),
            message="錯誤記錄保存完成"
        )
    
    def get_knowledge_points(
        self, 
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> ServiceResult[List[Dict[str, Any]]]:
        """獲取知識點列表"""
        return self._execute_with_error_handling(
            "get_knowledge_points",
            self._get_knowledge_points_impl,
            category=category,
            limit=limit
        )
    
    def _get_knowledge_points_impl(
        self, 
        category: Optional[str], 
        limit: Optional[int]
    ) -> ServiceResult[List[Dict[str, Any]]]:
        """獲取知識點列表的實際實現"""
        points = self.knowledge_manager.knowledge_points.copy()
        
        # 按類別篩選
        if category:
            category_filter_result = self._filter_points_by_category(points, category)
            if not category_filter_result.success:
                return category_filter_result
            points = category_filter_result.data
        
        # 限制數量並格式化
        if limit and limit > 0:
            points = points[:limit]
        points_data = [self._format_knowledge_point(point) for point in points]
        
        return ServiceResult.success(
            data=points_data,
            message=f"獲取 {len(points_data)} 個知識點"
        )
    
    def get_knowledge_point_by_id(self, point_id: str) -> ServiceResult[Dict[str, Any]]:
        """
        根據ID獲取知識點詳情
        
        Args:
            point_id: 知識點ID
            
        Returns:
            ServiceResult: 包含知識點詳情的服務結果
        """
        return self._execute_with_error_handling(
            "get_knowledge_point_by_id",
            self._get_knowledge_point_by_id_impl,
            point_id=point_id
        )
    
    def _get_knowledge_point_by_id_impl(self, point_id: str) -> ServiceResult[Dict[str, Any]]:
        """根據ID獲取知識點的實際實現"""
        point = self.knowledge_manager.get_knowledge_point(point_id)
        if not point:
            return ServiceResult.error(
                message=f"找不到ID為 {point_id} 的知識點",
                error_type="NotFoundError",
                error_code="KNOWLEDGE_POINT_NOT_FOUND"
            )
        
        point_data = self._format_knowledge_point(point)
        return ServiceResult.success(
            data=point_data,
            message="知識點詳情獲取成功"
        )
    
    def update_mastery(
        self, 
        point_id: str, 
        is_correct: bool,
        review_context: Optional[Dict[str, Any]] = None
    ) -> ServiceResult[Dict[str, Any]]:
        """更新知識點掌握度"""
        return self._execute_with_error_handling(
            "update_mastery",
            self._update_mastery_impl,
            point_id=point_id,
            is_correct=is_correct,
            review_context=review_context
        )
    
    def _update_mastery_impl(
        self, 
        point_id: str, 
        is_correct: bool,
        review_context: Optional[Dict[str, Any]]
    ) -> ServiceResult[Dict[str, Any]]:
        """更新掌握度的實際實現"""
        success = self.knowledge_manager.update_knowledge_point(int(point_id), is_correct)
        
        if not success:
            return ServiceResult.error(
                message=f"更新知識點 {point_id} 掌握度失敗",
                error_type="UpdateError",
                error_code="MASTERY_UPDATE_FAILED"
            )
        
        # 更新統計並獲取新的掌握度
        self._update_operation_stats("mastery_updates")
        point = self.knowledge_manager.get_knowledge_point(point_id)
        
        return ServiceResult.success(
            data=self._create_mastery_update_response(point_id, is_correct, point, review_context),
            message="掌握度更新成功"
        )
    
    def get_review_queue(self, max_points: int = 5) -> ServiceResult[List[Dict[str, Any]]]:
        """
        獲取待複習知識點佇列
        
        Args:
            max_points: 最大返回數量
            
        Returns:
            ServiceResult: 包含複習佇列的服務結果
        """
        return self._execute_with_error_handling(
            "get_review_queue",
            self._get_review_queue_impl,
            max_points=max_points
        )
    
    def _get_review_queue_impl(self, max_points: int) -> ServiceResult[List[Dict[str, Any]]]:
        """獲取複習佇列的實際實現"""
        candidates = self.knowledge_manager.get_review_candidates(max_points=max_points)
        
        # 更新統計
        self._operation_stats["review_requests"] += 1
        self._operation_stats["last_operation"] = datetime.now().isoformat()
        
        # 格式化複習候選點
        review_data = []
        for point in candidates:
            review_data.append({
                **self._format_knowledge_point(point),
                "priority_score": self._calculate_review_priority(point),
                "is_due": point.next_review <= datetime.now().isoformat() if point.next_review else False
            })
        
        return ServiceResult.success(
            data=review_data,
            message=f"獲取 {len(review_data)} 個待複習知識點"
        )
    
    def get_knowledge_statistics(self) -> ServiceResult[Dict[str, Any]]:
        """
        獲取知識點統計資訊
        
        Returns:
            ServiceResult: 包含統計資訊的服務結果
        """
        return self._execute_with_error_handling(
            "get_knowledge_statistics",
            self._get_knowledge_statistics_impl
        )
    
    def _get_knowledge_statistics_impl(self) -> ServiceResult[Dict[str, Any]]:
        """獲取統計資訊的實際實現"""
        # 從知識管理器獲取基本統計
        basic_stats = self.knowledge_manager.get_statistics()
        
        # 添加服務層統計
        stats_data = {
            **basic_stats,
            "service_stats": self._operation_stats.copy(),
            "repository_stats": self._get_repository_statistics()
        }
        
        return ServiceResult.success(
            data=stats_data,
            message="統計資訊獲取成功"
        )
    
    # === 私有輔助方法 ===
    
    def _validate_mistake_request(self, request: SaveMistakeRequest) -> ServiceResult[bool]:
        """驗證錯誤保存請求"""
        if not request.chinese_sentence.strip():
            return ServiceResult.error(
                message="中文句子不能為空",
                error_type="ValidationError",
                error_code="EMPTY_CHINESE_SENTENCE"
            )
        
        if not request.user_answer.strip():
            return ServiceResult.error(
                message="用戶答案不能為空",
                error_type="ValidationError",
                error_code="EMPTY_USER_ANSWER"
            )
        
        if not isinstance(request.feedback, dict):
            return ServiceResult.error(
                message="回饋資料格式錯誤",
                error_type="ValidationError",
                error_code="INVALID_FEEDBACK_FORMAT"
            )
        
        return ServiceResult.success(data=True, message="驗證通過")
    
    def _record_practice(self, request: SaveMistakeRequest) -> Dict[str, Any]:
        """記錄練習（調用 PracticeRecordService 或使用內建功能）"""
        if self.practice_record_service:
            # 如果有練習記錄服務，使用服務
            return self.practice_record_service.record_practice(request)
        else:
            # 使用內建功能
            return {
                "timestamp": datetime.now().isoformat(),
                "chinese_sentence": request.chinese_sentence,
                "user_answer": request.user_answer,
                "practice_mode": request.practice_mode,
                "is_correct": request.feedback.get("is_generally_correct", False)
            }
    
    def _process_errors(self, request: SaveMistakeRequest) -> List[Dict[str, Any]]:
        """處理錯誤並創建知識點"""
        if self.error_processing_service:
            # 如果有錯誤處理服務，使用服務
            return self.error_processing_service.process_errors(request)
        else:
            # 使用知識管理器的內建功能
            try:
                self.knowledge_manager.save_mistake(
                    chinese_sentence=request.chinese_sentence,
                    user_answer=request.user_answer,
                    feedback=request.feedback,
                    practice_mode=request.practice_mode
                )
                
                # 提取新創建的知識點資訊
                errors = request.feedback.get("error_analysis", [])
                return [{"key_point": error.get("key_point_summary", "")} for error in errors]
            except Exception as e:
                self.logger.error(f"處理錯誤失敗: {str(e)}")
                return []
    
    def _update_review_mastery(
        self, 
        target_point_ids: List[str], 
        is_correct: bool,
        request: SaveMistakeRequest
    ):
        """更新複習模式下的掌握度"""
        for point_id in target_point_ids:
            try:
                if is_correct:
                    self.knowledge_manager.add_review_success(
                        knowledge_point_id=int(point_id),
                        chinese_sentence=request.chinese_sentence,
                        user_answer=request.user_answer
                    )
                else:
                    self.knowledge_manager.update_knowledge_point(int(point_id), False)
                
                self._operation_stats["mastery_updates"] += 1
            except Exception as e:
                self.logger.error(f"更新複習掌握度失敗 {point_id}: {str(e)}")
    
    def _format_knowledge_point(self, point) -> Dict[str, Any]:
        """格式化知識點為字典"""
        return {
            "id": point.id,
            "key_point": point.key_point,
            "category": point.category.value,
            "category_chinese": point.category.to_chinese(),
            "subtype": point.subtype,
            "explanation": point.explanation,
            "original_phrase": point.original_phrase,
            "correction": point.correction,
            "mastery_level": point.mastery_level,
            "mistake_count": point.mistake_count,
            "correct_count": point.correct_count,
            "created_at": point.created_at,
            "last_seen": point.last_seen,
            "next_review": point.next_review,
            "examples_count": len(point.review_examples) + (1 if point.original_error else 0)
        }
    
    def _calculate_review_priority(self, point) -> float:
        """計算複習優先級分數"""
        mastery_factor = 1.0 - point.mastery_level
        mistake_factor = min(point.mistake_count / 10, 1.0)
        time_factor = 1.0
        
        if point.next_review and point.next_review <= datetime.now().isoformat():
            time_factor = 1.5
        
        return (mastery_factor * 0.4 + mistake_factor * 0.3) * time_factor
    
    def _get_repository_statistics(self) -> Dict[str, Any]:
        """獲取資料庫層統計資訊"""
        try:
            return self.knowledge_repo.get_statistics()
        except Exception as e:
            self.logger.warning(f"獲取資料庫統計失敗: {str(e)}")
            return {}
    
    def _filter_points_by_category(self, points, category: str) -> ServiceResult[List]:
        """按類別篩選知識點"""
        from core.error_types import ErrorCategory
        try:
            target_category = ErrorCategory.from_string(category)
            filtered_points = [p for p in points if p.category == target_category]
            return ServiceResult.success(data=filtered_points)
        except (ValueError, KeyError):
            return ServiceResult.error(
                message=f"無效的錯誤類別: {category}",
                error_type="ValidationError",
                error_code="INVALID_CATEGORY"
            )
    
    def _update_operation_stats(self, operation_type: str, count: int = 1):
        """更新操作統計"""
        if operation_type == "mistakes_saved":
            self._operation_stats["mistakes_saved"] += 1
            self._operation_stats["knowledge_points_created"] += count
        elif operation_type == "mastery_updates":
            self._operation_stats["mastery_updates"] += 1
        self._operation_stats["last_operation"] = datetime.now().isoformat()
    
    def _log_save_mistake_operation(self, start_time: float, is_correct: bool, practice_mode: str, knowledge_points: List):
        """記錄保存錯誤操作的日誌"""
        duration_ms = int((time.time() - start_time) * 1000)
        self.log_operation(
            operation="save_mistake",
            success=True,
            duration_ms=duration_ms,
            is_correct=is_correct,
            practice_mode=practice_mode,
            knowledge_points_created=len(knowledge_points)
        )
    
    def _create_save_mistake_response(self, is_correct: bool, practice_mode: str, knowledge_points: List, practice_record: Dict) -> Dict[str, Any]:
        """創建保存錯誤的響應數據"""
        return {
            "is_correct": is_correct,
            "practice_mode": practice_mode,
            "knowledge_points_created": knowledge_points,
            "practice_record": practice_record
        }
    
    def _create_mastery_update_response(self, point_id: str, is_correct: bool, point, review_context: Optional[Dict]) -> Dict[str, Any]:
        """創建掌握度更新的響應數據"""
        return {
            "point_id": point_id,
            "is_correct": is_correct,
            "new_mastery_level": point.mastery_level if point else 0.0,
            "review_context": review_context
        }
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        return {
            "service_name": "KnowledgeService",
            "version": "1.0.0",
            "description": "知識點管理服務",
            "capabilities": [
                "錯誤記錄保存",
                "知識點資訊獲取",
                "掌握度更新管理",
                "複習佇列管理",
                "知識點統計分析"
            ],
            "statistics": self._operation_stats.copy(),
            "dependencies": {
                "knowledge_manager": self.knowledge_manager.__class__.__name__,
                "knowledge_repository": self.knowledge_repo.__class__.__name__,
                "error_processing_service": (
                    self.error_processing_service.__class__.__name__ 
                    if self.error_processing_service else "None"
                ),
                "practice_record_service": (
                    self.practice_record_service.__class__.__name__ 
                    if self.practice_record_service else "None"
                )
            },
            "initialized": self._initialized
        }