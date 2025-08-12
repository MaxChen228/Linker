#!/usr/bin/env python
"""測試應用程式是否正常運行"""

from web.main import app
import traceback

try:
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.get('/')
    
    print(f'Status: {response.status_code}')
    
    if response.status_code != 200:
        print(f'Response text: {response.text}')
        
        # 測試其他端點
        test_endpoints = ['/practice', '/knowledge', '/patterns']
        for endpoint in test_endpoints:
            try:
                r = client.get(endpoint)
                print(f'{endpoint}: {r.status_code}')
            except Exception as e:
                print(f'{endpoint}: Error - {e}')
                
except Exception as e:
    print(f'Error: {e}')
    traceback.print_exc()