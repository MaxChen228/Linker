"""
知識點測試數據工廠
提供各種知識點測試數據的生成和管理
"""

import factory
from datetime import datetime, timedelta
from typing import List, Optional
import random

from core.knowledge import KnowledgePoint, OriginalError, ReviewExample
from core.error_types import ErrorCategory


class OriginalErrorFactory(factory.Factory):
    """原始錯誤測試數據工廠"""
    
    class Meta:
        model = OriginalError
    
    chinese_sentence = factory.Sequence(
        lambda n: [
            "我昨天去了圖書館。",
            "她正在學習中文。", 
            "我們明天要開會。",
            "他每天早上跑步。",
            "這本書很有趣。",
            "我喜歡吃中國菜。",
            "天氣今天很好。",
            "我在公司工作。",
            "老師講課很清楚。",
            "學生們正在考試。"
        ][n % 10]
    )
    
    user_answer = factory.Sequence(
        lambda n: [
            "I go to library yesterday.",
            "She studying Chinese.",
            "We will meeting tomorrow.",
            "He run every morning.",
            "This book very interesting.",
            "I like eat Chinese food.",
            "Weather today very good.",
            "I work in company.",
            "Teacher teach very clear.",
            "Students taking exam."
        ][n % 10]
    )
    
    correct_answer = factory.Sequence(
        lambda n: [
            "I went to the library yesterday.",
            "She is studying Chinese.",
            "We will have a meeting tomorrow.", 
            "He runs every morning.",
            "This book is very interesting.",
            "I like eating Chinese food.",
            "The weather is very good today.",
            "I work in a company.",
            "The teacher teaches very clearly.",
            "The students are taking an exam."
        ][n % 10]
    )
    
    timestamp = factory.LazyFunction(
        lambda: datetime.now().isoformat()
    )


class ReviewExampleFactory(factory.Factory):
    """複習例句測試數據工廠"""
    
    class Meta:
        model = ReviewExample
    
    chinese_sentence = factory.Sequence(
        lambda n: [
            "我上週買了一本書。",
            "他們正在討論問題。",
            "老師已經批改作業。",
            "學生明天交報告。",
            "我們經常去那家餐廳。"
        ][n % 5]
    )
    
    user_answer = factory.Sequence(
        lambda n: [
            "I bought a book last week.",
            "They are discussing the problem.",
            "The teacher has graded the homework.",
            "Students will submit the report tomorrow.",
            "We often go to that restaurant."
        ][n % 5]
    )
    
    correct_answer = factory.Sequence(
        lambda n: [
            "I bought a book last week.",
            "They are discussing the problem.",
            "The teacher has graded the homework.",
            "Students will submit the report tomorrow.",
            "We often go to that restaurant."
        ][n % 5]
    )
    
    timestamp = factory.LazyFunction(
        lambda: datetime.now().isoformat()
    )
    
    is_correct = factory.LazyFunction(lambda: random.choice([True, False]))


