# Linker - AI-Powered English Learning Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent English translation practice system powered by Google Gemini AI, providing real-time grading, error analysis, and personalized learning tracking.

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd linker-cli

# Set API key
export GEMINI_API_KEY="your-api-key"

# Run application
./run.sh
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

## System Requirements

- Python 3.9+
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
