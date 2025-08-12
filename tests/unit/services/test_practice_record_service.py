"""
PracticeRecordService 測試套件

測試練習記錄服務的所有核心功能，包括記錄管理、統計分析、歷史查詢等
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from services.practice_record_service import PracticeRecordService
from services.base_service import ServiceResult
from core.repositories.practice_repository import PracticeRepository


# Global fixtures for PracticeRecordService tests
@pytest.fixture
def mock_practice_repository():
    """Mock PracticeRepository"""
    repo = Mock(spec=PracticeRepository)
    
    # 預設返回值
    repo.add_practice_record.return_value = True
    repo.load.return_value = {
        'data': [
            {
                'timestamp': '2024-01-15T10:00:00',
                'chinese_sentence': '我去學校',
                'user_answer': 'I go to school',
                'is_correct': True,
                'practice_mode': 'new',
                'difficulty_level': 1
            },
            {
                'timestamp': '2024-01-15T11:00:00',
                'chinese_sentence': '他昨天來了',
                'user_answer': 'He come yesterday',
                'is_correct': False,
                'practice_mode': 'new',
                'difficulty_level': 2
            }
        ]
    }
    repo.get_statistics.return_value = {
        'total_practices': 100,
        'correct_count': 80,
        'accuracy': 0.8,
        'avg_difficulty': 1.5
    }
    repo.get_recent_records.return_value = []
    repo.get_records_by_practice_mode.return_value = []
    repo.get_records_by_date_range.return_value = []
    repo.get_performance_trend.return_value = []
    
    return repo

@pytest.fixture
def practice_record_service(mock_practice_repository):
    """創建 PracticeRecordService 實例"""
    return PracticeRecordService(practice_repo=mock_practice_repository)

@pytest.fixture
def sample_practice_record():
    """樣本練習記錄"""
    return {
        'timestamp': datetime.now().isoformat(),
        'chinese_sentence': '我昨天去了學校',
        'user_answer': 'I went to school yesterday',
        'is_correct': True,
        'feedback': {
            'is_generally_correct': True,
            'overall_suggestion': 'Perfect!'
        },
        'practice_mode': 'new',
        'difficulty_level': 2,
        'knowledge_point_ids': [1, 2]
    }

@pytest.fixture
def sample_records_data():
    """樣本記錄數據集"""
    base_time = datetime.now()
    return [
        {
            'timestamp': (base_time - timedelta(days=i)).isoformat(),
            'chinese_sentence': f'測試句子{i}',
            'user_answer': f'Test sentence {i}',
            'is_correct': i % 2 == 0,  # 交替正確/錯誤
            'practice_mode': 'new' if i < 5 else 'review',
            'difficulty_level': (i % 3) + 1
        }
        for i in range(10)
    ]


class TestPracticeRecordService:
    """PracticeRecordService 測試類別"""


class TestRecordPractice:
    """測試記錄練習功能"""

    def test_record_practice_success(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試成功記錄練習"""
        result = practice_record_service.record_practice(
            chinese_sentence="我去學校",
            user_answer="I go to school",
            is_correct=True,
            feedback={"score": 10},
            practice_mode="new",
            difficulty_level=1,
            knowledge_point_ids=[1, 2]
        )
        
        assert result.success is True
        assert result.message == "練習記錄已保存"
        assert result.data["chinese_sentence"] == "我去學校"
        assert result.data["is_correct"] is True
        
        # 驗證repository被調用
        mock_practice_repository.add_practice_record.assert_called_once()

    def test_record_practice_with_minimal_data(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試使用最小數據記錄練習"""
        result = practice_record_service.record_practice(
            chinese_sentence="簡單句子",
            user_answer="Simple sentence",
            is_correct=False,
            feedback={}
        )
        
        assert result.success is True
        assert result.data["practice_mode"] == "new"  # 預設值
        assert result.data["difficulty_level"] == 1   # 預設值
        assert result.data["knowledge_point_ids"] == []  # 預設值

    def test_record_practice_repository_failure(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試repository保存失敗"""
        mock_practice_repository.add_practice_record.return_value = False
        
        result = practice_record_service.record_practice(
            chinese_sentence="測試",
            user_answer="Test",
            is_correct=True,
            feedback={}
        )
        
        assert result.success is False
        assert "保存練習記錄失敗" in result.message

    def test_record_practice_exception_handling(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試異常處理"""
        mock_practice_repository.add_practice_record.side_effect = Exception("Database error")
        
        result = practice_record_service.record_practice(
            chinese_sentence="測試",
            user_answer="Test",
            is_correct=True,
            feedback={}
        )
        
        assert result.success is False
        assert "記錄練習失敗" in result.message
        assert "Database error" in result.message

    def test_record_practice_data_structure(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試記錄數據結構正確性"""
        practice_record_service.record_practice(
            chinese_sentence="完整測試",
            user_answer="Complete test",
            is_correct=True,
            feedback={"detailed": "feedback"},
            practice_mode="review",
            difficulty_level=3,
            knowledge_point_ids=[5, 6, 7]
        )
        
        # 獲取傳給repository的參數
        call_args = mock_practice_repository.add_practice_record.call_args[0][0]
        
        assert "timestamp" in call_args
        assert call_args["chinese_sentence"] == "完整測試"
        assert call_args["user_answer"] == "Complete test"
        assert call_args["is_correct"] is True
        assert call_args["feedback"] == {"detailed": "feedback"}
        assert call_args["practice_mode"] == "review"
        assert call_args["difficulty_level"] == 3
        assert call_args["knowledge_point_ids"] == [5, 6, 7]


class TestGetPracticeHistory:
    """測試獲取練習歷史"""

    def test_get_practice_history_all_records(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試獲取所有記錄"""
        result = practice_record_service.get_practice_history()
        
        assert result.success is True
        assert len(result.data) == 2
        assert "獲取到 2 條練習記錄" in result.message
        
        # 驗證記錄按時間降序排列
        timestamps = [record['timestamp'] for record in result.data]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_practice_history_with_limit(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試限制返回數量"""
        result = practice_record_service.get_practice_history(limit=1)
        
        assert result.success is True
        assert len(result.data) == 1
        assert "獲取到 1 條練習記錄" in result.message

    def test_get_practice_history_by_mode(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試按練習模式篩選"""
        filtered_records = [
            {
                'timestamp': '2024-01-15T10:00:00',
                'practice_mode': 'review',
                'is_correct': True
            }
        ]
        mock_practice_repository.get_records_by_practice_mode.return_value = filtered_records
        
        result = practice_record_service.get_practice_history(practice_mode="review")
        
        assert result.success is True
        mock_practice_repository.get_records_by_practice_mode.assert_called_once_with("review")

    def test_get_practice_history_exception(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試獲取歷史異常處理"""
        mock_practice_repository.load.side_effect = Exception("Load error")
        
        result = practice_record_service.get_practice_history()
        
        assert result.success is False
        assert "獲取練習歷史失敗" in result.message


class TestGetPracticeStatistics:
    """測試獲取練習統計"""

    def test_get_practice_statistics_success(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試成功獲取統計"""
        # 設置額外的統計計算Mock
        with patch.object(practice_record_service, '_calculate_streak_days', return_value=7), \
             patch.object(practice_record_service, '_calculate_average_daily_practices', return_value=5.2), \
             patch.object(practice_record_service, '_calculate_improvement_trend', return_value="improving"):
            
            result = practice_record_service.get_practice_statistics()
            
            assert result.success is True
            assert result.data['total_practices'] == 100
            assert result.data['accuracy'] == 0.8
            assert result.data['streak_days'] == 7
            assert result.data['average_daily_practices'] == 5.2
            assert result.data['improvement_trend'] == "improving"

    def test_get_practice_statistics_with_days_filter(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試按天數篩選統計"""
        with patch.object(practice_record_service, '_calculate_streak_days', return_value=3), \
             patch.object(practice_record_service, '_calculate_average_daily_practices', return_value=2.1), \
             patch.object(practice_record_service, '_calculate_improvement_trend', return_value="stable"):
            
            result = practice_record_service.get_practice_statistics(days=7)
            
            assert result.success is True
            mock_practice_repository.get_statistics.assert_called_once_with(7)

    def test_get_practice_statistics_exception(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試統計獲取異常"""
        mock_practice_repository.get_statistics.side_effect = Exception("Stats error")
        
        result = practice_record_service.get_practice_statistics()
        
        assert result.success is False
        assert "獲取統計失敗" in result.message


class TestGetRecentPractices:
    """測試獲取最近練習"""

    def test_get_recent_practices_default_days(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試預設天數獲取最近練習"""
        recent_records = [
            {'timestamp': '2024-01-15T10:00:00', 'is_correct': True}
        ]
        mock_practice_repository.get_recent_records.return_value = recent_records
        
        result = practice_record_service.get_recent_practices()
        
        assert result.success is True
        assert result.data == recent_records
        assert "獲取最近 7 天的練習記錄" in result.message
        mock_practice_repository.get_recent_records.assert_called_once_with(7)

    def test_get_recent_practices_custom_days(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試自定義天數"""
        result = practice_record_service.get_recent_practices(days=30)
        
        assert result.success is True
        assert "獲取最近 30 天的練習記錄" in result.message
        mock_practice_repository.get_recent_records.assert_called_once_with(30)

    def test_get_recent_practices_exception(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試異常處理"""
        mock_practice_repository.get_recent_records.side_effect = Exception("Recent error")
        
        result = practice_record_service.get_recent_practices()
        
        assert result.success is False
        assert "獲取最近練習失敗" in result.message


class TestGetPracticeByDateRange:
    """測試按日期範圍獲取練習"""

    def test_get_practice_by_date_range_success(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試成功按日期範圍獲取"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        range_records = [
            {'timestamp': '2024-01-15T10:00:00', 'is_correct': True}
        ]
        mock_practice_repository.get_records_by_date_range.return_value = range_records
        
        result = practice_record_service.get_practice_by_date_range(start_date, end_date)
        
        assert result.success is True
        assert result.data == range_records
        assert "2024-01-01 到 2024-01-31" in result.message
        mock_practice_repository.get_records_by_date_range.assert_called_once_with(start_date, end_date)

    def test_get_practice_by_date_range_exception(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試日期範圍查詢異常"""
        mock_practice_repository.get_records_by_date_range.side_effect = Exception("Range error")
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = practice_record_service.get_practice_by_date_range(start_date, end_date)
        
        assert result.success is False
        assert "按日期範圍獲取練習失敗" in result.message


class TestCalculateAccuracy:
    """測試準確率計算"""

    def test_calculate_accuracy_all_records(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試計算所有記錄的準確率"""
        result = practice_record_service.calculate_accuracy()
        
        assert result.success is True
        # 根據mock數據：2條記錄，1條正確 = 50%
        assert result.data == 0.5
        assert "準確率: 50.00%" in result.message

    def test_calculate_accuracy_with_days_filter(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試按天數篩選計算準確率"""
        recent_records = [
            {'is_correct': True},
            {'is_correct': True},
            {'is_correct': False}
        ]
        mock_practice_repository.get_recent_records.return_value = recent_records
        
        result = practice_record_service.calculate_accuracy(days=7)
        
        assert result.success is True
        # 3條記錄，2條正確 = 66.67%
        expected_accuracy = 2 / 3
        assert abs(result.data - expected_accuracy) < 0.001

    def test_calculate_accuracy_with_practice_mode_filter(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試按練習模式篩選準確率"""
        all_records = [
            {'is_correct': True, 'practice_mode': 'new'},
            {'is_correct': False, 'practice_mode': 'new'},
            {'is_correct': True, 'practice_mode': 'review'},
            {'is_correct': True, 'practice_mode': 'review'}
        ]
        mock_practice_repository.load.return_value = {'data': all_records}
        
        result = practice_record_service.calculate_accuracy(practice_mode="review")
        
        assert result.success is True
        # review模式：2條記錄，2條正確 = 100%
        assert result.data == 1.0

    def test_calculate_accuracy_no_records(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試沒有記錄時的準確率計算"""
        mock_practice_repository.load.return_value = {'data': []}
        
        result = practice_record_service.calculate_accuracy()
        
        assert result.success is True
        assert result.data == 0.0
        assert "無練習記錄" in result.message

    def test_calculate_accuracy_exception(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試準確率計算異常"""
        mock_practice_repository.load.side_effect = Exception("Accuracy error")
        
        result = practice_record_service.calculate_accuracy()
        
        assert result.success is False
        assert "計算準確率失敗" in result.message


class TestGetDailyStatistics:
    """測試獲取每日統計"""

    def test_get_daily_statistics_success(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試成功獲取每日統計"""
        trend_data = [
            {'date': '2024-01-15', 'practices': 5, 'accuracy': 0.8},
            {'date': '2024-01-16', 'practices': 3, 'accuracy': 0.67}
        ]
        mock_practice_repository.get_performance_trend.return_value = trend_data
        
        result = practice_record_service.get_daily_statistics(days=30)
        
        assert result.success is True
        assert result.data == trend_data
        assert "獲取最近 30 天的每日統計" in result.message
        mock_practice_repository.get_performance_trend.assert_called_once_with(30)

    def test_get_daily_statistics_default_days(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試預設天數"""
        result = practice_record_service.get_daily_statistics()
        
        assert result.success is True
        mock_practice_repository.get_performance_trend.assert_called_once_with(30)

    def test_get_daily_statistics_exception(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試每日統計異常"""
        mock_practice_repository.get_performance_trend.side_effect = Exception("Trend error")
        
        result = practice_record_service.get_daily_statistics()
        
        assert result.success is False
        assert "獲取每日統計失敗" in result.message


class TestPrivateMethods:
    """測試私有方法"""

    def test_calculate_streak_days_no_records(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試沒有記錄時的連續天數計算"""
        mock_practice_repository.get_recent_records.return_value = []
        
        streak = practice_record_service._calculate_streak_days()
        
        assert streak == 0

    def test_calculate_streak_days_with_records(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試有記錄時的連續天數計算"""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)
        
        records = [
            {'timestamp': today.isoformat() + 'T10:00:00'},
            {'timestamp': today.isoformat() + 'T11:00:00'},  # 今天兩次
            {'timestamp': yesterday.isoformat() + 'T10:00:00'},  # 昨天一次
            # 前天沒有記錄，所以連續2天
        ]
        mock_practice_repository.get_recent_records.return_value = records
        
        streak = practice_record_service._calculate_streak_days()
        
        assert streak == 2

    def test_calculate_average_daily_practices_with_days(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試指定天數的平均每日練習次數"""
        records = [{'timestamp': '2024-01-15T10:00:00'}] * 10  # 10條記錄
        mock_practice_repository.get_recent_records.return_value = records
        
        avg = practice_record_service._calculate_average_daily_practices(days=5)
        
        assert avg == 2.0  # 10條記錄 / 5天 = 2.0

    def test_calculate_average_daily_practices_all_records(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試所有記錄的平均每日練習次數"""
        # 設置第一條記錄的時間為3天前
        first_record_time = (datetime.now() - timedelta(days=2)).isoformat()
        records = [
            {'timestamp': first_record_time},
            {'timestamp': datetime.now().isoformat()},
            {'timestamp': datetime.now().isoformat()}
        ]
        mock_practice_repository.load.return_value = {'data': records}
        
        avg = practice_record_service._calculate_average_daily_practices()
        
        # 3條記錄，3天期間 = 1.0
        assert avg == 1.0

    def test_calculate_improvement_trend_improving(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試改善趨勢 - 正在改善"""
        trend_data = [
            {'accuracy': 0.5},  # 前期準確率低
            {'accuracy': 0.6},
            {'accuracy': 0.8},  # 後期準確率高
            {'accuracy': 0.9}
        ]
        mock_practice_repository.get_performance_trend.return_value = trend_data
        
        trend = practice_record_service._calculate_improvement_trend(days=4)
        
        assert trend == "improving"

    def test_calculate_improvement_trend_declining(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試改善趨勢 - 正在下降"""
        trend_data = [
            {'accuracy': 0.9},  # 前期準確率高
            {'accuracy': 0.8},
            {'accuracy': 0.5},  # 後期準確率低
            {'accuracy': 0.4}
        ]
        mock_practice_repository.get_performance_trend.return_value = trend_data
        
        trend = practice_record_service._calculate_improvement_trend(days=4)
        
        assert trend == "declining"

    def test_calculate_improvement_trend_stable(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試改善趨勢 - 穩定"""
        trend_data = [
            {'accuracy': 0.7},
            {'accuracy': 0.72},
            {'accuracy': 0.68},
            {'accuracy': 0.71}
        ]
        mock_practice_repository.get_performance_trend.return_value = trend_data
        
        trend = practice_record_service._calculate_improvement_trend(days=4)
        
        assert trend == "stable"

    def test_calculate_improvement_trend_insufficient_data(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試數據不足時的趨勢計算"""
        trend_data = [
            {'accuracy': 0.7}
        ]
        mock_practice_repository.get_performance_trend.return_value = trend_data
        
        trend = practice_record_service._calculate_improvement_trend(days=1)
        
        assert trend == "insufficient_data"

    def test_calculate_improvement_trend_exception(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試趨勢計算異常"""
        mock_practice_repository.get_performance_trend.side_effect = Exception("Trend error")
        
        trend = practice_record_service._calculate_improvement_trend()
        
        assert trend == "unknown"


class TestServiceInfo:
    """測試服務資訊"""

    def test_get_service_info(self, practice_record_service):
        """測試獲取服務資訊"""
        info = practice_record_service.get_service_info()
        
        assert info["service_name"] == "PracticeRecordService"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        assert "repository" in info
        
        # 驗證能力列表
        capabilities = info["capabilities"]
        assert "record_practice" in capabilities
        assert "get_practice_history" in capabilities
        assert "get_practice_statistics" in capabilities
        assert "calculate_accuracy" in capabilities
        assert "get_daily_statistics" in capabilities


class TestEdgeCases:
    """測試邊界情況"""

    def test_empty_feedback_handling(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試空回饋處理"""
        result = practice_record_service.record_practice(
            chinese_sentence="測試",
            user_answer="Test",
            is_correct=True,
            feedback={}
        )
        
        assert result.success is True
        assert result.data["feedback"] == {}

    def test_very_long_sentences(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試很長的句子"""
        long_sentence = "這是一個非常非常長的句子，" * 100
        long_answer = "This is a very very long sentence, " * 100
        
        result = practice_record_service.record_practice(
            chinese_sentence=long_sentence,
            user_answer=long_answer,
            is_correct=True,
            feedback={"note": "長句測試"}
        )
        
        assert result.success is True
        assert len(result.data["chinese_sentence"]) > 1000

    def test_unicode_characters_handling(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試Unicode字符處理"""
        result = practice_record_service.record_practice(
            chinese_sentence="我喜歡🍎和🌟",
            user_answer="I like 🍎 and ⭐",
            is_correct=True,
            feedback={"emoji": "✅"}
        )
        
        assert result.success is True
        assert "🍎" in result.data["chinese_sentence"]

    def test_negative_difficulty_level(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試負數難度等級"""
        result = practice_record_service.record_practice(
            chinese_sentence="測試",
            user_answer="Test",
            is_correct=True,
            feedback={},
            difficulty_level=-1
        )
        
        assert result.success is True
        assert result.data["difficulty_level"] == -1  # 應該保持原值

    def test_zero_days_statistics(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試零天數統計"""
        result = practice_record_service.get_recent_practices(days=0)
        
        assert result.success is True
        mock_practice_repository.get_recent_records.assert_called_once_with(0)


@pytest.mark.integration
class TestPracticeRecordServiceIntegration:
    """整合測試"""

    def test_complete_practice_workflow(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試完整的練習記錄工作流程"""
        # 1. 記錄練習
        record_result = practice_record_service.record_practice(
            chinese_sentence="我昨天去了學校",
            user_answer="I went to school yesterday",
            is_correct=True,
            feedback={"score": 95}
        )
        assert record_result.success is True
        
        # 2. 獲取歷史
        history_result = practice_record_service.get_practice_history(limit=10)
        assert history_result.success is True
        
        # 3. 計算準確率
        accuracy_result = practice_record_service.calculate_accuracy()
        assert accuracy_result.success is True
        
        # 4. 獲取統計
        with patch.object(practice_record_service, '_calculate_streak_days', return_value=5):
            stats_result = practice_record_service.get_practice_statistics()
            assert stats_result.success is True

    def test_batch_practice_recording(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試批量練習記錄"""
        practice_sessions = [
            ("句子1", "Sentence 1", True),
            ("句子2", "Sentence 2", False),
            ("句子3", "Sentence 3", True),
            ("句子4", "Sentence 4", True),
            ("句子5", "Sentence 5", False)
        ]
        
        results = []
        for chinese, english, is_correct in practice_sessions:
            result = practice_record_service.record_practice(
                chinese_sentence=chinese,
                user_answer=english,
                is_correct=is_correct,
                feedback={"batch": True}
            )
            results.append(result)
        
        # 驗證所有記錄都成功
        assert all(r.success for r in results)
        assert len(results) == 5
        
        # 驗證repository被調用了5次
        assert mock_practice_repository.add_practice_record.call_count == 5

    def test_performance_analysis_workflow(
        self,
        practice_record_service,
        mock_practice_repository
    ):
        """測試性能分析工作流程"""
        # 設置趨勢數據
        trend_data = [
            {'date': '2024-01-10', 'practices': 3, 'accuracy': 0.67},
            {'date': '2024-01-11', 'practices': 5, 'accuracy': 0.80},
            {'date': '2024-01-12', 'practices': 4, 'accuracy': 0.75},
            {'date': '2024-01-13', 'practices': 6, 'accuracy': 0.83}
        ]
        mock_practice_repository.get_performance_trend.return_value = trend_data
        
        # 設置計算方法的返回值
        with patch.object(practice_record_service, '_calculate_streak_days', return_value=4), \
             patch.object(practice_record_service, '_calculate_average_daily_practices', return_value=4.5), \
             patch.object(practice_record_service, '_calculate_improvement_trend', return_value="improving"):
            
            # 1. 獲取每日統計
            daily_result = practice_record_service.get_daily_statistics(days=7)
            assert daily_result.success is True
            assert len(daily_result.data) == 4
            
            # 2. 獲取整體統計
            stats_result = practice_record_service.get_practice_statistics(days=7)
            assert stats_result.success is True
            assert stats_result.data["streak_days"] == 4
            assert stats_result.data["improvement_trend"] == "improving"
            
            # 3. 計算準確率
            accuracy_result = practice_record_service.calculate_accuracy(days=7)
            assert accuracy_result.success is True