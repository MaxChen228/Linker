# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Linker is an AI-powered English learning platform using Gemini API for intelligent sentence generation and grading.

## Key Commands

```bash
# Development
./run.sh                    # Start development server
uvicorn web.main:app --reload --port 8000

# Code Quality
ruff check .               # Lint check
ruff format .              # Format code
pytest                     # Run tests

# Environment
export GEMINI_API_KEY=your-key
```

## Architecture

```
web/main.py → Routes & SSR
    ↓
core/ai_service.py → Gemini API (2.5 Flash/Pro)
    ↓
core/knowledge.py → Knowledge tracking
    ↓
data/*.json → Local storage
```

## Important Notes

- **CSS Architecture**: Design system with @import - DO NOT delete subfiles
- **Dual AI Models**: Flash for generation (speed), Pro for grading (quality)
- **Error Categories**: systematic, isolated, enhancement, other
- **No dist folder needed**: CSS works with current structure

## Common Tasks

- Add new route: `web/routers/`
- Modify AI prompts: `core/ai_service.py`
- Update knowledge logic: `core/knowledge.py`
- Change UI: `web/templates/` and `web/static/css/pages/`

- AI 開發規範 (AI Development Constitution)

    1 # Linker 專案 AI 開發最高指導原則 (v1.0)
    2
    3 ## 1. 核心使命 (Core Mission)
    4
    5 你的首要任務是協助開發 Linker 專案，一個由 FastAPI 和 Vanilla JS 驅動的 AI 英語學習平台。你必須嚴格遵守本文件定義的所有規範，以確保程式碼的**一致性、可維護性、可讀性和高品質**。
      **杜絕任何形式的技術債、硬編碼和風格不一致**。
    6
    7 ## 2. 專案架構與技術棧
    8
    9 在進行任何修改前，你必須回顧並理解專案的架構。
   10
   11 *   **後端**: Python 3.9+, FastAPI, Pydantic
   12 *   **前端**: Vanilla JavaScript (ES6+), Jinja2, 模組化 CSS
   13 *   **資料**: 本地 JSON 檔案 (`data/*.json`)，並有向 PostgreSQL 遷移的長期計畫 (`docs/DATABASE_MIGRATION_PLAN.md`)。
   14 *   **品質**: `ruff check .` (風格檢查), `ruff format .` (格式化), `pytest` (單元測試)。
   15
   16 **關鍵目錄結構:**
   17 *   `core/`: 核心業務邏輯 (AI 服務、知識點管理)。**與 Web 層解耦**。
   18 *   `web/`: Web 服務層。
   19     *   `routers/`: API 端點定義。
   20     *   `static/`: 前端資源 (CSS, JS)。
   21     *   `templates/`: Jinja2 HTML 模板。
   22 *   `data/`: 應用程式資料。**絕不直接在程式碼中硬編碼路徑**，應透過配置 (`core/config.py`) 獲取。
   23 *   `docs/`: **你的知識來源**。在不確定時，優先查閱此處文件。
   24
   25 ## 3. 開發黃金律 (The Golden Rules)
   26
   27 ### 3.1. **零硬編碼 (Zero Hardcoding)**
   28 嚴禁在程式碼中出現任何硬編碼的字串、路徑、數字或配置。所有此類值必須定義在：
   29 *   **環境變數** (`.env`) 並由 `core/config.py` 中的 Pydantic `Settings` 類載入。
   30 *   **應用常數** (例如，定義在 `core/constants.py` 或相關模組頂部的大寫變數)。
   31 *   **API 回應模型** (Pydantic Models)。
   32
   33 **錯誤範例**: `file_path = "data/knowledge.json"`
   34 **正確範例**: `file_path = settings.KNOWLEDGE_DATA_PATH`
   35
   36 ### 3.2. **遵循既有模式 (Follow Existing Patterns)**
   37 在添加或修改功能前，**必須**先閱讀相關模組的現有程式碼。你的新程式碼必須與周圍的程式碼在風格、結構和命名上**完全一致**。
   38 *   **新增 API 端點?** -> 參考 `web/routers/knowledge.py` 的結構。
   39 *   **修改知識點邏輯?** -> 參考 `core/knowledge.py` 的方法。
   40 *   **添加前端互動?** -> 參考 `web/static/js/practice-logic.js` 的風格和 `DYNAMIC_STYLING_GUIDE.md`。
   41
   42 ### 3.3. **命名規範 (Naming Conventions)**
   43 *   **Python (後端)**:
   44     *   變數、函式、方法: `snake_case` (e.g., `get_user_data`)。
   45     *   類別: `PascalCase` (e.g., `KnowledgeManager`)。
   46     *   常數: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MASTERY_LEVEL`)。
   47     *   Pydantic 模型: `PascalCase` (e.g., `KnowledgePointResponse`)。
   48 *   **JavaScript (前端)**:
   49     *   變數、函式: `camelCase` (e.g., `fetchQuestion`)。
   50     *   類別: `PascalCase` (e.g., `SelectionManager`)。
   51     *   常數: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`)。
   52 *   **CSS**:
   53     *   遵循 BEM-like 命名法，如 `component-name__element--modifier` (e.g., `.card__title--highlighted`)。
   54     *   參考 `web/static/css/components/` 下的現有命名。
   55 *   **檔案名稱**:
   56     *   Python: `snake_case.py`。
   57     *   JavaScript/CSS: `kebab-case.js`, `kebab-case.css`。
   58
   59 ### 3.4. **資料模型驅動 (Model-Driven Development)**
   60 所有 API 的請求和回應體都**必須**使用 Pydantic 模型進行定義和驗證。這能確保資料的一致性和類型安全。
   61 *   **位置**: 在相應的 router 檔案中或 `web/models.py` 中定義。
   62 *   **原則**: 清晰、明確，並包含欄位描述。
   63
   64 ### 3.5. **前端樣式與互動 (Frontend Styling & Interaction)**
   65 *   **嚴格遵守 `DYNAMIC_STYLING_GUIDE.md`**。
   66 *   **禁止**直接在 HTML 中寫行內樣式 (`style="..."`)，除非是為了綁定 CSS 自訂屬性 (`--variable`)。
   67 *   **優先使用** `style-utils.js` 提供的工具函式來操作動態樣式。
   68 *   所有新組件的 CSS 都應在 `web/static/css/components/` 中建立獨立檔案，並在 `main.css` 中 `@import`。
   69
   70 ## 4. 工作流程 (Workflow)
   71
   72 1.  **理解需求**: 分析使用者請求。
   73 2.  **情境載入**: 使用你的記憶功能載入相關檔案。
   74     *   **修改 API?** -> `#web/routers/api_knowledge.py`, `#docs/API.md`
   75     *   **修改 UI?** -> `#web/templates/practice.html`, `#web/static/css/pages/practice.css`, `#DYNAMIC_STYLING_GUIDE.md`
   76 3.  **規劃**: 簡要說明你的修改計畫，並明確指出將遵循哪一條規範。
   77 4.  **執行**: 進行程式碼修改。
   78 5.  **驗證**:
   79     *   **執行 `ruff check .` 和 `ruff format .`** 確保程式碼品質。
   80     *   **執行 `pytest`** 確保沒有破壞現有功能。
   81     *   **聲明**: 在回應中明確表示你已完成驗證步驟。
   82
   83 ## 5. 常用指令與參考
   84
   85 *   **啟動開發伺服器**: `./run.sh`
   86 *   **程式碼檢查**: `ruff check .`
   87 *   **程式碼格式化**: `ruff format .`
   88 *   **執行測試**: `pytest`
   89 *   **API 文件**: `docs/API.md`
   90 *   **架構總覽**: `docs/ARCHITECTURE.md`
   91 *   **樣式指南**: `DYNAMIC_STYLING_GUIDE.md`
   92 *   **資料庫遷移計畫**: `docs/DATABASE_MIGRATION_PLAN.md` (在處理資料層時，需考慮此長期目標)
   93
   94 ---
