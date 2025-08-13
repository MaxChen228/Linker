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