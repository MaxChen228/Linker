# TASK-22: 批改完成後知識點確認/刪除功能

- **Priority**: 🟠 HIGH
- **Estimated Time**: 8-10 hours
- **Related Components**: 
  - `web/static/js/practice-logic.js`
  - `web/routers/practice.py`
  - `core/knowledge.py`
  - `web/static/css/components/practice.css`
  - `web/templates/practice.html`
- **Parent Task**: None

---

## 🎯 Task Objective

實現批改完成後的知識點確認機制，讓用戶可以在批改結果展示介面選擇是否將錯誤添加到知識庫，或直接刪除。取代現有的自動添加機制，提供更好的用戶控制。

## 📊 Current System Analysis

### 現有流程分析
1. **自動添加機制**：
   - 位置：`core/knowledge.py` → `save_mistake()` → `_process_error()`
   - 觸發：當 `is_generally_correct = False` 時自動執行
   - 行為：自動將所有錯誤分析結果加入知識庫

2. **依賴鏈分析**：
```
用戶提交答案
    ↓
web/routers/practice.py::grade_answer_api()
    ↓
ai_service.grade_translation() [AI批改]
    ↓
knowledge.save_mistake() [自動保存]
    ↓
_process_error() [對每個錯誤]
    ↓
自動創建/更新 KnowledgePoint
```

3. **前端呈現流程**：
```
practice-logic.js::submitAnswer()
    ↓
fetch('/api/grade-answer')
    ↓
renderSandboxResult() [展示結果]
    ↓
顯示錯誤分析列表（僅展示，無交互）
```

## ✅ Acceptance Criteria

### 功能需求
- [ ] 批改完成後不自動添加知識點到知識庫
- [ ] 在批改結果介面顯示每個錯誤的確認/刪除按鈕
- [ ] 支援批量確認（全部添加）和批量刪除（全部忽略）
- [ ] 確認後才將知識點添加到知識庫
- [ ] 提供視覺反饋顯示哪些已確認/已刪除
- [ ] 保留練習歷史記錄（不受確認/刪除影響）

### 技術需求
- [ ] 新增暫存機制，暫時保存待確認的知識點
- [ ] 實現新的 API 端點處理確認/刪除請求
- [ ] 前端狀態管理支援待確認狀態
- [ ] 向後兼容：提供配置選項切換自動/手動模式

## 🔧 Implementation Plan

### Phase 1: 後端架構調整（3小時）

#### 1.1 修改批改流程
```python
# web/routers/practice.py
@router.post("/api/grade-answer")
async def grade_answer_api(request: GradeAnswerRequest):
    # ... AI 批改邏輯 ...
    
    # 新增：生成待確認的知識點數據
    pending_points = []
    if not is_correct:
        for error in result.get("error_analysis", []):
            pending_points.append({
                "id": generate_temp_id(),
                "error": error,
                "chinese_sentence": chinese,
                "user_answer": english,
                "correct_answer": result.get("overall_suggestion", "")
            })
    
    # 返回待確認的知識點，而非自動保存
    return JSONResponse({
        "success": True,
        **result,
        "pending_knowledge_points": pending_points,
        "auto_save": False  # 標記為手動確認模式
    })
```

#### 1.2 新增確認/刪除 API
```python
# web/routers/practice.py
@router.post("/api/confirm-knowledge-points")
async def confirm_knowledge_points(request: ConfirmKnowledgeRequest):
    """確認並保存選中的知識點"""
    knowledge = await get_knowledge_manager_async_dependency()
    
    confirmed_ids = []
    for point_data in request.confirmed_points:
        # 調用現有的 _process_error 邏輯
        point_id = knowledge.add_knowledge_point_from_error(
            point_data["chinese_sentence"],
            point_data["user_answer"],
            point_data["error"],
            point_data["correct_answer"]
        )
        confirmed_ids.append(point_id)
    
    return JSONResponse({
        "success": True,
        "confirmed_count": len(confirmed_ids),
        "point_ids": confirmed_ids
    })
```

### Phase 2: 前端交互設計（4小時）

#### 2.1 修改結果展示介面
```javascript
// web/static/js/practice-logic.js
renderSandboxResult(question) {
    const result = question.gradeResult;
    const pendingPoints = result.pending_knowledge_points || [];
    
    // 新增：渲染待確認的知識點列表
    const pendingList = pendingPoints.map(point => `
        <div class="pending-point" data-point-id="${point.id}">
            <div class="error-content">
                <span class="error-type">${point.error.type}</span>
                <span class="error-text">${point.error.key_point_summary}</span>
            </div>
            <div class="point-actions">
                <button class="btn-confirm-point" data-point-id="${point.id}">
                    <i class="fas fa-check"></i> 加入知識庫
                </button>
                <button class="btn-ignore-point" data-point-id="${point.id}">
                    <i class="fas fa-times"></i> 忽略
                </button>
            </div>
        </div>
    `).join('');
    
    // 新增批量操作按鈕
    const batchActions = `
        <div class="batch-actions">
            <button class="btn-confirm-all">全部加入</button>
            <button class="btn-ignore-all">全部忽略</button>
        </div>
    `;
}
```

