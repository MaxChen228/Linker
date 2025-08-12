"""
用戶輸入測試數據工廠
提供各種用戶輸入場景的測試數據
"""

import factory
from typing import Dict, List, Any, Optional
import random


class UserTranslationInputFactory(factory.Factory):
    """用戶翻譯輸入測試數據工廠"""
    
    class Meta:
        model = dict
    
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
            # 各種典型錯誤模式
            "I go to library yesterday.",  # 時態錯誤 + 冠詞缺失
            "She studying Chinese.",        # 缺少 be 動詞
            "We will meeting tomorrow.",    # 動詞形式錯誤
            "He run every morning.",        # 第三人稱單數錯誤
            "This book very interesting.",  # 缺少 be 動詞
            "I like eat Chinese food.",     # 動名詞錯誤
            "Weather today very good.",     # 語序和 be 動詞錯誤
            "I work in company.",           # 冠詞缺失
            "Teacher teach very clear.",    # 冠詞缺失 + 副詞錯誤
            "Students taking exam."         # 冠詞缺失 + 進行時錯誤
        ][n % 10]
    )
    
    practice_mode = factory.LazyFunction(
        lambda: random.choice(["new", "review"])
    )
    
    session_id = factory.Sequence(lambda n: f"session_{n:04d}")


class UserInputVariationFactory(factory.Factory):
    """用戶輸入變化測試數據工廠"""
    
    class Meta:
        model = dict
    
    @factory.LazyAttribute
    def input_variations(obj):
        """生成不同類型的用戶輸入"""
        base_sentence = "I went to the library yesterday."
        
        variations = {
            "perfect": base_sentence,
            "minor_typo": "I went to the libary yesterday.",  # 拼寫錯誤
            "grammar_error": "I go to library yesterday.",    # 語法錯誤
            "missing_article": "I went to library yesterday.", # 冠詞缺失
            "wrong_tense": "I will go to library yesterday.", # 時態錯誤
            "word_order": "Yesterday I went to library.",      # 語序不佳
            "incomplete": "I went to",                         # 未完成
            "overly_complex": "Yesterday, I went to the public library in order to read some books.", # 過度複雜
            "informal": "I went 2 the library yesterday.",     # 非正式表達
            "chinese_thinking": "Yesterday I go library.",     # 中式英語思維
        }
        
        return variations


class CommonErrorPatternFactory(factory.Factory):
    """常見錯誤模式測試數據工廠"""
    
    class Meta:
        model = dict
    
    error_type = factory.LazyFunction(
        lambda: random.choice([
            "tense_error", "article_missing", "preposition_error",
            "subject_verb_disagreement", "word_order", "gerund_infinitive",
            "plural_form", "spelling", "vocabulary_choice"
        ])
    )
    
    @factory.LazyAttribute
    def examples(obj):
        """根據錯誤類型生成例子"""
        error_examples = {
            "tense_error": [
                {"wrong": "I go there yesterday.", "correct": "I went there yesterday."},
                {"wrong": "She will came tomorrow.", "correct": "She will come tomorrow."},
            ],
            "article_missing": [
                {"wrong": "I go to school.", "correct": "I go to the school."},
                {"wrong": "He is teacher.", "correct": "He is a teacher."},
            ],
            "preposition_error": [
                {"wrong": "I'm interested on music.", "correct": "I'm interested in music."},
                {"wrong": "We arrived to Beijing.", "correct": "We arrived in Beijing."},
            ],
            "subject_verb_disagreement": [
                {"wrong": "She don't like coffee.", "correct": "She doesn't like coffee."},
                {"wrong": "They was happy.", "correct": "They were happy."},
            ],
            "word_order": [
                {"wrong": "I like very much apples.", "correct": "I like apples very much."},
                {"wrong": "Always I get up early.", "correct": "I always get up early."},
            ],
            "gerund_infinitive": [
                {"wrong": "I like swim.", "correct": "I like swimming."},
                {"wrong": "I want swimming.", "correct": "I want to swim."},
            ],
        }
        
        return error_examples.get(obj.error_type, [])


