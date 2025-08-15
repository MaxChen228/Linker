"""
統一API端點管理系統 - Python版
TASK-34: 消除硬編碼 - 統一管理所有API路由定義

使用方法：
from web.config.api_endpoints import API_ENDPOINTS
router.post(API_ENDPOINTS.GRADE_ANSWER)
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ApiEndpoints:
    """API端點常量定義類
    
    使用dataclass確保不可變性，避免運行時意外修改
    """

    # ========== 練習相關API ==========
    GENERATE_QUESTION: str = "/api/generate-question"
    GRADE_ANSWER: str = "/api/grade-answer"
    CONFIRM_KNOWLEDGE: str = "/api/confirm-knowledge-points"

    # ========== 知識點管理API ==========
    KNOWLEDGE_BASE: str = "/api/knowledge"
    KNOWLEDGE_DETAIL: str = "/api/knowledge/{point_id}"
    KNOWLEDGE_RECOMMENDATIONS: str = "/api/knowledge/recommendations"
    KNOWLEDGE_TRASH_LIST: str = "/api/knowledge/trash/list"
    KNOWLEDGE_TRASH_CLEAR: str = "/api/knowledge/trash/clear"
    KNOWLEDGE_BATCH: str = "/api/knowledge/batch"
    KNOWLEDGE_BATCH_PROGRESS: str = "/api/knowledge/batch/{task_id}/progress"
    KNOWLEDGE_BATCH_DELETE: str = "/api/knowledge/batch/{task_id}"
    KNOWLEDGE_RESTORE: str = "/api/knowledge/{point_id}/restore"
    KNOWLEDGE_TAGS: str = "/api/knowledge/{point_id}/tags"
    KNOWLEDGE_NOTES: str = "/api/knowledge/{point_id}/notes"
    KNOWLEDGE_MAINTENANCE_DELETE_OLD: str = "/api/knowledge/maintenance/delete-old-points"
    KNOWLEDGE_DAILY_LIMIT_STATUS: str = "/api/knowledge/daily-limit/status"
    KNOWLEDGE_DAILY_LIMIT_CONFIG: str = "/api/knowledge/daily-limit/config"
    KNOWLEDGE_DAILY_LIMIT_STATS: str = "/api/knowledge/daily-limit/stats"
    KNOWLEDGE_SAVE_WITH_LIMIT: str = "/api/knowledge/save-with-limit"

    # ========== 日曆相關API ==========
    CALENDAR_DAY: str = "/calendar/api/day/{date}"
    CALENDAR_COMPLETE_REVIEW: str = "/calendar/api/complete-review/{pointId}"
    CALENDAR_STREAK_STATS: str = "/calendar/api/stats/streak"
    CALENDAR_STATS: str = "/calendar/api/stats"

    # ========== 模式分析API ==========
    PATTERNS_BASE: str = "/api/patterns"
    PATTERNS_DETAIL: str = "/api/patterns/{id}"

    # ========== 日誌與監控API ==========
    LOGS: str = "/api/logs"
    HEALTH: str = "/api/health"
    HEALTHZ: str = "/healthz"  # 健康檢查端點
    CONFIG: str = "/api/config"  # 配置端點（端口、環境等）

    # ========== 測試專用API ==========
    TEST_ASYNC_STATS: str = "/api/test/async-stats"
    TEST_ASYNC_REVIEW_CANDIDATES: str = "/api/test/async-review-candidates"
    TEST_SERVICE_HEALTH: str = "/api/test/service-health"

    # ========== 頁面路由 ==========
    HOME: str = "/"  # 主頁
    SETTINGS_PAGE: str = "/settings"  # 設定頁面
    KNOWLEDGE_PAGE: str = "/knowledge"  # 知識點頁面
    KNOWLEDGE_TRASH_PAGE: str = "/knowledge/trash"  # 知識點回收站頁面
    KNOWLEDGE_DETAIL_PAGE: str = "/knowledge/{point_id}"  # 知識點詳情頁面

    def get_all_endpoints(self) -> Dict[str, str]:
        """獲取所有端點的字典形式
        
        Returns:
            端點名稱到路徑的映射
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith('_') and isinstance(value, str)
        }

    def format_url(self, endpoint: str, **kwargs) -> str:
        """格式化帶參數的URL
        
        Args:
            endpoint: 端點路徑模板
            **kwargs: 要替換的參數
            
        Returns:
            格式化後的URL
            
        Example:
            >>> api.format_url(api.KNOWLEDGE_DETAIL, id=123)
            '/api/knowledge/123'
        """
        url = endpoint
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in url:
                url = url.replace(placeholder, str(value))
        return url

    def validate_endpoints(self) -> list:
        """驗證所有端點的格式
        
        Returns:
            錯誤列表，如果沒有錯誤則返回空列表
        """
        errors = []
        for name, path in self.get_all_endpoints().items():
            # 檢查路徑是否以/開頭
            if not path.startswith('/'):
                errors.append(f"端點 {name} 的路徑應以/開頭: {path}")

            # 檢查是否有未配對的大括號
            open_braces = path.count('{')
            close_braces = path.count('}')
            if open_braces != close_braces:
                errors.append(f"端點 {name} 的參數佔位符不配對: {path}")

        return errors


# 創建全局實例
API_ENDPOINTS = ApiEndpoints()

# 驗證配置
_validation_errors = API_ENDPOINTS.validate_endpoints()
if _validation_errors:
    import warnings
    warnings.warn(f"API端點配置錯誤: {_validation_errors}")


# 便捷函數
def get_endpoint(name: str) -> Optional[str]:
    """根據名稱獲取端點路徑
    
    Args:
        name: 端點名稱（大寫形式）
        
    Returns:
        端點路徑，如果不存在則返回None
    """
    return getattr(API_ENDPOINTS, name, None)


def format_endpoint(name: str, **kwargs) -> str:
    """格式化端點URL
    
    Args:
        name: 端點名稱
        **kwargs: URL參數
        
    Returns:
        格式化後的URL
        
    Raises:
        AttributeError: 如果端點不存在
    """
    endpoint = get_endpoint(name)
    if endpoint is None:
        raise AttributeError(f"未知的API端點: {name}")
    return API_ENDPOINTS.format_url(endpoint, **kwargs)


# 導出常用變量
__all__ = [
    'API_ENDPOINTS',
    'ApiEndpoints',
    'get_endpoint',
    'format_endpoint'
]