#### 2.2 實現確認/刪除邏輯
```javascript
// 單個確認
async confirmKnowledgePoint(pointId) {
    const point = this.pendingPoints.get(pointId);
    if (!point) return;
    
    const response = await this.fetchAPI('/api/confirm-knowledge-points', {
        confirmed_points: [point]
    });
    
    if (response.success) {
        // 更新UI狀態
        this.markPointAsConfirmed(pointId);
        this.showNotification('已加入知識庫', 'success');
    }
}

// 批量確認
async confirmAllPoints() {
    const points = Array.from(this.pendingPoints.values())
        .filter(p => p.status === 'pending');
    
    if (points.length === 0) return;
    
    const response = await this.fetchAPI('/api/confirm-knowledge-points', {
        confirmed_points: points
    });
    
    if (response.success) {
        points.forEach(p => this.markPointAsConfirmed(p.id));
        this.showNotification(`已加入 ${points.length} 個知識點`, 'success');
    }
}
```

### Phase 3: UI/UX 優化（2小時）

#### 3.1 視覺狀態設計
```css
/* web/static/css/components/practice.css */
.pending-point {
    padding: 12px;
    border: 1px solid var(--border-light);
    border-radius: 8px;
    margin-bottom: 8px;
    transition: all 0.3s ease;
}

.pending-point.confirmed {
    background: var(--success-light);
    opacity: 0.7;
}

.pending-point.ignored {
    background: var(--gray-light);
    opacity: 0.5;
    text-decoration: line-through;
}

.point-actions {
    display: flex;
    gap: 8px;
    margin-top: 8px;
}

.btn-confirm-point {
    background: var(--success-color);
    color: white;
}

.btn-ignore-point {
    background: var(--gray-color);
    color: white;
}

.batch-actions {
    display: flex;
    justify-content: space-between;
    padding: 16px;
    border-top: 2px solid var(--border-default);
    margin-top: 16px;
}
```

### Phase 4: 配置與兼容性（1小時）

#### 4.1 添加配置選項
```python
# core/config.py
class PracticeSettings(BaseSettings):
    AUTO_SAVE_KNOWLEDGE_POINTS: bool = False  # 預設為手動確認
    SHOW_CONFIRMATION_UI: bool = True
```

#### 4.2 向後兼容處理
```python
# 根據配置決定行為
if settings.AUTO_SAVE_KNOWLEDGE_POINTS:
    # 使用舊的自動保存邏輯
    knowledge.save_mistake(...)
else:
    # 返回待確認的知識點
    return pending_points
```

## 📝 Testing Requirements

### 單元測試
- [ ] 測試待確認知識點的生成邏輯
- [ ] 測試確認/刪除 API 的正確性
- [ ] 測試批量操作的事務性

### 整合測試
- [ ] 測試完整的批改→確認→保存流程
- [ ] 測試網路異常時的處理
- [ ] 測試並發確認的資料一致性

### UI 測試
- [ ] 測試按鈕點擊響應
- [ ] 測試視覺狀態轉換
- [ ] 測試批量操作的用戶體驗

## 🚨 Risk Assessment

### 技術風險
1. **資料一致性**：確認操作可能與其他操作衝突
   - 緩解：使用事務處理確認操作
   
2. **性能影響**：批量確認可能造成延遲
   - 緩解：實現批次處理和進度顯示

3. **狀態管理複雜性**：前端需要管理更多狀態
   - 緩解：使用清晰的狀態機模型

### 用戶體驗風險
1. **增加操作步驟**：可能降低學習效率
   - 緩解：提供快捷鍵和批量操作
   
2. **用戶困惑**：不理解為何需要確認
   - 緩解：添加說明文字和引導

## 🔄 Migration Strategy

1. **階段一**：實現新功能但預設關閉
2. **階段二**：小範圍測試用戶開啟
3. **階段三**：根據反饋調整後全面推出
4. **階段四**：移除舊的自動保存邏輯

## 📚 Related Documentation

- [知識點管理系統設計文檔](../docs/knowledge-system.md)
- [AI 批改服務接口文檔](../docs/ai-service-api.md)
- [前端狀態管理指南](../docs/frontend-state.md)

## 🔍 Review Comments
(待審查者填寫)