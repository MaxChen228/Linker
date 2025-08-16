"""
統一日誌配置模組

此模組為整個應用程式提供集中式的日誌配置管理。
它會從環境變數讀取設定，並根據運行環境（生產或開發）調整預設值，
然後將這些配置應用於 `core.logger` 模組。

主要職責：
- 從環境變數讀取 `LOG_LEVEL`, `LOG_DIR`, `LOG_FORMAT` 等設定。
- 根據 `ENV` 環境變數判斷是否為生產環境，並應用不同的日誌策略。
- 提供 `get_module_logger` 函數，作為應用中所有模組獲取 logger 的統一入口。
- 提供 `set_log_level` 函數，允許在運行時動態調整日誌級別。
"""

import os

from core.logger import Logger, get_logger

# --- 從環境變數讀取日誌配置 ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()  # 可選值: "text" 或 "json"

# --- 根據環境調整預設配置 ---
IS_PRODUCTION = os.getenv("ENV", "development").lower() == "production"

if IS_PRODUCTION:
    # 生產環境預設：記錄到檔案，使用 JSON 格式，級別為 WARNING
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "false").lower() == "true"
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()
    LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
else:
    # 開發環境預設：輸出到控制台，使用 TEXT 格式，級別為 DEBUG
    LOG_TO_CONSOLE = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

# --- 將最終配置設定為環境變數，供 core.logger 模組使用 ---
# 這樣可以確保 logger 模組在被匯入時能讀取到一致的配置
os.environ["LOG_DIR"] = LOG_DIR
os.environ["LOG_LEVEL"] = LOG_LEVEL
os.environ["LOG_TO_CONSOLE"] = str(LOG_TO_CONSOLE).lower()
os.environ["LOG_TO_FILE"] = str(LOG_TO_FILE).lower()
os.environ["LOG_FORMAT"] = LOG_FORMAT


def get_module_logger(module_name: str) -> Logger:
    """
    獲取一個為特定模組配置好的 logger 實例。

    這是應用程式中所有模組獲取 logger 的標準方法。

    Args:
        module_name: 模組的名稱，通常傳入 `__name__`。

    Returns:
        一個配置好的 `Logger` 實例。
    """
    # 簡化模組名稱，例如將 `linker_cli.core.database` 簡化為 `core.database`
    if module_name.startswith("linker_cli."):
        module_name = module_name[len("linker_cli.") :]

    if module_name == "__main__":
        module_name = "main"

    return get_logger(name=module_name)


# 日誌級別的名稱到數字的映射
LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}


def set_log_level(level: str) -> bool:
    """
    在應用程式運行時動態地設定全域日誌級別。

    Args:
        level: 目標日誌級別的字串（不區分大小寫）。

    Returns:
        如果設定成功，返回 True，否則返回 False。
    """
    import logging

    level_upper = level.upper()
    if level_upper in LOG_LEVELS:
        logging.getLogger().setLevel(LOG_LEVELS[level_upper])
        print(f"日誌級別已動態設定為: {level_upper}")
        return True
    print(f"錯誤：無效的日誌級別 '{level}'")
    return False


# 導出公共接口和變數
__all__ = [
    "get_module_logger",
    "set_log_level",
    "IS_PRODUCTION",
    "LOG_LEVEL",
    "LOG_DIR",
    "LOG_FORMAT",
]
