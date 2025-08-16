"""
錯誤類型定義模組

定義了應用程式中用於學習和反饋的核心錯誤分類系統。
此系統將使用者在翻譯練習中可能犯的錯誤分為四大類，並進一步細分亞型，
旨在提供更精確、更有針對性的學習建議和複習策略。

主要組件：
- `ErrorCategory` (Enum): 定義四種主要的錯誤類別，是整個分類系統的基礎。
- `ErrorSubtype` (dataclass): 定義具體的錯誤子類型，包含中英文名稱、關鍵字和範例。
- `ErrorTypeSystem`: 一個靜態類，集中管理所有的錯誤子類型，並提供分類和查詢的工具方法。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCategory(Enum):
    """
    定義四種主要的錯誤類別，用於對使用者的錯誤進行宏觀分類。

    - SYSTEMATIC: 系統性錯誤，通常與文法規則相關，可透過學習規則來系統性地改進。
    - ISOLATED: 單一性錯誤，通常是需要個別記憶的詞彙、片語或固定用法。
    - ENHANCEMENT: 可改進的錯誤，表示文法基本正確，但在表達上可以更自然、更道地。
    - OTHER: 其他無法歸入上述類別的錯誤。
    """

    SYSTEMATIC = "systematic"
    ISOLATED = "isolated"
    ENHANCEMENT = "enhancement"
    OTHER = "other"

    @classmethod
    def from_string(cls, value: str) -> "ErrorCategory":
        """從字串安全地轉換為 ErrorCategory 枚舉成員。"""
        return next((member for name, member in cls.__members__.items() if name.lower() == value.lower()), cls.OTHER)

    def to_chinese(self) -> str:
        """將錯誤類別轉換為對應的中文名稱。"""
        return {
            self.SYSTEMATIC: "系統性錯誤",
            self.ISOLATED: "單一性錯誤",
            self.ENHANCEMENT: "可以更好",
            self.OTHER: "其他錯誤",
        }[self]

    def get_priority(self) -> int:
        """獲取該類別錯誤的學習優先級（1 為最高）。"""
        return {self.SYSTEMATIC: 1, self.ISOLATED: 2, self.OTHER: 3, self.ENHANCEMENT: 4}[self]

    def get_review_multiplier(self) -> float:
        """獲取用於計算下次複習時間的間隔乘數。"""
        return {self.SYSTEMATIC: 0.8, self.ISOLATED: 1.0, self.OTHER: 1.0, self.ENHANCEMENT: 1.5}[self]


@dataclass
class ErrorSubtype:
    """定義一個具體的錯誤子類型。"""

    name: str
    chinese_name: str
    category: ErrorCategory
    keywords: list[str]
    examples: list[str]

    def matches(self, text: str) -> bool:
        """檢查給定的文本是否符合此子類型的關鍵字。"""
        return any(keyword.lower() in text.lower() for keyword in self.keywords)


class ErrorTypeSystem:
    """
    錯誤類型系統，管理所有錯誤的分類和子類型。
    這是一個靜態類，不應被實例化。
    """

    SYSTEMATIC_SUBTYPES = [
        ErrorSubtype(
            name="verb_conjugation", chinese_name="動詞變化", category=ErrorCategory.SYSTEMATIC,
            keywords=["第三人稱單數", "動詞變化", "動詞形式", "third person", "singular", "verb form"],
            examples=["He goes (not go)", "She plays (not play)"]
        ),
        ErrorSubtype(
            name="tense", chinese_name="時態", category=ErrorCategory.SYSTEMATIC,
            keywords=["時態", "過去式", "現在式", "完成式", "進行式", "tense", "past", "present", "perfect"],
            examples=["I went (not go)", "has done (not have do)"]
        ),
        ErrorSubtype(
            name="voice", chinese_name="語態", category=ErrorCategory.SYSTEMATIC,
            keywords=["主動", "被動", "語態", "被動語態", "active", "passive", "voice"],
            examples=["was done (not did)", "is written (not writes)"]
        ),
        ErrorSubtype(
            name="agreement", chinese_name="主謂一致", category=ErrorCategory.SYSTEMATIC,
            keywords=["主詞動詞一致", "單複數", "主謂一致", "subject-verb", "agreement", "plural"],
            examples=["They are (not is)", "The books are (not is)"]
        ),
    ]

    ISOLATED_SUBTYPES = [
        ErrorSubtype(
            name="vocabulary", chinese_name="詞彙選擇", category=ErrorCategory.ISOLATED,
            keywords=["單字", "詞彙", "用詞", "翻譯", "詞義", "vocabulary", "word choice"],
            examples=["interested (not interesting)", "affect (not effect)"]
        ),
        ErrorSubtype(
            name="collocation", chinese_name="搭配詞", category=ErrorCategory.ISOLATED,
            keywords=["搭配詞", "片語", "慣用語", "固定搭配", "collocation", "phrase", "idiom"],
            examples=["make a decision", "on the other hand"]
        ),
        ErrorSubtype(
            name="preposition", chinese_name="介係詞", category=ErrorCategory.ISOLATED,
            keywords=["介詞", "介係詞", "介系詞", "preposition", "at", "in", "on", "by", "for"],
            examples=["interested in", "good at", "depend on"]
        ),
        ErrorSubtype(
            name="spelling", chinese_name="拼寫", category=ErrorCategory.ISOLATED,
            keywords=["拼寫", "拼字", "拼錯", "字母", "spelling", "misspell", "typo"],
            examples=["receive (not recieve)", "necessary (not neccessary)"]
        ),
    ]

    ENHANCEMENT_SUBTYPES = [
        ErrorSubtype(
            name="naturalness", chinese_name="自然度", category=ErrorCategory.ENHANCEMENT,
            keywords=["更自然", "更道地", "更流暢", "不夠自然", "生硬", "natural", "native", "fluent", "awkward"],
            examples=["How are you doing? (vs How do you do?)"]
        ),
        ErrorSubtype(
            name="style", chinese_name="風格", category=ErrorCategory.ENHANCEMENT,
            keywords=["風格", "正式", "非正式", "語氣", "委婉", "style", "formal", "informal", "tone"],
            examples=["Could you please... (more polite)"]
        ),
    ]

    OTHER_SUBTYPES = [
        ErrorSubtype(
            name="omission", chinese_name="遺漏", category=ErrorCategory.OTHER,
            keywords=["遺漏", "漏譯", "缺少", "忘記", "omit", "miss", "forget"],
            examples=["Missing translation of key information"]
        ),
        ErrorSubtype(
            name="misunderstanding", chinese_name="理解偏差", category=ErrorCategory.OTHER,
            keywords=["理解錯誤", "誤解", "偏差", "misunderstand", "wrong meaning"],
            examples=["Complete misinterpretation of the sentence"]
        ),
    ]

    @classmethod
    def get_all_subtypes(cls) -> list[ErrorSubtype]:
        """獲取所有已定義的錯誤子類型列表。"""
        return cls.SYSTEMATIC_SUBTYPES + cls.ISOLATED_SUBTYPES + cls.ENHANCEMENT_SUBTYPES + cls.OTHER_SUBTYPES

    @classmethod
    def classify(cls, key_point: str, explanation: str, severity: str = "major") -> tuple[ErrorCategory, str]:
        """
        根據錯誤的關鍵點、解釋和嚴重性，自動將其分類。

        Args:
            key_point: 錯誤的簡短描述。
            explanation: 錯誤的詳細解釋。
            severity: 錯誤的嚴重性 ("major" 或 "minor")。

        Returns:
            一個元組，包含 `ErrorCategory` 和子類型的名稱（字串）。
        """
        combined_text = f"{key_point} {explanation}".lower()

        # 優先處理 "enhancement" 類別，因為它們通常是次要問題
        if severity == "minor" or any(kw in combined_text for kw in ["更自然", "更道地", "更好", "不夠自然"]):
            for subtype in cls.ENHANCEMENT_SUBTYPES:
                if subtype.matches(combined_text):
                    return ErrorCategory.ENHANCEMENT, subtype.name
            return ErrorCategory.ENHANCEMENT, "style"

        # 依序檢查其他類別
        for subtype in cls.SYSTEMATIC_SUBTYPES:
            if subtype.matches(combined_text):
                return ErrorCategory.SYSTEMATIC, subtype.name
        for subtype in cls.ISOLATED_SUBTYPES:
            if subtype.matches(combined_text):
                return ErrorCategory.ISOLATED, subtype.name
        for subtype in cls.OTHER_SUBTYPES:
            if subtype.matches(combined_text):
                return ErrorCategory.OTHER, subtype.name

        # 如果沒有匹配的關鍵字，則歸為未分類
        return ErrorCategory.OTHER, "unclassified"

    @classmethod
    def get_subtype_by_name(cls, name: str) -> Optional[ErrorSubtype]:
        """根據名稱查找並返回 `ErrorSubtype` 物件。"""
        return next((subtype for subtype in cls.get_all_subtypes() if subtype.name == name), None)

    @classmethod
    def get_learning_advice(cls, category: ErrorCategory, subtype_name: str) -> str:
        """根據錯誤的類別和子類型，提供具體的學習建議。"""
        subtype = cls.get_subtype_by_name(subtype_name)
        subtype_chinese = f"「{subtype.chinese_name}」" if subtype else "相關"

        advice = {
            ErrorCategory.SYSTEMATIC: f"建議系統性學習{subtype_chinese}的文法規則，掌握後可避免同類錯誤。",
            ErrorCategory.ISOLATED: f"這屬於需要個別記憶的{subtype_chinese}知識點，建議製作記憶卡片或多加練習。",
            ErrorCategory.ENHANCEMENT: "您的基礎不錯！多接觸原文材料（如閱讀、影集）可以讓表達更自然。",
            ErrorCategory.OTHER: "請注意理解題意，確保翻譯的完整性和準確性。",
        }
        return advice.get(category, "持續練習，您會越來越進步！")
