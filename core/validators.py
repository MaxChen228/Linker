"""
輸入驗證系統
提供全面的輸入驗證功能，支援中英文內容驗證
"""

import re
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
from enum import Enum

from core.constants import (
    ValidationRules,
    UIMessages,
    ErrorTypes,
)


class ValidationError(Exception):
    """驗證錯誤異常"""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


@dataclass
class ValidationResult:
    """驗證結果"""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_value: Any = None
    
    def add_error(self, message: str):
        """添加錯誤訊息"""
        self.is_valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """添加警告訊息"""
        self.warnings.append(message)


class BaseValidator:
    """基礎驗證器"""
    
    def __init__(self, strict: bool = True):
        self.strict = strict
    
    def validate(self, value: Any) -> ValidationResult:
        """執行驗證"""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], cleaned_value=value)
        
        try:
            # 基本類型檢查
            if not self._check_type(value):
                result.add_error("資料類型不正確")
                return result
            
            # 執行具體驗證
            self._validate_content(value, result)
            
            # 清理和標準化
            if result.is_valid:
                result.cleaned_value = self._clean_value(value)
                
        except Exception as e:
            result.add_error(f"驗證過程發生錯誤: {str(e)}")
        
        return result
    
    def _check_type(self, value: Any) -> bool:
        """檢查基本類型"""
        return True
    
    def _validate_content(self, value: Any, result: ValidationResult):
        """驗證內容（子類實現）"""
        pass
    
    def _clean_value(self, value: Any) -> Any:
        """清理和標準化值"""
        return value


