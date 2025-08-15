# TASK-31: 完全異步化架構重構

- **Priority**: 🔴 CRITICAL
- **Estimated Time**: 40 hours (分階段執行)
- **Related Components**: 
  - `core/database/simplified_adapter.py`
  - `web/routers/*.py`
  - `web/dependencies.py`
  - `core/services/` (新建)
- **Parent Task**: TASK-30 (純資料庫遷移)
- **Created**: 2025-01-15
- **Author**: Claude (根據深度分析生成)

---

## 🎯 任務目標

完全異步化整個應用架構，解決事件循環衝突問題，實現純異步資料流，提升系統性能和可維護性。

### 問題背景

在 TASK-30 重構過程中發現的系統性問題：
```
ERROR - 獲取活躍知識點失敗: Cannot run the event loop while another loop is running
ERROR - 獲取複習候選失敗: Cannot run the event loop while another loop is running
```

這暴露了混合同步/異步架構的根本缺陷：
- FastAPI 運行在異步環境中
- 適配器層試圖創建新事件循環來橋接同步/異步
- 導致事件循環衝突，系統功能失效

## ✅ 驗收標準

### Phase 1 - 基礎設施 (8 hours)
- [ ] 創建異步服務層架構 `core/services/`
- [ ] 實現異步依賴注入框架
- [ ] 建立異步測試環境
- [ ] 實現請求級別的上下文管理
- [ ] 創建異步錯誤邊界機制

### Phase 2 - 核心遷移 (16 hours)
- [ ] 遷移 `practice` 路由到純異步
- [ ] 遷移 `knowledge` 路由到純異步
- [ ] 遷移 `calendar` 路由到純異步
- [ ] 遷移 `api_knowledge` 路由到純異步
- [ ] 遷移 `pages` 路由到純異步

### Phase 3 - 資料層重構 (8 hours)
- [ ] 移除 `SimplifiedDatabaseAdapter` 所有同步方法
- [ ] 創建 `PureAsyncKnowledgeManager`
- [ ] 優化資料庫查詢並發
- [ ] 實現批處理優化

### Phase 4 - 清理與優化 (8 hours)
- [ ] 移除所有遺留的同步包裝代碼
- [ ] 統一錯誤處理模式
- [ ] 性能調優和監控
- [ ] 更新所有文檔

## 📐 架構設計

### 目標架構
```
┌─────────────────────────────────┐
│   FastAPI Routes (純異步)        │ ← async def
├─────────────────────────────────┤
│   Service Layer (純異步)         │ ← 業務邏輯
├─────────────────────────────────┤
│  Repository Layer (純異步)       │ ← 資料存取
├─────────────────────────────────┤
│    Database (異步驅動)           │ ← asyncpg
└─────────────────────────────────┘
```

### 核心實現策略

#### 1. 異步服務層
```python
# core/services/async_knowledge_service.py
class AsyncKnowledgeService:
    """純異步服務層"""
    def __init__(self, db_manager: DatabaseKnowledgeManager):
        self.db = db_manager
        self.cache = UnifiedCacheManager()
    
    async def get_review_candidates(self, limit: int = 5) -> list[KnowledgePoint]:
        """直接異步，無需轉換"""
        return await self.db.get_review_candidates(limit)
```

#### 2. 依賴注入
```python
# web/dependencies.py
async def get_knowledge_service() -> AsyncGenerator[AsyncKnowledgeService, None]:
    """異步依賴注入"""
    db_manager = await create_database_manager()
    try:
        yield AsyncKnowledgeService(db_manager)
    finally:
        await db_manager.close()
```

#### 3. 路由層異步化
```python
# web/routers/practice.py
@router.post("/api/grade-answer")
async def grade_answer_api(
    request: GradeAnswerRequest,
    service: AsyncKnowledgeService = Depends(get_knowledge_service)
):
    """純異步路由處理"""
    return await service.grade_answer(request)
```

## 🚀 實施計劃

### Week 1: Foundation (第一週)
1. **Day 1-2**: 建立異步服務層基礎架構
   - 創建 `core/services/__init__.py`
   - 實現 `AsyncServiceRegistry`
   - 建立依賴注入框架

2. **Day 3-4**: 異步測試環境
   - 設置 pytest-asyncio
   - 創建異步測試基類
   - 實現測試用 fixtures

3. **Day 5**: 監控與日誌
   - 異步日誌處理
   - 性能監控基準
   - 錯誤追蹤機制

### Week 2: Migration (第二週)
1. **Day 6-7**: Practice 模組遷移
   - 遷移 practice 路由
   - 更新相關依賴
   - 完整測試

