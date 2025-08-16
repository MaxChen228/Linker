# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Linker is an AI-powered English learning platform that provides translation practice with real-time grading, error analysis, and personalized learning tracking. The system uses Google Gemini API for intelligent sentence generation and grading, with a sophisticated spaced repetition algorithm for optimal learning outcomes.

## Core Architecture

### System Design
```
web/main.py → FastAPI Routes (Pure Async) & SSR
    ↓
core/services/async_knowledge_service.py → AsyncKnowledgeService Layer
    ↓
core/ai_service.py → Gemini API (2.5 Flash/Pro dual-model)
    ↓
core/knowledge.py → Knowledge tracking & spaced repetition
    ↓
PostgreSQL → Database backend
```

### Key Components
- **Backend**: Python 3.9+, FastAPI, Pydantic for API-first architecture
- **Frontend**: Vanilla JavaScript (ES6+) SPA with Jinja2 templates
- **AI Service**: Dual Gemini models - Flash for speed (generation), Pro for quality (grading)
- **Service Layer**: Pure async service architecture with AsyncKnowledgeService (TASK-31 完成)
- **Data Layer**: PostgreSQL database (JSON mode removed)
- **Cache System**: Unified cache management with thread-safe operations and TTL support
- **CSS Architecture**: Unified design system with zero hardcode principle (TASK-35 完成)
- **Design Tokens**: Comprehensive token system for colors, spacing, typography, and dimensions

## Development Commands

### 🚀 主要開發工具：Linker 管理系統 (推薦)

專案提供了功能完整的管理腳本 `linker.sh`，整合所有開發、測試和維護功能：

```bash
# 啟動互動式管理介面（推薦）
./linker.sh

# 直接命令模式
./linker.sh start   # 快速啟動服務
./linker.sh dev     # 開發模式（背景執行 + 自動重載）
./linker.sh stop    # 停止服務
./linker.sh reset   # 重置系統（清空資料庫）
./linker.sh test    # 執行測試套件
./linker.sh help    # 顯示使用說明
```

**Linker 管理系統功能**：
1. **🚀 快速啟動** - 自動設置環境並啟動服務
2. **🔧 開發模式** - 背景執行，檔案變更自動重載
3. **🔄 系統重置** - 清空資料庫並重置為初始狀態
4. **🗄️ 資料庫管理** - 備份、還原、初始化、狀態檢查
5. **⏹️ 停止服務** - 優雅關閉所有服務
6. **🔍 程式碼品質** - Ruff 檢查與自動修復
7. **🧪 執行測試** - 單元、整合、API 測試與覆蓋率
8. **⚙️ 環境設定** - 管理 API Key、資料庫連接等
9. **🔗 快速連結** - 顯示所有重要 URL
10. **ℹ️ 系統資訊** - 查看狀態與統計

詳細使用說明請參考 `docs/guides/LINKER_MANAGER.md`。

### Alternative Commands (舊版命令)

如果偏好使用個別腳本：

```bash
# 快速啟動
./run.sh                         # 啟動開發服務器
uvicorn web.main:app --reload    # 手動啟動

# 系統重置
./reset.sh                       # 重置系統

# 程式碼品質
ruff check .                     # 靜態分析
ruff check . --fix              # 自動修復
ruff format .                   # 格式化代碼

# 測試
pytest                          # 所有測試
pytest -m unit                  # 單元測試
pytest -m integration           # 整合測試
pytest --cov=core --cov=web    # 覆蓋率報告
```

### Database Operations
```bash
# 使用 linker.sh（推薦）
./linker.sh                     # 選擇 4 進入資料庫管理

# 手動操作
python scripts/init_database.py # 初始化結構
python scripts/migrate_data.py  # 遷移資料
python scripts/configure_db.py  # 配置設定
```

