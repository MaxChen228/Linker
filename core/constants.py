"""
統一常數定義模組
集中管理項目中的所有常數，消除魔法數字和重複的字符串
"""

from enum import Enum
from typing import Dict, List


class APIEndpoints:
    """API 相關常數"""
    
    # Gemini API
    GEMINI_GENERATE_MODEL_DEFAULT = "gemini-2.5-flash"
    GEMINI_GRADE_MODEL_DEFAULT = "gemini-2.5-pro"
    GEMINI_REQUEST_TIMEOUT = 30
    GEMINI_MAX_RETRIES = 3
    
    # Response格式
    RESPONSE_MIME_TYPE_JSON = "application/json"
    RESPONSE_MIME_TYPE_HTML = "text/html"
    
    # Generation配置
    TEMPERATURE_CREATIVE = 1.0
    TEMPERATURE_PRECISE = 0.2
    TOP_P_DEFAULT = 0.95
    TOP_K_DEFAULT = 40


class HTTPStatus:
    """HTTP 狀態碼常數"""
    
    # 成功狀態碼
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    
    # 重定向狀態碼
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    
    # 客戶端錯誤狀態碼
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    
    # 服務器錯誤狀態碼
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class ErrorTypes:
    """錯誤類型常數"""
    
    # 主要錯誤類別
    SYSTEMATIC = "systematic"
    ISOLATED = "isolated"
    ENHANCEMENT = "enhancement"
    OTHER = "other"
    
    # 系統性錯誤子類型
    VERB_CONJUGATION = "verb_conjugation"
    TENSE = "tense"
    VOICE = "voice"
    AGREEMENT = "agreement"
    
    # 單一性錯誤子類型
    VOCABULARY = "vocabulary"
    COLLOCATION = "collocation"
    PREPOSITION = "preposition"
    SPELLING = "spelling"
    
    # 可以更好子類型
    NATURALNESS = "naturalness"
    STYLE = "style"
    
    # 其他錯誤子類型
    OMISSION = "omission"
    MISUNDERSTANDING = "misunderstanding"


class FilePaths:
    """文件路徑常數"""
    
    # 靜態資源路徑
    STATIC_DIR = "/static"
    TEMPLATES_DIR = "/templates"
    FAVICON_ICO = "/favicon.ico"
    
    # API路徑
    API_GRADE_ANSWER = "/api/grade-answer"
    API_GENERATE_QUESTION = "/api/generate-question"
    API_GENERATE_TAGGED = "/api/generate-tagged-question"
    API_PREVIEW_TAGGED = "/api/preview-tagged-question"
    API_TAGS = "/api/tags"
    API_VALIDATE_COMBINATION = "/api/validate-tag-combination"
    API_TAG_TEMPLATES = "/api/tag-templates"
    
    # 頁面路徑
    HOME = "/"
    PRACTICE = "/practice"
    KNOWLEDGE = "/knowledge"
    PATTERNS = "/patterns"
    HEALTHZ = "/healthz"
    
    # 資料檔案路徑
    DATA_KNOWLEDGE_JSON = "data/knowledge.json"
    DATA_PRACTICE_LOG_JSON = "data/practice_log.json"
    DATA_PATTERNS_JSON = "data/patterns_enriched_complete.json"
    DATA_GRAMMAR_PATTERNS_JSON = "data/grammar_patterns.json"


class ValidationRules:
    """驗證規則常數"""
    
    # 句子長度限制
    MIN_SENTENCE_LENGTH = 1
    MAX_SENTENCE_LENGTH = 500
    MIN_PRACTICE_SENTENCE_LENGTH = 10
    MAX_PRACTICE_SENTENCE_LENGTH = 30
    
    # 翻譯長度限制
    MIN_TRANSLATION_LENGTH = 1
    MAX_TRANSLATION_LENGTH = 1000
    
    # 文本長度限制
    MIN_HINT_LENGTH = 0
    MAX_HINT_LENGTH = 200
    MIN_EXPLANATION_LENGTH = 5
    MAX_EXPLANATION_LENGTH = 500
    
    # 查詢參數限制
    MIN_QUERY_LENGTH = 1
    MAX_QUERY_LENGTH = 100
    
    # 數值範圍限制
    MIN_DIFFICULTY_LEVEL = 1
    MAX_DIFFICULTY_LEVEL = 5
    MIN_MASTERY_LEVEL = 0.0
    MAX_MASTERY_LEVEL = 1.0
    
    # 英文單詞數量限制
    MIN_ENGLISH_WORDS = 1
    MAX_ENGLISH_WORDS = 50
    
    # 練習模式
    VALID_PRACTICE_MODES = ["new", "review"]
    VALID_SENTENCE_LENGTHS = ["short", "medium", "long"]


