"""
測試工具模組

提供各種測試輔助工具，包括：
- 測試輔助函數
- 自定義斷言
- 測試清理工具
"""

from .test_helpers import (
    create_temp_file,
    create_temp_dir,
    load_json_file,
    save_json_file,
    compare_knowledge_points,
    wait_for_condition,
    async_timeout,
    patch_datetime_now,
    suppress_logging,
    create_test_environment_vars,
    mock_environment_variables,
    generate_test_data_file,
    simulate_network_delay,
    simulate_async_network_delay,
    capture_function_calls,
    create_fixture_file,
    load_fixture_file,
    TestTimer,
    assert_timing,
    random_string,
    random_choice_exclude,
    deep_merge_dict,
    change_working_directory,
    ensure_test_data_dir,
)

from .test_assertions import (
    assert_knowledge_point_valid,
    assert_review_example_valid,
    assert_practice_record_valid,
    assert_ai_response_valid,
    assert_response_success,
    assert_response_error,
    assert_json_file_valid,
    assert_knowledge_points_equal,
    assert_list_contains_knowledge_point,
    assert_mastery_level_in_range,
    assert_timestamp_recent,
    assert_subtype_valid,
    assert_error_category_valid,
    assert_practice_statistics_valid,
    assert_file_backup_created,
    KnowledgePointAssertionError,
    PracticeRecordAssertionError,
    AIResponseAssertionError,
)

from .test_cleanup import (
    TestEnvironmentCleaner,
    test_environment,
    temporary_directory,
    temporary_file,
    backup_and_restore_file,
    DatabaseCleaner,
    isolated_data_environment,
    cleanup_test_artifacts,
    ResourceTracker,
)

__all__ = [
    # Test helpers
    "create_temp_file",
    "create_temp_dir", 
    "load_json_file",
    "save_json_file",
    "compare_knowledge_points",
    "wait_for_condition",
    "async_timeout",
    "patch_datetime_now",
    "suppress_logging",
    "create_test_environment_vars",
    "mock_environment_variables",
    "generate_test_data_file",
    "simulate_network_delay",
    "simulate_async_network_delay",
    "capture_function_calls",
    "create_fixture_file",
    "load_fixture_file",
    "TestTimer",
    "assert_timing",
    "random_string",
    "random_choice_exclude",
    "deep_merge_dict",
    "change_working_directory",
    "ensure_test_data_dir",
    
    # Test assertions
    "assert_knowledge_point_valid",
    "assert_review_example_valid",
    "assert_practice_record_valid",
    "assert_ai_response_valid",
    "assert_response_success",
    "assert_response_error",
    "assert_json_file_valid",
    "assert_knowledge_points_equal",
    "assert_list_contains_knowledge_point",
    "assert_mastery_level_in_range",
    "assert_timestamp_recent",
    "assert_subtype_valid",
    "assert_error_category_valid",
    "assert_practice_statistics_valid",
    "assert_file_backup_created",
    "KnowledgePointAssertionError",
    "PracticeRecordAssertionError",
    "AIResponseAssertionError",
    
    # Test cleanup
    "TestEnvironmentCleaner",
    "test_environment",
    "temporary_directory",
    "temporary_file",
    "backup_and_restore_file",
    "DatabaseCleaner",
    "isolated_data_environment",
    "cleanup_test_artifacts",
    "ResourceTracker",
]