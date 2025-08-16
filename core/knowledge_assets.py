"""
知識資源載入與管理模組

此模組作為一個統一的入口，負責載入、管理和提供應用程式所需的靜態知識資源。
它取代了舊的、分散的資源載入方式，提供了一個清晰、集中的資源存取點。

主要管理的資源：
- **文法句型 (Grammar Patterns)**：從 `assets/grammar_patterns.json` 載入。
- **分級例句庫 (Example Sentence Bank)**：從 `core/assets.py` 載入。

設計模式：
- **倉儲模式 (Repository Pattern)**：使用 `GrammarRepository` 和 `ExampleRepository`
  來封裝不同資源的載入邏輯，使得資源的來源和格式對上層透明。
- **門面模式 (Facade Pattern)**：`KnowledgeAssets` 類別作為一個統一的門面，
  為應用程式的其他部分提供簡單、一致的資源查詢介面。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 定義專案和資源目錄的絕對路徑
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"


@dataclass
class GrammarPattern:
    """定義文法句型的標準資料結構。"""

    id: str | None
    category: str | None
    pattern: str
    explanation: str | None
    example_zh: str | None
    example_en: str | None


class GrammarRepository:
    """文法句型資源的倉儲。

    負責從 `grammar_patterns.json` 檔案中讀取和解析文法句型資料。
    """

    def __init__(self, grammar_patterns_file: Path | str | None = None):
        """初始化倉儲，指定文法句型檔案的路徑。"""
        self.grammar_patterns_file = (
            Path(grammar_patterns_file)
            if grammar_patterns_file
            else ASSETS_DIR / "grammar_patterns.json"
        )

    def load_all_grammar(self) -> list[GrammarPattern]:
        """載入所有文法句型。

        Returns:
            一個包含所有 `GrammarPattern` 物件的列表。
        """
        if not self.grammar_patterns_file.exists():
            return []
        try:
            data = json.loads(self.grammar_patterns_file.read_text(encoding="utf-8"))
            return [GrammarPattern(**item) for item in data if isinstance(item, dict)]
        except (json.JSONDecodeError, TypeError) as e:
            # 在實際應用中，應使用 logger 記錄錯誤
            print(f"Error loading grammar patterns: {e}")
            return []


class ExampleRepository:
    """分級例句庫的倉儲。

    負責從 `core/assets.py` 中的 `EXAMPLE_SENTENCE_BANK` 變數載入例句。
    """

    def load_bank_from_assets(self) -> dict[str, Any]:
        """動態載入 `EXAMPLE_SENTENCE_BANK`。
        使用延遲匯入（lazy import）以避免不必要的啟動成本。
        """
        try:
            from core.assets import EXAMPLE_SENTENCE_BANK

            return EXAMPLE_SENTENCE_BANK if isinstance(EXAMPLE_SENTENCE_BANK, dict) else {}
        except ImportError as e:
            print(f"Error importing example bank: {e}")
            return {}

    def sample_bank(self, length: str, difficulty: int) -> list[str]:
        """
        根據指定的長度和難度，從例句庫中取樣。

        Args:
            length: 句子長度 ("short", "medium", "long")。
            difficulty: 難度等級 (1-5)。

        Returns:
            一個包含符合條件的例句的列表。
        """
        bank = self.load_bank_from_assets()
        return bank.get(length, {}).get(str(difficulty), [])


class KnowledgeAssets:
    """
    知識資源的統一門面。

    為應用程式的其他部分提供一個簡單的介面來查詢文法句型和例句，
    隱藏了底層的資料來源和載入邏輯。
    """

    def __init__(
        self,
        grammar_repo: GrammarRepository | None = None,
        example_repo: ExampleRepository | None = None,
    ):
        self.grammar_repo = grammar_repo or GrammarRepository()
        self.example_repo = example_repo or ExampleRepository()

    def get_grammar_patterns(self, category: str | None = None) -> list[GrammarPattern]:
        """
        獲取文法句型。

        Args:
            category: 可選的分類篩選條件。

        Returns:
            一個 `GrammarPattern` 物件的列表。
        """
        patterns = self.grammar_repo.load_all_grammar()
        if category:
            return [p for p in patterns if p.category == category]
        return patterns

    def get_example_bank(self, length: str, difficulty: int) -> list[str]:
        """
        獲取指定長度和難度的例句。

        Args:
            length: 句子長度。
            difficulty: 難度等級。

        Returns:
            一個例句字串的列表。
        """
        return self.example_repo.sample_bank(length=length, difficulty=difficulty)


# 導出主要的類別，方便其他模組使用
__all__ = [
    "GrammarPattern",
    "GrammarRepository",
    "ExampleRepository",
    "KnowledgeAssets",
]
