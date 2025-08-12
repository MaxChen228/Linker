"""
統一配置管理模組
集中管理所有配置項，消除魔術數字
"""

import json
from dataclasses import dataclass
from pathlib import Path

# 引入常數定義，但保持向後兼容性
from core.constants import (
    DisplayConstants,
    LearningConstants,
    APIEndpoints,
    ValidationRules,
    CacheConstants,
)


@dataclass
class DisplaySettings:
    """顯示相關配置"""

    MAX_DISPLAY_ITEMS: int = 10
    MAX_EXAMPLES_PER_POINT: int = 5
    SEPARATOR_WIDTH: int = 50
    SEPARATOR_CHAR: str = "-"
    WIDE_SEPARATOR_CHAR: str = "="
    SEPARATOR_LINE: str = "-" * 50
    WIDE_SEPARATOR_LINE: str = "=" * 50


@dataclass
class LearningSettings:
    """學習相關配置"""

    # 掌握度提升幅度
    MASTERY_INCREMENTS: dict[str, float] = None

    # 掌握度下降幅度
    MASTERY_DECREMENTS: dict[str, float] = None

    # 複習間隔（天數）
    REVIEW_INTERVALS: dict[str, int] = None

    # 掌握度閾值
    MASTERY_THRESHOLDS: dict[str, float] = None

    # 難度級別描述
    DIFFICULTY_LEVELS: dict[int, str] = None

    def __post_init__(self):
        if self.MASTERY_INCREMENTS is None:
            self.MASTERY_INCREMENTS = {
                "systematic": 0.25,
                "isolated": 0.20,
                "enhancement": 0.15,
                "other": 0.15,
            }

        if self.MASTERY_DECREMENTS is None:
            self.MASTERY_DECREMENTS = {"systematic": 0.15, "isolated": 0.10, "other": 0.10}

        if self.REVIEW_INTERVALS is None:
            self.REVIEW_INTERVALS = {
                "immediate": 1,  # 立即複習
                "short": 3,  # 短期記憶
                "medium": 7,  # 中期記憶
                "long": 14,  # 長期記憶
                "mastered": 30,  # 已掌握
            }

        if self.MASTERY_THRESHOLDS is None:
            self.MASTERY_THRESHOLDS = {
                "beginner": 0.3,
                "intermediate": 0.5,
                "advanced": 0.7,
                "expert": 0.9,
            }

        if self.DIFFICULTY_LEVELS is None:
            self.DIFFICULTY_LEVELS = {
                1: "初級 (國中基礎)",
                2: "中級 (高中核心)",
                3: "高級 (學測挑戰)",
            }


@dataclass
class CacheSettings:
    """緩存配置（已禁用）"""

    CACHE_TTL_SECONDS: int = 0  # 完全禁用緩存
    MAX_CACHE_SIZE: int = 0  # 不儲存任何緩存
    CACHE_KEY_LENGTH: int = 50  # 緩存鍵的截取長度（已無作用）


@dataclass
class APISettings:
    """API相關配置"""

    DEFAULT_MODEL: str = "gemini-2.0-flash-exp"
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RESPONSE_MIME_TYPE: str = "application/json"


@dataclass
class ErrorPrioritySettings:
    """錯誤優先級配置"""

    PRIORITIES: dict[str, int] = None

    def __post_init__(self):
        if self.PRIORITIES is None:
            self.PRIORITIES = {
                "systematic": 1,  # 系統性錯誤 - 最高優先
                "isolated": 2,  # 單一性錯誤
                "other": 3,  # 其他錯誤
                "enhancement": 4,  # 可以更好 - 最低優先
            }


@dataclass
class PracticeSettings:
    """練習相關配置"""

    MIN_SENTENCE_LENGTH: int = 10
    MAX_SENTENCE_LENGTH: int = 30
    RECENT_MISTAKES_COUNT: int = 10  # 分析最近N次錯誤
    MIN_PRACTICE_FOR_ANALYSIS: int = 5  # 最少練習次數才進行AI分析

    # 難度映射
    DIFFICULTY_DESCRIPTIONS: dict[int, str] = None

    def __post_init__(self):
        if self.DIFFICULTY_DESCRIPTIONS is None:
            self.DIFFICULTY_DESCRIPTIONS = {
                1: "國中基礎程度，簡單詞彙和基本句型",
                2: "高中程度，包含常見片語和複雜句型",
                3: "學測程度，包含進階詞彙和複雜語法",
            }


