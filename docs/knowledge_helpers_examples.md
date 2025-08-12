# 知識點輔助函數使用示例

本文檔展示如何使用 `services/knowledge_helpers.py` 中的輔助函數。

## 基本工具函數

### 1. 生成唯一標識符

```python
from services.knowledge_helpers import generate_unique_identifier

# 為知識點生成唯一標識
identifier = generate_unique_identifier(
    key_point="動詞變化: go",
    original_phrase="go", 
    correction="goes"
)
print(identifier)  # "動詞變化: go|go|goes#d1133c15"
```

### 2. 驗證知識點數據

```python
from services.knowledge_helpers import validate_knowledge_point_data

data = {
    'key_point': '動詞變化錯誤',
    'category': 'systematic',
    'explanation': '第三人稱單數動詞需要加s',
    'original_phrase': 'go',
    'correction': 'goes',
    'mastery_level': 0.5,
    'mistake_count': 2,
    'correct_count': 1
}

is_valid, errors = validate_knowledge_point_data(data)
if is_valid:
    print("數據有效")
else:
    print(f"驗證失敗: {errors}")
```

### 3. 計算掌握度

```python
from services.knowledge_helpers import _calculate_mastery_level

# 計算基於正確/錯誤次數的掌握度
mastery = _calculate_mastery_level(correct_count=3, mistake_count=2)
print(f"掌握度: {mastery:.2f}")  # 0.40
```

## 間隔重複算法

### 4. 計算複習間隔

```python
from services.knowledge_helpers import calculate_next_review_interval

# 基於 SM-2 算法計算複習間隔
interval = calculate_next_review_interval(
    mastery_level=0.6,
    mistake_count=2,
    correct_count=3
)
print(f"下次複習間隔: {interval} 天")
```

### 5. 計算下次複習時間

```python
from services.knowledge_helpers import _calculate_next_review
from core.error_types import ErrorCategory

base_intervals = {
    "immediate": 1,
    "short": 3,
    "medium": 7,
    "long": 14,
    "mastered": 30
}

next_review = _calculate_next_review(
    mastery_level=0.3,
    category=ErrorCategory.SYSTEMATIC,
    base_intervals=base_intervals
)
print(f"下次複習時間: {next_review}")
```

## 知識點管理

### 6. 查找知識點

```python
from services.knowledge_helpers import _find_knowledge_point

# 在知識點列表中查找匹配的點
found_point = _find_knowledge_point(
    knowledge_points=my_knowledge_points,
    key_point="動詞變化: go",
    original_phrase="go",
    correction="goes"
)
```

### 7. 知識點分組

```python
from services.knowledge_helpers import _group_knowledge_points

# 按類別分組知識點
groups = _group_knowledge_points(knowledge_points)
for category, points in groups.items():
    print(f"{category}: {len(points)} 個知識點")
```

### 8. 合併重複知識點

```python
from services.knowledge_helpers import _merge_duplicate_points

# 合併具有相同標識符的知識點
unique_points = _merge_duplicate_points(knowledge_points)
print(f"合併後: {len(unique_points)} 個唯一知識點")
```

## 複習管理

### 9. 計算複習優先級

```python
from services.knowledge_helpers import calculate_review_priority

level, score = calculate_review_priority(knowledge_point)
priority_names = {1: "緊急", 2: "重要", 3: "一般", 4: "可延後"}
print(f"優先級: {priority_names[level]} (分數: {score:.2f})")
```

### 10. 篩選複習候選

```python
from services.knowledge_helpers import filter_review_candidates
from core.error_types import ErrorCategory

# 篩選系統性錯誤且掌握度低的知識點
candidates = filter_review_candidates(
    knowledge_points=my_points,
    categories=[ErrorCategory.SYSTEMATIC, ErrorCategory.ISOLATED],
    max_mastery=0.6,
    min_mistakes=1
)
print(f"找到 {len(candidates)} 個複習候選")
```

