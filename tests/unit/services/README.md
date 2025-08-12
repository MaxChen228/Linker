# 服務層測試套件

這個目錄包含了所有服務層類別的單元測試，提供完整的測試覆蓋和Mock策略。

## 測試文件結構

```
tests/unit/services/
├── __init__.py                         # 服務測試套件初始化
├── test_knowledge_service.py           # 知識點服務測試
├── test_error_processing_service.py    # 錯誤處理服務測試
├── test_practice_record_service.py     # 練習記錄服務測試
└── README.md                          # 本文檔
```

## 測試統計

- **總測試數量**: 103個測試
- **測試類別數**: 30個測試類
- **測試覆蓋範圍**: 服務層所有公開方法

### 各服務測試詳情

#### KnowledgeService (test_knowledge_service.py)
- **測試數量**: 42個
- **主要測試範圍**:
  - save_mistake: 錯誤保存流程測試 (7個測試)
  - get_knowledge_points: 知識點查詢測試 (4個測試)
  - get_knowledge_point_by_id: 單個知識點查詢 (2個測試)
  - update_mastery: 掌握度更新測試 (3個測試)
  - get_review_queue: 複習佇列測試 (3個測試)
  - get_knowledge_statistics: 統計查詢測試 (2個測試)
  - 私有方法測試 (4個測試)
  - 服務資訊測試 (1個測試)
  - 邊界情況測試 (3個測試)
  - 整合測試 (2個測試)

#### ErrorProcessingService (test_error_processing_service.py)
- **測試數量**: 31個
- **主要測試範圍**:
  - process_errors: 批量錯誤處理 (3個測試)
  - process_single_error: 單個錯誤處理 (3個測試)
  - extract_error_details: 錯誤詳情提取 (3個測試)
  - classify_error: 錯誤分類測試 (3個測試)
  - 知識點生成和更新 (6個測試)
  - 服務初始化測試 (3個測試)
  - 邊界情況測試 (4個測試)
  - 整合測試 (3個測試)

#### PracticeRecordService (test_practice_record_service.py)
- **測試數量**: 30個
- **主要測試範圍**:
  - record_practice: 練習記錄測試 (5個測試)
  - get_practice_history: 歷史查詢測試 (4個測試)
  - get_practice_statistics: 統計分析測試 (3個測試)
  - calculate_accuracy: 準確率計算 (5個測試)
  - 每日統計和趨勢分析 (8個測試)
  - 服務資訊和邊界情況 (5個測試)

## Mock 策略

### 依賴Mock化
所有測試都使用完整的Mock策略來隔離外部依賴：

- **KnowledgeManager**: Mock所有知識點操作
- **Repository層**: Mock所有數據存取操作
- **外部服務**: Mock AI服務、錯誤處理服務等

### Fixture設計
每個測試文件都提供完整的fixture支援：

```python
# 服務實例fixtures
knowledge_service          # 完整配置的服務實例
error_processing_service   # 錯誤處理服務實例
practice_record_service    # 練習記錄服務實例

# Mock依賴fixtures
mock_knowledge_manager     # Mock知識管理器
mock_knowledge_repository  # Mock知識點Repository
mock_practice_repository   # Mock練習記錄Repository

# 測試數據fixtures  
sample_mistake_request     # 樣本錯誤請求
sample_knowledge_point     # 樣本知識點
sample_practice_record     # 樣本練習記錄
```

## 測試覆蓋策略

### 1. 功能測試
- ✅ 正常執行路徑測試
- ✅ 成功案例測試
- ✅ 各種輸入參數組合

### 2. 錯誤處理測試
- ✅ 輸入驗證失敗
- ✅ 外部依賴失敗
- ✅ 異常情況處理
- ✅ 錯誤訊息驗證

### 3. 邊界情況測試
- ✅ 空數據處理
- ✅ 大量數據處理
- ✅ 特殊字符處理
- ✅ 並發操作模擬

### 4. 整合測試
- ✅ 完整工作流程測試
- ✅ 服務間協作測試
- ✅ 端到端場景測試

## 運行測試

### 運行所有服務測試
```bash
python -m pytest tests/unit/services/ -v
```

### 運行特定服務測試
```bash
# 知識點服務測試
python -m pytest tests/unit/services/test_knowledge_service.py -v

# 錯誤處理服務測試
python -m pytest tests/unit/services/test_error_processing_service.py -v

# 練習記錄服務測試
python -m pytest tests/unit/services/test_practice_record_service.py -v
```

### 運行特定測試類
```bash
python -m pytest tests/unit/services/test_knowledge_service.py::TestSaveMistake -v
```

### 運行測試並生成覆蓋率報告
```bash
python -m pytest tests/unit/services/ --cov=services --cov-report=html
```

## 測試特點

### 高質量Mock
- 所有外部依賴都被Mock化
- Mock對象設置完整的返回值
- 驗證Mock方法被正確調用

### 全面的斷言
- 驗證返回值結構和內容
- 檢查成功/失敗狀態
- 驗證錯誤訊息和錯誤碼
- 確認副作用發生

### 清晰的測試組織
- 按功能分組的測試類
- 描述性的測試方法名稱
- 詳細的測試文檔字符串
- 邏輯清晰的測試步驟

### 完整的場景覆蓋
- 正常操作流程
- 各種錯誤情況
- 邊界條件處理
- 整合測試場景

## 注意事項

1. **Fixture作用域**: 所有fixture都使用函數作用域，確保測試間的隔離
2. **Mock重置**: 每個測試都使用新的Mock實例，避免狀態污染
3. **數據一致性**: 測試數據與實際業務邏輯保持一致
4. **錯誤處理**: 所有可能的錯誤路徑都有對應的測試覆蓋

## 維護指南

### 新增測試
1. 在對應的測試文件中添加新的測試方法
2. 使用現有的fixture或創建新的fixture
3. 確保測試名稱清晰描述測試目的
4. 添加適當的文檔字符串

### 更新測試
1. 當服務代碼發生變化時，更新相應的測試
2. 確保Mock設置與新的依賴要求匹配
3. 更新測試斷言以反映新的預期行為

### 測試維護
1. 定期運行所有測試確保通過
2. 監控測試覆蓋率，維持高覆蓋率
3. 重構重複的測試代碼到共用fixture
4. 保持測試代碼的可讀性和可維護性