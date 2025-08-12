"""
錯誤處理服務 - 專門處理錯誤分析和知識點創建
從 KnowledgeManager._process_error 提取的邏輯重構為獨立服務
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_service import BaseService, ServiceResult
from core.error_types import ErrorCategory, ErrorTypeSystem
from core.repositories.knowledge_repository import KnowledgeRepository
from core.knowledge import KnowledgeManager, KnowledgePoint, OriginalError, ReviewExample


class ErrorProcessingService(BaseService):
    """錯誤處理服務 - 負責處理錯誤分析和知識點管理"""
    
    def __init__(
        self,
        error_type_system: Optional[ErrorTypeSystem] = None,
        knowledge_repository: Optional[KnowledgeRepository] = None,
        knowledge_manager: Optional[KnowledgeManager] = None
    ):
        super().__init__("ErrorProcessingService")
        
        # 依賴注入
        self.error_type_system = error_type_system or ErrorTypeSystem()
        self.knowledge_repository = knowledge_repository or KnowledgeRepository("data/knowledge.json")
        self.knowledge_manager = knowledge_manager or KnowledgeManager()
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        return {
            "name": "ErrorProcessingService",
            "version": "1.0.0",
            "description": "處理錯誤分析和知識點創建",
            "status": "active",
            "dependencies": [
                "ErrorTypeSystem",
                "KnowledgeRepository", 
                "KnowledgeManager"
            ]
        }
    
    def process_errors(
        self,
        chinese_sentence: str,
        user_answer: str,
        feedback: Dict[str, Any],
        practice_mode: str = "new"
    ) -> ServiceResult[List[Dict[str, Any]]]:
        """
        批量處理錯誤 - 主要入口方法
        
        Args:
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            feedback: AI 反饋內容
            practice_mode: 練習模式 ('new' 或 'review')
            
        Returns:
            包含處理結果的 ServiceResult
        """
        return self._execute_with_error_handling(
            "process_errors",
            self._process_errors_impl,
            chinese_sentence,
            user_answer, 
            feedback,
            practice_mode
        )
    
    def _process_errors_impl(
        self,
        chinese_sentence: str,
        user_answer: str,
        feedback: Dict[str, Any],
        practice_mode: str
    ) -> ServiceResult[List[Dict[str, Any]]]:
        """實際的批量錯誤處理邏輯"""
        errors = feedback.get("error_analysis", [])
        correct_answer = feedback.get("overall_suggestion", "")
        processed_errors = []
        
        for error in errors:
            result = self.process_single_error(
                chinese_sentence=chinese_sentence,
                user_answer=user_answer,
                error=error,
                correct_answer=correct_answer,
                practice_mode=practice_mode
            )
            
            if result.success:
                processed_errors.append(result.data)
            else:
                self.logger.warning(f"處理錯誤失敗: {result.message}")
        
        return ServiceResult.success(
            data=processed_errors,
            message=f"成功處理 {len(processed_errors)} 個錯誤"
        )
    
    def process_single_error(
        self,
        chinese_sentence: str,
        user_answer: str,
        error: Dict[str, Any],
        correct_answer: str,
        practice_mode: str = "new"
    ) -> ServiceResult[Dict[str, Any]]:
        """
        處理單個錯誤
        
        Args:
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            error: 單個錯誤信息
            correct_answer: 正確答案
            practice_mode: 練習模式
            
        Returns:
            處理結果
        """
        return self._execute_with_error_handling(
            "process_single_error",
            self._process_single_error_impl,
            chinese_sentence,
            user_answer,
            error,
            correct_answer,
            practice_mode
        )
    
    def _process_single_error_impl(
        self,
        chinese_sentence: str,
        user_answer: str,
        error: Dict[str, Any],
        correct_answer: str,
        practice_mode: str
    ) -> ServiceResult[Dict[str, Any]]:
        """實際的單個錯誤處理邏輯"""
        # 提取錯誤詳細信息
        error_details = self.extract_error_details(error)
        
        # 錯誤分類
        category, subtype = self.classify_error(error_details)
        
        # 生成具體的知識點描述
        specific_key_point = self._generate_specific_key_point(error_details)
        
        # 查找或更新現有知識點
        knowledge_point = self.find_or_update_existing_point(
            key_point=specific_key_point,
            original_phrase=error_details["original_phrase"],
            correction=error_details["correction"],
            chinese_sentence=chinese_sentence,
            user_answer=user_answer,
            correct_answer=correct_answer,
            practice_mode=practice_mode
        )
        
        if not knowledge_point:
            # 創建新知識點
            knowledge_point = self.create_knowledge_point_from_error(
                error_details=error_details,
                category=category,
                subtype=subtype,
                specific_key_point=specific_key_point,
                chinese_sentence=chinese_sentence,
                user_answer=user_answer,
                correct_answer=correct_answer
            )
        
        return ServiceResult.success(
            data={
                "knowledge_point_id": knowledge_point.id if knowledge_point else None,
                "category": category.value,
                "subtype": subtype,
                "key_point": specific_key_point,
                "practice_mode": practice_mode
            },
            message="錯誤處理完成"
        )
    
    def extract_error_details(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取錯誤詳細信息
        
        Args:
            error: 錯誤信息字典
            
        Returns:
            標準化的錯誤詳細信息
        """
        return {
            "key_point": error.get("key_point_summary", ""),
            "original_phrase": error.get("original_phrase", ""),
            "correction": error.get("correction", ""),
            "explanation": error.get("explanation", ""),
            "severity": error.get("severity", "major")
        }
    
    def classify_error(self, error_details: Dict[str, Any]) -> tuple[ErrorCategory, str]:
        """
        使用 ErrorTypeSystem 進行錯誤分類
        
        Args:
            error_details: 錯誤詳細信息
            
        Returns:
            (ErrorCategory, subtype_name) 元組
        """
        # 優先使用 AI 返回的分類
        if "category" in error_details:
            try:
                category = ErrorCategory.from_string(error_details["category"])
                _, subtype = self.error_type_system.classify(
                    error_details["key_point"],
                    error_details["explanation"],
                    error_details["severity"]
                )
                return category, subtype
            except ValueError:
                # AI 分類無效，回退到自動分類
                pass
        
        # 使用分類系統自動分類
        return self.error_type_system.classify(
            error_details["key_point"],
            error_details["explanation"],
            error_details["severity"]
        )
    
    def _generate_specific_key_point(self, error_details: Dict[str, Any]) -> str:
        """生成具體的知識點描述"""
        key_point = error_details["key_point"]
        original_phrase = error_details["original_phrase"]
        
        if original_phrase and original_phrase.strip():
            return f"{key_point}: {original_phrase}"
        return key_point
    
    def find_or_update_existing_point(
        self,
        key_point: str,
        original_phrase: str,
        correction: str,
        chinese_sentence: str,
        user_answer: str,
        correct_answer: str,
        practice_mode: str
    ) -> Optional[KnowledgePoint]:
        """
        查找或更新現有知識點
        
        Args:
            key_point: 知識點描述
            original_phrase: 原始短語
            correction: 修正版本
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            correct_answer: 正確答案
            practice_mode: 練習模式
            
        Returns:
            更新後的知識點或 None
        """
        existing = self.knowledge_manager._find_knowledge_point(
            key_point, original_phrase, correction
        )
        
        if existing:
            # 更新現有知識點的掌握度
            existing.update_mastery(is_correct=False)
            
            if practice_mode == "review":
                # 複習模式：添加到複習例句
                review_example = ReviewExample(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    timestamp=datetime.now().isoformat(),
                    is_correct=False
                )
                existing.review_examples.append(review_example)
            else:
                # 新題模式下發現重複（異常情況）
                self.logger.warning(f"新題模式下發現重複知識點: {existing.unique_identifier}")
            
            # 保存更新
            self.knowledge_manager._save_knowledge()
            return existing
        
        return None
    
    def create_knowledge_point_from_error(
        self,
        error_details: Dict[str, Any],
        category: ErrorCategory,
        subtype: str,
        specific_key_point: str,
        chinese_sentence: str,
        user_answer: str,
        correct_answer: str
    ) -> KnowledgePoint:
        """
        從錯誤創建新的知識點
        
        Args:
            error_details: 錯誤詳細信息
            category: 錯誤類別
            subtype: 錯誤子類型
            specific_key_point: 具體知識點描述
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            correct_answer: 正確答案
            
        Returns:
            新創建的知識點
        """
        # 創建原始錯誤記錄
        original_error = OriginalError(
            chinese_sentence=chinese_sentence,
            user_answer=user_answer,
            correct_answer=correct_answer,
            timestamp=datetime.now().isoformat()
        )
        
        # 創建新知識點
        new_point = KnowledgePoint(
            id=self.knowledge_manager._get_next_id(),
            key_point=specific_key_point,
            category=category,
            subtype=subtype,
            explanation=error_details["explanation"],
            original_phrase=error_details["original_phrase"],
            correction=error_details["correction"],
            original_error=original_error,
            review_examples=[]
        )
        
        # 添加到知識點列表
        self.knowledge_manager.knowledge_points.append(new_point)
        
        # 保存
        self.knowledge_manager._save_knowledge()
        
        return new_point