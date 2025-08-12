"""
練習記錄測試數據工廠
提供各種練習記錄測試數據的生成和管理
"""

import factory
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random
import uuid


class PracticeRecordFactory(factory.Factory):
    """練習記錄測試數據工廠"""
    
    class Meta:
        model = dict  # 練習記錄使用字典格式
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    
    chinese_sentence = factory.Sequence(
        lambda n: [
            "我昨天看了一部電影。",
            "她正在準備考試。",
            "我們計劃下週去旅行。", 
            "他每天騎自行車上班。",
            "這家餐廳的食物很美味。",
            "老師正在黑板上寫字。",
            "學生們在圖書館學習。",
            "我媽媽正在廚房做飯。",
            "天氣預報說明天會下雨。",
            "我們應該保護環境。"
        ][n % 10]
    )
    
    user_answer = factory.Sequence(
        lambda n: [
            "I watch a movie yesterday.",
            "She preparing for exam.",
            "We plan go travel next week.",
            "He ride bicycle to work everyday.",
            "This restaurant food very delicious.",
            "Teacher writing on blackboard.",
            "Students study in library.",
            "My mother cooking in kitchen.",
            "Weather report say tomorrow will rain.",
            "We should protect environment."
        ][n % 10]
    )
    
    correct_answer = factory.Sequence(
        lambda n: [
            "I watched a movie yesterday.",
            "She is preparing for the exam.",
            "We plan to go traveling next week.",
            "He rides his bicycle to work every day.",
            "The food at this restaurant is very delicious.",
            "The teacher is writing on the blackboard.",
            "Students are studying in the library.",
            "My mother is cooking in the kitchen.",
            "The weather report says it will rain tomorrow.",
            "We should protect the environment."
        ][n % 10]
    )
    
    is_correct = factory.LazyFunction(lambda: random.choice([True, False]))
    
    score = factory.LazyAttribute(
        lambda obj: random.randint(85, 100) if obj.is_correct 
        else random.randint(30, 80)
    )
    
    feedback = factory.LazyAttribute(
        lambda obj: "答案正確，表達清晰！" if obj.is_correct
        else "需要注意時態和冠詞的使用。"
    )
    
    knowledge_points = factory.LazyFunction(
        lambda: random.sample([
            "past_tense", "present_continuous", "article_usage",
            "preposition", "word_order", "plural_form",
            "future_tense", "modal_verbs", "gerund"
        ], k=random.randint(1, 3))
    )
    
    practice_mode = factory.LazyFunction(
        lambda: random.choice(["new", "review"])
    )
    
    difficulty = factory.LazyFunction(
        lambda: random.choice(["easy", "medium", "hard"])
    )
    
    timestamp = factory.LazyFunction(
        lambda: datetime.now().isoformat()
    )
    
    session_id = factory.LazyFunction(lambda: str(uuid.uuid4())[:8])


class PracticeSessionFactory(factory.Factory):
    """練習會話測試數據工廠"""
    
    class Meta:
        model = dict
    
    session_id = factory.LazyFunction(lambda: str(uuid.uuid4())[:8])
    start_time = factory.LazyFunction(lambda: datetime.now().isoformat())
    end_time = factory.LazyAttribute(
        lambda obj: (datetime.fromisoformat(obj.start_time) + 
                    timedelta(minutes=random.randint(10, 60))).isoformat()
    )
    
    total_questions = factory.LazyFunction(lambda: random.randint(5, 20))
    correct_answers = factory.LazyAttribute(
        lambda obj: random.randint(0, obj.total_questions)
    )
    
    accuracy = factory.LazyAttribute(
        lambda obj: obj.correct_answers / obj.total_questions 
        if obj.total_questions > 0 else 0.0
    )
    
    practice_mode = factory.LazyFunction(
        lambda: random.choice(["new", "review", "mixed"])
    )


class PracticeTestDataBuilder:
    """練習記錄測試數據建構器"""
    
    def __init__(self):
        self.data = {}
    
    def correct_answer(self):
        """設置為正確答案"""
        self.data['is_correct'] = True
        self.data['score'] = random.randint(85, 100)
        self.data['feedback'] = "答案正確！"
        return self
    
    def incorrect_answer(self):
        """設置為錯誤答案"""
        self.data['is_correct'] = False
        self.data['score'] = random.randint(30, 80)
        self.data['feedback'] = "需要改進"
        return self
    
    def with_mode(self, mode: str):
        """設置練習模式"""
        self.data['practice_mode'] = mode
        return self
    
    def with_knowledge_points(self, points: List[str]):
        """設置知識點"""
        self.data['knowledge_points'] = points
        return self
    
    def with_difficulty(self, level: str):
        """設置難度"""
        self.data['difficulty'] = level
        return self
    
    def with_timestamp(self, timestamp: str):
        """設置時間戳"""
        self.data['timestamp'] = timestamp
        return self
    
    def build(self) -> Dict[str, Any]:
        return PracticeRecordFactory.build(**self.data)


def create_correct_practice_record() -> Dict[str, Any]:
    """創建正確的練習記錄"""
    return (PracticeTestDataBuilder()
            .correct_answer()
            .with_mode("new")
            .build())


def create_incorrect_practice_record() -> Dict[str, Any]:
    """創建錯誤的練習記錄"""
    return (PracticeTestDataBuilder()
            .incorrect_answer()
            .with_mode("new")
            .build())


def create_review_practice_record() -> Dict[str, Any]:
    """創建複習模式的練習記錄"""
    return (PracticeTestDataBuilder()
            .with_mode("review")
            .with_knowledge_points(["past_tense", "article"])
            .build())


def create_practice_history(days: int = 7) -> List[Dict[str, Any]]:
    """創建練習歷史記錄"""
    records = []
    
    for day in range(days):
        # 每天 3-8 個練習記錄
        daily_count = random.randint(3, 8)
        date = datetime.now() - timedelta(days=day)
        
        for _ in range(daily_count):
            record = PracticeRecordFactory.build()
            # 設置該天的時間
            record['timestamp'] = date.replace(
                hour=random.randint(9, 21),
                minute=random.randint(0, 59)
            ).isoformat()
            records.append(record)
    
    return sorted(records, key=lambda x: x['timestamp'])


def create_practice_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """根據練習記錄創建統計數據"""
    if not records:
        return {
            "total_questions": 0,
            "correct_answers": 0,
            "accuracy": 0.0,
            "total_sessions": 0,
            "avg_score": 0.0,
            "knowledge_point_stats": {}
        }
    
    total = len(records)
    correct = sum(1 for r in records if r.get('is_correct', False))
    total_score = sum(r.get('score', 0) for r in records)
    
    # 統計知識點
    knowledge_point_stats = {}
    for record in records:
        for kp in record.get('knowledge_points', []):
            if kp not in knowledge_point_stats:
                knowledge_point_stats[kp] = {"total": 0, "correct": 0}
            knowledge_point_stats[kp]["total"] += 1
            if record.get('is_correct', False):
                knowledge_point_stats[kp]["correct"] += 1
    
    # 計算知識點準確率
    for kp_stats in knowledge_point_stats.values():
        kp_stats["accuracy"] = (kp_stats["correct"] / kp_stats["total"] 
                               if kp_stats["total"] > 0 else 0.0)
    
    return {
        "total_questions": total,
        "correct_answers": correct,
        "accuracy": correct / total if total > 0 else 0.0,
        "total_sessions": len(set(r.get('session_id', '') for r in records)),
        "avg_score": total_score / total if total > 0 else 0.0,
        "knowledge_point_stats": knowledge_point_stats
    }