"""
統一測試配置管理
TASK-34: 消除硬編碼 - 統一所有測試的數據庫配置

此模組提供統一的測試配置，消除測試文件中的硬編碼數據庫連接，
確保測試環境的一致性和安全性。
"""

import os
import pytest
from typing import Optional
from pathlib import Path

# TASK-34: 使用統一數據庫配置管理系統
try:
    from core.settings.database import DatabaseConfig
    _database_config_available = True
except ImportError:
    _database_config_available = False


class TestDatabaseConfig:
    """
    測試數據庫配置管理類
    
    提供統一的測試數據庫配置，避免在每個測試文件中重複配置
    """
    
    def __init__(self):
        self._test_db_url = self._get_test_database_url()
        self._original_env = {}
    
    def _get_test_database_url(self) -> str:
        """獲取測試數據庫URL"""
        # 優先使用專門的測試環境變數
        test_url = os.getenv('TEST_DATABASE_URL')
        if test_url:
            return test_url
        
        # 嘗試使用統一配置系統生成測試URL
        if _database_config_available:
            try:
                # 為測試創建特殊的配置實例
                db_config = DatabaseConfig()
                if db_config.is_configured():
                    return db_config.get_test_url()
            except Exception:
                pass
        
        # 最後回退：基於現有DATABASE_URL生成測試URL
        base_url = os.getenv('DATABASE_URL')
        if base_url:
            # 簡單替換：將數據庫名稱添加_test後綴
            if '/linker' in base_url:
                return base_url.replace('/linker', '/linker_test')
            elif base_url.endswith('/'):
                return base_url + 'linker_test'
            else:
                return base_url + '_test'
        
        # 默認測試配置（僅用於開發環境）
        # 使用環境變數或從core.config獲取
        from core.settings.database import DatabaseConfig
        db_config = DatabaseConfig()
        if db_config.is_configured():
            return db_config.get_test_url()
        # 如果未配置，使用默認值
        return os.getenv('TEST_DATABASE_URL', f'postgresql://test:test@{os.getenv("DB_HOST", "localhost")}:{os.getenv("DB_PORT", "5432")}/linker_test')
    
    def get_test_url(self) -> str:
        """獲取測試數據庫URL"""
        return self._test_db_url
    
    def setup_test_environment(self):
        """設置測試環境變數"""
        # 保存原始環境變數
        self._original_env = {
            'DATABASE_URL': os.environ.get('DATABASE_URL'),
            'USE_DATABASE': os.environ.get('USE_DATABASE'),
            'ENVIRONMENT': os.environ.get('ENVIRONMENT'),
        }
        
        # 設置測試環境變數
        os.environ['DATABASE_URL'] = self._test_db_url
        os.environ['USE_DATABASE'] = 'true'
        os.environ['ENVIRONMENT'] = 'test'
        
        # 跳過數據庫配置檢查（避免在測試中輸出配置信息）
        os.environ['SKIP_DB_CONFIG_CHECK'] = 'true'
    
    def restore_environment(self):
        """恢復原始環境變數"""
        for key, value in self._original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        # 移除測試專用變數
        os.environ.pop('SKIP_DB_CONFIG_CHECK', None)


# 全局測試配置實例
_test_config = TestDatabaseConfig()


# ========== pytest fixtures ==========

@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    提供測試數據庫URL的session級別fixture
    
    這個fixture確保所有測試使用相同的數據庫配置
    """
    return _test_config.get_test_url()


@pytest.fixture(scope="session")
def test_database_config():
    """
    提供測試數據庫配置對象的fixture
    """
    return _test_config


@pytest.fixture(scope="function")
def isolated_test_env():
    """
    為單個測試提供隔離的環境配置
    
    使用此fixture的測試將在獨立的環境變數配置下運行
    """
    _test_config.setup_test_environment()
    yield _test_config
    _test_config.restore_environment()


@pytest.fixture(scope="class")
def class_test_env():
    """
    為測試類提供隔離的環境配置
    
    使用此fixture的測試類將在獨立的環境變數配置下運行
    """
    _test_config.setup_test_environment()
    yield _test_config
    _test_config.restore_environment()


# ========== 便捷函數 ==========

def get_test_database_url() -> str:
    """
    便捷函數：獲取測試數據庫URL
    
    可以在任何測試文件中直接使用，無需fixture
    """
    return _test_config.get_test_url()


def setup_test_database_env():
    """
    便捷函數：設置測試環境
    
    在測試模組級別使用，如在conftest.py中
    """
    _test_config.setup_test_environment()


def restore_test_database_env():
    """
    便捷函數：恢復原始環境
    """
    _test_config.restore_environment()


# ========== 測試專用配置常量 ==========

class TestConfig:
    """測試專用配置常量"""
    
    # 測試數據庫相關
    TEST_DATABASE_URL = _test_config.get_test_url()
    TEST_DATABASE_NAME = "linker_test"
    
    # 測試環境標識
    IS_TEST_ENV = True
    
    # 測試專用設定
    SKIP_EXTERNAL_CALLS = True  # 跳過外部API調用
    USE_MOCK_DATA = True        # 使用模擬數據
    ENABLE_DEBUG_LOGS = False   # 禁用調試日誌（減少測試輸出）
    
    @classmethod
    def get_connection_params(cls) -> dict:
        """獲取測試數據庫連接參數"""
        if _database_config_available:
            try:
                db_config = DatabaseConfig()
                test_config = db_config.create_test_config()
                return test_config.get_connection_params()
            except Exception:
                pass
        
        # 默認測試連接參數
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': cls.TEST_DATABASE_NAME,
            'user': 'test',
            'password': 'test'
        }


# ========== 自動環境檢測 ==========

def is_running_tests() -> bool:
    """
    檢測是否在運行測試
    
    Returns:
        True如果當前在測試環境中
    """
    # 檢測pytest
    if 'pytest' in os.environ.get('_', ''):
        return True
    
    # 檢測unittest
    if 'unittest' in os.environ.get('_', ''):
        return True
    
    # 檢測測試相關的環境變數
    test_indicators = ['CI', 'TEST', 'PYTEST_CURRENT_TEST']
    for indicator in test_indicators:
        if os.environ.get(indicator):
            return True
    
    return False


# 如果檢測到測試環境，自動設置測試配置
if is_running_tests():
    setup_test_database_env()


# ========== 使用示例 ==========

"""
使用示例：

# 在單個測試文件中
def test_something(test_database_url):
    # test_database_url 自動提供統一的測試數據庫URL
    assert test_database_url.endswith('linker_test')

# 在測試類中
class TestDatabaseOperations:
    def test_insert(self, class_test_env):
        # 整個測試類都使用隔離的測試環境
        pass

# 直接使用便捷函數
def test_direct_usage():
    from tests.config import get_test_database_url
    url = get_test_database_url()
    # 使用統一的測試數據庫URL

# 在conftest.py中設置全局測試環境
import pytest
from tests.config import setup_test_database_env, restore_test_database_env

def pytest_sessionstart(session):
    setup_test_database_env()

def pytest_sessionfinish(session, exitstatus):
    restore_test_database_env()
"""