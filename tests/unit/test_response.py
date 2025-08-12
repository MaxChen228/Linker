"""
統一API響應格式模組測試
"""

import json
import pytest
from datetime import datetime
from fastapi.responses import JSONResponse

from core.response import (
    APIResponse, 
    ResponseBuilder,
    success_response,
    error_response,
    paginated_response,
)


class TestAPIResponse:
    """APIResponse類測試"""
    
    def test_success_response_creation(self):
        """測試成功響應創建"""
        data = {"user_id": 123, "name": "test"}
        response = APIResponse.success(
            data=data,
            message="操作成功",
            request_id="req-123"
        )
        
        assert response.success is True
        assert response.data == data
        assert response.message == "操作成功"
        assert response.request_id == "req-123"
        assert response.error_type is None
        assert response.error_code is None
        assert response.timestamp is not None
    
    def test_error_response_creation(self):
        """測試錯誤響應創建"""
        response = APIResponse.error(
            message="驗證失敗",
            error_type="驗證錯誤",
            error_code="VALIDATION_ERROR",
            data={"field": "email"},
            request_id="req-456"
        )
        
        assert response.success is False
        assert response.message == "驗證失敗"
        assert response.error_type == "驗證錯誤"
        assert response.error_code == "VALIDATION_ERROR"
        assert response.data == {"field": "email"}
        assert response.request_id == "req-456"
        assert response.timestamp is not None
    
    def test_to_dict_excludes_none_values(self):
        """測試to_dict方法排除None值"""
        response = APIResponse.success(data={"test": "data"})
        response_dict = response.to_dict()
        
        assert "success" in response_dict
        assert "data" in response_dict
        assert "message" in response_dict
        assert "timestamp" in response_dict
        
        # None值應該被排除
        assert "error_type" not in response_dict
        assert "error_code" not in response_dict
        assert "request_id" not in response_dict
    
    def test_to_json(self):
        """測試JSON序列化"""
        data = {"test": "中文內容"}
        response = APIResponse.success(data=data, message="測試成功")
        json_str = response.to_json()
        
        # 驗證JSON格式
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert parsed["data"]["test"] == "中文內容"
        assert parsed["message"] == "測試成功"
        
        # 驗證ensure_ascii=False（中文正確顯示）
        assert "中文內容" in json_str
        assert "測試成功" in json_str
    
    def test_to_fastapi_response_success(self):
        """測試轉換為FastAPI響應（成功）"""
        data = {"result": "ok"}
        response = APIResponse.success(
            data=data,
            request_id="req-789"
        )
        
        fastapi_response = response.to_fastapi_response()
        
        assert isinstance(fastapi_response, JSONResponse)
        assert fastapi_response.status_code == 200
        assert fastapi_response.headers["X-Request-ID"] == "req-789"
        
        # 驗證響應內容
        content = json.loads(fastapi_response.body.decode())
        assert content["success"] is True
        assert content["data"] == data
    
    def test_to_fastapi_response_error_status_codes(self):
        """測試錯誤響應的狀態碼映射"""
        test_cases = [
            ("VALIDATION_ERROR", 400),
            ("NOT_FOUND_ERROR", 404),
            ("PERMISSION_ERROR", 403),
            ("API_ERROR", 502),
            ("CONFIG_ERROR", 500),
            ("FILE_OPERATION_ERROR", 500),
            ("DATA_ERROR", 422),
            ("PARSE_ERROR", 400),
            ("USER_INPUT_ERROR", 400),
            ("UNKNOWN_ERROR", 500),  # 未知錯誤默認500
        ]
        
        for error_code, expected_status in test_cases:
            response = APIResponse.error(
                message="測試錯誤",
                error_code=error_code
            )
            
            fastapi_response = response.to_fastapi_response()
            assert fastapi_response.status_code == expected_status
    
    def test_timestamp_generation(self):
        """測試時間戳生成"""
        response1 = APIResponse.success()
        response2 = APIResponse.success()
        
        # 時間戳應該不同
        assert response1.timestamp != response2.timestamp
        
        # 時間戳格式驗證
        datetime.fromisoformat(response1.timestamp)  # 應該不拋異常
        datetime.fromisoformat(response2.timestamp)  # 應該不拋異常


