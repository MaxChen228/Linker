"""
測試清理工具
提供測試環境清理和資源管理功能
"""

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any, Generator
import json

import pytest


class TestEnvironmentCleaner:
    """測試環境清理器"""
    
    def __init__(self):
        self.temp_files: List[Path] = []
        self.temp_dirs: List[Path] = []
        self.created_files: List[Path] = []
        self.modified_files: Dict[Path, str] = {}  # 文件路徑 -> 原始內容
        self.cleanup_callbacks: List[callable] = []
    
    def register_temp_file(self, file_path: Path):
        """註冊臨時文件，測試結束時自動刪除"""
        self.temp_files.append(file_path)
    
    def register_temp_dir(self, dir_path: Path):
        """註冊臨時目錄，測試結束時自動刪除"""
        self.temp_dirs.append(dir_path)
    
    def register_created_file(self, file_path: Path):
        """註冊創建的文件，測試結束時刪除"""
        self.created_files.append(file_path)
    
    def backup_file(self, file_path: Path):
        """備份文件，測試結束時恢復"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                self.modified_files[file_path] = f.read()
    
    def register_cleanup_callback(self, callback: callable):
        """註冊清理回調函數"""
        self.cleanup_callbacks.append(callback)
    
    def cleanup(self):
        """執行所有清理操作"""
        # 執行自定義清理回調
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Warning: Cleanup callback failed: {e}")
        
        # 刪除臨時文件
        for file_path in self.temp_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to remove temp file {file_path}: {e}")
        
        # 刪除創建的文件
        for file_path in self.created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                print(f"Warning: Failed to remove created file {file_path}: {e}")
        
        # 刪除臨時目錄
        for dir_path in self.temp_dirs:
            try:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
            except Exception as e:
                print(f"Warning: Failed to remove temp dir {dir_path}: {e}")
        
        # 恢復修改的文件
        for file_path, original_content in self.modified_files.items():
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
            except Exception as e:
                print(f"Warning: Failed to restore file {file_path}: {e}")
        
        # 清空記錄
        self.temp_files.clear()
        self.temp_dirs.clear()
        self.created_files.clear()
        self.modified_files.clear()
        self.cleanup_callbacks.clear()


@contextmanager
def test_environment() -> Generator[TestEnvironmentCleaner, None, None]:
    """測試環境上下文管理器"""
    cleaner = TestEnvironmentCleaner()
    try:
        yield cleaner
    finally:
        cleaner.cleanup()


@contextmanager
def temporary_directory() -> Generator[Path, None, None]:
    """臨時目錄上下文管理器"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@contextmanager
def temporary_file(content: str = "", suffix: str = ".tmp") -> Generator[Path, None, None]:
    """臨時文件上下文管理器"""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        temp_file = Path(f.name)
    
    try:
        yield temp_file
    finally:
        if temp_file.exists():
            temp_file.unlink()


@contextmanager
def backup_and_restore_file(file_path: Path) -> Generator[Path, None, None]:
    """備份並在結束時恢復文件"""
    backup_content = None
    
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
    
    try:
        yield file_path
    finally:
        if backup_content is not None:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
        elif file_path.exists():
            # 如果原本不存在，刪除創建的文件
            file_path.unlink()


class DatabaseCleaner:
    """數據庫清理器（針對文件數據庫）"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.backup_dir = None
        self.original_files = {}
    
    def backup_data(self):
        """備份現有數據"""
        if not self.data_dir.exists():
            return
        
        self.backup_dir = Path(tempfile.mkdtemp(suffix="_test_backup"))
        
        for file_path in self.data_dir.glob("*.json"):
            backup_file = self.backup_dir / file_path.name
            shutil.copy2(file_path, backup_file)
            
            # 記錄原始內容
            with open(file_path, 'r', encoding='utf-8') as f:
                self.original_files[file_path] = f.read()
    
    def restore_data(self):
        """恢復原始數據"""
        if not self.backup_dir:
            return
        
        # 恢復文件
        for original_file, content in self.original_files.items():
            try:
                with open(original_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                print(f"Warning: Failed to restore {original_file}: {e}")
        
        # 清理備份目錄
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
    
    def clear_data(self):
        """清空所有數據文件"""
        if not self.data_dir.exists():
            return
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                # 寫入空的有效 JSON 結構
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
            except Exception as e:
                print(f"Warning: Failed to clear {file_path}: {e}")
    
    def __enter__(self):
        self.backup_data()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore_data()


@contextmanager
def isolated_data_environment(data_dir: Path) -> Generator[Path, None, None]:
    """隔離的數據環境"""
    with DatabaseCleaner(data_dir) as cleaner:
        cleaner.clear_data()  # 開始時清空數據
        yield data_dir


def cleanup_test_artifacts(test_name: str = None):
    """清理測試產生的文件"""
    # 定義常見的測試文件模式
    patterns = [
        "test_*.json",
        "*.test",
        "temp_*",
        "*_backup_*",
        "test_data_*"
    ]
    
    current_dir = Path.cwd()
    
    for pattern in patterns:
        for file_path in current_dir.glob(pattern):
            try:
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Warning: Failed to cleanup {file_path}: {e}")


class ResourceTracker:
    """資源使用追蹤器"""
    
    def __init__(self):
        self.file_handles = []
        self.open_files = set()
        self.memory_usage = []
    
    def track_file_handle(self, file_handle):
        """追蹤文件句柄"""
        self.file_handles.append(file_handle)
    
    def track_open_file(self, file_path: Path):
        """追蹤打開的文件"""
        self.open_files.add(file_path)
    
    def close_file(self, file_path: Path):
        """標記文件已關閉"""
        self.open_files.discard(file_path)
    
    def check_resource_leaks(self):
        """檢查資源洩漏"""
        issues = []
        
        if self.open_files:
            issues.append(f"Unclosed files: {self.open_files}")
        
        for handle in self.file_handles:
            if not handle.closed:
                issues.append(f"Unclosed file handle: {handle}")
        
        if issues:
            pytest.fail(f"Resource leaks detected: {'; '.join(issues)}")
    
    def cleanup(self):
        """清理所有追蹤的資源"""
        # 關閉文件句柄
        for handle in self.file_handles:
            try:
                if not handle.closed:
                    handle.close()
            except Exception:
                pass
        
        self.file_handles.clear()
        self.open_files.clear()


@pytest.fixture
def test_cleaner():
    """測試清理器 fixture"""
    cleaner = TestEnvironmentCleaner()
    yield cleaner
    cleaner.cleanup()


@pytest.fixture
def resource_tracker():
    """資源追蹤器 fixture"""
    tracker = ResourceTracker()
    yield tracker
    tracker.check_resource_leaks()
    tracker.cleanup()