class UserInputTestDataBuilder:
    """用戶輸入測試數據建構器"""
    
    def __init__(self):
        self.data = {}
    
    def with_sentence(self, chinese: str, user_answer: str):
        """設置句子和用戶答案"""
        self.data['chinese_sentence'] = chinese
        self.data['user_answer'] = user_answer
        return self
    
    def with_mode(self, mode: str):
        """設置練習模式"""
        self.data['practice_mode'] = mode
        return self
    
    def with_session(self, session_id: str):
        """設置會話 ID"""
        self.data['session_id'] = session_id
        return self
    
    def perfect_answer(self):
        """完美答案"""
        self.data['user_answer'] = "I went to the library yesterday."
        return self
    
    def with_grammar_error(self):
        """包含語法錯誤"""
        self.data['user_answer'] = "I go to library yesterday."
        return self
    
    def with_typo(self):
        """包含拼寫錯誤"""
        self.data['user_answer'] = "I went to the libary yesterday."
        return self
    
    def incomplete(self):
        """不完整的答案"""
        self.data['user_answer'] = "I went to"
        return self
    
    def build(self) -> Dict[str, Any]:
        return UserTranslationInputFactory.build(**self.data)


def create_perfect_user_input() -> Dict[str, Any]:
    """創建完美的用戶輸入"""
    return (UserInputTestDataBuilder()
            .with_sentence("我昨天去了圖書館。", "I went to the library yesterday.")
            .build())


def create_error_user_input(error_type: str = "grammar") -> Dict[str, Any]:
    """創建包含錯誤的用戶輸入"""
    builder = UserInputTestDataBuilder()
    
    if error_type == "grammar":
        return builder.with_grammar_error().build()
    elif error_type == "typo":
        return builder.with_typo().build()
    elif error_type == "incomplete":
        return builder.incomplete().build()
    else:
        return builder.build()


def create_batch_user_inputs(count: int = 10) -> List[Dict[str, Any]]:
    """創建批量用戶輸入"""
    inputs = []
    
    for i in range(count):
        # 70% 包含錯誤，30% 完美答案
        if random.random() < 0.7:
            error_type = random.choice(["grammar", "typo", "incomplete"])
            input_data = create_error_user_input(error_type)
        else:
            input_data = create_perfect_user_input()
        
        input_data['session_id'] = f"batch_session_{i//5}"  # 每5個一組
        inputs.append(input_data)
    
    return inputs


def create_review_mode_inputs(knowledge_points: List[str]) -> List[Dict[str, Any]]:
    """創建複習模式的用戶輸入"""
    inputs = []
    
    sentences_map = {
        "past_tense": ("我昨天看電影了。", "I watched a movie yesterday."),
        "present_continuous": ("她正在讀書。", "She is reading a book."),
        "article_usage": ("我去學校。", "I go to school."),
        "preposition": ("我對音樂感興趣。", "I'm interested in music."),
    }
    
    for kp in knowledge_points:
        if kp in sentences_map:
            chinese, correct = sentences_map[kp]
            # 故意加入相關錯誤
            if kp == "past_tense":
                user_answer = "I watch a movie yesterday."
            elif kp == "present_continuous":
                user_answer = "She reading a book."
            elif kp == "article_usage":
                user_answer = "I go to school."  # 可能需要定冠詞
            elif kp == "preposition":
                user_answer = "I'm interested on music."
            else:
                user_answer = correct
            
            input_data = (UserInputTestDataBuilder()
                         .with_sentence(chinese, user_answer)
                         .with_mode("review")
                         .build())
            inputs.append(input_data)
    
    return inputs


def create_progressive_difficulty_inputs() -> List[Dict[str, Any]]:
    """創建漸進式難度的用戶輸入"""
    easy_inputs = [
        {"chinese": "我是學生。", "user": "I am student.", "errors": ["article"]},
        {"chinese": "今天很熱。", "user": "Today very hot.", "errors": ["be_verb"]},
    ]
    
    medium_inputs = [
        {"chinese": "我昨天去了圖書館。", "user": "I go to library yesterday.", "errors": ["tense", "article"]},
        {"chinese": "她正在學習中文。", "user": "She studying Chinese.", "errors": ["auxiliary_verb"]},
    ]
    
    hard_inputs = [
        {"chinese": "如果明天不下雨，我們就去公園。", "user": "If tomorrow no rain, we go to park.", "errors": ["conditional", "article", "tense"]},
        {"chinese": "我已經完成了作業，但還沒有檢查。", "user": "I already finish homework, but not check yet.", "errors": ["perfect_tense", "article"]},
    ]
    
    all_inputs = []
    
    for difficulty, inputs in [("easy", easy_inputs), ("medium", medium_inputs), ("hard", hard_inputs)]:
        for item in inputs:
            input_data = (UserInputTestDataBuilder()
                         .with_sentence(item["chinese"], item["user"])
                         .build())
            input_data["difficulty"] = difficulty
            input_data["expected_errors"] = item["errors"]
            all_inputs.append(input_data)
    
    return all_inputs