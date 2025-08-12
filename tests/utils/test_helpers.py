"""
測試輔助函數
提供各種測試過程中常用的工具函數和便利方法
"""

import asyncio
import json
import tempfile
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Generator
from unittest.mock import patch, Mock

import pytest
from freezegun import freeze_time

from core.knowledge import KnowledgePoint
from core.response import APIResponse


def create_temp_file(content: str = "", suffix: str = ".json") -> Path:
    """創建臨時文件並返回路徑"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=suffix) as f:
        f.write(content)
        return Path(f.name)


def create_temp_dir() -> Path:
    """創建臨時目錄並返回路徑"""
    temp_dir = tempfile.mkdtemp()
    return Path(temp_dir)


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """安全載入 JSON 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load JSON file {file_path}: {e}")


def save_json_file(file_path: Union[str, Path], data: Any):
    """保存數據到 JSON 文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pytest.fail(f"Failed to save JSON file {file_path}: {e}")


def compare_knowledge_points(kp1: KnowledgePoint, kp2: KnowledgePoint, 
                           ignore_fields: Optional[List[str]] = None) -> bool:
    """比較兩個知識點是否相等，可忽略指定欄位"""
    ignore_fields = ignore_fields or ["updated_at", "created_at"]
    
    kp1_dict = kp1.__dict__.copy()
    kp2_dict = kp2.__dict__.copy()
    
    for field in ignore_fields:
        kp1_dict.pop(field, None)
        kp2_dict.pop(field, None)
    
    return kp1_dict == kp2_dict


def assert_response_success(response: APIResponse, expected_message: str = None):
    """斷言回應是成功的"""
    assert response.success, f"Expected successful response, but got error: {response.message}"
    
    if expected_message:
        assert expected_message in (response.message or ""), (
            f"Expected message to contain '{expected_message}', "
            f"but got: '{response.message}'"
        )


def assert_response_error(response: APIResponse, expected_message: str = None):
    """斷言回應是錯誤的"""
    assert not response.success, f"Expected error response, but got success: {response.message}"
    
    if expected_message:
        assert expected_message in (response.message or ""), (
            f"Expected error message to contain '{expected_message}', "
            f"but got: '{response.message}'"
        )


def wait_for_condition(condition_func: Callable[[], bool], 
                      timeout: float = 5.0, 
                      interval: float = 0.1) -> bool:
    """等待條件成立，用於異步測試"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    
    return False


@asynccontextmanager
async def async_timeout(seconds: float):
    """異步超時上下文管理器"""
    try:
        await asyncio.wait_for(asyncio.sleep(0), timeout=seconds)
        yield
    except asyncio.TimeoutError:
        pytest.fail(f"Operation timed out after {seconds} seconds")


@contextmanager
def patch_datetime_now(fake_now: datetime):
    """Mock datetime.now() 到指定時間"""
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = fake_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_datetime


@contextmanager
def suppress_logging():
    """暫時抑制日志輸出"""
    import logging
    
    # 保存原始日志等級
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    original_levels = {logger: logger.level for logger in loggers}
    
    # 設置為 CRITICAL 等級
    for logger in loggers:
        logger.setLevel(logging.CRITICAL)
    
    try:
        yield
    finally:
        # 恢復原始等級
        for logger, level in original_levels.items():
            logger.setLevel(level)


def create_test_environment_vars() -> Dict[str, str]:
    """創建測試環境變數"""
    return {
        "GEMINI_API_KEY": "test_api_key_12345",
        "GEMINI_GENERATE_MODEL": "gemini-2.5-flash",
        "GEMINI_GRADE_MODEL": "gemini-2.5-pro",
    }


@contextmanager
def mock_environment_variables(env_vars: Dict[str, str]):
    """Mock 環境變數"""
    with patch.dict('os.environ', env_vars):
        yield


