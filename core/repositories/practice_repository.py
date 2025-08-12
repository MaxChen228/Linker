"""
練習記錄數據庫操作層

處理練習記錄的 CRUD 操作，包括：
- 時間範圍查詢
- 統計分析方法
- 資料清理功能
- 練習模式分析
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .base_repository import JSONRepository


class PracticeRepository(JSONRepository[List[Dict[str, Any]]]):
    """練習記錄數據庫"""
    
    @property
    def current_version(self) -> str:
        return "2.0"
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """驗證練習記錄數據格式"""
        if not isinstance(data, dict):
            return False
        
        # 檢查是否有 data 欄位
        if 'data' not in data:
            return False
        
        practice_records = data['data']
        if not isinstance(practice_records, list):
            return False
        
        # 驗證每條記錄的格式
        for record in practice_records:
            if not self._validate_practice_record(record):
                return False
        
        return True
    
    def _validate_practice_record(self, record: Dict[str, Any]) -> bool:
        """驗證單條練習記錄格式"""
        required_fields = [
            'timestamp', 'chinese_sentence', 'user_answer', 'is_correct'
        ]
        
        for field in required_fields:
            if field not in record:
                return False
        
        # 驗證時間格式
        try:
            datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False
        
        # 驗證布林值
        if not isinstance(record['is_correct'], bool):
            return False
        
        return True
    
    def migrate_data(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """數據版本遷移"""
        if from_version == "2.0":
            return data
        
        # 處理舊格式 (v1.0 及更早)
        if from_version in ["1.0"] or from_version is None:
            return self._migrate_from_legacy(data)
        
        return data
    
    def _migrate_from_legacy(self, data: Any) -> Dict[str, Any]:
        """從舊版本遷移到 v2.0"""
        # 如果數據是列表格式（v1.0）
        if isinstance(data, list):
            practice_records = data
        elif isinstance(data, dict) and 'data' in data:
            # 已經是新格式但缺少版本信息
            practice_records = data['data']
        else:
            practice_records = []
        
        # 遷移每條記錄
        migrated_records = []
        for record in practice_records:
            migrated_record = self._migrate_practice_record(record)
            if migrated_record:
                migrated_records.append(migrated_record)
        
        return {
            'version': '2.0',
            'migration_date': datetime.now().isoformat(),
            'data': migrated_records
        }
    
    def _migrate_practice_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """遷移單條練習記錄"""
        try:
            # 確保必要欄位存在
            migrated = {
                'timestamp': record.get('timestamp', datetime.now().isoformat()),
                'chinese_sentence': record.get('chinese_sentence', ''),
                'user_answer': record.get('user_answer', ''),
                'is_correct': record.get('is_correct', False),
                'feedback': record.get('feedback', {}),
                'practice_mode': record.get('practice_mode', 'new')  # 默認為新題模式
            }
            
            return migrated
            
        except Exception:
            # 忽略無法遷移的記錄
            return None
    
    def _detect_version(self, data: Any) -> str:
        """檢測數據版本"""
        # 如果是列表格式，是 v1.0
        if isinstance(data, list):
            return "1.0"
        
        # 如果有 data 欄位但沒有 version，可能是 v2.0 的不完整版本
        if isinstance(data, dict) and 'data' in data:
            return "1.9"  # 接近 v2.0 的版本
        
        return "1.0"
    
    def _get_default_data(self) -> Dict[str, Any]:
        """獲取默認數據結構"""
        return {
            'version': self.current_version,
            'created_at': datetime.now().isoformat(),
            'data': []
        }
    
    def add_practice_record(self, record: Dict[str, Any]) -> bool:
        """添加練習記錄"""
        if not self._validate_practice_record(record):
            return False
        
        data = self.load()
        
        # 確保時間戳存在
        if 'timestamp' not in record:
            record['timestamp'] = datetime.now().isoformat()
        
        data['data'].append(record)
        self.save(data)
        return True
    
    def get_records_by_date_range(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        根據時間範圍獲取練習記錄
        
        Args:
            start_date: 開始時間（包含）
            end_date: 結束時間（包含）
            
        Returns:
            符合條件的練習記錄列表
        """
        data = self.load()
        records = data['data']
        
        if not start_date and not end_date:
            return records
        
        filtered_records = []
        for record in records:
            try:
                record_time = datetime.fromisoformat(
                    record['timestamp'].replace('Z', '+00:00')
                )
                
                if start_date and record_time < start_date:
                    continue
                if end_date and record_time > end_date:
                    continue
                
                filtered_records.append(record)
                
            except (ValueError, KeyError):
                # 忽略時間格式錯誤的記錄
                continue
        
        return filtered_records
    
    def get_records_by_practice_mode(self, mode: str) -> List[Dict[str, Any]]:
        """根據練習模式獲取記錄"""
        data = self.load()
        
        return [
            record for record in data['data']
            if record.get('practice_mode') == mode
        ]
    
    def get_incorrect_records(self) -> List[Dict[str, Any]]:
        """獲取所有錯誤記錄"""
        data = self.load()
        
        return [
            record for record in data['data']
            if not record.get('is_correct', True)
        ]
    
    def get_recent_records(self, days: int = 7) -> List[Dict[str, Any]]:
        """獲取最近幾天的練習記錄"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return self.get_records_by_date_range(start_date, end_date)
    
    def get_statistics(self, days: Optional[int] = None) -> Dict[str, Any]:
        """
        獲取統計資料
        
        Args:
            days: 統計最近多少天的數據，None 表示全部數據
            
        Returns:
            統計資料字典
        """
        if days:
            records = self.get_recent_records(days)
        else:
            data = self.load()
            records = data['data']
        
        if not records:
            return {
                'total_practices': 0,
                'correct_count': 0,
                'incorrect_count': 0,
                'accuracy': 0.0,
                'practice_modes': {},
                'daily_stats': {},
                'error_categories': {}
            }
        
        # 基礎統計
        total_practices = len(records)
        correct_count = sum(1 for r in records if r.get('is_correct', False))
        incorrect_count = total_practices - correct_count
        accuracy = correct_count / total_practices if total_practices > 0 else 0.0
        
        # 練習模式統計
        practice_modes = {}
        for record in records:
            mode = record.get('practice_mode', 'unknown')
            practice_modes[mode] = practice_modes.get(mode, 0) + 1
        
        # 每日統計
        daily_stats = {}
        for record in records:
            try:
                date_str = record['timestamp'][:10]  # 取日期部分
                if date_str not in daily_stats:
                    daily_stats[date_str] = {'total': 0, 'correct': 0}
                
                daily_stats[date_str]['total'] += 1
                if record.get('is_correct', False):
                    daily_stats[date_str]['correct'] += 1
                    
            except (KeyError, IndexError):
                continue
        
        # 錯誤類別統計
        error_categories = {}
        for record in records:
            if not record.get('is_correct', True):
                feedback = record.get('feedback', {})
                errors = feedback.get('error_analysis', [])
                
                for error in errors:
                    category = error.get('category', 'unknown')
                    error_categories[category] = error_categories.get(category, 0) + 1
        
        return {
            'total_practices': total_practices,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'accuracy': accuracy,
            'practice_modes': practice_modes,
            'daily_stats': daily_stats,
            'error_categories': error_categories
        }
    
    def cleanup_old_records(self, days_to_keep: int = 365) -> int:
        """
        清理舊的練習記錄
        
        Args:
            days_to_keep: 保留最近多少天的記錄
            
        Returns:
            刪除的記錄數量
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        data = self.load()
        original_count = len(data['data'])
        
        # 保留較新的記錄
        kept_records = []
        for record in data['data']:
            try:
                record_time = datetime.fromisoformat(
                    record['timestamp'].replace('Z', '+00:00')
                )
                
                if record_time >= cutoff_date:
                    kept_records.append(record)
                    
            except (ValueError, KeyError):
                # 保留時間格式錯誤的記錄（以防萬一）
                kept_records.append(record)
        
        if len(kept_records) < original_count:
            data['data'] = kept_records
            self.save(data)
            return original_count - len(kept_records)
        
        return 0
    
    def get_performance_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        獲取表現趨勢
        
        Args:
            days: 分析最近多少天
            
        Returns:
            每日表現數據列表
        """
        records = self.get_recent_records(days)
        
        # 按日期分組
        daily_data = {}
        for record in records:
            try:
                date_str = record['timestamp'][:10]
                if date_str not in daily_data:
                    daily_data[date_str] = []
                daily_data[date_str].append(record)
            except (KeyError, IndexError):
                continue
        
        # 計算每日趨勢
        trend_data = []
        for date_str in sorted(daily_data.keys()):
            day_records = daily_data[date_str]
            correct_count = sum(1 for r in day_records if r.get('is_correct', False))
            total_count = len(day_records)
            accuracy = correct_count / total_count if total_count > 0 else 0.0
            
            trend_data.append({
                'date': date_str,
                'total_practices': total_count,
                'correct_count': correct_count,
                'accuracy': accuracy
            })
        
        return trend_data
    
    def search_records(
        self, 
        query: str, 
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜尋練習記錄
        
        Args:
            query: 搜尋關鍵字
            fields: 要搜尋的欄位列表
            
        Returns:
            匹配的記錄列表
        """
        if not query.strip():
            return []
        
        data = self.load()
        query = query.lower()
        
        if fields is None:
            fields = ['chinese_sentence', 'user_answer']
        
        results = []
        for record in data['data']:
            for field in fields:
                field_value = str(record.get(field, '')).lower()
                if query in field_value:
                    results.append(record)
                    break  # 避免重複添加同一條記錄
        
        return results
    
    def export_data(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format_type: str = 'json'
    ) -> Any:
        """
        匯出數據
        
        Args:
            start_date: 開始時間
            end_date: 結束時間
            format_type: 匯出格式 ('json' 或 'csv')
            
        Returns:
            匯出的數據
        """
        records = self.get_records_by_date_range(start_date, end_date)
        
        if format_type == 'json':
            return {
                'export_date': datetime.now().isoformat(),
                'record_count': len(records),
                'data': records
            }
        elif format_type == 'csv':
            # 簡化的 CSV 格式數據
            csv_data = []
            for record in records:
                csv_data.append({
                    'timestamp': record.get('timestamp', ''),
                    'chinese_sentence': record.get('chinese_sentence', ''),
                    'user_answer': record.get('user_answer', ''),
                    'is_correct': record.get('is_correct', False),
                    'practice_mode': record.get('practice_mode', '')
                })
            return csv_data
        else:
            raise ValueError(f"不支援的匯出格式: {format_type}")
    
    def batch_delete(self, record_ids: List[int]) -> int:
        """
        批量刪除記錄
        
        Args:
            record_ids: 要刪除的記錄索引列表
            
        Returns:
            成功刪除的數量
        """
        if not record_ids:
            return 0
        
        data = self.load()
        original_count = len(data['data'])
        
        # 按索引降序排序，從後往前刪除避免索引錯位
        sorted_ids = sorted(set(record_ids), reverse=True)
        
        deleted_count = 0
        for record_id in sorted_ids:
            if 0 <= record_id < len(data['data']):
                del data['data'][record_id]
                deleted_count += 1
        
        if deleted_count > 0:
            self.save(data)
        
        return deleted_count
    
    # === 新增的聚合操作方法 ===
    
    def get_aggregated_statistics(
        self, 
        group_by: str = 'date',
        date_range: Optional[Tuple[datetime, datetime]] = None,
        practice_modes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        獲取聚合統計數據
        
        Args:
            group_by: 分組方式 ('date', 'week', 'month', 'practice_mode', 'difficulty')
            date_range: 日期範圍 (start_date, end_date)
            practice_modes: 練習模式篩選
            
        Returns:
            聚合統計結果
        """
        # 獲取數據
        if date_range:
            records = self.get_records_by_date_range(date_range[0], date_range[1])
        else:
            data = self.load()
            records = data['data']
        
        # 篩選練習模式
        if practice_modes:
            records = [r for r in records if r.get('practice_mode') in practice_modes]
        
        # 根據分組方式進行聚合
        if group_by == 'date':
            return self._aggregate_by_date(records)
        elif group_by == 'week':
            return self._aggregate_by_week(records)
        elif group_by == 'month':
            return self._aggregate_by_month(records)
        elif group_by == 'practice_mode':
            return self._aggregate_by_practice_mode(records)
        elif group_by == 'difficulty':
            return self._aggregate_by_difficulty(records)
        else:
            raise ValueError(f"不支持的分組方式: {group_by}")
    
    def get_learning_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        獲取學習分析數據
        
        Args:
            days: 分析最近多少天的數據
            
        Returns:
            學習分析結果
        """
        with self._cache_lock:
            cache_key = f"learning_analytics_{days}"
            
            # 檢查緩存
            if (self._last_cache_update and 
                datetime.now() - self._last_cache_update < timedelta(minutes=10) and
                cache_key in self._stats_cache):
                return self._stats_cache[cache_key]
            
            # 計算分析數據
            records = self.get_recent_records(days)
            analytics = self._calculate_learning_analytics(records, days)
            
            # 更新緩存
            self._stats_cache[cache_key] = analytics
            self._last_cache_update = datetime.now()
            
            return analytics
    
    def archive_old_practices(
        self, 
        cutoff_date: datetime,
        archive_file_path: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        歸檔舊練習記錄
        
        Args:
            cutoff_date: 截止日期
            archive_file_path: 歸檔文件路徑
            
        Returns:
            歸檔的記錄數量和歸檔文件路徑
        """
        data = self.load()
        original_count = len(data['data'])
        
        cutoff_str = cutoff_date.isoformat()
        
        # 分離要歸檔和保留的記錄
        to_archive = []
        to_keep = []
        
        for record in data['data']:
            timestamp = record.get('timestamp', '')
            if timestamp and timestamp < cutoff_str:
                to_archive.append(record)
            else:
                to_keep.append(record)
        
        if not to_archive:
            return 0, ""
        
        # 創建歸檔文件
        if archive_file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file_path = f"{self.file_path.parent}/practice_archive_{timestamp}.json"
        
        archive_data = {
            'version': self.current_version,
            'archived_at': datetime.now().isoformat(),
            'cutoff_date': cutoff_str,
            'original_count': original_count,
            'data': to_archive
        }
        
        # 保存歸檔文件
        with open(archive_file_path, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=2)
        
        # 更新主文件
        data['data'] = to_keep
        self.save(data)
        self._clear_cache()
        
        return len(to_archive), archive_file_path
    
    # === 私有輔助方法 ===
    
    def _aggregate_by_date(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按日期聚合數據"""
        daily_data = defaultdict(lambda: {'total': 0, 'correct': 0, 'practice_modes': Counter()})
        
        for record in records:
            try:
                date_str = record['timestamp'][:10]
                daily_data[date_str]['total'] += 1
                if record.get('is_correct', False):
                    daily_data[date_str]['correct'] += 1
                
                mode = record.get('practice_mode', 'unknown')
                daily_data[date_str]['practice_modes'][mode] += 1
            except (KeyError, IndexError):
                continue
        
        # 計算每日準確率
        for date_str, data in daily_data.items():
            data['accuracy'] = data['correct'] / data['total'] if data['total'] > 0 else 0.0
            data['practice_modes'] = dict(data['practice_modes'])
        
        return {
            'aggregation_type': 'date',
            'total_days': len(daily_data),
            'data': dict(daily_data)
        }
    
    def _aggregate_by_week(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按週聚合數據"""
        weekly_data = defaultdict(lambda: {'total': 0, 'correct': 0, 'days_active': set()})
        
        for record in records:
            try:
                date_obj = datetime.fromisoformat(record['timestamp'][:10])
                week_start = date_obj - timedelta(days=date_obj.weekday())
                week_str = week_start.strftime('%Y-W%U')
                
                weekly_data[week_str]['total'] += 1
                if record.get('is_correct', False):
                    weekly_data[week_str]['correct'] += 1
                weekly_data[week_str]['days_active'].add(record['timestamp'][:10])
            except (KeyError, ValueError):
                continue
        
        # 轉換 set 為 count
        for week_str, data in weekly_data.items():
            data['accuracy'] = data['correct'] / data['total'] if data['total'] > 0 else 0.0
            data['days_active'] = len(data['days_active'])
        
        return {
            'aggregation_type': 'week',
            'total_weeks': len(weekly_data),
            'data': dict(weekly_data)
        }
    
    def _aggregate_by_month(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按月聚合數據"""
        monthly_data = defaultdict(lambda: {'total': 0, 'correct': 0, 'days_active': set()})
        
        for record in records:
            try:
                month_str = record['timestamp'][:7]  # YYYY-MM
                monthly_data[month_str]['total'] += 1
                if record.get('is_correct', False):
                    monthly_data[month_str]['correct'] += 1
                monthly_data[month_str]['days_active'].add(record['timestamp'][:10])
            except (KeyError, IndexError):
                continue
        
        # 轉換 set 為 count
        for month_str, data in monthly_data.items():
            data['accuracy'] = data['correct'] / data['total'] if data['total'] > 0 else 0.0
            data['days_active'] = len(data['days_active'])
        
        return {
            'aggregation_type': 'month',
            'total_months': len(monthly_data),
            'data': dict(monthly_data)
        }
    
    def _aggregate_by_practice_mode(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按練習模式聚合數據"""
        mode_data = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for record in records:
            mode = record.get('practice_mode', 'unknown')
            mode_data[mode]['total'] += 1
            if record.get('is_correct', False):
                mode_data[mode]['correct'] += 1
        
        for mode, data in mode_data.items():
            data['accuracy'] = data['correct'] / data['total'] if data['total'] > 0 else 0.0
        
        return {
            'aggregation_type': 'practice_mode',
            'total_modes': len(mode_data),
            'data': dict(mode_data)
        }
    
    def _aggregate_by_difficulty(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """按難度聚合數據"""
        difficulty_data = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for record in records:
            difficulty = record.get('difficulty_level', 1)
            difficulty_data[f"level_{difficulty}"]['total'] += 1
            if record.get('is_correct', False):
                difficulty_data[f"level_{difficulty}"]['correct'] += 1
        
        for level, data in difficulty_data.items():
            data['accuracy'] = data['correct'] / data['total'] if data['total'] > 0 else 0.0
        
        return {
            'aggregation_type': 'difficulty',
            'total_levels': len(difficulty_data),
            'data': dict(difficulty_data)
        }
    
    def _calculate_learning_analytics(self, records: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
        """計算學習分析數據"""
        if not records:
            return self._empty_analytics()
        
        # 基礎指標
        total_practices = len(records)
        correct_count = sum(1 for r in records if r.get('is_correct', False))
        accuracy = correct_count / total_practices
        
        # 時間分析
        practice_times = [r['timestamp'] for r in records if 'timestamp' in r]
        time_analysis = self._analyze_practice_times(practice_times)
        
        # 進步分析
        progress_analysis = self._analyze_progress(records)
        
        # 困難點分析
        difficulty_analysis = self._analyze_difficulties(records)
        
        # 學習效率分析
        efficiency_analysis = self._calculate_learning_efficiency(records, days)
        
        return {
            'period_days': days,
            'basic_metrics': {
                'total_practices': total_practices,
                'accuracy': accuracy,
                'daily_average': total_practices / days if days > 0 else 0
            },
            'time_analysis': time_analysis,
            'progress_analysis': progress_analysis,
            'difficulty_analysis': difficulty_analysis,
            'efficiency_analysis': efficiency_analysis
        }
    
    def _empty_analytics(self) -> Dict[str, Any]:
        """返回空的分析數據結構"""
        return {
            'period_days': 0,
            'basic_metrics': {
                'total_practices': 0,
                'accuracy': 0.0,
                'daily_average': 0.0
            },
            'time_analysis': {},
            'progress_analysis': {},
            'difficulty_analysis': {},
            'efficiency_analysis': {}
        }
    
    def _analyze_practice_times(self, timestamps: List[str]) -> Dict[str, Any]:
        """分析練習時間模式"""
        if not timestamps:
            return {}
        
        hour_distribution = defaultdict(int)
        day_distribution = defaultdict(int)
        
        for ts in timestamps:
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                hour_distribution[dt.hour] += 1
                day_distribution[dt.strftime('%A')] += 1
            except ValueError:
                continue
        
        return {
            'most_active_hour': max(hour_distribution, key=hour_distribution.get) if hour_distribution else None,
            'most_active_day': max(day_distribution, key=day_distribution.get) if day_distribution else None,
            'hour_distribution': dict(hour_distribution),
            'day_distribution': dict(day_distribution)
        }
    
    def _analyze_progress(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析學習進步情況"""
        if len(records) < 10:  # 數據太少，無法分析趨勢
            return {'insufficient_data': True}
        
        # 按時間排序
        sorted_records = sorted(records, key=lambda r: r.get('timestamp', ''))
        
        # 分成前後兩半進行對比
        mid_point = len(sorted_records) // 2
        early_records = sorted_records[:mid_point]
        recent_records = sorted_records[mid_point:]
        
        early_accuracy = sum(1 for r in early_records if r.get('is_correct', False)) / len(early_records)
        recent_accuracy = sum(1 for r in recent_records if r.get('is_correct', False)) / len(recent_records)
        
        improvement = recent_accuracy - early_accuracy
        
        return {
            'early_period_accuracy': early_accuracy,
            'recent_period_accuracy': recent_accuracy,
            'improvement': improvement,
            'trend': 'improving' if improvement > 0.05 else 'declining' if improvement < -0.05 else 'stable'
        }
    
    def _analyze_difficulties(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析困難點"""
        error_types = defaultdict(int)
        difficult_sentences = []
        
        for record in records:
            if not record.get('is_correct', True):
                # 分析錯誤類型
                feedback = record.get('feedback', {})
                error_analysis = feedback.get('error_analysis', [])
                
                for error in error_analysis:
                    error_type = error.get('category', 'unknown')
                    error_types[error_type] += 1
                
                # 記錄困難句子
                sentence = record.get('chinese_sentence', '')
                if sentence and len(sentence) > 20:  # 較長的句子可能更困難
                    difficult_sentences.append({
                        'sentence': sentence,
                        'user_answer': record.get('user_answer', ''),
                        'timestamp': record.get('timestamp', '')
                    })
        
        return {
            'common_error_types': dict(error_types),
            'most_common_error': max(error_types, key=error_types.get) if error_types else None,
            'difficult_sentences_count': len(difficult_sentences),
            'sample_difficult_sentences': difficult_sentences[:5]  # 只返回前5個樣本
        }
    
    def _calculate_learning_efficiency(self, records: List[Dict[str, Any]], days: int) -> Dict[str, Any]:
        """計算學習效率"""
        if not records or days <= 0:
            return {}
        
        total_practices = len(records)
        correct_count = sum(1 for r in records if r.get('is_correct', False))
        
        # 每日練習效率
        daily_efficiency = (correct_count / days) if days > 0 else 0
        
        # 練習密度
        practice_density = total_practices / days
        
        # 學習一致性（連續練習天數）
        practice_dates = set()
        for record in records:
            try:
                date_str = record['timestamp'][:10]
                practice_dates.add(date_str)
            except (KeyError, IndexError):
                continue
        
        consistency = len(practice_dates) / days if days > 0 else 0
        
        return {
            'daily_efficiency': daily_efficiency,
            'practice_density': practice_density,
            'consistency_ratio': consistency,
            'active_days': len(practice_dates),
            'efficiency_score': (daily_efficiency * 0.4 + practice_density * 0.3 + consistency * 0.3)
        }
    
    def _clear_cache(self):
        """清除緩存"""
        with self._cache_lock:
            self._stats_cache.clear()
            self._last_cache_update = None