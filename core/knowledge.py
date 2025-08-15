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

from core.cache_manager import UnifiedCacheManager, CacheCategories
from core.error_types import ErrorCategory, ErrorTypeSystem
from core.exceptions import DataError, handle_file_operation
from core.log_config import get_module_logger
from core.error_handler import ErrorHandler, with_error_handling
from core.fallback_strategies import get_fallback_manager
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

        # TASK-20D: 統一錯誤處理體系
        self._error_handler = ErrorHandler(mode="json")
        self._fallback_manager = get_fallback_manager()

        # 統一快取管理器
        self._cache_manager = UnifiedCacheManager(default_ttl=300)  # 5分鐘預設 TTL

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

    def add_knowledge_point_from_error(
        self, chinese_sentence: str, user_answer: str, error: dict, correct_answer: str
    ) -> int:
        """從錯誤信息創建知識點（用於手動確認功能）
        
        Args:
            chinese_sentence: 中文句子
            user_answer: 用戶答案
            error: 錯誤分析數據
            correct_answer: 正確答案
            
        Returns:
            新創建的知識點ID
        """
        from datetime import datetime
        
        # 創建新的知識點
        point_id = self._get_next_id()
        from core.error_types import ErrorCategory
        
        # 處理 category - 確保是枚舉類型
        category_str = error.get("category", "other")
        try:
            category = ErrorCategory(category_str) if isinstance(category_str, str) else category_str
        except ValueError:
            category = ErrorCategory.OTHER
            
        point = KnowledgePoint(
            id=point_id,
            key_point=error.get("key_point_summary", "未知錯誤"),
            original_phrase=error.get("original_phrase", user_answer),
            correction=error.get("correction", correct_answer),
            explanation=error.get("explanation", ""),
            category=category,
            subtype=error.get("subtype", "general"),
            mastery_level=0.1,
            mistake_count=1,
            correct_count=0,
            last_seen=datetime.now().isoformat(),
            next_review=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            original_error=OriginalError(
                chinese_sentence=chinese_sentence,
                user_answer=user_answer,
                correct_answer=correct_answer,
                timestamp=datetime.now().isoformat()
            )
        )
        
        self.knowledge_points.append(point)
        self._save_knowledge()
        
        return point_id

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

        # 清除相關快取（不論是否出錯，都可能影響統計）
        self._invalidate_caches()

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
            self._invalidate_caches()

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
        now = datetime.now()
        due_points = []

        for p in self.knowledge_points:
            if p.next_review:
                try:
                    review_date = datetime.fromisoformat(p.next_review)
                    # 確保兩個 datetime 都是 offset-naive
                    if review_date.tzinfo is not None:
                        review_date = review_date.replace(tzinfo=None)
                    if review_date <= now:
                        due_points.append(p)
                except (ValueError, TypeError):
                    # 如果解析失敗，跳過此點
                    continue

        return due_points

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

    @with_error_handling(operation="get_statistics", mode="json")
    def get_statistics(self) -> dict[str, Any]:
        """獲取統計資料（使用統一快取管理器）

        TASK-20A: 統一快取管理系統
        TASK-20D: 添加統一錯誤處理
        使用 UnifiedCacheManager 提供快取統計
        """
        try:
            result = self._cache_manager.get_or_compute(
                key=f"{CacheCategories.STATISTICS}:json",
                compute_func=self._compute_statistics,
                ttl=60,  # 統計快取1分鐘
            )

            # 更新降級快取
            self._update_fallback_cache("get_statistics", result)
            return result

        except Exception as e:
            # 統一錯誤處理
            return self._handle_error_with_fallback(e, "get_statistics")

    def _compute_statistics(self) -> dict[str, Any]:
        """計算統計資料（JSON 模式）"""
        from core.statistics_utils import UnifiedStatistics

        # 提取統一格式的練習記錄
        practice_records = UnifiedStatistics.extract_json_practice_records(self)

        # 標準化處理
        practice_records = UnifiedStatistics.normalize_practice_records(practice_records)

        # 使用統一邏輯計算統計
        stats = UnifiedStatistics.calculate_practice_statistics(
            knowledge_points=self.knowledge_points,
            practice_records=practice_records,
            include_original_errors=True,
        )

        self.logger.debug(
            f"JSON 統計計算完成: 練習{stats['total_practices']}, 正確{stats['correct_count']}, 知識點{stats['knowledge_points']}"
        )

        return stats

    def _invalidate_caches(self) -> None:
        """清除相關快取"""
        # 清除統計快取
        self._cache_manager.invalidate(CacheCategories.STATISTICS)
        # 清除複習候選快取
        self._cache_manager.invalidate(CacheCategories.REVIEW_CANDIDATES)
        # 清除知識點快取
        self._cache_manager.invalidate(CacheCategories.KNOWLEDGE_POINTS)
        # 清除搜索結果快取
        self._cache_manager.invalidate(CacheCategories.SEARCH_RESULTS)

        self.logger.debug("已清除相關快取")

    def get_learning_recommendations(self) -> dict[str, Any]:
        """獲取學習建議

        Returns:
            包含推薦信息的字典：
            - recommendations: 推薦描述列表
            - focus_areas: 重點學習領域
            - suggested_difficulty: 建議難度等級
            - next_review_count: 待複習知識點數量
            - priority_points: 優先學習的知識點列表
        """
        from collections import defaultdict

        # 如果沒有知識點，返回初始建議
        if not self.knowledge_points:
            return {
                "recommendations": ["開始第一次練習，建立學習基礎"],
                "focus_areas": [],
                "suggested_difficulty": 1,
                "next_review_count": 0,
                "priority_points": [],
                "statistics": {},
            }

        # 統計分析
        low_mastery_points = []  # 低掌握度知識點（< 0.3）
        medium_mastery_points = []  # 中等掌握度（0.3-0.7）
        due_for_review = self.get_due_points()  # 待複習的點
        category_stats = defaultdict(lambda: {"count": 0, "avg_mastery": 0, "points": []})

        for point in self.knowledge_points:
            # 掌握度分類
            if point.mastery_level < 0.3:
                low_mastery_points.append(point)
            elif point.mastery_level < 0.7:
                medium_mastery_points.append(point)

            # 統計各類別
            category = point.category.value
            category_stats[category]["count"] += 1
            category_stats[category]["avg_mastery"] += point.mastery_level
            category_stats[category]["points"].append(point)

        # 計算各類別平均掌握度
        for _category, stats in category_stats.items():
            if stats["count"] > 0:
                stats["avg_mastery"] /= stats["count"]

        # 生成推薦
        recommendations = []
        focus_areas = []

        # 1. 優先處理低掌握度的系統性錯誤
        systematic_low = [p for p in low_mastery_points if p.category.value == "systematic"]
        if systematic_low:
            recommendations.append(f"重點練習文法規則錯誤 ({len(systematic_low)} 個知識點待加強)")
            focus_areas.append("systematic")

        # 2. 處理待複習的知識點
        if len(due_for_review) > 5:
            recommendations.append(f"有 {len(due_for_review)} 個知識點需要複習，建議優先完成")

        # 3. 根據類別統計提供建議
        if category_stats:
            weakest_category = min(category_stats.items(), key=lambda x: x[1]["avg_mastery"])
            if weakest_category[1]["avg_mastery"] < 0.5:
                category_name = weakest_category[0]
                category_chinese = {
                    "systematic": "文法規則",
                    "isolated": "個別詞彙",
                    "enhancement": "表達優化",
                    "other": "其他",
                }.get(category_name, category_name)

                recommendations.append(
                    f"加強「{category_chinese}」類型的練習 (平均掌握度 {weakest_category[1]['avg_mastery']:.1%})"
                )
                if category_name not in focus_areas:
                    focus_areas.append(category_name)

        # 如果沒有特別的推薦，給出一般建議
        if not recommendations:
            if len(self.knowledge_points) < 10:
                recommendations.append("繼續累積練習，建立更多知識點")
            else:
                recommendations.append("保持練習頻率，鞏固已學知識")

        # 確定建議難度
        avg_mastery = sum(p.mastery_level for p in self.knowledge_points) / len(
            self.knowledge_points
        )
        if avg_mastery < 0.3:
            suggested_difficulty = 1
        elif avg_mastery < 0.6:
            suggested_difficulty = 2
        else:
            suggested_difficulty = 3

        # 選擇優先學習的知識點（最多10個）
        priority_points = sorted(
            low_mastery_points + medium_mastery_points,
            key=lambda p: (p.mastery_level, -p.mistake_count),
        )[:10]

        # 統計信息
        statistics = {
            "total_points": len(self.knowledge_points),
            "low_mastery_count": len(low_mastery_points),
            "medium_mastery_count": len(medium_mastery_points),
            "average_mastery": avg_mastery,
            "category_distribution": {cat: stats["count"] for cat, stats in category_stats.items()},
        }

        return {
            "recommendations": recommendations,
            "focus_areas": focus_areas,
            "suggested_difficulty": suggested_difficulty,
            "next_review_count": len(due_for_review),
            "priority_points": [
                {
                    "id": p.id,
                    "key_point": p.key_point,
                    "mastery_level": p.mastery_level,
                    "category": p.category.value,
                    "mistake_count": p.mistake_count,
                }
                for p in priority_points
            ],
            "statistics": statistics,
        }

    # TASK-20D: 統一錯誤處理輔助方法
    def _update_fallback_cache(self, method_name: str, result: Any) -> None:
        """更新降級快取"""
        try:
            # 找到快取降級策略並更新快取
            cache_strategy = None
            for strategy in self._fallback_manager.strategies:
                if hasattr(strategy, "update_cache"):
                    cache_strategy = strategy
                    break

            if cache_strategy and result is not None:
                # 建立方法引用
                method_func = getattr(self, method_name, None)
                if method_func:
                    cache_strategy.update_cache(method_func, (self,), {}, result)

        except Exception as e:
            self.logger.warning(f"更新降級快取失敗: {e}")

    def _handle_error_with_fallback(self, error: Exception, operation: str) -> Any:
        """統一錯誤處理和降級邏輯"""
        try:
            # 使用統一錯誤處理器
            error_response = self._error_handler.handle_error(error, operation)

            # JSON 模式通常不需要降級，但可以返回安全的默認值
            self.logger.warning(f"JSON 模式錯誤處理: {operation} - {error}")

            # 根據操作類型返回安全的默認值
            return self._get_safe_default_for_operation(operation)

        except Exception as fallback_error:
            self.logger.error(f"錯誤處理失敗: {fallback_error}")
            return self._get_safe_default_for_operation(operation)

    def _get_safe_default_for_operation(self, operation: str) -> Any:
        """根據操作獲取安全的默認值"""
        defaults = {
            "get_statistics": {
                "total_practices": 0,
                "correct_count": 0,
                "knowledge_points": 0,
                "avg_mastery": 0.0,
                "category_distribution": {},
                "due_reviews": 0,
                "_json_error_fallback": True,
                "_operation": operation,
            },
            "get_knowledge_points": [],
            "get_all_knowledge_points": [],
            "get_review_candidates": [],
            "search_knowledge_points": [],
            "get_knowledge_point": None,
            "add_knowledge_point": False,
            "edit_knowledge_point": None,
            "delete_knowledge_point": False,
            "restore_knowledge_point": None,
        }

        result = defaults.get(operation, None)
        if isinstance(result, dict):
            result = result.copy()
            result["_json_error_fallback"] = True
            result["_operation"] = operation

        return result