class TestResponseBuilder:
    """ResponseBuilder類測試"""
    
    def test_builder_pattern_success(self):
        """測試建構器模式（成功響應）"""
        response = (ResponseBuilder()
                   .success(True)
                   .data({"test": "data"})
                   .message("建構器測試成功")
                   .request_id("builder-123")
                   .build())
        
        assert response.success is True
        assert response.data == {"test": "data"}
        assert response.message == "建構器測試成功"
        assert response.request_id == "builder-123"
    
    def test_builder_pattern_error(self):
        """測試建構器模式（錯誤響應）"""
        response = (ResponseBuilder()
                   .success(False)
                   .message("建構器錯誤測試")
                   .error_type("測試錯誤")
                   .error_code("BUILDER_ERROR")
                   .build())
        
        assert response.success is False
        assert response.message == "建構器錯誤測試"
        assert response.error_type == "測試錯誤"
        assert response.error_code == "BUILDER_ERROR"
    
    def test_builder_chaining(self):
        """測試建構器方法鏈"""
        builder = ResponseBuilder()
        
        # 每個方法都應該返回同一個建構器實例
        assert builder.success() is builder
        assert builder.data("test") is builder
        assert builder.message("test") is builder
        assert builder.error_type("test") is builder
        assert builder.error_code("test") is builder
        assert builder.request_id("test") is builder


class TestConvenienceFunctions:
    """便利函數測試"""
    
    def test_success_response_function(self):
        """測試success_response便利函數"""
        data = {"items": [1, 2, 3]}
        response = success_response(
            data=data,
            message="查詢成功",
            request_id="func-123"
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        
        content = json.loads(response.body.decode())
        assert content["success"] is True
        assert content["data"] == data
        assert content["message"] == "查詢成功"
    
    def test_error_response_function(self):
        """測試error_response便利函數"""
        response = error_response(
            message="操作失敗",
            error_type="業務錯誤",
            error_code="VALIDATION_ERROR",  # 使用已定義的錯誤代碼
            status_code=422
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        
        content = json.loads(response.body.decode())
        assert content["success"] is False
        assert content["message"] == "操作失敗"
        assert content["error_type"] == "業務錯誤"
        assert content["error_code"] == "VALIDATION_ERROR"
    
    def test_paginated_response_function(self):
        """測試paginated_response便利函數"""
        items = [{"id": i, "name": f"item{i}"} for i in range(1, 6)]
        response = paginated_response(
            items=items,
            total=23,
            page=2,
            page_size=5,
            message="分頁查詢成功"
        )
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        
        content = json.loads(response.body.decode())
        assert content["success"] is True
        assert content["message"] == "分頁查詢成功"
        
        # 驗證分頁數據結構
        data = content["data"]
        assert data["items"] == items
        
        pagination = data["pagination"]
        assert pagination["total"] == 23
        assert pagination["page"] == 2
        assert pagination["page_size"] == 5
        assert pagination["total_pages"] == 5
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is True
    
    def test_paginated_response_edge_cases(self):
        """測試分頁響應邊界情況"""
        # 第一頁
        response = paginated_response([], 10, 1, 5)
        content = json.loads(response.body.decode())
        pagination = content["data"]["pagination"]
        assert pagination["has_prev"] is False
        assert pagination["has_next"] is True
        
        # 最後一頁
        response = paginated_response([], 10, 2, 5)
        content = json.loads(response.body.decode())
        pagination = content["data"]["pagination"]
        assert pagination["has_prev"] is True
        assert pagination["has_next"] is False
        
        # 空結果
        response = paginated_response([], 0, 1, 5)
        content = json.loads(response.body.decode())
        pagination = content["data"]["pagination"]
        assert pagination["total_pages"] == 0
        assert pagination["has_prev"] is False
        assert pagination["has_next"] is False