class ChineseSentenceValidator(BaseValidator):
    """中文句子驗證器"""
    
    def __init__(self, 
                 min_length: int = ValidationRules.MIN_SENTENCE_LENGTH,
                 max_length: int = ValidationRules.MAX_SENTENCE_LENGTH,
                 strict: bool = True):
        super().__init__(strict)
        self.min_length = min_length
        self.max_length = max_length
        
        # 中文字符範圍
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        # 標點符號
        self.punctuation_pattern = re.compile(r'[，。！？；：（）【】《》""''、]')
    
    def _check_type(self, value: Any) -> bool:
        return isinstance(value, str)
    
    def _validate_content(self, value: str, result: ValidationResult):
        """驗證中文句子內容"""
        if not value or not value.strip():
            result.add_error(UIMessages.ERROR_SENTENCE_TOO_SHORT)
            return
        
        clean_text = value.strip()
        
        # 長度檢查
        if len(clean_text) < self.min_length:
            result.add_error(UIMessages.ERROR_SENTENCE_TOO_SHORT)
        
        if len(clean_text) > self.max_length:
            result.add_error(UIMessages.ERROR_SENTENCE_TOO_LONG)
        
        # 中文字符檢查
        chinese_chars = self.chinese_pattern.findall(clean_text)
        if len(chinese_chars) < max(2, len(clean_text) // 3):
            result.add_warning("句子中的中文字符較少，請確認是否為中文句子")
        
        # 檢查是否包含基本的句子結構
        if self.strict:
            if not self._has_basic_sentence_structure(clean_text):
                result.add_warning("句子結構可能不完整")
    
    def _has_basic_sentence_structure(self, text: str) -> bool:
        """檢查是否有基本的句子結構"""
        # 簡單檢查：是否有主語和動詞的基本組合
        # 這裡用簡化的邏輯，實際項目中可以更複雜
        chinese_chars = len(self.chinese_pattern.findall(text))
        return chinese_chars >= 3  # 至少3個中文字符
    
    def _clean_value(self, value: str) -> str:
        """清理中文句子"""
        if not value:
            return ""
        
        # 去除前後空白
        cleaned = value.strip()
        
        # 標準化空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 移除多餘的標點符號
        cleaned = re.sub(r'[，。]{2,}', '。', cleaned)
        
        return cleaned


class EnglishTranslationValidator(BaseValidator):
    """英文翻譯驗證器"""
    
    def __init__(self,
                 min_length: int = ValidationRules.MIN_TRANSLATION_LENGTH,
                 max_length: int = ValidationRules.MAX_TRANSLATION_LENGTH,
                 strict: bool = True):
        super().__init__(strict)
        self.min_length = min_length
        self.max_length = max_length
        
        # 英文單詞模式
        self.word_pattern = re.compile(r'\b[a-zA-Z]+\b')
        # 基本句子模式（包含主謂結構）
        self.sentence_pattern = re.compile(r'\b[A-Z][a-z]*\b.*\b(is|are|was|were|have|has|do|does|did|will|can|could|should|would)\b', re.IGNORECASE)
    
    def _check_type(self, value: Any) -> bool:
        return isinstance(value, str)
    
    def _validate_content(self, value: str, result: ValidationResult):
        """驗證英文翻譯內容"""
        if not value or not value.strip():
            result.add_error(UIMessages.ERROR_TRANSLATION_EMPTY)
            return
        
        clean_text = value.strip()
        
        # 長度檢查
        if len(clean_text) < self.min_length:
            result.add_error("翻譯內容過短")
        
        if len(clean_text) > self.max_length:
            result.add_error("翻譯內容過長")
        
        # 英文單詞檢查
        words = self.word_pattern.findall(clean_text)
        if len(words) < 2:  # 至少2個英文單詞才算合理
            result.add_warning("翻譯中的英文單詞較少")
        
        if len(words) > ValidationRules.MAX_ENGLISH_WORDS:
            result.add_warning("翻譯中的英文單詞過多，建議簡化")
        
        # 基本語法檢查
        if self.strict:
            if not self._has_basic_grammar(clean_text):
                result.add_warning("翻譯可能缺少完整的句子結構")
            
            # 檢查是否有明顯的中文字符（混合語言）
            if re.search(r'[\u4e00-\u9fff]', clean_text):
                result.add_error("翻譯中不應包含中文字符")
    
    def _has_basic_grammar(self, text: str) -> bool:
        """檢查是否有基本的英文語法結構"""
        # 簡化的語法檢查
        words = self.word_pattern.findall(text.lower())
        
        # 至少要有一個動詞
        common_verbs = ['is', 'are', 'was', 'were', 'have', 'has', 'do', 'does', 'did', 
                       'will', 'can', 'could', 'should', 'would', 'go', 'come', 'get', 'make', 'take']
        has_verb = any(verb in words for verb in common_verbs)
        
        return has_verb and len(words) >= 2
    
    def _clean_value(self, value: str) -> str:
        """清理英文翻譯"""
        if not value:
            return ""
        
        # 去除前後空白
        cleaned = value.strip()
        
        # 標準化空白字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 修正基本的大小寫（句首大寫）
        if cleaned and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        # 確保句末有標點符號
        if cleaned and cleaned[-1] not in '.!?':
            cleaned += '.'
        
        return cleaned


class PracticeModeValidator(BaseValidator):
    """練習模式驗證器"""
    
    def _check_type(self, value: Any) -> bool:
        return isinstance(value, str)
    
    def _validate_content(self, value: str, result: ValidationResult):
        """驗證練習模式"""
        if value not in ValidationRules.VALID_PRACTICE_MODES:
            result.add_error(f"練習模式必須是 {', '.join(ValidationRules.VALID_PRACTICE_MODES)} 之一")


class SentenceLengthValidator(BaseValidator):
    """句子長度類型驗證器"""
    
    def _check_type(self, value: Any) -> bool:
        return isinstance(value, str)
    
    def _validate_content(self, value: str, result: ValidationResult):
        """驗證句子長度類型"""
        if value not in ValidationRules.VALID_SENTENCE_LENGTHS:
            result.add_error(f"句子長度必須是 {', '.join(ValidationRules.VALID_SENTENCE_LENGTHS)} 之一")


class DifficultyLevelValidator(BaseValidator):
    """難度等級驗證器"""
    
    def _check_type(self, value: Any) -> bool:
        return isinstance(value, (int, str))
    
    def _validate_content(self, value: Union[int, str], result: ValidationResult):
        """驗證難度等級"""
        try:
            level = int(value)
            if not (ValidationRules.MIN_DIFFICULTY_LEVEL <= level <= ValidationRules.MAX_DIFFICULTY_LEVEL):
                result.add_error(
                    f"難度等級必須在 {ValidationRules.MIN_DIFFICULTY_LEVEL} "
                    f"到 {ValidationRules.MAX_DIFFICULTY_LEVEL} 之間"
                )
        except (ValueError, TypeError):
            result.add_error("難度等級必須是數字")
    
    def _clean_value(self, value: Union[int, str]) -> int:
        """清理難度等級"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return ValidationRules.MIN_DIFFICULTY_LEVEL


class KnowledgePointValidator(BaseValidator):
    """知識點數據驗證器"""
    
    def _check_type(self, value: Any) -> bool:
        return isinstance(value, dict)
    
    def _validate_content(self, value: dict, result: ValidationResult):
        """驗證知識點數據"""
        required_fields = ['key_point', 'category', 'original_phrase', 'correction', 'explanation']
        
        for field in required_fields:
            if field not in value:
                result.add_error(f"缺少必要欄位: {field}")
                continue
            
            if not value[field] or (isinstance(value[field], str) and not value[field].strip()):
                result.add_error(f"欄位 {field} 不能為空")
        
        # 驗證 category
        if 'category' in value:
            category = value['category']
            valid_categories = [ErrorTypes.SYSTEMATIC, ErrorTypes.ISOLATED, 
                             ErrorTypes.ENHANCEMENT, ErrorTypes.OTHER]
            if category not in valid_categories:
                result.add_error(f"知識點類別必須是 {', '.join(valid_categories)} 之一")
        
        # 驗證 mastery_level
        if 'mastery_level' in value:
            try:
                level = float(value['mastery_level'])
                if not (ValidationRules.MIN_MASTERY_LEVEL <= level <= ValidationRules.MAX_MASTERY_LEVEL):
                    result.add_error(
                        f"掌握度必須在 {ValidationRules.MIN_MASTERY_LEVEL} "
                        f"到 {ValidationRules.MAX_MASTERY_LEVEL} 之間"
                    )
            except (ValueError, TypeError):
                result.add_error("掌握度必須是數字")


class CompoundValidator:
    """複合驗證器 - 組合多個驗證器"""
    
    def __init__(self):
        self.validators = {}
    
    def add_validator(self, field: str, validator: BaseValidator):
        """添加字段驗證器"""
        self.validators[field] = validator
    
    def validate_dict(self, data: dict) -> Dict[str, ValidationResult]:
        """驗證字典數據"""
        results = {}
        
        for field, validator in self.validators.items():
            value = data.get(field)
            results[field] = validator.validate(value)
        
        return results
    
    def is_all_valid(self, results: Dict[str, ValidationResult]) -> bool:
        """檢查所有驗證結果是否都通過"""
        return all(result.is_valid for result in results.values())


class ValidationService:
    """驗證服務 - 提供常用的驗證功能"""
    
    @staticmethod
    def validate_practice_input(chinese: str, english: str, mode: str = "new", 
                               level: Union[int, str] = 1, length: str = "short") -> Tuple[bool, List[str], dict]:
        """
        驗證練習輸入
        
        Returns:
            Tuple[is_valid, errors, cleaned_data]
        """
        errors = []
        cleaned_data = {}
        
        # 驗證中文句子
        chinese_validator = ChineseSentenceValidator()
        chinese_result = chinese_validator.validate(chinese)
        if not chinese_result.is_valid:
            errors.extend([f"中文句子: {error}" for error in chinese_result.errors])
        else:
            cleaned_data['chinese'] = chinese_result.cleaned_value
        
        # 驗證英文翻譯
        english_validator = EnglishTranslationValidator()
        english_result = english_validator.validate(english)
        if not english_result.is_valid:
            errors.extend([f"英文翻譯: {error}" for error in english_result.errors])
        else:
            cleaned_data['english'] = english_result.cleaned_value
        
        # 驗證練習模式
        mode_validator = PracticeModeValidator()
        mode_result = mode_validator.validate(mode)
        if not mode_result.is_valid:
            errors.extend([f"練習模式: {error}" for error in mode_result.errors])
        else:
            cleaned_data['mode'] = mode
        
        # 驗證難度等級
        level_validator = DifficultyLevelValidator()
        level_result = level_validator.validate(level)
        if not level_result.is_valid:
            errors.extend([f"難度等級: {error}" for error in level_result.errors])
        else:
            cleaned_data['level'] = level_result.cleaned_value
        
        # 驗證句子長度
        length_validator = SentenceLengthValidator()
        length_result = length_validator.validate(length)
        if not length_result.is_valid:
            errors.extend([f"句子長度: {error}" for error in length_result.errors])
        else:
            cleaned_data['length'] = length
        
        is_valid = len(errors) == 0
        
        return is_valid, errors, cleaned_data
    
    @staticmethod
    def validate_knowledge_point(data: dict) -> Tuple[bool, List[str]]:
        """驗證知識點數據"""
        validator = KnowledgePointValidator()
        result = validator.validate(data)
        
        return result.is_valid, result.errors
    
    @staticmethod
    def sanitize_user_input(text: str) -> str:
        """清理用戶輸入"""
        if not text:
            return ""
        
        # 去除前後空白
        cleaned = text.strip()
        
        # 移除潛在的危險字符（保留更多內容以供測試）
        # 只移除明顯的HTML標籤字符
        cleaned = re.sub(r'[<>]', '', cleaned)
        
        # 限制長度
        if len(cleaned) > ValidationRules.MAX_SENTENCE_LENGTH:
            cleaned = cleaned[:ValidationRules.MAX_SENTENCE_LENGTH]
        
        return cleaned


# 創建常用的驗證器實例
chinese_sentence_validator = ChineseSentenceValidator()
english_translation_validator = EnglishTranslationValidator()
practice_mode_validator = PracticeModeValidator()
difficulty_level_validator = DifficultyLevelValidator()
knowledge_point_validator = KnowledgePointValidator()

# 驗證服務實例
validation_service = ValidationService()