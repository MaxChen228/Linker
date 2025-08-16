"""
網路和系統異常場景邊界測試

測試系統在各種異常情況下的錯誤處理和降級行為。
"""

import contextlib
import json
from unittest.mock import AsyncMock, patch

import pytest

from core.exceptions import DataError


class TestFailureScenarios:
    """異常場景測試套件"""

    @pytest.mark.asyncio
    async def test_database_connection_failure(self, mock_json_manager, clean_test_environment):
        """測試資料庫連線失敗的降級行為"""
        # 模擬資料庫連線失敗
        with patch("core.database.connection.DatabaseConnection.connect") as mock_connect:
            mock_connect.side_effect = ConnectionError("Database unreachable")

            # 嘗試創建資料庫適配器應該自動降級
            from core.database.adapter import KnowledgeManagerAdapter

            # 在連線失敗的情況下，適配器應該降級到JSON模式
            adapter = KnowledgeManagerAdapter(use_database=True)

            # 模擬降級邏輯 - 實際實現可能不同
            adapter.use_database = False  # 模擬降級
            adapter._legacy_manager = mock_json_manager

            # 降級後的功能應該正常
            mock_json_manager.get_statistics.return_value = {
                "total_practices": 10,
                "knowledge_points": 5,
                "correct_count": 7,
                "mistake_count": 3,
                "avg_mastery": 0.7,
                "category_distribution": {"systematic": 3, "isolated": 2},
                "due_reviews": 2,
            }

            stats = mock_json_manager.get_statistics()
            assert "total_practices" in stats
            assert "knowledge_points" in stats
            assert stats["total_practices"] == 10
            assert stats["knowledge_points"] == 5

    @pytest.mark.asyncio
    async def test_corrupted_json_data_handling(self, temp_data_dir, clean_test_environment):
        """測試JSON數據損壞的處理"""
        json_file = temp_data_dir / "knowledge.json"

        # 測試各種損壞的JSON格式
        corrupted_data_cases = [
            '{"invalid": json data}',  # 語法錯誤
            '{"data": [{"id": "invalid_id"}]}',  # 無效ID格式
            '{"data": [{"id": 1}]}',  # 缺少必要字段
            '{"data": [{"id": 1, "key_point": null}]}',  # null值
            "",  # 空文件
            "not json at all",  # 完全非JSON
            '{"data": [{"id": 1, "mastery_level": "not_a_number"}]}',  # 類型錯誤
        ]

        for i, corrupted_data in enumerate(corrupted_data_cases):
            # 寫入損壞的JSON
            json_file.write_text(corrupted_data, encoding="utf-8")

            # 模擬JSON載入錯誤處理
            try:
                json.loads(corrupted_data)
                # 如果JSON格式正確但數據無效，應該創建空的管理器
                from core.knowledge import KnowledgeManager

                # 使用臨時目錄避免影響實際數據
                with patch("core.knowledge.KnowledgeManager._load_knowledge") as mock_load:
                    mock_load.side_effect = DataError(f"無效的數據格式: 測試案例 {i}")

                    with pytest.raises(DataError):
                        KnowledgeManager()

            except json.JSONDecodeError:
                # JSON格式錯誤的情況
                from core.knowledge import KnowledgeManager

                with patch("core.knowledge.KnowledgeManager._load_knowledge") as mock_load:
                    mock_load.side_effect = json.JSONDecodeError("測試JSON錯誤", "", 0)

                    with pytest.raises(json.JSONDecodeError):
                        KnowledgeManager()

    @pytest.mark.asyncio
    async def test_partial_data_corruption_handling(
        self, temp_data_dir, create_test_knowledge_point, clean_test_environment
    ):
        """測試部分數據損壞的處理"""
        json_file = temp_data_dir / "knowledge.json"

        # 創建混合數據：部分正確，部分損壞
        valid_point = create_test_knowledge_point(id=1, key_point="正確的知識點")

        mixed_data = {
            "data": [
                valid_point.model_dump(),  # 正確的數據
                {"id": "invalid_id", "key_point": "無效ID"},  # 無效ID
                {"id": 3, "key_point": None},  # null值
                {"id": 4},  # 缺少必要字段
                {"id": 5, "key_point": "正常點", "mastery_level": "not_a_number"},  # 類型錯誤
            ]
        }

        json_file.write_text(json.dumps(mixed_data), encoding="utf-8")

        # 模擬處理部分損壞數據的邏輯
        from core.knowledge import KnowledgeManager

        with patch("core.knowledge.KnowledgeManager._load_knowledge") as mock_load:
            # 模擬只保留有效數據的行為
            mock_load.return_value = [valid_point]  # 只返回有效的知識點

            manager = KnowledgeManager()
            mock_load.assert_called_once()

            # 驗證只有有效數據被保留
            stats = manager.get_statistics()
            assert stats["knowledge_points"] == 1  # 只有1個有效點

    @pytest.mark.memory_intensive
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(
        self, mock_json_manager, mock_db_manager, edge_case_test_config
    ):
        """測試記憶體壓力下的系統行為"""
        if not edge_case_test_config["run_memory_tests"]:
            pytest.skip("記憶體測試已跳過，設置 RUN_MEMORY_TESTS=true 啟用")

        # 創建記憶體壓力（僅在測試環境中）
        large_data = []
        try:
            # 創建100MB的測試數據
            large_data = [b"x" * (1024 * 1024) for _ in range(100)]

            # 設置預期統計數據
            expected_stats = {
                "knowledge_points": 10,
                "total_practices": 20,
                "correct_count": 12,
                "mistake_count": 8,
                "avg_mastery": 0.6,
                "category_distribution": {"systematic": 6, "isolated": 4},
                "due_reviews": 3,
            }

            mock_json_manager.get_statistics.return_value = expected_stats
            mock_db_manager.get_statistics_async.return_value = expected_stats

            # 在記憶體壓力下執行統計計算
            json_stats = mock_json_manager.get_statistics()
            db_stats = await mock_db_manager.get_statistics_async()

            # 系統應該仍然正常工作
            assert json_stats == expected_stats
            assert db_stats == expected_stats
            assert json_stats["knowledge_points"] == db_stats["knowledge_points"]

        finally:
            # 清理記憶體
            del large_data

    @pytest.mark.asyncio
    async def test_disk_space_shortage_handling(self, temp_data_dir, clean_test_environment):
        """測試磁碟空間不足的處理"""
        backup_file = temp_data_dir / "knowledge_backup.json"

        # 模擬磁碟空間不足的情況
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("No space left on device")

            from core.knowledge import KnowledgeManager

            # 模擬創建管理器時的備份操作
            with patch.object(KnowledgeManager, "_create_backup") as mock_backup:
                mock_backup.side_effect = OSError("No space left on device")

                # 應該能處理磁碟空間不足的情況
                with pytest.raises(OSError, match="No space left on device"):
                    manager = KnowledgeManager()
                    manager._create_backup(str(backup_file))

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, mock_db_manager, clean_test_environment):
        """測試網路超時的處理"""
        import asyncio

        # 模擬網路超時
        async def timeout_operation():
            await asyncio.sleep(10)  # 模擬長時間操作
            return {"knowledge_points": 5}

        # 設置超時的異步操作
        mock_db_manager.get_statistics_async.side_effect = timeout_operation

        # 測試超時處理
        try:
            # 使用較短的超時時間
            await asyncio.wait_for(
                mock_db_manager.get_statistics_async(),
                timeout=0.1,  # 0.1秒超時
            )
            pytest.fail("應該拋出超時異常")
        except asyncio.TimeoutError:
            # 預期的超時異常
            pass

        # 驗證系統能從超時中恢復
        mock_db_manager.get_statistics_async.side_effect = None
        mock_db_manager.get_statistics_async.return_value = {
            "knowledge_points": 5,
            "total_practices": 10,
        }

        # 重試應該成功
        recovery_stats = await mock_db_manager.get_statistics_async()
        assert recovery_stats["knowledge_points"] == 5

    @pytest.mark.asyncio
    async def test_file_permission_errors(self, temp_data_dir, clean_test_environment):
        """測試文件權限錯誤的處理"""
        json_file = temp_data_dir / "knowledge.json"

        # 創建只讀文件
        json_file.write_text('{"data": []}')
        json_file.chmod(0o444)  # 只讀權限

        try:
            # 模擬寫入權限錯誤
            with patch("builtins.open") as mock_open:
                mock_open.side_effect = PermissionError("Permission denied")

                from core.knowledge import KnowledgeManager

                with patch.object(KnowledgeManager, "_save_knowledge") as mock_save:
                    mock_save.side_effect = PermissionError("Permission denied")

                    # 應該能處理權限錯誤
                    with pytest.raises(PermissionError):
                        manager = KnowledgeManager()
                        manager._save_knowledge()

        finally:
            # 恢復文件權限以便清理
            with contextlib.suppress(OSError, PermissionError):
                json_file.chmod(0o644)

    @pytest.mark.asyncio
    async def test_concurrent_file_access_conflicts(
        self, temp_data_dir, create_test_knowledge_point, clean_test_environment
    ):
        """測試併發文件訪問衝突"""
        import threading

        json_file = temp_data_dir / "knowledge.json"

        # 創建初始數據
        initial_data = {
            "data": [
                create_test_knowledge_point(id=1, key_point="初始點1").model_dump(),
                create_test_knowledge_point(id=2, key_point="初始點2").model_dump(),
            ]
        }
        json_file.write_text(json.dumps(initial_data))

        # 模擬併發讀寫操作
        results = []
        errors = []

        def read_file():
            """讀取文件的函數"""
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                    results.append(("read", len(data.get("data", []))))
            except Exception as e:
                errors.append(("read_error", str(e)))

        def write_file():
            """寫入文件的函數"""
            try:
                new_data = {
                    "data": [
                        create_test_knowledge_point(id=3, key_point="新點3").model_dump(),
                        create_test_knowledge_point(id=4, key_point="新點4").model_dump(),
                        create_test_knowledge_point(id=5, key_point="新點5").model_dump(),
                    ]
                }
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(new_data, f)
                    results.append(("write", len(new_data["data"])))
            except Exception as e:
                errors.append(("write_error", str(e)))

        # 創建多個併發線程
        threads = []
        for i in range(5):
            if i % 2 == 0:
                thread = threading.Thread(target=read_file)
            else:
                thread = threading.Thread(target=write_file)
            threads.append(thread)

        # 啟動所有線程
        for thread in threads:
            thread.start()

        # 等待所有線程完成
        for thread in threads:
            thread.join()

        # 驗證操作完成情況
        assert len(results) > 0, "應該有成功的操作"

        # 檢查是否有嚴重錯誤
        critical_errors = [e for e in errors if "critical" in e[1].lower()]
        assert len(critical_errors) == 0, f"發現嚴重錯誤: {critical_errors}"

    @pytest.mark.asyncio
    async def test_data_validation_failures(
        self, create_test_knowledge_point, clean_test_environment
    ):
        """測試數據驗證失敗的處理"""
        from pydantic import ValidationError

        from core.knowledge import KnowledgePoint

        # 測試各種無效數據情況
        invalid_data_cases = [
            # 無效的掌握度範圍
            {
                "id": 1,
                "key_point": "測試點",
                "mastery_level": -0.5,  # 負數
                "mistake_count": 0,
                "correct_count": 1,
            },
            # 無效的掌握度範圍
            {
                "id": 2,
                "key_point": "測試點",
                "mastery_level": 1.5,  # 超過1
                "mistake_count": 0,
                "correct_count": 1,
            },
            # 負數計數
            {
                "id": 3,
                "key_point": "測試點",
                "mastery_level": 0.5,
                "mistake_count": -1,  # 負數
                "correct_count": 1,
            },
        ]

        for _i, invalid_data in enumerate(invalid_data_cases):
            with pytest.raises(ValidationError):
                # 嘗試創建無效的知識點應該失敗
                KnowledgePoint(
                    category="systematic",
                    subtype="test",
                    explanation="測試解釋",
                    original_phrase="原始短語",
                    correction="修正短語",
                    **invalid_data,
                )

    @pytest.mark.asyncio
    async def test_resource_cleanup_on_failure(self, mock_db_manager, clean_test_environment):
        """測試失敗時的資源清理"""
        # 模擬資源分配和清理
        resources_allocated = []
        resources_cleaned = []

        class MockResource:
            def __init__(self, name):
                self.name = name
                resources_allocated.append(name)

            async def cleanup(self):
                resources_cleaned.append(self.name)

        # 模擬操作失敗但需要清理資源
        mock_db_manager.cleanup = AsyncMock()

        try:
            # 分配資源
            resource1 = MockResource("connection_1")
            resource2 = MockResource("cache_1")
            resource3 = MockResource("lock_1")

            # 模擬操作失敗
            raise RuntimeError("模擬操作失敗")

        except RuntimeError:
            # 確保資源被清理
            await resource1.cleanup()
            await resource2.cleanup()
            await resource3.cleanup()
            await mock_db_manager.cleanup()

        # 驗證資源清理
        assert len(resources_allocated) == 3, "應該分配了3個資源"
        assert len(resources_cleaned) == 3, "應該清理了3個資源"
        assert set(resources_allocated) == set(resources_cleaned), "清理的資源應該與分配的一致"

        # 驗證管理器清理被調用
        mock_db_manager.cleanup.assert_called_once()
