"""
應用程式核心資料模型定義

此模組使用 `dataclasses` 定義了應用程式中的核心資料結構，
如 `KnowledgePoint`, `OriginalError`, 和 `ReviewExample`。
將資料模型與業務邏輯分離，有助於避免循環導入問題，並提高程式碼的清晰度和可維護性。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from core.error_types import ErrorCategory
from settings import settings


@dataclass
class OriginalError:
    """記錄知識點最初被創建時的原始錯誤資訊。"""
    chinese_sentence: str
    user_answer: str
    correct_answer: str
    timestamp: str

    def __post_init__(self):
        """如果 timestamp 未被提供，則自動設定為當前時間。"""
        if not getattr(self, "timestamp", None):
            self.timestamp = datetime.now().isoformat()


@dataclass
class ReviewExample:
    """記錄每一次複習的具體例句和結果。"""
    chinese_sentence: str
    user_answer: str
    correct_answer: str
    timestamp: str
    is_correct: bool

    def __post_init__(self):
        """如果 timestamp 未被提供，則自動設定為當前時間。"""
        if not getattr(self, "timestamp", None):
            self.timestamp = datetime.now().isoformat()


@dataclass
class KnowledgePoint:
    """
    知識點的核心資料模型。

    每個 `KnowledgePoint` 物件代表一個具體的使用者錯誤模式，並包含其所有相關資訊，
    例如錯誤分類、掌握度、複習排程和編輯歷史等。
    """
    id: int
    key_point: str  # 錯誤的簡短描述，例如 "單字拼寫錯誤: irrevertable"
    category: ErrorCategory
    subtype: str
    explanation: str
    original_phrase: str
    correction: str

    original_error: OriginalError
    review_examples: list[ReviewExample] = field(default_factory=list)

    # 學習進度和排程
    mastery_level: float = 0.0
    mistake_count: int = 1
    correct_count: int = 0
    created_at: str = ""
    last_seen: str = ""
    next_review: str = ""

    # 版本 4.0 新增欄位，支援更豐富的管理功能
    is_deleted: bool = False
    deleted_at: str = ""
    deleted_reason: str = ""
    tags: list[str] = field(default_factory=list)
    custom_notes: str = ""
    version_history: list[dict] = field(default_factory=list)
    last_modified: str = ""

    def __post_init__(self):
        """初始化預設值和空列表，確保物件狀態的一致性。"""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.last_seen:
            self.last_seen = now
        if not self.next_review:
            self.next_review = self._calculate_next_review()
        if not self.last_modified:
            self.last_modified = self.created_at

    @property
    def unique_identifier(self) -> str:
        """生成一個用於識別相似知識點的唯一標識符。"""
        return f"{self.key_point}|{self.original_phrase}|{self.correction}"

    def _calculate_next_review(self) -> str:
        """根據艾賓浩斯遺忘曲線和錯誤類型，計算下一次最佳複習時間。"""
        thresholds = settings.learning.MASTERY_THRESHOLDS
        intervals = settings.learning.REVIEW_INTERVALS

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

        multiplier = self.category.get_review_multiplier()
        days = max(1, int(base_days * multiplier))
        return (datetime.now() + timedelta(days=days)).isoformat()

    def update_mastery(self, is_correct: bool):
        """根據練習結果更新掌握度、計數和下次複習時間。"""
        if is_correct:
            self.correct_count += 1
            increment = settings.learning.MASTERY_INCREMENTS.get(self.category.value, settings.learning.MASTERY_INCREMENTS["other"])
            self.mastery_level = min(1.0, self.mastery_level + increment)
        else:
            self.mistake_count += 1
            decrement = settings.learning.MASTERY_DECREMENTS.get(self.category.value, settings.learning.MASTERY_DECREMENTS["other"])
            self.mastery_level = max(0.0, self.mastery_level - decrement)

        self.last_seen = datetime.now().isoformat()
        self.next_review = self._calculate_next_review()

    def edit(self, updates: dict[str, Any]) -> dict[str, Any]:
        """
        編輯知識點屬性，並將變更記錄到 `version_history`。

        Args:
            updates: 一個包含要更新欄位和新值的字典。

        Returns:
            一個描述此次變更的歷史記錄項目。
        """
        before_state = {field: getattr(self, field) for field in updates.keys()}
        
        for key, value in updates.items():
            if hasattr(self, key):
                if key == "category":
                    setattr(self, key, ErrorCategory.from_string(value))
                else:
                    setattr(self, key, value)

        self.last_modified = datetime.now().isoformat()
        after_state = {field: getattr(self, field) for field in updates.keys()}

        history_entry = {
            "timestamp": self.last_modified,
            "before": before_state,
            "after": after_state,
            "changed_fields": list(updates.keys()),
        }
        self.version_history.append(history_entry)
        return history_entry

    def soft_delete(self, reason: str = ""):
        """將知識點標記為已刪除。"""
        self.is_deleted = True
        self.deleted_at = datetime.now().isoformat()
        self.deleted_reason = reason
        self.last_modified = self.deleted_at

    def restore(self):
        """從軟刪除狀態恢復知識點。"""
        self.is_deleted = False
        self.deleted_at = ""
        self.deleted_reason = ""
        self.last_modified = datetime.now().isoformat()
