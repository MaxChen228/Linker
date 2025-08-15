# TASK-32: 每日儲存知識點上限功能

- **Priority**: 🟠 HIGH
- **Estimated Time**: 20 hours (分階段執行)
- **Related Components**: 
  - `core/services/async_knowledge_service.py`
  - `core/database/repositories/knowledge_repository.py`
  - `web/routers/api_knowledge.py`
  - `web/templates/practice.html`
  - `web/static/js/practice-logic.js`
- **Parent Task**: 學習效率優化專案
- **Created**: 2025-08-15
- **Author**: Claude (基於用戶需求分析)

---

## 🎯 功能目標

實現每日儲存知識點上限控制，專門針對「單一知識點」(isolated) 和「可以更好」(enhancement) 類型，避免新增知識點速度超過複習能力，維持學習與複習的平衡。

### 核心問題解決
- **問題**: 用戶新增知識點過快 → 複習積壓 → 學習效果下降
- **解決方案**: 智能限額控制 + 用戶自主配置 + 實時反饋
- **預期效果**: 提升複習完成率，降低知識點遺忘率

## ✅ 驗收標準

### Phase 1 - 核心限額功能 (8 hours)
- [ ] 設計並實現資料庫 schema (user_settings, daily_knowledge_stats)
- [ ] 在 AsyncKnowledgeService 中整合限額檢查邏輯
- [ ] 實現基本 API 端點 (狀態查詢、配置更新)
- [ ] 修改知識點儲存流程，加入限額驗證
- [ ] 單元測試覆蓋率 > 90%

### Phase 2 - 前端整合與體驗 (8 hours)
- [ ] 練習頁面添加實時限額顯示 (已用/總數)
- [ ] 達到上限時的用戶互動設計
- [ ] 設定頁面增加限額配置介面
- [ ] 統計頁面顯示每日使用趨勢
- [ ] 響應式設計適配所有設備

### Phase 3 - 智能化與優化 (4 hours)
- [ ] 基於複習表現的智能建議系統
- [ ] 緩存優化，減少資料庫查詢
- [ ] 錯誤處理和降級策略
- [ ] 性能測試和優化

## 📐 技術設計

### 資料庫設計

#### 新增資料表 - user_settings
```sql
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) DEFAULT 'default_user',
    daily_knowledge_limit INTEGER DEFAULT 15 CHECK (daily_knowledge_limit BETWEEN 5 AND 50),
    limit_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 新增資料表 - daily_knowledge_stats  
```sql
CREATE TABLE IF NOT EXISTS daily_knowledge_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    user_id VARCHAR(50) DEFAULT 'default_user',
    isolated_count INTEGER DEFAULT 0,
    enhancement_count INTEGER DEFAULT 0,
    total_limited_count INTEGER GENERATED ALWAYS AS (isolated_count + enhancement_count) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, user_id)
);
```

### API 設計

#### 1. GET /api/daily-limit/status
```json
{
  "date": "2025-08-15",
  "limit_enabled": true,
  "daily_limit": 15,
  "used_count": 8,
  "remaining": 7,
  "breakdown": {
    "isolated": 5,
    "enhancement": 3
  },
  "can_add_more": true
}
```

#### 2. PUT /api/daily-limit/config
```json
{
  "daily_limit": 20,
  "limit_enabled": true
}
```

#### 3. GET /api/daily-limit/stats?days=7
```json
{
  "stats": [
    {
      "date": "2025-08-15",
      "total_count": 12,
      "isolated_count": 7,
      "enhancement_count": 5,
      "limit": 15
    }
  ],
  "summary": {
    "avg_daily_usage": 11.2,
    "peak_day": "2025-08-12",
    "suggested_limit": 18
  }
}
```

### 服務層整合

#### AsyncKnowledgeService 擴展
```python
class AsyncKnowledgeService(BaseAsyncService):
    
    async def check_daily_limit(self, error_type: str) -> dict:
        """檢查當日知識點儲存限額"""
        if error_type not in ['isolated', 'enhancement']:
            return {"can_add": True, "reason": "type_not_limited"}
        
        # 使用緩存避免頻繁DB查詢
        cache_key = f"daily_limit_status:{datetime.now().date()}"
        status = await self._cache_manager.get(cache_key)
        
        if not status:
            status = await self._calculate_daily_status()
            await self._cache_manager.set(cache_key, status, ttl=3600)
        
        return status
    
    async def save_knowledge_point_with_limit(
        self, 
        knowledge_point: KnowledgePoint
    ) -> dict:
        """帶限額檢查的知識點儲存"""
        
        # 檢查是否啟用限額功能
        settings = await self._get_user_settings()
        if not settings.limit_enabled:
            return await self.save_knowledge_point(knowledge_point)
        
        # 檢查限額狀態
        limit_status = await self.check_daily_limit(knowledge_point.error_type)
        
        if not limit_status["can_add"]:
            return {
                "success": False,
                "reason": "daily_limit_exceeded",
                "limit_status": limit_status,
                "suggestion": "請先完成今日的複習任務，或調整每日上限設定"
            }
        
        # 儲存知識點並更新統計
        result = await self.save_knowledge_point(knowledge_point)
        if result["success"]:
            await self._update_daily_stats(knowledge_point.error_type)
        
        return {
            **result,
            "limit_status": await self.check_daily_limit(knowledge_point.error_type)
        }
