# Linker 測試框架文檔

## 概述

本測試框架為 Linker 專案提供完整的測試基礎設施，支援單元測試、整合測試和端到端測試。

## 框架結構

```
tests/
├── conftest.py              # 全局測試配置和 fixtures
├── factories/               # 測試數據工廠
│   ├── knowledge_factory.py     # 知識點測試數據
│   ├── practice_factory.py      # 練習記錄測試數據
│   ├── ai_response_factory.py   # AI 回應測試數據
│   └── user_input_factory.py    # 用戶輸入測試數據
├── mocks/                   # Mock 對象系統
│   ├── mock_ai_service.py       # AI 服務 Mock
│   ├── mock_file_operations.py  # 文件操作 Mock
│   ├── mock_repositories.py     # Repository Mock
│   └── mock_external_apis.py    # 外部 API Mock
├── utils/                   # 測試工具
│   ├── test_helpers.py          # 輔助函數
│   ├── test_assertions.py       # 自定義斷言
│   └── test_cleanup.py          # 清理工具
├── unit/                    # 單元測試
├── integration/             # 整合測試
└── fixtures/                # 測試固定數據
```

## 主要特性

### 1. 豐富的測試數據工廠

```python
from tests.factories import KnowledgePointFactory, create_systematic_knowledge_point

# 基本工廠使用
kp = KnowledgePointFactory.build()

# 專門化知識點
systematic_kp = create_systematic_knowledge_point()

# 批量創建
kps = KnowledgePointFactory.build_batch(10)

# 建構器模式
from tests.factories.knowledge_factory import KnowledgePointTestDataBuilder

kp = (KnowledgePointTestDataBuilder()
      .with_category("systematic")
      .with_mastery_level(0.8)
      .needs_review()
      .build())
```

### 2. 強大的 Mock 系統

```python
from tests.mocks import create_mock_ai_service, MockKnowledgeRepository

# 創建不同行為的 Mock
ai_service = create_mock_ai_service("unreliable")  # 30% 失敗率
repo = MockKnowledgeRepository()

# 設置自定義回應
ai_service.set_error_rate(0.1)
repo.set_error_rate(save_error_rate=0.2)
```

### 3. 自定義斷言

```python
from tests.utils import (
    assert_knowledge_point_valid,
    assert_response_success,
    assert_ai_response_valid
)

# 驗證知識點數據完整性
assert_knowledge_point_valid(kp, strict=True)

# 驗證 API 回應格式
assert_ai_response_valid(response, "grading")

# 驗證業務邏輯回應
assert_response_success(response, "保存成功")
```

### 4. 環境隔離和清理

```python
from tests.utils import test_environment, temporary_file

with test_environment() as cleaner:
    # 測試代碼
    temp_file = create_temp_file("test content")
    cleaner.register_temp_file(temp_file)
    
    # 測試結束時自動清理
```

## 配置說明

### pytest 配置（pyproject.toml）

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "-v",
    "--cov=core",
    "--cov=web", 
    "--cov-report=html",
    "--asyncio-mode=auto"
]
markers = [
    "unit: 單元測試",
    "integration: 整合測試",
    "ai: 涉及 AI 服務的測試",
    "slow: 慢速測試"
]
```

### 測試標記

- `@pytest.mark.unit` - 單元測試
- `@pytest.mark.integration` - 整合測試  
- `@pytest.mark.ai` - AI 服務相關測試
- `@pytest.mark.mock` - 使用 Mock 的測試
- `@pytest.mark.slow` - 耗時測試
- `@pytest.mark.asyncio` - 異步測試

## 使用指南

### 1. 基本測試編寫

```python
import pytest
from tests.factories import KnowledgePointFactory
from tests.utils import assert_knowledge_point_valid

@pytest.mark.unit
def test_knowledge_point_creation():
    """測試知識點創建"""
    kp = KnowledgePointFactory.build()
    assert_knowledge_point_valid(kp)
    assert kp.mastery_level >= 0.0
```

### 2. 異步測試

```python
import pytest
from tests.mocks import create_mock_ai_service

@pytest.mark.asyncio
@pytest.mark.ai
async def test_ai_service():
    """測試 AI 服務"""
    ai_service = create_mock_ai_service()
    
    result = await ai_service.generate_practice_question()
    assert "chinese_sentence" in result
```

### 3. 使用 Fixtures

```python
def test_with_fixtures(sample_knowledge_point, mock_ai_service):
    """使用全局 fixtures 的測試"""
    assert sample_knowledge_point.knowledge_point_id
    assert mock_ai_service.generate_practice_question.return_value
