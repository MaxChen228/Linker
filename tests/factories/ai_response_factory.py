"""
AI 回應測試數據工廠
提供各種 AI 服務回應格式的測試數據
"""

import factory
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
import json


class AIGenerateQuestionFactory(factory.Factory):
    """AI 生成題目回應工廠"""
    
    class Meta:
        model = dict
    
    chinese_sentence = factory.Sequence(
        lambda n: [
            "我每天早上七點起床。",
            "她正在圖書館讀書。", 
            "我們明天要去看電影。",
            "他昨天買了一件新衣服。",
            "老師正在黑板上寫字。",
            "這本書非常有趣。",
            "我喜歡在公園散步。",
            "學生們在討論問題。",
            "天氣今天很好。",
            "我媽媽會做很多菜。"
        ][n % 10]
    )
    
    knowledge_points = factory.LazyFunction(
        lambda: random.sample([
            "present_tense", "daily_routine", "time_expression",
            "present_continuous", "location_preposition", "reading_vocabulary",
            "future_tense", "modal_verbs", "entertainment",
            "past_tense", "shopping_vocabulary", "clothing",
            "present_continuous", "classroom_vocabulary", "actions",
            "adjective_usage", "book_vocabulary", "description",
            "preference_expression", "outdoor_activities", "gerund",
            "present_continuous", "discussion_vocabulary", "group_activity",
            "weather_vocabulary", "present_tense", "description",
            "cooking_vocabulary", "ability_expression", "family"
        ], k=random.randint(1, 3))
    )
    
    difficulty = factory.LazyFunction(
        lambda: random.choice(["easy", "medium", "hard"])
    )
    
    explanation = factory.LazyAttribute(
        lambda obj: f"This sentence focuses on {', '.join(obj.knowledge_points[:2])}."
    )
    
    expected_patterns = factory.LazyFunction(
        lambda: random.sample([
            "subject + verb + object",
            "time expression + main clause", 
            "present continuous structure",
            "modal verb + base form",
            "past tense pattern"
        ], k=random.randint(1, 2))
    )


class AIGradingResponseFactory(factory.Factory):
    """AI 批改回應工廠"""
    
    class Meta:
        model = dict
    
    is_correct = factory.LazyFunction(lambda: random.choice([True, False]))
    
    score = factory.LazyAttribute(
        lambda obj: random.randint(85, 100) if obj.is_correct 
        else random.randint(40, 84)
    )
    
    feedback = factory.LazyAttribute(
        lambda obj: "Excellent! Your translation is accurate and natural." 
        if obj.is_correct else "Good effort! Please check the grammar points mentioned below."
    )
    
    knowledge_points = factory.LazyFunction(
        lambda: [
            {
                "title": random.choice([
                    "動詞時態錯誤", "冠詞使用錯誤", "介詞搭配錯誤",
                    "單複數形式錯誤", "語序錯誤", "動詞形式錯誤"
                ]),
                "description": random.choice([
                    "注意動詞時態的一致性", "缺少必要的冠詞",
                    "介詞搭配不當", "名詞單複數形式錯誤",
                    "英文語序與中文不同", "動詞形式需要調整"
                ]),
                "error_category": random.choice([
                    "systematic", "singular", "better", "other"
                ]),
                "examples": [
                    random.choice([
                        "I went (not go) yesterday",
                        "the book (not book)",
                        "interested in (not interested on)", 
                        "books (not book)",
                        "I like apples (not like I apples)",
                        "he runs (not he run)"
                    ])
                ]
            } for _ in range(random.randint(1, 3))
        ]
    )
    
    suggestions = factory.LazyFunction(
        lambda: random.sample([
            "Review past tense formation",
            "Study article usage rules", 
            "Practice preposition collocations",
            "Check subject-verb agreement",
            "Pay attention to word order",
            "Review irregular verb forms"
        ], k=random.randint(1, 3))
    )
    
    corrected_answer = factory.LazyAttribute(
        lambda obj: "I went to the library yesterday." if not obj.is_correct
        else None
    )


class AIReviewQuestionFactory(factory.Factory):
    """AI 複習題目生成回應工廠"""
    
    class Meta:
        model = dict
    
    chinese_sentence = factory.Sequence(
        lambda n: [
            "我昨天完成了作業。",
            "她每天練習鋼琴。",
            "我們正在準備考試。",
            "他喜歡看英文電影。",
            "老師講解得很清楚。"
        ][n % 5]
    )
    
    target_knowledge_points = factory.LazyFunction(
        lambda: random.sample([
            "past_tense", "homework_vocabulary", "completion",
            "daily_routine", "musical_instrument", "practice",
            "present_continuous", "exam_preparation", "group_activity",
            "preference_expression", "entertainment", "language_learning",
            "adverb_usage", "teaching_vocabulary", "clarity"
        ], k=random.randint(1, 2))
    )
    
    focus_areas = factory.LazyFunction(
        lambda: random.sample([
            "時態一致性", "動詞形式", "冠詞使用",
            "介詞搭配", "語序調整", "詞彙選擇"
        ], k=random.randint(1, 2))
    )
    
    hints = factory.LazyFunction(
        lambda: random.sample([
            "注意動詞的過去式形式",
            "記得添加適當的冠詞",
            "檢查介詞的使用",
            "確認主謂一致",
            "注意英文的語序"
        ], k=random.randint(1, 2))
    )


