"""
全局錯誤處理器模組測試
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from core.error_handler import (
    GlobalErrorHandler,
    handle_api_errors,
    handle_validation_errors,
    handle_file_errors,
    global_exception_handler,
    http_exception_handler,
)
from core.exceptions import (
    LinkerError,
    DataException,
    ValidationException,
    APIException,
    GeminiAPIException,
    ConfigException,
    FileOperationException,
    ParseException,
    UserInputException,
)
from core.response import APIResponse


class TestGlobalErrorHandler:
    """GlobalErrorHandler類測試"""
    
    def test_handle_linker_error(self):
        """測試處理LinkerError"""
        error = DataException(
            message="資料載入失敗",
            data_type="json",
            file_path="/path/to/file.json"
        )
        
        response = GlobalErrorHandler.handle(error, request_id="test-123")
        
        assert response.success is False
        assert response.message == "資料載入失敗"
        assert response.error_type == "數據錯誤"
        assert response.error_code == "DATA_ERROR"
        assert response.request_id == "test-123"
        assert response.data is None  # 默認不包含詳細信息
    
    def test_handle_validation_exception(self):
        """測試處理ValidationException"""
        error = ValidationException(
            message="Email格式錯誤",
            field="email",
            value="invalid-email",
            expected_type="email format"
        )
        
        response = GlobalErrorHandler.handle(error)
        
        assert response.success is False
        assert response.message == "Email格式錯誤"
        assert response.error_type == "驗證錯誤"
        assert response.error_code == "VALIDATION_ERROR"
    
    def test_handle_gemini_api_exception(self):
        """測試處理GeminiAPIException"""
        error = GeminiAPIException(
            message="API配額不足",
            model="gemini-pro",
            prompt="測試prompt"
        )
        
        response = GlobalErrorHandler.handle(error)
        
        assert response.success is False
        assert response.message == "API配額不足"
        assert response.error_type == "AI服務錯誤"
        assert response.error_code == "API_ERROR"
    
    def test_handle_python_standard_exceptions(self):
        """測試處理Python標準異常"""
        test_cases = [
            (ValueError("無效數值"), "數值錯誤", "VALUEERROR"),
            (TypeError("類型錯誤"), "類型錯誤", "TYPEERROR"),
            (KeyError("missing_key"), "缺少必要參數", "KEYERROR"),
            (FileNotFoundError("文件不存在"), "文件不存在", "FILENOTFOUNDERROR"),
            (PermissionError("權限不足"), "權限錯誤", "PERMISSIONERROR"),
            (ConnectionError("連接失敗"), "連接錯誤", "CONNECTIONERROR"),
            (TimeoutError("操作超時"), "超時錯誤", "TIMEOUTERROR"),
        ]
        
        for exception, expected_type, expected_code in test_cases:
            response = GlobalErrorHandler.handle(exception)
            
            assert response.success is False
            assert response.error_type == expected_type
            assert response.error_code == expected_code
    
    def test_handle_http_exception(self):
        """測試處理HTTPException"""
        error = HTTPException(status_code=404, detail="頁面不存在")
        
        response = GlobalErrorHandler.handle(error)
        
        assert response.success is False
        assert response.message == "404: 頁面不存在"
        assert response.error_type == "HTTP錯誤"
        assert response.error_code == "HTTPEXCEPTION"
    
    def test_handle_unknown_exception(self):
        """測試處理未知異常"""
        class CustomException(Exception):
            pass
        
        error = CustomException("自定義錯誤")
        response = GlobalErrorHandler.handle(error)
        
        assert response.success is False
        assert response.message == "自定義錯誤"
        assert response.error_type == "未知錯誤"
        assert response.error_code == "CUSTOMEXCEPTION"
    
    def test_handle_with_details(self):
        """測試包含詳細信息的錯誤處理"""
        error = ValidationException(
            message="驗證失敗",
            field="age",
            value="-5",
            expected_type="positive integer"
        )
        
        response = GlobalErrorHandler.handle(error, include_details=True)
        
        assert response.success is False
        assert response.data is not None
        assert "exception_type" in response.data
        assert "traceback" in response.data
        assert "details" in response.data
        assert response.data["details"]["field"] == "age"
        assert response.data["details"]["value"] == "-5"
    
    @patch('core.error_handler.logger')
    def test_logging_levels(self, mock_logger):
        """測試不同錯誤的日誌級別"""
        # Error級別
        error = APIException("API錯誤")
        GlobalErrorHandler.handle(error)
        mock_logger.log_exception.assert_called()
        
        mock_logger.reset_mock()
        
        # Warning級別
        error = ValidationException("驗證錯誤", field="test")
        GlobalErrorHandler.handle(error)
        mock_logger.warning.assert_called()
        
        mock_logger.reset_mock()
        
        # Info級別
        error = UserInputException("輸入錯誤", input_type="text")
        GlobalErrorHandler.handle(error)
        mock_logger.info.assert_called()


class TestErrorDecorators:
    """錯誤處理裝飾器測試"""
    
    def test_handle_api_errors_sync_function(self):
        """測試同步函數的錯誤處理裝飾器"""
        @handle_api_errors()
        def test_function():
            raise ValueError("測試錯誤")
        
        result = test_function()
        
        assert isinstance(result, JSONResponse)
        content = json.loads(result.body.decode())
        assert content["success"] is False
        assert content["message"] == "測試錯誤"
        assert content["error_type"] == "數值錯誤"
    
    @pytest.mark.asyncio
    async def test_handle_api_errors_async_function(self):
        """測試異步函數的錯誤處理裝飾器"""
        @handle_api_errors()
        async def test_async_function():
            raise DataException("資料錯誤", data_type="json")
        
        result = await test_async_function()
        
        assert isinstance(result, JSONResponse)
        content = json.loads(result.body.decode())
        assert content["success"] is False
        assert content["message"] == "資料錯誤"
        assert content["error_type"] == "數據錯誤"
    
    def test_handle_api_errors_with_custom_message(self):
        """測試自定義錯誤訊息的裝飾器"""
        @handle_api_errors(default_message="自定義錯誤訊息")
        def test_function():
            raise ValueError("原始錯誤")
        
        result = test_function()
        content = json.loads(result.body.decode())
        assert content["message"] == "自定義錯誤訊息"
    
    def test_handle_api_errors_with_details(self):
        """測試包含詳細信息的裝飾器"""
        @handle_api_errors(include_details=True)
        def test_function():
            raise ValidationException("驗證失敗", field="email")
        
        result = test_function()
        content = json.loads(result.body.decode())
        assert content["data"] is not None
        assert "traceback" in content["data"]
    
    def test_handle_api_errors_success_case(self):
        """測試裝飾器不影響正常執行"""
        @handle_api_errors()
        def test_function():
            return {"status": "ok"}
        
        result = test_function()
        assert result == {"status": "ok"}
    
    @pytest.mark.asyncio
    async def test_handle_api_errors_async_success_case(self):
        """測試異步函數正常執行情況"""
        @handle_api_errors()
        async def test_async_function():
            return {"status": "ok"}
        
        result = await test_async_function()
        assert result == {"status": "ok"}
    
    def test_handle_validation_errors_decorator(self):
        """測試驗證錯誤專用裝飾器"""
        @handle_validation_errors
        def test_function():
            raise ValueError("驗證錯誤")
        
        result = test_function()
        content = json.loads(result.body.decode())
        assert content["message"] == "資料驗證失敗，請檢查輸入格式"
        assert content["data"] is not None  # 包含詳細信息
    
    def test_handle_file_errors_decorator(self):
        """測試文件錯誤專用裝飾器"""
        @handle_file_errors
        def test_function():
            raise FileNotFoundError("文件不存在")
        
        result = test_function()
        content = json.loads(result.body.decode())
        assert content["message"] == "文件操作失敗，請稍後再試"
        assert "data" not in content or content.get("data") is None  # 不包含詳細信息
    
    def test_request_id_extraction_from_fastapi_request(self):
        """測試從FastAPI Request中提取request_id"""
        # 創建模擬的FastAPI Request
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.request_id = "extracted-123"
        
        @handle_api_errors()
        def test_function(request):
            raise ValueError("測試錯誤")
        
        result = test_function(mock_request)
        content = json.loads(result.body.decode())
        assert content["request_id"] == "extracted-123"


class TestFastAPIExceptionHandlers:
    """FastAPI異常處理器測試"""
    
    @pytest.mark.asyncio
    async def test_global_exception_handler(self):
        """測試全局異常處理器"""
        # 創建模擬的Request
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.request_id = "global-123"
        
        exception = ValueError("全局異常測試")
        response = await global_exception_handler(mock_request, exception)
        
        assert isinstance(response, JSONResponse)
        content = json.loads(response.body.decode())
        assert content["success"] is False
        assert content["request_id"] == "global-123"
        assert content["error_type"] == "數值錯誤"
    
    @pytest.mark.asyncio
    async def test_http_exception_handler(self):
        """測試HTTP異常處理器"""
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.request_id = "http-456"
        
        exception = HTTPException(status_code=404, detail="資源不存在")
        response = await http_exception_handler(mock_request, exception)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        content = json.loads(response.body.decode())
        assert content["success"] is False
        assert content["message"] == "資源不存在"
        assert content["error_type"] == "HTTP錯誤"
        assert content["error_code"] == "HTTP_404"
        assert content["request_id"] == "http-456"
    
    @pytest.mark.asyncio
    async def test_exception_handler_without_request_id(self):
        """測試沒有request_id的異常處理"""
        # 創建一個簡單的物件而不是Mock來避免序列化問題
        class MockState:
            pass
        
        class MockRequest:
            def __init__(self):
                self.state = MockState()
        
        mock_request = MockRequest()
        
        exception = ValueError("無request_id測試")
        response = await global_exception_handler(mock_request, exception)
        
        content = json.loads(response.body.decode())
        assert "request_id" not in content or content.get("request_id") is None


class TestExceptionMapping:
    """異常映射測試"""
    
    def test_exception_mapping_completeness(self):
        """測試異常映射的完整性"""
        # 驗證所有Linker異常都有對應的映射
        linker_exceptions = [
            DataException,
            ValidationException,
            APIException,
            GeminiAPIException,
            ConfigException,
            FileOperationException,
            ParseException,
            UserInputException,
        ]
        
        for exc_class in linker_exceptions:
            # 創建異常實例
            if exc_class == GeminiAPIException:
                exc = exc_class("測試", model="test")
            elif exc_class == DataException:
                exc = exc_class("測試", data_type="test", file_path="test")
            elif exc_class == FileOperationException:
                exc = exc_class("測試", operation="read", file_path="test")
            elif exc_class == ValidationException:
                exc = exc_class("測試", field="test")
            elif exc_class == ConfigException:
                exc = exc_class("測試", config_key="test")
            elif exc_class == ParseException:
                exc = exc_class("測試", parse_type="json")
            elif exc_class == UserInputException:
                exc = exc_class("測試", input_type="text")
            else:
                exc = exc_class("測試")
            
            # 驗證能找到配置
            config = GlobalErrorHandler._find_exception_config(type(exc))
            assert config["error_type"] is not None
            assert config["default_message"] is not None
            assert config["log_level"] in ["error", "warning", "info"]
    
    def test_inheritance_mapping(self):
        """測試繼承關係的異常映射"""
        # 創建繼承自ValidationException的自定義異常
        class CustomValidationError(ValidationException):
            pass
        
        error = CustomValidationError("自定義驗證錯誤", field="test")
        response = GlobalErrorHandler.handle(error)
        
        # 應該使用父類的映射配置
        assert response.error_type == "驗證錯誤"
        assert response.error_code == "VALIDATION_ERROR"