```

### 4. 整合測試

```python
@pytest.mark.integration
def test_knowledge_manager_integration(mock_settings):
    """知識點管理器整合測試"""
    with FileOperationMockContext() as file_ctx:
        # 設置測試環境
        file_ctx.json_handler.write_json(
            str(mock_settings.KNOWLEDGE_FILE),
            {"version": "3.0", "knowledge_points": []}
        )
        
        # 執行業務邏輯測試
        manager = KnowledgeManager(str(mock_settings.KNOWLEDGE_FILE))
        kp = KnowledgePointFactory.build()
        
        response = manager.add_knowledge_point(kp)
        assert_response_success(response)
```

## 運行測試

### 基本命令

```bash
# 運行所有測試
pytest

# 運行特定模組
pytest tests/unit/

# 運行特定測試文件
pytest tests/test_framework_integration.py

# 使用標記過濾
pytest -m unit                    # 只運行單元測試
pytest -m "not slow"             # 排除慢速測試
pytest -m "unit and not ai"      # 組合條件

# 詳細輸出
pytest -v

# 覆蓋率報告
pytest --cov=core --cov-report=html
```

### 調試模式

```bash
# 在第一個失敗時停止
pytest -x

# 顯示本地變數
pytest -l

# 進入調試器
pytest --pdb
```

## Mock 使用策略

### 1. AI 服務 Mock

```python
# 正常行為
ai_service = create_mock_ai_service("normal")

# 不可靠網絡
ai_service = create_mock_ai_service("unreliable") 

# 慢速響應
ai_service = create_mock_ai_service("slow")

# 配額限制
ai_service = create_mock_ai_service("quota_limited")
```

### 2. Repository Mock

```python
# 空數據庫
repo = create_mock_knowledge_repository("empty")

# 正常數據
repo = create_mock_knowledge_repository("normal")  

# 大量需複習數據
repo = create_mock_knowledge_repository("review_heavy")

# 容易出錯
repo = create_mock_knowledge_repository("error_prone")
```

### 3. 文件系統 Mock

```python
with FileOperationMockContext() as file_ctx:
    # 在內存中操作文件
    file_ctx.json_handler.write_json("test.json", {"data": "test"})
    data = file_ctx.json_handler.read_json("test.json")
```

## 最佳實踐

### 1. 測試組織

- 按功能模組組織測試文件
- 使用描述性的測試名稱
- 遵循 AAA 模式（Arrange, Act, Assert）

### 2. 數據管理

- 優先使用工廠生成測試數據
- 避免硬編碼測試數據
- 使用 fixtures 共享通用設置

### 3. Mock 策略

- Mock 外部依賴（API、文件系統）
- 不要 Mock 被測試的代碼
- 驗證 Mock 的調用行為

### 4. 斷言最佳化

- 使用自定義斷言提高可讀性
- 提供清晰的錯誤信息
- 驗證關鍵業務邏輯

### 5. 性能考量

- 使用 `@pytest.mark.slow` 標記耗時測試
- 並行運行獨立測試
- 優化測試數據大小

## 故障排除

### 常見問題

1. **異步測試問題**
   ```python
   # 確保使用 @pytest.mark.asyncio
   @pytest.mark.asyncio
   async def test_async_function():
       result = await some_async_function()
       assert result
   ```

2. **Mock 不生效**
   ```python
   # 確保 patch 路徑正確
   with patch('core.ai_service.AIService') as mock_service:
       # 測試代碼
   ```

3. **文件清理問題**
   ```python
   # 使用上下文管理器確保清理
   with test_environment() as cleaner:
       # 測試代碼
   ```

4. **測試數據隔離**
   ```python
   # 每個測試使用獨立的臨時目錄
   def test_with_isolation(temp_data_dir):
       # temp_data_dir 自動清理
   ```

## 擴展指南

### 添加新的工廠

1. 在 `tests/factories/` 中創建新文件
2. 實現 Factory 類和建構器
3. 在 `__init__.py` 中導出
4. 編寫使用範例

### 添加新的 Mock

1. 在 `tests/mocks/` 中創建 Mock 類
2. 實現不同行為模式
3. 提供統計和配置方法
4. 添加上下文管理器支援

### 添加新的斷言

1. 在 `tests/utils/test_assertions.py` 中添加函數
2. 提供清晰的錯誤信息
3. 支援可選參數配置
4. 編寫使用文檔

## 貢獻指南

1. 新增測試時請更新相關文檔
2. 確保測試具有良好的覆蓋率
3. 遵循現有的命名和組織慣例
4. 添加適當的測試標記和分類

## 參考資源

- [pytest 官方文檔](https://docs.pytest.org/)
- [factory_boy 文檔](https://factoryboy.readthedocs.io/)
- [Python unittest.mock 文檔](https://docs.python.org/3/library/unittest.mock.html)