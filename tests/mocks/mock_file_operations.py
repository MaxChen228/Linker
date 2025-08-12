"""
文件操作 Mock 實現
模擬文件系統操作，避免測試時對真實文件的依賴
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from core.response import APIResponse


class MockFileSystem:
    """模擬文件系統，在內存中管理虛擬文件"""
    
    def __init__(self):
        self.files: Dict[str, str] = {}  # 文件路徑 -> 內容
        self.directories: set = set()    # 目錄集合
        self.file_operations = []        # 操作記錄
        
    def write_file(self, file_path: str, content: str):
        """寫入文件"""
        file_path = str(file_path)
        self.files[file_path] = content
        
        # 自動創建目錄
        dir_path = str(Path(file_path).parent)
        self.directories.add(dir_path)
        
        self.file_operations.append({
            "operation": "write",
            "path": file_path,
            "timestamp": datetime.now().isoformat(),
            "content_length": len(content)
        })
    
    def read_file(self, file_path: str) -> Optional[str]:
        """讀取文件"""
        file_path = str(file_path)
        content = self.files.get(file_path)
        
        self.file_operations.append({
            "operation": "read",
            "path": file_path,
            "timestamp": datetime.now().isoformat(),
            "success": content is not None
        })
        
        return content
    
    def delete_file(self, file_path: str) -> bool:
        """刪除文件"""
        file_path = str(file_path)
        existed = file_path in self.files
        
        if existed:
            del self.files[file_path]
        
        self.file_operations.append({
            "operation": "delete", 
            "path": file_path,
            "timestamp": datetime.now().isoformat(),
            "success": existed
        })
        
        return existed
    
    def exists(self, path: str) -> bool:
        """檢查文件或目錄是否存在"""
        path = str(path)
        return path in self.files or path in self.directories
    
    def list_files(self) -> List[str]:
        """列出所有文件"""
        return list(self.files.keys())
    
    def clear(self):
        """清空文件系統"""
        self.files.clear()
        self.directories.clear() 
        self.file_operations.clear()
    
    def get_operation_count(self, operation_type: str) -> int:
        """獲取特定操作的次數"""
        return sum(1 for op in self.file_operations if op["operation"] == operation_type)


class MockJSONFileHandler:
    """模擬 JSON 文件處理"""
    
    def __init__(self, file_system: MockFileSystem):
        self.fs = file_system
        
    def read_json(self, file_path: str, default: Any = None) -> Any:
        """讀取 JSON 文件"""
        content = self.fs.read_file(file_path)
        
        if content is None:
            if default is not None:
                return default
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
    
    def write_json(self, file_path: str, data: Any, indent: int = 2):
        """寫入 JSON 文件"""
        try:
            content = json.dumps(data, ensure_ascii=False, indent=indent)
            self.fs.write_file(file_path, content)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot serialize data to JSON: {e}")
    
    def update_json(self, file_path: str, updates: Dict[str, Any]):
        """更新 JSON 文件的部分數據"""
        try:
            data = self.read_json(file_path, {})
            data.update(updates)
            self.write_json(file_path, data)
        except Exception as e:
            raise RuntimeError(f"Failed to update JSON file {file_path}: {e}")


class MockBackupManager:
    """模擬備份管理"""
    
    def __init__(self, file_system: MockFileSystem):
        self.fs = file_system
        self.backups: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_backup(self, source_file: str, backup_dir: str = "backups") -> str:
        """創建文件備份"""
        content = self.fs.read_file(source_file)
        if content is None:
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = Path(source_file).stem
        backup_file = f"{backup_dir}/{file_name}_backup_{timestamp}.json"
        
        self.fs.write_file(backup_file, content)
        
        # 記錄備份信息
        if source_file not in self.backups:
            self.backups[source_file] = []
        
        self.backups[source_file].append({
            "backup_file": backup_file,
            "timestamp": timestamp,
            "size": len(content)
        })
        
        return backup_file
    
    def restore_from_backup(self, backup_file: str, target_file: str):
        """從備份恢復文件"""
        content = self.fs.read_file(backup_file)
        if content is None:
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        self.fs.write_file(target_file, content)
    
    def list_backups(self, source_file: str) -> List[Dict[str, Any]]:
        """列出文件的所有備份"""
        return self.backups.get(source_file, [])


def create_mock_file_operations() -> MockFileSystem:
    """創建標準的文件操作 Mock"""
    return MockFileSystem()


def create_populated_mock_filesystem() -> MockFileSystem:
    """創建包含測試數據的模擬文件系統"""
    fs = MockFileSystem()
    
    # 創建知識點文件
    knowledge_data = {
        "version": "3.0",
        "knowledge_points": [
            {
                "knowledge_point_id": "kp_001",
                "title": "動詞時態錯誤",
                "description": "過去式時態使用錯誤",
                "error_category": "systematic",
                "original_error": {
                    "chinese_sentence": "我昨天去了圖書館。",
                    "user_answer": "I go to library yesterday.",
                    "correct_answer": "I went to the library yesterday.",
                    "timestamp": "2024-01-01T10:00:00"
                },
                "review_examples": [],
                "correct_count": 0,
                "incorrect_count": 1,
                "mastery_level": 0.0,
                "next_review_date": "2024-01-02T10:00:00",
                "tags": ["grammar", "tense"],
                "created_at": "2024-01-01T10:00:00",
                "updated_at": "2024-01-01T10:00:00"
            }
        ]
    }
    
    fs.write_file("data/knowledge.json", json.dumps(knowledge_data, ensure_ascii=False, indent=2))
    
    # 創建練習記錄文件
    practice_data = {
        "version": "1.0",
        "records": [
            {
                "id": "practice_001",
                "chinese_sentence": "我喜歡讀書。",
                "user_answer": "I like read books.",
                "correct_answer": "I like reading books.",
                "is_correct": False,
                "timestamp": "2024-01-01T12:00:00",
                "knowledge_points": ["gerund_usage"]
            }
        ]
    }
    
    fs.write_file("data/practice_log.json", json.dumps(practice_data, ensure_ascii=False, indent=2))
    
    # 創建文法模式文件
    patterns_data = {
        "version": "1.0",
        "patterns": [
            {
                "id": "pattern_001", 
                "title": "現在進行時",
                "pattern": "be + V-ing",
                "examples": ["I am reading.", "She is studying."],
                "usage": "表示正在進行的動作"
            }
        ]
    }
    
    fs.write_file("data/grammar_patterns.json", json.dumps(patterns_data, ensure_ascii=False, indent=2))
    
    return fs


class FileOperationMockContext:
    """文件操作 Mock 上下文管理器"""
    
    def __init__(self, file_system: Optional[MockFileSystem] = None):
        self.file_system = file_system or MockFileSystem()
        self.json_handler = MockJSONFileHandler(self.file_system)
        self.backup_manager = MockBackupManager(self.file_system)
        self.patches = []
    
    def __enter__(self):
        # Mock Path.exists
        path_exists_patch = patch('pathlib.Path.exists')
        mock_exists = path_exists_patch.start()
        mock_exists.side_effect = lambda: self.file_system.exists(str(self))
        self.patches.append(path_exists_patch)
        
        # Mock Path.read_text
        path_read_patch = patch('pathlib.Path.read_text')
        mock_read = path_read_patch.start()
        def read_text_side_effect(encoding='utf-8'):
            content = self.file_system.read_file(str(self))
            if content is None:
                raise FileNotFoundError(f"File not found: {self}")
            return content
        mock_read.side_effect = read_text_side_effect
        self.patches.append(path_read_patch)
        
        # Mock Path.write_text
        path_write_patch = patch('pathlib.Path.write_text')
        mock_write = path_write_patch.start()
        def write_text_side_effect(content, encoding='utf-8'):
            self.file_system.write_file(str(self), content)
        mock_write.side_effect = write_text_side_effect
        self.patches.append(path_write_patch)
        
        # Mock Path.mkdir
        path_mkdir_patch = patch('pathlib.Path.mkdir')
        mock_mkdir = path_mkdir_patch.start()
        def mkdir_side_effect(parents=False, exist_ok=False):
            self.file_system.directories.add(str(self))
        mock_mkdir.side_effect = mkdir_side_effect
        self.patches.append(path_mkdir_patch)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch_obj in reversed(self.patches):
            patch_obj.stop()
        self.patches.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取文件操作統計"""
        return {
            "total_files": len(self.file_system.files),
            "total_operations": len(self.file_system.file_operations),
            "read_count": self.file_system.get_operation_count("read"),
            "write_count": self.file_system.get_operation_count("write"),
            "delete_count": self.file_system.get_operation_count("delete"),
            "operation_history": self.file_system.file_operations[-10:]  # 最近10次操作
        }