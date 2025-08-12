"""
知識點數據庫操作層

專門處理知識點數據的 CRUD 操作，包括：
- 複合鍵查找 (key_point, original_phrase, correction)
- 批量操作支援
- 統計查詢方法
- 掌握度更新
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from functools import lru_cache
import json
import threading
from collections import defaultdict

from .base_repository import JSONRepository
from ..error_types import ErrorCategory
from ..constants import DisplayConstants, LearningConstants


class KnowledgeRepository(JSONRepository[Dict[str, Any]]):
    """知識點數據庫
    
    增強功能：
    - 批量操作支援
    - 查詢結果緩存
    - 統計數據聚合
    - 事務性操作
    - 數據導出功能
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 查詢結果緩存
        self._cache_lock = threading.RLock()
        self._stats_cache = {}
        self._last_cache_update = None
        
        # 批量操作緩衝區
        self._batch_buffer = []
        self._batch_mode = False
    
    @property
    def current_version(self) -> str:
        return "3.0"
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """驗證知識點數據格式"""
        if not isinstance(data, dict):
            return False
        
        # 檢查必要的頂層欄位
        if 'data' not in data:
            return False
        
        knowledge_points = data['data']
        if not isinstance(knowledge_points, list):
            return False
        
        # 驗證每個知識點的格式
        for point in knowledge_points:
            if not self._validate_knowledge_point(point):
                return False
        
        return True
    
    def _validate_knowledge_point(self, point: Dict[str, Any]) -> bool:
        """驗證單個知識點格式"""
        required_fields = [
            'id', 'key_point', 'category', 'subtype', 
            'explanation', 'original_phrase', 'correction'
        ]
        
        for field in required_fields:
            if field not in point:
                return False
        
        # 驗證類型
        if not isinstance(point['id'], int):
            return False
        
        if point['category'] not in ['systematic', 'isolated', 'enhancement', 'other']:
            return False
        
        return True
    
    def migrate_data(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """數據版本遷移"""
        if from_version == "3.0":
            return data
        
        # 處理舊格式 (v2.0 及更早)
        if from_version in ["2.0", "1.0"] or from_version is None:
            return self._migrate_from_legacy(data)
        
        # 其他版本的遷移邏輯
        return data
    
    def _migrate_from_legacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """從舊版本遷移到 v3.0"""
        # 如果數據是列表格式（很舊的版本）
        if isinstance(data, list):
            knowledge_points = data
        # 如果數據有 knowledge_points 欄位（v2.0）
        elif isinstance(data, dict) and 'knowledge_points' in data:
            knowledge_points = data['knowledge_points']
        # 如果已經是新格式但缺少版本信息
        elif isinstance(data, dict) and 'data' in data:
            knowledge_points = data['data']
        else:
            knowledge_points = []
        
        # 遷移每個知識點
        migrated_points = []
        for point in knowledge_points:
            migrated_point = self._migrate_knowledge_point(point)
            if migrated_point:
                migrated_points.append(migrated_point)
        
        return {
            'version': '3.0',
            'migration_date': datetime.now().isoformat(),
            'data': migrated_points
        }
    
    def _migrate_knowledge_point(self, point: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """遷移單個知識點"""
        try:
            # 處理舊格式的 examples 欄位
            examples = point.get('examples', [])
            
            # 創建 original_error（從第一個例句）
            if examples:
                first_example = examples[0]
                original_error = {
                    'chinese_sentence': first_example.get('chinese', ''),
                    'user_answer': first_example.get('user_answer', ''),
                    'correct_answer': first_example.get('correct', ''),
                    'timestamp': point.get('created_at', datetime.now().isoformat())
                }
            else:
                original_error = {
                    'chinese_sentence': '',
                    'user_answer': point.get('original_phrase', ''),
                    'correct_answer': point.get('correction', ''),
                    'timestamp': point.get('created_at', datetime.now().isoformat())
                }
            
            # 創建 review_examples（從其餘例句）
            review_examples = []
            for example in examples[1:]:
                review_examples.append({
                    'chinese_sentence': example.get('chinese', ''),
                    'user_answer': example.get('user_answer', ''),
                    'correct_answer': example.get('correct', ''),
                    'timestamp': point.get('last_seen', datetime.now().isoformat()),
                    'is_correct': False  # 假設都是錯誤記錄
                })
            
            # 構建遷移後的知識點
            migrated = {
                'id': point.get('id', 0),
                'key_point': point.get('key_point', ''),
                'category': point.get('category', 'other'),
                'subtype': point.get('subtype', ''),
                'explanation': point.get('explanation', ''),
                'original_phrase': point.get('original_phrase', ''),
                'correction': point.get('correction', ''),
                'original_error': original_error,
                'review_examples': review_examples,
                'mastery_level': point.get('mastery_level', 0.0),
                'mistake_count': point.get('mistake_count', 1),
                'correct_count': point.get('correct_count', 0),
                'created_at': point.get('created_at', datetime.now().isoformat()),
                'last_seen': point.get('last_seen', datetime.now().isoformat()),
                'next_review': point.get('next_review', datetime.now().isoformat())
            }
            
            return migrated
            
        except Exception:
            # 忽略無法遷移的數據點
            return None
    
    def _detect_version(self, data: Dict[str, Any]) -> str:
        """檢測數據版本"""
        # 如果是列表格式，是很舊的版本
        if isinstance(data, list):
            return "1.0"
        
        # 如果有 knowledge_points 欄位，是 v2.0
        if isinstance(data, dict) and 'knowledge_points' in data:
            return "2.0"
        
        # 如果有 data 欄位但沒有 version，可能是 v3.0 的不完整版本
        if isinstance(data, dict) and 'data' in data:
            return "2.9"  # 接近 v3.0 的版本
        
        return "1.0"
    
    def find_by_composite_key(
        self, 
        key_point: str, 
        original_phrase: str = "", 
        correction: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        使用複合鍵查找知識點
        
        Args:
            key_point: 知識點摘要
            original_phrase: 原始短語
            correction: 修正版本
            
        Returns:
            匹配的知識點，如果沒找到則返回 None
        """
        data = self.load()
        
        for point in data['data']:
            if (point.get('key_point') == key_point and 
                point.get('original_phrase') == original_phrase and 
                point.get('correction') == correction):
                return point
        
        return None
    
    def find_by_id(self, point_id: int) -> Optional[Dict[str, Any]]:
        """根據 ID 查找知識點"""
        data = self.load()
        
        for point in data['data']:
            if point.get('id') == point_id:
                return point
        
        return None
    
    def find_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根據類別查找知識點"""
        data = self.load()
        
        return [
            point for point in data['data'] 
            if point.get('category') == category
        ]
    
    def find_due_for_review(self) -> List[Dict[str, Any]]:
        """查找需要複習的知識點"""
        data = self.load()
        now = datetime.now().isoformat()
        
        return [
            point for point in data['data']
            if point.get('next_review', '') <= now
        ]
    
    def find_review_candidates(self, max_points: int = 5) -> List[Dict[str, Any]]:
        """查找複習候選知識點（單一性錯誤和可以更好類別）"""
        data = self.load()
        
        # 篩選單一性錯誤和可以更好類別
        candidates = [
            point for point in data['data']
            if point.get('category') in ['isolated', 'enhancement']
        ]
        
        if not candidates:
            return []
        
        # 按複習優先級排序
        now = datetime.now().isoformat()
        
        def sort_key(point: Dict[str, Any]) -> tuple:
            is_due = point.get('next_review', '') <= now
            mastery_level = point.get('mastery_level', 0.0)
            mistake_count = point.get('mistake_count', 0)
            
            return (
                not is_due,  # 到期的排前面
                mastery_level,  # 掌握度低的排前面
                -mistake_count  # 錯誤次數多的排前面
            )
        
        candidates.sort(key=sort_key)
        return candidates[:max_points]
    
    def add_knowledge_point(self, point: Dict[str, Any]) -> bool:
        """添加新知識點"""
        if not self._validate_knowledge_point(point):
            return False
        
        data = self.load()
        
        # 檢查是否已存在（使用複合鍵）
        existing = self.find_by_composite_key(
            point['key_point'],
            point.get('original_phrase', ''),
            point.get('correction', '')
        )
        
        if existing:
            return False  # 已存在
        
        # 確保 ID 是唯一的
        if point.get('id') is None:
            point['id'] = self._get_next_id(data['data'])
        
        data['data'].append(point)
        self.save(data)
        return True
    
    def update_knowledge_point(self, point_id: int, updates: Dict[str, Any]) -> bool:
        """更新知識點"""
        data = self.load()
        
        for i, point in enumerate(data['data']):
            if point.get('id') == point_id:
                data['data'][i].update(updates)
                self.save(data)
                return True
        
        return False
    
    def update_mastery(
        self, 
        point_id: int, 
        is_correct: bool,
        review_example: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新知識點掌握度
        
        Args:
            point_id: 知識點ID
            is_correct: 是否答對
            review_example: 複習例句（可選）
            
        Returns:
            是否更新成功
        """
        point = self.find_by_id(point_id)
        if not point:
            return False
        
        # 更新計數
        if is_correct:
            point['correct_count'] = point.get('correct_count', 0) + 1
        else:
            point['mistake_count'] = point.get('mistake_count', 0) + 1
        
        # 更新掌握度（簡化版本，實際邏輯可能更複雜）
        correct_count = point.get('correct_count', 0)
        mistake_count = point.get('mistake_count', 0)
        total_count = correct_count + mistake_count
        
        if total_count > 0:
            point['mastery_level'] = correct_count / total_count
        
        # 更新時間戳
        point['last_seen'] = datetime.now().isoformat()
        
        # 計算下次複習時間（簡化版本）
        if is_correct:
            # 答對則延長複習間隔
            days = min(30, int(point['mastery_level'] * 30) + 1)
        else:
            # 答錯則縮短複習間隔
            days = max(1, int((1 - point['mastery_level']) * 7))
        
        from datetime import timedelta
        next_review = datetime.now() + timedelta(days=days)
        point['next_review'] = next_review.isoformat()
        
        # 添加複習例句
        if review_example and isinstance(review_example, dict):
            if 'review_examples' not in point:
                point['review_examples'] = []
            point['review_examples'].append(review_example)
        
        # 保存更新
        return self.update_knowledge_point(point_id, point)
    
    def delete_knowledge_point(self, point_id: int) -> bool:
        """刪除知識點"""
        data = self.load()
        
        for i, point in enumerate(data['data']):
            if point.get('id') == point_id:
                del data['data'][i]
                self.save(data)
                return True
        
        return False
    
    def batch_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新知識點
        
        Args:
            updates: 更新列表，每個元素包含 'id' 和要更新的欄位
            
        Returns:
            成功更新的數量
        """
        if not updates:
            return 0
        
        data = self.load()
        updated_count = 0
        
        # 創建 ID 到索引的映射
        id_to_index = {
            point.get('id'): i 
            for i, point in enumerate(data['data'])
        }
        
        for update in updates:
            point_id = update.get('id')
            if point_id in id_to_index:
                index = id_to_index[point_id]
                update_data = {k: v for k, v in update.items() if k != 'id'}
                data['data'][index].update(update_data)
                updated_count += 1
        
        if updated_count > 0:
            self.save(data)
        
        return updated_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資料"""
        data = self.load()
        points = data['data']
        
        if not points:
            return {
                'total_points': 0,
                'avg_mastery': 0.0,
                'category_distribution': {},
                'due_reviews': 0
            }
        
        # 基礎統計
        total_points = len(points)
        avg_mastery = sum(point.get('mastery_level', 0.0) for point in points) / total_points
        
        # 類別分佈
        category_distribution = {}
        for point in points:
            category = point.get('category', 'other')
            category_distribution[category] = category_distribution.get(category, 0) + 1
        
        # 需要複習的數量
        now = datetime.now().isoformat()
        due_reviews = sum(
            1 for point in points 
            if point.get('next_review', '') <= now
        )
        
        return {
            'total_points': total_points,
            'avg_mastery': avg_mastery,
            'category_distribution': category_distribution,
            'due_reviews': due_reviews,
            'mastery_levels': {
                'beginner': sum(1 for p in points if p.get('mastery_level', 0) < 0.3),
                'intermediate': sum(1 for p in points if 0.3 <= p.get('mastery_level', 0) < 0.7),
                'advanced': sum(1 for p in points if p.get('mastery_level', 0) >= 0.7)
            }
        }
    
    def _get_next_id(self, points: List[Dict[str, Any]]) -> int:
        """獲取下一個可用的 ID"""
        if not points:
            return 1
        
        max_id = max(point.get('id', 0) for point in points)
        return max_id + 1
    
    def search(self, query: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        搜尋知識點
        
        Args:
            query: 搜尋關鍵字
            fields: 要搜尋的欄位列表，默認搜尋所有文字欄位
            
        Returns:
            匹配的知識點列表
        """
        if not query.strip():
            return []
        
        data = self.load()
        query = query.lower()
        
        if fields is None:
            fields = ['key_point', 'explanation', 'original_phrase', 'correction']
        
        results = []
        for point in data['data']:
            for field in fields:
                field_value = str(point.get(field, '')).lower()
                if query in field_value:
                    results.append(point)
                    break  # 避免重複添加同一個知識點
        
        return results
    
    # === 新增的批量操作方法 ===
    
    def batch_save_knowledge_points(
        self, 
        points: List[Dict[str, Any]], 
        validate_each: bool = True
    ) -> Tuple[int, List[str]]:
        """
        批量保存知識點
        
        Args:
            points: 要保存的知識點列表
            validate_each: 是否驗證每個知識點
            
        Returns:
            成功保存的數量和錯誤信息列表
        """
        if not points:
            return 0, []
        
        data = self.load()
        saved_count = 0
        errors = []
        
        # 創建 ID 映射以快速檢查重複
        existing_keys = set()
        for point in data['data']:
            key = (point.get('key_point', ''), point.get('original_phrase', ''), point.get('correction', ''))
            existing_keys.add(key)
        
        for i, point in enumerate(points):
            try:
                # 驗證格式
                if validate_each and not self._validate_knowledge_point(point):
                    errors.append(f"第 {i+1} 個知識點格式無效")
                    continue
                
                # 檢查重複
                key = (point.get('key_point', ''), point.get('original_phrase', ''), point.get('correction', ''))
                if key in existing_keys:
                    errors.append(f"第 {i+1} 個知識點已存在")
                    continue
                
                # 確保 ID 唯一
                if point.get('id') is None:
                    point['id'] = self._get_next_id(data['data'])
                
                data['data'].append(point)
                existing_keys.add(key)
                saved_count += 1
                
            except Exception as e:
                errors.append(f"第 {i+1} 個知識點保存失敗: {str(e)}")
        
        if saved_count > 0:
            self.save(data)
            self._clear_cache()
        
        return saved_count, errors
    
    def find_by_composite_key_batch(
        self, 
        keys: List[Tuple[str, str, str]]
    ) -> List[Optional[Dict[str, Any]]]:
        """
        批量使用複合鍵查找知識點
        
        Args:
            keys: 複合鍵列表 [(key_point, original_phrase, correction), ...]
            
        Returns:
            對應的知識點列表，找不到的為 None
        """
        if not keys:
            return []
        
        data = self.load()
        
        # 建立索引以提高查找效率
        index = {}
        for point in data['data']:
            key = (point.get('key_point', ''), point.get('original_phrase', ''), point.get('correction', ''))
            index[key] = point
        
        return [index.get(key) for key in keys]
    
    def batch_update_mastery(
        self, 
        updates: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        """
        批量更新知識點掌握度
        
        Args:
            updates: 更新列表，每個元素包含 point_id, is_correct, review_example 等
            
        Returns:
            成功更新的數量和錯誤信息列表
        """
        if not updates:
            return 0, []
        
        data = self.load()
        updated_count = 0
        errors = []
        
        # 創建 ID 到索引的映射
        id_to_index = {point.get('id'): i for i, point in enumerate(data['data'])}
        
        for update in updates:
            try:
                point_id = update.get('point_id')
                is_correct = update.get('is_correct')
                review_example = update.get('review_example')
                
                if point_id not in id_to_index:
                    errors.append(f"找不到 ID 為 {point_id} 的知識點")
                    continue
                
                index = id_to_index[point_id]
                point = data['data'][index]
                
                # 更新計數
                if is_correct:
                    point['correct_count'] = point.get('correct_count', 0) + 1
                else:
                    point['mistake_count'] = point.get('mistake_count', 0) + 1
                
                # 重新計算掌握度
                correct_count = point.get('correct_count', 0)
                mistake_count = point.get('mistake_count', 0)
                total_count = correct_count + mistake_count
                
                if total_count > 0:
                    point['mastery_level'] = correct_count / total_count
                
                # 更新時間和複習計劃
                point['last_seen'] = datetime.now().isoformat()
                
                # 計算下次複習時間
                category = point.get('category', 'other')
                mastery_level = point.get('mastery_level', 0.0)
                
                if is_correct:
                    days = self._calculate_review_interval(category, mastery_level, True)
                else:
                    days = self._calculate_review_interval(category, mastery_level, False)
                
                next_review = datetime.now() + timedelta(days=days)
                point['next_review'] = next_review.isoformat()
                
                # 添加複習例句
                if review_example and isinstance(review_example, dict):
                    if 'review_examples' not in point:
                        point['review_examples'] = []
                    point['review_examples'].append({
                        **review_example,
                        'timestamp': datetime.now().isoformat(),
                        'is_correct': is_correct
                    })
                
                updated_count += 1
                
            except Exception as e:
                errors.append(f"更新知識點 {update.get('point_id')} 失敗: {str(e)}")
        
        if updated_count > 0:
            self.save(data)
            self._clear_cache()
        
        return updated_count, errors
    
    def find_by_multiple_criteria(
        self, 
        categories: Optional[List[str]] = None,
        mastery_range: Optional[Tuple[float, float]] = None,
        due_before: Optional[datetime] = None,
        mistake_count_min: Optional[int] = None,
        limit: Optional[int] = None,
        sort_by: str = 'last_seen',
        sort_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        根據多個條件查找知識點
        
        Args:
            categories: 類別列表
            mastery_range: 掌握度範圍 (min, max)
            due_before: 需要在此時間前複習
            mistake_count_min: 最少錯誤次數
            limit: 限制返回數量
            sort_by: 排序欄位
            sort_desc: 是否降序
            
        Returns:
            符合條件的知識點列表
        """
        data = self.load()
        points = data['data']
        
        # 應用篩選條件
        if categories:
            points = [p for p in points if p.get('category') in categories]
        
        if mastery_range:
            min_mastery, max_mastery = mastery_range
            points = [
                p for p in points 
                if min_mastery <= p.get('mastery_level', 0.0) <= max_mastery
            ]
        
        if due_before:
            due_str = due_before.isoformat()
            points = [
                p for p in points 
                if p.get('next_review', '') <= due_str
            ]
        
        if mistake_count_min is not None:
            points = [
                p for p in points 
                if p.get('mistake_count', 0) >= mistake_count_min
            ]
        
        # 排序
        if sort_by in points[0] if points else False:
            points.sort(
                key=lambda p: p.get(sort_by, ''),
                reverse=sort_desc
            )
        
        # 限制數量
        if limit and limit > 0:
            points = points[:limit]
        
        return points
    
    def get_advanced_statistics(self) -> Dict[str, Any]:
        """
        獲取進階統計資料（帶緩存）
        
        Returns:
            詳細的統計資料字典
        """
        with self._cache_lock:
            # 檢查緩存是否有效
            if (self._last_cache_update and 
                datetime.now() - self._last_cache_update < timedelta(minutes=5) and
                'advanced_stats' in self._stats_cache):
                return self._stats_cache['advanced_stats']
            
            # 重新計算統計
            data = self.load()
            points = data['data']
            
            if not points:
                return self._empty_advanced_stats()
            
            stats = self._calculate_advanced_statistics(points)
            
            # 更新緩存
            self._stats_cache['advanced_stats'] = stats
            self._last_cache_update = datetime.now()
            
            return stats
    
    def archive_old_records(
        self, 
        cutoff_date: datetime,
        archive_file_path: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        歸檔舊記錄
        
        Args:
            cutoff_date: 截止日期，早於此日期的記錄將被歸檔
            archive_file_path: 歸檔文件路徑，None 則使用默認路徑
            
        Returns:
            歸檔的記錄數量和歸檔文件路徑
        """
        data = self.load()
        original_count = len(data['data'])
        
        cutoff_str = cutoff_date.isoformat()
        
        # 分離要歸檔和保留的記錄
        to_archive = []
        to_keep = []
        
        for point in data['data']:
            created_at = point.get('created_at', '')
            if created_at and created_at < cutoff_str:
                to_archive.append(point)
            else:
                to_keep.append(point)
        
        if not to_archive:
            return 0, ""
        
        # 創建歸檔文件
        if archive_file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file_path = f"{self.file_path.parent}/knowledge_archive_{timestamp}.json"
        
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
    
    def export_to_format(
        self, 
        format_type: str = 'json',
        categories: Optional[List[str]] = None,
        include_examples: bool = True
    ) -> Any:
        """
        導出數據到指定格式
        
        Args:
            format_type: 導出格式 ('json', 'csv', 'summary')
            categories: 要導出的類別，None 表示全部
            include_examples: 是否包含例句
            
        Returns:
            導出的數據
        """
        data = self.load()
        points = data['data']
        
        # 篩選類別
        if categories:
            points = [p for p in points if p.get('category') in categories]
        
        if format_type == 'json':
            return {
                'export_date': datetime.now().isoformat(),
                'point_count': len(points),
                'categories_included': categories or 'all',
                'include_examples': include_examples,
                'data': points
            }
        
        elif format_type == 'csv':
            csv_data = []
            for point in points:
                row = {
                    'id': point.get('id', ''),
                    'key_point': point.get('key_point', ''),
                    'category': point.get('category', ''),
                    'subtype': point.get('subtype', ''),
                    'explanation': point.get('explanation', ''),
                    'original_phrase': point.get('original_phrase', ''),
                    'correction': point.get('correction', ''),
                    'mastery_level': point.get('mastery_level', 0.0),
                    'mistake_count': point.get('mistake_count', 0),
                    'correct_count': point.get('correct_count', 0),
                    'created_at': point.get('created_at', ''),
                    'last_seen': point.get('last_seen', ''),
                    'next_review': point.get('next_review', '')
                }
                
                if include_examples:
                    examples = point.get('review_examples', [])
                    row['example_count'] = len(examples)
                    if examples:
                        row['latest_example'] = examples[-1].get('chinese_sentence', '')
                
                csv_data.append(row)
            
            return csv_data
        
        elif format_type == 'summary':
            summary = {
                'export_date': datetime.now().isoformat(),
                'total_points': len(points),
                'categories': {},
                'mastery_distribution': {
                    'beginner': 0,
                    'intermediate': 0,
                    'advanced': 0,
                    'expert': 0
                },
                'review_status': {
                    'due': 0,
                    'upcoming': 0,
                    'future': 0
                }
            }
            
            now = datetime.now().isoformat()
            
            for point in points:
                # 統計類別
                category = point.get('category', 'other')
                summary['categories'][category] = summary['categories'].get(category, 0) + 1
                
                # 統計掌握度分佈
                mastery = point.get('mastery_level', 0.0)
                if mastery < LearningConstants.MASTERY_THRESHOLD_BEGINNER:
                    summary['mastery_distribution']['beginner'] += 1
                elif mastery < LearningConstants.MASTERY_THRESHOLD_INTERMEDIATE:
                    summary['mastery_distribution']['intermediate'] += 1
                elif mastery < LearningConstants.MASTERY_THRESHOLD_ADVANCED:
                    summary['mastery_distribution']['advanced'] += 1
                else:
                    summary['mastery_distribution']['expert'] += 1
                
                # 統計複習狀態
                next_review = point.get('next_review', '')
                if next_review <= now:
                    summary['review_status']['due'] += 1
                elif next_review <= (datetime.now() + timedelta(days=7)).isoformat():
                    summary['review_status']['upcoming'] += 1
                else:
                    summary['review_status']['future'] += 1
            
            return summary
        
        else:
            raise ValueError(f"不支援的導出格式: {format_type}")
    
    # === 優化和輔助方法 ===
    
    def _calculate_review_interval(
        self, 
        category: str, 
        mastery_level: float, 
        is_correct: bool
    ) -> int:
        """
        計算複習間隔天數
        
        Args:
            category: 錯誤類別
            mastery_level: 掌握度
            is_correct: 是否答對
            
        Returns:
            複習間隔天數
        """
        base_interval = LearningConstants.REVIEW_INTERVAL_SHORT
        
        if is_correct:
            # 答對則延長間隔
            if mastery_level >= LearningConstants.MASTERY_THRESHOLD_EXPERT:
                base_interval = LearningConstants.REVIEW_INTERVAL_MASTERED
            elif mastery_level >= LearningConstants.MASTERY_THRESHOLD_ADVANCED:
                base_interval = LearningConstants.REVIEW_INTERVAL_LONG
            elif mastery_level >= LearningConstants.MASTERY_THRESHOLD_INTERMEDIATE:
                base_interval = LearningConstants.REVIEW_INTERVAL_MEDIUM
        else:
            # 答錯則縮短間隔
            base_interval = max(LearningConstants.REVIEW_INTERVAL_IMMEDIATE, 
                              int(base_interval * (1 - mastery_level)))
        
        # 根據類別調整
        multipliers = {
            'systematic': LearningConstants.REVIEW_MULTIPLIER_SYSTEMATIC,
            'isolated': LearningConstants.REVIEW_MULTIPLIER_ISOLATED,
            'enhancement': LearningConstants.REVIEW_MULTIPLIER_ENHANCEMENT,
            'other': LearningConstants.REVIEW_MULTIPLIER_OTHER
        }
        
        multiplier = multipliers.get(category, 1.0)
        return max(1, int(base_interval * multiplier))
    
    def _calculate_advanced_statistics(self, points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算進階統計資料"""
        total_points = len(points)
        now = datetime.now().isoformat()
        
        # 基礎統計
        categories = defaultdict(int)
        mastery_levels = []
        mistake_counts = []
        correct_counts = []
        
        # 時間相關統計
        due_counts = {'overdue': 0, 'today': 0, 'week': 0, 'month': 0}
        creation_dates = []
        last_seen_dates = []
        
        # 學習效果統計
        improvement_trends = defaultdict(list)
        
        for point in points:
            # 基礎統計
            categories[point.get('category', 'other')] += 1
            mastery_levels.append(point.get('mastery_level', 0.0))
            mistake_counts.append(point.get('mistake_count', 0))
            correct_counts.append(point.get('correct_count', 0))
            
            # 時間統計
            next_review = point.get('next_review', '')
            if next_review:
                if next_review < now:
                    due_counts['overdue'] += 1
                elif next_review <= (datetime.now() + timedelta(days=1)).isoformat():
                    due_counts['today'] += 1
                elif next_review <= (datetime.now() + timedelta(days=7)).isoformat():
                    due_counts['week'] += 1
                elif next_review <= (datetime.now() + timedelta(days=30)).isoformat():
                    due_counts['month'] += 1
            
            # 收集日期用於趨勢分析
            if point.get('created_at'):
                creation_dates.append(point['created_at'])
            if point.get('last_seen'):
                last_seen_dates.append(point['last_seen'])
            
            # 學習效果趨勢
            category = point.get('category', 'other')
            mastery = point.get('mastery_level', 0.0)
            improvement_trends[category].append(mastery)
        
        # 計算統計指標
        stats = {
            'total_points': total_points,
            'categories': dict(categories),
            'mastery_stats': {
                'average': sum(mastery_levels) / total_points if total_points else 0,
                'median': sorted(mastery_levels)[total_points // 2] if total_points else 0,
                'distribution': {
                    'expert': sum(1 for m in mastery_levels if m >= LearningConstants.MASTERY_THRESHOLD_EXPERT),
                    'advanced': sum(1 for m in mastery_levels if LearningConstants.MASTERY_THRESHOLD_ADVANCED <= m < LearningConstants.MASTERY_THRESHOLD_EXPERT),
                    'intermediate': sum(1 for m in mastery_levels if LearningConstants.MASTERY_THRESHOLD_INTERMEDIATE <= m < LearningConstants.MASTERY_THRESHOLD_ADVANCED),
                    'beginner': sum(1 for m in mastery_levels if m < LearningConstants.MASTERY_THRESHOLD_INTERMEDIATE)
                }
            },
            'mistake_stats': {
                'total': sum(mistake_counts),
                'average': sum(mistake_counts) / total_points if total_points else 0,
                'max': max(mistake_counts) if mistake_counts else 0
            },
            'correct_stats': {
                'total': sum(correct_counts),
                'average': sum(correct_counts) / total_points if total_points else 0,
                'max': max(correct_counts) if correct_counts else 0
            },
            'review_due_stats': due_counts,
            'category_mastery': {
                category: {
                    'average': sum(mastery_list) / len(mastery_list) if mastery_list else 0,
                    'count': len(mastery_list)
                }
                for category, mastery_list in improvement_trends.items()
            },
            'activity_stats': {
                'oldest_creation': min(creation_dates) if creation_dates else None,
                'newest_creation': max(creation_dates) if creation_dates else None,
                'latest_activity': max(last_seen_dates) if last_seen_dates else None
            }
        }
        
        return stats
    
    def _empty_advanced_stats(self) -> Dict[str, Any]:
        """返回空的統計資料結構"""
        return {
            'total_points': 0,
            'categories': {},
            'mastery_stats': {
                'average': 0.0,
                'median': 0.0,
                'distribution': {'expert': 0, 'advanced': 0, 'intermediate': 0, 'beginner': 0}
            },
            'mistake_stats': {'total': 0, 'average': 0.0, 'max': 0},
            'correct_stats': {'total': 0, 'average': 0.0, 'max': 0},
            'review_due_stats': {'overdue': 0, 'today': 0, 'week': 0, 'month': 0},
            'category_mastery': {},
            'activity_stats': {
                'oldest_creation': None,
                'newest_creation': None,
                'latest_activity': None
            }
        }
    
    def _clear_cache(self):
        """清除緩存"""
        with self._cache_lock:
            self._stats_cache.clear()
            self._last_cache_update = None
    
    # === 事務性操作方法 ===
    
    def begin_batch_mode(self):
        """開始批量模式"""
        self._batch_mode = True
        self._batch_buffer.clear()
    
    def commit_batch(self) -> bool:
        """
        提交批量操作
        
        Returns:
            是否成功提交
        """
        if not self._batch_mode or not self._batch_buffer:
            return True
        
        try:
            # 執行批量操作
            for operation in self._batch_buffer:
                self._execute_batch_operation(operation)
            
            self._batch_buffer.clear()
            self._batch_mode = False
            self._clear_cache()
            return True
            
        except Exception as e:
            self.logger.error(f"批量操作提交失敗: {str(e)}")
            self._batch_buffer.clear()
            self._batch_mode = False
            return False
    
    def rollback_batch(self):
        """回滾批量操作"""
        self._batch_buffer.clear()
        self._batch_mode = False
    
    def _execute_batch_operation(self, operation: Dict[str, Any]):
        """執行單個批量操作"""
        op_type = operation.get('type')
        data = operation.get('data')
        
        if op_type == 'add':
            self.add_knowledge_point(data)
        elif op_type == 'update':
            self.update_knowledge_point(data['id'], data['updates'])
        elif op_type == 'delete':
            self.delete_knowledge_point(data['id'])
        else:
            raise ValueError(f"未知的批量操作類型: {op_type}")