### Environment Setup
```bash
# 使用 linker.sh（推薦）
./linker.sh                     # 選擇 8 進行環境設定

# 手動設定
export GEMINI_API_KEY=your-key      # AI 功能必需
export DATABASE_URL=postgresql://... # 資料庫連接
export DEFAULT_DAILY_LIMIT=15       # 每日限額

# 安裝依賴
pip install -r requirements.txt      # 生產依賴
pip install -e ".[dev]"             # 開發依賴
```

## Development Guidelines

### 零硬編碼原則 (Zero Hardcoding) ✅ TASK-35 完成
**已實現**: 專案已達成95.6%零硬編碼率，建立完整的設計令牌系統。

**核心原則**:
- **配置值**: 環境變數 (`.env`) 由 `core/config.py` 載入
- **應用常數**: 定義在模組頂部 (UPPER_SNAKE_CASE)
- **資料驗證**: Pydantic 模型進行嚴格驗證
- **CSS樣式**: 統一設計令牌系統 (`web/static/css/design-system/`)
- **硬編碼值**: 嚴禁魔術數字，全面使用設計令牌

**TASK-35成果** (2025-08-16完成):
- ✅ CSS雙重系統統一
- ✅ RGBA硬編碼清理: 218→3 (98.6%)
- ✅ PX硬編碼清理: 420→25 (94.0%)
- ✅ 總清理率: 638→28 (95.6%)

### 命名規範 (Naming Conventions)

**Python Backend:**
- Variables/Functions: `snake_case` (e.g., `get_user_data`)
- Classes: `PascalCase` (e.g., `KnowledgeManager`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MASTERY_LEVEL`)
- Files: `snake_case.py`

**JavaScript Frontend:**
- Variables/Functions: `camelCase` (e.g., `fetchQuestion`)
- Classes: `PascalCase` (e.g., `SelectionManager`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`)
- Files: `kebab-case.js`, `kebab-case.css`

**CSS:**
- BEM-like naming: `component-name__element--modifier`
- Design tokens: Use CSS variables from `web/static/css/design-system/01-tokens/`
- Zero hardcode: Never use magic numbers, always use design tokens
- Modular structure: Follow `design-system/` hierarchy with proper imports

### Code Style Requirements

1. **Type Annotations**: 所有函式必須包含參數和返回值的類型註解
2. **Docstrings**: 使用 Google style docstrings 為所有公開函式撰寫文檔
3. **Error Handling**: 使用具體的 Exception 子類，FastAPI 路由使用適當的 HTTPException
4. **API Models**: 所有 API 請求/回應必須使用 Pydantic 模型進行驗證
5. **Import Order**: 標準庫、第三方套件、本地模組分組，組間空一行

### Testing Requirements

- **Framework**: Pytest with fixtures and parametrization
- **Coverage Target**: Maintain minimum 90% test coverage
- **Test Organization**: Mirror app structure in `tests/` directory
- **Test Markers**: 
  - `@pytest.mark.unit` - Fast unit tests
  - `@pytest.mark.integration` - Integration tests
  - `@pytest.mark.asyncio` - Async tests
  - `@pytest.mark.external` - Tests requiring external APIs

**Critical**: Never fake test results. All tests must actually execute.

## Workflow Process

### When Making Changes:

1. **理解需求** - Analyze the request thoroughly
3. **遵循模式** - Follow existing patterns in the codebase
4. **執行驗證** - Run linting, formatting, and tests
5. **明確聲明** - Explicitly state validation completion

### Memory MCP Usage Requirements

**CRITICAL**: You MUST use the Memory MCP (Model Context Protocol) to record the current detailed state during major events:

#### When to Use Memory MCP:
- **Major Code Changes**: When implementing new features, refactoring core components, or fixing critical bugs
- **Architecture Decisions**: When making structural changes or design decisions
- **Problem Resolution**: When solving complex issues or debugging difficult problems
- **Migration/Updates**: During database migrations, dependency updates, or configuration changes
- **Task Completion**: Upon completing significant tasks or milestones
- **Error Recovery**: After resolving system errors or recovering from failures

