"""
錯誤類型定義 - 核心分類系統
完全重新設計的四級分類體系
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCategory(Enum):
    """主要錯誤類別"""

    SYSTEMATIC = "systematic"  # 系統性錯誤
    ISOLATED = "isolated"  # 單一性錯誤
    ENHANCEMENT = "enhancement"  # 可以更好
    OTHER = "other"  # 其他錯誤

    @classmethod
    def from_string(cls, value: str) -> "ErrorCategory":
        """從字符串轉換"""
        mapping = {
            "systematic": cls.SYSTEMATIC,
            "isolated": cls.ISOLATED,
            "enhancement": cls.ENHANCEMENT,
            "other": cls.OTHER,
        }
        return mapping.get(value, cls.OTHER)

    def to_chinese(self) -> str:
        """轉換為中文名稱"""
        names = {
            self.SYSTEMATIC: "系統性錯誤",
            self.ISOLATED: "單一性錯誤",
            self.ENHANCEMENT: "可以更好",
            self.OTHER: "其他錯誤",
        }
        return names[self]

    def get_priority(self) -> int:
        """獲取學習優先級（1最高，4最低）"""
        priorities = {self.SYSTEMATIC: 1, self.ISOLATED: 2, self.OTHER: 3, self.ENHANCEMENT: 4}
        return priorities[self]

    def get_review_multiplier(self) -> float:
        """獲取複習間隔倍數"""
        multipliers = {
            self.SYSTEMATIC: 0.8,  # 更頻繁複習
            self.ISOLATED: 1.0,  # 標準複習
            self.OTHER: 1.0,  # 標準複習
            self.ENHANCEMENT: 1.5,  # 可以延後
        }
        return multipliers[self]


@dataclass
class ErrorSubtype:
    """錯誤子類型"""

    name: str
    chinese_name: str
    category: ErrorCategory
    keywords: list[str]
    examples: list[str]

    def matches(self, text: str) -> bool:
        """檢查文本是否匹配此子類型"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)


