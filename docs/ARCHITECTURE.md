# Technical Architecture

## System Overview

Linker is built on a modern, scalable architecture using FastAPI for the backend and Server-Side Rendering (SSR) with Jinja2 templates for the frontend.

```
┌─────────────────────────────────────────────────┐
│                   Client Layer                   │
│            (Browser / Mobile Device)             │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/HTTPS
┌─────────────────▼───────────────────────────────┐
│                Application Layer                 │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │            FastAPI Server                │   │
│  │                                          │   │
│  │  ┌────────────┐  ┌──────────────────┐  │   │
│  │  │   Routes   │  │    Templates     │  │   │
│  │  │            │  │   (Jinja2 SSR)   │  │   │
│  │  └──────┬─────┘  └──────────────────┘  │   │
│  │         │                               │   │
│  │  ┌──────▼─────────────────────────┐    │   │
│  │  │     Business Logic Layer       │    │   │
│  │  │  ┌──────────┐ ┌─────────────┐ │    │   │
│  │  │  │AIService │ │KnowledgeMgr │ │    │   │
│  │  │  └──────────┘ └─────────────┘ │    │   │
│  │  └─────────────────────────────────┘    │   │
│  └──────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│                 External Services                │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │  Gemini AI API   │  │  Local Storage   │    │
│  │  (2.5 Flash/Pro) │  │   (JSON Files)   │    │
│  └──────────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────┘
```

## Core Components

### 1. Web Layer (`web/`)
- **FastAPI Application**: Handles HTTP requests and responses
- **Routers**: Modular route handlers for different features
- **Templates**: Jinja2 templates for server-side rendering
- **Static Assets**: CSS design system and JavaScript for interactivity

### 2. Core Business Logic (`core/`)
- **AIService**: Manages Gemini AI API interactions
- **KnowledgeManager**: Handles knowledge point tracking and review scheduling
- **ErrorClassifier**: Categorizes translation errors
- **VersionManager**: Manages data schema migrations

### 3. Data Layer
- **JSON Storage**: Lightweight, file-based persistence
- **Automatic Versioning**: Schema migration on startup
- **Backup Strategy**: Automatic backups before migrations

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend Framework | FastAPI 0.111+ | High-performance async web framework |
| Template Engine | Jinja2 | Server-side rendering |
| AI Service | Google Gemini API | Natural language processing |
| Data Storage | JSON Files | Simple, portable data persistence |
| CSS Architecture | Design System | Modular, maintainable styling |
| Python Version | 3.9+ | Modern Python features |

## Design Patterns

### Dependency Injection
All services are initialized once and injected where needed, ensuring single instances and efficient resource usage.

### Repository Pattern
Data access is abstracted through manager classes, allowing easy migration to databases if needed.

### Service Layer
Business logic is separated from web handlers, making the code testable and maintainable.

## Performance Optimizations

1. **Async Operations**: Non-blocking I/O for API calls
2. **Connection Pooling**: Reused HTTP connections to AI services
3. **Smart Caching**: Frequently accessed data cached in memory
4. **Lazy Loading**: Resources loaded only when needed

## Security Considerations

- API keys stored in environment variables
- Input validation on all user inputs
- XSS protection through template escaping
- No sensitive data in client-side code

## Scalability Path

The current architecture supports:
- Horizontal scaling with load balancer
- Migration to microservices
- Database integration (PostgreSQL/MongoDB)
- Container deployment (Docker/Kubernetes)