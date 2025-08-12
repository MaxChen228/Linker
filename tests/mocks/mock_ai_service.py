"""
AI 服務 Mock 實現
模擬 AIService 的各種行為，包括成功、失敗和異常情況
"""

import asyncio
import random
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from tests.factories.ai_response_factory import (
    create_successful_grading_response,
    create_failed_grading_response,
    create_question_generation_response,
    create_llm_interaction_log,
)


class MockAIService:
    """AI 服務 Mock 類，模擬真實 AI 服務的行為"""
    
    def __init__(self, 
                 failure_rate: float = 0.0,
                 response_delay: float = 0.1,
                 enable_api_errors: bool = False):
        """
        初始化 Mock AI 服務
        
        Args:
            failure_rate: 失敗率 (0.0-1.0)，控制返回錯誤回應的機率
            response_delay: 模擬網絡延遲時間（秒）
            enable_api_errors: 是否啟用 API 錯誤模擬
        """
        self.failure_rate = failure_rate
        self.response_delay = response_delay
        self.enable_api_errors = enable_api_errors
        self.call_count = 0
        self.last_llm_interaction = None
        
        # 預設回應配置
        self.grade_accuracy = 0.8  # 批改準確度
        self.generation_diversity = 0.9  # 生成題目多樣性
        
        # 錯誤統計
        self.api_errors = []
        self.response_times = []
        
    async def _simulate_network_delay(self):
        """模擬網絡延遲"""
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)
    
    def _should_fail(self) -> bool:
        """根據失敗率決定是否應該失敗"""
        return random.random() < self.failure_rate
    
    def _record_interaction(self, 
                           method: str, 
                           prompt: str, 
                           response: Dict[str, Any],
                           model: str = "gemini-2.5-flash"):
        """記錄 LLM 互動"""
        self.call_count += 1
        start_time = datetime.now()
        
        self.last_llm_interaction = {
            "method": method,
            "prompt": prompt,
            "response": response,
            "model": model,
            "timestamp": start_time.isoformat(),
            "call_number": self.call_count,
            "response_time": self.response_delay
        }
        
        self.response_times.append(self.response_delay)
    
    async def generate_practice_question(self, 
                                       difficulty: str = "medium",
                                       knowledge_points: Optional[List[str]] = None,
                                       **kwargs) -> Dict[str, Any]:
        """
        模擬生成練習題目
        
        Args:
            difficulty: 難度等級
            knowledge_points: 指定的知識點
            
        Returns:
            生成的題目數據
        """
        await self._simulate_network_delay()
        
        if self.enable_api_errors and self._should_fail():
            error_msg = "API quota exceeded" if random.random() < 0.5 else "Network timeout"
            self.api_errors.append(error_msg)
            raise Exception(error_msg)
        
        # 根據知識點生成對應的題目
        if knowledge_points:
            # 針對特定知識點生成
            chinese_sentences = {
                "past_tense": "我昨天去了圖書館。",
                "present_continuous": "她正在學習中文。",
                "article_usage": "我是一個學生。",
                "preposition": "我對音樂很感興趣。",
            }
            
            selected_kp = knowledge_points[0] if knowledge_points else "past_tense"
            chinese_sentence = chinese_sentences.get(selected_kp, "我每天早上七點起床。")
            
            response = {
                "chinese_sentence": chinese_sentence,
                "knowledge_points": knowledge_points,
                "difficulty": difficulty,
                "explanation": f"針對 {selected_kp} 的練習題"
            }
        else:
            # 生成通用題目
            response = create_question_generation_response(difficulty)
        
        prompt = f"生成{difficulty}難度的翻譯練習題目"
        self._record_interaction("generate_practice_question", prompt, response)
        
        return response
    
    async def grade_translation(self, 
                              chinese_sentence: str,
                              user_answer: str,
                              correct_answer: Optional[str] = None,
                              **kwargs) -> Dict[str, Any]:
        """
        模擬批改翻譯
        
        Args:
            chinese_sentence: 中文原句
            user_answer: 用戶答案
            correct_answer: 標準答案（可選）
            
        Returns:
            批改結果
        """
        await self._simulate_network_delay()
        
        if self.enable_api_errors and self._should_fail():
            error_msg = "AI model is temporarily unavailable"
            self.api_errors.append(error_msg)
            raise Exception(error_msg)
        
        # 簡單的答案評估邏輯
        is_likely_correct = self._evaluate_answer_quality(user_answer)
        
        if is_likely_correct and random.random() < self.grade_accuracy:
            response = create_successful_grading_response()
        else:
            # 生成錯誤分析
            error_count = self._count_likely_errors(user_answer)
            response = create_failed_grading_response(error_count)
            response['corrected_answer'] = correct_answer or self._generate_correction(user_answer)
        
        prompt = f"請批改翻譯：{chinese_sentence} -> {user_answer}"
        self._record_interaction("grade_translation", prompt, response, "gemini-2.5-pro")
        
        return response
    
    async def generate_review_question(self,
                                     knowledge_points: List[str],
                                     difficulty: str = "medium",
                                     **kwargs) -> Dict[str, Any]:
        """
        模擬生成複習題目
        
        Args:
            knowledge_points: 要複習的知識點
            difficulty: 難度等級
            
        Returns:
            複習題目數據
        """
        await self._simulate_network_delay()
        
        if self.enable_api_errors and self._should_fail():
            error_msg = "Review generation service unavailable"
            self.api_errors.append(error_msg)
            raise Exception(error_msg)
        
        # 根據知識點生成復習題
        review_sentences = {
            "past_tense": "我上週完成了這個專案。",
            "present_continuous": "他們正在討論重要問題。", 
            "article_usage": "這是一本很有用的書。",
            "preposition": "我們對結果很滿意。",
        }
        
        # 選擇第一個知識點對應的句子
        primary_kp = knowledge_points[0] if knowledge_points else "past_tense"
        chinese_sentence = review_sentences.get(primary_kp, "我每天都練習英文。")
        
        response = {
            "chinese_sentence": chinese_sentence,
            "target_knowledge_points": knowledge_points,
            "difficulty": difficulty,
            "focus_areas": [f"{kp}_review" for kp in knowledge_points[:2]],
            "hints": [f"注意 {kp} 的使用" for kp in knowledge_points[:2]]
        }
        
        prompt = f"為知識點 {knowledge_points} 生成復習題目"
        self._record_interaction("generate_review_question", prompt, response)
        
        return response
    
    def _evaluate_answer_quality(self, answer: str) -> bool:
        """簡單評估答案質量"""
        # 基於一些啟發式規則
        if len(answer.strip()) < 3:
            return False
        
        # 檢查常見錯誤模式
        common_errors = [
            "go to library",  # 缺少冠詞
            "I go yesterday", # 時態錯誤
            "She studying",   # 缺少be動詞
            "very interesting book",  # 缺少be動詞
        ]
        
        for error_pattern in common_errors:
            if error_pattern in answer.lower():
                return False
        
        return True
    
    def _count_likely_errors(self, answer: str) -> int:
        """估算答案中的錯誤數量"""
        error_indicators = [
            ("go to library", 2),      # 時態+冠詞
            ("studying", 1),           # be動詞
            ("very interesting", 1),   # be動詞
            ("interested on", 1),      # 介詞
            ("everyday", 1),           # 拼寫
        ]
        
        total_errors = 0
        for pattern, error_count in error_indicators:
            if pattern in answer.lower():
                total_errors += error_count
        
        return max(1, total_errors)  # 至少1個錯誤
    
    def _generate_correction(self, answer: str) -> str:
        """生成簡單的糾正版本"""
        corrections = {
            "go to library": "went to the library",
            "studying Chinese": "is studying Chinese", 
            "very interesting": "is very interesting",
            "interested on": "interested in",
            "everyday": "every day",
        }
        
        corrected = answer
        for wrong, right in corrections.items():
            corrected = corrected.replace(wrong, right)
        
        return corrected
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取 Mock 服務統計信息"""
        return {
            "total_calls": self.call_count,
            "api_errors": len(self.api_errors),
            "avg_response_time": sum(self.response_times) / len(self.response_times) 
                                if self.response_times else 0,
            "failure_rate": self.failure_rate,
            "last_interaction": self.last_llm_interaction
        }
    
    def reset_statistics(self):
        """重置統計信息"""
        self.call_count = 0
        self.api_errors = []
        self.response_times = []
        self.last_llm_interaction = None


def create_mock_ai_service(behavior: str = "normal") -> MockAIService:
    """
    創建不同行為模式的 Mock AI 服務
    
    Args:
        behavior: 行為模式 ("normal", "unreliable", "slow", "error_prone")
    """
    configs = {
        "normal": {"failure_rate": 0.0, "response_delay": 0.1, "enable_api_errors": False},
        "unreliable": {"failure_rate": 0.3, "response_delay": 0.2, "enable_api_errors": True},
        "slow": {"failure_rate": 0.0, "response_delay": 2.0, "enable_api_errors": False},
        "error_prone": {"failure_rate": 0.5, "response_delay": 0.1, "enable_api_errors": True},
    }
    
    config = configs.get(behavior, configs["normal"])
    return MockAIService(**config)


def create_ai_service_mock_with_responses(responses: Dict[str, Any]) -> Mock:
    """
    創建預設回應的 AI 服務 Mock
    
    Args:
        responses: 預設的回應字典，key 為方法名，value 為回應數據
    """
    mock = Mock()
    
    # 設置異步方法的回應
    for method_name, response_data in responses.items():
        mock_method = AsyncMock()
        if isinstance(response_data, list):
            mock_method.side_effect = response_data
        else:
            mock_method.return_value = response_data
        
        setattr(mock, method_name, mock_method)
    
    return mock