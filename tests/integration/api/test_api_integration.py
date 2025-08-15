from fastapi.testclient import TestClient

from tests.config.api_endpoints import TEST_API_ENDPOINTS
from web.main import app


def test_get_knowledge_point_not_found():
    """測試請求一個不存在的知識點"""
    client = TestClient(app)
    response = client.get(TEST_API_ENDPOINTS.get_knowledge_detail(9999))
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["error_code"] == "KNOWLEDGE_NOT_FOUND"


def test_get_knowledge_point_deleted():
    """測試請求一個已被刪除的知識點"""
    # 使用一個不存在的高ID來測試刪除情況
    client = TestClient(app)
    response = client.get(TEST_API_ENDPOINTS.get_knowledge_detail(99999))
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["error_code"] == "KNOWLEDGE_NOT_FOUND"


def test_get_knowledge_point_invalid_id():
    """測試請求一個無效格式的ID (FastAPI validation)"""
    client = TestClient(app)  # 這個測試不需要 mock，使用原始客戶端
    response = client.get(TEST_API_ENDPOINTS.KNOWLEDGE_DETAIL.replace("{point_id}", "abc"))
    assert response.status_code == 422
    json_data = response.json()
    assert json_data["detail"][0]["type"] == "int_parsing"


def test_get_knowledge_point_success():
    """測試成功獲取知識點"""
    client = TestClient(app)
    response = client.get(TEST_API_ENDPOINTS.get_knowledge_detail(1))
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["id"] == 1
    assert json_data["key_point"] == "主詞動詞不一致: she have to"
