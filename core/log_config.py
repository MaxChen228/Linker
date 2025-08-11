"""
統一日誌配置
所有模組都應該使用這個配置來獲取 logger
"""

import os

from core.logger import Logger, get_logger

# 環境變數配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()  # text or json

# 生產環境檢測
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

# 根據環境調整預設值
if IS_PRODUCTION:
    # 生產環境：記錄到文件，使用 JSON 格式，不輸出到控制台
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "false").lower() == "true"
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING")
else:
    # 開發環境：輸出到控制台，使用文字格式
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

# 一次性設置環境變數，供 logger.py 使用
os.environ["LOG_DIR"] = LOG_DIR
os.environ["LOG_LEVEL"] = LOG_LEVEL
os.environ["LOG_TO_CONSOLE"] = str(LOG_TO_CONSOLE).lower()
os.environ["LOG_TO_FILE"] = str(LOG_TO_FILE).lower()
os.environ["LOG_FORMAT"] = LOG_FORMAT

def get_module_logger(module_name: str) -> Logger:
    """
    獲取模組專用的 logger
    
    Args:
        module_name: 模組名稱，建議使用 __name__
        
    Returns:
        配置好的 Logger 實例
    """
    # 簡化模組名稱（去除 linker_cli. 前綴）
    if module_name.startswith("linker_cli."):
        module_name = module_name[11:]
    
    # 如果是 __main__ 則使用更有意義的名稱
    if module_name == "__main__":
        module_name = "main"
    
    # 直接調用 get_logger，它會自動從環境變數讀取配置
    # 不需要重複設置環境變數
    return get_logger(name=module_name)

# 不再預定義 logger 實例，避免重複初始化
# 每個模組應該在自己的代碼中調用 get_module_logger(__name__)

# 日誌級別映射（用於動態調整）
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

def set_log_level(level: str):
    """動態設置日誌級別"""
    import logging
    level = level.upper()
    if level in LOG_LEVELS:
        logging.getLogger().setLevel(LOG_LEVELS[level])
        return True
    return False

# 導出
__all__ = [
    "get_module_logger",
    "set_log_level",
    "IS_PRODUCTION",
    "LOG_LEVEL",
    "LOG_DIR",
    "LOG_FORMAT"
]
