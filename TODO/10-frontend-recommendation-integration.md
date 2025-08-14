# 10. 前端推薦系統整合

## 優先級: HIGH 🟠
## 預估時間: 5-6 小時
## 狀態: ⏳ PENDING

### 背景
後端推薦系統已實作完成（`get_learning_recommendations()`），但缺少前端整合。需要創建 UI 組件並連接 API。

### 子任務清單

#### A. API 路由實作 (1.5小時)
- [ ] 創建推薦系統 API 端點
  ```python
  # web/routers/api_knowledge.py
  @router.get("/api/recommendations")
  async def get_recommendations():
      # 調用 adapter.get_learning_recommendations()
      pass
  ```
  
- [ ] 實現響應模型
  - [ ] 創建 `RecommendationResponse` Pydantic 模型
  - [ ] 包含推薦列表、重點領域、建議難度
  - [ ] 添加優先知識點列表

- [ ] 添加錯誤處理
  - [ ] 處理無數據情況
  - [ ] 處理資料庫連線錯誤
  - [ ] 返回適當的 HTTP 狀態碼

#### B. 前端組件開發 (2小時)
- [ ] 創建推薦卡片組件
  ```javascript
  // web/static/js/components/recommendation-card.js
  class RecommendationCard {
      constructor(recommendations) {
          this.recommendations = recommendations;
      }
      
      render() {
          // 渲染推薦內容
      }
  }
  ```
  
- [ ] 設計 UI 樣式
  - [ ] 創建 `web/static/css/components/recommendation.css`
  - [ ] 遵循現有設計系統
  - [ ] 響應式設計支援

- [ ] 實現動態更新
  - [ ] 每次練習後重新獲取推薦
  - [ ] 顯示載入狀態
  - [ ] 處理錯誤狀態

#### C. 練習頁面整合 (1.5小時)
- [ ] 修改 `practice-logic.js`
  - [ ] 在頁面載入時獲取推薦
  - [ ] 在側邊欄或頂部顯示推薦
  - [ ] 根據推薦調整練習難度
  
- [ ] 更新練習模板
  - [ ] 修改 `web/templates/practice.html`
  - [ ] 添加推薦顯示區域
  - [ ] 整合推薦組件

- [ ] 實現交互功能
  - [ ] 點擊推薦項目查看詳情
  - [ ] 根據推薦篩選知識點
  - [ ] 忽略或接受推薦

#### D. 數據視覺化 (1小時)
- [ ] 創建進度圖表
  - [ ] 顯示各類別掌握度
  - [ ] 顯示學習趨勢
  - [ ] 使用 Chart.js 或類似庫
  
- [ ] 實現統計面板
  - [ ] 總知識點數量
  - [ ] 低掌握度數量
  - [ ] 待複習數量
  
- [ ] 添加學習建議提示
  - [ ] 根據時間建議學習強度
  - [ ] 提供學習策略建議

### 驗收標準
1. 練習頁面顯示個性化推薦
2. 推薦內容根據學習進度動態更新
3. UI 設計與現有系統一致
4. 響應時間 < 200ms

### 測試場景
```javascript
// 測試推薦 API
fetch('/api/recommendations')
    .then(res => res.json())
    .then(data => console.log(data));

// 測試推薦卡片渲染
const card = new RecommendationCard(mockData);
card.render();

// 測試動態更新
practiceSession.onComplete(() => {
    updateRecommendations();
});
```

### 相關文件
- `/Users/chenliangyu/Desktop/linker/core/database/adapter.py` (後端實作)
- `/Users/chenliangyu/Desktop/linker/web/routers/api_knowledge.py` (需要添加路由)
- `/Users/chenliangyu/Desktop/linker/web/static/js/practice-logic.js` (需要整合)
- `/Users/chenliangyu/Desktop/linker/web/templates/practice.html` (需要修改)

### 依賴關係
- 依賴任務 02 的 API 路由實作
- 需要先完成推薦系統後端優化