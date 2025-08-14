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
2. **載入情境** - Load relevant files using memory feature
3. **遵循模式** - Follow existing patterns in the codebase
4. **執行驗證** - Run linting, formatting, and tests
5. **明確聲明** - Explicitly state validation completion

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

The project uses a granular task tracking system in the `TODO/` directory. **All new features and fixes must be documented as detailed subtasks before implementation.**

### Creating New Tasks
When starting any work:
1. Create a new `.md` file in `TODO/` with format: `XX-task-name.md`
2. Break down the work into small, executable subtasks
3. Include time estimates, priority, and acceptance criteria
4. Update `TODO/00-index.md` with the new task

### Task Structure
```markdown
# Task Title
## Priority: CRITICAL/HIGH/MEDIUM/LOW
## Time Estimate: X hours
## Status: ⏳ PENDING / 🚧 IN_PROGRESS / ✅ COMPLETED

### Subtasks
- [ ] Specific actionable item
- [ ] Another subtask with clear scope
```

### 🚨 MANDATORY Task Execution Process

**CRITICAL: You MUST follow these steps IN ORDER when working on TODO tasks:**

1. **📖 READ AND UNDERSTAND** (BEFORE any changes)
   - Read the entire task file from `TODO/`
   - Read ALL related files mentioned in the task
   - Understand the acceptance criteria completely
   - DO NOT proceed until you fully understand the requirements

2. **🚧 UPDATE STATUS TO IN_PROGRESS**
   - Edit the task file and change status to `🚧 IN_PROGRESS`
   - Update `TODO/00-index.md` status accordingly
   - Use TodoWrite tool to track the task

3. **📝 PLAN BEFORE CODING**
   - List all files that need to be modified
   - Identify existing patterns to follow
   - Break down the work into small steps
   - DO NOT start coding until the plan is clear

4. **💻 EXECUTE SUBTASKS** (one by one)
   - Complete subtasks sequentially
   - Mark each subtask with [x] when done
   - Follow existing code patterns
   - Run `ruff check` after EACH file modification

5. **✅ VALIDATE AND TEST**
   - Run ALL test scenarios in the task's acceptance criteria
   - Execute `ruff check .` and `ruff format .`
   - Run `pytest` if tests exist
   - Fix any issues before proceeding

6. **📊 MARK COMPLETED**
   - ONLY mark as COMPLETED when ALL subtasks pass
   - Update task file status to `✅ COMPLETED`
   - Update `TODO/00-index.md` with completion date
   - Update progress statistics

**⛔ STOP CONDITIONS:**
- If tests fail → Keep status as IN_PROGRESS
- If blocked → Create new blocking task
- If requirements unclear → Ask for clarification BEFORE coding

### Current Critical Tasks
See `TODO/00-index.md` for the complete task list. **Priority tasks**:
- `01-database-adapter-sync-methods.md` - CRITICAL: Fix missing adapter methods
- `02-learning-recommendation-system.md` - HIGH: Implement recommendations

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