class UIMessages:
    """用戶介面訊息常數"""
    
    # 成功訊息
    SUCCESS_PRACTICE_COMPLETED = "練習完成！"
    SUCCESS_KNOWLEDGE_UPDATED = "知識點已更新"
    SUCCESS_CONFIG_SAVED = "配置已保存"
    
    # 錯誤訊息
    ERROR_INVALID_INPUT = "輸入格式不正確"
    ERROR_SENTENCE_TOO_SHORT = "句子太短，請輸入更完整的句子"
    ERROR_SENTENCE_TOO_LONG = "句子太長，請簡化內容"
    ERROR_TRANSLATION_EMPTY = "請輸入翻譯內容"
    ERROR_AI_SERVICE_UNAVAILABLE = "AI 服務暫時無法使用，請稍後再試"
    ERROR_NETWORK_FAILED = "網路連線失敗，請檢查網路連線"
    ERROR_API_KEY_MISSING = "AI 服務未正確配置，請檢查 GEMINI_API_KEY 環境變數設置"
    ERROR_DEPENDENCY_MISSING = "AI 服務依賴未安裝，請執行 pip install google-generativeai"
    ERROR_KNOWLEDGE_POINT_NOT_FOUND = "找不到指定的知識點"
    ERROR_PATTERN_NOT_FOUND = "找不到指定的句型"
    
    # 提示訊息
    INFO_NO_REVIEW_POINTS = "目前沒有需要複習的知識點（單一性錯誤或可以更好類別）。請先練習新題目累積知識點。"
    INFO_LOADING = "載入中..."
    INFO_GENERATING_QUESTION = "正在生成題目..."
    INFO_GRADING_ANSWER = "正在批改答案..."
    
    # 複習相關訊息
    REVIEW_DUE_TODAY = "今天"
    REVIEW_DUE_TOMORROW = "明天"
    REVIEW_DUE_DAYS_FORMAT = "{} 天後"
    REVIEW_OVERDUE = "已到期"


class LearningConstants:
    """學習相關常數"""
    
    # 掌握度調整幅度
    MASTERY_INCREMENT_SYSTEMATIC = 0.25
    MASTERY_INCREMENT_ISOLATED = 0.20
    MASTERY_INCREMENT_ENHANCEMENT = 0.15
    MASTERY_INCREMENT_OTHER = 0.15
    
    MASTERY_DECREMENT_SYSTEMATIC = 0.15
    MASTERY_DECREMENT_ISOLATED = 0.10
    MASTERY_DECREMENT_OTHER = 0.10
    
    # 複習間隔（天數）
    REVIEW_INTERVAL_IMMEDIATE = 1
    REVIEW_INTERVAL_SHORT = 3
    REVIEW_INTERVAL_MEDIUM = 7
    REVIEW_INTERVAL_LONG = 14
    REVIEW_INTERVAL_MASTERED = 30
    
    # 掌握度閾值
    MASTERY_THRESHOLD_BEGINNER = 0.3
    MASTERY_THRESHOLD_INTERMEDIATE = 0.5
    MASTERY_THRESHOLD_ADVANCED = 0.7
    MASTERY_THRESHOLD_EXPERT = 0.9
    
    # 錯誤優先級
    ERROR_PRIORITY_SYSTEMATIC = 1
    ERROR_PRIORITY_ISOLATED = 2
    ERROR_PRIORITY_OTHER = 3
    ERROR_PRIORITY_ENHANCEMENT = 4
    
    # 複習間隔倍數
    REVIEW_MULTIPLIER_SYSTEMATIC = 0.8
    REVIEW_MULTIPLIER_ISOLATED = 1.0
    REVIEW_MULTIPLIER_OTHER = 1.0
    REVIEW_MULTIPLIER_ENHANCEMENT = 1.5


