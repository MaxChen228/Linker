"""
統一配置管理器
集中管理所有配置項，提供單一接入點
"""
from typing import Optional, Dict, Any
import os
from core.constants import AIConfig, PracticeConfig, SystemConfig, APIEndpoints
from core.log_config import get_module_logger

logger = get_module_logger(__name__)


class ConfigManager:
    """統一配置管理器 - 單例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config()
            self._initialized = True
    
    def _load_config(self):
        """載入配置"""
        logger.info("Loading configuration from environment and defaults")
        
        # AI 配置
        self.ai_max_tokens = int(os.getenv("AI_MAX_TOKENS", AIConfig.MAX_TOKENS_DEFAULT))
        self.ai_max_retries = int(os.getenv("AI_MAX_RETRIES", AIConfig.MAX_RETRY_ATTEMPTS))
        self.ai_timeout = float(os.getenv("AI_REQUEST_TIMEOUT", AIConfig.REQUEST_TIMEOUT))
        self.lock_timeout = float(os.getenv("LOCK_TIMEOUT", AIConfig.LOCK_TIMEOUT))
        
        # 溫度設定
        self.temperature_generate = float(os.getenv("AI_TEMPERATURE_GENERATE", AIConfig.TEMPERATURE_CREATIVE))
        self.temperature_grade = float(os.getenv("AI_TEMPERATURE_GRADE", AIConfig.TEMPERATURE_PRECISE))
        self.temperature_enrich = float(os.getenv("AI_TEMPERATURE_ENRICH", AIConfig.TEMPERATURE_BALANCED))
        
        # 模型設定
        self.model_generate = os.getenv("GEMINI_GENERATE_MODEL", APIEndpoints.GEMINI_GENERATE_MODEL_DEFAULT)
        self.model_grade = os.getenv("GEMINI_GRADE_MODEL", APIEndpoints.GEMINI_GRADE_MODEL_DEFAULT)
        self.model_enrich = os.getenv("GEMINI_ENRICHMENT_MODEL", APIEndpoints.GEMINI_GRADE_MODEL_DEFAULT)
        
        # 練習配置
        self.practice_recent_days = int(
            os.getenv("PRACTICE_RECENT_DAYS", PracticeConfig.RECENT_RECORDS_DAYS)
        )
        self.practice_max_chinese_chars = int(
            os.getenv("PRACTICE_MAX_CHINESE_CHARS", PracticeConfig.MAX_CHINESE_CHARS)
        )
        
        # 系統配置
        self.request_queue_size = int(
            os.getenv("REQUEST_QUEUE_SIZE", SystemConfig.REQUEST_QUEUE_SIZE)
        )
        self.max_response_size = int(
            os.getenv("MAX_RESPONSE_SIZE", SystemConfig.MAX_RESPONSE_SIZE)
        )
        
        logger.debug(f"Loaded configuration: models={self.model_generate}/{self.model_grade}, "
                    f"max_tokens={self.ai_max_tokens}, retries={self.ai_max_retries}")
    
    def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """獲取模型配置
        
        Args:
            model_type: 模型類型 ('generate', 'grade', 'enrich')
            
        Returns:
            包含模型配置的字典
        """
        configs = {
            "generate": {
                "model": self.model_generate,
                "temperature": self.temperature_generate,
                "max_tokens": self.ai_max_tokens
            },
            "grade": {
                "model": self.model_grade,
                "temperature": self.temperature_grade,
                "max_tokens": self.ai_max_tokens
            },
            "enrich": {
                "model": self.model_enrich,
                "temperature": self.temperature_enrich,
                "max_tokens": self.ai_max_tokens
            }
        }
        
        config = configs.get(model_type, {})
        if not config:
            logger.warning(f"Unknown model type: {model_type}, returning empty config")
        
        return config
    
    def get_ai_config(self) -> Dict[str, Any]:
        """獲取 AI 相關配置"""
        return {
            "max_tokens": self.ai_max_tokens,
            "max_retries": self.ai_max_retries,
            "timeout": self.ai_timeout,
            "retry_backoff": AIConfig.RETRY_BACKOFF_BASE,
            "debug_truncate": AIConfig.DEBUG_RESPONSE_TRUNCATE
        }
    
    def get_practice_config(self) -> Dict[str, Any]:
        """獲取練習相關配置"""
        return {
            "recent_days": self.practice_recent_days,
            "max_chinese_chars": self.practice_max_chinese_chars,
            "score_max": PracticeConfig.SCORE_MAX,
            "score_min": PracticeConfig.SCORE_MIN
        }
    
    def reload(self):
        """重新載入配置（用於測試或熱更新）"""
        logger.info("Reloading configuration")
        self._load_config()
    
    def __str__(self) -> str:
        """返回配置摘要"""
        return (
            f"ConfigManager("
            f"models={self.model_generate}/{self.model_grade}/{self.model_enrich}, "
            f"max_tokens={self.ai_max_tokens}, "
            f"retries={self.ai_max_retries})"
        )


# 全局配置實例
config = ConfigManager()


def get_config() -> ConfigManager:
    """獲取全局配置實例"""
    return config