"""
標籤系統核心模組
處理文法句型標籤的管理和題目生成
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.log_config import get_module_logger

logger = get_module_logger(__name__)

# 資料目錄
DATA_DIR = Path(__file__).parent.parent / "data"


class TagType(Enum):
    """標籤類型"""
    GRAMMAR = "grammar"        # 文法句型 (GP001-GP111)
    KNOWLEDGE = "knowledge"    # 知識點 (錯誤ID)
    TOPIC = "topic"           # 主題 (旅遊、商業、日常)
    DIFFICULTY = "difficulty" # 難度標籤
    FOCUS = "focus"          # 重點考察 (時態、介係詞等)


class CombinationMode(Enum):
    """標籤組合模式"""
    ALL = "all"           # 必須包含所有標籤
    ANY = "any"           # 包含至少一個標籤
    FOCUS = "focus"       # 重點練習第一個，其他為輔
    WEIGHTED = "weighted" # 根據掌握度權重選擇


@dataclass
class Tag:
    """標籤資料結構"""
    id: str
    type: TagType
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    complexity: int = 2  # 1-5 複雜度
    usage_count: int = 0
    success_rate: float = 0.0
    last_practiced: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TagCombination:
    """標籤組合"""
    tags: List[Tag]
    mode: CombinationMode
    name: Optional[str] = None
    description: Optional[str] = None


class TagRelationship:
    """標籤關聯規則"""

    # 相關標籤推薦規則
    RELATED_TAGS = {
        # 強調句型相關
        'GP001': ['GP002', 'GP015'],  # 強調句 → 倒裝句、被動語態
        'GP002': ['GP001', 'GP003'],  # 倒裝句 → 強調句、省略句

        # 時態相關
        'GP010': ['GP011', 'GP012'],  # 現在完成式 → 過去完成式、完成進行式
        'GP011': ['GP010', 'GP012'],  # 過去完成式 → 現在完成式、完成進行式

        # 條件句相關
        'GP020': ['GP021', 'GP022'],  # 條件句 → 假設語氣、願望句
        'GP021': ['GP020', 'GP022'],  # 假設語氣 → 條件句、願望句

        # 比較級相關
        'GP030': ['GP031', 'GP032'],  # 比較級 → 最高級、同級比較
        'GP031': ['GP030', 'GP032'],  # 最高級 → 比較級、同級比較
    }

    # 互斥標籤（不建議一起使用）
    EXCLUSIVE_TAGS = {
        'GP010': ['GP050'],  # 現在完成式 vs 簡單過去式
        'GP020': ['GP060'],  # 條件句 vs 直述句
    }

    # 標籤組合模板
    TEMPLATES = {
        "時態大師": {
            "tags": ["GP010", "GP011", "GP012"],
            "description": "練習各種完成式時態",
            "difficulty": 3
        },
        "條件達人": {
            "tags": ["GP020", "GP021", "GP022"],
            "description": "掌握條件句和假設語氣",
            "difficulty": 4
        },
        "比較專家": {
            "tags": ["GP030", "GP031", "GP032"],
            "description": "精通比較級和最高級",
            "difficulty": 2
        },
        "強調與倒裝": {
            "tags": ["GP001", "GP002"],
            "description": "學習強調句型和倒裝結構",
            "difficulty": 3
        },
        "商業英文": {
            "tags": ["GP040", "GP041", "GP042"],
            "description": "商業場景常用句型",
            "difficulty": 3
        }
    }


class TagManager:
    """標籤管理器"""

    def __init__(self):
        self.logger = logger
        self.tags: Dict[str, Tag] = {}
        self.patterns_data = self._load_patterns_data()
        self._initialize_grammar_tags()

    def _load_patterns_data(self) -> Dict:
        """載入文法句型資料"""
        patterns_file = DATA_DIR / "patterns_enriched_complete.json"
        if patterns_file.exists():
            with open(patterns_file, encoding='utf-8') as f:
                data = json.load(f)
                return {p['id']: p for p in data.get('patterns', [])}
        return {}

    def _initialize_grammar_tags(self):
        """初始化文法句型標籤"""
        for pattern_id, pattern in self.patterns_data.items():
            tag = Tag(
                id=pattern_id,
                type=TagType.GRAMMAR,
                name=pattern.get('pattern', ''),
                description=pattern.get('core_concept', ''),
                category=pattern.get('category', ''),
                complexity=self._calculate_complexity(pattern)
            )
            self.tags[pattern_id] = tag

        self.logger.info(f"Initialized {len(self.tags)} grammar tags")

    def _calculate_complexity(self, pattern: Dict) -> int:
        """計算句型複雜度 (1-5)"""
        # 基於例句長度、變化數量等因素計算
        complexity = 2  # 預設中等

        if pattern.get('variations'):
            complexity += min(2, len(pattern['variations']) // 3)

        if pattern.get('common_errors'):
            complexity += min(1, len(pattern['common_errors']) // 2)

        return min(5, max(1, complexity))

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """獲取標籤"""
        return self.tags.get(tag_id)

    def get_tags_by_type(self, tag_type: TagType) -> List[Tag]:
        """根據類型獲取標籤"""
        return [t for t in self.tags.values() if t.type == tag_type]

    def get_tags_by_category(self, category: str) -> List[Tag]:
        """根據分類獲取標籤"""
        return [t for t in self.tags.values() if t.category == category]

    def get_related_tags(self, tag_id: str, max_count: int = 3) -> List[Tag]:
        """獲取相關標籤"""
        related_ids = TagRelationship.RELATED_TAGS.get(tag_id, [])
        related_tags = []

        for rid in related_ids[:max_count]:
            tag = self.get_tag(rid)
            if tag:
                related_tags.append(tag)

        return related_tags

    def validate_combination(self, tag_ids: List[str]) -> Dict[str, Any]:
        """驗證標籤組合的合理性"""
        warnings = []
        suggestions = []

        if not tag_ids:
            return {
                "valid": False,
                "warnings": ["至少需要選擇一個標籤"],
                "suggestions": []
            }

        tags = [self.get_tag(tid) for tid in tag_ids if self.get_tag(tid)]

        # 檢查標籤數量
        if len(tags) > 3:
            warnings.append("標籤過多，建議不超過3個以確保練習效果")

        # 檢查複雜度跨度
        complexities = [t.complexity for t in tags]
        if complexities:
            complexity_range = max(complexities) - min(complexities)
            if complexity_range > 2:
                warnings.append("標籤難度跨度較大，可能影響練習體驗")

        # 檢查互斥標籤
        for tid in tag_ids:
            exclusive = TagRelationship.EXCLUSIVE_TAGS.get(tid, [])
            conflicts = [e for e in exclusive if e in tag_ids]
            if conflicts:
                warnings.append(f"標籤 {tid} 與 {conflicts} 不建議同時使用")

        # 提供建議
        if len(tags) == 1:
            related = self.get_related_tags(tags[0].id)
            if related:
                suggestions.append(f"可以考慮加入相關標籤：{', '.join([t.name for t in related])}")

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "suggestions": suggestions,
            "complexity_score": sum(complexities) / len(complexities) if complexities else 2
        }

    def get_template(self, template_name: str) -> Optional[TagCombination]:
        """獲取標籤組合模板"""
        template = TagRelationship.TEMPLATES.get(template_name)
        if not template:
            return None

        tags = [self.get_tag(tid) for tid in template['tags'] if self.get_tag(tid)]

        return TagCombination(
            tags=tags,
            mode=CombinationMode.ALL,
            name=template_name,
            description=template.get('description')
        )

    def get_all_templates(self) -> Dict[str, TagCombination]:
        """獲取所有模板"""
        templates = {}
        for name in TagRelationship.TEMPLATES:
            template = self.get_template(name)
            if template:
                templates[name] = template
        return templates

    def search_tags(self, query: str, limit: int = 10) -> List[Tag]:
        """搜尋標籤"""
        query = query.lower()
        results = []

        for tag in self.tags.values():
            # 搜尋名稱和描述
            if (query in tag.name.lower() or
                (tag.description and query in tag.description.lower()) or
                (tag.category and query in tag.category.lower())):
                results.append(tag)

            if len(results) >= limit:
                break

        return results

    def update_tag_stats(self, tag_id: str, success: bool):
        """更新標籤使用統計"""
        tag = self.get_tag(tag_id)
        if not tag:
            return

        tag.usage_count += 1
        tag.last_practiced = datetime.now()

        # 更新成功率 (移動平均)
        alpha = 0.1  # 平滑係數
        tag.success_rate = (1 - alpha) * tag.success_rate + alpha * (1.0 if success else 0.0)

        self.logger.info(f"Updated stats for tag {tag_id}: usage={tag.usage_count}, success_rate={tag.success_rate:.2f}")


# 全域實例
tag_manager = TagManager()