class DisplayConstants:
    """顯示相關常數"""
    
    # 列表顯示限制
    MAX_DISPLAY_ITEMS = 10
    MAX_EXAMPLES_PER_POINT = 5
    MAX_REVIEW_CANDIDATES = 10
    MAX_RELATED_MISTAKES = 10
    MAX_PATTERNS_DISPLAY = 200
    MAX_RECENT_MISTAKES = 50
    
    # 分頁相關
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 文本截取長度
    QUERY_PREVIEW_LENGTH = 200
    USER_AGENT_MAX_LENGTH = 200
    PROMPT_PREVIEW_LENGTH = 200
    CHINESE_SENTENCE_PREVIEW = 50
    ENGLISH_TRANSLATION_PREVIEW = 50
    
    # 分隔符
    SEPARATOR_WIDTH = 50
    SEPARATOR_CHAR = "-"
    WIDE_SEPARATOR_CHAR = "="
    
    # 掌握度顯示
    MASTERY_BAR_LENGTH = 10
    MASTERY_BAR_FILLED = "█"
    MASTERY_BAR_EMPTY = "░"


class CacheConstants:
    """緩存相關常數（已禁用）"""
    
    CACHE_TTL_SECONDS = 0  # 完全禁用緩存
    MAX_CACHE_SIZE = 0  # 不儲存任何緩存
    CACHE_KEY_LENGTH = 50  # 緩存鍵的截取長度（已無作用）


class RequestConstants:
    """請求相關常數"""
    
    # 超時設置
    REQUEST_TIMEOUT_SECONDS = 30
    
    # 重試設置
    MAX_RETRY_ATTEMPTS = 3
    RETRY_BACKOFF_FACTOR = 2
    
    # 請求頭
    CONTENT_TYPE_JSON = "application/json"
    CONTENT_TYPE_HTML = "text/html; charset=utf-8"
    CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"
    
    # 請求大小限制
    MAX_REQUEST_BODY_SIZE = 1024 * 1024  # 1MB
    MAX_FORM_FIELD_SIZE = 10240  # 10KB


class EnvironmentConstants:
    """環境變數常數"""
    
    # AI服務相關
    ENV_GEMINI_API_KEY = "GEMINI_API_KEY"
    ENV_GEMINI_GENERATE_MODEL = "GEMINI_GENERATE_MODEL"
    ENV_GEMINI_GRADE_MODEL = "GEMINI_GRADE_MODEL"
    
    # 部署相關
    ENV_RENDER = "RENDER"
    ENV_DATA_DIR = "DATA_DIR"
    ENV_PORT = "PORT"
    ENV_HOST = "HOST"
    
    # 日誌相關
    ENV_LOG_LEVEL = "LOG_LEVEL"
    ENV_LOG_FORMAT = "LOG_FORMAT"


class CategoryEmojis:
    """分類表情符號常數"""
    
    SYSTEMATIC = "⚙️"
    ISOLATED = "📌"
    ENHANCEMENT = "✨"
    OTHER = "❓"


class PriorityEmojis:
    """優先級表情符號常數"""
    
    PRIORITY_1 = "🔥"  # 最高優先
    PRIORITY_2 = "⭐"
    PRIORITY_3 = "💫"
    PRIORITY_4 = "☆"   # 最低優先


class DifficultyLevels:
    """難度級別常數"""
    
    LEVEL_1_NAME = "初級 (國中基礎)"
    LEVEL_2_NAME = "中級 (高中核心)"
    LEVEL_3_NAME = "高級 (學測挑戰)"
    LEVEL_4_NAME = "進階 (指考程度)"
    LEVEL_5_NAME = "專業 (學術用語)"
    
    LEVEL_DESCRIPTIONS = {
        1: "國中基礎程度，簡單詞彙和基本句型",
        2: "高中程度，包含常見片語和複雜句型",
        3: "學測程度，包含進階詞彙和複雜語法",
        4: "指考程度，包含高階詞彙和複雜結構",
        5: "進階程度，包含學術或專業用語",
    }


class SentenceLengthHints:
    """句子長度提示常數"""
    
    SHORT = "字數約10-20，句子簡潔"
    MEDIUM = "字數約20-35，結構完整"
    LONG = "字數約35-60，包含從屬子句或分詞構句"
    
    HINTS = {
        "short": SHORT,
        "medium": MEDIUM,
        "long": LONG,
    }


class LoggingConstants:
    """日誌相關常數"""
    
    # 日誌級別
    LOG_LEVEL_DEBUG = "DEBUG"
    LOG_LEVEL_INFO = "INFO"
    LOG_LEVEL_WARNING = "WARNING"
    LOG_LEVEL_ERROR = "ERROR"
    LOG_LEVEL_CRITICAL = "CRITICAL"
    
    # 日誌格式
    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 過濾的請求路徑
    FILTERED_PATHS = [
        "/.well-known/appspecific",
        "/favicon.ico",
        "/__vite_",
    ]