```

## 🎨 前端設計

### 練習頁面即時顯示
```html
<!-- 在練習頁面頂部顯示 -->
<div class="daily-limit-indicator" id="dailyLimitIndicator">
    <div class="limit-progress">
        <span class="limit-text">今日已儲存: <strong id="usedCount">8</strong>/<strong id="totalLimit">15</strong></span>
        <div class="progress-bar">
            <div class="progress-fill" style="width: 53%"></div>
        </div>
    </div>
    <small class="limit-detail">重點複習: <span id="isolatedCount">5</span> | 可改進: <span id="enhancementCount">3</span></small>
</div>
```

### 達到上限時的按鈕狀態設計
```html
<!-- 正常情況下的按鈕組 -->
<div class="knowledge-action-buttons" id="knowledgeActions">
    <button class="btn btn-success" id="addKnowledgeBtn">
        ✓ 加入知識庫
    </button>
    <button class="btn btn-secondary" id="skipBtn">
        × 忽略
    </button>
</div>

<!-- 達到上限時的合併按鈕 -->
<div class="knowledge-action-buttons limit-reached" id="knowledgeActionsLimited" style="display: none;">
    <button class="btn btn-warning btn-limit-reached" id="limitReachedBtn">
        📊 已到達上限 - 點擊設定
    </button>
    <small class="limit-reached-hint">今日知識點儲存已達上限 (15/15)，可到設定頁面調整</small>
</div>
```

```javascript
// 達到上限時的UI狀態切換
function updateKnowledgeButtonsState(limitStatus) {
    const normalButtons = document.getElementById('knowledgeActions');
    const limitButtons = document.getElementById('knowledgeActionsLimited');
    const limitBtn = document.getElementById('limitReachedBtn');
    
    if (limitStatus.can_add_more) {
        // 正常狀態：顯示原本的兩個按鈕
        normalButtons.style.display = 'flex';
        limitButtons.style.display = 'none';
    } else {
        // 達到上限：顯示合併的限制按鈕
        normalButtons.style.display = 'none';
        limitButtons.style.display = 'block';
        
        // 更新提示文字
        const hint = limitButtons.querySelector('.limit-reached-hint');
        hint.textContent = `今日知識點儲存已達上限 (${limitStatus.used_count}/${limitStatus.daily_limit})，可到設定頁面調整`;
        
        // 點擊跳轉到設定頁面的限額設定區域
        limitBtn.onclick = () => {
            window.location.href = '/settings#daily-limit';
        };
    }
}

// 在每次顯示錯誤分析結果時檢查限額狀態
async function displayErrorAnalysis(errorData) {
    // ... 現有的錯誤分析顯示邏輯 ...
    
    // 檢查當前限額狀態
    const limitStatus = await fetch('/api/daily-limit/status').then(r => r.json());
    
    // 根據限額狀態更新按鈕顯示
    updateKnowledgeButtonsState(limitStatus);
    
    // 如果錯誤類型受限且已達上限，直接切換到限制狀態
    if (['isolated', 'enhancement'].includes(errorData.error_type) && !limitStatus.can_add_more) {
        showLimitReachedNotification(limitStatus);
    }
}

