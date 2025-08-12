"""
Repository 層單元測試

包含原子操作、備份、版本遷移的完整測試
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.repositories import JSONRepository, KnowledgeRepository, PracticeRepository


class TestJSONRepository(unittest.TestCase):
    """基礎 JSON Repository 測試"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test.json"
        
    def tearDown(self):
        """清理測試環境"""
        self.temp_dir.cleanup()
    
    def create_test_repository(self):
        """創建測試用的 Repository"""
        class TestRepository(JSONRepository):
            @property
            def current_version(self) -> str:
                return "1.0"
            
            def migrate_data(self, data, from_version):
                return data
            
            def validate_data(self, data) -> bool:
                return isinstance(data, dict) and 'test_data' in data
        
        return TestRepository(str(self.test_file))
    
    def test_file_creation(self):
        """測試文件創建"""
        repo = self.create_test_repository()
        self.assertTrue(self.test_file.parent.exists())
    
    def test_load_nonexistent_file(self):
        """測試加載不存在的文件"""
        repo = self.create_test_repository()
        data = repo.load()
        
        self.assertIn('version', data)
        self.assertIn('created_at', data)
        self.assertIn('data', data)
    
    def test_save_and_load(self):
        """測試保存和加載"""
        repo = self.create_test_repository()
        
        test_data = {
            'test_data': ['item1', 'item2']
        }
        
        repo.save(test_data)
        self.assertTrue(self.test_file.exists())
        
        loaded_data = repo.load()
        self.assertEqual(loaded_data['test_data'], ['item1', 'item2'])
        self.assertIn('version', loaded_data)
        self.assertIn('last_updated', loaded_data)
    
    def test_atomic_write(self):
        """測試原子性寫入"""
        repo = self.create_test_repository()
        
        # 模擬寫入過程中的中斷
        original_method = repo._write_atomic
        
        def mock_atomic_write(data):
            temp_file = self.test_file.with_suffix(f"{self.test_file.suffix}.tmp")
            self.assertFalse(self.test_file.exists() or temp_file.exists())
            original_method(data)
            # 寫入完成後臨時文件應該消失，正式文件應該存在
            self.assertFalse(temp_file.exists())
            self.assertTrue(self.test_file.exists())
        
        repo._write_atomic = mock_atomic_write
        
        test_data = {'test_data': ['atomic_test']}
        repo.save(test_data)
    
    def test_backup_creation(self):
        """測試備份創建"""
        repo = self.create_test_repository()
        
        # 先創建原文件
        test_data = {'test_data': ['original']}
        repo.save(test_data)
        
        # 修改數據並保存
        test_data['test_data'] = ['modified']
        repo.save(test_data)
        
        # 檢查備份文件
        backups = repo.list_backups()
        self.assertGreater(len(backups), 0)
        
        # 檢查備份內容
        with open(backups[0], 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        self.assertIn('test_data', backup_data)
    
    def test_backup_cleanup(self):
        """測試備份清理"""
        repo = self.create_test_repository()
        repo.backup_count = 2  # 只保留 2 個備份
        
        # 創建多個備份
        for i in range(5):
            test_data = {'test_data': [f'version_{i}']}
            repo.save(test_data)
        
        # 檢查備份數量不超過限制
        backups = repo.list_backups()
        self.assertLessEqual(len(backups), repo.backup_count)
    
    def test_file_locking(self):
        """測試文件鎖定"""
        repo = self.create_test_repository()
        
        with repo._file_lock():
            self.assertTrue(repo._lock_acquired)
        
        self.assertFalse(repo._lock_acquired)
    
    def test_restore_from_backup(self):
        """測試從備份恢復"""
        repo = self.create_test_repository()
        
        # 創建原始數據
        original_data = {'test_data': ['original']}
        repo.save(original_data)
        
        # 修改數據
        modified_data = {'test_data': ['modified']}
        repo.save(modified_data)
        
        # 獲取備份
        backups = repo.list_backups()
        self.assertGreater(len(backups), 0)
        
        # 從備份恢復
        repo.restore_from_backup(backups[0])
        
        # 驗證恢復結果
        restored_data = repo.load()
        self.assertEqual(restored_data['test_data'], ['original'])


class TestKnowledgeRepository(unittest.TestCase):
    """知識點 Repository 測試"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "knowledge.json"
        self.repo = KnowledgeRepository(str(self.test_file))
    
    def tearDown(self):
        """清理測試環境"""
        self.temp_dir.cleanup()
    
    def create_sample_knowledge_point(self, point_id=1):
        """創建示例知識點"""
        return {
            'id': point_id,
            'key_point': '主詞動詞不一致',
            'category': 'systematic',
            'subtype': 'verb_conjugation',
            'explanation': '主詞與動詞不一致的錯誤',
            'original_phrase': 'she have',
            'correction': 'she has',
            'original_error': {
                'chinese_sentence': '她有一本書。',
                'user_answer': 'She have a book.',
                'correct_answer': 'She has a book.',
                'timestamp': '2024-01-01T10:00:00'
            },
            'review_examples': [],
            'mastery_level': 0.0,
            'mistake_count': 1,
            'correct_count': 0,
            'created_at': '2024-01-01T10:00:00',
            'last_seen': '2024-01-01T10:00:00',
            'next_review': '2024-01-02T10:00:00'
        }
    
    def test_add_knowledge_point(self):
        """測試添加知識點"""
        point = self.create_sample_knowledge_point()
        
        result = self.repo.add_knowledge_point(point)
        self.assertTrue(result)
        
        # 驗證存儲
        loaded_point = self.repo.find_by_id(1)
        self.assertIsNotNone(loaded_point)
        self.assertEqual(loaded_point['key_point'], '主詞動詞不一致')
    
    def test_duplicate_knowledge_point(self):
        """測試重複知識點處理"""
        point = self.create_sample_knowledge_point()
        
        # 第一次添加成功
        result1 = self.repo.add_knowledge_point(point)
        self.assertTrue(result1)
        
        # 第二次添加失敗（重複）
        result2 = self.repo.add_knowledge_point(point)
        self.assertFalse(result2)
    
    def test_find_by_composite_key(self):
        """測試複合鍵查找"""
        point = self.create_sample_knowledge_point()
        self.repo.add_knowledge_point(point)
        
        found = self.repo.find_by_composite_key(
            '主詞動詞不一致', 'she have', 'she has'
        )
        self.assertIsNotNone(found)
        self.assertEqual(found['id'], 1)
        
        # 測試不存在的組合
        not_found = self.repo.find_by_composite_key(
            '不存在的錯誤', 'test', 'test'
        )
        self.assertIsNone(not_found)
    
    def test_find_by_category(self):
        """測試按類別查找"""
        point1 = self.create_sample_knowledge_point(1)
        point1['category'] = 'systematic'
        point1['key_point'] = '系統性錯誤'
        point1['original_phrase'] = 'systematic_test'
        point1['correction'] = 'systematic_correct'
        
        point2 = self.create_sample_knowledge_point(2)
        point2['category'] = 'isolated'
        point2['key_point'] = '單字拼寫錯誤'
        point2['original_phrase'] = 'isolated_test'
        point2['correction'] = 'isolated_correct'
        
        self.repo.add_knowledge_point(point1)
        self.repo.add_knowledge_point(point2)
        
        systematic_points = self.repo.find_by_category('systematic')
        self.assertEqual(len(systematic_points), 1)
        self.assertEqual(systematic_points[0]['id'], 1)
        
        isolated_points = self.repo.find_by_category('isolated')
        self.assertEqual(len(isolated_points), 1)
        self.assertEqual(isolated_points[0]['id'], 2)
    
    def test_update_mastery(self):
        """測試掌握度更新"""
        point = self.create_sample_knowledge_point()
        self.repo.add_knowledge_point(point)
        
        # 測試答對時的更新
        review_example = {
            'chinese_sentence': '複習句子',
            'user_answer': '正確答案',
            'correct_answer': '正確答案',
            'timestamp': datetime.now().isoformat(),
            'is_correct': True
        }
        
        result = self.repo.update_mastery(1, True, review_example)
        self.assertTrue(result)
        
        # 驗證更新結果
        updated_point = self.repo.find_by_id(1)
        self.assertEqual(updated_point['correct_count'], 1)
        self.assertGreater(updated_point['mastery_level'], 0)
        self.assertEqual(len(updated_point['review_examples']), 1)
    
    def test_batch_update(self):
        """測試批量更新"""
        # 添加多個知識點（使用不同的複合鍵避免重複）
        for i in range(3):
            point = self.create_sample_knowledge_point(i + 1)
            point['key_point'] = f'錯誤類型{i+1}'
            point['original_phrase'] = f'phrase_{i+1}'
            point['correction'] = f'correction_{i+1}'
            self.repo.add_knowledge_point(point)
        
        # 批量更新
        updates = [
            {'id': 1, 'mastery_level': 0.5},
            {'id': 2, 'mastery_level': 0.7},
            {'id': 3, 'mastery_level': 0.3}
        ]
        
        updated_count = self.repo.batch_update(updates)
        self.assertEqual(updated_count, 3)
        
        # 驗證更新結果
        point1 = self.repo.find_by_id(1)
        self.assertEqual(point1['mastery_level'], 0.5)
        
        point2 = self.repo.find_by_id(2)
        self.assertEqual(point2['mastery_level'], 0.7)
    
    def test_statistics(self):
        """測試統計功能"""
        # 添加不同類別的知識點（使用不同的複合鍵避免重複）
        point1 = self.create_sample_knowledge_point(1)
        point1['category'] = 'systematic'
        point1['mastery_level'] = 0.2
        point1['key_point'] = '系統性錯誤'
        point1['original_phrase'] = 'systematic_phrase'
        point1['correction'] = 'systematic_correction'
        
        point2 = self.create_sample_knowledge_point(2)
        point2['category'] = 'isolated'
        point2['mastery_level'] = 0.8
        point2['key_point'] = '單一性錯誤'
        point2['original_phrase'] = 'isolated_phrase'
        point2['correction'] = 'isolated_correction'
        
        self.repo.add_knowledge_point(point1)
        self.repo.add_knowledge_point(point2)
        
        stats = self.repo.get_statistics()
        
        self.assertEqual(stats['total_points'], 2)
        self.assertEqual(stats['avg_mastery'], 0.5)
        self.assertIn('systematic', stats['category_distribution'])
        self.assertIn('isolated', stats['category_distribution'])
    
    def test_search(self):
        """測試搜尋功能"""
        point = self.create_sample_knowledge_point()
        point['key_point'] = '主詞動詞不一致測試'
        self.repo.add_knowledge_point(point)
        
        # 搜尋關鍵字
        results = self.repo.search('主詞')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], 1)
        
        # 搜尋不存在的關鍵字
        no_results = self.repo.search('不存在的關鍵字')
        self.assertEqual(len(no_results), 0)
    
    def test_version_migration(self):
        """測試版本遷移"""
        # 模擬舊版本數據（v2.0格式）
        old_data = {
            'knowledge_points': [
                {
                    'id': 1,
                    'key_point': '測試錯誤',
                    'category': 'systematic',
                    'subtype': 'test',
                    'explanation': '測試說明',
                    'original_phrase': 'test',
                    'correction': 'test_correct',
                    'examples': [
                        {
                            'chinese': '中文句子',
                            'user_answer': '用戶答案',
                            'correct': '正確答案'
                        }
                    ],
                    'mastery_level': 0.0,
                    'mistake_count': 1,
                    'correct_count': 0,
                    'created_at': '2024-01-01T10:00:00',
                    'last_seen': '2024-01-01T10:00:00',
                    'next_review': '2024-01-02T10:00:00'
                }
            ]
        }
        
        # 寫入舊格式數據
        with open(self.test_file, 'w', encoding='utf-8') as f:
            json.dump(old_data, f)
        
        # 加載數據應該觸發遷移
        migrated_data = self.repo.load()
        
        self.assertEqual(migrated_data['version'], '3.0')
        self.assertIn('migration_date', migrated_data)
        self.assertEqual(len(migrated_data['data']), 1)
        
        # 檢查遷移後的數據結構
        point = migrated_data['data'][0]
        self.assertIn('original_error', point)
        self.assertIn('review_examples', point)


class TestPracticeRepository(unittest.TestCase):
    """練習記錄 Repository 測試"""
    
    def setUp(self):
        """設置測試環境"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "practice.json"
        self.repo = PracticeRepository(str(self.test_file))
    
    def tearDown(self):
        """清理測試環境"""
        self.temp_dir.cleanup()
    
    def create_sample_practice_record(self, timestamp=None, is_correct=True):
        """創建示例練習記錄"""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        return {
            'timestamp': timestamp,
            'chinese_sentence': '她有一本書。',
            'user_answer': 'She has a book.' if is_correct else 'She have a book.',
            'is_correct': is_correct,
            'feedback': {
                'is_generally_correct': is_correct,
                'overall_suggestion': 'She has a book.',
                'error_analysis': [] if is_correct else [
                    {
                        'category': 'systematic',
                        'key_point_summary': '主詞動詞不一致',
                        'severity': 'major'
                    }
                ]
            },
            'practice_mode': 'new'
        }
    
    def test_add_practice_record(self):
        """測試添加練習記錄"""
        record = self.create_sample_practice_record()
        
        result = self.repo.add_practice_record(record)
        self.assertTrue(result)
        
        # 驗證存儲
        data = self.repo.load()
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['chinese_sentence'], '她有一本書。')
    
    def test_get_records_by_date_range(self):
        """測試按日期範圍查詢"""
        # 創建不同時間的記錄
        base_time = datetime.now()
        
        record1 = self.create_sample_practice_record(
            (base_time - timedelta(days=2)).isoformat()
        )
        record2 = self.create_sample_practice_record(
            (base_time - timedelta(days=1)).isoformat()
        )
        record3 = self.create_sample_practice_record(base_time.isoformat())
        
        self.repo.add_practice_record(record1)
        self.repo.add_practice_record(record2)
        self.repo.add_practice_record(record3)
        
        # 查詢最近1天的記錄
        recent_records = self.repo.get_records_by_date_range(
            base_time - timedelta(hours=1),
            base_time + timedelta(hours=1)
        )
        
        self.assertEqual(len(recent_records), 1)
    
    def test_get_statistics(self):
        """測試統計功能"""
        # 添加正確和錯誤記錄
        correct_record = self.create_sample_practice_record(is_correct=True)
        incorrect_record = self.create_sample_practice_record(is_correct=False)
        
        self.repo.add_practice_record(correct_record)
        self.repo.add_practice_record(incorrect_record)
        
        stats = self.repo.get_statistics()
        
        self.assertEqual(stats['total_practices'], 2)
        self.assertEqual(stats['correct_count'], 1)
        self.assertEqual(stats['incorrect_count'], 1)
        self.assertEqual(stats['accuracy'], 0.5)
    
    def test_cleanup_old_records(self):
        """測試清理舊記錄"""
        # 創建舊記錄
        old_time = datetime.now() - timedelta(days=400)
        recent_time = datetime.now() - timedelta(days=1)
        
        old_record = self.create_sample_practice_record(old_time.isoformat())
        recent_record = self.create_sample_practice_record(recent_time.isoformat())
        
        self.repo.add_practice_record(old_record)
        self.repo.add_practice_record(recent_record)
        
        # 清理超過365天的記錄
        deleted_count = self.repo.cleanup_old_records(365)
        
        self.assertEqual(deleted_count, 1)
        
        # 驗證剩餘記錄
        data = self.repo.load()
        self.assertEqual(len(data['data']), 1)
    
    def test_performance_trend(self):
        """測試表現趨勢分析"""
        base_time = datetime.now()
        
        # 創建不同天的記錄
        for i in range(3):
            date = base_time - timedelta(days=i)
            
            # 每天添加正確和錯誤記錄
            correct_record = self.create_sample_practice_record(
                date.isoformat(), True
            )
            incorrect_record = self.create_sample_practice_record(
                date.isoformat(), False
            )
            
            self.repo.add_practice_record(correct_record)
            self.repo.add_practice_record(incorrect_record)
        
        trend_data = self.repo.get_performance_trend(7)
        
        # 應該有3天的數據
        self.assertEqual(len(trend_data), 3)
        
        # 每天的準確率應該是0.5（一對一錯）
        for day_data in trend_data:
            self.assertEqual(day_data['accuracy'], 0.5)
            self.assertEqual(day_data['total_practices'], 2)
    
    def test_search_records(self):
        """測試搜尋記錄"""
        record = self.create_sample_practice_record()
        record['chinese_sentence'] = '這是特殊的測試句子'
        
        self.repo.add_practice_record(record)
        
        # 搜尋關鍵字
        results = self.repo.search_records('特殊')
        self.assertEqual(len(results), 1)
        self.assertIn('特殊', results[0]['chinese_sentence'])
        
        # 搜尋不存在的關鍵字
        no_results = self.repo.search_records('不存在')
        self.assertEqual(len(no_results), 0)


if __name__ == '__main__':
    unittest.main()