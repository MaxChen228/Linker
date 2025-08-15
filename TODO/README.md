# 📋 純手動任務管理系統 (Manual Task Management System)

## 🎯 核心理念：位置即狀態 (Location is State)

這是一個完全手動、零依賴的任務管理系統。任務的狀態由其所在的**文件夾位置**決定，而非文件內容。移動文件 = 改變狀態。

## 📁 文件夾結構

```
TODO/
├── 01_Pending/         # 📥 待處理區 (想法與草稿)
├── 02_Todo/            # 📝 待辦區 (已規劃，可執行)
├── 03_InProgress/      # 🏃 進行中 (您正在處理的任務)
├── 04_Review/          # 👀 審查區 (已完成，待驗證)
└── 05_Done/            # ✅ 完成區 (已歸檔)
```

### 各文件夾說明

- **01_Pending**: 新想法、未經詳細規劃的任務入口
- **02_Todo**: 已評估和規劃，準備執行的任務池
- **03_InProgress**: 當前處理中的任務（建議限制 1-3 個）
- **04_Review**: 已完成，待審查驗證的任務
- **05_Done**: 通過驗證，已歸檔的完成任務

## 📝 任務文件範本

每個任務文件建議使用以下格式：

```markdown
# TASK-XX: [清晰的任務標題]

- **優先級**: [🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW]
- **預計時間**: [例如：2 小時]
- **關聯組件**: [例如：core/database/adapter.py]
- **父任務**: [如果是子任務，連結到父任務]

---

### 🎯 任務目標
(清晰描述這個任務完成後要達到的具體成果)

### ✅ 驗收標準 (Acceptance Criteria)
- [ ] 標準一：...
- [ ] 標準二：...
- [ ] 標準三：...

### 📝 執行筆記 (Optional)
(執行過程中的想法、程式碼片段或遇到的問題)

### 🔍 審查意見 (For Reviewer)
(留空，供 reviewer 填寫)
```

## 🔄 工作流程

### 1️⃣ 規劃與待辦 (Planning)
1. 在 `01_Pending/` 創建新任務文件
2. 完善任務詳情後，移動至 `02_Todo/`

### 2️⃣ 選取與執行 (Claim & Execute)
1. 從 `02_Todo/` 選擇任務
2. 移動至 `03_InProgress/`（即認領任務）
3. 開始工作，記錄進度

### 3️⃣ 完成與提交 (Complete & Submit)
1. 完成所有驗收標準
2. 移動至 `04_Review/` 提交審查

### 4️⃣ 審查與歸檔 (Review & Archive)
- **通過**: 移動至 `05_Done/`
- **需修改**: 添加審查意見，移回 `03_InProgress/`

## 💡 使用範例

### 創建新任務
```bash
# 在 01_Pending 創建新任務
touch TODO/01_Pending/TASK-21-optimize-cache.md
# 編輯任務詳情...
# 規劃完成後移至待辦
mv TODO/01_Pending/TASK-21-optimize-cache.md TODO/02_Todo/
```

### 認領任務
```bash
# 選擇一個任務開始工作
mv TODO/02_Todo/TASK-21-optimize-cache.md TODO/03_InProgress/
```

### 提交審查
```bash
# 完成後提交審查
mv TODO/03_InProgress/TASK-21-optimize-cache.md TODO/04_Review/
```

### 歸檔完成
```bash
# 審查通過後歸檔
mv TODO/04_Review/TASK-21-optimize-cache.md TODO/05_Done/
```

## 🚀 快速開始

1. 選擇一個想法，在 `01_Pending/` 創建任務文件
2. 使用範本填寫任務詳情
3. 準備好後移至 `02_Todo/`
4. 開始工作時移至 `03_InProgress/`
5. 完成後移至 `04_Review/`
6. 通過審查後移至 `05_Done/`

## ⚠️ 重要原則

- **一次專注 1-3 個任務**: `03_InProgress/` 不應超過 3 個文件
- **位置決定狀態**: 不需要編輯文件內容來改變狀態
- **手動控制一切**: 無腳本、無自動化、完全透明
- **定期清理**: 定期將 `05_Done/` 的舊任務歸檔或刪除

## 📊 狀態總覽

隨時使用以下命令查看各狀態任務數量：

```bash
# 查看各文件夾任務數
ls TODO/01_Pending/ | wc -l    # 待處理數
ls TODO/02_Todo/ | wc -l        # 待辦數
ls TODO/03_InProgress/ | wc -l  # 進行中數
ls TODO/04_Review/ | wc -l      # 待審查數
ls TODO/05_Done/ | wc -l        # 已完成數
```

---

這個系統的美在於其**簡單性**。沒有隱藏的邏輯，沒有複雜的腳本，只有文件和文件夾。您完全掌控一切。