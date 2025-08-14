# Technical Architecture (v4.0)

## System Overview

Linker is built on a modern, decoupled architecture. The backend is a **FastAPI-based API service**, and the frontend is a **dynamic, single-page application (SPA)** driven by JavaScript that consumes this API.

This API-first approach provides flexibility, clear separation of concerns, and allows for future clients (e.g., mobile apps) to easily connect.

```mermaid
graph TD
    subgraph Client Layer
        A[Browser - SPA Frontend]
    end

    subgraph API Layer (FastAPI)
        B[API Routers]
        C[Business Logic Layer]
        D[Data Access Layer / Adapter]
    end

    subgraph Core Services
        E[AI Service]
        F[Knowledge Manager]
        G[Tag Manager]
    end

    subgraph Data Storage
        I[JSON Files]
        J[PostgreSQL Database]
    end

    subgraph External Services
        H[Google Gemini API]
    end

    A -- HTTP/JSON --> B
    B --> C
    C --> E
    C --> F
    C --> G
    F --> D
    D -- selects --> I
    D -- selects --> J
    E -- API Call --> H

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style H fill:#f69,stroke:#333,stroke-width:2px
    style J fill:#cde,stroke:#333,stroke-width:2px
```

## Core Components

### 1. Frontend Layer (`web/static/` & `web/templates/`)
- **Single-Page Application (SPA) Logic**: The core practice loop is managed by JavaScript (`practice-logic.js`), which dynamically fetches questions and submits answers by calling the backend API.
- **HTML Skeleton**: Jinja2 templates (`practice.html`, `index.html`) are used to serve the initial HTML structure.
- **CSS Design System**: A modular and reusable design system (`web/static/css/design-system/`) ensures a consistent and modern UI.

### 2. Backend API Layer (`web/`)
- **FastAPI Application (`web/main.py`)**: The main entry point for the application, handling middleware, and startup events.
- **API Routers (`web/routers/`)**: Modular route handlers for different features (practice, knowledge, patterns). All routes under `/api/` serve JSON data to the frontend.

### 3. Core Business Logic (`core/`)
- **AIService**: Manages all interactions with the Google Gemini API, including generating questions and grading translations. It uses separate models for generation (`gemini-2.5-flash`) and grading (`gemini-2.5-pro`).
- **KnowledgeManager**: The heart of the learning system. It manages the lifecycle of `KnowledgePoint` objects, including creation from mistakes, mastery level updates, and scheduling for the spaced repetition system.
- **TagManager**: Manages the grammar pattern tags, providing functionalities like searching, categorization, and validating tag combinations for practice.
- **ErrorTypeSystem**: A sophisticated system for classifying user errors into four distinct categories (`systematic`, `isolated`, `enhancement`, `other`), which drives the learning and review logic.
- **VersionManager**: Manages data schema versions and handles automated migrations for all JSON data files upon startup.

### 4. Data Layer (`core/database/` & `data/`)
- **Dual Backend Support**: The system supports two data backends through a sophisticated **Adapter Pattern** (`core/database/adapter.py`).
  - **JSON Storage**: The default backend uses local JSON files, making the application portable and easy to set up for development.
  - **PostgreSQL Backend**: For production and scalability, the system can be configured to use a PostgreSQL database, offering higher performance, concurrency, and data integrity.
- **Automatic Backups**: The system automatically creates backups of data files before performing version migrations.

## Data Flow: A Typical Practice Loop

1.  The user navigates to the `/practice` page. The FastAPI server returns the static HTML shell.
2.  The frontend JavaScript (`practice-logic.js`) sends a request to `POST /api/generate-question`.
3.  The `AIService` generates a new question and returns it as JSON.
4.  The frontend renders the question in the browser.
5.  The user types and submits their translation.
6.  The frontend sends the user's answer to `POST /api/grade-answer`.
7.  The `AIService` grades the answer. If incorrect, the `KnowledgeManager` (via the adapter) creates or updates a corresponding `KnowledgePoint` in the configured backend (JSON or PostgreSQL).
8.  The API returns the detailed grading result as JSON.
9.  The frontend dynamically displays the feedback, score, and error analysis.

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend Framework | FastAPI | High-performance asynchronous API server |
| Frontend Logic | Vanilla JavaScript (ES6+) | Dynamic UI updates and API communication |
| Template Engine | Jinja2 | Serving the initial HTML page structure |
| AI Service | Google Gemini API | Core NLP for generation and grading |
| Data Storage | JSON Files / PostgreSQL | Dual-backend support for data persistence |
| Code Quality | Ruff | Linting and formatting |
| Testing | Pytest | Unit and integration testing |
| Python Version | 3.9+ | Modern Python features |

## Design Principles

- **API-First**: The backend is designed as a standalone API, separating it from the frontend presentation.
- **Modularity**: The code is organized into distinct, single-responsibility modules (`core`, `web`, `data`).
- **Dependency Injection**: FastAPI's dependency injection system is used to manage services like `KnowledgeManager` and `AIService`.
- **Configuration over Code**: Key parameters (model names, log levels, database usage) are managed via environment variables or settings files.

## Scalability Path

The current architecture is highly scalable:
- **Stateless Backend**: The API is stateless, allowing for horizontal scaling by running multiple instances behind a load balancer.
- **Production-Ready Database**: The system's support for PostgreSQL means it is ready for production workloads that require high concurrency and large datasets. The `KnowledgeManagerAdapter` ensures that this powerful backend can be enabled with a simple configuration change.
- **Client Flexibility**: The API-first design allows for the development of new clients, such as a native mobile app, without backend changes.
