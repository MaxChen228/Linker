"""
測試 settings 模組
"""

import tempfile
from pathlib import Path

from settings import Settings, settings


class TestSettings:
    """測試配置管理"""

    def test_default_settings(self):
        """測試默認配置值"""
        s = Settings()

        # 測試顯示設定
        assert s.display.MAX_DISPLAY_ITEMS == 10
        assert s.display.MAX_EXAMPLES_PER_POINT == 5
        assert s.display.SEPARATOR_WIDTH == 50

        # 測試學習設定
        assert s.learning.MASTERY_INCREMENTS["systematic"] == 0.25
        assert s.learning.REVIEW_INTERVALS["immediate"] == 1
        assert s.learning.MASTERY_THRESHOLDS["beginner"] == 0.3

        # 測試緩存設定
        assert s.cache.CACHE_TTL_SECONDS == 300
        assert s.cache.MAX_CACHE_SIZE == 100

        # 測試API設定
        assert s.api.DEFAULT_MODEL == "gemini-2.0-flash-exp"
        assert s.api.REQUEST_TIMEOUT == 30

    def test_settings_singleton(self):
        """測試全局設定實例"""
        assert settings.display.MAX_DISPLAY_ITEMS == 10
        assert isinstance(settings.learning.DIFFICULTY_LEVELS, dict)
        assert 1 in settings.learning.DIFFICULTY_LEVELS

    def test_save_and_load(self):
        """測試保存和載入配置"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            config_file = f.name

        try:
            # 創建設定並修改值
            s = Settings()
            s.display.MAX_DISPLAY_ITEMS = 20
            s.cache.CACHE_TTL_SECONDS = 600

            # 保存設定
            s.save_to_file(config_file)

            # 驗證文件存在
            assert Path(config_file).exists()

            # 載入設定
            loaded = Settings.load_from_file(config_file)

            # 驗證載入的值
            assert loaded.display.MAX_DISPLAY_ITEMS == 20
            assert loaded.cache.CACHE_TTL_SECONDS == 600

            # 驗證未修改的值保持默認
            assert loaded.api.DEFAULT_MODEL == "gemini-2.0-flash-exp"

        finally:
            # 清理測試文件
            Path(config_file).unlink(missing_ok=True)

    def test_load_invalid_file(self):
        """測試載入無效配置文件"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            # 寫入無效JSON
            f.write(b"invalid json{")
            config_file = f.name

        try:
            # 應該使用默認值
            loaded = Settings.load_from_file(config_file)
            assert loaded.display.MAX_DISPLAY_ITEMS == 10
        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_error_priority_settings(self):
        """測試錯誤優先級配置"""
        s = Settings()

        assert s.error_priority.PRIORITIES["systematic"] == 1
        assert s.error_priority.PRIORITIES["isolated"] == 2
        assert s.error_priority.PRIORITIES["other"] == 3
        assert s.error_priority.PRIORITIES["enhancement"] == 4

    def test_practice_settings(self):
        """測試練習配置"""
        s = Settings()

        assert s.practice.MIN_SENTENCE_LENGTH == 10
        assert s.practice.MAX_SENTENCE_LENGTH == 30
        assert s.practice.RECENT_MISTAKES_COUNT == 10
        assert 1 in s.practice.DIFFICULTY_DESCRIPTIONS

    def test_ui_settings(self):
        """測試UI配置"""
        s = Settings()

        assert s.ui.CATEGORY_EMOJIS["systematic"] == "⚙️"
        assert s.ui.PRIORITY_EMOJIS[1] == "🔥"
        assert s.ui.MASTERY_BAR_LENGTH == 10
        assert s.ui.MASTERY_BAR_FILLED == "█"
