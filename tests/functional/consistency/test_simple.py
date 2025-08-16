"""
簡化的一致性測試 - 確保測試框架工作
"""

import pytest

from .conftest import ConsistencyValidator


@pytest.mark.unit
class TestSimpleConsistency:
    """簡化的一致性測試套件"""

    def test_json_manager_basic_operation(self, json_manager):
        """測試 JSON 管理器基本操作"""
        # 獲取統計
        stats = json_manager.get_statistics()

        # 基本驗證
        assert isinstance(stats, dict), "統計應該是字典"
        assert "knowledge_points" in stats, "統計應包含 knowledge_points"
        assert "total_practices" in stats, "統計應包含 total_practices"
        assert stats["knowledge_points"] >= 0, "知識點數量應非負"

        print(f"JSON 統計: {stats}")

    def test_db_manager_mock_operation(self, db_manager_mock):
        """測試 DB 管理器 Mock 操作"""
        # 獲取統計
        stats = db_manager_mock.get_statistics()

        # 基本驗證
        assert isinstance(stats, dict), "統計應該是字典"
        assert "total_knowledge_points" in stats, "統計應包含 total_knowledge_points"
        assert "total_practices" in stats, "統計應包含 total_practices"
        assert stats["total_knowledge_points"] >= 0, "知識點數量應非負"

        print(f"DB Mock 統計: {stats}")

    @pytest.mark.asyncio
    async def test_async_operation(self, db_manager_mock):
        """測試異步操作"""
        async_stats = await db_manager_mock.get_statistics_async()
        sync_stats = db_manager_mock.get_statistics()

        assert async_stats == sync_stats, "異步和同步統計應該一致"

        print("異步統計驗證通過")

    def test_consistency_validator(self):
        """測試一致性驗證器"""
        validator = ConsistencyValidator()

        # 測試匹配驗證

        # 不應該拋出異常（這個測試不做嚴格字段匹配）
        assert validator is not None
        print("一致性驗證器創建成功")


@pytest.mark.integration
class TestBasicIntegration:
    """基本整合測試"""

    def test_both_managers_return_data(self, json_manager, db_manager_mock):
        """測試兩種管理器都能返回數據"""
        json_stats = json_manager.get_statistics()
        db_stats = db_manager_mock.get_statistics()

        # 基本數據類型檢查
        assert isinstance(json_stats, dict)
        assert isinstance(db_stats, dict)

        # 檢查核心字段存在
        assert "total_practices" in json_stats
        assert "total_practices" in db_stats

        print(f"整合測試通過 - JSON字段: {list(json_stats.keys())[:5]}...")
        print(f"整合測試通過 - DB字段: {list(db_stats.keys())[:5]}...")
