"""
驗證器測試模組
測試所有輸入驗證功能，包括邊界情況和錯誤處理
"""

import pytest
from unittest.mock import patch

from core.validators import (
    ValidationError,
    ValidationResult,
    ChineseSentenceValidator,
    EnglishTranslationValidator,
    PracticeModeValidator,
    DifficultyLevelValidator,
    KnowledgePointValidator,
    CompoundValidator,
    ValidationService,
    chinese_sentence_validator,
    english_translation_validator,
    validation_service,
)
from core.constants import ValidationRules, ErrorTypes


class TestValidationResult:
    """測試 ValidationResult 類"""

    def test_validation_result_init(self):
        """測試驗證結果初始化"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.cleaned_value is None

    def test_add_error(self):
        """測試添加錯誤"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.add_error("測試錯誤")
        
        assert result.is_valid is False
        assert "測試錯誤" in result.errors

    def test_add_warning(self):
        """測試添加警告"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.add_warning("測試警告")
        
        assert result.is_valid is True
        assert "測試警告" in result.warnings


class TestChineseSentenceValidator:
    """測試中文句子驗證器"""

    def test_valid_chinese_sentence(self):
        """測試有效的中文句子"""
        validator = ChineseSentenceValidator()
        result = validator.validate("今天天氣很好。")
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.cleaned_value == "今天天氣很好。"

    def test_empty_sentence(self):
        """測試空句子"""
        validator = ChineseSentenceValidator()
        result = validator.validate("")
        
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_sentence_too_short(self):
        """測試句子過短"""
        validator = ChineseSentenceValidator(min_length=10)
        result = validator.validate("短")
        
        assert result.is_valid is False
        assert any("太短" in error for error in result.errors)

    def test_sentence_too_long(self):
        """測試句子過長"""
        validator = ChineseSentenceValidator(max_length=10)
        long_sentence = "這是一個非常非常非常非常非常長的句子用來測試長度限制功能"
        result = validator.validate(long_sentence)
        
        assert result.is_valid is False
        assert any("太長" in error for error in result.errors)

    def test_whitespace_cleaning(self):
        """測試空白字符清理"""
        validator = ChineseSentenceValidator()
        result = validator.validate("  今天   天氣   很好  ")
        
        assert result.is_valid is True
        assert result.cleaned_value == "今天 天氣 很好"

    def test_non_string_input(self):
        """測試非字符串輸入"""
        validator = ChineseSentenceValidator()
        result = validator.validate(123)
        
        assert result.is_valid is False
        assert any("類型" in error for error in result.errors)

    def test_few_chinese_chars_warning(self):
        """測試中文字符較少的警告"""
        validator = ChineseSentenceValidator()
        result = validator.validate("Hello world 你好")
        
        # 應該有警告但可能仍然有效
        assert len(result.warnings) > 0
        assert any("中文字符較少" in warning for warning in result.warnings)

    def test_punctuation_normalization(self):
        """測試標點符號標準化"""
        validator = ChineseSentenceValidator()
        result = validator.validate("今天天氣很好，，，。。。")
        
        assert result.is_valid is True
        assert result.cleaned_value == "今天天氣很好。"


class TestEnglishTranslationValidator:
    """測試英文翻譯驗證器"""

    def test_valid_english_translation(self):
        """測試有效的英文翻譯"""
        validator = EnglishTranslationValidator()
        result = validator.validate("The weather is very good today.")
        
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_empty_translation(self):
        """測試空翻譯"""
        validator = EnglishTranslationValidator()
        result = validator.validate("")
        
        assert result.is_valid is False
        assert any("翻譯內容" in error or "空" in error for error in result.errors)

    def test_translation_too_short(self):
        """測試翻譯過短"""
        validator = EnglishTranslationValidator(min_length=20)
        result = validator.validate("Hi")
        
        assert result.is_valid is False
        assert any("過短" in error for error in result.errors)

    def test_translation_too_long(self):
        """測試翻譯過長"""
        validator = EnglishTranslationValidator(max_length=20)
        long_translation = "This is a very very very very very long translation for testing length limits"
        result = validator.validate(long_translation)
        
        assert result.is_valid is False
        assert any("過長" in error for error in result.errors)

    def test_chinese_chars_in_translation(self):
        """測試翻譯中包含中文字符"""
        validator = EnglishTranslationValidator()
        result = validator.validate("Hello 你好 world")
        
        assert result.is_valid is False
        assert any("中文字符" in error for error in result.errors)

    def test_few_english_words_warning(self):
        """測試英文單詞較少的警告"""
        validator = EnglishTranslationValidator()
        result = validator.validate("Hi!")
        
        assert len(result.warnings) > 0
        assert any("英文單詞較少" in warning for warning in result.warnings)

    def test_sentence_capitalization(self):
        """測試句首大寫處理"""
        validator = EnglishTranslationValidator()
        result = validator.validate("hello world")
        
        assert result.is_valid is True
        assert result.cleaned_value.startswith("Hello")

    def test_sentence_ending_punctuation(self):
        """測試句末標點符號補充"""
        validator = EnglishTranslationValidator()
        result = validator.validate("Hello world")
        
        assert result.is_valid is True
        assert result.cleaned_value.endswith(".")

    def test_grammar_structure_warning(self):
        """測試語法結構警告"""
        validator = EnglishTranslationValidator()
        result = validator.validate("word word word")
        
        # 應該有語法結構警告
        assert len(result.warnings) > 0


class TestPracticeModeValidator:
    """測試練習模式驗證器"""

    def test_valid_practice_modes(self):
        """測試有效的練習模式"""
        validator = PracticeModeValidator()
        
        for mode in ValidationRules.VALID_PRACTICE_MODES:
            result = validator.validate(mode)
            assert result.is_valid is True, f"Mode {mode} should be valid"

    def test_invalid_practice_mode(self):
        """測試無效的練習模式"""
        validator = PracticeModeValidator()
        result = validator.validate("invalid_mode")
        
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_non_string_mode(self):
        """測試非字符串模式"""
        validator = PracticeModeValidator()
        result = validator.validate(123)
        
        assert result.is_valid is False


class TestDifficultyLevelValidator:
    """測試難度等級驗證器"""

    def test_valid_difficulty_levels(self):
        """測試有效的難度等級"""
        validator = DifficultyLevelValidator()
        
        for level in range(ValidationRules.MIN_DIFFICULTY_LEVEL, 
                          ValidationRules.MAX_DIFFICULTY_LEVEL + 1):
            result = validator.validate(level)
            assert result.is_valid is True, f"Level {level} should be valid"

    def test_string_difficulty_level(self):
        """測試字符串格式的難度等級"""
        validator = DifficultyLevelValidator()
        result = validator.validate("2")
        
        assert result.is_valid is True
        assert result.cleaned_value == 2

    def test_invalid_difficulty_level(self):
        """測試無效的難度等級"""
        validator = DifficultyLevelValidator()
        
        # 測試過低
        result = validator.validate(0)
        assert result.is_valid is False
        
        # 測試過高
        result = validator.validate(10)
        assert result.is_valid is False

    def test_non_numeric_difficulty(self):
        """測試非數字難度"""
        validator = DifficultyLevelValidator()
        result = validator.validate("abc")
        
        assert result.is_valid is False
        assert any("數字" in error for error in result.errors)


class TestKnowledgePointValidator:
    """測試知識點驗證器"""

    def test_valid_knowledge_point(self):
        """測試有效的知識點"""
        validator = KnowledgePointValidator()
        valid_data = {
            "key_point": "動詞時態錯誤",
            "category": ErrorTypes.SYSTEMATIC,
            "original_phrase": "I go yesterday",
            "correction": "I went yesterday",
            "explanation": "過去式應該用 went",
            "mastery_level": 0.5
        }
        
        result = validator.validate(valid_data)
        assert result.is_valid is True

    def test_missing_required_fields(self):
        """測試缺少必要欄位"""
        validator = KnowledgePointValidator()
        incomplete_data = {
            "key_point": "動詞時態錯誤",
            # 缺少其他必要欄位
        }
        
        result = validator.validate(incomplete_data)
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_empty_field_values(self):
        """測試空欄位值"""
        validator = KnowledgePointValidator()
        data_with_empty = {
            "key_point": "",  # 空值
            "category": ErrorTypes.SYSTEMATIC,
            "original_phrase": "I go yesterday",
            "correction": "I went yesterday",
            "explanation": "過去式應該用 went"
        }
        
        result = validator.validate(data_with_empty)
        assert result.is_valid is False
        assert any("不能為空" in error for error in result.errors)

    def test_invalid_category(self):
        """測試無效的類別"""
        validator = KnowledgePointValidator()
        invalid_data = {
            "key_point": "動詞時態錯誤",
            "category": "invalid_category",
            "original_phrase": "I go yesterday",
            "correction": "I went yesterday",
            "explanation": "過去式應該用 went"
        }
        
        result = validator.validate(invalid_data)
        assert result.is_valid is False
        assert any("類別" in error for error in result.errors)

    def test_invalid_mastery_level(self):
        """測試無效的掌握度"""
        validator = KnowledgePointValidator()
        invalid_data = {
            "key_point": "動詞時態錯誤",
            "category": ErrorTypes.SYSTEMATIC,
            "original_phrase": "I go yesterday",
            "correction": "I went yesterday",
            "explanation": "過去式應該用 went",
            "mastery_level": 1.5  # 超出範圍
        }
        
        result = validator.validate(invalid_data)
        assert result.is_valid is False
        assert any("掌握度" in error for error in result.errors)


class TestCompoundValidator:
    """測試複合驗證器"""

    def test_compound_validation(self):
        """測試複合驗證"""
        validator = CompoundValidator()
        validator.add_validator("chinese", ChineseSentenceValidator())
        validator.add_validator("english", EnglishTranslationValidator())
        validator.add_validator("mode", PracticeModeValidator())
        
        data = {
            "chinese": "今天天氣很好",
            "english": "The weather is good today",
            "mode": "new"
        }
        
        results = validator.validate_dict(data)
        
        assert len(results) == 3
        assert validator.is_all_valid(results)

    def test_compound_validation_with_errors(self):
        """測試複合驗證包含錯誤"""
        validator = CompoundValidator()
        validator.add_validator("chinese", ChineseSentenceValidator())
        validator.add_validator("mode", PracticeModeValidator())
        
        data = {
            "chinese": "",  # 空句子，應該無效
            "mode": "invalid_mode"  # 無效模式
        }
        
        results = validator.validate_dict(data)
        
        assert not validator.is_all_valid(results)
        assert not results["chinese"].is_valid
        assert not results["mode"].is_valid


class TestValidationService:
    """測試驗證服務"""

    def test_validate_practice_input_success(self):
        """測試成功的練習輸入驗證"""
        is_valid, errors, cleaned_data = ValidationService.validate_practice_input(
            chinese="今天天氣很好",
            english="The weather is good today",
            mode="new",
            level=2,
            length="short"
        )
        
        assert is_valid is True
        assert len(errors) == 0
        assert "chinese" in cleaned_data
        assert "english" in cleaned_data

    def test_validate_practice_input_with_errors(self):
        """測試包含錯誤的練習輸入驗證"""
        is_valid, errors, cleaned_data = ValidationService.validate_practice_input(
            chinese="",  # 空中文句子
            english="",  # 空英文翻譯
            mode="invalid",  # 無效模式
            level=10,  # 無效等級
            length="invalid"  # 無效長度
        )
        
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_knowledge_point_success(self):
        """測試成功的知識點驗證"""
        data = {
            "key_point": "動詞時態錯誤",
            "category": ErrorTypes.SYSTEMATIC,
            "original_phrase": "I go yesterday",
            "correction": "I went yesterday",
            "explanation": "過去式應該用 went"
        }
        
        is_valid, errors = ValidationService.validate_knowledge_point(data)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_sanitize_user_input(self):
        """測試用戶輸入清理"""
        # 測試基本清理
        cleaned = ValidationService.sanitize_user_input("  hello world  ")
        assert cleaned == "hello world"
        
        # 測試危險字符移除
        cleaned = ValidationService.sanitize_user_input('hello<script>alert("xss")</script>')
        assert "<script>" not in cleaned
        assert "hello" in cleaned
        
        # 測試長度限制
        long_text = "a" * (ValidationRules.MAX_SENTENCE_LENGTH + 100)
        cleaned = ValidationService.sanitize_user_input(long_text)
        assert len(cleaned) == ValidationRules.MAX_SENTENCE_LENGTH
        
        # 測試空輸入
        cleaned = ValidationService.sanitize_user_input("")
        assert cleaned == ""
        
        # 測試 None 輸入
        cleaned = ValidationService.sanitize_user_input(None)
        assert cleaned == ""


class TestValidationIntegration:
    """測試驗證器整合功能"""

    def test_chinese_english_pair_validation(self):
        """測試中英文配對驗證"""
        # 測試正常情況
        chinese_result = chinese_sentence_validator.validate("我喜歡學習英語")
        english_result = english_translation_validator.validate("I like learning English")
        
        assert chinese_result.is_valid
        assert english_result.is_valid

    def test_edge_case_validation(self):
        """測試邊界情況驗證"""
        # 最短有效中文句子
        min_sentence = "我好"
        result = chinese_sentence_validator.validate(min_sentence)
        # 根據設定，這可能有效也可能無效，取決於最小長度設定
        
        # 最短有效英文翻譯
        min_translation = "I"
        result = english_translation_validator.validate(min_translation)
        # 應該會有警告，但可能仍然有效

    def test_validation_performance(self):
        """測試驗證性能"""
        # 簡單的性能測試
        import time
        
        start_time = time.time()
        for i in range(100):
            ValidationService.validate_practice_input(
                chinese=f"這是第{i}個測試句子",
                english=f"This is test sentence number {i}",
                mode="new",
                level=2,
                length="medium"
            )
        end_time = time.time()
        
        # 100次驗證應該在合理時間內完成（比如1秒）
        assert (end_time - start_time) < 1.0


# 邊界情況和錯誤處理測試
class TestEdgeCases:
    """測試邊界情況"""

    def test_unicode_handling(self):
        """測試Unicode字符處理"""
        validator = ChineseSentenceValidator()
        
        # 測試特殊Unicode字符
        result = validator.validate("今天天氣很好😊")
        assert result.is_valid  # 應該能處理emoji
        
        # 測試繁簡體混合
        result = validator.validate("今天天氣很好，明天會更好")
        assert result.is_valid

    def test_memory_and_security(self):
        """測試記憶體和安全性"""
        # 測試大量輸入
        large_input = "測試" * 10000
        result = ValidationService.sanitize_user_input(large_input)
        assert len(result) <= ValidationRules.MAX_SENTENCE_LENGTH
        
        # 測試惡意輸入
        malicious_inputs = [
            '<script>alert("xss")</script>',
            '"; DROP TABLE users; --',
            '../../../etc/passwd',
            '\x00\x01\x02',  # 控制字符
        ]
        
        for malicious in malicious_inputs:
            cleaned = ValidationService.sanitize_user_input(malicious)
            # 確保危險字符被移除或轉義
            assert '<script>' not in cleaned
            # 不同的惡意輸入有不同的處理結果
            if 'DROP TABLE' in malicious:
                assert 'DROP TABLE' in cleaned  # SQL注入字符串可能保留但在此層不危險


if __name__ == "__main__":
    # 執行測試時的簡單檢查
    print("開始執行驗證器測試...")
    
    # 可以在這裡添加一些簡單的手動測試
    chinese_validator = ChineseSentenceValidator()
    result = chinese_validator.validate("今天天氣很好")
    print(f"中文驗證測試: {'通過' if result.is_valid else '失敗'}")
    
    english_validator = EnglishTranslationValidator()
    result = english_validator.validate("The weather is good today")
    print(f"英文驗證測試: {'通過' if result.is_valid else '失敗'}")
    
    print("驗證器測試完成!")