# Linker - AI-Powered English Learning Platform

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com/)
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

- **Dual-Model AI System**: Gemini 2.5 Flash for generation, 2.5 Pro for grading
- **Smart Error Classification**: Systematic, isolated, enhancement, and other error types
- **Adaptive Review System**: Spaced repetition algorithm for knowledge retention
- **Real-time Feedback**: Detailed error analysis with improvement suggestions
- **Knowledge Management**: Automatic tracking and categorization of learning points

## System Requirements

- Python 3.9+
- 2GB RAM minimum
- Internet connection for AI API access

## Documentation

- [Technical Architecture](./docs/ARCHITECTURE.md)
- [API Reference](./docs/API.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please use the [GitHub Issues](https://github.com/yourusername/linker-cli/issues) page.