## 顯示和分析

### 11. 格式化知識點顯示

```python
from services.knowledge_helpers import format_knowledge_point_display

# 格式化知識點為可讀文本
display_text = format_knowledge_point_display(
    knowledge_point,
    include_stats=True
)
print(display_text)
```

### 12. 計算難度分數

```python
from services.knowledge_helpers import calculate_difficulty_score

difficulty = calculate_difficulty_score(knowledge_point)
print(f"難度分數: {difficulty:.1f}/10.0")
```

### 13. 提取錯誤標籤

```python
from services.knowledge_helpers import extract_tags_from_error

error_info = {
    'key_point_summary': '動詞時態錯誤',
    'explanation': '過去式動詞變化不正確',
    'category': 'systematic'
}

tags = extract_tags_from_error(error_info)
print(f"提取的標籤: {tags}")
```

## 學習分析

### 14. 獲取學習建議

```python
from services.knowledge_helpers import get_learning_recommendations
from core.error_types import ErrorTypeSystem

type_system = ErrorTypeSystem()
recommendations = get_learning_recommendations(knowledge_points, type_system)

for rec in recommendations:
    print(f"類別: {rec['category']}")
    print(f"建議: {rec['advice']}")
    print(f"重點領域: {rec['focus_area']}")
    print(f"弱點數量: {len(rec['weak_points'])}")
    print("---")
```

## 實際應用示例

### 完整的複習流程

```python
from services.knowledge_helpers import *
from core.error_types import ErrorCategory

# 1. 篩選需要複習的知識點
review_candidates = filter_review_candidates(
    knowledge_points=all_points,
    categories=[ErrorCategory.SYSTEMATIC, ErrorCategory.ISOLATED],
    max_mastery=0.7
)

# 2. 計算每個點的優先級並排序
prioritized = []
for point in review_candidates:
    level, score = calculate_review_priority(point)
    prioritized.append((point, level, score))

# 按優先級排序
prioritized.sort(key=lambda x: (x[1], x[2]))

# 3. 選擇前5個最需要複習的
top_5 = prioritized[:5]

print("今日複習計劃:")
for i, (point, level, score) in enumerate(top_5, 1):
    print(f"{i}. {point.key_point}")
    print(f"   優先級: {level}, 掌握度: {int(point.mastery_level*100)}%")
    print(f"   難度: {calculate_difficulty_score(point):.1f}/10")
    print()
```

### 錯誤分析流程

```python
# 分析新的錯誤並創建知識點
def process_new_error(error_info, knowledge_points):
    # 1. 提取標籤
    tags = extract_tags_from_error(error_info)
    
    # 2. 生成唯一標識符
    identifier = generate_unique_identifier(
        error_info['key_point_summary'],
        error_info['original_phrase'],
        error_info['correction']
    )
    
    # 3. 檢查是否已存在
    existing = _find_knowledge_point(
        knowledge_points,
        error_info['key_point_summary'],
        error_info['original_phrase'],
        error_info['correction']
    )
    
    if existing:
        # 更新現有知識點
        existing.mistake_count += 1
        existing.mastery_level = _calculate_mastery_level(
            existing.correct_count,
            existing.mistake_count
        )
        return existing
    else:
        # 創建新知識點
        new_id = _get_next_id(knowledge_points)
        # ... 創建新的 KnowledgePoint 對象
        return new_point
```

## 注意事項

1. **純函數設計**: 所有輔助函數都是純函數，不產生副作用，易於測試
2. **類型安全**: 使用了完整的類型提示，提高代碼可靠性
3. **錯誤處理**: 內建數據驗證和邊界檢查
4. **性能考慮**: 算法經過優化，適合處理大量知識點
5. **可擴展性**: 模組化設計，易於添加新功能

## 測試

運行測試確保功能正常:

```bash
python -m pytest tests/unit/test_knowledge_helpers.py -v
```

所有函數都通過了全面的單元測試，確保可靠性。