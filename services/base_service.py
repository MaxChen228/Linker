"""
服務層基礎類別
提供統一的服務結果格式和錯誤處理機制
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime

from core.response import APIResponse
from core.error_handler import GlobalErrorHandler
from core.log_config import get_module_logger

# 泛型類型
T = TypeVar('T')

logger = get_module_logger(__name__)


@dataclass
class ServiceResult(Generic[T]):
    """
    服務執行結果
    
    統一的服務層返回格式，包含成功/失敗狀態、資料、訊息等
    """
    
    success: bool
    data: T | None = None
    message: str = ""
    error_type: str | None = None
    error_code: str | None = None
    warnings: List[str] | None = None
    metadata: Dict[str, Any] | None = None
    request_id: str | None = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())[:8]
    
    @staticmethod
    def success(
        data: T = None, 
        message: str = "操作成功",
        metadata: Dict[str, Any] | None = None,
        request_id: str | None = None
    ) -> ServiceResult[T]:
        """創建成功結果"""
        return ServiceResult(
            success=True,
            data=data,
            message=message,
            metadata=metadata,
            request_id=request_id
        )
    
    @staticmethod
    def error(
        message: str,
        error_type: str | None = None,
        error_code: str | None = None,
        data: T = None,
        warnings: List[str] | None = None,
        request_id: str | None = None
    ) -> ServiceResult[T]:
        """創建錯誤結果"""
        return ServiceResult(
            success=False,
            data=data,
            message=message,
            error_type=error_type,
            error_code=error_code,
            warnings=warnings,
            request_id=request_id
        )
    
    def to_api_response(self) -> APIResponse:
        """轉換為 API 響應格式"""
        if self.success:
            return APIResponse.success(
                data=self.data,
                message=self.message,
                request_id=self.request_id
            )
        else:
            return APIResponse.error(
                message=self.message,
                error_type=self.error_type,
                error_code=self.error_code,
                data=self.data,
                request_id=self.request_id
            )
    
    def add_warning(self, warning: str):
        """添加警告訊息"""
        if self.warnings is None:
            self.warnings = []
        self.warnings.append(warning)
    
    def add_metadata(self, key: str, value: Any):
        """添加元數據"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value


class BaseService(ABC):
    """
    服務層基礎抽象類別
    
    提供統一的服務架構，包含：
    - 依賴注入支援
    - 統一錯誤處理
    - 日誌記錄
    - 請求追蹤
    """
    
    def __init__(self, logger_name: str | None = None):
        """
        初始化基礎服務
        
        Args:
            logger_name: 日誌記錄器名稱，預設使用類別名稱
        """
        self.logger = get_module_logger(logger_name or self.__class__.__name__)
        self._initialized = False
    
    async def initialize(self):
        """
        異步初始化服務
        
        子類可以重寫此方法進行異步初始化操作
        """
        if not self._initialized:
            await self._setup_dependencies()
            self._initialized = True
            self.logger.info(f"{self.__class__.__name__} 服務初始化完成")
    
    async def _setup_dependencies(self):
        """設置依賴項（子類實現）"""
        pass
    
    def _create_request_context(
        self, 
        operation: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """創建請求上下文"""
        return {
            "service": self.__class__.__name__,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4())[:8],
            **kwargs
        }
    
    def _execute_with_error_handling(
        self, 
        operation: str, 
        func, 
        *args, 
        **kwargs
    ) -> ServiceResult:
        """
        執行操作並處理錯誤
        
        Args:
            operation: 操作名稱
            func: 要執行的函數
            *args: 位置參數
            **kwargs: 關鍵字參數
            
        Returns:
            ServiceResult: 服務執行結果
        """
        context = self._create_request_context(operation, **kwargs)
        request_id = context["request_id"]
        
        self.logger.info(
            f"開始執行 {operation}",
            operation=operation,
            request_id=request_id
        )
        
        try:
            # 執行業務邏輯
            result = func(*args, **kwargs)
            
            # 確保返回 ServiceResult 格式
            if not isinstance(result, ServiceResult):
                result = ServiceResult.success(
                    data=result,
                    message=f"{operation} 完成",
                    request_id=request_id
                )
            
            # 設置 request_id 如果沒有的話
            if result.request_id is None:
                result.request_id = request_id
            
            self.logger.info(
                f"{operation} 執行成功",
                operation=operation,
                request_id=request_id,
                success=result.success
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"{operation} 執行失敗",
                operation=operation,
                request_id=request_id,
                error=str(e),
                exc_info=True
            )
            
            return ServiceResult.error(
                message=f"{operation} 執行失敗: {str(e)}",
                error_type=type(e).__name__,
                error_code="SERVICE_EXECUTION_ERROR",
                request_id=request_id
            )
    
    def validate_input(self, data: Dict[str, Any], rules: Dict[str, Any]) -> ServiceResult[Dict[str, Any]]:
        """
        驗證輸入資料
        
        Args:
            data: 要驗證的資料
            rules: 驗證規則
            
        Returns:
            ServiceResult: 包含清理後資料的結果
        """
        from core.validators import ValidationService
        
        try:
            # 使用驗證服務進行驗證
            if "chinese" in data and "english" in data:
                is_valid, errors, cleaned_data = ValidationService.validate_practice_input(
                    chinese=data.get("chinese", ""),
                    english=data.get("english", ""),
                    mode=data.get("mode", "new"),
                    level=data.get("level", 1),
                    length=data.get("length", "short")
                )
                
                if not is_valid:
                    return ServiceResult.error(
                        message="輸入驗證失敗",
                        error_type="ValidationError",
                        error_code="VALIDATION_ERROR",
                        data={"errors": errors}
                    )
                
                return ServiceResult.success(
                    data=cleaned_data,
                    message="輸入驗證通過"
                )
            
            # 其他驗證邏輯...
            return ServiceResult.success(
                data=data,
                message="輸入驗證通過"
            )
            
        except Exception as e:
            return ServiceResult.error(
                message=f"輸入驗證過程發生錯誤: {str(e)}",
                error_type=type(e).__name__,
                error_code="VALIDATION_PROCESS_ERROR"
            )
    
    def log_operation(
        self,
        operation: str,
        success: bool,
        duration_ms: int | None = None,
        **context
    ):
        """記錄操作日誌"""
        log_data = {
            "operation": operation,
            "success": success,
            "service": self.__class__.__name__,
            **context
        }
        
        if duration_ms is not None:
            log_data["duration_ms"] = duration_ms
        
        if success:
            self.logger.info(f"操作成功: {operation}", **log_data)
        else:
            self.logger.warning(f"操作失敗: {operation}", **log_data)
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """
        獲取服務資訊
        
        Returns:
            Dict: 包含服務名稱、版本、狀態等資訊
        """
        pass


class ServiceRegistry:
    """服務註冊表"""
    
    _services: Dict[str, BaseService] = {}
    
    @classmethod
    def register(cls, name: str, service: BaseService):
        """註冊服務"""
        cls._services[name] = service
        logger.info(f"服務已註冊: {name} -> {service.__class__.__name__}")
    
    @classmethod
    def get(cls, name: str) -> BaseService | None:
        """獲取服務"""
        return cls._services.get(name)
    
    @classmethod
    def list_services(cls) -> List[str]:
        """列出所有註冊的服務"""
        return list(cls._services.keys())
    
    @classmethod
    def get_service_info(cls) -> Dict[str, Dict[str, Any]]:
        """獲取所有服務資訊"""
        return {
            name: service.get_service_info()
            for name, service in cls._services.items()
        }