# 創建常用的字典映射，以便在其他模組中使用
MASTERY_INCREMENTS = {
    ErrorTypes.SYSTEMATIC: LearningConstants.MASTERY_INCREMENT_SYSTEMATIC,
    ErrorTypes.ISOLATED: LearningConstants.MASTERY_INCREMENT_ISOLATED,
    ErrorTypes.ENHANCEMENT: LearningConstants.MASTERY_INCREMENT_ENHANCEMENT,
    ErrorTypes.OTHER: LearningConstants.MASTERY_INCREMENT_OTHER,
}

MASTERY_DECREMENTS = {
    ErrorTypes.SYSTEMATIC: LearningConstants.MASTERY_DECREMENT_SYSTEMATIC,
    ErrorTypes.ISOLATED: LearningConstants.MASTERY_DECREMENT_ISOLATED,
    ErrorTypes.OTHER: LearningConstants.MASTERY_DECREMENT_OTHER,
}

REVIEW_INTERVALS = {
    "immediate": LearningConstants.REVIEW_INTERVAL_IMMEDIATE,
    "short": LearningConstants.REVIEW_INTERVAL_SHORT,
    "medium": LearningConstants.REVIEW_INTERVAL_MEDIUM,
    "long": LearningConstants.REVIEW_INTERVAL_LONG,
    "mastered": LearningConstants.REVIEW_INTERVAL_MASTERED,
}

MASTERY_THRESHOLDS = {
    "beginner": LearningConstants.MASTERY_THRESHOLD_BEGINNER,
    "intermediate": LearningConstants.MASTERY_THRESHOLD_INTERMEDIATE,
    "advanced": LearningConstants.MASTERY_THRESHOLD_ADVANCED,
    "expert": LearningConstants.MASTERY_THRESHOLD_EXPERT,
}

ERROR_PRIORITIES = {
    ErrorTypes.SYSTEMATIC: LearningConstants.ERROR_PRIORITY_SYSTEMATIC,
    ErrorTypes.ISOLATED: LearningConstants.ERROR_PRIORITY_ISOLATED,
    ErrorTypes.OTHER: LearningConstants.ERROR_PRIORITY_OTHER,
    ErrorTypes.ENHANCEMENT: LearningConstants.ERROR_PRIORITY_ENHANCEMENT,
}

CATEGORY_EMOJIS = {
    ErrorTypes.SYSTEMATIC: CategoryEmojis.SYSTEMATIC,
    ErrorTypes.ISOLATED: CategoryEmojis.ISOLATED,
    ErrorTypes.ENHANCEMENT: CategoryEmojis.ENHANCEMENT,
    ErrorTypes.OTHER: CategoryEmojis.OTHER,
}

PRIORITY_EMOJIS = {
    1: PriorityEmojis.PRIORITY_1,
    2: PriorityEmojis.PRIORITY_2,
    3: PriorityEmojis.PRIORITY_3,
    4: PriorityEmojis.PRIORITY_4,
}


class AIConfig:
    """AI 服務配置常數"""
    
    # Token 限制
    MAX_TOKENS_DEFAULT = 3000
    MAX_TOKENS_ENRICHMENT = 3000
    
    # 溫度設定
    TEMPERATURE_CREATIVE = 1.0    # 用於生成題目
    TEMPERATURE_BALANCED = 0.7    # 用於擴充內容
    TEMPERATURE_PRECISE = 0.2     # 用於批改
    
    # 重試設定
    MAX_RETRY_ATTEMPTS = 3
    RETRY_BACKOFF_BASE = 2  # 指數退避基數
    
    # 超時設定
    REQUEST_TIMEOUT = 30.0
    LOCK_TIMEOUT = 30.0
    
    # 回應截斷
    DEBUG_RESPONSE_TRUNCATE = 500

class PracticeConfig:
    """練習系統配置"""
    
    # 分數範圍
    SCORE_MAX = 100
    SCORE_MIN = 0
    
    # 記錄查詢
    RECENT_RECORDS_DAYS = 365
    
    # 輸入限制
    MAX_CHINESE_CHARS = 100

class SystemConfig:
    """系統配置"""
    
    REQUEST_QUEUE_SIZE = 100
    MAX_RESPONSE_SIZE = 1024 * 1024  # 1MB
    TEST_TIMEOUT = 5.0