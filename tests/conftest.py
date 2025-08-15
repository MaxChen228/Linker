"""
pytest 配置檔案 - 提供測試中的共用設置和夾具
"""

import os
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

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
    config.addinivalue_line("markers", "slow: 標記為慢速測試，需要更長的執行時間")
    config.addinivalue_line("markers", "integration: 整合測試，測試多個組件的交互")
    config.addinivalue_line("markers", "unit: 單元測試，測試單一組件的功能")
    config.addinivalue_line("markers", "ai: 涉及 AI 服務的測試，可能需要 API 密鑰")
    config.addinivalue_line("markers", "stress: 壓力測試，測試系統在高負載下的表現")
    config.addinivalue_line("markers", "memory_intensive: 記憶體密集型測試")
    config.addinivalue_line("markers", "asyncio: 非同步測試")
    config.addinivalue_line("markers", "e2e: 端對端測試")


def pytest_collection_modifyitems(config, items):
    """修改測試收集結果"""
    # 為沒有明確標記的測試添加 unit 標記
    for item in items:
        if not any(mark.name in ["slow", "integration", "ai"] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# 資料庫測試相關夾具


@pytest.fixture
async def mock_pool():
    """模擬 asyncpg.Pool 物件"""
    from unittest.mock import AsyncMock, MagicMock

    pool = AsyncMock()
    pool._closed = False
    pool._minsize = 5
    pool._maxsize = 20

    # 模擬連線池方法
    pool.get_size.return_value = 10
    pool.get_idle_size.return_value = 5
    pool.close = AsyncMock()
    pool.terminate = AsyncMock()

    # 模擬連線獲取
    mock_conn = AsyncMock()

    # 配置 fetchval 支持不同的回傳值
    def mock_fetchval_side_effect(*args, **kwargs):
        if args and (
            "UPDATE knowledge_points" in str(args[0]) and "RETURNING last_modified" in str(args[0])
        ):
            # UPDATE 查詢返回 last_modified，確保更新成功
            mock_state["mastery_level"] = 0.50 if len(args) > 8 else mock_state["mastery_level"]
            return datetime.now()
        elif (
            args
            and "UPDATE knowledge_points" in str(args[0])
            and "is_deleted = TRUE" in str(args[0])
        ):
            # 軟刪除操作返回 ID 表示成功
            mock_state["is_deleted"] = True
            return 1
        elif args and "NOW()" in str(args[0]):
            # 其他 NOW() 查詢
            return datetime.now()
        return 1  # 預設返回值

    mock_conn.fetchval = AsyncMock(side_effect=mock_fetchval_side_effect)
    mock_conn.execute = AsyncMock()

    # 模擬知識點數據結構 - 簡化版本
    from datetime import datetime

    mock_knowledge_point_row = {
        "id": 1,
        "key_point": "Inversion with 'not only'",  # 與測試期待一致
        "category": "systematic",
        "subtype": "inversion",
        "explanation": "When 'Not only' starts a sentence, the subject and verb must be inverted.",
        "original_phrase": "Not only this is his duty",
        "correction": "Not only is this his duty",
        "mastery_level": 0.25,  # 會根據操作動態調整
        "mistake_count": 0,
        "correct_count": 1,
        "created_at": datetime(2024, 1, 1),
        "last_seen": None,
        "next_review": None,
        "is_deleted": False,
        "deleted_at": None,
        "deleted_reason": None,
        "custom_notes": None,
        "last_modified": datetime(2024, 1, 1),
    }

    # 追蹤對象狀態
    mock_state = {
        "is_deleted": False,
        "mastery_level": 0.25,
        "updated": False,
        "custom_notes": "",
        "deleted_reason": "",
    }

    def mock_execute_side_effect(*args, **kwargs):
        if args and "UPDATE knowledge_points SET" in str(args[0]):
            print(f"Debug: Execute args: {args}")  # 添加調試
            if "is_deleted = TRUE" in str(args[0]):
                # 軟刪除操作: UPDATE knowledge_points SET is_deleted = TRUE, deleted_at = $2, deleted_reason = $3 WHERE id = $1
                mock_state["is_deleted"] = True
                if len(args) >= 4:  # reason 參數在第3個位置 (args[3])
                    mock_state["deleted_reason"] = args[3]
            else:
                # 一般更新操作，更新多個欄位
                mock_state["updated"] = True
                # UPDATE ... SET key_point=$2, category=$3, ..., mastery_level=$8, ..., custom_notes=$13 WHERE id=$1
                if len(args) > 8:  # mastery_level 在第8個位置
                    mock_state["mastery_level"] = args[8]
                if len(args) > 13:  # custom_notes 在第13個位置
                    mock_state["custom_notes"] = args[13]
        return None

    def mock_fetchrow_side_effect(*args, **kwargs):
        if (
            mock_state["is_deleted"]
            and "SELECT" in str(args[0])
            and "is_deleted = FALSE" in str(args[0])
        ):
            # 已删除的對象不應該被查到
            return None
        elif "SELECT * FROM knowledge_points WHERE id" in str(args[0]):
            # 直接查詢，返回真實狀態（包括刪除狀態）
            row = mock_knowledge_point_row.copy()
            row["mastery_level"] = mock_state["mastery_level"]
            row["is_deleted"] = mock_state["is_deleted"]
            row["custom_notes"] = mock_state["custom_notes"]
            row["deleted_reason"] = mock_state["deleted_reason"]
            return row
        # 動態返回数據
        row = mock_knowledge_point_row.copy()
        row["mastery_level"] = mock_state["mastery_level"]
        row["is_deleted"] = mock_state["is_deleted"]
        row["custom_notes"] = mock_state["custom_notes"]
        return row

    mock_conn.execute = AsyncMock(side_effect=mock_execute_side_effect)
    mock_conn.fetchrow = AsyncMock(side_effect=mock_fetchrow_side_effect)
    mock_conn.fetch = AsyncMock(return_value=[mock_knowledge_point_row])

    # 模擬事務支持
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=None)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    mock_conn.transaction = MagicMock(return_value=mock_transaction)

    # 正確設置異步上下文管理器
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    pool.acquire = MagicMock(return_value=mock_context_manager)

    return pool