class ErrorTypeSystem:
    """錯誤類型系統 - 管理所有錯誤分類"""

    # 系統性錯誤子類型
    SYSTEMATIC_SUBTYPES = [
        ErrorSubtype(
            name="verb_conjugation",
            chinese_name="動詞變化",
            category=ErrorCategory.SYSTEMATIC,
            keywords=[
                "第三人稱單數",
                "動詞變化",
                "加s",
                "加es",
                "動詞形式",
                "third person",
                "singular",
                "verb form",
            ],
            examples=["He goes (not go)", "She plays (not play)"],
        ),
        ErrorSubtype(
            name="tense",
            chinese_name="時態",
            category=ErrorCategory.SYSTEMATIC,
            keywords=[
                "時態",
                "過去式",
                "現在式",
                "完成式",
                "進行式",
                "tense",
                "past",
                "present",
                "perfect",
                "continuous",
            ],
            examples=["I went (not go)", "has done (not have do)"],
        ),
        ErrorSubtype(
            name="voice",
            chinese_name="語態",
            category=ErrorCategory.SYSTEMATIC,
            keywords=["主動", "被動", "語態", "被動語態", "active", "passive", "voice"],
            examples=["was done (not did)", "is written (not writes)"],
        ),
        ErrorSubtype(
            name="agreement",
            chinese_name="主謂一致",
            category=ErrorCategory.SYSTEMATIC,
            keywords=["主詞動詞一致", "單複數", "主謂一致", "subject-verb", "agreement", "plural"],
            examples=["They are (not is)", "The books are (not is)"],
        ),
    ]

    # 單一性錯誤子類型
    ISOLATED_SUBTYPES = [
        ErrorSubtype(
            name="vocabulary",
            chinese_name="詞彙選擇",
            category=ErrorCategory.ISOLATED,
            keywords=[
                "單字",
                "詞彙",
                "用詞",
                "翻譯",
                "詞義",
                "vocabulary",
                "word choice",
                "meaning",
            ],
            examples=["interested (not interesting)", "affect (not effect)"],
        ),
        ErrorSubtype(
            name="collocation",
            chinese_name="搭配詞",
            category=ErrorCategory.ISOLATED,
            keywords=["搭配詞", "片語", "慣用語", "固定搭配", "collocation", "phrase", "idiom"],
            examples=["make a decision", "on the other hand"],
        ),
        ErrorSubtype(
            name="preposition",
            chinese_name="介係詞",
            category=ErrorCategory.ISOLATED,
            keywords=[
                "介詞",
                "介係詞",
                "介系詞",
                "前置詞",
                "preposition",
                "at",
                "in",
                "on",
                "by",
                "for",
            ],
            examples=["interested in", "good at", "depend on"],
        ),
        ErrorSubtype(
            name="spelling",
            chinese_name="拼寫",
            category=ErrorCategory.ISOLATED,
            keywords=["拼寫", "拼字", "拼錯", "字母", "spelling", "misspell", "typo"],
            examples=["receive (not recieve)", "necessary (not neccessary)"],
        ),
    ]

    # 可以更好子類型
    ENHANCEMENT_SUBTYPES = [
        ErrorSubtype(
            name="naturalness",
            chinese_name="自然度",
            category=ErrorCategory.ENHANCEMENT,
            keywords=[
                "更自然",
                "更道地",
                "更流暢",
                "不夠自然",
                "生硬",
                "natural",
                "native",
                "fluent",
                "awkward",
            ],
            examples=["How are you doing? (vs How do you do?)"],
        ),
        ErrorSubtype(
            name="style",
            chinese_name="風格",
            category=ErrorCategory.ENHANCEMENT,
            keywords=[
                "風格",
                "正式",
                "非正式",
                "語氣",
                "委婉",
                "style",
                "formal",
                "informal",
                "tone",
            ],
            examples=["Could you please... (more polite)"],
        ),
    ]

    # 其他錯誤子類型
    OTHER_SUBTYPES = [
        ErrorSubtype(
            name="omission",
            chinese_name="遺漏",
            category=ErrorCategory.OTHER,
            keywords=["遺漏", "漏譯", "缺少", "忘記", "omit", "miss", "forget"],
            examples=["Missing translation of key information"],
        ),
        ErrorSubtype(
            name="misunderstanding",
            chinese_name="理解偏差",
            category=ErrorCategory.OTHER,
            keywords=["理解錯誤", "誤解", "偏差", "misunderstand", "wrong meaning"],
            examples=["Complete misinterpretation of the sentence"],
        ),
    ]

    @classmethod
    def get_all_subtypes(cls) -> list[ErrorSubtype]:
        """獲取所有子類型"""
        return (
            cls.SYSTEMATIC_SUBTYPES
            + cls.ISOLATED_SUBTYPES
            + cls.ENHANCEMENT_SUBTYPES
            + cls.OTHER_SUBTYPES
        )

    @classmethod
    def classify(cls, key_point: str, explanation: str, severity: str = "major") -> tuple:
        """
        分類錯誤
        返回: (ErrorCategory, subtype_name)
        """
        combined_text = f"{key_point} {explanation}".lower()

        # 優先檢查是否為enhancement（通常severity為minor）
        if severity == "minor" or any(
            kw in combined_text
            for kw in [
                "更自然",
                "更道地",
                "更好",
                "不夠自然",
                "生硬",
                "more natural",
                "better",
                "awkward",
            ]
        ):
            # 找出具體的enhancement子類型
            for subtype in cls.ENHANCEMENT_SUBTYPES:
                if subtype.matches(combined_text):
                    return ErrorCategory.ENHANCEMENT, subtype.name
            return ErrorCategory.ENHANCEMENT, "style"

        # 檢查系統性錯誤
        for subtype in cls.SYSTEMATIC_SUBTYPES:
            if subtype.matches(combined_text):
                return ErrorCategory.SYSTEMATIC, subtype.name

        # 檢查單一性錯誤
        for subtype in cls.ISOLATED_SUBTYPES:
            if subtype.matches(combined_text):
                return ErrorCategory.ISOLATED, subtype.name

        # 檢查其他錯誤
        for subtype in cls.OTHER_SUBTYPES:
            if subtype.matches(combined_text):
                return ErrorCategory.OTHER, subtype.name

        # 默認為其他錯誤
        return ErrorCategory.OTHER, "unclassified"

    @classmethod
    def get_subtype_by_name(cls, name: str) -> Optional[ErrorSubtype]:
        """根據名稱獲取子類型"""
        for subtype in cls.get_all_subtypes():
            if subtype.name == name:
                return subtype
        return None

    @classmethod
    def get_learning_advice(cls, category: ErrorCategory, subtype_name: str) -> str:
        """獲取學習建議"""
        subtype = cls.get_subtype_by_name(subtype_name)

        if category == ErrorCategory.SYSTEMATIC:
            return f"建議系統性學習{subtype.chinese_name if subtype else '文法規則'}，掌握後可避免同類錯誤"
        if category == ErrorCategory.ISOLATED:
            return (
                f"需要個別記憶{subtype.chinese_name if subtype else '此知識點'}，建議製作記憶卡片"
            )
        if category == ErrorCategory.ENHANCEMENT:
            return "你的基礎不錯！多接觸原文材料可以讓表達更自然"
        return "注意理解題意，確保翻譯完整準確"
