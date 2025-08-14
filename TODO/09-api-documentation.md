# 09. API 文檔撰寫與整合

## 優先級: MEDIUM 🟡
## 預估時間: 4-5 小時
## 狀態: ⏳ PENDING

### 背景
目前系統缺少完整的 API 文檔，需要建立 OpenAPI/Swagger 文檔系統，方便開發者理解和使用 API。

### 子任務清單

#### A. FastAPI 自動文檔優化 (1小時)
- [ ] 為所有路由添加詳細的 docstrings
  - [ ] 描述每個端點的功能
  - [ ] 說明請求參數
  - [ ] 提供響應範例
  
- [ ] 完善 Pydantic 模型文檔
  - [ ] 為每個欄位添加 Field 描述
  - [ ] 提供範例值
  - [ ] 添加驗證規則說明

#### B. OpenAPI Schema 客製化 (1.5小時)
- [ ] 配置 OpenAPI 元數據
  ```python
  app = FastAPI(
      title="Linker API",
      description="AI-powered English learning platform",
      version="1.0.0",
      docs_url="/api/docs",
      redoc_url="/api/redoc"
  )
  ```
  
- [ ] 添加 API 標籤分類
  - [ ] Practice 練習相關
  - [ ] Knowledge 知識點管理
  - [ ] Calendar 學習日曆
  - [ ] Recommendations 推薦系統
  
- [ ] 實現請求/響應範例
  - [ ] 使用 `example` 和 `examples` 參數
  - [ ] 提供成功和錯誤情況範例

#### C. API 使用指南撰寫 (1.5小時)
- [ ] 創建 `docs/API.md` 文檔
  - [ ] API 概述和架構說明
  - [ ] 認證方式（如果有）
  - [ ] 錯誤代碼表
  - [ ] Rate limiting 說明
  
- [ ] 撰寫常見使用案例
  - [ ] 獲取練習題目流程
  - [ ] 提交答案並獲取批改
  - [ ] 管理知識點 CRUD
  - [ ] 查詢學習進度

#### D. Postman Collection 建立 (1小時)
- [ ] 創建 Postman collection
  - [ ] 組織所有 API 端點
  - [ ] 添加環境變數配置
  - [ ] 設置預設請求頭
  
- [ ] 添加測試腳本
  - [ ] 響應狀態碼驗證
  - [ ] 響應結構檢查
  - [ ] 資料正確性驗證
  
- [ ] 導出並加入版本控制
  - [ ] `docs/postman_collection.json`
  - [ ] `docs/postman_environment.json`

### 驗收標準
1. 訪問 `/api/docs` 能看到完整的 Swagger UI
2. 所有 API 端點都有清晰的文檔
3. Postman collection 可以成功導入並執行
4. API 文檔與實際實作保持同步

### 測試計劃
```bash
# 檢查自動文檔
curl http://localhost:8000/openapi.json | jq .

# 訪問 Swagger UI
open http://localhost:8000/api/docs

# 訪問 ReDoc
open http://localhost:8000/api/redoc

# 執行 Postman collection
newman run docs/postman_collection.json -e docs/postman_environment.json
```

### 相關文件
- FastAPI 文檔: https://fastapi.tiangolo.com/tutorial/metadata/
- OpenAPI 規範: https://swagger.io/specification/
- `/Users/chenliangyu/Desktop/linker/web/main.py`
- `/Users/chenliangyu/Desktop/linker/web/routers/`