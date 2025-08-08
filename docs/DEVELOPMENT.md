# 開發指南

## 開發環境設置

### 系統需求

- Python 3.8 或更高版本
- pip 套件管理器
- Git（版本控制）
- 文字編輯器或 IDE（推薦 VS Code 或 PyCharm）

### 環境準備

1. **克隆專案**
```bash
git clone <repository-url>
cd linker-cli
```

2. **創建虛擬環境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安裝開發依賴**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 開發工具（如果有）
```

4. **設定環境變數**
```bash
cp .env.example .env  # 複製範例配置
# 編輯 .env 文件，填入您的 API Key
```

5. **驗證安裝**
```bash
python test_refactoring.py
```

## 專案結構說明

```
linker-cli/
├── linker_cli.py          # 主程式入口點
├── settings.py            # 配置管理中心
├── config.py              # 舊版配置（保留兼容）
│
├── core/                  # 核心業務邏輯
│   ├── __init__.py        # 模組初始化
│   ├── ai_service.py      # AI 服務封裝
│   ├── knowledge.py       # 知識點管理
│   ├── error_classifier.py # 錯誤分類器
│   ├── error_types.py     # 錯誤類型定義
│   ├── exceptions.py      # 異常定義
│   └── logger.py          # 日誌系統
│
├── data/                  # 數據存儲
│   ├── knowledge.json     # 知識點數據
│   ├── practice_log.json  # 練習記錄
│   ├── examples.json      # 例句庫
│   └── grammar.json       # 文法規則
│
├── docs/                  # 專案文檔
│   ├── API.md            # API 文檔
│   ├── ARCHITECTURE.md   # 架構說明
│   ├── CONFIGURATION.md  # 配置指南
│   └── DEVELOPMENT.md    # 開發指南（本文件）
│
├── tests/                 # 測試文件（計劃中）
│   ├── test_ai_service.py
│   ├── test_knowledge.py
│   └── test_classifier.py
│
└── logs/                  # 日誌輸出（自動生成）
```

## 編碼規範

### Python 代碼風格

遵循 PEP 8 規範，主要原則：

1. **縮排**：使用 4 個空格
2. **行長**：最多 88 字符（使用 Black 格式化）
3. **命名規範**：
   - 類名：`PascalCase`
   - 函數/變數：`snake_case`
   - 常數：`UPPER_SNAKE_CASE`
   - 私有成員：`_leading_underscore`

### 類型提示

使用 Python 3.8+ 的類型提示：

```python
from typing import List, Dict, Optional, Union

def process_data(
    items: List[str],
    options: Optional[Dict[str, Any]] = None
) -> Union[str, None]:
    """
    處理數據項目
    
    Args:
        items: 要處理的項目列表
        options: 可選的處理選項
        
    Returns:
        處理結果或 None
    """
    if not items:
        return None
    # 處理邏輯
    return result
```

### 文檔字串

使用 Google 風格的 docstring：

```python
class KnowledgeManager:
    """
    知識點管理器
    
    管理知識點的創建、更新、查詢和統計功能。
    
    Attributes:
        data_path: 數據文件路徑
        cache: 內存緩存字典
        
    Example:
        >>> manager = KnowledgeManager("data/knowledge.json")
        >>> point_id = manager.add_knowledge_point({...})
        >>> manager.update_mastery(point_id, True)
    """
    
    def update_mastery(
        self,
        point_id: int,
        is_correct: bool
    ) -> Dict[str, Any]:
        """
        更新知識點掌握度
        
        Args:
            point_id: 知識點 ID
            is_correct: 是否答對
            
        Returns:
            包含新掌握度和變化的字典
            
        Raises:
            DataException: 如果知識點不存在
            ValidationException: 如果參數無效
        """
        pass
```

## 測試指南

### 單元測試

使用 pytest 進行測試：

```python
# test_knowledge.py
import pytest
from core.knowledge import KnowledgeManager
from core.exceptions import DataException

class TestKnowledgeManager:
    @pytest.fixture
    def manager(self, tmp_path):
        """創建測試用的管理器"""
        data_file = tmp_path / "test_knowledge.json"
        return KnowledgeManager(data_file)
    
    def test_add_knowledge_point(self, manager):
        """測試添加知識點"""
        data = {
            "key_point": "測試知識點",
            "category": "systematic",
            "explanation": "測試說明"
        }
        point_id = manager.add_knowledge_point(data)
        assert point_id > 0
        
    def test_update_mastery(self, manager):
        """測試更新掌握度"""
        # 先添加知識點
        point_id = manager.add_knowledge_point({...})
        
        # 測試正確回答
        result = manager.update_mastery(point_id, True)
        assert result["change"] > 0
        
        # 測試錯誤回答
        result = manager.update_mastery(point_id, False)
        assert result["change"] < 0
    
    def test_invalid_point_id(self, manager):
        """測試無效的知識點 ID"""
        with pytest.raises(DataException):
            manager.update_mastery(999, True)
```

### 運行測試

```bash
# 運行所有測試
pytest

# 運行特定測試文件
pytest tests/test_knowledge.py

# 運行並顯示覆蓋率
pytest --cov=core --cov-report=html

# 運行並顯示詳細輸出
pytest -v