// 顯示達到上限的通知
function showLimitReachedNotification(limitStatus) {
    // 可以使用現有的通知系統顯示友善提醒
    showNotification({
        type: 'info',
        title: '今日學習目標已達成！',
        message: `您今日已儲存 ${limitStatus.used_count} 個重點知識點，建議先複習現有內容來鞏固學習效果。`,
        duration: 5000
    });
}
```

### 設定頁面配置介面
```html
<div class="setting-group" id="daily-limit">
    <h3>每日學習節奏控制</h3>
    <div class="setting-item">
        <label class="switch">
            <input type="checkbox" id="limitEnabled">
            <span class="slider"></span>
        </label>
        <div class="setting-info">
            <strong>啟用每日知識點上限</strong>
            <p>幫助維持學習與複習的平衡，避免新知識點累積過快</p>
        </div>
    </div>
    
    <div class="setting-item" id="limitConfig">
        <label for="dailyLimit">每日上限設定</label>
        <div class="limit-selector">
            <input type="range" id="dailyLimit" min="5" max="50" value="15">
            <span class="limit-value">15 個知識點</span>
        </div>
        <div class="limit-suggestion">
            💡 建議: 根據您的複習完成率，推薦上限為 <strong>18</strong> 個
        </div>
        
        <!-- 快速切換區域（從「已到達上限」按鈕進入時的直接操作） -->
        <div class="quick-toggle-section" id="quickToggleSection" style="display: none;">
            <div class="alert alert-info">
                <strong>📊 您已達今日上限</strong><br>
                可以在這裡快速調整設定，或是暫時關閉限額功能。
            </div>
            <div class="quick-actions">
                <button class="btn btn-primary" id="increaseLimit">提高上限至 +5</button>
                <button class="btn btn-secondary" id="disableTodayLimit">今日暫時關閉</button>
            </div>
        </div>
    </div>
</div>

<!-- CSS 樣式建議 -->
<style>
/* 限額按鈕的特殊樣式 */
.btn-limit-reached {
    background: linear-gradient(135deg, #ffeaa7, #fdcb6e);
    color: #2d3436;
    border: 2px solid #fdcb6e;
    font-weight: 600;
    padding: 12px 24px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.btn-limit-reached:hover {
    background: linear-gradient(135deg, #fdcb6e, #e17055);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(253, 203, 110, 0.4);
}

.limit-reached-hint {
    display: block;
    margin-top: 8px;
    color: #636e72;
    font-style: italic;
    text-align: center;
}

.knowledge-action-buttons.limit-reached {
    text-align: center;
    padding: 16px;
    background: rgba(255, 234, 167, 0.1);
    border-radius: 8px;
    border: 1px dashed #fdcb6e;
}

/* 快速操作按鈕組 */
.quick-actions {
    display: flex;
    gap: 12px;
    margin-top: 12px;
}

.quick-actions .btn {
    flex: 1;
}
</style>
```

## 🚀 實施計劃

### Week 1: 後端基礎設施 (第一週)
**Day 1-2: 資料庫與服務層 (8h)**
1. 設計並創建新資料表
2. 實現 AsyncKnowledgeService 的限額檢查邏輯
3. 整合到現有的知識點儲存流程
4. 添加緩存機制優化性能

**Day 3: API 端點實現 (4h)**
1. 實現狀態查詢 API
2. 實現配置更新 API  
3. 實現統計數據 API
4. 編寫 API 測試

### Week 2: 前端整合 (第二週)
**Day 4-5: 練習頁面整合 (8h)**
1. 添加即時限額顯示組件
2. 修改知識點儲存流程
3. 實現達到上限時的互動設計
4. 優化用戶體驗和視覺設計

**Day 6: 設定和統計頁面 (4h)**
1. 設定頁面添加限額配置
2. 統計頁面添加使用趨勢圖
3. 智能建議系統實現
4. 完整的功能測試

## 📊 智能化設計

### 動態建議算法
```python
def calculate_suggested_limit(user_stats: dict) -> int:
    """基於用戶複習表現計算建議上限"""
    
    # 取得過去7天的複習完成率
    review_completion_rate = user_stats.get('avg_review_completion', 0.7)
    
    # 取得平均每日新增量
    avg_daily_additions = user_stats.get('avg_daily_additions', 10)
    
    # 智能計算公式
    if review_completion_rate >= 0.9:
        # 複習表現優秀，可以提高上限
        suggested = int(avg_daily_additions * 1.3)
    elif review_completion_rate >= 0.7:
        # 複習表現良好，維持當前水準
        suggested = int(avg_daily_additions * 1.1)
    else:
        # 複習表現待改善，降低上限
        suggested = int(avg_daily_additions * 0.8)
    
    # 限制在合理範圍內
    return max(5, min(50, suggested))
```

### 緩存策略
```python
# 緩存設計
CACHE_KEYS = {
    "daily_status": "daily_limit_status:{date}",      # TTL: 1小時
    "user_settings": "user_settings:{user_id}",      # TTL: 24小時  
    "weekly_stats": "weekly_stats:{user_id}:{week}", # TTL: 6小時
}
```

## ⚠️ 風險管理與緩解策略

| 風險項目 | 影響等級 | 緩解策略 |
|---------|---------|---------|
| 用戶接受度低，被視為限制 | 高 | 1. 預設關閉，用戶選擇啟用<br>2. 清晰說明功能價值<br>3. 提供彈性設定選項 |
| 影響現有學習流程 | 中 | 1. 向後相容設計<br>2. 漸進式推出<br>3. 完整的回退機制 |
| 效能影響 | 中 | 1. 積極使用緩存<br>2. 異步處理統計更新<br>3. 資料庫查詢優化 |
| 資料一致性問題 | 低 | 1. 事務性操作<br>2. 定期資料校驗<br>3. 異常恢復機制 |

## 🎯 成功指標

### 量化指標
1. **功能採用率**: 目標 > 30% 用戶啟用
2. **複習完成率提升**: 啟用用戶的複習完成率提升 > 15%
3. **知識點重現錯誤率**: 降低 > 10%
4. **用戶滿意度**: NPS 分數 > 70
5. **按鈕互動率**: 「已到達上限」按鈕點擊率 > 60%（表示用戶理解並願意調整設定）

### 質化指標
1. **學習節奏穩定性**: 用戶反饋學習壓力降低
2. **功能理解度**: 用戶能正確理解和使用功能（通過按鈕狀態切換的直觀設計）
3. **個人化體驗**: 建議算法準確度 > 80%
4. **UI直觀性**: 用戶無需額外說明即可理解「已到達上限」按鈕的含義和作用

## 🔧 技術細節

### 錯誤類型映射
```python
# 受限制的錯誤類型
LIMITED_ERROR_TYPES = {
    'isolated': '單一知識點',      # 需要記憶的個別項目
    'enhancement': '可以更好'      # 正確但可改善的回答
}

# 不受限制的錯誤類型  
UNLIMITED_ERROR_TYPES = {
    'systematic': '系統性錯誤',    # 語法規則可學習
    'other': '其他錯誤'           # 其他類型錯誤
}
```

### 緩存失效策略
```python
async def invalidate_daily_cache(self, date: str = None):
    """失效當日相關緩存"""
    target_date = date or datetime.now().date()
    
    cache_keys = [
        f"daily_limit_status:{target_date}",
        f"daily_stats:{target_date}",
        "user_settings:default_user"
    ]
    
    await self._cache_manager.delete_multiple(cache_keys)
```

### 資料庫遷移腳本
```sql
-- 遷移腳本: 001_add_daily_limit_tables.sql
BEGIN;

-- 創建用戶設定表
CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) DEFAULT 'default_user',
    daily_knowledge_limit INTEGER DEFAULT 15 CHECK (daily_knowledge_limit BETWEEN 5 AND 50),
    limit_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 創建每日統計表
CREATE TABLE IF NOT EXISTS daily_knowledge_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    user_id VARCHAR(50) DEFAULT 'default_user',
    isolated_count INTEGER DEFAULT 0,
    enhancement_count INTEGER DEFAULT 0,
    total_limited_count INTEGER GENERATED ALWAYS AS (isolated_count + enhancement_count) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, user_id)
);

