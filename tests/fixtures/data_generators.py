"""
測試數據生成器
提供各種場景的一致性測試數據
"""

import random
from datetime import datetime, timedelta
from typing import Any

from core.error_types import ErrorCategory
from core.knowledge import KnowledgePoint, OriginalError, ReviewExample


class ConsistencyTestDataGenerator:
    """一致性測試專用數據生成器"""

    def __init__(self, seed: int = 42):
        """初始化生成器

        Args:
            seed: 隨機種子，確保測試結果可重現
        """
        self.seed = seed
        random.seed(seed)

        # 預定義測試數據模板
        self.chinese_sentences = [
            "我昨天去學校",
            "她正在看書",
            "我們明天會去旅行",
            "他喜歡吃蘋果",
            "這本書很有趣",
            "我需要買一些食物",
            "天氣今天很好",
            "我正在學習英語",
            "他們在公園裡玩",
            "我想去看電影",
        ]

        self.grammar_points = [
            ("動詞時態", "過去式的正確使用"),
            ("介詞用法", "時間介詞的選擇"),
            ("冠詞使用", "定冠詞和不定冠詞"),
            ("語序問題", "英語語序規則"),
            ("單複數", "名詞單複數變化"),
            ("被動語態", "被動語態的構成"),
            ("條件句", "假設語句的結構"),
            ("疑問句", "疑問句的語序"),
            ("比較級", "形容詞比較級用法"),
            ("倒裝句", "特殊倒裝結構"),
        ]

        self.error_categories = list(ErrorCategory)

    def generate_knowledge_point(
        self,
        index: int = 0,
        category: ErrorCategory = None,
        mastery_level: float = None,
        has_review_examples: bool = True,
        has_original_error: bool = True,
    ) -> KnowledgePoint:
        """生成單個知識點

        Args:
            index: 索引，用於生成唯一數據
            category: 指定錯誤分類
            mastery_level: 指定掌握度
            has_review_examples: 是否包含複習例句
            has_original_error: 是否包含原始錯誤
        """
        if category is None:
            category = random.choice(self.error_categories)

        if mastery_level is None:
            mastery_level = round(random.uniform(0.1, 0.9), 2)

        # 選擇語法點
        subtype, explanation = random.choice(self.grammar_points)

        # 生成原始錯誤
        original_error = None
        if has_original_error:
            chinese_sentence = random.choice(self.chinese_sentences)
            original_error = OriginalError(
                chinese_sentence=chinese_sentence,
                user_answer=f"Incorrect translation {index}",
                correct_answer=f"Correct translation {index}",
                timestamp=(datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            )

        # 生成複習例句
        review_examples = []
        if has_review_examples:
            num_examples = random.randint(1, 4)
            for i in range(num_examples):
                chinese_sentence = random.choice(self.chinese_sentences)
                is_correct = random.choice([True, False])
                review_examples.append(
                    ReviewExample(
                        chinese_sentence=chinese_sentence,
                        user_answer=f"User answer {index}-{i}",
                        correct_answer=f"Correct answer {index}-{i}",
                        timestamp=(
                            datetime.now() - timedelta(days=random.randint(0, 15))
                        ).isoformat(),
                        is_correct=is_correct,
                    )
                )

        # 計算統計數據
        correct_count = sum(1 for ex in review_examples if ex.is_correct)
        mistake_count = len(review_examples) - correct_count

        return KnowledgePoint(
            id=1000 + index,  # 使用固定範圍的 ID
            key_point=f"語法點_{index}: {subtype}",
            category=category,
            subtype=subtype,
            explanation=explanation,
            original_phrase=f"原句_{index}",
            correction=f"修正_{index}",
            original_error=original_error,
            review_examples=review_examples,
            mastery_level=mastery_level,
            mistake_count=mistake_count,
            correct_count=correct_count,
            created_at=(datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
            last_seen=(datetime.now() - timedelta(days=random.randint(0, 7))).isoformat(),
            next_review=(datetime.now() + timedelta(days=random.randint(1, 14))).isoformat(),
            tags=[f"標籤_{index}", f"分類_{category.value}"],
            custom_notes=f"測試筆記_{index}",
            is_deleted=False,
            deleted_at="",
            deleted_reason="",
            version_history=[],
            last_modified=datetime.now().isoformat(),
        )

    def generate_consistent_dataset(
        self, size: int = 20
    ) -> tuple[list[KnowledgePoint], dict[str, Any]]:
        """生成一致的測試數據集，並計算期望的統計結果

        Args:
            size: 數據集大小

        Returns:
            (知識點列表, 期望統計結果)
        """
        points = []
        total_practices = 0
        correct_count = 0
        categories = set()
        mastery_levels = []
        due_reviews = 0

        now = datetime.now()

        for i in range(size):
            point = self.generate_knowledge_point(i)

            # 計算統計
            total_practices += len(point.review_examples)
            if point.original_error:
                total_practices += 1

            correct_count += sum(1 for ex in point.review_examples if ex.is_correct)
            categories.add(point.category.to_chinese())
            mastery_levels.append(point.mastery_level)

            # 檢查是否需要復習
            if point.next_review and datetime.fromisoformat(point.next_review) <= now:
                due_reviews += 1

            points.append(point)

        expected_stats = {
            "total_knowledge_points": size,
            "total_practices": total_practices,
            "correct_count": correct_count,
            "categories": sorted(list(categories)),  # 按字母順序排序
            "average_mastery": round(sum(mastery_levels) / len(mastery_levels), 4)
            if mastery_levels
            else 0,
            "due_reviews": due_reviews,
        }

        return points, expected_stats

    def generate_edge_case_dataset(self) -> list[KnowledgePoint]:
        """生成邊界情況測試數據"""
        edge_cases = []

        # 1. 極低掌握度
        edge_cases.append(
            self.generate_knowledge_point(
                index=9001,
                mastery_level=0.0,
                has_review_examples=False,  # 沒有練習例句
            )
        )

        # 2. 極高掌握度
        edge_cases.append(
            self.generate_knowledge_point(
                index=9002,
                mastery_level=1.0,
                has_original_error=False,  # 沒有原始錯誤
            )
        )

        # 3. 只有原始錯誤，沒有複習例句
        edge_cases.append(
            self.generate_knowledge_point(
                index=9003, has_review_examples=False, has_original_error=True
            )
        )

        # 4. 只有複習例句，沒有原始錯誤
        edge_cases.append(
            self.generate_knowledge_point(
                index=9004, has_review_examples=True, has_original_error=False
            )
        )

        # 5. 完全空的練習記錄
        empty_point = self.generate_knowledge_point(
            index=9005, has_review_examples=False, has_original_error=False
        )
        empty_point.mistake_count = 0
        empty_point.correct_count = 0
        edge_cases.append(empty_point)

        return edge_cases

    def generate_category_balanced_dataset(
        self, size_per_category: int = 5
    ) -> list[KnowledgePoint]:
        """生成每個分類平均分佈的數據集"""
        balanced_points = []
        index = 8000

        for category in self.error_categories:
            for _i in range(size_per_category):
                point = self.generate_knowledge_point(index=index, category=category)
                balanced_points.append(point)
                index += 1

        return balanced_points

    def generate_performance_test_dataset(self, size: int = 1000) -> list[KnowledgePoint]:
        """生成性能測試數據集"""
        performance_points = []

        for i in range(size):
            # 為性能測試生成更複雜的數據
            point = self.generate_knowledge_point(
                index=7000 + i, has_review_examples=True, has_original_error=True
            )

            # 增加更多複習例句
            additional_examples = []
            for j in range(random.randint(2, 8)):
                chinese_sentence = random.choice(self.chinese_sentences)
                additional_examples.append(
                    ReviewExample(
                        chinese_sentence=chinese_sentence,
                        user_answer=f"Performance test answer {i}-{j}",
                        correct_answer=f"Performance test correct {i}-{j}",
                        timestamp=(
                            datetime.now() - timedelta(days=random.randint(0, 30))
                        ).isoformat(),
                        is_correct=random.choice([True, False]),
                    )
                )

            point.review_examples.extend(additional_examples)

            # 重新計算統計
            point.correct_count = sum(1 for ex in point.review_examples if ex.is_correct)
            point.mistake_count = len(point.review_examples) - point.correct_count

            performance_points.append(point)

        return performance_points

    def generate_migration_test_data(self) -> tuple[list[KnowledgePoint], list[KnowledgePoint]]:
        """生成遷移測試數據

        返回 (遷移前數據, 遷移後數據)，用於測試數據遷移的一致性
        """
        # 生成原始數據
        original_data, _ = self.generate_consistent_dataset(30)

        # 生成"遷移後"的數據（模擬遷移過程可能的變化）
        migrated_data = []
        for point in original_data:
            # 創建副本
            migrated_point = KnowledgePoint(
                id=point.id,
                key_point=point.key_point,
                category=point.category,
                subtype=point.subtype,
                explanation=point.explanation,
                original_phrase=point.original_phrase,
                correction=point.correction,
                original_error=point.original_error,
                review_examples=point.review_examples.copy(),
                mastery_level=point.mastery_level,
                mistake_count=point.mistake_count,
                correct_count=point.correct_count,
                created_at=point.created_at,
                last_seen=point.last_seen,
                next_review=point.next_review,
                tags=point.tags.copy(),
                custom_notes=point.custom_notes,
                is_deleted=point.is_deleted,
                deleted_at=point.deleted_at,
                deleted_reason=point.deleted_reason,
                version_history=point.version_history.copy(),
                last_modified=datetime.now().isoformat(),  # 更新最後修改時間
            )
            migrated_data.append(migrated_point)

        return original_data, migrated_data


# 便利函數
def create_test_knowledge_point_with_stats(
    total_practices: int = 5, correct_practices: int = 3, mastery_level: float = 0.6
) -> KnowledgePoint:
    """創建具有指定統計特性的測試知識點"""
    generator = ConsistencyTestDataGenerator()

    # 生成基本知識點
    point = generator.generate_knowledge_point(
        index=random.randint(1, 1000), mastery_level=mastery_level
    )

    # 根據要求調整練習數據
    review_examples = []
    for i in range(total_practices):
        is_correct = i < correct_practices
        review_examples.append(
            ReviewExample(
                chinese_sentence=f"測試句子 {i}",
                user_answer=f"用戶答案 {i}",
                correct_answer=f"正確答案 {i}",
                timestamp=datetime.now().isoformat(),
                is_correct=is_correct,
            )
        )

    point.review_examples = review_examples
    point.correct_count = correct_practices
    point.mistake_count = total_practices - correct_practices

    return point


def create_minimal_test_dataset(size: int = 3) -> list[KnowledgePoint]:
    """創建最小測試數據集（用於快速測試）"""
    generator = ConsistencyTestDataGenerator(seed=123)
    return [generator.generate_knowledge_point(i) for i in range(size)]
