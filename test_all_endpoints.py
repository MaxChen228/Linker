#!/usr/bin/env python
"""測試所有端點是否正常"""

from web.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 測試端點列表
endpoints = [
    ('/', 'GET', '首頁'),
    ('/practice', 'GET', '練習頁面'),
    ('/knowledge', 'GET', '知識點頁面'),
    ('/patterns', 'GET', '文法句型頁面'),
    ('/api/practice/generate', 'POST', 'API: 生成題目'),
    ('/api/practice/submit', 'POST', 'API: 提交答案'),
    ('/api/llm/last-interaction', 'GET', 'API: LLM互動記錄'),
]

print("=" * 60)
print("測試所有端點")
print("=" * 60)

for path, method, description in endpoints:
    try:
        if method == 'GET':
            response = client.get(path)
        elif method == 'POST':
            # 為 POST 請求提供基本數據
            if 'generate' in path:
                response = client.post(path, json={"mode": "new", "level": 1})
            elif 'submit' in path:
                response = client.post(path, json={
                    "chinese": "測試",
                    "english": "test",
                    "hint": ""
                })
            else:
                response = client.post(path, json={})
        
        status = "✅" if response.status_code in [200, 422] else "❌"
        print(f"{status} {description:20} ({path:30}) - {response.status_code}")
        
    except Exception as e:
        print(f"❌ {description:20} ({path:30}) - Error: {e}")

print("=" * 60)
print("測試完成！")