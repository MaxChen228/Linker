"""
JSON 文件操作基礎抽象層

提供統一的 JSON 文件操作，包括：
- 原子性讀寫操作
- 自動備份機制
- 文件鎖定防止並發問題
- 版本遷移支援
"""

import json
import os
import shutil
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar('T')


class FileOperationError(Exception):
    """文件操作錯誤"""
    pass


class VersionMigrationError(Exception):
    """版本遷移錯誤"""
    pass


class JSONRepository(ABC, Generic[T]):
    """
    JSON 文件操作基礎抽象類
    
    提供統一的 JSON 文件操作接口，包含原子性操作、備份機制和並發控制。
    """
    
    def __init__(
        self, 
        file_path: str, 
        backup_count: int = 5,
        enable_backup: bool = True,
        lock_timeout: float = 30.0
    ):
        """
        初始化 JSON Repository
        
        Args:
            file_path: JSON 文件路徑
            backup_count: 保留的備份文件數量
            enable_backup: 是否啟用自動備份
            lock_timeout: 文件鎖超時時間（秒）
        """
        self.file_path = Path(file_path)
        self.backup_count = backup_count
        self.enable_backup = enable_backup
        self.lock_timeout = lock_timeout
        
        # 確保父目錄存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 文件鎖，防止並發操作
        self._lock = threading.RLock()
        self._lock_acquired = False
        
    @property
    @abstractmethod
    def current_version(self) -> str:
        """當前支持的數據版本"""
        pass
    
    @abstractmethod
    def migrate_data(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """
        數據版本遷移
        
        Args:
            data: 原始數據
            from_version: 原始版本
            
        Returns:
            遷移後的數據
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        驗證數據格式
        
        Args:
            data: 要驗證的數據
            
        Returns:
            是否有效
        """
        pass
    
    @contextmanager
    def _file_lock(self):
        """文件鎖上下文管理器"""
        acquired = self._lock.acquire(timeout=self.lock_timeout)
        if not acquired:
            raise FileOperationError(f"無法獲取文件鎖：{self.file_path}")
        
        self._lock_acquired = True
        try:
            yield
        finally:
            self._lock_acquired = False
            self._lock.release()
    
    def _create_backup(self) -> Optional[Path]:
        """創建備份文件"""
        if not self.enable_backup or not self.file_path.exists():
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.file_path.with_suffix(f".bak_{timestamp}{self.file_path.suffix}")
        
        try:
            shutil.copy2(self.file_path, backup_path)
            self._cleanup_old_backups()
            
            # 記錄事務操作
            if self._transaction_active:
                self._record_transaction_operation(
                    'backup', 
                    backup_path=backup_path,
                    description=f"創建備份文件：{backup_path.name}"
                )
            
            return backup_path
        except Exception as e:
            raise FileOperationError(f"創建備份失敗：{e}")
    
    def _cleanup_old_backups(self) -> int:
        """清理舊備份文件"""
        pattern = f"{self.file_path.stem}.bak_*{self.file_path.suffix}"
        backup_files = sorted(
            self.file_path.parent.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # 刪除超過 backup_count 的舊備份
        deleted_count = 0
        for backup_file in backup_files[self.backup_count:]:
            try:
                backup_file.unlink()
                deleted_count += 1
            except Exception:
                pass  # 忽略刪除失敗
        
        return deleted_count
    
    def _write_atomic(self, data: Dict[str, Any]) -> None:
        """原子性寫入文件"""
        temp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        
        try:
            # 寫入臨時文件
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子性重命名
            if os.name == 'nt':  # Windows
                if self.file_path.exists():
                    self.file_path.unlink()
            temp_path.replace(self.file_path)
            
        except Exception as e:
            # 清理臨時文件
            if temp_path.exists():
                temp_path.unlink()
            raise FileOperationError(f"原子性寫入失敗：{e}")
    
    def load(self) -> Dict[str, Any]:
        """
        加載數據
        
        Returns:
            加載的數據字典
        """
        with self._file_lock():
            if not self.file_path.exists():
                return self._get_default_data()
            
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # 檢查版本並進行遷移
                data = self._handle_version_migration(raw_data)
                
                # 驗證數據
                if not self.validate_data(data):
                    raise FileOperationError("數據格式驗證失敗")
                
                return data
                
            except json.JSONDecodeError as e:
                raise FileOperationError(f"JSON 解析錯誤：{e}")
            except Exception as e:
                raise FileOperationError(f"加載文件失敗：{e}")
    
    def save(self, data: Dict[str, Any]) -> None:
        """
        保存數據
        
        Args:
            data: 要保存的數據
        """
        with self._file_lock():
            # 驗證數據
            if not self.validate_data(data):
                raise FileOperationError("數據格式驗證失敗")
            
            # 創建備份
            backup_path = self._create_backup()
            
            try:
                # 添加版本信息和時間戳
                save_data = {
                    'version': self.current_version,
                    'last_updated': datetime.now().isoformat(),
                    **data
                }
                
                # 原子性寫入
                self._write_atomic(save_data)
                
            except Exception as e:
                # 如果保存失敗且有備份，嘗試恢復
                if backup_path and backup_path.exists():
                    try:
                        shutil.copy2(backup_path, self.file_path)
                    except Exception:
                        pass
                
                raise FileOperationError(f"保存文件失敗：{e}")
    
    def _handle_version_migration(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理版本遷移"""
        # 如果沒有版本信息，假設是舊版本
        if 'version' not in raw_data:
            # 根據數據結構推斷版本
            from_version = self._detect_version(raw_data)
        else:
            from_version = raw_data['version']
        
        # 如果版本相同，直接返回
        if from_version == self.current_version:
            return raw_data
        
        # 執行版本遷移
        try:
            migrated_data = self.migrate_data(raw_data, from_version)
            # 添加遷移標記
            migrated_data.setdefault('migration_date', datetime.now().isoformat())
            return migrated_data
        except Exception as e:
            raise VersionMigrationError(f"版本遷移失敗 ({from_version} -> {self.current_version}): {e}")
    
    def _detect_version(self, data: Dict[str, Any]) -> str:
        """檢測數據版本"""
        # 子類應該實現具體的版本檢測邏輯
        return "1.0"
    
    def _get_default_data(self) -> Dict[str, Any]:
        """獲取默認數據結構"""
        return {
            'version': self.current_version,
            'created_at': datetime.now().isoformat(),
            'data': []
        }
    
    def backup_now(self) -> Path:
        """
        立即創建備份
        
        Returns:
            備份文件路徑
        """
        with self._file_lock():
            backup_path = self._create_backup()
            if backup_path is None:
                raise FileOperationError("無法創建備份（文件不存在或備份已禁用）")
            return backup_path
    
    def restore_from_backup(self, backup_path: Path) -> None:
        """
        從備份恢復
        
        Args:
            backup_path: 備份文件路徑
        """
        with self._file_lock():
            if not backup_path.exists():
                raise FileOperationError(f"備份文件不存在：{backup_path}")
            
            try:
                # 驗證備份文件
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                if not self.validate_data(backup_data):
                    raise FileOperationError("備份文件數據格式無效")
                
                # 恢復文件
                shutil.copy2(backup_path, self.file_path)
                
            except json.JSONDecodeError as e:
                raise FileOperationError(f"備份文件 JSON 格式錯誤：{e}")
            except Exception as e:
                raise FileOperationError(f"恢復備份失敗：{e}")
    
    def list_backups(self) -> List[Path]:
        """
        列出所有備份文件
        
        Returns:
            按時間排序的備份文件列表（最新的在前）
        """
        pattern = f"{self.file_path.stem}.bak_*{self.file_path.suffix}"
        backup_files = list(self.file_path.parent.glob(pattern))
        return sorted(backup_files, key=lambda p: p.stat().st_mtime, reverse=True)
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        獲取文件信息
        
        Returns:
            文件信息字典
        """
        if not self.file_path.exists():
            return {
                'exists': False,
                'path': str(self.file_path)
            }
        
        stat = self.file_path.stat()
        return {
            'exists': True,
            'path': str(self.file_path),
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'is_locked': self._lock_acquired,
            'backup_count': len(self.list_backups())
        }