"""
pytest 配置檔案 - 提供測試中的共用設置和夾具
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# 確保可以導入專案模組
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """返回專案根目錄路徑"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """為每個測試提供臨時目錄"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def temp_data_dir(temp_dir: Path) -> Path:
    """為測試創建臨時 data 目錄"""
    data_dir = temp_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture(scope="function")
def mock_env_vars():
    """模擬環境變數的夾具"""
    original_env = os.environ.copy()
    
    # 設置測試用的環境變數
    test_env = {
        "GEMINI_API_KEY": "test-api-key",
        "GEMINI_GENERATE_MODEL": "gemini-2.5-flash",
        "GEMINI_GRADE_MODEL": "gemini-2.5-pro",
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # 恢復原始環境變數
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def prevent_external_api_calls(monkeypatch):
    """防止意外的外部 API 調用（手動使用）"""
    def mock_api_call(*args, **kwargs):
        raise RuntimeError("測試中不允許真實的 API 調用！請使用 mock。")
    
    # 可以根據需要添加更多的 API 調用點
    try:
        import google.generativeai as genai
        # 檢查正確的 API 方法
        if hasattr(genai, "generate"):
            monkeypatch.setattr(genai, "generate", mock_api_call)
    except ImportError:
        pass
    
    return mock_api_call


# 測試標記配置
pytest_plugins = []

def pytest_configure(config):
    """pytest 配置鉤子"""
    # 註冊自定義標記
    config.addinivalue_line(
        "markers", "slow: 標記為慢速測試，需要更長的執行時間"
    )
    config.addinivalue_line(
        "markers", "integration: 整合測試，測試多個組件的交互"
    )
    config.addinivalue_line(
        "markers", "unit: 單元測試，測試單一組件的功能"
    )
    config.addinivalue_line(
        "markers", "ai: 涉及 AI 服務的測試，可能需要 API 密鑰"
    )


def pytest_collection_modifyitems(config, items):
    """修改測試收集結果"""
    # 為沒有明確標記的測試添加 unit 標記
    for item in items:
        if not any(mark.name in ["slow", "integration", "ai"] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)