@pytest.fixture
def mock_database_settings():
    """模擬資料庫設定"""
    from unittest.mock import MagicMock

    settings = MagicMock()
    settings.USE_DATABASE = False  # 預設不使用資料庫
    # 使用統一的測試配置
    from tests.config import TestConfig
    test_config = TestConfig()
    settings.DATABASE_URL = test_config.get_test_url()
    settings.DB_POOL_MIN_SIZE = 2
    settings.DB_POOL_MAX_SIZE = 5
    settings.DB_POOL_TIMEOUT = 5
    settings.DB_MAX_RETRIES = 2
    settings.DB_RETRY_DELAY = 0.1

    return settings


@pytest.fixture
async def mock_db_connection(mock_pool, mock_database_settings):
    """模擬 DatabaseConnection 實例"""
    from unittest.mock import patch

    from core.database.connection import DatabaseConnection

    # 重置 Singleton
    DatabaseConnection._instances.clear()

    with patch("core.database.connection.DatabaseSettings", return_value=mock_database_settings):
        db_conn = DatabaseConnection()
        db_conn._pool = mock_pool

        # 確保 connect 方法返回 mock_pool

        async def mock_connect():
            db_conn._pool = mock_pool
            return mock_pool

        db_conn.connect = mock_connect

        yield db_conn

        # 清理
        await db_conn.disconnect()
        DatabaseConnection._instances.clear()


@pytest.fixture
def db_connection(mock_pool):
    """為了向後兼容，提供 db_connection 夾具"""
    return mock_pool
