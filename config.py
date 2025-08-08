"""
配置管理模組
"""

import os
from pathlib import Path


class Config:
    """應用配置"""

    # API 配置
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    # 路徑配置
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"

    # 緩存配置
    CACHE_TTL = 300  # 5分鐘
    MAX_CACHE_SIZE = 100

    # 學習配置
    REVIEW_INTERVALS = {
        "immediate": 1,  # 立即複習
        "short": 3,  # 短期記憶
        "medium": 7,  # 中期記憶
        "long": 14,  # 長期記憶
        "mastered": 30,  # 已掌握
    }

    # 難度級別
    DIFFICULTY_LEVELS = {1: "初級 (國中基礎)", 2: "中級 (高中核心)", 3: "高級 (學測挑戰)"}

    # 錯誤分類優先級
    ERROR_PRIORITIES = {
        "systematic": 1,  # 系統性錯誤 - 最高優先
        "isolated": 2,  # 單一性錯誤
        "other": 3,  # 其他錯誤
        "enhancement": 4,  # 可以更好 - 最低優先
    }

    # 掌握度閾值
    MASTERY_THRESHOLDS = {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.7, "expert": 0.9}

    @classmethod
    def validate(cls):
        """驗證配置"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("請設定 GEMINI_API_KEY 環境變數")

        # 創建必要的目錄
        cls.DATA_DIR.mkdir(exist_ok=True)

        return True
