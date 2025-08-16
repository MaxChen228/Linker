# Linker - AI-Powered English Learning Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent English translation practice system powered by Google Gemini AI, providing real-time grading, error analysis, and personalized learning tracking.

## Quick Start

### 🚀 Using Linker Management System (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd linker

# Launch interactive management interface
./linker.sh

# Or use direct commands
./linker.sh start   # Quick start server
./linker.sh dev     # Development mode with auto-reload
./linker.sh stop    # Stop server
```

The `linker.sh` script provides:
- 🔧 Automatic environment setup
- 📦 Dependency installation
- ⚙️ Environment configuration wizard
- 🗄️ Database management tools
- 🧪 Testing and code quality checks
- 📊 Real-time system status display

For detailed usage, see [LINKER_MANAGER.md](./docs/guides/LINKER_MANAGER.md)

### Alternative Quick Start

```bash
# Manual setup (without linker.sh)
export GEMINI_API_KEY="your-api-key"
uvicorn web.main:app --reload
# Access http://localhost:8000
```

## Core Features

- **API-First Architecture**: Decoupled backend (FastAPI) and dynamic frontend (Vanilla JS) for a responsive user experience and high scalability.
- **Dual-Model AI System**: Utilizes Google's Gemini 2.5 Flash for efficient question generation and the more powerful Gemini 2.5 Pro for precise, in-depth grading.
- **Multiple Practice Modes**:
  - **New Questions**: For general practice.
  - **Spaced Repetition**: Intelligently schedules reviews based on your performance.
  - **Grammar Patterns**: Allows focused practice on specific grammar structures.
- **Advanced Knowledge Management**: Go beyond simple tracking. You can now:
  - **Edit** incorrect AI analysis or add your own insights.
  - **Tag** knowledge points for custom categorization.
  - **Add Notes** to any learning point.
  - **Delete** mastered points to clean up your workspace.
- **Recycle Bin**: Soft-deleted knowledge points are moved to a recycle bin, allowing you to restore them if needed.
- **Smart Error Classification**: A sophisticated system automatically categorizes errors into **Systematic**, **Isolated**, **Enhancement**, or **Other** types, helping you focus on what matters most.
- **Production-Ready Database Backend**: Officially supports PostgreSQL for enhanced performance, data integrity, and scalability. A complete migration system from JSON to PostgreSQL is included.
- **Robust Data Handling**: Features an automatic data versioning and migration system to ensure data integrity across updates.

## Development Tools

### 🛠️ Linker Management System

The project includes a comprehensive management script `linker.sh` that integrates all development, testing, and maintenance functions:

**Features:**
- **Interactive Menu**: User-friendly interface with numbered options
- **Environment Management**: Automatic venv setup, dependency installation
- **Database Tools**: Backup, restore, initialization, status check
- **Code Quality**: Integrated Ruff for linting and formatting
- **Testing Suite**: Unit, integration, API tests with coverage reports
- **Configuration Wizard**: Easy setup for API keys and database connections
- **Real-time Status**: Live display of server, database, and AI service status

**Usage:**
```bash
# Interactive mode (recommended)
./linker.sh

# Command mode
./linker.sh start   # Quick start
./linker.sh dev     # Development mode
./linker.sh reset   # Reset system
./linker.sh test    # Run tests
```

See [LINKER_MANAGER.md](./docs/guides/LINKER_MANAGER.md) for complete documentation.

## System Requirements

- Python 3.9+
- PostgreSQL 12+ (for production)
- 2GB RAM minimum
- Internet connection for AI API access

## Documentation

- [Technical Architecture](./docs/ARCHITECTURE.md)
- [API Reference](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Database Migration](./docs/DATABASE_MIGRATION.md)
- [Dynamic Styling](./docs/DYNAMIC_STYLING.md)

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/yourusername/linker-cli/issues) page.

<!-- Hook detection test -->