class LLMInteractionFactory(factory.Factory):
    """LLM 互動記錄工廠（用於調試）"""
    
    class Meta:
        model = dict
    
    prompt = factory.LazyFunction(
        lambda: random.choice([
            "請將以下中文句子翻譯成英文：我昨天去了圖書館。",
            "請生成一個中文句子用於英文翻譯練習，難度：中等。",
            "請批改以下英文翻譯：I go library yesterday."
        ])
    )
    
    response = factory.LazyAttribute(
        lambda obj: {
            "chinese_sentence": "我昨天去了圖書館。",
            "knowledge_points": ["past_tense", "location"]
        } if "生成" in obj.prompt else {
            "is_correct": False,
            "feedback": "時態錯誤",
            "knowledge_points": [{"title": "過去式", "category": "systematic"}]
        }
    )
    
    model_name = factory.LazyFunction(
        lambda: random.choice(["gemini-2.5-flash", "gemini-2.5-pro"])
    )
    
    temperature = factory.LazyFunction(lambda: random.choice([0.7, 1.0, 1.2]))
    
    timestamp = factory.LazyFunction(lambda: datetime.now().isoformat())
    
    token_count = factory.LazyFunction(lambda: random.randint(50, 500))
    
    response_time = factory.LazyFunction(lambda: random.uniform(0.5, 3.0))


class AIResponseTestDataBuilder:
    """AI 回應測試數據建構器"""
    
    def __init__(self):
        self.data = {}
    
    def correct_grading(self):
        """設置為正確的批改結果"""
        self.data['is_correct'] = True
        self.data['score'] = random.randint(90, 100)
        self.data['feedback'] = "Excellent translation!"
        self.data['knowledge_points'] = []
        return self
    
    def incorrect_grading(self, error_count: int = 1):
        """設置為錯誤的批改結果"""
        self.data['is_correct'] = False
        self.data['score'] = random.randint(40, 80)
        self.data['feedback'] = "Please review the following points:"
        
        error_types = [
            {
                "title": "動詞時態錯誤",
                "description": "應使用過去式",
                "error_category": "systematic"
            },
            {
                "title": "冠詞缺失",
                "description": "名詞前應加定冠詞",
                "error_category": "systematic"
            },
            {
                "title": "介詞錯誤",
                "description": "介詞搭配不當",
                "error_category": "singular"
            }
        ]
        
        self.data['knowledge_points'] = random.sample(error_types, error_count)
        return self
    
    def with_model(self, model_name: str):
        """設置使用的模型"""
        self.data['model_name'] = model_name
        return self
    
    def with_knowledge_points(self, points: List[str]):
        """設置知識點（用於題目生成）"""
        self.data['knowledge_points'] = points
        return self
    
    def build_grading_response(self) -> Dict[str, Any]:
        """建構批改回應"""
        return AIGradingResponseFactory.build(**self.data)
    
    def build_question_response(self) -> Dict[str, Any]:
        """建構題目生成回應"""
        return AIGenerateQuestionFactory.build(**self.data)


def create_successful_grading_response() -> Dict[str, Any]:
    """創建成功的批改回應"""
    return (AIResponseTestDataBuilder()
            .correct_grading()
            .build_grading_response())


def create_failed_grading_response(error_count: int = 2) -> Dict[str, Any]:
    """創建失敗的批改回應"""
    return (AIResponseTestDataBuilder()
            .incorrect_grading(error_count)
            .build_grading_response())


def create_question_generation_response(difficulty: str = "medium") -> Dict[str, Any]:
    """創建題目生成回應"""
    return AIGenerateQuestionFactory.build(difficulty=difficulty)


def create_llm_interaction_log(interaction_type: str = "grading") -> Dict[str, Any]:
    """創建 LLM 互動日志"""
    if interaction_type == "grading":
        prompt = "請批改以下英文翻譯：I go library yesterday."
        response = create_failed_grading_response()
    elif interaction_type == "generation":
        prompt = "請生成一個中文句子用於英文翻譯練習。"
        response = create_question_generation_response()
    else:
        prompt = "請生成複習題目。"
        response = AIReviewQuestionFactory.build()
    
    return LLMInteractionFactory.build(
        prompt=prompt,
        response=response
    )