#### What to Record:
- **Current State**: Detailed snapshot of system state before and after changes
- **Decision Rationale**: Why specific approaches were chosen
- **Implementation Details**: Key code changes and their purposes
- **Relationships**: How components interact and depend on each other
- **Known Issues**: Any problems discovered or limitations identified
- **Next Steps**: What needs to be done following the current work

#### How to Use:
1. Create entities for key components, features, or concepts
2. Add observations about their current state and behavior
3. Create relations to show dependencies and interactions
4. Update the knowledge graph as the system evolves
5. Search and reference previous recordings when needed

This ensures continuity across sessions and helps maintain comprehensive understanding of the project's evolution.

### Git Workflow

- Feature branches: `feature/<description>` from `dev`
- Hotfix branches: `hotfix/<description>` for urgent fixes
- Commit format: Follow Conventional Commits (`feat:`, `fix:`, etc.)
- Add `(AI)` suffix to AI-assisted commits for transparency

## Critical System Notes

### Architecture Migration Complete (TASK-31) ✅
**RESOLVED**: The previous database adapter issues have been fully resolved through complete async architecture migration.

Key improvements:
- **AsyncKnowledgeService**: Pure async service layer replaces problematic adapters
- **Event Loop Conflicts**: All `asyncio.new_event_loop()` conflicts eliminated 
- **Performance**: 3-5x concurrent processing improvement with unified async architecture
- **Code Simplification**: 600+ lines of sync wrapper code removed
- **Reliability**: Zero event loop conflicts, stable production operation

### Error Classification System
The system categorizes errors into four types:
- **systematic**: Grammar rules that can be learned
- **isolated**: Individual items requiring memorization
- **enhancement**: Correct but can be improved
- **other**: Miscellaneous errors

### Cache Management System
The system includes a unified cache management architecture:

#### Core Components
- **UnifiedCacheManager**: Thread-safe cache with TTL support
- **LayeredCacheManager**: Category-based cache with different TTL policies
- **CacheSyncManager**: Multi-cache consistency management

#### TTL Policies
- Statistics cache: 60 seconds
- Knowledge points cache: 300 seconds (5 minutes)
- Review candidates cache: 120 seconds (2 minutes)
- Search results cache: 180 seconds (3 minutes)

#### Key Features
- **Thread Safety**: RLock-based protection for concurrent access
- **Auto Expiration**: Automatic cleanup of expired cache entries
- **Performance Monitoring**: Cache hit/miss statistics and reporting
- **Async/Sync Consistency**: Both modes use identical cache logic
- **Smart Invalidation**: Automatic cache clearing on data changes

#### Usage
```python
from core.cache_manager import UnifiedCacheManager, CacheCategories

# Create cache manager
cache = UnifiedCacheManager(default_ttl=300)

# Cache with auto-computation
result = cache.get_or_compute("stats", compute_func, ttl=60)

# Category-based caching
cache.set_with_category(CacheCategories.STATISTICS, "json", data)
```

### Frontend Architecture
- SPA with vanilla JavaScript (`practice-logic.js`)
- Dynamic styling via `style-utils.js` - avoid inline styles
- **Unified CSS Design System** (`web/static/css/design-system/`):
  - `01-tokens/`: Colors, spacing, typography, dimensions, animations
  - `02-base/`: Reset, typography base, accessibility
  - `03-components/`: Buttons, forms, cards, modals, etc.
  - `04-layouts/`: Grid systems and layout utilities
  - `05-utilities/`: Helper classes and utilities
- **Zero Hardcode CSS**: 95.6% hardcode elimination achieved
- All API routes under `/api/` serve JSON to frontend

### Async Service Layer (New Architecture)
The system now uses a pure async service layer for all operations:

