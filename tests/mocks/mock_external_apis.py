"""
外部 API Mock 實現
模擬 Gemini API 和其他外部服務的行為
"""

import asyncio
import json
import random
import time
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

import responses


class MockGeminiAPI:
    """Gemini API Mock 實現"""
    
    def __init__(self, 
                 response_delay: float = 0.1,
                 error_rate: float = 0.0,
                 quota_limit: int = 1000):
        self.response_delay = response_delay
        self.error_rate = error_rate
        self.quota_limit = quota_limit
        self.request_count = 0
        self.quota_used = 0
        
        # API 調用歷史
        self.call_history: List[Dict[str, Any]] = []
        
        # 模型配置
        self.models = {
            "gemini-2.5-flash": {
                "temperature": 1.0,
                "top_p": 0.95,
                "top_k": 40,
                "response_format": "json"
            },
            "gemini-2.5-pro": {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 20,
                "response_format": "json"
            }
        }
    
    async def generate_content_async(self, 
                                   model_name: str,
                                   prompt: str,
                                   **kwargs) -> Dict[str, Any]:
        """異步生成內容"""
        await asyncio.sleep(self.response_delay)
        
        self.request_count += 1
        self.quota_used += len(prompt) // 4  # 簡單的 token 估算
        
        # 記錄調用
        call_record = {
            "model": model_name,
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "timestamp": datetime.now().isoformat(),
            "request_id": self.request_count,
            "quota_used": len(prompt) // 4
        }
        self.call_history.append(call_record)
        
        # 檢查配額
        if self.quota_used > self.quota_limit:
            raise Exception("API quota exceeded")
        
        # 模擬錯誤
        if random.random() < self.error_rate:
            error_types = [
                "Network timeout",
                "Rate limit exceeded", 
                "Model temporarily unavailable",
                "Invalid request format"
            ]
            raise Exception(random.choice(error_types))
        
        # 根據模型和提示生成回應
        return self._generate_response(model_name, prompt, kwargs)
    
    def _generate_response(self, 
                          model_name: str, 
                          prompt: str, 
                          kwargs: Dict) -> Dict[str, Any]:
        """根據提示生成適當的回應"""
        
        # 分析提示內容
        if "生成" in prompt and "翻譯練習" in prompt:
            return self._generate_practice_question_response(prompt)
        
        elif "批改" in prompt:
            return self._generate_grading_response(prompt)
        
        elif "複習" in prompt:
            return self._generate_review_response(prompt)
        
        else:
            return self._generate_generic_response(prompt)
    
    def _generate_practice_question_response(self, prompt: str) -> Dict[str, Any]:
        """生成練習題目回應"""
        sentences = [
            "我昨天去了圖書館。",
            "她正在準備考試。",
            "我們計劃下週去旅行。",
            "他每天騎自行車上班。", 
            "這家餐廳的食物很美味。",
        ]
        
        knowledge_points_options = [
            ["past_tense", "location"],
            ["present_continuous", "exam_preparation"],
            ["future_plan", "travel_vocabulary"],
            ["daily_routine", "transportation"],
            ["restaurant", "food_vocabulary", "adjective"]
        ]
        
        idx = random.randint(0, len(sentences) - 1)
        
        return {
            "chinese_sentence": sentences[idx],
            "knowledge_points": knowledge_points_options[idx],
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "explanation": f"這個句子主要練習 {knowledge_points_options[idx][0]} 的使用。"
        }
    
    def _generate_grading_response(self, prompt: str) -> Dict[str, Any]:
        """生成批改回應"""
        # 簡單分析用戶答案（從提示中提取）
        is_likely_correct = "correct" in prompt.lower() or "perfect" in prompt.lower()
        
        if is_likely_correct:
            return {
                "is_correct": True,
                "score": random.randint(90, 100),
                "feedback": "Excellent! Your translation is accurate and natural.",
                "knowledge_points": [],
                "suggestions": []
            }
        else:
            return {
                "is_correct": False,
                "score": random.randint(50, 80),
                "feedback": "Good effort! Please review the grammar points below.",
                "knowledge_points": [
                    {
                        "title": random.choice([
                            "動詞時態錯誤", "冠詞使用錯誤", "介詞搭配錯誤"
                        ]),
                        "description": random.choice([
                            "注意動詞時態的一致性", "缺少必要的冠詞", "介詞搭配不當"
                        ]),
                        "error_category": random.choice([
                            "systematic", "singular", "better"
                        ]),
                        "examples": ["Example correction here"]
                    }
                ],
                "suggestions": [
                    random.choice([
                        "Review past tense formation",
                        "Study article usage rules",
                        "Practice preposition collocations"
                    ])
                ]
            }
    
    def _generate_review_response(self, prompt: str) -> Dict[str, Any]:
        """生成複習題目回應"""
        return {
            "chinese_sentence": "我上週完成了作業。",
            "target_knowledge_points": ["past_tense", "completion"],
            "focus_areas": ["時態一致性", "動詞形式"],
            "hints": ["注意動詞的過去式形式", "確認時間狀語的搭配"]
        }
    
    def _generate_generic_response(self, prompt: str) -> Dict[str, Any]:
        """生成通用回應"""
        return {
            "response": "Generic AI response",
            "confidence": random.uniform(0.7, 0.95),
            "processing_time": self.response_delay
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取 API 統計信息"""
        return {
            "total_requests": self.request_count,
            "quota_used": self.quota_used,
            "quota_limit": self.quota_limit,
            "quota_remaining": max(0, self.quota_limit - self.quota_used),
            "error_rate": self.error_rate,
            "recent_calls": self.call_history[-10:],
            "average_response_time": self.response_delay
        }
    
    def reset_statistics(self):
        """重置統計信息"""
        self.request_count = 0
        self.quota_used = 0
        self.call_history.clear()
    
    def set_error_rate(self, error_rate: float):
        """設置錯誤率"""
        self.error_rate = error_rate
    
    def set_quota_limit(self, limit: int):
        """設置配額限制"""
        self.quota_limit = limit


class MockHTTPClient:
    """HTTP 客戶端 Mock，用於模擬網絡請求"""
    
    def __init__(self):
        self.responses_data = {}
        self.request_history = []
    
    def set_response(self, url: str, response_data: Any, status_code: int = 200):
        """設置 URL 的回應數據"""
        self.responses_data[url] = {
            "data": response_data,
            "status_code": status_code
        }
    
    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        """模擬 GET 請求"""
        self.request_history.append({
            "method": "GET",
            "url": url,
            "kwargs": kwargs,
            "timestamp": datetime.now().isoformat()
        })
        
        if url in self.responses_data:
            response_config = self.responses_data[url]
            if response_config["status_code"] != 200:
                raise Exception(f"HTTP {response_config['status_code']} Error")
            return response_config["data"]
        else:
            raise Exception(f"No mock response configured for URL: {url}")
    
    async def post(self, url: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """模擬 POST 請求"""
        self.request_history.append({
            "method": "POST",
            "url": url,
            "data": data,
            "kwargs": kwargs,
            "timestamp": datetime.now().isoformat()
        })
        
        if url in self.responses_data:
            response_config = self.responses_data[url]
            if response_config["status_code"] != 200:
                raise Exception(f"HTTP {response_config['status_code']} Error")
            return response_config["data"]
        else:
            raise Exception(f"No mock response configured for URL: {url}")


@responses.activate
def setup_gemini_api_responses():
    """設置 Gemini API 的 HTTP 回應"""
    
    # 生成內容 API
    responses.add(
        responses.POST,
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        json={
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "chinese_sentence": "我昨天去了圖書館。",
                            "knowledge_points": ["past_tense", "location"]
                        }, ensure_ascii=False)
                    }]
                }
            }]
        },
        status=200
    )
    
    # 批改 API 
    responses.add(
        responses.POST,
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent",
        json={
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "is_correct": False,
                            "feedback": "需要注意時態",
                            "knowledge_points": [{
                                "title": "動詞時態錯誤",
                                "error_category": "systematic"
                            }]
                        }, ensure_ascii=False)
                    }]
                }
            }]
        },
        status=200
    )


def create_mock_gemini_api(behavior: str = "normal") -> MockGeminiAPI:
    """
    創建不同行為的 Gemini API Mock
    
    Args:
        behavior: API 行為模式 ("normal", "slow", "unreliable", "quota_limited")
    """
    configs = {
        "normal": {"response_delay": 0.1, "error_rate": 0.0, "quota_limit": 10000},
        "slow": {"response_delay": 2.0, "error_rate": 0.0, "quota_limit": 10000},
        "unreliable": {"response_delay": 0.5, "error_rate": 0.3, "quota_limit": 10000},
        "quota_limited": {"response_delay": 0.1, "error_rate": 0.0, "quota_limit": 100}
    }
    
    config = configs.get(behavior, configs["normal"])
    return MockGeminiAPI(**config)


class ExternalAPIMockContext:
    """外部 API Mock 上下文管理器"""
    
    def __init__(self, gemini_api: Optional[MockGeminiAPI] = None):
        self.gemini_api = gemini_api or MockGeminiAPI()
        self.patches = []
    
    def __enter__(self):
        # Mock google.generativeai
        genai_patch = patch('google.generativeai')
        mock_genai = genai_patch.start()
        
        # Mock 生成模型
        mock_model = Mock()
        mock_model.generate_content_async = self.gemini_api.generate_content_async
        
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        self.patches.append(genai_patch)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch_obj in reversed(self.patches):
            patch_obj.stop()
        self.patches.clear()
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """獲取 API 統計信息"""
        return self.gemini_api.get_statistics()