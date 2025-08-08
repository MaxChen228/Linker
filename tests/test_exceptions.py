"""
測試異常處理模組
"""

import tempfile
from pathlib import Path

import pytest

from core.exceptions import (
    APIException,
    DataException,
    FileOperationException,
    GeminiAPIException,
    LinkerError,
    ParseException,
    ValidationException,
    handle_file_operation,
    safe_parse_json,
    validate_input,
)


class TestExceptionHierarchy:
    """測試異常層級"""

    def test_base_exception(self):
        """測試基礎異常"""
        exc = LinkerError("測試錯誤", error_code="TEST001")
        assert exc.message == "測試錯誤"
        assert exc.error_code == "TEST001"
        assert exc.details == {}
        assert "[TEST001]" in str(exc)

    def test_api_exception(self):
        """測試API異常"""
        exc = APIException(
            "API錯誤",
            api_name="test_api",
            status_code=500,
            response={"error": "Internal Server Error"},
        )
        assert exc.api_name == "test_api"
        assert exc.status_code == 500
        assert exc.response == {"error": "Internal Server Error"}

    def test_gemini_api_exception(self):
        """測試Gemini API異常"""
        exc = GeminiAPIException("Gemini錯誤", model="gemini-pro", prompt="test prompt")
        # GeminiAPIException 沒有直接存儲 model 和 prompt 作為屬性
        assert exc.details["model"] == "gemini-pro"
        assert "test prompt" in exc.details["prompt_preview"]

    def test_parse_exception(self):
        """測試解析異常"""
        exc = ParseException("解析錯誤", parse_type="json", content="invalid json")
        assert exc.details["parse_type"] == "json"
        assert exc.details["content_preview"] == "invalid json"

    def test_validation_exception(self):
        """測試驗證異常"""
        exc = ValidationException("驗證失敗", field="age", value=150, expected_type="int < 120")
        assert exc.details["field"] == "age"
        assert exc.details["value"] == "150"
        assert exc.details["expected_type"] == "int < 120"

    def test_file_operation_exception(self):
        """測試文件操作異常"""
        exc = FileOperationException("文件錯誤", operation="read", file_path="/test/file.txt")
        assert exc.details["file_path"] == "/test/file.txt"
        assert exc.details["operation"] == "read"

    def test_data_exception(self):
        """測試數據異常"""
        exc = DataException("數據錯誤", data_type="json", file_path="/data/test.json")
        assert exc.details["data_type"] == "json"
        assert exc.details["file_path"] == "/data/test.json"


class TestUtilityFunctions:
    """測試工具函數"""

    def test_validate_input_valid(self):
        """測試有效輸入驗證"""
        # 應該不拋出異常
        validate_input(1, valid_options=[1, 2, 3])
        validate_input("a", valid_options=["a", "b", "c"])
        validate_input(5.0, min_value=0, max_value=10)

    def test_validate_input_invalid_option(self):
        """測試無效選項"""
        with pytest.raises(ValidationException) as exc_info:
            validate_input(4, valid_options=[1, 2, 3], field_name="choice")

        assert "choice" in str(exc_info.value)
        assert exc_info.value.details["value"] == "4"

    def test_validate_input_out_of_range(self):
        """測試超出範圍"""
        with pytest.raises(ValidationException) as exc_info:
            validate_input(15, min_value=0, max_value=10, field_name="score")

        assert "score" in str(exc_info.value)
        assert exc_info.value.details["value"] == "15"

    def test_safe_parse_json_valid(self):
        """測試有效JSON解析"""
        result = safe_parse_json('{"key": "value"}')
        assert result == {"key": "value"}

        result = safe_parse_json("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_safe_parse_json_invalid(self):
        """測試無效JSON解析"""
        with pytest.raises(ParseException) as exc_info:
            safe_parse_json("invalid json")

        assert exc_info.value.details["content_preview"] == "invalid json"

    def test_safe_parse_json_with_default(self):
        """測試帶默認值的JSON解析"""
        # 無效JSON返回默認值
        result = safe_parse_json("invalid", default={})
        assert result == {}

        # 空字符串會拋出異常（沒有default時）
        with pytest.raises(ParseException):
            safe_parse_json("")


class TestFileOperationDecorator:
    """測試文件操作裝飾器"""

    def test_successful_read(self):
        """測試成功的讀取操作"""

        @handle_file_operation("read")
        def read_file(path):
            with open(path) as f:
                return f.read()

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = read_file(temp_path)
            assert result == "test content"
        finally:
            Path(temp_path).unlink()

    def test_failed_read(self):
        """測試失敗的讀取操作"""

        @handle_file_operation("read")
        def read_file(path):
            with open(path) as f:
                return f.read()

        with pytest.raises(FileOperationException) as exc_info:
            read_file("/nonexistent/file.txt")

        assert exc_info.value.details["operation"] == "read"
        assert "/nonexistent/file.txt" in exc_info.value.details["file_path"]

    def test_successful_write(self):
        """測試成功的寫入操作"""

        @handle_file_operation("write")
        def write_file(path, content):
            with open(path, "w") as f:
                f.write(content)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            write_file(temp_path, "new content")
            with open(temp_path) as f:
                assert f.read() == "new content"
        finally:
            Path(temp_path).unlink()

    def test_permission_error(self):
        """測試權限錯誤"""

        @handle_file_operation("write")
        def write_file(path, content):
            with open(path, "w") as f:
                f.write(content)

        # 嘗試寫入根目錄（通常會失敗）
        with pytest.raises(FileOperationException) as exc_info:
            write_file("/root_file.txt", "content")

        assert exc_info.value.details["operation"] == "write"