2. **Day 8-9**: Knowledge 模組遷移
   - 遷移 knowledge 路由
   - 遷移 api_knowledge 路由
   - 集成測試

3. **Day 10**: 其他模組遷移
   - calendar 路由
   - pages 路由
   - 輔助路由

### Week 3: Optimization (第三週)
1. **Day 11-12**: 資料層優化
   - 移除同步方法
   - 查詢優化
   - 連接池調優

2. **Day 13**: 性能測試
   - 壓力測試
   - 性能對比
   - 瓶頸分析

3. **Day 14-15**: 文檔與部署
   - 更新 API 文檔
   - 部署指南
   - 遷移指南

## 🔧 技術細節

### 事件循環管理
```python
# 正確的異步模式
async def handle_request():
    # 在現有事件循環中執行
    result = await async_operation()
    return result

# 錯誤的模式（當前問題）
def handle_request():
    loop = asyncio.new_event_loop()  # ❌ 在異步環境中創建新循環
    return loop.run_until_complete(async_operation())
```

### 並發控制
```python
class ConcurrencyLimiter:
    def __init__(self, max_concurrent: int = 10):
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run(self, coro):
        async with self._semaphore:
            return await coro
```

### 批處理優化
```python
class BatchProcessor:
    async def process_batch(self, items: list, processor):
        """批量處理，減少 I/O 往返"""
        tasks = [processor(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

## 📊 預期收益

1. **性能提升**
   - 並發處理能力提升 3-5 倍
   - 資料庫連接池利用率提升 50%
   - 記憶體使用減少 20%（無需多線程）

2. **代碼簡化**
   - 移除 600+ 行同步包裝代碼
   - 統一的異步編程模型
   - 更清晰的錯誤處理流程

3. **可維護性**
   - 單一的執行模型
   - 更容易理解的資料流
   - 更好的測試覆蓋率

## ⚠️ 風險管理

| 風險項目 | 影響等級 | 緩解策略 |
|---------|---------|---------|
| 開發者學習曲線 | 中 | 提供培訓材料和最佳實踐指南 |
| 第三方庫兼容性 | 低 | 預先測試所有依賴的異步支援 |
| 部署複雜度增加 | 中 | 使用藍綠部署和回滾策略 |
| 性能退化風險 | 低 | 建立性能基準和持續監控 |
| 測試覆蓋不足 | 高 | 要求 90% 以上的測試覆蓋率 |

## 🏁 完成標準

1. **功能完整性**
   - 所有原有功能正常運作
   - 無事件循環衝突錯誤
   - API 響應時間改善

2. **代碼品質**
   - 通過所有 linting 檢查
   - 測試覆蓋率 > 90%
   - 無同步/異步混用代碼

3. **性能指標**
   - 並發請求處理能力提升
   - 資料庫查詢延遲降低
   - 記憶體使用優化

4. **文檔完整**
   - API 文檔更新
   - 遷移指南完成
   - 性能報告發布

## 📝 執行筆記

### 2025-01-15 初始規劃
- 根據事件循環衝突錯誤的深度分析制定此計劃
- 確定採用完全異步化方案（方案2）
- 預估總工時 40 小時，分三週執行

### 關鍵決策點
1. **Q: 是否保留任何同步 API？**
   - A: 不保留，完全異步化

2. **Q: 如何處理向後兼容？**
   - A: 使用版本化 API 路由（/v2/），逐步遷移

3. **Q: 是否需要重寫所有測試？**
   - A: 是，所有測試都需要異步化

## 🔍 相關資源

- [Python asyncio 官方文檔](https://docs.python.org/3/library/asyncio.html)
- [FastAPI 異步最佳實踐](https://fastapi.tiangolo.com/async/)
- [asyncpg 性能指南](https://magicstack.github.io/asyncpg/current/)
- 內部文檔: `docs/ASYNC_MIGRATION.md` (待創建)

## 📋 子任務清單

### TASK-31A: 異步服務層基礎設施
- 創建服務層架構
- 實現依賴注入
- 建立測試框架

### TASK-31B: Practice 模組異步化
- 遷移 practice 路由
- 更新 grade_answer API
- 更新 generate_question API

### TASK-31C: Knowledge 模組異步化
- 遷移 knowledge 路由
- 更新 CRUD 操作
- 優化查詢性能

### TASK-31D: 資料層純異步化
- 移除同步方法
- 優化連接池
- 實現批處理

### TASK-31E: 性能優化與監控
- 壓力測試
- 性能調優
- 監控設置

### TASK-31F: 文檔與部署
- 更新所有文檔
- 準備部署計劃
- 用戶培訓材料

---

**注意**: 這是一個關鍵的架構升級，需要謹慎執行。建議在開發環境充分測試後再部署到生產環境。