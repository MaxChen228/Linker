"""
練習服務層
統一處理練習相關的業務邏輯，包括翻譯提交、題目生成、複習模式等
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseService, ServiceResult
from core.ai_service import AIService
from core.knowledge import KnowledgeManager
from core.validators import ValidationService
# 使用 ValidationRules 和其他現有常數
from core.repositories import KnowledgeRepository, PracticeRepository
from core.config_manager import get_config
from core.constants import PracticeConfig


class PracticeService(BaseService):
    """
    練習服務
    
    統一的練習業務邏輯處理，包含：
    - 翻譯提交和批改
    - 練習題目生成
    - 複習模式處理
    - 練習統計獲取
    """
    
    def __init__(
        self,
        ai_service: AIService,
        knowledge_manager: KnowledgeManager,
        knowledge_repository: KnowledgeRepository | None = None,
        practice_repository: PracticeRepository | None = None
    ):
        """
        初始化練習服務
        
        Args:
            ai_service: AI 服務實例
            knowledge_manager: 知識點管理器
            knowledge_repository: 知識點數據存取層
            practice_repository: 練習記錄數據存取層
        """
        super().__init__()
        self.ai_service = ai_service
        self.knowledge_manager = knowledge_manager
        self.knowledge_repo = knowledge_repository
        self.practice_repo = practice_repository
        
        # 服務統計
        self._operation_stats = {
            "submissions_processed": 0,
            "questions_generated": 0,
            "review_sessions": 0,
            "last_operation": None
        }
    
    async def _setup_dependencies(self):
        """設置依賴項"""
        # 如果沒有提供 repository，使用預設實現
        if self.knowledge_repo is None:
            from core.repositories import KnowledgeRepository
            self.knowledge_repo = KnowledgeRepository()
        
        if self.practice_repo is None:
            from core.repositories import PracticeRepository
            self.practice_repo = PracticeRepository()
    
    def submit_translation(
        self,
        chinese: str,
        english: str,
        mode: str = "new",
        level: int = 1,
        length: str = "short",
        target_point_ids: List[str] | None = None,
        request_id: str | None = None
    ) -> ServiceResult[Dict[str, Any]]:
        """
        提交翻譯答案進行批改
        
        Args:
            chinese: 中文句子
            english: 英文翻譯
            mode: 練習模式 ("new" 或 "review")
            level: 難度等級
            length: 句子長度類型
            target_point_ids: 目標知識點ID列表（複習模式用）
            request_id: 請求ID
            
        Returns:
            ServiceResult: 包含批改結果的服務結果
        """
        return self._execute_with_error_handling(
            "submit_translation",
            self._submit_translation_impl,
            chinese=chinese,
            english=english,
            mode=mode,
            level=level,
            length=length,
            target_point_ids=target_point_ids,
            request_id=request_id
        )
    
    def _submit_translation_impl(
        self,
        chinese: str,
        english: str,
        mode: str,
        level: int,
        length: str,
        target_point_ids: List[str] | None,
        request_id: str | None
    ) -> ServiceResult[Dict[str, Any]]:
        """提交翻譯的實際實現"""
        start_time = time.time()
        
        # 1. 輸入驗證
        validation_result = self.validate_input(
            {
                "chinese": chinese,
                "english": english,
                "mode": mode,
                "level": level,
                "length": length
            },
            {}  # 規則由 ValidationService 內部定義
        )
        
        if not validation_result.success:
            return validation_result
        
        cleaned_data = validation_result.data
        
        # 2. AI 批改
        try:
            grading_result = self.ai_service.grade_translation(
                chinese=cleaned_data["chinese"],
                english=cleaned_data["english"]
            )
        except Exception as e:
            return ServiceResult.error(
                message=f"AI 批改服務失敗: {str(e)}",
                error_type="AIServiceError",
                error_code="AI_GRADING_FAILED"
            )
        
        # 3. 處理複習模式的知識點更新
        if mode == "review" and target_point_ids:
            self._handle_review_updates(
                target_point_ids,
                grading_result,
                chinese,
                english
            )
        
        # 4. 保存錯誤知識點（如果有錯誤）
        is_correct = grading_result.get("is_generally_correct", False)
        if not is_correct:
            try:
                self.knowledge_manager.save_mistake(
                    chinese_sentence=cleaned_data["chinese"],
                    user_answer=cleaned_data["english"],
                    feedback=grading_result,
                    practice_mode=mode
                )
            except Exception as e:
                self.logger.warning(f"保存錯誤知識點失敗: {str(e)}")
        
        # 5. 處理複習成功記錄
        elif mode == "review" and target_point_ids:
            self._handle_review_success(target_point_ids, chinese, english)
        
        # 6. 計算分數
        score = self._calculate_score(grading_result)
        
        # 7. 更新統計
        self._operation_stats["submissions_processed"] += 1
        self._operation_stats["last_operation"] = datetime.now().isoformat()
        
        if mode == "review":
            self._operation_stats["review_sessions"] += 1
        
        # 8. 記錄日誌
        duration_ms = int((time.time() - start_time) * 1000)
        self.log_operation(
            operation="submit_translation",
            success=True,
            duration_ms=duration_ms,
            mode=mode,
            is_correct=is_correct,
            score=score,
            chinese_length=len(chinese),
            english_length=len(english)
        )
        
        # 9. 準備響應資料
        response_data = {
            "grading_result": grading_result,
            "score": score,
            "is_correct": is_correct,
            "mode": mode,
            "target_point_ids": target_point_ids or [],
            "processed_data": {
                "chinese": cleaned_data["chinese"],
                "english": cleaned_data["english"],
                "level": cleaned_data["level"],
                "length": cleaned_data["length"]
            }
        }
        
        return ServiceResult.success(
            data=response_data,
            message="翻譯批改完成",
            request_id=request_id
        )
    
    def generate_practice_sentence(
        self,
        mode: str = "new",
        level: int = 1,
        length: str = "short",
        topic: str | None = None,
        target_points: List[str] | None = None,
        request_id: str | None = None
    ) -> ServiceResult[Dict[str, Any]]:
        """
        生成練習句子
        
        Args:
            mode: 練習模式 ("new" 或 "review")
            level: 難度等級
            length: 句子長度類型
            topic: 主題（可選）
            target_points: 目標知識點（複習模式用）
            request_id: 請求ID
            
        Returns:
            ServiceResult: 包含生成句子的服務結果
        """
        return self._execute_with_error_handling(
            "generate_practice_sentence",
            self._generate_practice_sentence_impl,
            mode=mode,
            level=level,
            length=length,
            topic=topic,
            target_points=target_points,
            request_id=request_id
        )
    
    def _generate_practice_sentence_impl(
        self,
        mode: str,
        level: int,
        length: str,
        topic: str | None,
        target_points: List[str] | None,
        request_id: str | None
    ) -> ServiceResult[Dict[str, Any]]:
        """生成練習句子的實際實現"""
        start_time = time.time()
        
        try:
            if mode == "review":
                # 複習模式：根據知識點生成題目
                sentence_data = self._generate_review_sentence(
                    target_points, level, length
                )
            else:
                # 新題模式：生成新的練習句子
                sentence_data = self._generate_new_sentence(
                    level, length, topic
                )
            
            # 更新統計
            self._operation_stats["questions_generated"] += 1
            self._operation_stats["last_operation"] = datetime.now().isoformat()
            
            # 記錄日誌
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_operation(
                operation="generate_practice_sentence",
                success=True,
                duration_ms=duration_ms,
                mode=mode,
                level=level,
                length=length
            )
            
            return ServiceResult.success(
                data=sentence_data,
                message="練習句子生成成功",
                request_id=request_id
            )
            
        except Exception as e:
            return ServiceResult.error(
                message=f"生成練習句子失敗: {str(e)}",
                error_type=type(e).__name__,
                error_code="SENTENCE_GENERATION_FAILED",
                request_id=request_id
            )
    
    def handle_review_mode(
        self,
        max_points: int = 5,
        categories: List[str] | None = None,
        request_id: str | None = None
    ) -> ServiceResult[Dict[str, Any]]:
        """
        處理複習模式邏輯
        
        Args:
            max_points: 最大知識點數量
            categories: 指定的錯誤類別
            request_id: 請求ID
            
        Returns:
            ServiceResult: 包含複習候選知識點的服務結果
        """
        return self._execute_with_error_handling(
            "handle_review_mode",
            self._handle_review_mode_impl,
            max_points=max_points,
            categories=categories,
            request_id=request_id
        )
    
    def _handle_review_mode_impl(
        self,
        max_points: int,
        categories: List[str] | None,
        request_id: str | None
    ) -> ServiceResult[Dict[str, Any]]:
        """處理複習模式的實際實現"""
        try:
            # 獲取複習候選知識點
            review_candidates = self.knowledge_manager.get_review_candidates(
                max_points=max_points
            )
            
            # 如果指定了類別，進行篩選
            if categories:
                from core.error_types import ErrorCategory
                category_enums = []
                for cat in categories:
                    try:
                        category_enums.append(ErrorCategory.from_string(cat))
                    except (ValueError, KeyError):
                        continue
                
                if category_enums:
                    review_candidates = [
                        point for point in review_candidates
                        if point.category in category_enums
                    ]
            
            # 準備響應資料
            candidate_data = []
            for point in review_candidates:
                candidate_data.append({
                    "id": point.id,
                    "key_point": point.key_point,
                    "category": point.category.value,
                    "category_chinese": point.category.to_chinese(),
                    "mastery_level": point.mastery_level,
                    "mistake_count": point.mistake_count,
                    "correct_count": point.correct_count,
                    "next_review": point.next_review,
                    "is_due": point.next_review <= datetime.now().isoformat() if point.next_review else False,
                    "priority_score": self._calculate_review_priority(point)
                })
            
            # 按優先級排序
            candidate_data.sort(key=lambda x: x["priority_score"], reverse=True)
            
            response_data = {
                "candidates": candidate_data,
                "total_candidates": len(candidate_data),
                "max_points": max_points,
                "categories_filter": categories or []
            }
            
            return ServiceResult.success(
                data=response_data,
                message=f"找到 {len(candidate_data)} 個複習候選知識點",
                request_id=request_id
            )
            
        except Exception as e:
            return ServiceResult.error(
                message=f"處理複習模式失敗: {str(e)}",
                error_type=type(e).__name__,
                error_code="REVIEW_MODE_HANDLING_FAILED",
                request_id=request_id
            )
    
    def get_practice_statistics(
        self, 
        request_id: str | None = None
    ) -> ServiceResult[Dict[str, Any]]:
        """
        獲取練習統計資料
        
        Args:
            request_id: 請求ID
            
        Returns:
            ServiceResult: 包含統計資料的服務結果
        """
        return self._execute_with_error_handling(
            "get_practice_statistics",
            self._get_practice_statistics_impl,
            request_id=request_id
        )
    
    def _get_practice_statistics_impl(
        self,
        request_id: str | None
    ) -> ServiceResult[Dict[str, Any]]:
        """獲取練習統計的實際實現"""
        try:
            # 從知識管理器獲取基本統計
            basic_stats = self.knowledge_manager.get_statistics()
            
            # 計算額外的統計資料
            all_points = self.knowledge_manager.knowledge_points
            
            # 掌握度分佈
            mastery_distribution = self._calculate_mastery_distribution(all_points)
            
            # 類別分佈
            category_distribution = self._calculate_category_distribution(all_points)
            
            # 最近活動
            recent_activity = self._get_recent_activity()
            
            # 複習建議
            review_suggestions = self._get_review_suggestions()
            
            stats_data = {
                **basic_stats,
                "mastery_distribution": mastery_distribution,
                "category_distribution": category_distribution,
                "recent_activity": recent_activity,
                "review_suggestions": review_suggestions,
                "service_stats": self._operation_stats.copy()
            }
            
            return ServiceResult.success(
                data=stats_data,
                message="統計資料獲取成功",
                request_id=request_id
            )
            
        except Exception as e:
            return ServiceResult.error(
                message=f"獲取統計資料失敗: {str(e)}",
                error_type=type(e).__name__,
                error_code="STATISTICS_RETRIEVAL_FAILED",
                request_id=request_id
            )
    
    # === 私有輔助方法 ===
    
    def _handle_review_updates(
        self,
        target_point_ids: List[str],
        grading_result: Dict[str, Any],
        chinese: str,
        english: str
    ):
        """處理複習模式的知識點更新"""
        is_correct = grading_result.get("is_generally_correct", False)
        
        for point_id in target_point_ids:
            try:
                self.knowledge_manager.update_knowledge_point(point_id, is_correct)
                
                self.logger.info(
                    "複習知識點更新",
                    point_id=point_id,
                    is_correct=is_correct,
                    chinese=chinese[:50],
                    english=english[:50]
                )
            except Exception as e:
                self.logger.error(f"更新知識點 {point_id} 失敗: {str(e)}")
    
    def _handle_review_success(
        self,
        target_point_ids: List[str],
        chinese: str,
        english: str
    ):
        """處理複習成功的記錄"""
        for point_id in target_point_ids:
            try:
                self.knowledge_manager.add_review_success(
                    knowledge_point_id=point_id,
                    chinese_sentence=chinese,
                    user_answer=english
                )
            except Exception as e:
                self.logger.error(f"記錄複習成功 {point_id} 失敗: {str(e)}")
    
    def _calculate_score(self, grading_result: Dict[str, Any]) -> int:
        """根據批改結果計算分數"""
        base_score = PracticeConfig.SCORE_MAX
        errors = grading_result.get("error_analysis", [])
        
        for error in errors:
            category = error.get("category", "other")
            if category == "systematic":
                base_score -= 15
            elif category == "isolated":
                base_score -= 10
            elif category == "enhancement":
                base_score -= 5
            else:
                base_score -= 8
        
        return max(PracticeConfig.SCORE_MIN, min(PracticeConfig.SCORE_MAX, base_score))
    
    def _generate_review_sentence(
        self,
        target_points: List[str] | None,
        level: int,
        length: str
    ) -> Dict[str, Any]:
        """生成複習句子"""
        if not target_points:
            # 自動選擇複習點
            candidates = self.knowledge_manager.get_review_candidates(max_points=3)
            if not candidates:
                raise ValueError("沒有可複習的知識點")
            selected_points = candidates[:2]  # 最多選擇2個
        else:
            # 使用指定的知識點
            selected_points = []
            for point_id in target_points:
                point = self.knowledge_manager.get_knowledge_point(point_id)
                if point:
                    selected_points.append(point)
        
        if not selected_points:
            raise ValueError("找不到指定的知識點")
        
        # 使用 AI 服務生成複習句子
        result = self.ai_service.generate_review_sentence(
            knowledge_points=selected_points,
            level=level,
            length=length
        )
        
        return {
            "chinese_sentence": result["sentence"],
            "target_points": [point.id for point in selected_points],
            "target_point_details": [
                {
                    "id": point.id,
                    "key_point": point.key_point,
                    "category": point.category.value
                }
                for point in selected_points
            ]
        }
    
    def _generate_new_sentence(
        self,
        level: int,
        length: str,
        topic: str | None
    ) -> Dict[str, Any]:
        """生成新的練習句子"""
        result = self.ai_service.generate_practice_sentence(
            level=level,
            length=length
        )
        
        return {
            "chinese_sentence": result["sentence"],
            "target_points": [],
            "target_point_details": []
        }
    
    def _calculate_review_priority(self, point) -> float:
        """計算複習優先級分數"""
        # 基於掌握度、錯誤次數、距離下次複習時間等因素
        mastery_factor = 1.0 - point.mastery_level  # 掌握度越低優先級越高
        mistake_factor = min(point.mistake_count / 10, 1.0)  # 錯誤次數影響
        
        # 時間因素（如果已經過期，優先級更高）
        time_factor = 1.0
        if point.next_review and point.next_review <= datetime.now().isoformat():
            time_factor = 1.5
        
        return (mastery_factor * 0.4 + mistake_factor * 0.3) * time_factor
    
    def _calculate_mastery_distribution(self, points) -> Dict[str, int]:
        """計算掌握度分佈"""
        distribution = {"低": 0, "中": 0, "高": 0}
        
        for point in points:
            if point.mastery_level < 0.3:
                distribution["低"] += 1
            elif point.mastery_level < 0.7:
                distribution["中"] += 1
            else:
                distribution["高"] += 1
        
        return distribution
    
    def _calculate_category_distribution(self, points) -> Dict[str, int]:
        """計算類別分佈"""
        distribution = {}
        
        for point in points:
            category = point.category.to_chinese()
            distribution[category] = distribution.get(category, 0) + 1
        
        return distribution
    
    def _get_recent_activity(self) -> Dict[str, Any]:
        """獲取最近活動資訊"""
        return {
            "last_operation": self._operation_stats.get("last_operation"),
            "operations_today": self._operation_stats["submissions_processed"],
            "reviews_today": self._operation_stats["review_sessions"]
        }
    
    def _get_review_suggestions(self) -> List[str]:
        """獲取複習建議"""
        suggestions = []
        
        # 檢查是否有過期的複習
        now = datetime.now().isoformat()
        overdue_count = len([
            p for p in self.knowledge_manager.knowledge_points
            if p.next_review and p.next_review <= now
        ])
        
        if overdue_count > 0:
            suggestions.append(f"您有 {overdue_count} 個知識點需要複習")
        
        # 檢查低掌握度的知識點
        low_mastery_count = len([
            p for p in self.knowledge_manager.knowledge_points
            if p.mastery_level < 0.3
        ])
        
        if low_mastery_count > 5:
            suggestions.append(f"建議加強練習 {low_mastery_count} 個掌握度較低的知識點")
        
        if not suggestions:
            suggestions.append("繼續保持學習，您的進度很好！")
        
        return suggestions
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        return {
            "service_name": "PracticeService",
            "version": "1.0.0",
            "description": "練習業務邏輯服務",
            "capabilities": [
                "翻譯提交批改",
                "練習題目生成", 
                "複習模式處理",
                "練習統計分析"
            ],
            "statistics": self._operation_stats.copy(),
            "dependencies": {
                "ai_service": self.ai_service.__class__.__name__,
                "knowledge_manager": self.knowledge_manager.__class__.__name__
            },
            "initialized": self._initialized
        }