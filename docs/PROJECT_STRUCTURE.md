# 📁 Linker Project Structure

## Overview

This document describes the organized structure of the Linker project after refactoring.

## Directory Structure

```
linker/
├── 📄 Core Documentation (Root)
│   ├── README.md                # Project introduction and quick start
│   ├── CLAUDE.md                # AI assistant guidelines
│   └── .gitignore              # Version control exclusions
│
├── 📘 docs/                    # All documentation
│   ├── guides/                 # User and developer guides
│   │   ├── LINKER_MANAGER.md  # Management system guide
│   │   └── LINKER_DOCUMENTATION_UPDATE.md
│   ├── migration/              # Migration documentation
│   │   └── MIGRATION_TO_LINKER.md
│   ├── reports/                # Analysis and reports
│   │   └── test_categorization_audit_report.md
│   ├── API.md                  # API reference
│   ├── ARCHITECTURE.md         # System architecture
│   ├── DATABASE_MIGRATION.md   # Database migration guide
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── PROJECT_STRUCTURE.md    # This file
│
├── 🔧 scripts/                 # All executable scripts
│   ├── legacy/                 # Old scripts (deprecated)
│   │   ├── run.sh             # Old startup script
│   │   ├── reset.sh           # Old reset script
│   │   └── ruff.sh            # Old linting script
│   ├── utils/                  # Utility scripts
│   │   ├── build-css.sh       # CSS build script
│   │   ├── play_sound.sh      # Sound notification
│   │   └── migrate_to_database.sh
│   └── [database scripts...]   # Database management scripts
│
├── 💼 core/                    # Core business logic
│   ├── ai_service.py          # AI integration
│   ├── knowledge.py           # Knowledge management
│   ├── database/              # Database layer
│   ├── services/              # Service layer
│   └── ...
│
├── 🌐 web/                     # Web application
│   ├── main.py                # FastAPI application
│   ├── routers/               # API routes
│   ├── templates/             # HTML templates
│   └── static/                # Frontend assets
│       ├── css/               # CSS styles with design system
│       │   ├── design-system/ # Unified design token system
│       │   │   ├── 01-tokens/     # Design tokens (colors, spacing, etc.)
│       │   │   ├── 02-base/       # Base styles and reset
│       │   │   ├── 03-components/ # Component styles
│       │   │   ├── 04-layouts/    # Layout utilities
│       │   │   └── 05-utilities/  # Utility classes
│       │   ├── pages/         # Page-specific styles
│       │   └── components/    # Legacy component styles
│       ├── js/                # JavaScript files
│       └── assets/            # Images, fonts, etc.
│
├── 📋 TODO/                    # Task management system
│   ├── 01_Pending/            # Ideas and drafts
│   ├── 02_Todo/               # Ready to execute
│   ├── 03_InProgress/         # Currently working
│   ├── 04_Review/             # Awaiting review
│   └── 05_Done/               # Completed tasks
│
├── 🗂️ data/                    # Application data
│   └── backups/               # Database backups
│
├── 🔒 .tmp/                    # Temporary files (gitignored)
│   ├── server.log             # Server logs
│   ├── htmlcov/               # Test coverage reports
│   └── [other temp files...]
│
├── ⚙️ Configuration Files
│   ├── pyproject.toml         # Python project config
│   ├── requirements.txt       # Dependencies
│   ├── Dockerfile             # Container config
│   ├── docker-compose.yml     # Multi-container config
│   └── render.yaml            # Deployment config
│
├── 🧪 tests/                  # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test fixtures
│
└── 🚀 linker.sh               # Main management script (entry point)
```

## UI Architecture (TASK-35 完成)

### Design System Excellence ✅
**Status**: 95.6% 零硬編碼率達成

**CSS 架構統一** (2025-08-16 完成):
- **設計令牌系統**: 完整的 token 架構取代硬編碼值
- **模組化結構**: 清晰的 5 層設計系統架構
- **零硬編碼原則**: 638 → 28 硬編碼值 (95.6% 清理率)
- **Alpha 透明度**: 28 個系統化透明度令牌
- **響應式設計**: 統一的斷點和媒體查詢系統

**技術成果**:
- RGBA 清理: 218 → 3 (98.6%)
- PX 清理: 420 → 25 (94.0%)
- 設計令牌: 200+ 個統一令牌
- CSS 架構: 雙重系統 → 統一設計系統

## Key Principles

### 1. **Single Entry Point**
- `linker.sh` is the only script in root directory
- All other scripts are organized in `scripts/`

### 2. **Clear Documentation Hierarchy**
- Essential docs (README, CLAUDE) in root
- All other docs organized in `docs/` with subdirectories

### 3. **Separation of Concerns**
- `core/` - Business logic
- `web/` - Web layer
- `scripts/` - Automation
- `docs/` - Documentation
- `.tmp/` - Temporary files

### 4. **Clean Root Directory**
Only essential files remain in root:
- Entry points (linker.sh)
- Core documentation (README.md, CLAUDE.md)
- Configuration files (requirements.txt, etc.)

### 5. **Version Control Hygiene**
`.gitignore` properly configured to exclude:
- `.tmp/` directory
- `venv/` and `node_modules/`
- Log files
- Coverage reports
- System files

## Benefits of This Structure

1. **Improved Discoverability** - New developers can quickly understand the project
2. **Reduced Clutter** - Clean root directory with clear organization
3. **Better Maintenance** - Related files grouped together
4. **Professional Appearance** - Industry-standard structure
5. **Easier Navigation** - Logical hierarchy for all components

## Migration Notes

If you're looking for files from the old structure:

| Old Location | New Location |
|-------------|--------------|
| `/LINKER_MANAGER.md` | `/docs/guides/LINKER_MANAGER.md` |
| `/run.sh` | `/scripts/legacy/run.sh` (use `./linker.sh` instead) |
| `/reset.sh` | `/scripts/legacy/reset.sh` (use `./linker.sh reset` instead) |
| `/test_*.md` | `/docs/reports/` |
| `/server.log` | `/.tmp/server.log` |
| `/htmlcov/` | `/.tmp/htmlcov/` |
| `/web/static/css/components.css` | **REMOVED** (migrated to design-system) |
| Hardcoded CSS values | `design-system/01-tokens/` (design tokens) |

## Development Workflow

1. **Start Development**: `./linker.sh dev`
2. **Run Tests**: `./linker.sh test`
3. **Check Code Quality**: Use linker.sh menu option 6
4. **View Documentation**: Check `docs/` directory
5. **Manage Tasks**: Use `TODO/` system

### CSS Development Guidelines
1. **Use Design Tokens**: Always use `var(--token-name)` instead of hardcoded values
2. **Follow Design System**: Reference `web/static/css/design-system/`
3. **Zero Hardcode**: No magic numbers (px, rgba, etc.)
4. **Semantic First**: Prefer semantic tokens over raw values
5. **Modular Structure**: Follow the 5-layer design system architecture

## Maintenance

- Temporary files are automatically placed in `.tmp/`
- Old scripts in `scripts/legacy/` can be removed after full migration
- Documentation should be updated in appropriate `docs/` subdirectory
- New scripts should go in `scripts/` with clear naming

---

Last Updated: 2025-08-16  
Refactoring Version: 1.0  
Design System Version: 1.0 (TASK-35 Complete)  
Zero Hardcode Achievement: 95.6% ✅