"""
Mock 系統模組

提供各種 Mock 對象和測試替身，包括：
- AI 服務 Mock
- 文件操作 Mock
- Repository Mock
- 外部 API Mock
"""

from .mock_ai_service import (
    MockAIService,
    create_mock_ai_service,
    create_ai_service_mock_with_responses,
)

from .mock_file_operations import (
    MockFileSystem,
    MockJSONFileHandler,
    MockBackupManager,
    FileOperationMockContext,
    create_mock_file_operations,
    create_populated_mock_filesystem,
)

from .mock_repositories import (
    MockKnowledgeRepository,
    MockPracticeRepository,
    MockKnowledgeManager,
    create_mock_knowledge_repository,
    create_mock_practice_repository,
)

from .mock_external_apis import (
    MockGeminiAPI,
    MockHTTPClient,
    ExternalAPIMockContext,
    create_mock_gemini_api,
    setup_gemini_api_responses,
)

__all__ = [
    # AI Service Mocks
    "MockAIService",
    "create_mock_ai_service", 
    "create_ai_service_mock_with_responses",
    
    # File Operation Mocks
    "MockFileSystem",
    "MockJSONFileHandler",
    "MockBackupManager",
    "FileOperationMockContext",
    "create_mock_file_operations",
    "create_populated_mock_filesystem",
    
    # Repository Mocks
    "MockKnowledgeRepository",
    "MockPracticeRepository",
    "MockKnowledgeManager",
    "create_mock_knowledge_repository",
    "create_mock_practice_repository",
    
    # External API Mocks
    "MockGeminiAPI",
    "MockHTTPClient",
    "ExternalAPIMockContext",
    "create_mock_gemini_api",
    "setup_gemini_api_responses",
]