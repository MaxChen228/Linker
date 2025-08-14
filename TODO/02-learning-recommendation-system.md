# 02. 學習推薦系統實現

## 優先級: HIGH
## 預估時間: 6-8 小時
## 狀態: ✅ COMPLETED (2025-08-14)

### 背景
實現智能學習推薦功能，根據用戶的錯誤模式和掌握度提供個性化建議。

### 子任務清單

#### A. 推薦算法設計 (2小時)
- [x] 分析現有數據結構
  - [x] 研究 knowledge_points 表結構
  - [x] 理解 mastery_level 計算邏輯
  - [x] 分析 review_schedule 機制

- [x] 設計推薦算法
  - [x] 定義推薦優先級計算公式
  - [x] 考慮錯誤類別權重（systematic > isolated > enhancement）
  - [x] 整合時間衰減因子

#### B. get_learning_recommendations() 實現 (3小時)
- [x] 數據收集階段
  - [x] 獲取低掌握度知識點（< 0.3）
  - [x] 統計各類別錯誤頻率
  - [x] 分析最近練習記錄

- [x] 推薦生成邏輯
  - [x] 計算每個類別的優先級分數
  - [x] 生成前3個重點練習領域
  - [x] 產生具體的練習建議

- [x] 返回格式設計
  ```python
  {
    'recommendations': [
      '重點練習 systematic 類型錯誤 (15 個知識點)',
      '加強 past tense 相關練習',
      '複習介係詞搭配用法'
    ],
    'focus_areas': ['systematic', 'isolated'],
    'suggested_difficulty': 2,
    'next_review_count': 5
  }
  ```

#### C. permanent_delete_old_points() 實現 (1.5小時)
- [x] 刪除邏輯設計
  - [x] 定義「舊」的標準（預設30天）
  - [x] 只刪除已軟刪除的點
  - [x] 保留高價值知識點

- [x] 資料庫操作
  - [x] 實現批量刪除查詢
  - [x] 添加事務保護
  - [x] 記錄刪除日誌

- [x] 安全機制
  - [x] 添加確認步驟
  - [x] 實現回滾機制
  - [x] 限制單次刪除數量

#### D. 整合到 Web 界面 (1.5小時)
- [x] API 端點創建
  - [x] 創建 `/api/recommendations` 路由
  - [x] 實現 Pydantic 響應模型
  - [x] 添加錯誤處理

- [ ] 前端顯示 (待實現)
  - [ ] 在練習頁面顯示推薦 (待實現)
  - [ ] 添加推薦卡片組件 (待實現)
  - [ ] 實現動態更新 (待實現)

### 測試計劃
```python
# 單元測試
def test_recommendation_algorithm():
    # 準備測試數據
    # 驗證推薦結果
    pass

def test_old_points_deletion():
    # 創建舊知識點
    # 執行刪除
    # 驗證結果
    pass

# 性能測試
def test_recommendation_performance():
    # 大量數據測試
    # 確保響應時間 < 100ms
    pass
```

### 驗收標準
1. 推薦系統能準確識別學習重點
2. 刪除功能安全可靠
3. API 響應時間 < 100ms
4. 前端能正確顯示推薦內容

### 相關文件
- `/Users/chenliangyu/Desktop/linker/core/database/adapter.py`
- `/Users/chenliangyu/Desktop/linker/core/knowledge.py`
- `/Users/chenliangyu/Desktop/linker/web/routers/api_knowledge.py`