#!/usr/bin/env python3
"""
Linker CLI - 智能英文學習工具
"""

import os
import sys
from pathlib import Path
from typing import Any, Optional

from core.ai_service import AIService
from core.display import display
from core.error_types import ErrorCategory, ErrorTypeSystem
from core.knowledge import KnowledgeManager
from core.log_config import get_module_logger
from settings import settings


class LinkerCLI:
    """終端學習應用主類"""

    def __init__(self):
        self.ai_service = AIService()
        self.knowledge = KnowledgeManager()
        self.type_system = ErrorTypeSystem()
        self.logger = get_module_logger(__name__)
        self.settings = settings

    def run(self):
        """主循環"""
        self.print_welcome()

        while True:
            try:
                self.show_menu()
                display.blank_line()
                choice = input(f"{display.colors.CYAN}請選擇功能 (輸入數字): {display.colors.RESET}").strip()

                if choice == "1":
                    self.practice_translation()
                elif choice == "2":
                    self.review_by_category()
                elif choice == "3":
                    self.view_knowledge_points()
                elif choice == "4":
                    self.show_detailed_statistics()
                elif choice == "5":
                    self.get_learning_recommendations()
                elif choice == "6":
                    display.blank_line()
                    display.success("👋 再見！繼續加油學習！")
                    break
                else:
                    display.error("無效選擇，請重新輸入")

            except KeyboardInterrupt:
                display.blank_line(2)
                display.warning("👋 程式中斷，再見！")
                break
            except Exception as e:
                display.error(f"發生錯誤: {e}")

    def print_welcome(self):
        """顯示歡迎訊息"""
        display.clear_screen()
        display.header(
            "🎯 Linker CLI - 智能英文學習系統",
            "採用全新四級錯誤分類系統"
        )
        display.info("⚙️  系統性錯誤 → 📌 單一性錯誤 → ✨ 可以更好 → ❓ 其他")
        print("=" * 60)


    def show_menu(self):
        """顯示主選單"""
        display.section("主選單", "📚")

        menu_items = [
            ("1", "開始翻譯練習", "GREEN"),
            ("2", "分類複習（按錯誤類型）", "YELLOW"),
            ("3", "查看所有知識點", "CYAN"),
            ("4", "詳細學習統計", "BLUE"),
            ("5", "獲取學習建議", "MAGENTA"),
            ("6", "退出程式", "RED")
        ]

        for num, text, color in menu_items:
            color_code = getattr(display.colors, color)
            display.list_item(f"{color_code}{num}.{display.colors.RESET} {text}")

    def practice_translation(self):
        """翻譯練習模式 - 主流程"""
        self.logger.info("開始翻譯練習")

        # 顯示標題
        self._display_practice_header()

        # 選擇難度
        level = self._select_difficulty_level()

        # 生成練習內容
        sentence_data = self._generate_practice_content(level)

        # 顯示題目
        self._display_practice_sentence(sentence_data)

        # 獲取用戶輸入
        user_answer = self._get_user_translation()
        if not user_answer:
            return

        # 批改並保存
        feedback = self._grade_and_save(
            sentence_data["sentence"], user_answer, sentence_data.get("hint")
        )

        # 顯示結果
        self.display_feedback(feedback)

    def _display_practice_header(self):
        """顯示練習模式標題"""
        print(f"\n{self.settings.display.SEPARATOR_LINE}")
        print("📝 翻譯練習模式")
        print(self.settings.display.SEPARATOR_LINE)

    def _select_difficulty_level(self) -> int:
        """選擇難度級別"""
        print("\n選擇難度:")
        for level, desc in self.settings.learning.DIFFICULTY_LEVELS.items():
            print(f"{level}. {desc}")

        user_input = input("請選擇 (1-3): ").strip()

        try:
            level = int(user_input)
            if level not in [1, 2, 3]:
                self.logger.warning(f"無效的難度選擇: {level}，使用默認值1")
                level = 1
        except (ValueError, TypeError) as e:
            self.logger.warning(f"難度輸入錯誤: {e}，使用默認值1")
            level = 1

        self.logger.info(f"選擇難度級別: {level}")
        return level

    def _generate_practice_content(self, level: int) -> dict[str, Any]:
        """生成練習內容"""
        print("\n🤖 生成練習題目...")
        sentence_data = self.ai_service.generate_practice_sentence(level)
        self.logger.info(f"生成練習句子: {sentence_data.get('sentence', 'N/A')[:50]}...")
        return sentence_data

    def _display_practice_sentence(self, sentence_data: dict[str, Any]):
        """顯示練習句子"""
        sentence = sentence_data["sentence"]
        hint = sentence_data.get("hint", "")

        display.blank_line()
        display.box(
            "📖 請翻譯以下句子",
            [sentence],
            color="CYAN"
        )

        if hint:
            display.blank_line()
            display.info(f"💡 提示: {hint}")

    def _get_user_translation(self) -> Optional[str]:
        """獲取用戶翻譯"""
        display.blank_line()
        user_answer = input(f"{display.colors.YELLOW}✍️  你的翻譯: {display.colors.RESET}").strip()

        if not user_answer:
            display.error("未輸入答案")
            self.logger.warning("用戶未輸入翻譯")
            return None

        self.logger.info(f"用戶輸入: {user_answer[:50]}...")
        return user_answer

    def _grade_and_save(
        self, chinese_sentence: str, user_answer: str, hint: Optional[str] = None
    ) -> dict[str, Any]:
        """批改翻譯並保存結果"""
        display.blank_line()
        display.info("🤖 AI 批改中...")

        # AI批改
        feedback = self.ai_service.grade_translation(chinese_sentence, user_answer, hint)

        # 保存錯誤記錄
        if not feedback.get("is_generally_correct", False):
            self.knowledge.save_mistake(chinese_sentence, user_answer, feedback)
            display.success("💾 錯誤已分類並記錄到知識庫")
            self.logger.info("錯誤已記錄到知識庫")
        else:
            self.logger.info("翻譯正確")

        return feedback

    def display_feedback(self, feedback: dict[str, Any]):
        """顯示批改結果 - 主函數"""
        display.separator("thick")

        # 顯示總體結果
        self._display_overall_result(feedback)

        # 顯示建議翻譯
        self._display_suggested_translation(feedback)

        # 顯示錯誤分析（精簡版）
        errors = feedback.get("error_analysis", [])
        if errors:
            self._display_error_analysis(errors)

    def _display_overall_result(self, feedback: dict[str, Any]):
        """顯示總體結果"""
        is_correct = feedback.get("is_generally_correct", False)

        display.blank_line()
        if is_correct:
            display.success("✅ 翻譯正確！做得很好！")
        else:
            display.warning("📝 發現一些需要改進的地方")

    def _display_suggested_translation(self, feedback: dict[str, Any]):
        """顯示建議翻譯"""
        if "overall_suggestion" in feedback:
            display.blank_line()
            display.section("參考翻譯", "💡")
            display.box(
                "參考答案",
                [feedback['overall_suggestion']],
                color="GREEN"
            )

    def _display_error_analysis(self, errors: list):
        """顯示錯誤分析（精簡版）"""
        display.blank_line()
        display.section(f"錯誤分析 ({len(errors)} 個)", "📊")

        # 分組錯誤
        error_groups = self._group_errors_by_nature(errors)

        # 統計各類錯誤數量
        stats = []
        for nature, group_errors in error_groups.items():
            if group_errors:
                category = self._parse_error_category(nature)
                emoji = self._get_category_emoji(category)
                stats.append([emoji, nature, str(len(group_errors))])

        if stats:
            display.table(
                ["類型", "分類", "數量"],
                stats,
                colors=["YELLOW", "WHITE", "RED"]
            )

        # 顯示每組錯誤（折疊顯示）
        for nature, group_errors in error_groups.items():
            if group_errors:
                self._display_error_group_compact(nature, group_errors)

    def _group_errors_by_nature(self, errors: list) -> dict[str, list]:
        """按錯誤性質分組"""
        error_groups = {"系統性錯誤": [], "單一性錯誤": [], "可以更好": [], "其他錯誤": []}

        for error in errors:
            nature = error.get("error_nature", "其他錯誤")
            if nature in error_groups:
                error_groups[nature].append(error)

        return error_groups

    def _display_error_group(self, nature: str, errors: list):
        """顯示一組錯誤"""
        # 轉換為枚舉類型
        category = self._parse_error_category(nature)
        emoji = self._get_category_emoji(category)

        print(f"\n{emoji} {nature} ({len(errors)} 個):")

        for i, error in enumerate(errors, 1):
            self._display_single_error(i, error)

    def _display_single_error(self, index: int, error: dict[str, Any]):
        """顯示單個錯誤"""
        severity = error.get("severity", "major")
        severity_mark = "⚠️" if severity == "major" else "💭"

        print(f"\n  {index}. {severity_mark} {error.get('key_point_summary', '錯誤點')}")
        print(f"     錯誤: {error.get('original_phrase', 'N/A')}")
        print(f"     正確: {error.get('correction', 'N/A')}")
        print(f"     說明: {error.get('explanation', 'N/A')}")

    def _display_error_group_compact(self, nature: str, errors: list):
        """顯示一組錯誤（精簡版）"""
        category = self._parse_error_category(nature)
        emoji = self._get_category_emoji(category)

        display.blank_line()
        # 只顯示標題，詳細內容折疊
        content_lines = []
        for i, error in enumerate(errors, 1):
            severity = error.get("severity", "major")
            severity_mark = "!" if severity == "major" else "?"
            content_lines.append(f"{i}. [{severity_mark}] {error.get('key_point_summary', '錯誤點')}")
            content_lines.append(f"   錯誤: {error.get('original_phrase', 'N/A')}")
            content_lines.append(f"   正確: {error.get('correction', 'N/A')}")
            content_lines.append(f"   說明: {error.get('explanation', 'N/A')}")
            content_lines.append("")

        # 使用折疊顯示
        display.collapsible(
            f"{emoji} {nature} ({len(errors)} 個)",
            "\n".join(content_lines),
            expanded=False  # 預設折疊
        )

    def _parse_error_category(self, nature: str) -> ErrorCategory:
        """解析錯誤類別字串為枚舉"""
        mapping = {
            "系統性": "systematic",
            "單一性": "isolated",
            "可以更好": "enhancement",
            "其他": "other",
        }

        for chinese, english in mapping.items():
            if chinese in nature:
                return ErrorCategory.from_string(english)

        return ErrorCategory.OTHER

    def _get_category_emoji(self, category: ErrorCategory) -> str:
        """獲取類別對應的表情符號"""
        emojis = {
            ErrorCategory.SYSTEMATIC: "⚙️",
            ErrorCategory.ISOLATED: "📌",
            ErrorCategory.ENHANCEMENT: "✨",
            ErrorCategory.OTHER: "❓",
        }
        return emojis.get(category, "•")

    def review_by_category(self):
        """按類別複習"""
        print("\n" + "-" * 50)
        print("🔄 分類複習模式")
        print("-" * 50)

        print("\n選擇要複習的錯誤類型:")
        print("1. ⚙️  系統性錯誤（文法規則類）")
        print("2. 📌 單一性錯誤（需個別記憶）")
        print("3. ✨ 可以更好（語言優化）")
        print("4. ❓ 其他錯誤")
        print("5. 📅 今日待複習（所有類型）")

        choice = input("\n請選擇 (1-5): ").strip()

        if choice == "1":
            category = ErrorCategory.SYSTEMATIC
        elif choice == "2":
            category = ErrorCategory.ISOLATED
        elif choice == "3":
            category = ErrorCategory.ENHANCEMENT
        elif choice == "4":
            category = ErrorCategory.OTHER
        elif choice == "5":
            points = self.knowledge.get_due_points()
            self._display_points(points, "今日待複習")
            return
        else:
            print("❌ 無效選擇")
            return

        points = self.knowledge.get_points_by_category(category)
        self._display_points(points, category.to_chinese())

    def _display_points(self, points: list, title: str):
        """顯示知識點列表"""
        if not points:
            print(f"\n✨ {title}中沒有知識點")
            return

        print(f"\n📚 {title} ({len(points)} 個):")

        for i, point in enumerate(points[:10], 1):  # 最多顯示10個
            print(f"\n{i}. {point.key_point}")

            # 獲取子類型資訊
            subtype_obj = self.type_system.get_subtype_by_name(point.subtype)
            if subtype_obj:
                print(f"   子類型: {subtype_obj.chinese_name}")

            print(
                f"   掌握度: {'█' * int(point.mastery_level * 10)}{'░' * (10 - int(point.mastery_level * 10))} {point.mastery_level:.0%}"
            )
            print(f"   錯誤/正確: {point.mistake_count}/{point.correct_count}")
            print(f"   下次複習: {point.next_review[:10]}")

            if point.examples:
                print(f"   例句: {point.examples[0]['chinese'][:30]}...")

        if len(points) > 10:
            print(f"\n... 還有 {len(points) - 10} 個知識點")

        input("\n按 Enter 繼續...")

    def view_knowledge_points(self):
        """查看所有知識點"""
        print("\n" + "-" * 50)
        print("📊 知識點總覽")
        print("-" * 50)

        stats = self.knowledge.get_statistics()

        print(f"\n總知識點數: {stats['knowledge_points']}")
        print(f"平均掌握度: {stats['avg_mastery']:.1%}")
        print(f"待複習: {stats['due_reviews']} 個")

        # 顯示分類分佈
        if stats["category_distribution"]:
            print("\n📈 錯誤類型分佈:")
            for category_name, count in stats["category_distribution"].items():
                print(f"  • {category_name}: {count} 個")

        # 顯示子類型分佈
        if stats["subtype_distribution"]:
            print("\n📊 具體問題分佈 (前5名):")
            sorted_subtypes = sorted(
                stats["subtype_distribution"].items(), key=lambda x: x[1], reverse=True
            )[:5]
            for subtype_name, count in sorted_subtypes:
                subtype_obj = self.type_system.get_subtype_by_name(subtype_name)
                if subtype_obj:
                    print(f"  • {subtype_obj.chinese_name}: {count} 個")

        input("\n按 Enter 繼續...")

    def show_detailed_statistics(self):
        """顯示詳細統計"""
        print("\n" + "-" * 50)
        print("📈 詳細學習統計")
        print("-" * 50)

        stats = self.knowledge.get_statistics()

        # 基礎統計
        print("\n📊 練習統計:")
        print(f"  總練習次數: {stats['total_practices']}")
        print(f"  正確次數: {stats['correct_count']}")
        print(f"  錯誤次數: {stats['mistake_count']}")
        print(f"  正確率: {stats['accuracy']:.1%}")

        # 知識點統計
        print("\n📚 知識點統計:")
        print(f"  總數量: {stats['knowledge_points']}")
        print(f"  平均掌握度: {stats['avg_mastery']:.1%}")
        print(f"  待複習: {stats['due_reviews']}")

        # 進度視覺化
        if stats["knowledge_points"] > 0:
            mastery_levels = {
                "已掌握 (>90%)": 0,
                "熟練 (70-90%)": 0,
                "進步中 (30-70%)": 0,
                "需加強 (<30%)": 0,
            }

            for point in self.knowledge.knowledge_points:
                if point.mastery_level >= 0.9:
                    mastery_levels["已掌握 (>90%)"] += 1
                elif point.mastery_level >= 0.7:
                    mastery_levels["熟練 (70-90%)"] += 1
                elif point.mastery_level >= 0.3:
                    mastery_levels["進步中 (30-70%)"] += 1
                else:
                    mastery_levels["需加強 (<30%)"] += 1

            print("\n📈 掌握度分佈:")
            for level, count in mastery_levels.items():
                percentage = count / stats["knowledge_points"] * 100
                bar = "█" * int(percentage / 5) + "░" * (20 - int(percentage / 5))
                print(f"  {level}: {bar} {count} ({percentage:.1f}%)")

        input("\n按 Enter 繼續...")

    def get_learning_recommendations(self):
        """獲取學習建議"""
        print("\n" + "-" * 50)
        print("💡 個性化學習建議")
        print("-" * 50)

        recommendations = self.knowledge.get_learning_recommendations()

        if not recommendations:
            print("\n📚 還沒有足夠的學習數據，繼續練習吧！")
            input("\n按 Enter 繼續...")
            return

        print("\n根據你的學習數據，以下是優先建議：")

        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {1: "🔥", 2: "⭐", 3: "💫", 4: "☆"}
            emoji = priority_emoji.get(rec["priority"], "•")

            print(f"\n{emoji} 優先級 {rec['priority']}: {rec['category']}")
            print(f"   問題數量: {rec['point_count']} 個")
            print(f"   平均掌握度: {rec['avg_mastery']:.1%}")
            print(f"   重點領域: {rec['focus_area']}")
            print(f"   📝 建議: {rec['advice']}")

        # AI 分析（如果有足夠的練習歷史）
        if len(self.knowledge.practice_history) >= 5:
            print("\n\n🤖 AI 學習分析中...")
            analysis = self.ai_service.analyze_common_mistakes(self.knowledge.practice_history)

            if analysis.get("overall_assessment"):
                print("\n💬 整體評估:")
                print(f"   {analysis['overall_assessment']}")

        input("\n按 Enter 繼續...")


def main():
    """主程式入口"""
    # 檢查 API KEY
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ 請設定 GEMINI_API_KEY 環境變數")
        print("   export GEMINI_API_KEY=your_api_key")
        sys.exit(1)

    # 創建資料目錄
    Path("data").mkdir(exist_ok=True)

    # 啟動應用
    app = LinkerCLI()
    app.run()


if __name__ == "__main__":
    main()
