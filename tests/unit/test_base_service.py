"""
測試基礎服務層功能
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from datetime import datetime

from services.base_service import BaseService, ServiceResult, ServiceRegistry
from core.response import APIResponse


class MockService(BaseService):
    """模擬服務用於測試"""
    
    def get_service_info(self):
        return {
            "service_name": "MockService",
            "version": "1.0.0",
            "description": "模擬測試服務"
        }
    
    def test_operation_success(self, value: str) -> ServiceResult[str]:
        """測試成功操作"""
        return ServiceResult.success(
            data=f"processed: {value}",
            message="操作成功"
        )
    
    def test_operation_error(self, should_fail: bool = False) -> ServiceResult[str]:
        """測試錯誤操作"""
        if should_fail:
            raise ValueError("測試錯誤")
        return ServiceResult.success(data="success")


class TestServiceResult:
    """測試 ServiceResult 類別"""
    
    def test_success_result_creation(self):
        """測試成功結果創建"""
        result = ServiceResult.success(
            data={"key": "value"},
            message="操作成功"
        )
        
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.message == "操作成功"
        assert result.error_type is None
        assert result.error_code is None
        assert result.request_id is not None
    
    def test_error_result_creation(self):
        """測試錯誤結果創建"""
        result = ServiceResult.error(
            message="操作失敗",
            error_type="TestError",
            error_code="TEST_ERROR"
        )
        
        assert result.success is False
        assert result.message == "操作失敗"
        assert result.error_type == "TestError"
        assert result.error_code == "TEST_ERROR"
        assert result.request_id is not None
    
    def test_add_warning(self):
        """測試添加警告"""
        result = ServiceResult.success()
        result.add_warning("警告訊息")
        
        assert result.warnings == ["警告訊息"]
        
        result.add_warning("另一個警告")
        assert len(result.warnings) == 2
    
    def test_add_metadata(self):
        """測試添加元數據"""
        result = ServiceResult.success()
        result.add_metadata("key1", "value1")
        result.add_metadata("key2", 42)
        
        assert result.metadata == {"key1": "value1", "key2": 42}
    
    def test_to_api_response_success(self):
        """測試轉換為成功的 API 響應"""
        result = ServiceResult.success(
            data={"test": "data"},
            message="成功",
            request_id="test-id"
        )
        
        api_response = result.to_api_response()
        
        assert isinstance(api_response, APIResponse)
        assert api_response.success is True
        assert api_response.data == {"test": "data"}
        assert api_response.message == "成功"
        assert api_response.request_id == "test-id"
    
    def test_to_api_response_error(self):
        """測試轉換為錯誤的 API 響應"""
        result = ServiceResult.error(
            message="失敗",
            error_type="TestError",
            error_code="TEST_FAILED",
            request_id="test-id"
        )
        
        api_response = result.to_api_response()
        
        assert isinstance(api_response, APIResponse)
        assert api_response.success is False
        assert api_response.message == "失敗"
        assert api_response.error_type == "TestError"
        assert api_response.error_code == "TEST_FAILED"
        assert api_response.request_id == "test-id"


class TestBaseService:
    """測試 BaseService 基礎類別"""
    
    def setup_method(self):
        """每個測試方法前的設置"""
        self.service = MockService()
    
    def test_initialization(self):
        """測試服務初始化"""
        assert self.service.logger is not None
        assert self.service._initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_service(self):
        """測試異步初始化"""
        await self.service.initialize()
        assert self.service._initialized is True
    
    def test_create_request_context(self):
        """測試請求上下文創建"""
        context = self.service._create_request_context(
            "test_operation",
            param1="value1",
            param2=42
        )
        
        assert context["service"] == "MockService"
        assert context["operation"] == "test_operation"
        assert context["param1"] == "value1"
        assert context["param2"] == 42
        assert "timestamp" in context
        assert "request_id" in context
    
    def test_execute_with_error_handling_success(self):
        """測試成功執行操作"""
        result = self.service._execute_with_error_handling(
            "test_operation",
            self.service.test_operation_success,
            "test_value"
        )
        
        assert result.success is True
        assert result.data == "processed: test_value"
        assert "test_operation" in result.message
    
    def test_execute_with_error_handling_error(self):
        """測試錯誤處理"""
        result = self.service._execute_with_error_handling(
            "test_operation",
            self.service.test_operation_error,
            should_fail=True
        )
        
        assert result.success is False
        assert "測試錯誤" in result.message
        assert result.error_type == "ValueError"
        assert result.error_code == "SERVICE_EXECUTION_ERROR"
    
    @patch('services.base_service.ValidationService')
    def test_validate_input_practice_data(self, mock_validation_service):
        """測試練習輸入驗證"""
        # 模擬驗證服務
        mock_validation_service.validate_practice_input.return_value = (
            True,  # is_valid
            [],    # errors
            {"chinese": "測試", "english": "test"}  # cleaned_data
        )
        
        data = {"chinese": "測試", "english": "test"}
        result = self.service.validate_input(data, {})
        
        assert result.success is True
        assert result.data == {"chinese": "測試", "english": "test"}
        mock_validation_service.validate_practice_input.assert_called_once()
    
    @patch('services.base_service.ValidationService')
    def test_validate_input_failure(self, mock_validation_service):
        """測試輸入驗證失敗"""
        mock_validation_service.validate_practice_input.return_value = (
            False,  # is_valid
            ["中文句子過短", "英文翻譯為空"],  # errors
            {}  # cleaned_data
        )
        
        data = {"chinese": "", "english": ""}
        result = self.service.validate_input(data, {})
        
        assert result.success is False
        assert "輸入驗證失敗" in result.message
        assert result.error_code == "VALIDATION_ERROR"
        assert "errors" in result.data
    
    def test_log_operation(self):
        """測試操作日誌記錄"""
        with patch.object(self.service.logger, 'info') as mock_info:
            self.service.log_operation(
                "test_operation",
                success=True,
                duration_ms=100,
                extra_context="test"
            )
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert "操作成功: test_operation" in args[0]
            assert kwargs["operation"] == "test_operation"
            assert kwargs["success"] is True
            assert kwargs["duration_ms"] == 100
    
    def test_get_service_info(self):
        """測試獲取服務資訊"""
        info = self.service.get_service_info()
        
        assert info["service_name"] == "MockService"
        assert info["version"] == "1.0.0"
        assert info["description"] == "模擬測試服務"


class TestServiceRegistry:
    """測試服務註冊表"""
    
    def setup_method(self):
        """每個測試方法前的設置"""
        # 清空註冊表
        ServiceRegistry._services.clear()
    
    def test_register_service(self):
        """測試註冊服務"""
        service = MockService()
        ServiceRegistry.register("test_service", service)
        
        assert "test_service" in ServiceRegistry._services
        assert ServiceRegistry._services["test_service"] is service
    
    def test_get_service(self):
        """測試獲取服務"""
        service = MockService()
        ServiceRegistry.register("test_service", service)
        
        retrieved = ServiceRegistry.get("test_service")
        assert retrieved is service
        
        # 測試不存在的服務
        not_found = ServiceRegistry.get("non_existent")
        assert not_found is None
    
    def test_list_services(self):
        """測試列出服務"""
        service1 = MockService()
        service2 = MockService()
        
        ServiceRegistry.register("service1", service1)
        ServiceRegistry.register("service2", service2)
        
        services = ServiceRegistry.list_services()
        assert set(services) == {"service1", "service2"}
    
    def test_get_service_info(self):
        """測試獲取所有服務資訊"""
        service = MockService()
        ServiceRegistry.register("test_service", service)
        
        info = ServiceRegistry.get_service_info()
        
        assert "test_service" in info
        assert info["test_service"]["service_name"] == "MockService"


class TestServiceResultTypes:
    """測試不同類型的服務結果"""
    
    def test_generic_typing(self):
        """測試泛型類型支援"""
        # 字符串類型結果
        str_result = ServiceResult.success(data="test string")
        assert isinstance(str_result.data, str)
        
        # 字典類型結果
        dict_result = ServiceResult.success(data={"key": "value"})
        assert isinstance(dict_result.data, dict)
        
        # 列表類型結果
        list_result = ServiceResult.success(data=[1, 2, 3])
        assert isinstance(list_result.data, list)
    
    def test_none_data(self):
        """測試空數據結果"""
        result = ServiceResult.success(data=None)
        assert result.success is True
        assert result.data is None
    
    def test_request_id_generation(self):
        """測試請求 ID 自動生成"""
        result1 = ServiceResult.success()
        result2 = ServiceResult.success()
        
        assert result1.request_id is not None
        assert result2.request_id is not None
        assert result1.request_id != result2.request_id
        assert len(result1.request_id) == 8  # UUID 前8位


# 集成測試
class TestServiceIntegration:
    """服務集成測試"""
    
    def test_service_workflow(self):
        """測試完整的服務工作流程"""
        service = MockService()
        
        # 1. 執行操作
        result = service._execute_with_error_handling(
            "integration_test",
            service.test_operation_success,
            "test_data"
        )
        
        # 2. 驗證結果
        assert result.success is True
        assert "processed: test_data" in result.data
        
        # 3. 轉換為 API 響應
        api_response = result.to_api_response()
        assert api_response.success is True
        
        # 4. 獲取服務資訊
        info = service.get_service_info()
        assert info["service_name"] == "MockService"