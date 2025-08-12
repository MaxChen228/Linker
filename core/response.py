"""
統一API響應格式模組
提供標準化的API響應格式，確保一致的客戶端體驗
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from fastapi.responses import JSONResponse


@dataclass
class APIResponse:
    """
    統一API響應格式

    提供標準化的響應結構，包含成功/失敗狀態、資料、訊息和元數據
    """

    success: bool
    data: Any | None = None
    message: str | None = None
    error_type: str | None = None
    error_code: str | None = None
    timestamp: str = ""
    request_id: str | None = None

    def __post_init__(self):
        """初始化後處理"""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @staticmethod
    def success(
        data: Any | None = None,
        message: str = "操作成功",
        request_id: str | None = None,
    ) -> APIResponse:
        """
        創建成功響應

        Args:
            data: 響應資料
            message: 成功訊息
            request_id: 請求ID

        Returns:
            APIResponse: 成功響應物件
        """
        return APIResponse(
            success=True,
            data=data,
            message=message,
            request_id=request_id,
        )

    @staticmethod
    def error(
        message: str = "操作失敗",
        error_type: str | None = None,
        error_code: str | None = None,
        data: Any | None = None,
        request_id: str | None = None,
    ) -> APIResponse:
        """
        創建錯誤響應

        Args:
            message: 錯誤訊息
            error_type: 錯誤類型
            error_code: 錯誤代碼
            data: 額外資料（例如驗證錯誤詳情）
            request_id: 請求ID

        Returns:
            APIResponse: 錯誤響應物件
        """
        return APIResponse(
            success=False,
            message=message,
            error_type=error_type,
            error_code=error_code,
            data=data,
            request_id=request_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """轉換為字典"""
        result = asdict(self)
        # 移除值為None的欄位以減少響應大小
        return {k: v for k, v in result.items() if v is not None}

    def to_json(self) -> str:
        """轉換為JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_fastapi_response(
        self,
        status_code: int | None = None,
        headers: dict[str, str] | None = None
    ) -> JSONResponse:
        """
        轉換為FastAPI JSONResponse

        Args:
            status_code: HTTP狀態碼，如果不指定會根據success自動決定
            headers: 額外的響應標頭

        Returns:
            JSONResponse: FastAPI響應物件
        """
        if status_code is None:
            status_code = 200 if self.success else 400

            # 根據錯誤類型調整狀態碼（僅當沒有顯式指定status_code時）
            if not self.success and self.error_code:
                error_status_mapping = {
                    "VALIDATION_ERROR": 400,
                    "NOT_FOUND_ERROR": 404,
                    "PERMISSION_ERROR": 403,
                    "API_ERROR": 502,
                    "CONFIG_ERROR": 500,
                    "FILE_OPERATION_ERROR": 500,
                    "DATA_ERROR": 422,
                    "PARSE_ERROR": 400,
                    "USER_INPUT_ERROR": 400,
                }
                status_code = error_status_mapping.get(self.error_code, 500)

        response_headers = headers or {}
        if self.request_id:
            response_headers["X-Request-ID"] = self.request_id

        return JSONResponse(
            content=self.to_dict(),
            status_code=status_code,
            headers=response_headers
        )


class ResponseBuilder:
    """
    響應建構器

    提供鏈式API來建構複雜的響應物件
    """

    def __init__(self):
        self._success: bool = True
        self._data: Any | None = None
        self._message: str | None = None
        self._error_type: str | None = None
        self._error_code: str | None = None
        self._request_id: str | None = None

    def success(self, success: bool = True) -> ResponseBuilder:
        """設置成功狀態"""
        self._success = success
        return self

    def data(self, data: Any) -> ResponseBuilder:
        """設置響應資料"""
        self._data = data
        return self

    def message(self, message: str) -> ResponseBuilder:
        """設置響應訊息"""
        self._message = message
        return self

    def error_type(self, error_type: str) -> ResponseBuilder:
        """設置錯誤類型"""
        self._error_type = error_type
        return self

    def error_code(self, error_code: str) -> ResponseBuilder:
        """設置錯誤代碼"""
        self._error_code = error_code
        return self

    def request_id(self, request_id: str) -> ResponseBuilder:
        """設置請求ID"""
        self._request_id = request_id
        return self

    def build(self) -> APIResponse:
        """建構響應物件"""
        return APIResponse(
            success=self._success,
            data=self._data,
            message=self._message,
            error_type=self._error_type,
            error_code=self._error_code,
            request_id=self._request_id,
        )


# 便利函數
def success_response(
    data: Any | None = None,
    message: str = "操作成功",
    request_id: str | None = None,
) -> JSONResponse:
    """快速創建成功響應"""
    return APIResponse.success(data, message, request_id).to_fastapi_response()


def error_response(
    message: str = "操作失敗",
    error_type: str | None = None,
    error_code: str | None = None,
    data: Any | None = None,
    request_id: str | None = None,
    status_code: int | None = None,
) -> JSONResponse:
    """快速創建錯誤響應"""
    response = APIResponse.error(message, error_type, error_code, data, request_id)
    return response.to_fastapi_response(status_code)


def paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "查詢成功",
    request_id: str | None = None,
) -> JSONResponse:
    """創建分頁響應"""
    total_pages = (total + page_size - 1) // page_size

    pagination_data = {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    }

    return success_response(pagination_data, message, request_id)
