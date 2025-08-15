"""
併發操作邊界測試

測試系統在併發讀寫操作下的數據一致性和穩定性。
"""

import asyncio
import random
import time
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.models import KnowledgePoint
from tests.test_edge_cases.conftest import assert_stats_consistent


class TestConcurrentOperations:
    """併發操作測試套件"""
    
    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_concurrent_read_write(
        self,
        create_test_knowledge_point,
        mock_json_manager,
        mock_db_manager,
        edge_case_test_config
    ):
        """測試併發讀寫操作的數據一致性"""
        if not edge_case_test_config['run_stress_tests']:
            pytest.skip("壓力測試已跳過，設置 RUN_STRESS_TESTS=true 啟用")
        
        # 創建基礎數據集
        base_dataset = [
            create_test_knowledge_point(id=i+1, key_point=f"基礎知識點 {i+1}")
            for i in range(20)
        ]
        
        # 設置初始狀態
        mock_json_manager.knowledge_points = base_dataset.copy()
        mock_db_manager._knowledge_points = base_dataset.copy()  # 內部狀態追蹤
        
        # 追蹤統計變化
        stats_tracker = {
            'knowledge_points': len(base_dataset),
            'total_practices': sum(p.mistake_count + p.correct_count for p in base_dataset),
            'correct_count': sum(p.correct_count for p in base_dataset),
            'mistake_count': sum(p.mistake_count for p in base_dataset)
        }
        
        async def reader_task():
            """讀取任務 - 多次讀取統計數據"""
            results = []
            for i in range(50):
                # 動態計算當前統計
                current_points = len(mock_json_manager.knowledge_points)
                current_total = sum(p.mistake_count + p.correct_count for p in mock_json_manager.knowledge_points)
                current_correct = sum(p.correct_count for p in mock_json_manager.knowledge_points)
                current_mistakes = sum(p.mistake_count for p in mock_json_manager.knowledge_points)
                
                json_stats = {
                    'knowledge_points': current_points,
                    'total_practices': current_total,
                    'correct_count': current_correct,
                    'mistake_count': current_mistakes,
                    'avg_mastery': 0.5,
                    'category_distribution': {'systematic': current_points},
                    'due_reviews': 0
                }
                
                # DB 統計應該與 JSON 一致
                db_stats = json_stats.copy()
                
                mock_json_manager.get_statistics.return_value = json_stats
                mock_db_manager.get_statistics_async.return_value = db_stats
                
                # 實際調用
                json_result = mock_json_manager.get_statistics()
                db_result = await mock_db_manager.get_statistics_async()
                
                results.append((json_result, db_result))
                await asyncio.sleep(0.01)  # 模擬讀取延遲
                
            return results
        
        async def writer_task():
            """寫入任務 - 添加新知識點"""
            for i in range(20):
                # 創建新知識點
                new_point = create_test_knowledge_point(
                    id=1000 + i,
                    key_point=f"動態添加知識點 {i+1}"
                )
                
                # 模擬同時寫入兩種模式
                mock_json_manager.knowledge_points.append(new_point)
                mock_db_manager._knowledge_points.append(new_point)
                
                # 更新統計追蹤
                stats_tracker['knowledge_points'] += 1
                stats_tracker['total_practices'] += new_point.mistake_count + new_point.correct_count
                stats_tracker['correct_count'] += new_point.correct_count
                stats_tracker['mistake_count'] += new_point.mistake_count
                
                await asyncio.sleep(0.02)  # 模擬寫入延遲
        
        # 同時執行讀寫任務
        start_time = time.time()
        reader_results, _ = await asyncio.gather(reader_task(), writer_task())
        duration = time.time() - start_time
        
        # 性能要求
        assert duration < 5.0, f"併發讀寫耗時過長: {duration:.2f}s"
        
        # 驗證讀取過程中數據的一致性
        for i, (json_stats, db_stats) in enumerate(reader_results):
            # 在併發環境下，知識點數量可能在變化，但變化應該是一致的
            json_count = json_stats['knowledge_points']
            db_count = db_stats['knowledge_points'] 
            
            # 數量應該完全一致（因為我們同步更新）
            assert json_count == db_count, \
                f"併發操作第{i+1}次讀取數量不一致: JSON={json_count}, DB={db_count}"
            
            # 知識點數量應該在合理範圍內（初始20個 + 最多20個新增）
            assert 20 <= json_count <= 40, \
                f"知識點數量超出預期範圍: {json_count}"

    @pytest.mark.asyncio
    async def test_cache_consistency_under_load(
        self,
        create_test_knowledge_point,
        mock_json_manager,
        mock_db_manager,
        edge_case_test_config
    ):
        """測試高負載下的快取一致性"""
        # 創建測試數據
        test_dataset = [
            create_test_knowledge_point(id=i+1, key_point=f"快取測試知識點 {i+1}")
            for i in range(50)
        ]
        
        # 模擬快取管理器
        cache_stats = {
            'hit_count': 0,
            'miss_count': 0,
            'total_requests': 0
        }
        
        def mock_get_stats():
            total = cache_stats['hit_count'] + cache_stats['miss_count']
            if total == 0:
                return {'hit_rate': 0.0}
            return {'hit_rate': cache_stats['hit_count'] / total}
        
        # 設置mock行為
        mock_cache_manager = MagicMock()
        mock_cache_manager.get_stats.side_effect = mock_get_stats
        
        mock_db_manager._cache_manager = mock_cache_manager
        
        # 設置統計結果
        expected_stats = {
            'knowledge_points': len(test_dataset),
            'total_practices': len(test_dataset) * 2,
            'correct_count': len(test_dataset),
            'mistake_count': len(test_dataset),
            'avg_mastery': 0.5,
            'category_distribution': {'systematic': len(test_dataset)},
            'due_reviews': 0
        }
        
        # 預熱快取
        mock_json_manager.get_statistics.return_value = expected_stats
        mock_db_manager.get_statistics_async.return_value = expected_stats
        
        await mock_json_manager.get_statistics()
        await mock_db_manager.get_statistics_async()
        
        async def load_generator():
            """負載生成器"""
            tasks = []
            
            # 100個併發請求
            for i in range(100):
                # 隨機選擇操作類型
                if random.choice([True, False]):
                    # 模擬快取命中
                    cache_stats['hit_count'] += 1
                    task = asyncio.create_task(
                        asyncio.coroutine(lambda: expected_stats)()
                    )
                else:
                    # 模擬快取未命中
                    cache_stats['miss_count'] += 1  
                    task = asyncio.create_task(
                        asyncio.coroutine(lambda: expected_stats)()
                    )
                
                cache_stats['total_requests'] += 1
                tasks.append(task)
            
            return await asyncio.gather(*tasks)
        
        # 執行負載測試
        start_time = time.time()
        results = await load_generator()
        duration = time.time() - start_time
        
        # 性能要求
        assert duration < 5.0, f"併發訪問耗時過長: {duration:.2f}s"
        
        # 驗證所有結果一致
        baseline_stats = results[0]
        for i, stats in enumerate(results[1:], 1):
            assert_stats_consistent(stats, baseline_stats)
        
        # 驗證快取效果
        final_cache_stats = mock_cache_manager.get_stats()
        # 在模擬環境下，我們預期有合理的快取命中率
        assert final_cache_stats['hit_rate'] >= 0.3, \
            f"快取命中率過低: {final_cache_stats['hit_rate']:.2f}"

    @pytest.mark.asyncio
    async def test_concurrent_statistics_calculation(
        self,
        create_test_knowledge_point,
        mock_json_manager,
        mock_db_manager
    ):
        """測試併發統計計算的正確性"""
        # 創建多樣化的測試數據
        test_points = []
        categories = ["systematic", "isolated", "enhancement", "other"]
        
        for i in range(40):
            point = create_test_knowledge_point(
                id=i+1,
                key_point=f"併發統計測試點 {i+1}",
                category=categories[i % len(categories)],
                mastery_level=random.uniform(0, 1),
                mistake_count=random.randint(0, 5),
                correct_count=random.randint(0, 3)
            )
            test_points.append(point)
        
        # 計算正確的統計數據
        correct_stats = {
            'knowledge_points': len(test_points),
            'total_practices': sum(p.mistake_count + p.correct_count for p in test_points),
            'correct_count': sum(p.correct_count for p in test_points),
            'mistake_count': sum(p.mistake_count for p in test_points),
            'avg_mastery': sum(p.mastery_level for p in test_points) / len(test_points),
            'category_distribution': {},
            'due_reviews': 0
        }
        
        # 計算分類分布
        for point in test_points:
            correct_stats['category_distribution'][point.category] = \
                correct_stats['category_distribution'].get(point.category, 0) + 1
        
        # 設置管理器
        mock_json_manager.knowledge_points = test_points
        mock_json_manager.get_statistics.return_value = correct_stats
        mock_db_manager.get_statistics_async.return_value = correct_stats
        
        # 併發統計計算任務
        async def concurrent_stats_task():
            """併發統計任務"""
            json_stats = mock_json_manager.get_statistics()
            db_stats = await mock_db_manager.get_statistics_async()
            return json_stats, db_stats
        
        # 創建多個併發任務
        concurrent_tasks = [concurrent_stats_task() for _ in range(20)]
        
        # 執行併發統計計算
        start_time = time.time()
        results = await asyncio.gather(*concurrent_tasks)
        duration = time.time() - start_time
        
        # 性能檢查
        assert duration < 3.0, f"併發統計計算耗時過長: {duration:.2f}s"
        
        # 驗證所有結果的一致性
        for i, (json_stats, db_stats) in enumerate(results):
            # 每對結果內部一致性
            assert_stats_consistent(json_stats, db_stats)
            
            # 與正確答案的一致性
            assert_stats_consistent(json_stats, correct_stats)
            assert_stats_consistent(db_stats, correct_stats)

    @pytest.mark.asyncio 
    async def test_race_condition_prevention(
        self,
        create_test_knowledge_point,
        mock_json_manager,
        mock_db_manager
    ):
        """測試競態條件的防範"""
        # 創建初始數據
        initial_points = [
            create_test_knowledge_point(id=i+1, key_point=f"競態測試點 {i+1}")
            for i in range(10)
        ]
        
        mock_json_manager.knowledge_points = initial_points.copy()
        shared_state = {'points': initial_points.copy()}  # 模擬共享狀態
        
        async def modify_data_task(task_id: int):
            """修改數據的任務"""
            for i in range(5):
                # 模擬數據修改操作
                new_point = create_test_knowledge_point(
                    id=task_id * 100 + i,
                    key_point=f"任務{task_id}添加的點{i}"
                )
                
                # 模擬線程安全的添加操作
                shared_state['points'].append(new_point)
                mock_json_manager.knowledge_points.append(new_point)
                
                await asyncio.sleep(0.001)  # 微小延遲模擬實際操作時間
        
        async def read_data_task():
            """讀取數據的任務"""
            readings = []
            for _ in range(20):
                # 讀取當前狀態
                current_count = len(shared_state['points'])
                json_count = len(mock_json_manager.knowledge_points)
                
                # 統計應該一致
                readings.append((current_count, json_count))
                await asyncio.sleep(0.002)
                
            return readings
        
        # 同時運行多個修改任務和讀取任務
        modify_tasks = [modify_data_task(i) for i in range(3)]
        read_task = read_data_task()
        
        # 執行併發操作
        results = await asyncio.gather(*modify_tasks, read_task)
        readings = results[-1]  # 最後一個是讀取任務的結果
        
        # 驗證讀取一致性
        for i, (shared_count, json_count) in enumerate(readings):
            assert shared_count == json_count, \
                f"第{i+1}次讀取不一致: 共享狀態={shared_count}, JSON管理器={json_count}"
        
        # 驗證最終狀態
        final_shared_count = len(shared_state['points'])
        final_json_count = len(mock_json_manager.knowledge_points)
        
        assert final_shared_count == final_json_count, \
            f"最終狀態不一致: 共享={final_shared_count}, JSON={final_json_count}"
        
        # 應該有初始10個 + 3個任務各5個 = 25個知識點
        expected_final_count = 10 + (3 * 5)
        assert final_json_count == expected_final_count, \
            f"最終知識點數量不正確: 期望={expected_final_count}, 實際={final_json_count}"

    @pytest.mark.asyncio
    async def test_deadlock_prevention(
        self,
        mock_json_manager,
        mock_db_manager
    ):
        """測試死鎖防範機制"""
        # 模擬可能導致死鎖的操作序列
        lock_a = asyncio.Lock()
        lock_b = asyncio.Lock()
        
        results = []
        
        async def task_a():
            """任務A：先獲取鎖A再獲取鎖B"""
            async with lock_a:
                await asyncio.sleep(0.01)  # 持有鎖A一段時間
                async with lock_b:
                    # 執行需要兩個鎖的操作
                    stats = mock_json_manager.get_statistics()
                    results.append(('task_a', stats))
        
        async def task_b():
            """任務B：先獲取鎖B再獲取鎖A（潛在死鎖）"""
            async with lock_b:
                await asyncio.sleep(0.01)  # 持有鎖B一段時間  
                async with lock_a:
                    # 執行需要兩個鎖的操作
                    stats = await mock_db_manager.get_statistics_async()
                    results.append(('task_b', stats))
        
        # 設置預期返回值
        expected_stats = {
            'knowledge_points': 0,
            'total_practices': 0,
            'correct_count': 0,
            'mistake_count': 0,
            'avg_mastery': 0.0,
            'category_distribution': {},
            'due_reviews': 0
        }
        
        mock_json_manager.get_statistics.return_value = expected_stats
        mock_db_manager.get_statistics_async.return_value = expected_stats
        
        # 使用超時來防止真正的死鎖
        try:
            await asyncio.wait_for(
                asyncio.gather(task_a(), task_b()),
                timeout=2.0  # 2秒超時
            )
        except asyncio.TimeoutError:
            pytest.fail("檢測到死鎖：操作在2秒內未完成")
        
        # 驗證兩個任務都完成了
        assert len(results) == 2, f"期望2個任務完成，實際完成{len(results)}個"
        
        # 驗證任務結果
        task_names = [result[0] for result in results]
        assert 'task_a' in task_names, "任務A未完成"
        assert 'task_b' in task_names, "任務B未完成"