# 運行特定測試函數
pytest tests/test_knowledge.py::TestKnowledgeManager::test_add_knowledge_point
```

### 整合測試

```python
# test_integration.py
def test_full_practice_flow():
    """測試完整的練習流程"""
    # 1. 初始化服務
    ai_service = AIService()
    knowledge_manager = KnowledgeManager()
    
    # 2. 執行翻譯檢查
    result = ai_service.check_translation(
        chinese="他每天跑步",
        english="He run every day"
    )
    
    # 3. 提取知識點
    assert not result["is_correct"]
    assert len(result["knowledge_points"]) > 0
    
    # 4. 更新知識庫
    for point in result["knowledge_points"]:
        knowledge_manager.add_knowledge_point(point)
    
    # 5. 驗證統計
    stats = knowledge_manager.get_statistics()
    assert stats["total_points"] > 0
```

## 調試技巧

### 使用日誌調試

```python
from core.logger import get_logger

logger = get_logger(__name__)

def debug_function(data):
    logger.debug(f"Input data: {data}")
    
    try:
        # 處理邏輯
        result = process(data)
        logger.debug(f"Processing result: {result}")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        raise
    
    return result
```

### 使用 Python 調試器

```python
import pdb

def complex_function(data):
    # 設置斷點
    pdb.set_trace()
    
    # 或使用 Python 3.7+ 的 breakpoint()
    breakpoint()
    
    # 代碼邏輯
    return result
```

### VS Code 調試配置

創建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Linker CLI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/linker_cli.py",
            "console": "integratedTerminal",
            "env": {
                "GEMINI_API_KEY": "your_test_key",
                "LOG_LEVEL": "DEBUG"
            }
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Test",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

## 性能優化

### 分析性能

```python
import cProfile
import pstats
from io import StringIO

def profile_function():
    """性能分析範例"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 要分析的代碼
    result = expensive_operation()
    
    profiler.disable()
    
    # 輸出分析結果
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(10)  # 顯示前10個最耗時的函數
    print(s.getvalue())
    
    return result
```

### 優化建議

1. **使用緩存**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param):
    # 複雜計算
    return result
```

2. **批量操作**
```python
# 不好的做法
for item in items:
    save_to_file(item)

# 好的做法
save_all_to_file(items)
```

3. **延遲載入**
```python
class LazyLoader:
    def __init__(self):
        self._data = None
    
    @property
    def data(self):
        if self._data is None:
            self._data = load_large_file()
        return self._data
```

## 版本控制

### Git 工作流程

1. **功能開發**
```bash
# 創建功能分支
git checkout -b feature/new-feature

# 開發並提交
git add .
git commit -m "feat: 添加新功能"

# 推送到遠端
git push origin feature/new-feature
```

2. **提交訊息規範**
```
<type>: <subject>

<body>

<footer>
```

類型（type）：
- `feat`: 新功能
- `fix`: 修復錯誤
- `docs`: 文檔更新
- `style`: 代碼格式調整
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 維護工作

範例：
```bash
git commit -m "feat: 添加批量練習模式

- 支援一次載入多個練習句子
- 添加進度顯示
- 優化記憶體使用

Closes #123"
```

### 發布流程

1. **更新版本號**
```python
# settings.py
VERSION = "2.1.0"
```

2. **更新 CHANGELOG**
```markdown
## [2.1.0] - 2025-08-10
### Added
- 批量練習模式
- 進度條顯示
```

3. **創建標籤**
```bash
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin v2.1.0
```

## 貢獻指南

### 提交 Pull Request

1. Fork 專案
2. 創建功能分支
3. 編寫代碼和測試
4. 確保測試通過
5. 提交 PR

### 代碼審查清單

- [ ] 代碼符合 PEP 8 規範
- [ ] 添加了適當的類型提示
- [ ] 編寫了文檔字串
- [ ] 添加了單元測試
- [ ] 測試覆蓋率 > 80%
- [ ] 更新了相關文檔
- [ ] 沒有引入新的依賴（或已討論）
- [ ] 性能沒有顯著下降

## 常見問題

### Q1: 如何添加新的錯誤類型？

1. 在 `core/error_types.py` 中定義：
```python
class NewErrorType(ErrorCategory):
    name = "new_type"
    priority = 5
    description = "新錯誤類型"
```

2. 在 `settings.py` 中添加配置：
```python
MASTERY_INCREMENTS["new_type"] = 0.10
MASTERY_DECREMENTS["new_type"] = 0.05
```

3. 更新分類器邏輯：
```python
def classify(error_desc):
    if "關鍵詞" in error_desc:
        return "new_type"
```

### Q2: 如何添加新的 AI 提供者？

1. 創建新的服務類：
```python
class NewAIService(BaseAIService):
    def check_translation(self, chinese, english):
        # 實現邏輯
        pass
```

2. 在配置中添加選項：
```python
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
```

3. 工廠模式創建：
```python
def create_ai_service():
    if settings.AI_PROVIDER == "new_provider":
        return NewAIService()
    return GeminiAIService()
```

### Q3: 如何優化啟動速度？

1. 延遲導入：
```python
def use_heavy_module():
    import heavy_module  # 只在需要時導入
    return heavy_module.process()
```

2. 預編譯：
```bash
python -m compileall .
```

3. 使用緩存：
```python
# 緩存配置
@lru_cache()
def load_config():
    return parse_config_file()
```

## 資源連結

### 官方文檔
- [Python 官方文檔](https://docs.python.org/3/)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [PEP 8 風格指南](https://pep8.org/)

### 推薦工具
- [Black](https://github.com/psf/black) - 代碼格式化
- [Flake8](https://flake8.pycqa.org/) - 代碼檢查
- [MyPy](http://mypy-lang.org/) - 類型檢查
- [Pytest](https://pytest.org/) - 測試框架

### 學習資源
- [Real Python](https://realpython.com/)
- [Python Design Patterns](https://python-patterns.guide/)
- [Clean Code in Python](https://github.com/zedr/clean-code-python)