-- 創建索引優化查詢
CREATE INDEX IF NOT EXISTS idx_daily_stats_date_user ON daily_knowledge_stats(date, user_id);
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);

-- 插入預設設定
INSERT INTO user_settings (user_id, daily_knowledge_limit, limit_enabled) 
VALUES ('default_user', 15, false) 
ON CONFLICT (user_id) DO NOTHING;

COMMIT;
```

## 📚 相關資源

- **UI/UX參考**: [學習應用最佳實踐](https://uxplanet.org/learning-app-ui-patterns)
- **緩存策略**: 現有 `core/cache_manager.py` 架構
- **資料庫遷移**: 參考 `scripts/migrate_data.py` 模式
- **API 測試**: 使用現有 pytest 框架

## 📝 執行筆記

### 2025-08-15 需求分析
- 用戶明確表達對學習節奏控制的需求
- 重點是 isolated 和 enhancement 兩種類型
- 需要平衡學習進度與複習質量

### 設計決策記錄
1. **Q: 為什麼只限制特定錯誤類型？**
   - A: isolated 和 enhancement 是需要重點複習的類型，限制這些能有效控制複習負擔

2. **Q: 達到上限時應該如何處理？**
   - A: 提供選擇而非強制阻止，保持用戶學習的彈性

3. **Q: 如何確保功能不會被濫用？**
   - A: 合理的上限範圍(5-50)和智能建議系統

---

**重要提醒**: 此功能的核心目的是協助用戶建立可持續的學習節奏，而非限制學習。實施時務必強調其價值並提供充分的用戶控制權。