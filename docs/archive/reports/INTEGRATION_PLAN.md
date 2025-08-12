# 服務層整合計劃

## 🎯 整合目標
將新創建的服務層架構整合到現有的 FastAPI 應用中，同時保持向後兼容性。

## 📋 整合清單

### Phase 1: 服務初始化 (立即可做)
```python
# web/main.py 添加服務初始化
from services import (
    KnowledgeService,
    ErrorProcessingService, 
    PracticeRecordService
)
from core.repositories import (
    KnowledgeRepository,
    PracticeRepository,
    CompositeRepository
)

# 初始化 Repository 層
knowledge_repo = KnowledgeRepository('data/knowledge.json')
practice_repo = PracticeRepository('data/practice_log.json')
composite_repo = CompositeRepository(knowledge_repo, practice_repo)

# 初始化服務層
knowledge_service = KnowledgeService(knowledge, knowledge_repo)
error_service = ErrorProcessingService(
    error_type_system=ErrorTypeSystem(),
    knowledge_repository=knowledge_repo,
    knowledge_manager=knowledge
)
practice_service = PracticeRecordService(practice_repo)
```

### Phase 2: API 端點遷移

#### 2.1 提交翻譯端點
**現有**: `POST /api/submit`
```python
# 原始代碼
@app.post("/api/submit")
async def api_submit_translation(request: Request):
    # 直接調用 knowledge.save_mistake()
```

**新實現**:
```python
@app.post("/api/submit")
async def api_submit_translation(request: Request):
    from services.dto import SaveMistakeRequest
    
    # 構建請求對象
    save_request = SaveMistakeRequest(
        chinese_sentence=chinese,
        user_answer=english,
        feedback=result,
        practice_mode=mode,
        difficulty_level=level,
        target_point_ids=target_point_ids
    )
    
    # 使用服務層
    service_result = knowledge_service.save_mistake(save_request)
    
    # 轉換為 API 響應
    return service_result.to_api_response()
```

#### 2.2 獲取知識點端點
**現有**: `GET /api/knowledge`
```python
# 使用服務層替代直接訪問
service_result = knowledge_service.get_knowledge_points(
    limit=limit,
    category_filter=category
)
```

#### 2.3 練習統計端點
**新增**: `GET /api/practice/statistics`
```python
@app.get("/api/practice/statistics")
async def get_practice_statistics(days: int = 7):
    result = practice_service.get_practice_statistics(days=days)
    return result.to_api_response()
```

### Phase 3: 模板更新

更新 Jinja2 模板以使用新的數據結構：

```python
# 在路由處理器中
@app.get("/practice")
async def practice_page(request: Request):
    # 使用服務層獲取數據
    stats = practice_service.get_practice_statistics()
    review_queue = knowledge_service.get_review_queue()
    
    return templates.TemplateResponse("practice.html", {
        "request": request,
        "statistics": stats.data,
        "review_queue": review_queue.data
    })
```

### Phase 4: 錯誤處理統一

```python
from fastapi import HTTPException
from core.error_handler import GlobalErrorHandler

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    service_result = GlobalErrorHandler.handle(exc)
    
    if not service_result.success:
        raise HTTPException(
            status_code=500,
            detail=service_result.message
        )
    
    return JSONResponse(
        content=service_result.to_api_response().dict()
    )
```

## 🔄 遷移策略

### 1. 並行運行期 (第一週)
- 新舊代碼並行運行
- 使用 feature flag 控制流量
- 監控兩套系統的輸出差異

```python
USE_NEW_SERVICE_LAYER = os.getenv("USE_NEW_SERVICE_LAYER", "false").lower() == "true"

if USE_NEW_SERVICE_LAYER:
    # 新服務層邏輯
    result = knowledge_service.save_mistake(request)
else:
    # 舊邏輯
    knowledge.save_mistake(...)
```

### 2. 逐步切換期 (第二週)
- 逐個端點切換到新服務層
- 保留回滾能力
- 收集性能指標

### 3. 清理期 (第三週)
- 移除舊代碼
- 優化性能
- 更新文檔

## 🧪 測試計劃

### 單元測試
```bash
# 運行服務層測試
pytest tests/unit/services/ -v

# 運行集成測試
pytest tests/integration/ -v
```

### 端到端測試
```bash
# 啟動測試服務器
uvicorn web.main:app --reload --port 8001

# 運行 E2E 測試
pytest tests/e2e/ --base-url http://localhost:8001
```

### 性能測試
```python
# 比較新舊實現的性能
import timeit

# 舊實現
old_time = timeit.timeit(
    lambda: knowledge.save_mistake(...),
    number=1000
)

# 新實現
new_time = timeit.timeit(
    lambda: knowledge_service.save_mistake(...),
    number=1000
)

print(f"性能提升: {(old_time - new_time) / old_time * 100:.2f}%")
```

## 📊 監控指標

### 關鍵指標
1. **響應時間**: P50, P95, P99
2. **錯誤率**: 5xx 錯誤比例
3. **吞吐量**: 每秒請求數
4. **資源使用**: CPU, 記憶體

### 監控代碼
```python
from prometheus_client import Counter, Histogram, generate_latest

# 定義指標
request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'API request duration')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.inc()
    request_duration.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🚨 回滾計劃

如果出現問題，可以快速回滾：

1. **環境變數切換**: 設置 `USE_NEW_SERVICE_LAYER=false`
2. **代碼回滾**: `git revert <commit-hash>`
3. **數據恢復**: 從備份恢復 JSON 文件

## 📅 時間表

| 階段 | 時間 | 任務 |
|-----|------|------|
| Week 1 | Day 1-2 | 服務層初始化和基礎整合 |
| Week 1 | Day 3-4 | API 端點遷移 |
| Week 1 | Day 5 | 測試和驗證 |
| Week 2 | Day 1-3 | 並行運行和監控 |
| Week 2 | Day 4-5 | 性能優化 |
| Week 3 | Day 1-2 | 清理舊代碼 |
| Week 3 | Day 3-5 | 文檔更新和培訓 |

## ✅ 成功標準

1. **功能完整性**: 所有現有功能正常運作
2. **性能提升**: 響應時間減少 20%
3. **代碼品質**: 函數複雜度降低 50%
4. **測試覆蓋**: 達到 80% 以上
5. **零停機時間**: 整個遷移過程不影響服務

## 📝 注意事項

1. **數據備份**: 每次更改前備份 `data/` 目錄
2. **版本控制**: 使用 feature branch 進行開發
3. **代碼審查**: 所有更改需要 code review
4. **漸進式部署**: 使用 canary deployment
5. **監控告警**: 設置關鍵指標的告警閾值

---

這個整合計劃確保了平滑的遷移過程，最小化風險，並提供了清晰的回滾策略。