class KnowledgePointFactory(factory.Factory):
    """知識點測試數據工廠"""
    
    class Meta:
        model = KnowledgePoint
    
    id = factory.Sequence(lambda n: n + 1)
    
    key_point = factory.Sequence(
        lambda n: [
            "動詞時態錯誤: go -> went",
            "冠詞使用錯誤: library -> the library",
            "介詞搭配錯誤: interested on -> interested in", 
            "單複數形式錯誤: book -> books",
            "語序錯誤: very much I like -> I like very much",
            "動詞形式錯誤: he run -> he runs",
            "形容詞比較級錯誤: more better -> better",
            "否定句結構錯誤: I no like -> I don't like",
            "疑問句結構錯誤: You are student? -> Are you a student?",
            "被動語態錯誤: The book read by me -> The book was read by me"
        ][n % 10]
    )
    
    category = factory.LazyFunction(
        lambda: random.choice(list(ErrorCategory))
    )
    
    subtype = factory.LazyFunction(
        lambda: random.choice([
            "verb_tense", "article_missing", "preposition_error",
            "plural_form", "word_order", "verb_form",
            "comparative", "negative", "question", "passive"
        ])
    )
    
    explanation = factory.LazyAttribute(
        lambda obj: f"錯誤說明：{obj.key_point} 的詳細解釋"
    )
    
    original_phrase = factory.Sequence(
        lambda n: [
            "I go to library",
            "She studying hard",
            "I interested on music",
            "I have two book",
            "I very much like",
            "He run fast",
            "This is more better",
            "I no like coffee",
            "You are student?",
            "The book read by me"
        ][n % 10]
    )
    
    correction = factory.Sequence(
        lambda n: [
            "I went to the library",
            "She is studying hard",
            "I am interested in music",
            "I have two books",
            "I like it very much",
            "He runs fast",
            "This is better",
            "I don't like coffee",
            "Are you a student?",
            "The book was read by me"
        ][n % 10]
    )
    
    original_error = factory.SubFactory(OriginalErrorFactory)
    review_examples = factory.List([])
    
    correct_count = factory.LazyFunction(lambda: random.randint(0, 10))
    mistake_count = factory.LazyFunction(lambda: random.randint(1, 5))
    
    mastery_level = factory.LazyAttribute(
        lambda obj: obj.correct_count / (obj.correct_count + obj.mistake_count)
        if (obj.correct_count + obj.mistake_count) > 0 else 0.0
    )
    
    created_at = factory.LazyFunction(
        lambda: (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
    )
    
    last_seen = factory.LazyFunction(lambda: datetime.now().isoformat())
    
    next_review = factory.LazyFunction(
        lambda: (datetime.now() + timedelta(days=random.randint(1, 7))).isoformat()
    )


class KnowledgePointTestDataBuilder:
    """知識點測試數據建構器，支援鏈式調用"""
    
    def __init__(self):
        self.data = {}
    
    def with_id(self, id: int):
        self.data['id'] = id
        return self
    
    def with_key_point(self, key_point: str):
        self.data['key_point'] = key_point
        return self
    
    def with_category(self, category):
        self.data['category'] = category
        return self
    
    def with_mastery_level(self, level: float):
        self.data['mastery_level'] = level
        return self
    
    def with_review_examples(self, count: int):
        self.data['review_examples'] = ReviewExampleFactory.build_batch(count)
        return self
    
    def needs_review(self):
        """設置為需要複習的知識點"""
        self.data['next_review'] = (
            datetime.now() - timedelta(days=1)
        ).isoformat()
        self.data['mastery_level'] = 0.3  # 低掌握度
        return self
    
    def mastered(self):
        """設置為已掌握的知識點"""
        self.data['mastery_level'] = 0.8
        self.data['correct_count'] = 8
        self.data['mistake_count'] = 2
        return self
    
    def build(self) -> KnowledgePoint:
        return KnowledgePointFactory.build(**self.data)


def create_systematic_knowledge_point() -> KnowledgePoint:
    """創建系統性錯誤知識點"""
    return (KnowledgePointTestDataBuilder()
            .with_category(ErrorCategory.SYSTEMATIC)
            .with_key_point("動詞時態一致性: go -> went")
            .build())


def create_singular_knowledge_point() -> KnowledgePoint:
    """創建單一性錯誤知識點"""
    return (KnowledgePointTestDataBuilder()
            .with_category(ErrorCategory.ISOLATED)
            .with_key_point("特殊動詞變化: run -> ran")
            .build())


def create_knowledge_points_for_review(count: int = 5) -> List[KnowledgePoint]:
    """創建需要複習的知識點列表"""
    return [
        KnowledgePointTestDataBuilder().needs_review().build()
        for _ in range(count)
    ]


def create_mastered_knowledge_points(count: int = 3) -> List[KnowledgePoint]:
    """創建已掌握的知識點列表"""
    return [
        KnowledgePointTestDataBuilder().mastered().build()
        for _ in range(count)
    ]


def create_mixed_knowledge_points(total: int = 10) -> List[KnowledgePoint]:
    """創建混合狀態的知識點列表"""
    points = []
    
    # 30% 需要複習
    review_count = int(total * 0.3)
    points.extend(create_knowledge_points_for_review(review_count))
    
    # 40% 已掌握  
    mastered_count = int(total * 0.4)
    points.extend(create_mastered_knowledge_points(mastered_count))
    
    # 30% 普通狀態
    normal_count = total - review_count - mastered_count
    points.extend(KnowledgePointFactory.build_batch(normal_count))
    
    return points