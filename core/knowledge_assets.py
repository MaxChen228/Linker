"""
知識資源載入器（新版本）

集中載入並提供查詢：
- data/grammar_patterns.json（文法句型主來源）
- core/assets.py 內的 EXAMPLE_SENTENCE_BANK（分級例句庫主來源）

此模組為新版本的統一入口，不再依賴舊的 examples.json 與 grammar.json。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class GrammarPattern:
    """文法句型資料結構（統一格式）"""

    id: Optional[str]
    category: Optional[str]
    pattern: str
    explanation: Optional[str]
    example_zh: Optional[str]
    example_en: Optional[str]


class GrammarRepository:
    """文法句型資源存取（僅使用新版來源）"""

    def __init__(self, grammar_patterns_file: Path | str | None = None):
        self.grammar_patterns_file = (
            Path(grammar_patterns_file) if grammar_patterns_file else DATA_DIR / "grammar_patterns.json"
        )

    def load_advanced_grammar(self) -> list[GrammarPattern]:
        """載入新增的 grammar_patterns.json（含 id / category）"""
        if not self.grammar_patterns_file.exists():
            return []

        try:
            data = json.loads(self.grammar_patterns_file.read_text(encoding="utf-8"))
        except Exception:
            return []

        patterns: list[GrammarPattern] = []
        for item in data:
            patterns.append(
                GrammarPattern(
                    id=item.get("id"),
                    category=item.get("category"),
                    pattern=item.get("pattern", ""),
                    explanation=item.get("explanation"),
                    example_zh=item.get("example_zh"),
                    example_en=item.get("example_en"),
                )
            )
        return patterns

    def load_all_grammar(self) -> list[GrammarPattern]:
        """返回所有文法句型（僅來自 grammar_patterns.json）。"""
        return self.load_advanced_grammar()


class ExampleRepository:
    """例句資源存取（僅使用新版來源）"""

    def load_bank_from_assets(self) -> dict[str, Any]:
        """載入 core/assets.py 的 EXAMPLE_SENTENCE_BANK。"""
        try:
            # 延遲匯入以避免啟動時不必要的成本
            from core.assets import EXAMPLE_SENTENCE_BANK  # type: ignore

            if isinstance(EXAMPLE_SENTENCE_BANK, dict):
                return EXAMPLE_SENTENCE_BANK
        except Exception:
            pass
        return {}

    def sample_bank(self, length: str, difficulty: int) -> list[str]:
        """從 assets 例句庫取樣。

        - length: "short" | "medium" | "long"
        - difficulty: 1..5
        """
        bank = self.load_bank_from_assets()
        if not bank:
            return []
        by_length = bank.get(length, {})
        candidates: list[str] = by_length.get(str(difficulty), []) if isinstance(by_length, dict) else []
        return list(candidates)


class KnowledgeAssets:
    """對外統一門面：提供文法句型與例句查詢。"""

    def __init__(
        self,
        grammar_repo: Optional[GrammarRepository] = None,
        example_repo: Optional[ExampleRepository] = None,
    ):
        self.grammar_repo = grammar_repo or GrammarRepository()
        self.example_repo = example_repo or ExampleRepository()

    # 文法查詢
    def get_grammar_patterns(self, category: Optional[str] = None) -> list[GrammarPattern]:
        patterns = self.grammar_repo.load_all_grammar()
        if category:
            return [p for p in patterns if (p.category == category)]
        return patterns

    # 例句查詢
    def get_example_bank(self, length: str, difficulty: int) -> list[str]:
        return self.example_repo.sample_bank(length=length, difficulty=difficulty)

    # 已不再提供舊 examples.json 的讀取


__all__ = [
    "GrammarPattern",
    "GrammarRepository",
    "ExampleRepository",
    "KnowledgeAssets",
]


