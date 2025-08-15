"""
數據模型定義
分離數據模型以避免循環導入問題
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Any

from core.error_types import ErrorCategory
from settings import settings


@dataclass
class OriginalError:
    """原始錯誤記錄 - 每個知識點只有一個"""

    chinese_sentence: str
    user_answer: str
    correct_answer: str
    timestamp: str

    def __post_init__(self):
        if not hasattr(self, "timestamp") or not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ReviewExample:
    """複習例句記錄 - 每個知識點可以有多個"""

    chinese_sentence: str
    user_answer: str
    correct_answer: str
    timestamp: str
    is_correct: bool

    def __post_init__(self):
        if not hasattr(self, "timestamp") or not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class KnowledgePoint:
    """知識點數據類 - 每個知識點對應一個具體的錯誤模式"""

    id: int
    key_point: str  # 更具體的描述，如 "單字拼寫錯誤: irrevertable"
    category: ErrorCategory
    subtype: str
    explanation: str
    original_phrase: str
    correction: str

    # 原始錯誤（只有一個）
    original_error: OriginalError

    # 複習例句（可以有多個）
    review_examples: list[ReviewExample] = None

    # 掌握度相關
    mastery_level: float = 0.0
    mistake_count: int = 1
    correct_count: int = 0
    created_at: str = ""
    last_seen: str = ""
    next_review: str = ""

    # 新增欄位 - 版本 4.0
    is_deleted: bool = False  # 軟刪除標記
    deleted_at: str = ""  # 刪除時間
    deleted_reason: str = ""  # 刪除原因
    tags: list[str] = None  # 自定義標籤
    custom_notes: str = ""  # 用戶筆記
    version_history: list[dict] = None  # 編輯歷史
    last_modified: str = ""  # 最後修改時間

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_seen:
            self.last_seen = datetime.now().isoformat()
        if not self.next_review:
            self.next_review = self._calculate_next_review()
        if self.review_examples is None:
            self.review_examples = []
        # 初始化新欄位
        if self.tags is None:
            self.tags = []
        if self.version_history is None:
            self.version_history = []
        if not self.last_modified:
            self.last_modified = self.created_at

    @property
    def unique_identifier(self) -> str:
        """知識點的唯一標識符"""
        return f"{self.key_point}|{self.original_phrase}|{self.correction}"

    @property
    def examples(self) -> list[dict]:
        """舊格式兼容屬性 - 將新格式轉換為舊格式"""
        examples_list = []

        # 添加原始錯誤作為第一個例句
        if self.original_error:
            examples_list.append(
                {
                    "chinese": self.original_error.chinese_sentence,
                    "user_answer": self.original_error.user_answer,
                    "correct": self.original_error.correct_answer,
                }
            )

        # 添加複習例句
        for review in self.review_examples:
            examples_list.append(
                {
                    "chinese": review.chinese_sentence,
                    "user_answer": review.user_answer,
                    "correct": review.correct_answer,
                }
            )

        return examples_list

    def _calculate_next_review(self) -> str:
        """計算下次複習時間"""
        # 從設定檔獲取複習間隔
        thresholds = settings.learning.MASTERY_THRESHOLDS
        intervals = settings.learning.REVIEW_INTERVALS

        # 根據掌握度決定基礎天數
        if self.mastery_level < thresholds["beginner"]:
            base_days = intervals["immediate"]
        elif self.mastery_level < thresholds["intermediate"]:
            base_days = intervals["short"]
        elif self.mastery_level < thresholds["advanced"]:
            base_days = intervals["medium"]
        elif self.mastery_level < thresholds["expert"]:
            base_days = intervals["long"]
        else:
            base_days = intervals["mastered"]

        # 根據錯誤類別調整
        multiplier = self.category.get_review_multiplier()
        days = max(1, int(base_days * multiplier))

        next_date = datetime.now() + timedelta(days=days)
        return next_date.isoformat()

    def update_mastery(self, is_correct: bool):
        """更新掌握度"""
        increments = settings.learning.MASTERY_INCREMENTS
        decrements = settings.learning.MASTERY_DECREMENTS

        if is_correct:
            self.correct_count += 1
            # 根據錯誤類別調整進步幅度
            category_key = self.category.value
            increment = increments.get(category_key, increments["other"])
            self.mastery_level = min(1.0, self.mastery_level + increment)
        else:
            self.mistake_count += 1
            # 錯誤時的懲罰
            category_key = self.category.value
            decrement = decrements.get(category_key, decrements["other"])
            self.mastery_level = max(0.0, self.mastery_level - decrement)

        self.last_seen = datetime.now().isoformat()
        self.next_review = self._calculate_next_review()

    def edit(self, updates: dict) -> dict:
        """編輯知識點並記錄歷史

        Args:
            updates: 要更新的欄位字典

        Returns:
            包含變更前後對比的字典
        """
        # 記錄變更前的狀態
        before_state = {
            "key_point": self.key_point,
            "explanation": self.explanation,
            "original_phrase": self.original_phrase,
            "correction": self.correction,
            "category": self.category.value,
            "subtype": self.subtype,
            "tags": self.tags.copy() if self.tags else [],
            "custom_notes": self.custom_notes,
        }

        # 應用更新
        if "key_point" in updates:
            self.key_point = updates["key_point"]
        if "explanation" in updates:
            self.explanation = updates["explanation"]
        if "original_phrase" in updates:
            self.original_phrase = updates["original_phrase"]
        if "correction" in updates:
            self.correction = updates["correction"]
        if "category" in updates:
            self.category = ErrorCategory.from_string(updates["category"])
        if "subtype" in updates:
            self.subtype = updates["subtype"]
        if "tags" in updates:
            self.tags = updates["tags"] if isinstance(updates["tags"], list) else []
        if "custom_notes" in updates:
            self.custom_notes = updates["custom_notes"]

        # 更新修改時間
        self.last_modified = datetime.now().isoformat()

        # 記錄到版本歷史
        history_entry = {
            "timestamp": self.last_modified,
            "before": before_state,
            "after": {
                "key_point": self.key_point,
                "explanation": self.explanation,
                "original_phrase": self.original_phrase,
                "correction": self.correction,
                "category": self.category.value,
                "subtype": self.subtype,
                "tags": self.tags.copy() if self.tags else [],
                "custom_notes": self.custom_notes,
            },
            "changed_fields": list(updates.keys()),
        }

        if self.version_history is None:
            self.version_history = []
        self.version_history.append(history_entry)

        return history_entry

    def soft_delete(self, reason: str = "") -> None:
        """軟刪除知識點

        Args:
            reason: 刪除原因
        """
        self.is_deleted = True
        self.deleted_at = datetime.now().isoformat()
        self.deleted_reason = reason
        self.last_modified = self.deleted_at

    def restore(self) -> None:
        """復原軟刪除的知識點"""
        self.is_deleted = False
        self.deleted_at = ""
        self.deleted_reason = ""
        self.last_modified = datetime.now().isoformat()