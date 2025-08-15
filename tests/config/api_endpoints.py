"""
測試專用API端點配置
TASK-34: 消除測試文件中的API硬編碼
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TestApiEndpoints:
    """測試用API端點常量定義"""

    # ========== 練習相關API ==========
    GENERATE_QUESTION: str = "/api/generate-question"
    GRADE_ANSWER: str = "/api/grade-answer"
    CONFIRM_KNOWLEDGE: str = "/api/confirm-knowledge-points"

    # ========== 知識點管理API ==========
    KNOWLEDGE_BASE: str = "/api/knowledge"
    KNOWLEDGE_DETAIL: str = "/api/knowledge/{point_id}"
    KNOWLEDGE_RECOMMENDATIONS: str = "/api/knowledge/recommendations"
    KNOWLEDGE_BATCH: str = "/api/knowledge/batch"
    KNOWLEDGE_BATCH_PROGRESS: str = "/api/knowledge/batch/{task_id}/progress"
    KNOWLEDGE_RESTORE: str = "/api/knowledge/{point_id}/restore"
    KNOWLEDGE_TRASH_CLEAR: str = "/api/knowledge/trash/clear"
    KNOWLEDGE_DAILY_LIMIT_STATUS: str = "/api/knowledge/daily-limit/status"
    KNOWLEDGE_SAVE_WITH_LIMIT: str = "/api/knowledge/save-with-limit"

    # ========== 日曆相關API ==========
    CALENDAR_DAY: str = "/calendar/api/day/{date}"
    CALENDAR_COMPLETE_REVIEW: str = "/calendar/api/complete-review/{point_id}"
    CALENDAR_STREAK_STATS: str = "/calendar/api/stats/streak"

    # ========== 測試專用API ==========
    TEST_ASYNC_STATS: str = "/api/test/stats"
    TEST_ASYNC_REVIEW_CANDIDATES: str = "/api/test/review-candidates"
    TEST_SERVICE_HEALTH: str = "/api/test/health"

    @classmethod
    def get_knowledge_detail(cls, point_id: int) -> str:
        """獲取知識點詳情API路徑"""
        return cls.KNOWLEDGE_DETAIL.replace("{point_id}", str(point_id))

    @classmethod
    def get_knowledge_restore(cls, point_id: int) -> str:
        """獲取恢復知識點API路徑"""
        return cls.KNOWLEDGE_RESTORE.replace("{point_id}", str(point_id))

    @classmethod
    def get_batch_progress(cls, task_id: str) -> str:
        """獲取批次進度API路徑"""
        return cls.KNOWLEDGE_BATCH_PROGRESS.replace("{task_id}", task_id)

    @classmethod
    def get_calendar_day(cls, date: str) -> str:
        """獲取日曆日期API路徑"""
        return cls.CALENDAR_DAY.replace("{date}", date)

    @classmethod
    def get_complete_review(cls, point_id: int) -> str:
        """獲取完成複習API路徑"""
        return cls.CALENDAR_COMPLETE_REVIEW.replace("{point_id}", str(point_id))


# 創建全局實例供測試使用
TEST_API_ENDPOINTS = TestApiEndpoints()
