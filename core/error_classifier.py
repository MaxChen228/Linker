"""
錯誤分類器 - 智能分類錯誤類型
"""


class ErrorClassifier:
    """錯誤智能分類器"""

    # 系統性錯誤的關鍵詞模式
    SYSTEMATIC_PATTERNS = {
        "verb_conjugation": [
            "第三人稱單數",
            "動詞變化",
            "加s",
            "加es",
            "動詞形式",
            "third person singular",
            "verb form",
            "conjugation",
        ],
        "tense": [
            "時態",
            "過去式",
            "現在式",
            "未來式",
            "完成式",
            "進行式",
            "tense",
            "past",
            "present",
            "future",
            "perfect",
            "continuous",
        ],
        "voice": [
            "主動",
            "被動",
            "語態",
            "被動語態",
            "主動語態",
            "active voice",
            "passive voice",
            "voice",
        ],
        "agreement": [
            "主詞動詞一致",
            "單複數一致",
            "主謂一致",
            "subject-verb agreement",
            "number agreement",
        ],
        "word_order": [
            "語序",
            "倒裝",
            "疑問句",
            "否定句",
            "word order",
            "inversion",
            "question",
            "negative",
        ],
    }

    # 單一性錯誤的關鍵詞模式
    ISOLATED_PATTERNS = {
        "vocabulary": [
            "單字",
            "詞彙",
            "用詞",
            "翻譯錯誤",
            "詞義",
            "vocabulary",
            "word choice",
            "translation",
            "meaning",
        ],
        "collocation": [
            "搭配詞",
            "片語",
            "慣用語",
            "固定搭配",
            "collocation",
            "phrase",
            "idiom",
            "fixed expression",
        ],
        "preposition": [
            "介詞",
            "介係詞",
            "介系詞",
            "前置詞",
            "preposition",
            "at",
            "in",
            "on",
            "by",
            "with",
            "for",
        ],
        "spelling": ["拼寫", "拼字", "拼錯", "字母", "spelling", "misspell", "typo"],
        "word_form": [
            "詞性",
            "名詞",
            "動詞",
            "形容詞",
            "副詞",
            "part of speech",
            "noun",
            "verb",
            "adjective",
            "adverb",
        ],
    }

    # 可以更好的關鍵詞模式
    ENHANCEMENT_PATTERNS = [
        "更自然",
        "更道地",
        "更流暢",
        "更常見",
        "更好",
        "建議使用",
        "不夠自然",
        "生硬",
        "中式英文",
        "語感",
        "慣用表達",
        "more natural",
        "native",
        "fluent",
        "better",
        "awkward",
        "Chinglish",
        "idiomatic",
    ]

    @classmethod
    def classify_error(cls, error_data: dict) -> tuple[str, str]:
        """
        分類單個錯誤

        Returns:
            (error_category, error_subcategory)
            error_category: "systematic", "isolated", "enhancement", "other"
            error_subcategory: 具體的子類別
        """
        # 獲取錯誤描述文本
        key_point = error_data.get("key_point_summary", "").lower()
        explanation = error_data.get("explanation", "").lower()
        severity = error_data.get("severity", "major")

        combined_text = f"{key_point} {explanation}"

        # 1. 檢查是否為「可以更好」類型
        if severity == "minor" or cls._is_enhancement(combined_text):
            return "enhancement", "style"

        # 2. 檢查系統性錯誤
        systematic_type = cls._check_systematic(combined_text)
        if systematic_type:
            return "systematic", systematic_type

        # 3. 檢查單一性錯誤
        isolated_type = cls._check_isolated(combined_text)
        if isolated_type:
            return "isolated", isolated_type

        # 4. 其他錯誤
        return "other", "unclassified"

    @classmethod
    def _is_enhancement(cls, text: str) -> bool:
        """檢查是否為「可以更好」類型"""
        for pattern in cls.ENHANCEMENT_PATTERNS:
            if pattern in text:
                return True
        return False

    @classmethod
    def _check_systematic(cls, text: str) -> str:
        """檢查系統性錯誤類型"""
        for error_type, patterns in cls.SYSTEMATIC_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return error_type
        return ""

    @classmethod
    def _check_isolated(cls, text: str) -> str:
        """檢查單一性錯誤類型"""
        for error_type, patterns in cls.ISOLATED_PATTERNS.items():
            for pattern in patterns:
                if pattern in text:
                    return error_type
        return ""

    @classmethod
    def get_category_name(cls, category: str) -> str:
        """獲取分類的中文名稱"""
        names = {
            "systematic": "系統性錯誤",
            "isolated": "單一性錯誤",
            "enhancement": "可以更好",
            "other": "其他錯誤",
        }
        return names.get(category, "未分類")

    @classmethod
    def get_subcategory_name(cls, subcategory: str) -> str:
        """獲取子分類的中文名稱"""
        names = {
            # 系統性錯誤
            "verb_conjugation": "動詞變化",
            "tense": "時態",
            "voice": "語態",
            "agreement": "主謂一致",
            "word_order": "語序",
            # 單一性錯誤
            "vocabulary": "詞彙選擇",
            "collocation": "搭配詞",
            "preposition": "介係詞",
            "spelling": "拼寫",
            "word_form": "詞性",
            # 其他
            "style": "語言風格",
            "unclassified": "未分類",
        }
        return names.get(subcategory, subcategory)

    @classmethod
    def get_learning_priority(cls, category: str) -> int:
        """
        獲取學習優先級（1-4，數字越小優先級越高）
        """
        priorities = {
            "systematic": 1,  # 最高優先級 - 解決一個規則能避免很多錯誤
            "isolated": 2,  # 次高優先級 - 需要個別記憶
            "other": 3,  # 中等優先級 - 其他類型錯誤
            "enhancement": 4,  # 最低優先級 - 已經正確，只是可以更好
        }
        return priorities.get(category, 3)

    @classmethod
    def analyze_error_patterns(cls, errors: list[dict]) -> dict:
        """
        分析錯誤模式，提供學習建議
        """
        category_counts = {"systematic": {}, "isolated": {}, "enhancement": 0, "other": 0}

        for error in errors:
            category, subcategory = cls.classify_error(error)

            if category in ["systematic", "isolated"]:
                if subcategory not in category_counts[category]:
                    category_counts[category][subcategory] = 0
                category_counts[category][subcategory] += 1
            else:
                category_counts[category] += 1

        # 生成學習建議
        suggestions = []

        # 系統性錯誤建議
        if category_counts["systematic"]:
            most_common = max(category_counts["systematic"].items(), key=lambda x: x[1])
            suggestions.append(
                {
                    "priority": "高",
                    "type": "系統性錯誤",
                    "focus": cls.get_subcategory_name(most_common[0]),
                    "count": most_common[1],
                    "advice": f"建議優先複習{cls.get_subcategory_name(most_common[0])}相關文法規則",
                }
            )

        # 單一性錯誤建議
        if category_counts["isolated"]:
            total_isolated = sum(category_counts["isolated"].values())
            suggestions.append(
                {
                    "priority": "中",
                    "type": "單一性錯誤",
                    "focus": "詞彙和搭配",
                    "count": total_isolated,
                    "advice": "建議加強單字記憶和常見搭配詞練習",
                }
            )

        # 可以更好建議
        if category_counts["enhancement"] > 0:
            suggestions.append(
                {
                    "priority": "低",
                    "type": "語言優化",
                    "focus": "表達自然度",
                    "count": category_counts["enhancement"],
                    "advice": "你的基礎不錯，可以多閱讀原文提升語感",
                }
            )

        return {
            "distribution": category_counts,
            "suggestions": suggestions,
            "total_errors": len(errors),
        }
