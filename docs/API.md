# API Reference (v4.0)

本文件描述了 Linker 學習平台最新的 API 端點，對應專案版本 v4.0+。

## 基礎 URL
```
http://localhost:8000
```

## 認證
所有 API 端點目前皆不需認證。AI 服務的 API 金鑰由後端伺服器透過環境變數管理。

---

## 練習與批改 (Practice & Grading)

核心的練習流程 API。

### 1. 生成練習題目
```http
POST /api/generate-question
```
根據指定模式和條件生成一個新的練習題目。

**Request Body:**
```json
{
  "mode": "new" | "review" | "pattern",
  "length": "short" | "medium" | "long",
  "level": 1 | 2 | 3 | 4 | 5,
  "pattern_id": "GP001" 
}
```
- `mode` (string, required): 練習模式。
  - `new`: 全新題目。
  - `review`: 根據待複習知識點出題。
  - `pattern`: 根據指定文法句型出題。
- `length` (string, required): 句子長度。
- `level` (integer, required): 難度等級 (1-5)。
- `pattern_id` (string, optional): 在 `pattern` 模式下指定要練習的句型 ID。若不提供，則隨機選擇。

**Success Response (200 OK):**
```json
{
  "success": true,
  "chinese": "這不僅是他的責任，也是他的榮幸。",
  "hint": "練習句型：Not only... but also...",
  "target_point_ids": [12, 15],
  "target_points": [
    {
      "id": 12,
      "key_point": "倒裝結構: Not only...",
      "category": "systematic",
      "mastery_level": 0.25
    }
  ],
  "target_points_description": "本題考察：倒裝結構"
}
```

### 2. 批改翻譯答案
```http
POST /api/grade-answer
```
提交使用者翻譯，由 AI 進行批改、評分並返回詳細分析。

**Request Body:**
```json
{
  "chinese": "這不僅是他的責任，也是他的榮幸。",
  "english": "Not only this is his duty, but also his honor.",
  "mode": "new" | "review" | "pattern",
  "target_point_ids": [12, 15]
}
```
- `chinese` (string, required): 原始中文題目。
- `english` (string, required): 使用者的英文翻譯。
- `mode` (string, required): 練習模式。
- `target_point_ids` (array, optional): 在 `review` 模式下，本次練習針對的知識點 ID 列表。

**Success Response (200 OK):**
```json
{
  "success": true,
  "score": 85,
  "is_generally_correct": false,
  "feedback": "Not only is this his duty, but it is also his honor.",
  "error_analysis": [
    {
      "category": "systematic",
      "key_point_summary": "倒裝錯誤: Not only...",
      "original_phrase": "Not only this is",
      "correction": "Not only is this",
      "explanation": "當 'Not only' 放在句首時，其後的主要子句需要使用倒裝結構，即助動詞或be動詞要移到主詞前面。",
      "severity": "major"
    }
  ]
}
```

---

## 知識點管理 (Knowledge Point Management)

管理使用者錯誤記錄所生成的知識點。

### 1. 獲取知識點詳情
```http
GET /api/knowledge/{point_id}
```
**Success Response (200 OK):**
```json
{
  "id": 12,
  "key_point": "倒裝錯誤: Not only...",
  "category": "systematic",
  "subtype": "inversion",
  "explanation": "當 'Not only' 放在句首時...",
  "original_phrase": "Not only this is",
  "correction": "Not only is this",
  "mastery_level": 0.25,
  "mistake_count": 1,
  "correct_count": 0,
  "created_at": "2025-08-13T21:50:00Z",
  "last_seen": "2025-08-13T21:50:00Z",
  "next_review": "2025-08-14T21:50:00Z",
  "is_deleted": false,
  "tags": ["grammar", "inversion"],
  "custom_notes": "這個錯誤經常犯，需要特別注意。",
  "version_history": [...]
}
```

### 2. 編輯知識點
```http
PUT /api/knowledge/{point_id}
```
**Request Body:**
```json
{
  "key_point": "新的重點描述",
  "explanation": "更新後的詳細解釋",
  "custom_notes": "新的使用者筆記"
}
```
*所有欄位均為可選。*

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "知識點已更新",
  "history": {
    "timestamp": "2025-08-13T22:00:00Z",
    "before": { "custom_notes": "..." },
    "after": { "custom_notes": "新的使用者筆記" },
    "changed_fields": ["custom_notes"]
  }
}
```

### 3. 軟刪除知識點 (移至回收站)
```http
DELETE /api/knowledge/{point_id}
```
**Request Body:**
```json
{
  "reason": "這個知識點已經掌握了"
}
```
**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "知識點已移至回收站"
}
```

### 4. 從回收站復原知識點
```http
POST /api/knowledge/{point_id}/restore
```
**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "知識點已復原"
}
```

### 5. 獲取回收站列表
```http
GET /api/knowledge/trash/list
```
**Success Response (200 OK):**
```json
{
  "success": true,
  "count": 1,
  "items": [
    {
      "id": 10,
      "key_point": "拼寫錯誤: recieve",
      "deleted_at": "2025-08-10T10:00:00Z",
      "deleted_reason": "已掌握"
    }
  ]
}
```

### 6. 永久清理回收站
```http
POST /api/knowledge/trash/clear?days=30
```
永久刪除回收站中超過指定天數的項目。

**Success Response (200 OK):**
```json
{
  "success": true,
  "deleted_count": 5,
  "message": "已永久刪除 5 個超過 30 天的知識點"
}
```

### 7. 更新知識點標籤
```http
POST /api/knowledge/{point_id}/tags
```
**Request Body:**
```json
["grammar", "inversion", "C1-level"]
```
**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "標籤已更新",
  "tags": ["grammar", "inversion", "C1-level"]
}
```

### 8. 更新知識點筆記
```http
POST /api/knowledge/{point_id}/notes
```
**Request Body:**
```json
"這是我的自訂筆記內容。"
```
**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "筆記已更新",
  "notes": "這是我的自訂筆記內容。"
}
```

---

## 文法句型 (Grammar Patterns)

### 1. 獲取所有文法句型
```http
GET /api/patterns
```
獲取所有可用於練習的文法句型摘要列表。

**Success Response (200 OK):**
```json
{
  "success": true,
  "patterns": [
    {
      "id": "GP001",
      "pattern": "It is ... that ... (強調句)",
      "category": "句子結構",
      "formula": "It + be動詞 + 強調部分 + that/who + ...",
      "core_concept": "用於強調句子中的特定部分，如主詞、受詞或副詞片語。"
    }
  ]
}
```

---

## 系統與調試 (System & Debug)

### 1. 健康檢查
```http
GET /healthz
```
**Success Response (200 OK):**
```json
{
  "status": "ok"
}
```

### 2. 獲取調試資訊
```http
GET /debug-info
```
**Success Response (200 OK):**
```json
{
  "environment": "development",
  "log_level": "DEBUG",
  "data_dir": "/Users/chenliangyu/Desktop/linker-cli/data",
  "settings": { ... }
}
```

---

## 錯誤回應格式
所有端點在發生錯誤時，都會回傳標準格式的 JSON。

**Error Response (e.g., 400, 404, 500):**
```json
{
  "detail": "Human-readable error message"
}
```
*FastAPI 預設的錯誤回應格式為 `{"detail": "..."}`。*
