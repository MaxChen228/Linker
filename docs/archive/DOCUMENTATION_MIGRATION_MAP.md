# 文檔遷移對照表

## 遷移策略總覽

| 狀態 | 說明 |
|------|------|
| ✅ 已完成 | 內容已遷移到新位置 |
| 🔄 進行中 | 正在遷移 |
| ⏳ 待處理 | 尚未開始遷移 |
| 🗑️ 廢棄 | 過時內容，將被刪除 |
| 📦 歸檔 | 移至 archive 目錄 |

## 詳細遷移對照

### 根目錄文檔

| 原文檔 | 狀態 | 遷移目標 | 說明 |
|--------|------|----------|------|
| **README.md** | ✅ | README_NEW.md → README.md | 精簡為入口頁面，詳細內容移至 docs/ |
| **CLAUDE.md** | ⏳ | 保留 | AI 助手專用，需更新連結 |
| **PROJECT_HANDOVER.md** | ⏳ | docs/archive/ + 部分內容分散 | 歷史文檔，有用內容提取 |
| **QUICK_REFERENCE.md** | ⏳ | 合併到 docs/index.md | 作為快速索引整合 |
| **CHANGELOG.md** | ⏳ | 保留 | 版本記錄，位置不變 |
| **VERSION_MIGRATION_DOCS.md** | 📦 | docs/archive/ | 歷史遷移記錄 |
| **MCP_SETUP.md** | ⏳ | docs/guides/integrations.md | 整合到第三方集成文檔 |

### docs/ 目錄文檔

| 原文檔 | 狀態 | 遷移目標 | 內容分配 |
|--------|------|----------|----------|
| **QUICK_START.md** | ✅ | getting-started/quick-start.md | 統一快速開始 |
| **DEVELOPMENT.md** | ⏳ | guides/developer-guide.md | 開發指南 |
| **DEPLOYMENT.md** | ⏳ | guides/deployment.md | 部署指南 |
| **CONFIGURATION.md** | ✅ | getting-started/configuration.md | 配置指南 |
| **API.md** | ⏳ | reference/api.md | API 參考 |
| **ARCHITECTURE.md** | ⏳ | reference/architecture.md | 架構文檔 |
| **LOGGING.md** | ⏳ | reference/logging.md | 日誌系統 |
| **DESIGN-SYSTEM-COMPLETE.md** | ⏳ | design/design-system.md | 設計系統 |

## 內容整合計劃

### 重複內容合併

#### 1. 環境設置（15處重複）
**原位置**:
- README.md#快速開始
- CLAUDE.md#開發指引
- PROJECT_HANDOVER.md#環境設置
- QUICK_REFERENCE.md#環境變數
- docs/DEVELOPMENT.md#環境配置
- docs/CONFIGURATION.md
- docs/DEPLOYMENT.md#環境變數
- 其他...

**新位置**: `docs/getting-started/configuration.md`（已完成）

#### 2. 安裝步驟（8處重複）
**原位置**:
- README.md#安裝
- CLAUDE.md#啟動專案
- PROJECT_HANDOVER.md#快速開始
- QUICK_REFERENCE.md#快速啟動
- docs/DEVELOPMENT.md#開發環境設置
- docs/DEPLOYMENT.md#安裝
- 其他...

**新位置**: `docs/getting-started/installation.md`（已完成）

#### 3. API 文檔（5處重複）
**原位置**:
- docs/API.md
- PROJECT_HANDOVER.md#API說明
- README.md#API使用
- docs/DEVELOPMENT.md#API開發
- CLAUDE.md#核心功能

**新位置**: `docs/reference/api.md`

#### 4. 架構說明（3處重複）
**原位置**:
- docs/ARCHITECTURE.md
- PROJECT_HANDOVER.md#系統架構
- README.md#專案結構

**新位置**: `docs/reference/architecture.md`

## 新增文檔

| 文檔 | 位置 | 狀態 | 說明 |
|------|------|------|------|
| **文檔索引** | docs/index.md | ✅ | 所有文檔入口 |
| **安裝指南** | docs/getting-started/installation.md | ✅ | 統一安裝說明 |
| **配置指南** | docs/getting-started/configuration.md | ✅ | 統一配置說明 |
| **待辦事項** | docs/TODO.md | ✅ | 任務追蹤 |
| **用戶手冊** | docs/guides/user-guide.md | ⏳ | 終端用戶指南 |
| **資料結構** | docs/reference/database.md | ⏳ | 資料模型文檔 |
| **貢獻指南** | CONTRIBUTING.md | ⏳ | 貢獻規範 |
| **整合指南** | docs/guides/integrations.md | ⏳ | 第三方整合 |

## 執行步驟

### Phase 1: 準備工作（已完成）
- [x] 創建新目錄結構
- [x] 建立文檔索引
- [x] 創建統一安裝/配置文檔
- [x] 創建 TODO.md

### Phase 2: 內容遷移（進行中）
- [ ] 遷移 API 文檔
- [ ] 遷移架構文檔
- [ ] 遷移開發指南
- [ ] 遷移部署指南

### Phase 3: 清理與優化
- [ ] 刪除重複內容
- [ ] 更新所有內部連結
- [ ] 歸檔舊文檔
- [ ] 更新 README.md

### Phase 4: 驗證與發布
- [ ] 檢查所有連結
- [ ] 確認無內容遺失
- [ ] 更新 CHANGELOG
- [ ] 通知團隊成員

## 預期結果

### Before
```
24 個文檔，4347 行
大量重複內容
結構混亂
```

### After
```
15 個文檔，約 3000 行
零重複內容
清晰的層級結構
```

## 風險與對策

| 風險 | 影響 | 對策 |
|------|------|------|
| 連結失效 | 用戶找不到文檔 | 保留重定向，逐步過渡 |
| 內容遺失 | 重要資訊丟失 | 先歸檔再刪除，保留備份 |
| 團隊混亂 | 開發效率降低 | 提前通知，提供對照表 |

---

> 📅 開始日期：2024-12-11  
> 📅 預計完成：2024-12-18  
> 👤 負責人：文檔維護團隊