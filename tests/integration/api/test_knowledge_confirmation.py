"""
測試知識點確認功能的整合測試
測試批改後的知識點確認/刪除機制
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from web.main import app


class TestKnowledgeConfirmation:
    """知識點確認功能測試套件"""

    @pytest.fixture
    def client(self):
        """創建測試客戶端"""
        return TestClient(app)

    @pytest.fixture
    def mock_grade_result(self):
        """模擬批改結果數據"""
        return {
            "success": True,
            "score": 70,
            "is_generally_correct": False,
            "feedback": "句子基本正確，但有一些小錯誤",
            "error_analysis": [
                {
                    "category": "systematic",
                    "key_point_summary": "時態使用錯誤",
                    "explanation": "應該使用過去式",
                    "original_phrase": "I go there yesterday",
                    "correction": "I went there yesterday",
                },
                {
                    "category": "isolated",
                    "key_point_summary": "冠詞缺失",
                    "explanation": "需要加上冠詞",
                    "original_phrase": "beautiful day",
                    "correction": "a beautiful day",
                },
            ],
        }

    def test_grade_answer_returns_pending_points(self, client, mock_grade_result):
        """測試批改答案時返回待確認的知識點（而非自動保存）"""

        with patch("web.routers.practice.get_ai_service") as mock_ai:
            # 模擬 AI 服務返回批改結果
            mock_ai_service = MagicMock()
            mock_ai_service.grade_translation.return_value = mock_grade_result
            mock_ai.return_value = mock_ai_service

            # 發送批改請求
            response = client.post(
                "/api/grade-answer",
                json={
                    "chinese": "我昨天去了那裡",
                    "english": "I go there yesterday",
                    "mode": "new",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # 檢查是否返回了待確認的知識點
            assert "pending_knowledge_points" in data
            assert len(data["pending_knowledge_points"]) == 2

            # 檢查待確認點的結構
            pending_point = data["pending_knowledge_points"][0]
            assert "id" in pending_point
            assert "error" in pending_point
            assert pending_point["error"]["category"] == "systematic"
            assert pending_point["chinese_sentence"] == "我昨天去了那裡"
            assert pending_point["user_answer"] == "I go there yesterday"

            # 確認沒有自動保存標記
            assert data.get("auto_save", True) == False

    def test_confirm_knowledge_points_success(self, client):
        """測試確認知識點API"""

        with patch("web.routers.practice.get_knowledge_manager_async_dependency") as mock_km:
            # 模擬知識管理器
            mock_knowledge = MagicMock()
            mock_knowledge.add_knowledge_point_from_error.return_value = 123
            mock_km.return_value = mock_knowledge

            # 發送確認請求
            response = client.post(
                "/api/confirm-knowledge-points",
                json={
                    "confirmed_points": [
                        {
                            "id": "temp_001",
                            "chinese_sentence": "我昨天去了那裡",
                            "user_answer": "I go there yesterday",
                            "error": {
                                "category": "systematic",
                                "key_point_summary": "時態使用錯誤",
                                "explanation": "應該使用過去式",
                                "original_phrase": "I go",
                                "correction": "I went",
                            },
                            "correct_answer": "I went there yesterday",
                        }
                    ]
                },
            )

            assert response.status_code == 200
            data = response.json()

            # 檢查返回結果
            assert data["success"] == True
            assert data["confirmed_count"] == 1
            assert 123 in data["point_ids"]

            # 確認調用了知識管理器
            mock_knowledge.add_knowledge_point_from_error.assert_called_once()

    def test_confirm_multiple_points(self, client):
        """測試批量確認多個知識點"""

        with patch("web.routers.practice.get_knowledge_manager_async_dependency") as mock_km:
            mock_knowledge = MagicMock()
            mock_knowledge.add_knowledge_point_from_error.side_effect = [100, 101, 102]
            mock_km.return_value = mock_knowledge

            # 發送批量確認請求
            response = client.post(
                "/api/confirm-knowledge-points",
                json={
                    "confirmed_points": [
                        {
                            "id": f"temp_{i:03d}",
                            "chinese_sentence": f"測試句子{i}",
                            "user_answer": f"Test sentence {i}",
                            "error": {
                                "category": "systematic",
                                "key_point_summary": f"錯誤{i}",
                                "explanation": f"解釋{i}",
                            },
                            "correct_answer": f"Correct sentence {i}",
                        }
                        for i in range(3)
                    ]
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["confirmed_count"] == 3
            assert data["point_ids"] == [100, 101, 102]

            # 確認調用了3次
            assert mock_knowledge.add_knowledge_point_from_error.call_count == 3

    def test_confirm_empty_points_list(self, client):
        """測試確認空列表的情況"""

        response = client.post("/api/confirm-knowledge-points", json={"confirmed_points": []})

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert data["confirmed_count"] == 0
        assert data["point_ids"] == []

    def test_grade_answer_with_auto_save_config(self, client, mock_grade_result):
        """測試當配置為自動保存時的行為"""

        with patch("core.config.AUTO_SAVE_KNOWLEDGE_POINTS", True):
            with patch("web.routers.practice.get_ai_service") as mock_ai:
                with patch(
                    "web.routers.practice.get_knowledge_manager_async_dependency"
                ) as mock_km:
                    # 模擬服務
                    mock_ai_service = MagicMock()
                    mock_ai_service.grade_translation.return_value = mock_grade_result
                    mock_ai.return_value = mock_ai_service

                    # 創建一個異步 Mock
                    from unittest.mock import AsyncMock
                    mock_knowledge = MagicMock()
                    # 模擬 _save_mistake_async 方法為異步方法
                    mock_knowledge._save_mistake_async = AsyncMock()
                    mock_knowledge.save_mistake = MagicMock()
                    mock_km.return_value = mock_knowledge

                    # 發送批改請求
                    response = client.post(
                        "/api/grade-answer",
                        json={
                            "chinese": "我昨天去了那裡",
                            "english": "I go there yesterday",
                            "mode": "new",
                        },
                    )

                    assert response.status_code == 200
                    data = response.json()

                    # 當自動保存開啟時，應該調用 save_mistake
                    if hasattr(mock_knowledge, "_save_mistake_async"):
                        mock_knowledge._save_mistake_async.assert_called_once()
                    elif hasattr(mock_knowledge, "save_mistake"):
                        mock_knowledge.save_mistake.assert_called_once()

                    # 不應該返回待確認的知識點
                    assert data.get("auto_save", False) == True

    @pytest.mark.asyncio
    async def test_knowledge_manager_add_from_error_method(self):
        """測試知識管理器的 add_knowledge_point_from_error 方法"""
        from core.knowledge import KnowledgeManager

        # 創建知識管理器實例
        km = KnowledgeManager()

        # 測試新增方法是否存在
        assert hasattr(km, "add_knowledge_point_from_error"), (
            "KnowledgeManager 缺少 add_knowledge_point_from_error 方法"
        )

        # 如果方法存在，測試其功能
        if hasattr(km, "add_knowledge_point_from_error"):
            error_data = {
                "category": "systematic",
                "key_point_summary": "測試錯誤",
                "explanation": "這是一個測試",
                "original_phrase": "test",
                "correction": "test corrected",
            }

            point_id = km.add_knowledge_point_from_error(
                chinese_sentence="測試句子",
                user_answer="Test sentence",
                error=error_data,
                correct_answer="Correct test sentence",
            )

            # 檢查返回的ID
            assert isinstance(point_id, int)
            assert point_id > 0

            # 檢查知識點是否真的被添加
            point = km.get_knowledge_point(point_id)
            assert point is not None
            assert point.key_point == error_data["key_point_summary"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
