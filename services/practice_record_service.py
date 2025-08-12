"""
練習記錄服務
處理練習記錄的業務邏輯，包括記錄管理、統計分析、歷史查詢等
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

from core.repositories.practice_repository import PracticeRepository
from core.config_manager import get_config
from core.constants import PracticeConfig

from .base_service import BaseService, ServiceResult


class PracticeRecordService(BaseService):
    """
    練習記錄服務

    負責處理練習記錄的所有業務邏輯：
    - 記錄練習活動
    - 統計分析
    - 歷史查詢
    - 準確率計算
    """

    def __init__(self, practice_repo: Optional[PracticeRepository] = None):
        """
        初始化練習記錄服務

        Args:
            practice_repo: 練習記錄倉庫，用於依賴注入
        """
        super().__init__()
        self.practice_repo = practice_repo or PracticeRepository("data/practice_log.json")

    def record_practice(
        self,
        chinese_sentence: str,
        user_answer: str,
        is_correct: bool,
        feedback: dict[str, Any],
        practice_mode: str = "new",
        difficulty_level: int = 1,
        knowledge_point_ids: Optional[list[int]] = None
    ) -> ServiceResult[dict[str, Any]]:
        """記錄練習活動"""
        try:
            record = {
                "timestamp": datetime.now().isoformat(),
                "chinese_sentence": chinese_sentence,
                "user_answer": user_answer,
                "is_correct": is_correct,
                "feedback": feedback,
                "practice_mode": practice_mode,
                "difficulty_level": difficulty_level,
                "knowledge_point_ids": knowledge_point_ids or []
            }

            success = self.practice_repo.add_practice_record(record)
            if success:
                return ServiceResult.success(record, "練習記錄已保存")
            else:
                return ServiceResult.error("保存練習記錄失敗")
        except Exception as e:
            return ServiceResult.error(f"記錄練習失敗: {str(e)}")

    def get_practice_history(
        self,
        limit: Optional[int] = None,
        practice_mode: Optional[str] = None
    ) -> ServiceResult[list[dict[str, Any]]]:
        """獲取練習歷史"""
        try:
            if practice_mode:
                records = self.practice_repo.get_records_by_practice_mode(practice_mode)
            else:
                data = self.practice_repo.load()
                records = data['data']

            # 按時間降序排序
            records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            if limit:
                records = records[:limit]

            return ServiceResult.success(records, f"獲取到 {len(records)} 條練習記錄")
        except Exception as e:
            return ServiceResult.error(f"獲取練習歷史失敗: {str(e)}")

    def get_practice_statistics(
        self,
        days: Optional[int] = None
    ) -> ServiceResult[dict[str, Any]]:
        """獲取練習統計"""
        try:
            stats = self.practice_repo.get_statistics(days)

            # 添加額外統計指標
            stats['streak_days'] = self._calculate_streak_days()
            stats['average_daily_practices'] = self._calculate_average_daily_practices(days)
            stats['improvement_trend'] = self._calculate_improvement_trend(days)

            return ServiceResult.success(stats, "統計數據獲取成功")
        except Exception as e:
            return ServiceResult.error(f"獲取統計失敗: {str(e)}")

    def get_recent_practices(self, days: int = 7) -> ServiceResult[list[dict[str, Any]]]:
        """獲取最近的練習記錄"""
        try:
            records = self.practice_repo.get_recent_records(days)
            return ServiceResult.success(records, f"獲取最近 {days} 天的練習記錄")
        except Exception as e:
            return ServiceResult.error(f"獲取最近練習失敗: {str(e)}")

    def get_practice_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> ServiceResult[list[dict[str, Any]]]:
        """按日期範圍獲取練習"""
        try:
            records = self.practice_repo.get_records_by_date_range(start_date, end_date)
            date_range = f"{start_date.date()} 到 {end_date.date()}"
            return ServiceResult.success(records, f"獲取 {date_range} 的練習記錄")
        except Exception as e:
            return ServiceResult.error(f"按日期範圍獲取練習失敗: {str(e)}")

    def calculate_accuracy(
        self,
        days: Optional[int] = None,
        practice_mode: Optional[str] = None
    ) -> ServiceResult[float]:
        """計算準確率"""
        try:
            if days:
                records = self.practice_repo.get_recent_records(days)
            else:
                data = self.practice_repo.load()
                records = data['data']

            if practice_mode:
                records = [r for r in records if r.get('practice_mode') == practice_mode]

            if not records:
                return ServiceResult.success(0.0, "無練習記錄")

            correct_count = sum(1 for r in records if r.get('is_correct', False))
            accuracy = correct_count / len(records)

            return ServiceResult.success(accuracy, f"準確率: {accuracy:.2%}")
        except Exception as e:
            return ServiceResult.error(f"計算準確率失敗: {str(e)}")

    def get_daily_statistics(self, days: int = 30) -> ServiceResult[list[dict[str, Any]]]:
        """獲取每日統計"""
        try:
            trend_data = self.practice_repo.get_performance_trend(days)
            return ServiceResult.success(trend_data, f"獲取最近 {days} 天的每日統計")
        except Exception as e:
            return ServiceResult.error(f"獲取每日統計失敗: {str(e)}")

    def _calculate_streak_days(self) -> int:
        """計算連續練習天數"""
        try:
            config = get_config()
            records = self.practice_repo.get_recent_records(config.practice_recent_days)  # 從配置讀取天數
            if not records:
                return 0

            # 按日期分組
            daily_practices = defaultdict(int)
            for record in records:
                date_str = record['timestamp'][:10]
                daily_practices[date_str] += 1

            # 從今天開始往前計算連續天數
            streak = 0
            current_date = datetime.now().date()

            while current_date.isoformat() in daily_practices:
                streak += 1
                current_date -= timedelta(days=1)

            return streak
        except Exception:
            return 0

    def _calculate_average_daily_practices(self, days: Optional[int] = None) -> float:
        """計算平均每日練習次數"""
        try:
            if days:
                records = self.practice_repo.get_recent_records(days)
                period_days = days
            else:
                data = self.practice_repo.load()
                records = data['data']
                if not records:
                    return 0.0
                # 計算從第一條記錄到現在的天數
                first_date = datetime.fromisoformat(records[0]['timestamp'][:10])
                period_days = (datetime.now() - first_date).days + 1

            if period_days <= 0:
                return 0.0

            return len(records) / period_days
        except Exception:
            return 0.0

    def _calculate_improvement_trend(self, days: Optional[int] = None) -> str:
        """計算改進趨勢"""
        try:
            trend_data = self.practice_repo.get_performance_trend(days or 14)
            if len(trend_data) < 2:
                return "insufficient_data"

            # 比較前半段和後半段的準確率
            mid_point = len(trend_data) // 2
            early_accuracy = sum(d['accuracy'] for d in trend_data[:mid_point]) / mid_point
            recent_accuracy = sum(d['accuracy'] for d in trend_data[mid_point:]) / (len(trend_data) - mid_point)

            diff = recent_accuracy - early_accuracy
            if diff > 0.05:
                return "improving"
            elif diff < -0.05:
                return "declining"
            else:
                return "stable"
        except Exception:
            return "unknown"

    def get_service_info(self) -> dict[str, Any]:
        """獲取服務資訊"""
        return {
            "service_name": "PracticeRecordService",
            "version": "1.0.0",
            "description": "練習記錄管理服務",
            "capabilities": [
                "record_practice",
                "get_practice_history",
                "get_practice_statistics",
                "calculate_accuracy",
                "get_daily_statistics"
            ],
            "repository": self.practice_repo.__class__.__name__
        }

