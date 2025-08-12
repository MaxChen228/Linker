"""
測試數據工廠模組

提供各種測試數據的生成和管理工具，支援：
- 知識點測試數據
- 練習記錄測試數據  
- AI 回應測試數據
- 用戶輸入測試數據
"""

from .knowledge_factory import (
    KnowledgePointFactory,
    OriginalErrorFactory,
    ReviewExampleFactory,
    KnowledgePointTestDataBuilder,
    create_systematic_knowledge_point,
    create_singular_knowledge_point,
    create_knowledge_points_for_review,
    create_mastered_knowledge_points,
    create_mixed_knowledge_points,
)

from .practice_factory import (
    PracticeRecordFactory,
    PracticeSessionFactory,
    PracticeTestDataBuilder,
    create_correct_practice_record,
    create_incorrect_practice_record,
    create_review_practice_record,
    create_practice_history,
    create_practice_statistics,
)

from .ai_response_factory import (
    AIGenerateQuestionFactory,
    AIGradingResponseFactory,
    AIReviewQuestionFactory,
    LLMInteractionFactory,
    AIResponseTestDataBuilder,
    create_successful_grading_response,
    create_failed_grading_response,
    create_question_generation_response,
    create_llm_interaction_log,
)

from .user_input_factory import (
    UserTranslationInputFactory,
    UserInputVariationFactory,
    CommonErrorPatternFactory,
    UserInputTestDataBuilder,
    create_perfect_user_input,
    create_error_user_input,
    create_batch_user_inputs,
    create_review_mode_inputs,
    create_progressive_difficulty_inputs,
)

# Alias for backward compatibility
KnowledgeFactory = KnowledgePointFactory
AIResponseFactory = AIGradingResponseFactory

__all__ = [
    # Knowledge factories
    "KnowledgePointFactory",
    "KnowledgeFactory",  # Alias
    "OriginalErrorFactory", 
    "ReviewExampleFactory",
    "KnowledgePointTestDataBuilder",
    "create_systematic_knowledge_point",
    "create_singular_knowledge_point",
    "create_knowledge_points_for_review",
    "create_mastered_knowledge_points",
    "create_mixed_knowledge_points",
    
    # Practice factories
    "PracticeRecordFactory",
    "PracticeSessionFactory", 
    "PracticeTestDataBuilder",
    "create_correct_practice_record",
    "create_incorrect_practice_record",
    "create_review_practice_record",
    "create_practice_history",
    "create_practice_statistics",
    
    # AI response factories
    "AIGenerateQuestionFactory",
    "AIGradingResponseFactory",
    "AIResponseFactory",  # Alias
    "AIReviewQuestionFactory",
    "LLMInteractionFactory",
    "AIResponseTestDataBuilder",
    "create_successful_grading_response",
    "create_failed_grading_response",
    "create_question_generation_response",
    "create_llm_interaction_log",
    
    # User input factories
    "UserTranslationInputFactory",
    "UserInputVariationFactory",
    "CommonErrorPatternFactory",
    "UserInputTestDataBuilder",
    "create_perfect_user_input",
    "create_error_user_input",
    "create_batch_user_inputs",
    "create_review_mode_inputs",
    "create_progressive_difficulty_inputs",
]