@dataclass
class UISettings:
    """UI相關配置"""

    # 表情符號映射
    CATEGORY_EMOJIS: dict[str, str] = None

    # 優先級表情符號
    PRIORITY_EMOJIS: dict[int, str] = None

    # 掌握度顯示
    MASTERY_BAR_LENGTH: int = 10
    MASTERY_BAR_FILLED: str = "█"
    MASTERY_BAR_EMPTY: str = "░"

    def __post_init__(self):
        if self.CATEGORY_EMOJIS is None:
            self.CATEGORY_EMOJIS = {
                "systematic": "⚙️",
                "isolated": "📌",
                "enhancement": "✨",
                "other": "❓",
            }

        if self.PRIORITY_EMOJIS is None:
            self.PRIORITY_EMOJIS = {1: "🔥", 2: "⭐", 3: "💫", 4: "☆"}


class Settings:
    """統一配置類"""

    def __init__(self):
        self.display = DisplaySettings()
        self.learning = LearningSettings()
        self.cache = CacheSettings()
        self.api = APISettings()
        self.error_priority = ErrorPrioritySettings()
        self.practice = PracticeSettings()
        self.ui = UISettings()

    @classmethod
    def load_from_file(cls, config_file: str = "config.json") -> "Settings":
        """從文件加載配置"""
        settings = cls()
        config_path = Path(config_file)

        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    data = json.load(f)

                # 更新各個配置部分
                if "display" in data:
                    for key, value in data["display"].items():
                        if hasattr(settings.display, key):
                            setattr(settings.display, key, value)

                if "learning" in data:
                    for key, value in data["learning"].items():
                        if hasattr(settings.learning, key):
                            setattr(settings.learning, key, value)

                if "cache" in data:
                    for key, value in data["cache"].items():
                        if hasattr(settings.cache, key):
                            setattr(settings.cache, key, value)

                if "api" in data:
                    for key, value in data["api"].items():
                        if hasattr(settings.api, key):
                            setattr(settings.api, key, value)

                print(f"✅ 已從 {config_file} 加載配置")
            except Exception as e:
                print(f"⚠️ 加載配置文件失敗: {e}，使用默認配置")

        return settings

    def save_to_file(self, config_file: str = "config.json"):
        """保存配置到文件"""
        data = {
            "display": {
                "MAX_DISPLAY_ITEMS": self.display.MAX_DISPLAY_ITEMS,
                "MAX_EXAMPLES_PER_POINT": self.display.MAX_EXAMPLES_PER_POINT,
                "SEPARATOR_WIDTH": self.display.SEPARATOR_WIDTH,
                "SEPARATOR_CHAR": self.display.SEPARATOR_CHAR,
                "WIDE_SEPARATOR_CHAR": self.display.WIDE_SEPARATOR_CHAR,
            },
            "learning": {
                "MASTERY_INCREMENTS": self.learning.MASTERY_INCREMENTS,
                "MASTERY_DECREMENTS": self.learning.MASTERY_DECREMENTS,
                "REVIEW_INTERVALS": self.learning.REVIEW_INTERVALS,
                "MASTERY_THRESHOLDS": self.learning.MASTERY_THRESHOLDS,
                "DIFFICULTY_LEVELS": self.learning.DIFFICULTY_LEVELS,
            },
            "cache": {
                "CACHE_TTL_SECONDS": self.cache.CACHE_TTL_SECONDS,
                "MAX_CACHE_SIZE": self.cache.MAX_CACHE_SIZE,
                "CACHE_KEY_LENGTH": self.cache.CACHE_KEY_LENGTH,
            },
            "api": {
                "DEFAULT_MODEL": self.api.DEFAULT_MODEL,
                "REQUEST_TIMEOUT": self.api.REQUEST_TIMEOUT,
                "MAX_RETRIES": self.api.MAX_RETRIES,
                "RESPONSE_MIME_TYPE": self.api.RESPONSE_MIME_TYPE,
            },
            "practice": {
                "MIN_SENTENCE_LENGTH": self.practice.MIN_SENTENCE_LENGTH,
                "MAX_SENTENCE_LENGTH": self.practice.MAX_SENTENCE_LENGTH,
                "RECENT_MISTAKES_COUNT": self.practice.RECENT_MISTAKES_COUNT,
                "MIN_PRACTICE_FOR_ANALYSIS": self.practice.MIN_PRACTICE_FOR_ANALYSIS,
            },
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 配置已保存到 {config_file}")


@dataclass
class ServiceSettings:
    """服務層配置"""
    
    # AI服務配置
    AI_REQUEST_TIMEOUT: int = APIEndpoints.GEMINI_REQUEST_TIMEOUT
    AI_MAX_RETRIES: int = APIEndpoints.GEMINI_MAX_RETRIES
    AI_TEMPERATURE_CREATIVE: float = APIEndpoints.TEMPERATURE_CREATIVE
    AI_TEMPERATURE_PRECISE: float = APIEndpoints.TEMPERATURE_PRECISE
    
    # 批次處理配置
    BATCH_SIZE_SMALL: int = 5
    BATCH_SIZE_MEDIUM: int = 10
    BATCH_SIZE_LARGE: int = 20
    
    # 併發配置
    MAX_CONCURRENT_REQUESTS: int = 3
    REQUEST_QUEUE_SIZE: int = 100


@dataclass  
class RepositorySettings:
    """資料存取層配置"""
    
    # 檔案操作配置
    FILE_ENCODING: str = "utf-8"
    BACKUP_ENABLED: bool = True
    BACKUP_MAX_COUNT: int = 5
    
    # 資料驗證配置
    VALIDATE_ON_LOAD: bool = True
    VALIDATE_ON_SAVE: bool = True
    AUTO_MIGRATE: bool = True
    
    # 查詢配置
    DEFAULT_LIMIT: int = DisplayConstants.DEFAULT_PAGE_SIZE
    MAX_LIMIT: int = DisplayConstants.MAX_PAGE_SIZE
    ENABLE_CACHING: bool = False  # 目前禁用


@dataclass
class ResponseSettings:
    """回應處理配置"""
    
    # HTTP回應配置  
    DEFAULT_TIMEOUT: int = APIEndpoints.GEMINI_REQUEST_TIMEOUT
    MAX_RESPONSE_SIZE: int = 1024 * 1024  # 1MB
    
    # 錯誤處理配置
    INCLUDE_ERROR_DETAILS: bool = True
    LOG_REQUEST_DETAILS: bool = True
    SANITIZE_ERROR_MESSAGES: bool = True
    
    # 快取配置（已禁用）
    CACHE_ENABLED: bool = False
    CACHE_TTL: int = CacheConstants.CACHE_TTL_SECONDS


@dataclass
class ValidationSettings:
    """驗證相關配置"""
    
    # 輸入驗證配置
    STRICT_VALIDATION: bool = True
    ALLOW_EMPTY_TRANSLATIONS: bool = False
    NORMALIZE_WHITESPACE: bool = True
    
    # 中文驗證配置
    MIN_CHINESE_CHARS: int = 2
    MAX_CHINESE_CHARS: int = 100
    ALLOW_MIXED_LANGUAGE: bool = True
    
    # 英文驗證配置
    MIN_ENGLISH_WORDS: int = 1
    MAX_ENGLISH_WORDS: int = 50
    CHECK_GRAMMAR: bool = False  # 暫時不啟用文法檢查
    
    # 特殊字符處理
    ALLOWED_PUNCTUATION: str = ".,!?;:()[]{}\"'-"
    STRIP_EXTRA_SPACES: bool = True
    

class Settings:
    """統一配置類"""

    def __init__(self):
        self.display = DisplaySettings()
        self.learning = LearningSettings()
        self.cache = CacheSettings()
        self.api = APISettings()
        self.error_priority = ErrorPrioritySettings()
        self.practice = PracticeSettings()
        self.ui = UISettings()
        
        # 新增配置區塊
        self.service = ServiceSettings()
        self.repository = RepositorySettings()
        self.response = ResponseSettings()
        self.validation = ValidationSettings()

    @classmethod
    def load_from_file(cls, config_file: str = "config.json") -> "Settings":
        """從文件加載配置"""
        settings = cls()
        config_path = Path(config_file)

        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    data = json.load(f)

                # 更新各個配置部分（保持向後兼容）
                config_sections = [
                    ("display", settings.display),
                    ("learning", settings.learning),
                    ("cache", settings.cache),
                    ("api", settings.api),
                    ("practice", settings.practice),
                    ("service", settings.service),
                    ("repository", settings.repository),
                    ("response", settings.response),
                    ("validation", settings.validation),
                ]
                
                for section_name, section_obj in config_sections:
                    if section_name in data:
                        for key, value in data[section_name].items():
                            if hasattr(section_obj, key):
                                setattr(section_obj, key, value)

                print(f"✅ 已從 {config_file} 加載配置")
            except Exception as e:
                print(f"⚠️ 加載配置文件失敗: {e}，使用默認配置")

        return settings

    def save_to_file(self, config_file: str = "config.json"):
        """保存配置到文件"""
        data = {
            "display": {
                "MAX_DISPLAY_ITEMS": self.display.MAX_DISPLAY_ITEMS,
                "MAX_EXAMPLES_PER_POINT": self.display.MAX_EXAMPLES_PER_POINT,
                "SEPARATOR_WIDTH": self.display.SEPARATOR_WIDTH,
                "SEPARATOR_CHAR": self.display.SEPARATOR_CHAR,
                "WIDE_SEPARATOR_CHAR": self.display.WIDE_SEPARATOR_CHAR,
            },
            "learning": {
                "MASTERY_INCREMENTS": self.learning.MASTERY_INCREMENTS,
                "MASTERY_DECREMENTS": self.learning.MASTERY_DECREMENTS,
                "REVIEW_INTERVALS": self.learning.REVIEW_INTERVALS,
                "MASTERY_THRESHOLDS": self.learning.MASTERY_THRESHOLDS,
                "DIFFICULTY_LEVELS": self.learning.DIFFICULTY_LEVELS,
            },
            "cache": {
                "CACHE_TTL_SECONDS": self.cache.CACHE_TTL_SECONDS,
                "MAX_CACHE_SIZE": self.cache.MAX_CACHE_SIZE,
                "CACHE_KEY_LENGTH": self.cache.CACHE_KEY_LENGTH,
            },
            "api": {
                "DEFAULT_MODEL": self.api.DEFAULT_MODEL,
                "REQUEST_TIMEOUT": self.api.REQUEST_TIMEOUT,
                "MAX_RETRIES": self.api.MAX_RETRIES,
                "RESPONSE_MIME_TYPE": self.api.RESPONSE_MIME_TYPE,
            },
            "practice": {
                "MIN_SENTENCE_LENGTH": self.practice.MIN_SENTENCE_LENGTH,
                "MAX_SENTENCE_LENGTH": self.practice.MAX_SENTENCE_LENGTH,
                "RECENT_MISTAKES_COUNT": self.practice.RECENT_MISTAKES_COUNT,
                "MIN_PRACTICE_FOR_ANALYSIS": self.practice.MIN_PRACTICE_FOR_ANALYSIS,
            },
            # 新增配置區塊
            "service": {
                "AI_REQUEST_TIMEOUT": self.service.AI_REQUEST_TIMEOUT,
                "AI_MAX_RETRIES": self.service.AI_MAX_RETRIES,
                "BATCH_SIZE_MEDIUM": self.service.BATCH_SIZE_MEDIUM,
                "MAX_CONCURRENT_REQUESTS": self.service.MAX_CONCURRENT_REQUESTS,
            },
            "repository": {
                "FILE_ENCODING": self.repository.FILE_ENCODING,
                "BACKUP_ENABLED": self.repository.BACKUP_ENABLED,
                "DEFAULT_LIMIT": self.repository.DEFAULT_LIMIT,
                "VALIDATE_ON_SAVE": self.repository.VALIDATE_ON_SAVE,
            },
            "response": {
                "DEFAULT_TIMEOUT": self.response.DEFAULT_TIMEOUT,
                "INCLUDE_ERROR_DETAILS": self.response.INCLUDE_ERROR_DETAILS,
                "CACHE_ENABLED": self.response.CACHE_ENABLED,
            },
            "validation": {
                "STRICT_VALIDATION": self.validation.STRICT_VALIDATION,
                "MIN_CHINESE_CHARS": self.validation.MIN_CHINESE_CHARS,
                "MAX_ENGLISH_WORDS": self.validation.MAX_ENGLISH_WORDS,
                "NORMALIZE_WHITESPACE": self.validation.NORMALIZE_WHITESPACE,
            },
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ 配置已保存到 {config_file}")


# 創建全局配置實例
settings = Settings()
