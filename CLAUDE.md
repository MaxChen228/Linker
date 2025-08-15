# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Linker is an AI-powered English learning platform that provides translation practice with real-time grading, error analysis, and personalized learning tracking. The system uses Google Gemini API for intelligent sentence generation and grading, with a sophisticated spaced repetition algorithm for optimal learning outcomes.

## Core Architecture

### System Design
```
web/main.py → FastAPI Routes & SSR
    ↓
core/ai_service.py → Gemini API (2.5 Flash/Pro dual-model)
    ↓
core/knowledge.py → Knowledge tracking & spaced repetition
    ↓
data/*.json / PostgreSQL → Dual storage backend
```

### Key Components
- **Backend**: Python 3.9+, FastAPI, Pydantic for API-first architecture
- **Frontend**: Vanilla JavaScript (ES6+) SPA with Jinja2 templates
- **AI Service**: Dual Gemini models - Flash for speed (generation), Pro for quality (grading)
- **Data Layer**: JSON files (default) with PostgreSQL migration support
- **Cache System**: Unified cache management with thread-safe operations and TTL support
- **CSS Architecture**: Modular design system with @import - DO NOT delete subfiles

## Development Commands

### Quick Start
```bash
# Launch development server (auto-setup venv, install deps)
./run.sh
# Access at http://localhost:8000

# Alternative manual start
uvicorn web.main:app --reload --port 8000
```

### Code Quality & Testing
```bash
# Linting and formatting (Black-compatible via Ruff)
ruff check .                    # Static code analysis
ruff check . --fix              # Auto-fix issues
ruff format .                   # Format code (88 char limit)

# Testing with Pytest
pytest                          # Run all tests with coverage
pytest tests/test_knowledge.py  # Run specific test file
pytest -m unit                  # Run unit tests only
pytest -m integration           # Run integration tests
pytest --cov=core --cov=web    # Generate coverage report
```

### Database Operations
```bash
# One-click migration from JSON to PostgreSQL
./migrate_to_database.sh

# Manual database operations
python scripts/init_database.py     # Initialize schema
python scripts/migrate_data.py      # Migrate data
python scripts/configure_db.py      # Configure settings
```

### Environment Setup
```bash
# Required environment variables
export GEMINI_API_KEY=your-key      # Required for AI functionality
export USE_DATABASE=false            # Toggle JSON/PostgreSQL backend

# Install dependencies
pip install -r requirements.txt      # Production dependencies
pip install -e ".[dev]"             # Development dependencies
```

## Development Guidelines

### 零硬編碼原則 (Zero Hardcoding)
**嚴禁**在程式碼中硬編碼任何配置值、路徑、API keys。所有配置必須通過：
- 環境變數 (`.env`) 由 `core/config.py` 載入
- 應用常數定義在模組頂部 (UPPER_SNAKE_CASE)
- Pydantic 模型進行資料驗證

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
- Reference existing patterns in `web/static/css/components/`

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

### Database Adapter Issue
**WARNING**: The database adapter (`core/database/adapter.py`) is missing critical sync methods required by web routes:
- `get_active_points()`
- `edit_knowledge_point()`
- `delete_knowledge_point()`
- `restore_knowledge_point()`

See `EMERGENCY_FIX.md` for immediate fixes. The web application will crash in database mode without these methods.

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
- CSS design system in `web/static/css/design-system/`
- All API routes under `/api/` serve JSON to frontend

## Common Development Tasks

- **Add new API route**: Create in `web/routers/`, follow existing patterns
- **Modify AI prompts**: Edit `core/ai_service.py` generation/grading methods
- **Update knowledge logic**: Modify `core/knowledge.py` and its algorithms
- **Change UI components**: Update `web/templates/` and `web/static/css/pages/`
- **Add frontend interaction**: Follow patterns in `web/static/js/practice-logic.js`

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

### Recent Completed Tasks (Legacy Reference)
- **TASK-20A**: Unified Cache Management System (2025-08-15) - Implemented thread-safe cache with 100% async/sync consistency
- **TASK-19D**: Unified Statistics Logic (2025-08-15) - Created UnifiedStatistics class achieving 80% consistency  
- **TASK-19B**: Dual-Mode Consistency Verification (2025-08-15) - Built comprehensive testing framework

*Note: The above completed tasks were managed under the previous task system. All new tasks should use the manual folder-based system described above.*

## DO NOT TOUCH - Critical Files

Unless explicitly permitted, do not modify:
- `.github/workflows/` - CI/CD pipeline configurations
- Database migration files in `scripts/` without understanding impact
- Environment configuration files containing secrets
- CSS design system core files without understanding @import dependencies

## Quality Checklist

Before submitting any changes:
- [ ] Code passes `ruff check .` without errors
- [ ] Code is formatted with `ruff format .`
- [ ] All tests pass with `pytest`
- [ ] Test coverage remains above 90%
- [ ] No hardcoded values or paths
- [ ] Type annotations are complete
- [ ] Docstrings are provided for public functions
- [ ] Follows existing code patterns
- [ ] No sensitive information in commits