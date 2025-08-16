"""
核心設定套件，包含端口和資料庫配置管理

將配置相關的模組分組管理，避免與 core.config.py 發生命名衝突
"""

from .ports import PortConfig, get_app_host, get_app_port, get_app_url, get_db_port, get_port_config

__all__ = [
    "PortConfig",
    "get_port_config",
    "get_app_port",
    "get_app_host",
    "get_db_port",
    "get_app_url",
]
