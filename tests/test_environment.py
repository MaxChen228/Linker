"""
測試環境驗證
確保測試環境正確設置並可以運行
"""

import sys

import pytest


class TestEnvironment:
    """測試環境驗證"""

    def test_python_version(self):
        """驗證 Python 版本"""
        assert sys.version_info >= (3, 9), "需要 Python 3.9 或更高版本"

    def test_project_structure(self, project_root_path):
        """驗證專案結構"""
        # 檢查核心目錄存在
        assert (project_root_path / "core").exists(), "core 目錄應該存在"
        assert (project_root_path / "web").exists(), "web 目錄應該存在"
        assert (project_root_path / "tests").exists(), "tests 目錄應該存在"

        # 檢查關鍵檔案存在
        assert (project_root_path / "pyproject.toml").exists(), "pyproject.toml 應該存在"
        assert (project_root_path / "requirements.txt").exists(), "requirements.txt 應該存在"

    def test_core_module_import(self):
        """測試核心模組可以正常導入"""
        try:
            from core import exceptions, logger

            assert True, "核心模組導入成功"
        except ImportError as e:
            pytest.fail(f"無法導入核心模組: {e}")

    def test_settings_import(self):
        """測試 settings 模組可以正常導入"""
        try:
            from settings import Settings, settings

            assert isinstance(settings.display.MAX_DISPLAY_ITEMS, int)
            assert True, "settings 模組導入成功"
        except ImportError as e:
            pytest.fail(f"無法導入 settings 模組: {e}")

    def test_temp_directory_fixture(self, temp_dir):
        """測試臨時目錄夾具"""
        assert temp_dir.exists(), "臨時目錄應該存在"
        assert temp_dir.is_dir(), "應該是一個目錄"

        # 測試可以在臨時目錄中創建檔案
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists(), "應該能在臨時目錄中創建檔案"

    def test_mock_env_vars(self, mock_env_vars):
        """測試環境變數 mock"""
        import os

        assert os.getenv("GEMINI_API_KEY") == "test-api-key"
        assert "GEMINI_GENERATE_MODEL" in mock_env_vars

    @pytest.mark.unit
    def test_unit_marker(self):
        """測試 unit 標記"""
        # 這個測試應該自動獲得 unit 標記
        assert True

    @pytest.mark.slow
    def test_slow_marker(self):
        """測試 slow 標記"""
        # 這是一個標記為 slow 的測試
        assert True


class TestPytestConfiguration:
    """測試 pytest 配置"""

    def test_pytest_markers_available(self, pytestconfig):
        """測試 pytest 標記是否正確註冊"""
        markers = pytestconfig.getini("markers")
        expected_markers = {"slow", "integration", "unit", "ai", "mock"}

        # 檢查我們定義的標記是否存在
        for marker in expected_markers:
            assert any(marker in m for m in markers), f"標記 '{marker}' 應該被註冊"

    def test_coverage_configuration(self, pytestconfig):
        """測試覆蓋率配置"""
        addopts = pytestconfig.getini("addopts")
        assert any("--cov=core" in opt for opt in addopts), "應該配置 core 模組的覆蓋率"
        assert any("--cov=web" in opt for opt in addopts), "應該配置 web 模組的覆蓋率"