def generate_test_data_file(data_type: str, count: int = 10) -> Path:
    """生成測試數據文件"""
    if data_type == "knowledge_points":
        from tests.factories.knowledge_factory import KnowledgePointFactory
        data = [kp.__dict__ for kp in KnowledgePointFactory.build_batch(count)]
        
    elif data_type == "practice_records":
        from tests.factories.practice_factory import PracticeRecordFactory
        data = PracticeRecordFactory.build_batch(count)
        
    else:
        raise ValueError(f"Unknown data type: {data_type}")
    
    # 創建臨時文件
    temp_file = create_temp_file()
    save_json_file(temp_file, {"version": "3.0", data_type: data})
    
    return temp_file


def simulate_network_delay(min_delay: float = 0.1, max_delay: float = 0.5):
    """模擬網絡延遲"""
    import random
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


async def simulate_async_network_delay(min_delay: float = 0.1, max_delay: float = 0.5):
    """異步模擬網絡延遲"""
    import random
    delay = random.uniform(min_delay, max_delay)
    await asyncio.sleep(delay)


def capture_function_calls(func: Callable, call_history: List[Dict[str, Any]]):
    """捕獲函數調用記錄"""
    def wrapper(*args, **kwargs):
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "args": args,
            "kwargs": kwargs
        }
        call_history.append(call_record)
        return func(*args, **kwargs)
    
    return wrapper


def create_fixture_file(fixture_name: str, data: Any) -> Path:
    """創建測試 fixture 文件"""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    
    fixture_file = fixtures_dir / f"{fixture_name}.json"
    save_json_file(fixture_file, data)
    
    return fixture_file


def load_fixture_file(fixture_name: str) -> Any:
    """載入測試 fixture 文件"""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    fixture_file = fixtures_dir / f"{fixture_name}.json"
    
    if not fixture_file.exists():
        pytest.fail(f"Fixture file not found: {fixture_file}")
    
    return load_json_file(fixture_file)


class TestTimer:
    """測試計時器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """開始計時"""
        self.start_time = time.time()
    
    def stop(self):
        """結束計時"""
        self.end_time = time.time()
    
    @property
    def elapsed(self) -> float:
        """獲取經過時間"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time or time.time()
        return end - self.start_time
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def assert_timing(min_time: float = 0.0, max_time: float = float('inf')):
    """斷言執行時間在指定範圍內"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with TestTimer() as timer:
                result = func(*args, **kwargs)
            
            elapsed = timer.elapsed
            assert min_time <= elapsed <= max_time, (
                f"Function {func.__name__} took {elapsed:.3f}s, "
                f"expected between {min_time:.3f}s and {max_time:.3f}s"
            )
            
            return result
        return wrapper
    return decorator


def random_string(length: int = 10, chars: str = None) -> str:
    """生成隨機字符串"""
    import random
    import string
    
    if chars is None:
        chars = string.ascii_letters + string.digits
    
    return ''.join(random.choice(chars) for _ in range(length))


def random_choice_exclude(choices: List[Any], exclude: List[Any]) -> Any:
    """從選擇中隨機選取，但排除指定項目"""
    import random
    
    valid_choices = [choice for choice in choices if choice not in exclude]
    
    if not valid_choices:
        raise ValueError("No valid choices remaining after exclusion")
    
    return random.choice(valid_choices)


def deep_merge_dict(base_dict: Dict, update_dict: Dict) -> Dict:
    """深度合併字典"""
    result = base_dict.copy()
    
    for key, value in update_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


@contextmanager
def change_working_directory(new_dir: Union[str, Path]):
    """臨時改變工作目錄"""
    import os
    
    old_dir = os.getcwd()
    try:
        os.chdir(str(new_dir))
        yield Path(new_dir)
    finally:
        os.chdir(old_dir)


def ensure_test_data_dir() -> Path:
    """確保測試數據目錄存在"""
    test_data_dir = Path(__file__).parent.parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    return test_data_dir