#### Usage Pattern
```python
# web/dependencies.py
async def get_knowledge_service() -> AsyncGenerator[AsyncKnowledgeService, None]:
    """Async dependency injection for service layer"""
    db_manager = await create_database_manager()
    try:
        service = AsyncKnowledgeService()
        await service.initialize()  # Initialize DB connection
        yield service
    finally:
        await service.cleanup()  # Clean up resources

# web/routers/example.py
@router.get("/api/example")
async def example_endpoint(
    service: AsyncKnowledgeService = Depends(get_knowledge_service)
):
    """Pure async route using service layer"""
    return await service.get_knowledge_points_async()
```

#### Key Benefits
- **No Event Loop Conflicts**: Pure async eliminates all event loop issues
- **Better Performance**: 3-5x improvement in concurrent processing
- **Simplified Code**: No sync/async bridging code required
- **Resource Efficiency**: Proper async resource management

## Common Development Tasks

- **Add new API route**: Create in `web/routers/` using pure async patterns, inject AsyncKnowledgeService
- **Modify AI prompts**: Edit `core/ai_service.py` generation/grading methods
- **Update knowledge logic**: Modify `core/knowledge.py` and its algorithms
- **Change UI components**: 
  - Templates: Update `web/templates/`
  - Styles: Use design tokens from `web/static/css/design-system/01-tokens/`
  - Pages: Modify `web/static/css/pages/` with zero hardcode principle
- **Add frontend interaction**: Follow patterns in `web/static/js/practice-logic.js`
- **Service layer integration**: Use `core/services/async_knowledge_service.py` for all data operations
- **CSS Styling**: 
  - Use design tokens: `var(--token-name)` instead of hardcoded values
  - Follow modular structure in `design-system/`
  - Never use magic numbers (px, rgba, etc.)

## Task Management System (TODO/)

The project uses a **Pure Manual Task Management System** based on the "Location is State" principle. Task status is determined by file location, not file content.

### 🎯 Core Concept: Location is State

This is a completely manual, zero-dependency task management system where:
- **Moving a file = Changing status**
- **Folder position determines task state**
- **No scripts, no automation, complete transparency**

### 📁 Folder Structure

```
TODO/
├── 01_Pending/         # 📥 Ideas & drafts (未規劃)
├── 02_Todo/            # 📝 Ready to execute (可執行)
├── 03_InProgress/      # 🏃 Currently working (進行中)
├── 04_Review/          # 👀 Completed, awaiting verification (待審查)
└── 05_Done/            # ✅ Archived & completed (已完成)
```

### 🔄 Workflow Process

1. **Planning**: Create task file in `01_Pending/`, refine details, move to `02_Todo/`
2. **Claim**: Move task from `02_Todo/` to `03_InProgress/` (claiming task)
3. **Execute**: Work on task, update execution notes in file
4. **Submit**: Move completed task to `04_Review/` for verification
5. **Archive**: After review approval, move to `05_Done/`

### 📝 Task File Template

Each task file follows this standard format:

```markdown
# TASK-XX: [Clear Task Title]

- **Priority**: [🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW]
- **Estimated Time**: [e.g., 2 hours]
- **Related Components**: [e.g., core/database/adapter.py]
- **Parent Task**: [if subtask, link to parent]

---

### 🎯 Task Objective
(Clear description of what should be achieved)

### ✅ Acceptance Criteria
- [ ] Criterion 1: ...
- [ ] Criterion 2: ...
- [ ] Criterion 3: ...

### 📝 Execution Notes (Optional)
(Ideas, code snippets, issues encountered during execution)

### 🔍 Review Comments (For Reviewer)
(Left empty for reviewer to fill)
```

### ⚠️ Important Principles

- **Focus on 1-3 tasks**: `03_InProgress/` should not exceed 3 files
- **Location determines state**: No need to edit file content to change status
- **Manual control**: No scripts, no automation, completely transparent
- **Regular cleanup**: Periodically archive or delete old tasks from `05_Done/`

