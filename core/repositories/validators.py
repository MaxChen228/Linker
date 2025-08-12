"""
數據驗證器模組

提供全面的數據驗證和遷移支援，確保數據完整性和格式一致性
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from ..constants import ValidationRules, ErrorTypes


class ValidationSeverity(Enum):
    """驗證錯誤嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """驗證結果"""
    is_valid: bool
    severity: ValidationSeverity
    field_path: str
    message: str
    suggested_fix: Optional[str] = None
    error_code: Optional[str] = None


@dataclass 
class MigrationResult:
    """遷移結果"""
    success: bool
    from_version: str
    to_version: str
    migrated_data: Optional[Dict[str, Any]] = None
    warnings: List[str] = None
    errors: List[str] = None


class BaseValidator(ABC):
    """基礎驗證器抽象類"""
    
    @abstractmethod
    def validate(self, data: Any, context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """執行驗證"""
        pass
    
    def _create_result(
        self, 
        is_valid: bool, 
        severity: ValidationSeverity,
        field_path: str, 
        message: str,
        suggested_fix: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> ValidationResult:
        """創建驗證結果"""
        return ValidationResult(
            is_valid=is_valid,
            severity=severity,
            field_path=field_path,
            message=message,
            suggested_fix=suggested_fix,
            error_code=error_code
        )


class FieldValidator(BaseValidator):
    """欄位驗證器"""
    
    def __init__(self, field_name: str):
        self.field_name = field_name
    
    def validate_required(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """驗證必要欄位"""
        results = []
        
        if self.field_name not in data:
            results.append(self._create_result(
                False, ValidationSeverity.ERROR, 
                self.field_name, 
                f"必要欄位 '{self.field_name}' 缺失",
                f"請添加 '{self.field_name}' 欄位",
                "MISSING_REQUIRED_FIELD"
            ))
        elif data[self.field_name] is None:
            results.append(self._create_result(
                False, ValidationSeverity.ERROR,
                self.field_name,
                f"必要欄位 '{self.field_name}' 不能為 None",
                f"請為 '{self.field_name}' 提供有效值",
                "NULL_REQUIRED_FIELD"
            ))
        
        return results
    
    def validate_type(self, data: Dict[str, Any], expected_type: type) -> List[ValidationResult]:
        """驗證欄位類型"""
        results = []
        
        if self.field_name in data:
            value = data[self.field_name]
            if not isinstance(value, expected_type):
                results.append(self._create_result(
                    False, ValidationSeverity.ERROR,
                    self.field_name,
                    f"欄位 '{self.field_name}' 類型錯誤，期望 {expected_type.__name__}，實際 {type(value).__name__}",
                    f"請將 '{self.field_name}' 轉換為 {expected_type.__name__} 類型",
                    "INVALID_FIELD_TYPE"
                ))
        
        return results
    
    def validate_range(
        self, 
        data: Dict[str, Any], 
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None
    ) -> List[ValidationResult]:
        """驗證數值範圍"""
        results = []
        
        if self.field_name in data:
            value = data[self.field_name]
            if isinstance(value, (int, float)):
                if min_val is not None and value < min_val:
                    results.append(self._create_result(
                        False, ValidationSeverity.ERROR,
                        self.field_name,
                        f"欄位 '{self.field_name}' 值 {value} 小於最小值 {min_val}",
                        f"請將 '{self.field_name}' 設置為 >= {min_val}",
                        "VALUE_TOO_SMALL"
                    ))
                
                if max_val is not None and value > max_val:
                    results.append(self._create_result(
                        False, ValidationSeverity.ERROR,
                        self.field_name,
                        f"欄位 '{self.field_name}' 值 {value} 大於最大值 {max_val}",
                        f"請將 '{self.field_name}' 設置為 <= {max_val}",
                        "VALUE_TOO_LARGE"
                    ))
        
        return results
    
    def validate_string_length(
        self, 
        data: Dict[str, Any], 
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> List[ValidationResult]:
        """驗證字符串長度"""
        results = []
        
        if self.field_name in data:
            value = data[self.field_name]
            if isinstance(value, str):
                length = len(value)
                
                if min_length is not None and length < min_length:
                    results.append(self._create_result(
                        False, ValidationSeverity.ERROR,
                        self.field_name,
                        f"欄位 '{self.field_name}' 長度 {length} 小於最小長度 {min_length}",
                        f"請增加 '{self.field_name}' 的內容",
                        "STRING_TOO_SHORT"
                    ))
                
                if max_length is not None and length > max_length:
                    results.append(self._create_result(
                        False, ValidationSeverity.ERROR,
                        self.field_name,
                        f"欄位 '{self.field_name}' 長度 {length} 大於最大長度 {max_length}",
                        f"請縮短 '{self.field_name}' 的內容",
                        "STRING_TOO_LONG"
                    ))
        
        return results
    
    def validate_enum_value(self, data: Dict[str, Any], valid_values: Set[Any]) -> List[ValidationResult]:
        """驗證枚舉值"""
        results = []
        
        if self.field_name in data:
            value = data[self.field_name]
            if value not in valid_values:
                results.append(self._create_result(
                    False, ValidationSeverity.ERROR,
                    self.field_name,
                    f"欄位 '{self.field_name}' 值 '{value}' 不在有效值範圍內：{valid_values}",
                    f"請將 '{self.field_name}' 設置為有效值之一：{', '.join(map(str, valid_values))}",
                    "INVALID_ENUM_VALUE"
                ))
        
        return results
    
    def validate_datetime_format(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """驗證日期時間格式"""
        results = []
        
        if self.field_name in data:
            value = data[self.field_name]
            if isinstance(value, str) and value:
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    results.append(self._create_result(
                        False, ValidationSeverity.ERROR,
                        self.field_name,
                        f"欄位 '{self.field_name}' 日期格式無效：{value}",
                        f"請使用 ISO 格式 (YYYY-MM-DDTHH:MM:SS)",
                        "INVALID_DATETIME_FORMAT"
                    ))
        
        return results
    
    def validate(self, data: Any, context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """執行所有驗證"""
        # 這是一個基礎實現，子類應該重寫此方法
        return []


class KnowledgePointValidator(BaseValidator):
    """知識點驗證器"""
    
    def validate(self, data: Any, context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """驗證知識點數據"""
        results = []
        
        if not isinstance(data, dict):
            results.append(self._create_result(
                False, ValidationSeverity.CRITICAL,
                "root",
                "知識點數據必須是字典格式",
                "請確保數據是 JSON 對象格式",
                "INVALID_DATA_TYPE"
            ))
            return results
        
        # 驗證必要欄位
        required_fields = ['id', 'key_point', 'category', 'explanation', 'original_phrase', 'correction']
        for field in required_fields:
            validator = FieldValidator(field)
            results.extend(validator.validate_required(data))
        
        # 驗證具體欄位
        if 'id' in data:
            validator = FieldValidator('id')
            results.extend(validator.validate_type(data, int))
            results.extend(validator.validate_range(data, min_val=1))
        
        if 'key_point' in data:
            validator = FieldValidator('key_point')
            results.extend(validator.validate_type(data, str))
            results.extend(validator.validate_string_length(
                data, 
                min_length=ValidationRules.MIN_EXPLANATION_LENGTH,
                max_length=ValidationRules.MAX_EXPLANATION_LENGTH
            ))
        
        if 'category' in data:
            validator = FieldValidator('category')
            results.extend(validator.validate_enum_value(
                data, 
                {ErrorTypes.SYSTEMATIC, ErrorTypes.ISOLATED, ErrorTypes.ENHANCEMENT, ErrorTypes.OTHER}
            ))
        
        if 'mastery_level' in data:
            validator = FieldValidator('mastery_level')
            results.extend(validator.validate_type(data, (int, float)))
            results.extend(validator.validate_range(
                data,
                min_val=ValidationRules.MIN_MASTERY_LEVEL,
                max_val=ValidationRules.MAX_MASTERY_LEVEL
            ))
        
        # 驗證時間戳格式
        for time_field in ['created_at', 'last_seen', 'next_review']:
            if time_field in data:
                validator = FieldValidator(time_field)
                results.extend(validator.validate_datetime_format(data))
        
        # 驗證邏輯一致性
        results.extend(self._validate_logical_consistency(data))
        
        return results
    
    def _validate_logical_consistency(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """驗證邏輯一致性"""
        results = []
        
        # 檢查掌握度與計數的一致性
        mastery_level = data.get('mastery_level', 0)
        correct_count = data.get('correct_count', 0)
        mistake_count = data.get('mistake_count', 0)
        total_count = correct_count + mistake_count
        
        if total_count > 0:
            expected_mastery = correct_count / total_count
            if abs(mastery_level - expected_mastery) > 0.01:  # 允許小誤差
                results.append(self._create_result(
                    False, ValidationSeverity.WARNING,
                    "mastery_level",
                    f"掌握度 {mastery_level} 與計數不一致，期望值 {expected_mastery:.3f}",
                    "請重新計算掌握度或更新計數",
                    "INCONSISTENT_MASTERY_LEVEL"
                ))
        
        # 檢查時間順序
        created_at = data.get('created_at')
        last_seen = data.get('last_seen')
        
        if created_at and last_seen:
            try:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                last_seen_time = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                
                if last_seen_time < created_time:
                    results.append(self._create_result(
                        False, ValidationSeverity.ERROR,
                        "last_seen",
                        "最後查看時間不能早於創建時間",
                        "請檢查時間戳設置",
                        "INVALID_TIME_ORDER"
                    ))
            except ValueError:
                pass  # 時間格式錯誤已在其他地方檢查
        
        return results


class PracticeRecordValidator(BaseValidator):
    """練習記錄驗證器"""
    
    def validate(self, data: Any, context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """驗證練習記錄數據"""
        results = []
        
        if not isinstance(data, dict):
            results.append(self._create_result(
                False, ValidationSeverity.CRITICAL,
                "root",
                "練習記錄數據必須是字典格式",
                "請確保數據是 JSON 對象格式",
                "INVALID_DATA_TYPE"
            ))
            return results
        
        # 驗證必要欄位
        required_fields = ['timestamp', 'chinese_sentence', 'user_answer', 'is_correct']
        for field in required_fields:
            validator = FieldValidator(field)
            results.extend(validator.validate_required(data))
        
        # 驗證具體欄位
        if 'timestamp' in data:
            validator = FieldValidator('timestamp')
            results.extend(validator.validate_datetime_format(data))
        
        if 'chinese_sentence' in data:
            validator = FieldValidator('chinese_sentence')
            results.extend(validator.validate_type(data, str))
            results.extend(validator.validate_string_length(
                data,
                min_length=ValidationRules.MIN_SENTENCE_LENGTH,
                max_length=ValidationRules.MAX_SENTENCE_LENGTH
            ))
        
        if 'user_answer' in data:
            validator = FieldValidator('user_answer')
            results.extend(validator.validate_type(data, str))
            results.extend(validator.validate_string_length(
                data,
                min_length=ValidationRules.MIN_TRANSLATION_LENGTH,
                max_length=ValidationRules.MAX_TRANSLATION_LENGTH
            ))
        
        if 'is_correct' in data:
            validator = FieldValidator('is_correct')
            results.extend(validator.validate_type(data, bool))
        
        if 'practice_mode' in data:
            validator = FieldValidator('practice_mode')
            results.extend(validator.validate_enum_value(
                data,
                set(ValidationRules.VALID_PRACTICE_MODES)
            ))
        
        if 'difficulty_level' in data:
            validator = FieldValidator('difficulty_level')
            results.extend(validator.validate_type(data, int))
            results.extend(validator.validate_range(
                data,
                min_val=ValidationRules.MIN_DIFFICULTY_LEVEL,
                max_val=ValidationRules.MAX_DIFFICULTY_LEVEL
            ))
        
        # 驗證特殊邏輯
        results.extend(self._validate_practice_logic(data))
        
        return results
    
    def _validate_practice_logic(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """驗證練習邏輯"""
        results = []
        
        # 檢查中文句子是否包含中文字符
        chinese_sentence = data.get('chinese_sentence', '')
        if chinese_sentence and not re.search(r'[\u4e00-\u9fff]', chinese_sentence):
            results.append(self._create_result(
                False, ValidationSeverity.WARNING,
                "chinese_sentence",
                "中文句子似乎不包含中文字符",
                "請檢查句子內容是否正確",
                "NO_CHINESE_CHARACTERS"
            ))
        
        # 檢查用戶答案是否包含英文
        user_answer = data.get('user_answer', '')
        if user_answer and not re.search(r'[a-zA-Z]', user_answer):
            results.append(self._create_result(
                False, ValidationSeverity.WARNING,
                "user_answer",
                "用戶答案似乎不包含英文字符",
                "請檢查答案內容是否正確",
                "NO_ENGLISH_CHARACTERS"
            ))
        
        # 檢查知識點ID引用
        knowledge_point_ids = data.get('knowledge_point_ids', [])
        if knowledge_point_ids:
            if not isinstance(knowledge_point_ids, list):
                results.append(self._create_result(
                    False, ValidationSeverity.ERROR,
                    "knowledge_point_ids",
                    "知識點ID必須是列表格式",
                    "請將知識點ID設置為列表",
                    "INVALID_ID_LIST_TYPE"
                ))
            else:
                for i, kp_id in enumerate(knowledge_point_ids):
                    if not isinstance(kp_id, int) or kp_id <= 0:
                        results.append(self._create_result(
                            False, ValidationSeverity.ERROR,
                            f"knowledge_point_ids[{i}]",
                            f"知識點ID必須是正整數，實際值：{kp_id}",
                            "請設置有效的知識點ID",
                            "INVALID_KNOWLEDGE_POINT_ID"
                        ))
        
        return results


class DataMigrator:
    """數據遷移器"""
    
    def __init__(self):
        self.migration_handlers = {}
        self._register_default_migrations()
    
    def _register_default_migrations(self):
        """註冊默認遷移處理器"""
        # 知識點遷移
        self.register_migration('knowledge', '1.0', '2.0', self._migrate_knowledge_1_to_2)
        self.register_migration('knowledge', '2.0', '3.0', self._migrate_knowledge_2_to_3)
        
        # 練習記錄遷移
        self.register_migration('practice', '1.0', '2.0', self._migrate_practice_1_to_2)
    
    def register_migration(
        self, 
        data_type: str, 
        from_version: str, 
        to_version: str, 
        handler: callable
    ):
        """註冊遷移處理器"""
        key = f"{data_type}:{from_version}->{to_version}"
        self.migration_handlers[key] = handler
    
    def migrate(
        self, 
        data: Dict[str, Any], 
        data_type: str, 
        from_version: str, 
        to_version: str
    ) -> MigrationResult:
        """執行數據遷移"""
        try:
            # 如果版本相同，不需要遷移
            if from_version == to_version:
                return MigrationResult(
                    success=True,
                    from_version=from_version,
                    to_version=to_version,
                    migrated_data=data
                )
            
            # 查找遷移路徑
            migration_path = self._find_migration_path(data_type, from_version, to_version)
            if not migration_path:
                return MigrationResult(
                    success=False,
                    from_version=from_version,
                    to_version=to_version,
                    errors=[f"找不到從 {from_version} 到 {to_version} 的遷移路徑"]
                )
            
            # 執行遷移鏈
            current_data = data.copy()
            warnings = []
            
            for step_from, step_to in migration_path:
                key = f"{data_type}:{step_from}->{step_to}"
                handler = self.migration_handlers[key]
                
                try:
                    current_data = handler(current_data)
                    warnings.append(f"成功遷移 {step_from} -> {step_to}")
                except Exception as e:
                    return MigrationResult(
                        success=False,
                        from_version=from_version,
                        to_version=to_version,
                        errors=[f"遷移步驟 {step_from} -> {step_to} 失敗：{str(e)}"]
                    )
            
            return MigrationResult(
                success=True,
                from_version=from_version,
                to_version=to_version,
                migrated_data=current_data,
                warnings=warnings
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                from_version=from_version,
                to_version=to_version,
                errors=[f"遷移過程發生錯誤：{str(e)}"]
            )
    
    def _find_migration_path(
        self, 
        data_type: str, 
        from_version: str, 
        to_version: str
    ) -> Optional[List[Tuple[str, str]]]:
        """查找遷移路徑"""
        # 簡化實現：直接查找一步遷移
        key = f"{data_type}:{from_version}->{to_version}"
        if key in self.migration_handlers:
            return [(from_version, to_version)]
        
        # 這裡可以實現更複雜的多步遷移路徑查找
        return None
    
    def _migrate_knowledge_1_to_2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """知識點從 v1.0 遷移到 v2.0"""
        # 處理舊格式到中間格式的遷移
        if isinstance(data, list):
            # v1.0 是列表格式
            return {
                'version': '2.0',
                'knowledge_points': data,
                'migrated_at': datetime.now().isoformat()
            }
        return data
    
    def _migrate_knowledge_2_to_3(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """知識點從 v2.0 遷移到 v3.0"""
        # 從 knowledge_points 改為 data
        if 'knowledge_points' in data:
            migrated = {
                'version': '3.0',
                'data': data['knowledge_points'],
                'migrated_at': datetime.now().isoformat()
            }
            
            # 保留其他元數據
            for key, value in data.items():
                if key not in ['knowledge_points', 'version']:
                    migrated[key] = value
            
            return migrated
        
        return data
    
    def _migrate_practice_1_to_2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """練習記錄從 v1.0 遷移到 v2.0"""
        if isinstance(data, list):
            # v1.0 是列表格式
            return {
                'version': '2.0',
                'data': data,
                'migrated_at': datetime.now().isoformat()
            }
        return data


class ValidationEngine:
    """驗證引擎"""
    
    def __init__(self):
        self.validators = {
            'knowledge_point': KnowledgePointValidator(),
            'practice_record': PracticeRecordValidator()
        }
        self.migrator = DataMigrator()
    
    def validate_knowledge_data(self, data: Dict[str, Any]) -> Tuple[bool, List[ValidationResult]]:
        """驗證知識點數據"""
        if 'data' not in data:
            return False, [ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                field_path="root",
                message="缺少 'data' 欄位",
                error_code="MISSING_DATA_FIELD"
            )]
        
        all_results = []
        is_valid = True
        
        # 驗證每個知識點
        for i, point in enumerate(data['data']):
            validator = self.validators['knowledge_point']
            results = validator.validate(point)
            
            # 調整欄位路徑
            for result in results:
                result.field_path = f"data[{i}].{result.field_path}"
                if result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    is_valid = False
            
            all_results.extend(results)
        
        return is_valid, all_results
    
    def validate_practice_data(self, data: Dict[str, Any]) -> Tuple[bool, List[ValidationResult]]:
        """驗證練習記錄數據"""
        if 'data' not in data:
            return False, [ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                field_path="root",
                message="缺少 'data' 欄位",
                error_code="MISSING_DATA_FIELD"
            )]
        
        all_results = []
        is_valid = True
        
        # 驗證每條練習記錄
        for i, record in enumerate(data['data']):
            validator = self.validators['practice_record']
            results = validator.validate(record)
            
            # 調整欄位路徑
            for result in results:
                result.field_path = f"data[{i}].{result.field_path}"
                if result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    is_valid = False
            
            all_results.extend(results)
        
        return is_valid, all_results
    
    def migrate_data(
        self, 
        data: Dict[str, Any], 
        data_type: str, 
        target_version: str
    ) -> MigrationResult:
        """遷移數據到目標版本"""
        current_version = data.get('version', '1.0')
        return self.migrator.migrate(data, data_type, current_version, target_version)
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """獲取驗證摘要"""
        summary = {
            'total_issues': len(results),
            'by_severity': {
                'critical': 0,
                'error': 0,
                'warning': 0,
                'info': 0
            },
            'by_category': {},
            'critical_issues': [],
            'suggestions': []
        }
        
        for result in results:
            # 統計嚴重程度
            summary['by_severity'][result.severity.value] += 1
            
            # 統計錯誤代碼類別
            if result.error_code:
                category = result.error_code.split('_')[0] if '_' in result.error_code else 'OTHER'
                summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
            
            # 收集關鍵問題
            if result.severity == ValidationSeverity.CRITICAL:
                summary['critical_issues'].append({
                    'field': result.field_path,
                    'message': result.message,
                    'fix': result.suggested_fix
                })
            
            # 收集建議
            if result.suggested_fix:
                summary['suggestions'].append({
                    'field': result.field_path,
                    'suggestion': result.suggested_fix
                })
        
        return summary


# 創建全局驗證引擎實例
validation_engine = ValidationEngine()