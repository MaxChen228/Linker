"""
統一數據庫配置管理系統
TASK-34: 消除硬編碼 - 安全的數據庫連接配置

此模組提供統一的數據庫配置管理，消除硬編碼的數據庫連接信息，
提高安全性並簡化環境配置管理。
"""

import logging
import os
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

# 設置日誌
logger = logging.getLogger(__name__)


class DatabaseConfigError(Exception):
    """數據庫配置相關的錯誤"""
    pass


class DatabaseConfig:
    """
    統一數據庫配置管理類

    功能：
    - 安全的數據庫URL管理（不暴露敏感信息）
    - 環境特定的配置支持
    - 測試環境自動配置
    - 配置驗證和錯誤處理
    """

    def __init__(self):
        """初始化數據庫配置管理器"""
        self._base_url = None
        self._parsed_url = None
        self._environment = self._detect_environment()

        # 嘗試載入配置
        self._load_configuration()

    def _detect_environment(self) -> str:
        """檢測當前運行環境"""
        # 檢測是否為測試環境
        if any(test_indicator in os.environ.get('_', '')
               for test_indicator in ['pytest', 'test', 'unittest']):
            return 'test'

        # 檢測是否為CI環境
        if any(ci_var in os.environ
               for ci_var in ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS']):
            return 'ci'

        # 檢測是否為生產環境
        if os.getenv('ENVIRONMENT', '').lower() in ['production', 'prod']:
            return 'production'

        # 檢測是否為開發環境
        if os.getenv('DEV_MODE', 'false').lower() == 'true':
            return 'development'

        # 默認為開發環境
        return 'development'

    def _load_configuration(self):
        """載入數據庫配置"""
        try:
            # 嘗試從環境變數載入
            self._base_url = self._get_database_url_from_env()

            if self._base_url:
                self._parsed_url = urlparse(self._base_url)
                self._validate_url()
            else:
                # 如果沒有配置，根據環境提供建議
                self._provide_configuration_guidance()

        except Exception as e:
            logger.error(f"數據庫配置載入失敗: {e}")
            raise DatabaseConfigError(f"無法載入數據庫配置: {e}")

    def _get_database_url_from_env(self) -> Optional[str]:
        """從環境變數獲取數據庫URL"""
        # 優先級順序的環境變數名稱
        env_vars = [
            'DATABASE_URL',           # 標準變數名
            'DB_URL',                # 簡化變數名
            f'{self._environment.upper()}_DATABASE_URL',  # 環境特定變數
        ]

        for var_name in env_vars:
            url = os.getenv(var_name)
            if url and url.strip():
                # 檢查是否為佔位符值
                placeholder_indicators = [
                    'your_database_url_here',
                    'user:password@localhost:5432',  # 更具體的佔位符模式
                ]

                if not any(indicator in url.lower() for indicator in placeholder_indicators):
                    logger.info(f"從環境變數 {var_name} 載入數據庫配置")
                    return url.strip()

        return None

    def _validate_url(self):
        """驗證數據庫URL的有效性"""
        if not self._parsed_url:
            raise DatabaseConfigError("數據庫URL未解析")

        # 檢查必要的組件
        if not self._parsed_url.scheme:
            raise DatabaseConfigError("數據庫URL缺少協議（如postgresql://）")

        if not self._parsed_url.hostname:
            raise DatabaseConfigError("數據庫URL缺少主機名")

        # 檢查是否使用了不安全的配置
        security_warnings = []

        if self._parsed_url.password == 'password':
            security_warnings.append("使用了不安全的密碼 'password'")

        if self._parsed_url.hostname == 'localhost' and self._environment == 'production':
            security_warnings.append("生產環境不應使用localhost")

        if security_warnings:
            for warning in security_warnings:
                logger.warning(f"數據庫配置安全警告: {warning}")

    def _provide_configuration_guidance(self):
        """提供配置指導"""
        guidance_messages = [
            "\n" + "="*60,
            "數據庫配置指導",
            "="*60,
            "",
            "請設置以下環境變數之一：",
            "  DATABASE_URL - 主要數據庫連接URL",
            "  DB_URL - 簡化的數據庫連接URL",
            f"  {self._environment.upper()}_DATABASE_URL - 環境特定的數據庫URL",
            "",
            "URL格式示例：",
            "  postgresql://username:password@hostname:5432/database_name",
            "  postgresql://user@localhost:5432/mydb",
            "",
            "當前環境：" + self._environment,
            "",
        ]

        # 根據環境提供特定建議
        if self._environment == 'development':
            guidance_messages.extend([
                "開發環境建議：",
                "  1. 創建 .env 文件",
                "  2. 設置: DATABASE_URL=postgresql://user:pass@localhost:5432/linker",
                "  3. 確保PostgreSQL服務正在運行",
                "",
            ])
        elif self._environment == 'test':
            guidance_messages.extend([
                "測試環境建議：",
                "  1. 設置: DATABASE_URL=postgresql://user:pass@localhost:5432/linker_test",
                "  2. 使用獨立的測試數據庫",
                "",
            ])
        elif self._environment == 'production':
            guidance_messages.extend([
                "生產環境建議：",
                "  1. 使用環境變數或secrets管理",
                "  2. 啟用SSL連接",
                "  3. 使用強密碼",
                "  4. 限制數據庫訪問權限",
                "",
            ])

        guidance_messages.append("="*60)

        for message in guidance_messages:
            print(message)

        logger.warning("數據庫URL未配置，請參考上述指導")

    # ========== 公共API方法 ==========

    def get_url(self, database_name: Optional[str] = None) -> str:
        """
        獲取數據庫URL

        Args:
            database_name: 可選的數據庫名稱覆蓋

        Returns:
            完整的數據庫連接URL

        Raises:
            DatabaseConfigError: 如果配置無效或未設置
        """
        if not self._base_url:
            raise DatabaseConfigError(
                "數據庫URL未配置。請設置 DATABASE_URL 環境變數。\n"
                "示例: DATABASE_URL=postgresql://user:pass@host:5432/dbname"
            )

        if not database_name:
            return self._base_url

        # 替換數據庫名稱
        if self._parsed_url:
            new_url = self._parsed_url._replace(path=f"/{database_name}")
            return urlunparse(new_url)

        return self._base_url

    def get_test_url(self, test_db_suffix: str = "_test") -> str:
        """
        獲取測試數據庫URL

        Args:
            test_db_suffix: 測試數據庫的後綴

        Returns:
            測試數據庫連接URL
        """
        if not self._parsed_url:
            raise DatabaseConfigError("無法生成測試數據庫URL：基礎配置無效")

        # 獲取原數據庫名稱
        original_db = self._parsed_url.path.lstrip('/')
        test_db = f"{original_db}{test_db_suffix}"

        return self.get_url(test_db)

    def get_connection_params(self) -> dict[str, Any]:
        """
        獲取連接參數字典（用於直接數據庫連接）

        Returns:
            包含連接參數的字典
        """
        if not self._parsed_url:
            raise DatabaseConfigError("無法獲取連接參數：URL未解析")

        params = {
            'host': self._parsed_url.hostname,
            'port': self._parsed_url.port or 5432,
            'database': self._parsed_url.path.lstrip('/'),
        }

        if self._parsed_url.username:
            params['user'] = self._parsed_url.username

        if self._parsed_url.password:
            params['password'] = self._parsed_url.password

        # 解析查詢參數
        if self._parsed_url.query:
            import urllib.parse
            query_params = urllib.parse.parse_qs(self._parsed_url.query)
            for key, values in query_params.items():
                if values:  # 取第一個值
                    params[key] = values[0]

        return params

    def is_configured(self) -> bool:
        """檢查是否已配置數據庫連接"""
        return self._base_url is not None

    def get_environment(self) -> str:
        """獲取當前環境"""
        return self._environment

    def get_database_info(self) -> dict[str, str]:
        """
        獲取數據庫信息（不包含敏感數據）

        Returns:
            包含數據庫基本信息的字典
        """
        if not self._parsed_url:
            return {'status': 'not_configured'}

        return {
            'status': 'configured',
            'scheme': self._parsed_url.scheme,
            'hostname': self._parsed_url.hostname,
            'port': str(self._parsed_url.port or 5432),
            'database': self._parsed_url.path.lstrip('/'),
            'environment': self._environment,
            'has_credentials': bool(self._parsed_url.username and self._parsed_url.password)
        }

    # ========== 工具方法 ==========

    def validate_connection(self) -> bool:
        """
        驗證數據庫連接（可選功能，需要額外的依賴）

        Returns:
            True如果連接成功，False如果失敗
        """
        try:
            # 這裡可以添加實際的連接測試邏輯
            # 目前只進行URL驗證
            if not self.is_configured():
                return False

            self._validate_url()
            return True

        except Exception as e:
            logger.error(f"數據庫連接驗證失敗: {e}")
            return False

    def create_test_config(self) -> 'DatabaseConfig':
        """
        創建測試專用的配置實例

        Returns:
            新的測試配置實例
        """
        test_config = DatabaseConfig.__new__(DatabaseConfig)
        test_config._environment = 'test'

        # 嘗試生成測試URL
        if self.is_configured():
            test_config._base_url = self.get_test_url()
            test_config._parsed_url = urlparse(test_config._base_url)
        else:
            test_config._base_url = None
            test_config._parsed_url = None

        return test_config


# ========== 全局實例和便捷函數 ==========

# 全局數據庫配置實例
_db_config_instance = None

def get_database_config() -> DatabaseConfig:
    """
    獲取全局數據庫配置實例（單例模式）

    Returns:
        DatabaseConfig實例
    """
    global _db_config_instance
    if _db_config_instance is None:
        _db_config_instance = DatabaseConfig()
    return _db_config_instance

def get_database_url(database_name: Optional[str] = None) -> str:
    """
    便捷函數：獲取數據庫URL

    Args:
        database_name: 可選的數據庫名稱

    Returns:
        數據庫連接URL
    """
    return get_database_config().get_url(database_name)

def get_test_database_url() -> str:
    """
    便捷函數：獲取測試數據庫URL

    Returns:
        測試數據庫連接URL
    """
    return get_database_config().get_test_url()

def is_database_configured() -> bool:
    """
    便捷函數：檢查數據庫是否已配置

    Returns:
        True如果已配置，False如果未配置
    """
    return get_database_config().is_configured()


# ========== 環境配置檢查 ==========

def check_database_configuration():
    """
    檢查並報告數據庫配置狀態
    這個函數會在模組載入時自動運行
    """
    try:
        config = get_database_config()
        info = config.get_database_info()

        if info['status'] == 'configured':
            logger.info(f"數據庫配置已載入 ({info['environment']}): {info['hostname']}:{info['port']}/{info['database']}")
        else:
            logger.warning("數據庫配置未設置，請檢查環境變數")

    except Exception as e:
        logger.error(f"數據庫配置檢查失敗: {e}")


# 模組載入時自動檢查配置（僅在非測試環境）
if not os.environ.get('SKIP_DB_CONFIG_CHECK'):
    check_database_configuration()
