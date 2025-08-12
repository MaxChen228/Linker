"""
複合資料庫操作層

提供跨實體的資料庫操作，協調知識點和練習記錄之間的關聯性操作
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict
import json
import threading

from .knowledge_repository import KnowledgeRepository
from .practice_repository import PracticeRepository
from ..constants import LearningConstants, DisplayConstants


class CompositeRepository:
    """
    複合資料庫操作層
    
    提供跨實體的複雜查詢和操作，包括：
    - 知識點與練習記錄的關聯分析
    - 跨實體統計和報告
    - 學習進度追蹤
    - 數據一致性維護
    """
    
    def __init__(
        self, 
        knowledge_repo: KnowledgeRepository,
        practice_repo: PracticeRepository
    ):
        """
        初始化複合資料庫
        
        Args:
            knowledge_repo: 知識點資料庫
            practice_repo: 練習記錄資料庫
        """
        self.knowledge_repo = knowledge_repo
        self.practice_repo = practice_repo
        
        # 操作鎖，確保跨倉庫操作的原子性
        self._operation_lock = threading.RLock()
        
        # 緩存
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._last_cache_update = None
    
    def get_comprehensive_learning_report(
        self, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        獲取綜合學習報告
        
        Args:
            days: 報告時間範圍（天數）
            
        Returns:
            包含知識點和練習記錄綜合分析的報告
        """
        with self._operation_lock:
            # 獲取基礎數據
            knowledge_stats = self.knowledge_repo.get_advanced_statistics()
            practice_analytics = self.practice_repo.get_learning_analytics(days)
            
            # 獲取關聯分析
            correlation_analysis = self._analyze_knowledge_practice_correlation(days)
            
            # 學習進度評估
            progress_assessment = self._assess_learning_progress(days)
            
            # 個性化建議
            recommendations = self._generate_learning_recommendations(knowledge_stats, practice_analytics)
            
            return {
                'report_date': datetime.now().isoformat(),
                'period_days': days,
                'knowledge_summary': knowledge_stats,
                'practice_summary': practice_analytics,
                'correlation_analysis': correlation_analysis,
                'progress_assessment': progress_assessment,
                'recommendations': recommendations,
                'next_actions': self._suggest_next_actions(knowledge_stats, practice_analytics)
            }
    
    def find_knowledge_practice_pairs(
        self, 
        knowledge_point_ids: Optional[List[int]] = None,
        practice_modes: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[Dict[str, Any]]:
        """
        查找知識點與練習記錄的配對
        
        Args:
            knowledge_point_ids: 指定的知識點ID列表
            practice_modes: 練習模式篩選
            date_range: 日期範圍
            
        Returns:
            知識點與相關練習記錄的配對列表
        """
        with self._operation_lock:
            # 獲取知識點數據
            knowledge_data = self.knowledge_repo.load()
            knowledge_points = knowledge_data['data']
            
            if knowledge_point_ids:
                knowledge_points = [
                    kp for kp in knowledge_points 
                    if kp.get('id') in knowledge_point_ids
                ]
            
            # 獲取練習記錄
            if date_range:
                practice_records = self.practice_repo.get_records_by_date_range(
                    date_range[0], date_range[1]
                )
            else:
                practice_data = self.practice_repo.load()
                practice_records = practice_data['data']
            
            if practice_modes:
                practice_records = [
                    pr for pr in practice_records 
                    if pr.get('practice_mode') in practice_modes
                ]
            
            # 建立配對關係
            pairs = []
            for knowledge_point in knowledge_points:
                kp_id = knowledge_point.get('id')
                
                # 查找相關的練習記錄
                related_practices = []
                for practice in practice_records:
                    # 檢查練習記錄是否與知識點相關
                    if self._is_practice_related_to_knowledge_point(practice, knowledge_point):
                        related_practices.append(practice)
                
                if related_practices or not date_range:  # 如果沒有日期限制，包含所有知識點
                    pairs.append({
                        'knowledge_point': knowledge_point,
                        'related_practices': related_practices,
                        'practice_count': len(related_practices),
                        'accuracy_in_practices': self._calculate_accuracy_for_practices(related_practices)
                    })
            
            return pairs
    
    def get_learning_efficiency_metrics(
        self, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        獲取學習效率指標
        
        Args:
            days: 分析時間範圍
            
        Returns:
            學習效率相關的各種指標
        """
        with self._cache_lock:
            cache_key = f"efficiency_metrics_{days}"
            
            # 檢查緩存
            if (self._last_cache_update and 
                datetime.now() - self._last_cache_update < timedelta(minutes=15) and
                cache_key in self._cache):
                return self._cache[cache_key]
            
            # 計算效率指標
            metrics = self._calculate_efficiency_metrics(days)
            
            # 更新緩存
            self._cache[cache_key] = metrics
            self._last_cache_update = datetime.now()
            
            return metrics
    
    def batch_save_practice_session(
        self, 
        practice_records: List[Dict[str, Any]],
        knowledge_updates: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[int, int, List[str]]:
        """
        批量保存練習會話數據
        
        Args:
            practice_records: 練習記錄列表
            knowledge_updates: 知識點更新列表
            
        Returns:
            (保存的練習記錄數, 更新的知識點數, 錯誤信息列表)
        """
        with self._operation_lock:
            errors = []
            practice_saved = 0
            knowledge_updated = 0
            
            try:
                # 批量保存練習記錄
                for record in practice_records:
                    if self.practice_repo.add_practice_record(record):
                        practice_saved += 1
                    else:
                        errors.append(f"保存練習記錄失敗: {record.get('timestamp', 'unknown')}")
                
                # 批量更新知識點
                if knowledge_updates:
                    updated_count, update_errors = self.knowledge_repo.batch_update_mastery(knowledge_updates)
                    knowledge_updated = updated_count
                    errors.extend(update_errors)
                
                return practice_saved, knowledge_updated, errors
                
            except Exception as e:
                errors.append(f"批量保存失敗: {str(e)}")
                return practice_saved, knowledge_updated, errors
    
    def synchronize_data_consistency(self) -> Dict[str, Any]:
        """
        同步數據一致性
        
        檢查並修復知識點和練習記錄之間的不一致問題
        
        Returns:
            同步結果報告
        """
        with self._operation_lock:
            inconsistencies = []
            fixes_applied = []
            
            # 檢查知識點引用
            knowledge_data = self.knowledge_repo.load()
            practice_data = self.practice_repo.load()
            
            # 檢查練習記錄中引用的知識點是否存在
            knowledge_ids = set(kp.get('id') for kp in knowledge_data['data'])
            
            for practice in practice_data['data']:
                referenced_ids = practice.get('knowledge_point_ids', [])
                for kp_id in referenced_ids:
                    if kp_id not in knowledge_ids:
                        inconsistencies.append({
                            'type': 'missing_knowledge_point',
                            'practice_timestamp': practice.get('timestamp'),
                            'missing_id': kp_id
                        })
            
            # 檢查知識點的統計數據是否與練習記錄一致
            for knowledge_point in knowledge_data['data']:
                kp_id = knowledge_point.get('id')
                
                # 統計相關的練習記錄
                related_practices = [
                    p for p in practice_data['data']
                    if kp_id in p.get('knowledge_point_ids', [])
                ]
                
                # 驗證統計數據
                actual_correct = sum(1 for p in related_practices if p.get('is_correct', False))
                actual_total = len(related_practices)
                
                stored_correct = knowledge_point.get('correct_count', 0)
                stored_mistake = knowledge_point.get('mistake_count', 0)
                stored_total = stored_correct + stored_mistake
                
                if abs(actual_total - stored_total) > 0:
                    inconsistencies.append({
                        'type': 'inconsistent_counts',
                        'knowledge_point_id': kp_id,
                        'actual_total': actual_total,
                        'stored_total': stored_total
                    })
                    
                    # 修復統計數據
                    if actual_total > 0:
                        knowledge_point['correct_count'] = actual_correct
                        knowledge_point['mistake_count'] = actual_total - actual_correct
                        knowledge_point['mastery_level'] = actual_correct / actual_total
                        fixes_applied.append({
                            'type': 'fixed_counts',
                            'knowledge_point_id': kp_id,
                            'new_correct': actual_correct,
                            'new_mistake': actual_total - actual_correct
                        })
            
            # 保存修復後的數據
            if fixes_applied:
                self.knowledge_repo.save(knowledge_data)
                self._clear_cache()
            
            return {
                'sync_date': datetime.now().isoformat(),
                'inconsistencies_found': len(inconsistencies),
                'fixes_applied': len(fixes_applied),
                'details': {
                    'inconsistencies': inconsistencies,
                    'fixes': fixes_applied
                }
            }
    
    def export_comprehensive_data(
        self, 
        format_type: str = 'json',
        include_analytics: bool = True
    ) -> Any:
        """
        導出綜合數據
        
        Args:
            format_type: 導出格式 ('json', 'csv', 'summary')
            include_analytics: 是否包含分析數據
            
        Returns:
            導出的綜合數據
        """
        with self._operation_lock:
            # 獲取基礎數據
            knowledge_data = self.knowledge_repo.export_to_format(format_type, include_examples=True)
            practice_data = self.practice_repo.export_data(format_type=format_type)
            
            export_data = {
                'export_metadata': {
                    'export_date': datetime.now().isoformat(),
                    'format': format_type,
                    'include_analytics': include_analytics,
                    'version': '1.0'
                },
                'knowledge_points': knowledge_data,
                'practice_records': practice_data
            }
            
            if include_analytics:
                export_data['analytics'] = {
                    'learning_report': self.get_comprehensive_learning_report(30),
                    'efficiency_metrics': self.get_learning_efficiency_metrics(30),
                    'data_consistency': self.synchronize_data_consistency()
                }
            
            return export_data
    
    # === 私有輔助方法 ===
    
    def _analyze_knowledge_practice_correlation(self, days: int) -> Dict[str, Any]:
        """分析知識點與練習記錄的關聯性"""
        recent_practices = self.practice_repo.get_recent_records(days)
        knowledge_data = self.knowledge_repo.load()['data']
        
        # 統計各類別知識點在練習中的表現
        category_performance = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        # 知識點命中率分析
        knowledge_point_hits = defaultdict(int)
        
        for practice in recent_practices:
            referenced_ids = practice.get('knowledge_point_ids', [])
            is_correct = practice.get('is_correct', False)
            
            for kp_id in referenced_ids:
                knowledge_point_hits[kp_id] += 1
                
                # 找到對應的知識點
                for kp in knowledge_data:
                    if kp.get('id') == kp_id:
                        category = kp.get('category', 'other')
                        category_performance[category]['total'] += 1
                        if is_correct:
                            category_performance[category]['correct'] += 1
                        break
        
        # 計算各類別準確率
        for category, stats in category_performance.items():
            stats['accuracy'] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0
        
        # 最常練習的知識點
        most_practiced_points = sorted(
            knowledge_point_hits.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            'analysis_period_days': days,
            'category_performance': dict(category_performance),
            'most_practiced_points': most_practiced_points,
            'total_practice_records': len(recent_practices),
            'knowledge_points_referenced': len(knowledge_point_hits)
        }
    
    def _assess_learning_progress(self, days: int) -> Dict[str, Any]:
        """評估學習進度"""
        # 獲取當前週期和上一週期的數據進行對比
        current_period = datetime.now() - timedelta(days=days)
        previous_period = current_period - timedelta(days=days)
        
        current_practices = self.practice_repo.get_records_by_date_range(current_period, datetime.now())
        previous_practices = self.practice_repo.get_records_by_date_range(previous_period, current_period)
        
        # 計算進步指標
        current_accuracy = self._calculate_accuracy_for_practices(current_practices)
        previous_accuracy = self._calculate_accuracy_for_practices(previous_practices)
        
        accuracy_improvement = current_accuracy - previous_accuracy
        
        # 知識點掌握進步
        knowledge_stats = self.knowledge_repo.get_advanced_statistics()
        avg_mastery = knowledge_stats.get('mastery_stats', {}).get('average', 0.0)
        
        # 學習一致性
        practice_dates = set()
        for practice in current_practices:
            try:
                date_str = practice['timestamp'][:10]
                practice_dates.add(date_str)
            except (KeyError, IndexError):
                continue
        
        consistency_score = len(practice_dates) / days if days > 0 else 0
        
        return {
            'assessment_period': days,
            'accuracy_improvement': accuracy_improvement,
            'current_accuracy': current_accuracy,
            'previous_accuracy': previous_accuracy,
            'average_mastery_level': avg_mastery,
            'consistency_score': consistency_score,
            'learning_trend': self._determine_learning_trend(
                accuracy_improvement, avg_mastery, consistency_score
            )
        }
    
    def _generate_learning_recommendations(
        self, 
        knowledge_stats: Dict[str, Any], 
        practice_analytics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成學習建議"""
        recommendations = []
        
        # 基於準確率的建議
        basic_metrics = practice_analytics.get('basic_metrics', {})
        accuracy = basic_metrics.get('accuracy', 0.0)
        
        if accuracy < 0.6:
            recommendations.append({
                'type': 'accuracy_improvement',
                'priority': 'high',
                'message': '準確率偏低，建議加強基礎練習',
                'specific_actions': [
                    '重複練習錯誤較多的知識點',
                    '降低練習難度，鞏固基礎',
                    '增加練習頻率'
                ]
            })
        elif accuracy > 0.85:
            recommendations.append({
                'type': 'challenge_increase',
                'priority': 'medium',
                'message': '準確率很高，可以挑戰更高難度',
                'specific_actions': [
                    '嘗試更長的句子',
                    '練習複雜的語法結構',
                    '挑戰較少練習的知識點'
                ]
            })
        
        # 基於練習頻率的建議
        daily_average = basic_metrics.get('daily_average', 0.0)
        if daily_average < 3:
            recommendations.append({
                'type': 'frequency_increase',
                'priority': 'medium',
                'message': '建議增加每日練習量',
                'specific_actions': [
                    '設定每日最低練習目標',
                    '利用碎片時間練習',
                    '建立固定的練習時間'
                ]
            })
        
        # 基於知識點掌握度的建議
        mastery_stats = knowledge_stats.get('mastery_stats', {})
        mastery_distribution = mastery_stats.get('distribution', {})
        
        beginner_count = mastery_distribution.get('beginner', 0)
        total_points = knowledge_stats.get('total_points', 1)
        
        if beginner_count / total_points > 0.3:
            recommendations.append({
                'type': 'mastery_improvement',
                'priority': 'high',
                'message': '有較多初級掌握度的知識點需要加強',
                'specific_actions': [
                    '重點複習掌握度低的知識點',
                    '使用複習模式進行針對性練習',
                    '分解複雜知識點進行專項練習'
                ]
            })
        
        return recommendations
    
    def _suggest_next_actions(
        self, 
        knowledge_stats: Dict[str, Any], 
        practice_analytics: Dict[str, Any]
    ) -> List[str]:
        """建議下一步行動"""
        actions = []
        
        # 檢查是否有到期的複習
        review_due_stats = knowledge_stats.get('review_due_stats', {})
        overdue_count = review_due_stats.get('overdue', 0)
        
        if overdue_count > 0:
            actions.append(f"立即複習 {overdue_count} 個已到期的知識點")
        
        # 檢查今天的複習
        today_due = review_due_stats.get('today', 0)
        if today_due > 0:
            actions.append(f"完成今天的 {today_due} 個知識點複習")
        
        # 基於最近表現建議
        basic_metrics = practice_analytics.get('basic_metrics', {})
        daily_average = basic_metrics.get('daily_average', 0.0)
        
        if daily_average == 0:
            actions.append("開始今天的練習，建議先從簡單題目開始")
        elif daily_average < 5:
            actions.append("增加練習量，嘗試完成 5-10 個練習題")
        
        # 困難點相關行動
        difficulty_analysis = practice_analytics.get('difficulty_analysis', {})
        common_errors = difficulty_analysis.get('common_error_types', {})
        
        if common_errors:
            most_common_error = max(common_errors, key=common_errors.get)
            actions.append(f"重點關注 {most_common_error} 類型的錯誤")
        
        return actions[:5]  # 限制在5個行動內
    
    def _calculate_efficiency_metrics(self, days: int) -> Dict[str, Any]:
        """計算學習效率指標"""
        # 獲取數據
        recent_practices = self.practice_repo.get_recent_records(days)
        knowledge_stats = self.knowledge_repo.get_advanced_statistics()
        
        if not recent_practices:
            return {'no_data': True}
        
        # 基礎效率指標
        total_practices = len(recent_practices)
        correct_count = sum(1 for p in recent_practices if p.get('is_correct', False))
        efficiency_ratio = correct_count / total_practices if total_practices > 0 else 0
        
        # 時間效率（假設每次練習耗時相同）
        practice_dates = set()
        for practice in recent_practices:
            try:
                date_str = practice['timestamp'][:10]
                practice_dates.add(date_str)
            except (KeyError, IndexError):
                continue
        
        active_days = len(practice_dates)
        practices_per_active_day = total_practices / active_days if active_days > 0 else 0
        
        # 知識點覆蓋效率
        total_knowledge_points = knowledge_stats.get('total_points', 0)
        practiced_knowledge_points = set()
        
        for practice in recent_practices:
            referenced_ids = practice.get('knowledge_point_ids', [])
            practiced_knowledge_points.update(referenced_ids)
        
        coverage_ratio = len(practiced_knowledge_points) / total_knowledge_points if total_knowledge_points > 0 else 0
        
        # 掌握度提升效率
        avg_mastery = knowledge_stats.get('mastery_stats', {}).get('average', 0.0)
        mastery_efficiency = avg_mastery * efficiency_ratio  # 結合掌握度和準確率
        
        return {
            'analysis_period_days': days,
            'basic_efficiency': {
                'total_practices': total_practices,
                'correct_count': correct_count,
                'efficiency_ratio': efficiency_ratio
            },
            'time_efficiency': {
                'active_days': active_days,
                'practices_per_active_day': practices_per_active_day,
                'consistency_score': active_days / days if days > 0 else 0
            },
            'coverage_efficiency': {
                'total_knowledge_points': total_knowledge_points,
                'practiced_knowledge_points': len(practiced_knowledge_points),
                'coverage_ratio': coverage_ratio
            },
            'overall_efficiency': {
                'mastery_efficiency': mastery_efficiency,
                'composite_score': (efficiency_ratio * 0.4 + coverage_ratio * 0.3 + (active_days / days) * 0.3) if days > 0 else 0
            }
        }
    
    def _is_practice_related_to_knowledge_point(
        self, 
        practice: Dict[str, Any], 
        knowledge_point: Dict[str, Any]
    ) -> bool:
        """判斷練習記錄是否與知識點相關"""
        # 檢查直接引用
        referenced_ids = practice.get('knowledge_point_ids', [])
        if knowledge_point.get('id') in referenced_ids:
            return True
        
        # 檢查內容相關性（簡化版本）
        practice_sentence = practice.get('chinese_sentence', '').lower()
        practice_answer = practice.get('user_answer', '').lower()
        
        kp_original = knowledge_point.get('original_phrase', '').lower()
        kp_correction = knowledge_point.get('correction', '').lower()
        
        # 如果練習內容包含知識點的原始短語或修正版本
        if (kp_original and kp_original in practice_sentence) or \
           (kp_original and kp_original in practice_answer) or \
           (kp_correction and kp_correction in practice_sentence) or \
           (kp_correction and kp_correction in practice_answer):
            return True
        
        return False
    
    def _calculate_accuracy_for_practices(self, practices: List[Dict[str, Any]]) -> float:
        """計算練習記錄的準確率"""
        if not practices:
            return 0.0
        
        correct_count = sum(1 for p in practices if p.get('is_correct', False))
        return correct_count / len(practices)
    
    def _determine_learning_trend(
        self, 
        accuracy_improvement: float, 
        avg_mastery: float, 
        consistency_score: float
    ) -> str:
        """判斷學習趨勢"""
        # 綜合考慮準確率改善、平均掌握度和一致性
        if accuracy_improvement > 0.1 and avg_mastery > 0.7 and consistency_score > 0.8:
            return 'excellent_progress'
        elif accuracy_improvement > 0.05 and avg_mastery > 0.5:
            return 'good_progress'
        elif accuracy_improvement > 0 or avg_mastery > 0.6:
            return 'steady_progress'
        elif accuracy_improvement < -0.1 or consistency_score < 0.3:
            return 'needs_attention'
        else:
            return 'stable'
    
    def _clear_cache(self):
        """清除緩存"""
        with self._cache_lock:
            self._cache.clear()
            self._last_cache_update = None
    
    def get_service_info(self) -> Dict[str, Any]:
        """獲取服務信息"""
        return {
            'service_name': 'CompositeRepository',
            'version': '1.0.0',
            'description': '複合資料庫操作層，提供跨實體的複雜查詢和操作',
            'capabilities': [
                'comprehensive_learning_reports',
                'knowledge_practice_correlation',
                'learning_efficiency_analysis',
                'batch_session_operations',
                'data_consistency_management',
                'comprehensive_data_export'
            ],
            'dependencies': {
                'knowledge_repository': self.knowledge_repo.__class__.__name__,
                'practice_repository': self.practice_repo.__class__.__name__
            }
        }