### 💡 Usage Examples

```bash
# Create new task
touch TODO/01_Pending/TASK-21-optimize-cache.md
# After planning, move to todo
mv TODO/01_Pending/TASK-21-optimize-cache.md TODO/02_Todo/

# Claim task (start working)
mv TODO/02_Todo/TASK-21-optimize-cache.md TODO/03_InProgress/

# Submit for review
mv TODO/03_InProgress/TASK-21-optimize-cache.md TODO/04_Review/

# Archive after approval
mv TODO/04_Review/TASK-21-optimize-cache.md TODO/05_Done/
```

### 📊 Current Status Overview

Check task counts in each stage:
```bash
ls TODO/01_Pending/ | wc -l    # Pending count
ls TODO/02_Todo/ | wc -l        # Todo count  
ls TODO/03_InProgress/ | wc -l  # In Progress count
ls TODO/04_Review/ | wc -l      # Review count
ls TODO/05_Done/ | wc -l        # Done count
```

### Recent Completed Tasks

#### TASK-35: UI技術債務清理 & 零硬編碼實施 (2025-08-16) 🎉
**STATUS**: 100% 完成 - 達成95.6%零硬編碼率

**Phase完成詳情**:
- ✅ **TASK-35-01**: Critical cleanup (調試文件清理)
- ✅ **TASK-35-02**: CSS架構統一 (components.css → design-system)
- ✅ **TASK-35-03**: RGBA硬編碼清理 (218→3, 98.6%清理率)
- ✅ **TASK-35-04**: PX硬編碼清理 (420→25, 94.0%清理率)

**技術成果**:
- **設計令牌系統**: 完整的token架構 (colors, spacing, typography, dimensions)
- **Alpha透明度系統**: 28個系統化透明度令牌
- **模組化CSS**: 統一的設計系統架構
- **零硬編碼**: 從638個硬編碼值減少到28個合理保留值

#### Legacy Tasks (參考)
- **TASK-31**: Complete Async Architecture Migration (2025-08-15) - 40h, 100% complete 🎉
- **TASK-20A**: Unified Cache Management System (2025-08-15)
- **TASK-19D**: Unified Statistics Logic (2025-08-15)
- **TASK-19B**: Dual-Mode Consistency Verification (2025-08-15)

## DO NOT TOUCH - Critical Files

Unless explicitly permitted, do not modify:
- `.github/workflows/` - CI/CD pipeline configurations
- Database migration files in `scripts/` without understanding impact
- Environment configuration files containing secrets
- **CSS Design System Core** (`web/static/css/design-system/01-tokens/`) - Foundation tokens
- **Design System Index** (`web/static/css/design-system/index.css`) - Master import file

### CSS Design System Guidelines
- **Never hardcode values**: Always use design tokens `var(--token-name)`
- **Follow token hierarchy**: Use semantic tokens over raw values
- **Maintain import structure**: Respect @import dependencies in design-system
- **Zero magic numbers**: All dimensions, colors, spacing must use tokens

## Quality Checklist

Before submitting any changes:
- [ ] Code passes `ruff check .` without errors
- [ ] Code is formatted with `ruff format .`
- [ ] All tests pass with `pytest`
- [ ] Test coverage remains above 90%
- [ ] **Zero hardcode compliance**: No magic numbers, use design tokens
- [ ] **CSS follows design system**: Use `var(--token-name)` format
- [ ] Type annotations are complete
- [ ] Docstrings are provided for public functions
- [ ] Follows existing code patterns
- [ ] No sensitive information in commits

### CSS-Specific Checklist
- [ ] No hardcoded px values (use spacing tokens)
- [ ] No hardcoded rgba/hex colors (use color tokens)
- [ ] Proper design-system imports
- [ ] Semantic token usage over raw tokens
- [ ] Responsive design with breakpoint tokens