"""
知識點管理模組 - 使用系統性/單一性錯誤分類系統
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.error_types import ErrorCategory, ErrorTypeSystem
from core.exceptions import DataError, handle_file_operation
from core.log_config import get_module_logger
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

    def to_dict(self) -> dict:
        """轉換為字典（用於JSON存儲）- 版本 4.0"""
        return {
            "id": self.id,
            "key_point": self.key_point,
            "category": self.category.value,  # 存儲枚舉值
            "subtype": self.subtype,
            "explanation": self.explanation,
            "original_phrase": self.original_phrase,
            "correction": self.correction,
            "original_error": {
                "chinese_sentence": self.original_error.chinese_sentence,
                "user_answer": self.original_error.user_answer,
                "correct_answer": self.original_error.correct_answer,
                "timestamp": self.original_error.timestamp,
            },
            "review_examples": [
                {
                    "chinese_sentence": example.chinese_sentence,
                    "user_answer": example.user_answer,
                    "correct_answer": example.correct_answer,
                    "timestamp": example.timestamp,
                    "is_correct": example.is_correct,
                }
                for example in self.review_examples
            ],
            "mastery_level": self.mastery_level,
            "mistake_count": self.mistake_count,
            "correct_count": self.correct_count,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "next_review": self.next_review,
            # 新增欄位 - 版本 4.0
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at,
            "deleted_reason": self.deleted_reason,
            "tags": self.tags,
            "custom_notes": self.custom_notes,
            "version_history": self.version_history,
            "last_modified": self.last_modified,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgePoint":
        """從字典創建實例 - 支援新舊資料格式"""
        data = data.copy()

        # 轉換category字符串為枚舉
        data["category"] = ErrorCategory.from_string(data.get("category", "other"))

        # 處理新格式的 original_error
        if "original_error" in data:
            original_error_data = data["original_error"]
            data["original_error"] = OriginalError(
                chinese_sentence=original_error_data.get("chinese_sentence", ""),
                user_answer=original_error_data.get("user_answer", ""),
                correct_answer=original_error_data.get("correct_answer", ""),
                timestamp=original_error_data.get("timestamp", datetime.now().isoformat()),
            )
        else:
            # 舊格式兼容：從 examples 的第一個元素創建 original_error
            examples = data.get("examples", [])
            if examples:
                first_example = examples[0]
                data["original_error"] = OriginalError(
                    chinese_sentence=first_example.get("chinese", ""),
                    user_answer=first_example.get("user_answer", ""),
                    correct_answer=first_example.get("correct", ""),
                    timestamp=data.get("created_at", datetime.now().isoformat()),
                )
            else:
                # 沒有 examples，創建空的 original_error
                data["original_error"] = OriginalError(
                    chinese_sentence="",
                    user_answer=data.get("original_phrase", ""),
                    correct_answer=data.get("correction", ""),
                    timestamp=data.get("created_at", datetime.now().isoformat()),
                )

        # 處理新格式的 review_examples
        if "review_examples" in data:
            review_examples_data = data["review_examples"]
            data["review_examples"] = [
                ReviewExample(
                    chinese_sentence=example.get("chinese_sentence", ""),
                    user_answer=example.get("user_answer", ""),
                    correct_answer=example.get("correct_answer", ""),
                    timestamp=example.get("timestamp", datetime.now().isoformat()),
                    is_correct=example.get("is_correct", False),
                )
                for example in review_examples_data
            ]
        else:
            # 舊格式兼容：從 examples 的其餘元素創建 review_examples
            examples = data.get("examples", [])
            if len(examples) > 1:
                data["review_examples"] = [
                    ReviewExample(
                        chinese_sentence=example.get("chinese", ""),
                        user_answer=example.get("user_answer", ""),
                        correct_answer=example.get("correct", ""),
                        timestamp=data.get("last_seen", datetime.now().isoformat()),
                        is_correct=False,  # 假設都是錯誤記錄
                    )
                    for example in examples[1:]
                ]
            else:
                data["review_examples"] = []

        # 移除舊格式的 examples 欄位
        data.pop("examples", None)

        # 處理新增欄位的預設值（版本 4.0）
        data.setdefault("is_deleted", False)
        data.setdefault("deleted_at", "")
        data.setdefault("deleted_reason", "")
        data.setdefault("tags", [])
        data.setdefault("custom_notes", "")
        data.setdefault("version_history", [])
        data.setdefault("last_modified", data.get("created_at", ""))

        return cls(**data)


class KnowledgeManager:
    """知識點管理器 V2"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # 創建備份目錄
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        self.knowledge_file = self.data_dir / "knowledge.json"
        self.practice_log = self.data_dir / "practice_log.json"

        self.logger = get_module_logger(__name__)
        self.settings = settings

        self.knowledge_points: list[KnowledgePoint] = self._load_knowledge()
        self.practice_history = self._load_practice_log()
        self.type_system = ErrorTypeSystem()

        # 執行資料遷移（如果需要）
        self._migrate_if_needed()

    @handle_file_operation("read")
    def _load_knowledge(self) -> list[KnowledgePoint]:
        """載入知識點"""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, encoding="utf-8") as f:
                    data = json.load(f)

                    # 支援新版本格式（含 version 和 data 欄位）
                    if isinstance(data, dict) and "data" in data:
                        knowledge_data = data["data"]
                    elif isinstance(data, dict) and "knowledge_points" in data:
                        knowledge_data = data["knowledge_points"]
                    elif isinstance(data, list):
                        knowledge_data = data
                    else:
                        knowledge_data = []

                    points = [KnowledgePoint.from_dict(item) for item in knowledge_data]
                    self.logger.info(f"載入 {len(points)} 個知識點")
                    return points
            except json.JSONDecodeError as e:
                self.logger.error(f"知識點文件解析失敗: {e}")
                raise DataError(
                    "知識點文件格式錯誤",
                    data_type="knowledge_points",
                    file_path=str(self.knowledge_file),
                ) from e
        return []

    def _create_backup(self, prefix: str = "knowledge") -> Path:
        """創建備份文件

        Args:
            prefix: 備份文件前綴

        Returns:
            備份文件路徑
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{prefix}_{timestamp}.json"

        if self.knowledge_file.exists():
            import shutil

            shutil.copy2(self.knowledge_file, backup_file)
            self.logger.info(f"創建備份: {backup_file}")

            # 清理舊備份（保留最近30個）
            backups = sorted(self.backup_dir.glob(f"{prefix}_*.json"))
            if len(backups) > 30:
                for old_backup in backups[:-30]:
                    old_backup.unlink()
                    self.logger.debug(f"刪除舊備份: {old_backup}")

        return backup_file

    def _migrate_if_needed(self):
        """檢查並執行資料遷移"""
        if not self.knowledge_file.exists():
            return

        try:
            with open(self.knowledge_file, encoding="utf-8") as f:
                data = json.load(f)

            current_version = data.get("version", "1.0") if isinstance(data, dict) else "1.0"

            # 如果版本低於 4.0，執行遷移
            if current_version < "4.0":
                self.logger.info(f"檢測到舊版本 {current_version}，開始遷移到 4.0")
                self._create_backup("knowledge_migration")

                # 標記需要保存（會自動使用新版本格式）
                self._needs_migration = True
                # 遷移會在第一次保存時自動完成（因為 to_dict 已經包含新欄位）
                self._save_knowledge()
                self.logger.info("資料遷移到 4.0 完成")
        except Exception as e:
            self.logger.error(f"資料遷移失敗: {e}", exc_info=True)

    @handle_file_operation("write")
    def _save_knowledge(self, create_backup: bool = False):
        """儲存知識點

        Args:
            create_backup: 是否創建備份
        """
        try:
            if create_backup:
                self._create_backup()

            # 使用新的版本格式 4.0
            data = {
                "version": "4.0",
                "last_updated": datetime.now().isoformat(),
                "data": [point.to_dict() for point in self.knowledge_points],
            }

            with open(self.knowledge_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"儲存 {len(self.knowledge_points)} 個知識點")
        except Exception as e:
            self.logger.error(f"儲存知識點失敗: {e}", exc_info=True)
            raise

    def _load_practice_log(self) -> list[dict]:
        """載入練習記錄"""
        if self.practice_log.exists():
            with open(self.practice_log, encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_practice_log(self):
        """儲存練習記錄"""
        with open(self.practice_log, "w", encoding="utf-8") as f:
            json.dump(self.practice_history, f, ensure_ascii=False, indent=2)

    def save_mistake(
        self,
        chinese_sentence: str,
        user_answer: str,
        feedback: dict[str, Any],
        practice_mode: str = "new",
    ):
        """儲存錯誤記錄（使用新的分類系統）

        Args:
            practice_mode: 'new' 表示新題模式，'review' 表示複習模式
        """
        # 記錄練習歷史
        practice = {
            "timestamp": datetime.now().isoformat(),
            "chinese_sentence": chinese_sentence,
            "user_answer": user_answer,
            "is_correct": feedback.get("is_generally_correct", False),
            "feedback": feedback,
            "practice_mode": practice_mode,
        }
        self.practice_history.append(practice)
        self._save_practice_log()

        # 處理結果
        if not feedback.get("is_generally_correct", False):
            # 錯誤情況：提取並儲存知識點
            errors = feedback.get("error_analysis", [])
            for error in errors:
                self._process_error(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    error=error,
                    correct_answer=feedback.get("overall_suggestion", ""),
                    practice_mode=practice_mode,
                )
        elif practice_mode == "review":
            # 複習模式下答對：更新相關知識點的掌握度
            self._process_correct_review(chinese_sentence, user_answer, feedback)

    def _process_correct_review(
        self, chinese_sentence: str, user_answer: str, feedback: dict[str, Any]
    ):
        """處理複習模式下的正確答案"""
        # 這裡可以根據題目內容推斷是在練習哪個知識點
        # 暫時先記錄，後續可以加入更智能的匹配邏輯
        self.logger.info(f"複習模式正確答案: {chinese_sentence}")

    def add_review_success(self, knowledge_point_id: int, chinese_sentence: str, user_answer: str):
        """為知識點添加複習成功記錄"""
        point = self.get_knowledge_point(str(knowledge_point_id))
        if point:
            review_example = ReviewExample(
                chinese_sentence=chinese_sentence,
                user_answer=user_answer,
                correct_answer=user_answer,  # 因為是正確的
                timestamp=datetime.now().isoformat(),
                is_correct=True,
            )
            point.review_examples.append(review_example)
            point.update_mastery(is_correct=True)
            self._save_knowledge()

    def _process_error(
        self,
        chinese_sentence: str,
        user_answer: str,
        error: dict[str, Any],
        correct_answer: str,
        practice_mode: str = "new",
    ):
        """處理單個錯誤 - 區分新題模式和複習模式"""
        key_point = error.get("key_point_summary", "")
        original_phrase = error.get("original_phrase", "")
        correction = error.get("correction", "")
        explanation = error.get("explanation", "")
        severity = error.get("severity", "major")

        # 生成更具體的 key_point 描述
        if original_phrase and correction:
            specific_key_point = f"{key_point}: {original_phrase}"
        else:
            specific_key_point = key_point

        # 優先使用AI返回的category，如果沒有則用分類系統推斷
        if "category" in error:
            category = ErrorCategory.from_string(error["category"])
            # 使用分類系統推斷subtype
            _, subtype = self.type_system.classify(key_point, explanation, severity)
        else:
            # 使用新的分類系統
            category, subtype = self.type_system.classify(key_point, explanation, severity)

        # 使用複合鍵查找現有知識點
        existing = self._find_knowledge_point(specific_key_point, original_phrase, correction)

        if existing:
            # 更新現有知識點的掌握度
            existing.update_mastery(is_correct=False)

            if practice_mode == "review":
                # 複習模式：添加到複習例句
                review_example = ReviewExample(
                    chinese_sentence=chinese_sentence,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    timestamp=datetime.now().isoformat(),
                    is_correct=False,
                )
                existing.review_examples.append(review_example)
            else:
                # 新題模式：這不應該發生，因為新題應該總是創建新知識點
                self.logger.warning(f"新題模式下發現重複知識點: {existing.unique_identifier}")
        else:
            # 創建新知識點（主要在新題模式下發生）
            original_error = OriginalError(
                chinese_sentence=chinese_sentence,
                user_answer=user_answer,
                correct_answer=correct_answer,
                timestamp=datetime.now().isoformat(),
            )

            new_point = KnowledgePoint(
                id=self._get_next_id(),
                key_point=specific_key_point,
                category=category,
                subtype=subtype,
                explanation=explanation,
                original_phrase=original_phrase,
                correction=correction,
                original_error=original_error,
                review_examples=[],
            )
            self.knowledge_points.append(new_point)

        self._save_knowledge()

    def _find_knowledge_point(
        self, key_point: str, original_phrase: str = "", correction: str = ""
    ) -> Optional[KnowledgePoint]:
        """查找知識點 - 使用複合鍵確保唯一性"""
        for point in self.knowledge_points:
            # 使用複合鍵匹配：key_point + original_phrase + correction
            if (
                point.key_point == key_point
                and point.original_phrase == original_phrase
                and point.correction == correction
            ):
                return point
        return None

    def _find_knowledge_point_by_identifier(self, identifier: str) -> Optional[KnowledgePoint]:
        """通過唯一標識符查找知識點"""
        for point in self.knowledge_points:
            if point.unique_identifier == identifier:
                return point
        return None

    def get_knowledge_point(self, point_id: str) -> Optional[KnowledgePoint]:
        """根據ID獲取知識點"""
        try:
            target_id = int(point_id)
            for point in self.knowledge_points:
                if point.id == target_id:
                    return point
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid point_id: {point_id}")
        return None

    def _get_next_id(self) -> int:
        """獲取下一個ID"""
        if not self.knowledge_points:
            return 1
        return max(p.id for p in self.knowledge_points) + 1

    def get_points_by_category(self, category: ErrorCategory) -> list[KnowledgePoint]:
        """根據類別獲取知識點"""
        return [p for p in self.knowledge_points if p.category == category]

    def get_all_mistakes(self) -> list[dict]:
        """獲取所有錯誤記錄"""
        # 返回練習歷史中的錯誤記錄，並為每個記錄添加知識點信息
        mistakes = []
        for practice in self.practice_history:
            if not practice.get("is_correct", True):
                # 為每個錯誤記錄添加關聯的知識點
                mistake = practice.copy()
                # 從feedback中提取知識點信息
                if "feedback" in mistake and "error_analysis" in mistake["feedback"]:
                    knowledge_points = []
                    for error in mistake["feedback"]["error_analysis"]:
                        key_point = error.get("key_point_summary", "")
                        point = self._find_knowledge_point(key_point)
                        if point:
                            knowledge_points.append(
                                {
                                    "id": str(point.id),
                                    "key_point": point.key_point,
                                    "category": point.category.value,
                                }
                            )
                    mistake["knowledge_points"] = knowledge_points
                mistakes.append(mistake)
        return mistakes

    def get_due_points(self) -> list[KnowledgePoint]:
        """獲取需要複習的知識點"""
        now = datetime.now().isoformat()
        return [p for p in self.knowledge_points if p.next_review <= now]

    def get_review_candidates(self, max_points: int = 5) -> list[KnowledgePoint]:
        """獲取適合複習的知識點（單一性錯誤和可以更好類別）

        Args:
            max_points: 最多返回的知識點數量

        Returns:
            需要複習的知識點列表，優先返回已到期的
        """
        # 篩選單一性錯誤和可以更好類別
        candidates = [
            p
            for p in self.knowledge_points
            if p.category in [ErrorCategory.ISOLATED, ErrorCategory.ENHANCEMENT]
        ]

        if not candidates:
            return []

        # 按複習優先級排序：
        # 1. 已到期的（next_review <= now）
        # 2. 掌握度低的
        # 3. 錯誤次數多的
        now = datetime.now().isoformat()

        def sort_key(point: KnowledgePoint) -> tuple:
            is_due = point.next_review <= now
            return (
                not is_due,  # 到期的排前面
                point.mastery_level,  # 掌握度低的排前面
                -point.mistake_count,  # 錯誤次數多的排前面
            )

        candidates.sort(key=sort_key)

        # 返回前max_points個最需要複習的
        return candidates[:max_points]

    def update_knowledge_point(self, point_id: int, is_correct: bool) -> bool:
        """更新指定知識點的掌握狀態

        Args:
            point_id: 知識點ID
            is_correct: 是否答對

        Returns:
            是否成功更新
        """
        for point in self.knowledge_points:
            if point.id == point_id:
                point.update_mastery(is_correct)
                self._save_knowledge()
                return True
        return False

    def edit_knowledge_point(self, point_id: int, updates: dict) -> Optional[dict]:
        """編輯知識點

        Args:
            point_id: 知識點ID
            updates: 要更新的欄位

        Returns:
            編輯歷史記錄，如果失敗返回 None
        """
        for point in self.knowledge_points:
            if point.id == point_id and not point.is_deleted:
                # 創建備份
                self._save_knowledge(create_backup=True)

                # 執行編輯
                history = point.edit(updates)

                # 保存變更
                self._save_knowledge()

                self.logger.info(f"編輯知識點 {point_id}: {list(updates.keys())}")
                return history

        self.logger.warning(f"找不到知識點 {point_id} 或已被刪除")
        return None

    def delete_knowledge_point(self, point_id: int, reason: str = "") -> bool:
        """軟刪除知識點

        Args:
            point_id: 知識點ID
            reason: 刪除原因

        Returns:
            是否成功刪除
        """
        for point in self.knowledge_points:
            if point.id == point_id and not point.is_deleted:
                # 創建備份
                self._save_knowledge(create_backup=True)

                # 執行軟刪除
                point.soft_delete(reason)

                # 保存變更
                self._save_knowledge()

                self.logger.info(f"軟刪除知識點 {point_id}，原因: {reason}")
                return True

        self.logger.warning(f"找不到知識點 {point_id} 或已被刪除")
        return False

    def restore_knowledge_point(self, point_id: int) -> bool:
        """復原軟刪除的知識點

        Args:
            point_id: 知識點ID

        Returns:
            是否成功復原
        """
        for point in self.knowledge_points:
            if point.id == point_id and point.is_deleted:
                # 執行復原
                point.restore()

                # 保存變更
                self._save_knowledge()

                self.logger.info(f"復原知識點 {point_id}")
                return True

        self.logger.warning(f"找不到已刪除的知識點 {point_id}")
        return False

    def get_deleted_points(self) -> list[KnowledgePoint]:
        """獲取所有已刪除的知識點

        Returns:
            已刪除的知識點列表
        """
        return [p for p in self.knowledge_points if p.is_deleted]

    def get_active_points(self) -> list[KnowledgePoint]:
        """獲取所有未刪除的知識點

        Returns:
            未刪除的知識點列表
        """
        return [p for p in self.knowledge_points if not p.is_deleted]

    def permanent_delete_old_points(self, days: int = 30) -> int:
        """永久刪除超過指定天數的軟刪除知識點

        Args:
            days: 天數閾值

        Returns:
            刪除的數量
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        # 過濾出需要保留的知識點
        remaining_points = []
        for point in self.knowledge_points:
            if point.is_deleted and point.deleted_at:
                try:
                    deleted_date = datetime.fromisoformat(point.deleted_at.replace("Z", "+00:00"))
                    # 移除時區信息進行比較
                    deleted_date = deleted_date.replace(tzinfo=None)
                    if deleted_date < cutoff_date:
                        deleted_count += 1
                        self.logger.info(f"永久刪除知識點 {point.id}")
                        continue
                except (ValueError, AttributeError):
                    pass

            remaining_points.append(point)

        if deleted_count > 0:
            self.knowledge_points = remaining_points
            self._save_knowledge(create_backup=True)
            self.logger.info(f"永久刪除了 {deleted_count} 個舊知識點")

        return deleted_count

    def get_statistics(self) -> dict[str, Any]:
        """獲取統計資料"""
        total_practices = len(self.practice_history)
        correct_count = sum(1 for p in self.practice_history if p.get("is_correct", False))

        # 分類統計
        category_stats = {
            ErrorCategory.SYSTEMATIC: 0,
            ErrorCategory.ISOLATED: 0,
            ErrorCategory.ENHANCEMENT: 0,
            ErrorCategory.OTHER: 0,
        }

        subtype_stats = {}

        for point in self.knowledge_points:
            category_stats[point.category] += 1
            if point.subtype not in subtype_stats:
                subtype_stats[point.subtype] = 0
            subtype_stats[point.subtype] += 1

        # 平均掌握度
        if self.knowledge_points:
            avg_mastery = sum(p.mastery_level for p in self.knowledge_points) / len(
                self.knowledge_points
            )
        else:
            avg_mastery = 0.0

        return {
            "total_practices": total_practices,
            "correct_count": correct_count,
            "mistake_count": total_practices - correct_count,
            "accuracy": correct_count / total_practices if total_practices > 0 else 0,
            "knowledge_points": len(self.knowledge_points),
            "avg_mastery": avg_mastery,
            "category_distribution": {
                cat.to_chinese(): count for cat, count in category_stats.items() if count > 0
            },
            "subtype_distribution": subtype_stats,
            "due_reviews": len(self.get_due_points()),
        }

    def get_learning_recommendations(self) -> list[dict]:
        """獲取學習建議"""
        recommendations = []

        # 分析各類別的知識點
        for category in ErrorCategory:
            points = self.get_points_by_category(category)
            if not points:
                continue

            # 計算該類別的平均掌握度
            avg_mastery = sum(p.mastery_level for p in points) / len(points)

            # 找出最常見的子類型
            subtype_counts = {}
            for point in points:
                if point.subtype not in subtype_counts:
                    subtype_counts[point.subtype] = 0
                subtype_counts[point.subtype] += 1

            if subtype_counts:
                most_common_subtype = max(subtype_counts.items(), key=lambda x: x[1])
                subtype_obj = self.type_system.get_subtype_by_name(most_common_subtype[0])

                recommendation = {
                    "category": category.to_chinese(),
                    "priority": category.get_priority(),
                    "point_count": len(points),
                    "avg_mastery": avg_mastery,
                    "focus_area": subtype_obj.chinese_name
                    if subtype_obj
                    else most_common_subtype[0],
                    "advice": self.type_system.get_learning_advice(
                        category, most_common_subtype[0]
                    ),
                }
                recommendations.append(recommendation)

        # 按優先級排序
        recommendations.sort(key=lambda x: x["priority"])

        return recommendations
