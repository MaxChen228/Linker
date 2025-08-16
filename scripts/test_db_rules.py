#!/usr/bin/env python3
"""
測試資料庫約束的完整性和功能
測試所有添加的約束是否正常工作
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2 import errors

# 載入環境變數
load_dotenv()


class ConstraintTester:
    """資料庫約束測試器"""

    def __init__(self):
        """初始化測試器"""
        self.connection = None
        self.cursor = None
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []

    def connect(self) -> bool:
        """連接到資料庫"""
        try:
            # 從環境變數獲取連接參數，使用 DATABASE_URL 或分別設定參數
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                # 解析 DATABASE_URL
                import urllib.parse

                parsed = urllib.parse.urlparse(database_url)
                db_params = {
                    "host": parsed.hostname,
                    "port": parsed.port,
                    "database": parsed.path[1:],  # 移除開頭的 /
                    "user": parsed.username,
                    "password": parsed.password,
                }
            else:
                # 使用個別環境變數
                db_params = {
                    "host": os.getenv("DB_HOST", "localhost"),
                    "port": os.getenv("DB_PORT", 5432),
                    "database": os.getenv("DB_NAME", "linker"),
                    "user": os.getenv("DB_USER", "linker_user"),
                    "password": os.getenv("DB_PASSWORD", ""),
                }

            self.connection = psycopg2.connect(**db_params)
            self.cursor = self.connection.cursor()
            print("✅ 成功連接到資料庫")
            return True
        except Exception as e:
            print(f"❌ 無法連接到資料庫: {e}")
            return False

    def disconnect(self):
        """斷開資料庫連接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def test_constraint(self, test_name: str, sql_query: str, should_fail: bool = True) -> bool:
        """
        測試單個約束

        Args:
            test_name: 測試名稱
            sql_query: 要執行的 SQL
            should_fail: 是否應該失敗（測試約束）
        """
        try:
            self.cursor.execute(sql_query)
            self.connection.commit()

            if should_fail:
                # 應該失敗但成功了
                self.failed_tests += 1
                self.test_results.append(f"❌ {test_name}: 約束未生效（應該失敗但成功了）")
                return False
            else:
                # 應該成功且成功了
                self.passed_tests += 1
                self.test_results.append(f"✅ {test_name}: 通過")
                return True

        except (errors.CheckViolation, errors.UniqueViolation, errors.ForeignKeyViolation) as e:
            self.connection.rollback()

            if should_fail:
                # 應該失敗且失敗了
                self.passed_tests += 1
                self.test_results.append(f"✅ {test_name}: 正確阻止了無效數據")
                return True
            else:
                # 應該成功但失敗了
                self.failed_tests += 1
                self.test_results.append(f"❌ {test_name}: 約束過於嚴格 - {str(e)[:50]}")
                return False
        except Exception as e:
            self.connection.rollback()
            self.failed_tests += 1
            self.test_results.append(f"❌ {test_name}: 發生錯誤 - {str(e)[:50]}")
            return False

    def setup_test_data(self):
        """設置測試數據"""
        try:
            # 創建測試知識點（不需要 users 表）
            self.cursor.execute("""
                INSERT INTO knowledge_points (
                    id, key_point, original_phrase, correction,
                    category, subtype, explanation, mastery_level, created_at
                )
                VALUES (
                    99999, 'Test Point', 'Test Phrase', 'Test Correction',
                    'systematic', 'grammar', 'Test explanation', 0.5, NOW()
                )
                ON CONFLICT (id) DO NOTHING
            """)

            self.connection.commit()
            print("✅ 測試數據準備完成\n")
        except Exception as e:
            self.connection.rollback()
            print(f"⚠️ 設置測試數據時發生錯誤: {e}\n")

    def cleanup_test_data(self):
        """清理測試數據"""
        try:
            self.cursor.execute("DELETE FROM knowledge_points WHERE id >= 99999")
            self.connection.commit()
        except Exception:
            self.connection.rollback()

    def test_check_constraints(self):
        """測試檢查約束"""
        print("=" * 60)
        print("📋 測試檢查約束 (CHECK Constraints)")
        print("=" * 60)

        # 測試 category 約束
        self.test_constraint(
            "無效 category 值",
            """INSERT INTO knowledge_points (key_point, category, subtype, explanation, original_phrase, correction)
               VALUES ('Test', 'invalid_category', 'grammar', 'test', 'test phrase', 'correction')""",
            should_fail=True,
        )

        self.test_constraint(
            "有效 category 值",
            """INSERT INTO knowledge_points (key_point, category, subtype, explanation, original_phrase, correction, created_at)
               VALUES ('Test Valid', 'systematic', 'grammar', 'test explanation', 'test phrase', 'correction', NOW())""",
            should_fail=False,
        )

        # 測試時間邏輯約束
        self.test_constraint(
            "無效時間邏輯 (next_review < last_seen)",
            """INSERT INTO knowledge_points (key_point, category, subtype, explanation, original_phrase, correction, last_seen, next_review)
               VALUES ('Time Test', 'systematic', 'grammar', 'test', 'test phrase', 'correction', '2025-01-15', '2025-01-10')""",
            should_fail=True,
        )

        # 測試掌握度與計數邏輯
        self.test_constraint(
            "計數邏輯不一致",
            """INSERT INTO knowledge_points (key_point, category, subtype, explanation, original_phrase, correction, mistake_count, correct_count, mastery_level)
               VALUES ('Count Test', 'systematic', 'grammar', 'test', 'test phrase', 'correction', 0, 0, 0.8)""",
            should_fail=True,
        )

        # 測試顏色格式約束
        self.test_constraint(
            "無效 HEX 顏色格式",
            """INSERT INTO tags (name, color)
               VALUES ('Bad Color', 'red')""",
            should_fail=True,
        )

        self.test_constraint(
            "有效 HEX 顏色格式",
            """INSERT INTO tags (name, color, created_at)
               VALUES ('Good Color Test', '#FF5733', NOW())""",
            should_fail=False,
        )

        # 測試 study_sessions mode 約束
        self.test_constraint(
            "無效 mode 值",
            """INSERT INTO study_sessions (mode, started_at)
               VALUES ('invalid_mode', NOW())""",
            should_fail=True,
        )

        print()

    def test_unique_constraints(self):
        """測試唯一約束"""
        print("=" * 60)
        print("🔑 測試唯一約束 (UNIQUE Constraints)")
        print("=" * 60)

        # 先插入一條記錄
        self.cursor.execute("""
            INSERT INTO knowledge_points (id, key_point, original_phrase, correction, category, subtype, explanation, created_at)
            VALUES (99998, 'Unique Test', 'Unique Phrase', 'Unique Correction', 'systematic', 'grammar', 'test explanation', NOW())
            ON CONFLICT DO NOTHING
        """)
        self.connection.commit()

        # 測試重複內容
        self.test_constraint(
            "重複知識點內容",
            """INSERT INTO knowledge_points (key_point, original_phrase, correction, category, subtype, explanation, created_at)
               VALUES ('Unique Test', 'Unique Phrase', 'Unique Correction', 'isolated', 'grammar', 'test explanation', NOW())""",
            should_fail=True,
        )

        # 測試部分不同的內容（應該允許）
        self.test_constraint(
            "部分不同的知識點",
            """INSERT INTO knowledge_points (key_point, original_phrase, correction, category, subtype, explanation, created_at)
               VALUES ('Unique Test', 'Different Phrase', 'Unique Correction', 'systematic', 'grammar', 'test explanation', NOW())""",
            should_fail=False,
        )

        print()

    def test_foreign_key_constraints(self):
        """測試外鍵約束"""
        print("=" * 60)
        print("🔗 測試外鍵約束 (FOREIGN KEY Constraints)")
        print("=" * 60)

        # 測試外鍵約束：original_errors 引用不存在的 knowledge_point_id
        self.test_constraint(
            "引用不存在的知識點",
            """INSERT INTO original_errors (knowledge_point_id, chinese_sentence, user_answer, correct_answer, timestamp)
               VALUES (88888, 'test sentence', 'user answer', 'correct answer', NOW())""",
            should_fail=True,
        )

        # 測試級聯刪除
        try:
            # 創建測試數據
            self.cursor.execute("""
                INSERT INTO knowledge_points (id, key_point, original_phrase, correction, category, subtype, explanation, created_at)
                VALUES (99997, 'Cascade Test', 'test', 'test', 'systematic', 'grammar', 'test explanation', NOW())
            """)

            self.cursor.execute("""
                INSERT INTO original_errors (knowledge_point_id, chinese_sentence, user_answer, correct_answer, timestamp)
                VALUES (99997, 'Test Chinese', 'Test User Answer', 'Test Correct Answer', NOW())
            """)

            # 刪除父記錄
            self.cursor.execute("DELETE FROM knowledge_points WHERE id = 99997")

            # 檢查子記錄是否被刪除
            self.cursor.execute("""
                SELECT COUNT(*) FROM original_errors
                WHERE knowledge_point_id = 99997
            """)
            count = self.cursor.fetchone()[0]

            if count == 0:
                self.passed_tests += 1
                self.test_results.append("✅ 級聯刪除: 正常工作")
            else:
                self.failed_tests += 1
                self.test_results.append("❌ 級聯刪除: 子記錄未被刪除")

            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.failed_tests += 1
            self.test_results.append(f"❌ 級聯刪除測試失敗: {str(e)[:50]}")

        print()

    def test_performance_indexes(self):
        """測試性能索引"""
        print("=" * 60)
        print("⚡ 測試性能索引 (Performance Indexes)")
        print("=" * 60)

        try:
            # 檢查索引是否存在
            self.cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'knowledge_points'
                AND indexname LIKE 'idx_kp_%'
            """)

            indexes = [row[0] for row in self.cursor.fetchall()]

            expected_indexes = ["idx_kp_category_mastery", "idx_kp_next_review", "idx_kp_search"]

            for idx in expected_indexes:
                if idx in indexes:
                    self.passed_tests += 1
                    self.test_results.append(f"✅ 索引 {idx}: 存在")
                else:
                    self.failed_tests += 1
                    self.test_results.append(f"❌ 索引 {idx}: 不存在")

            # 測試索引效能（使用 EXPLAIN）
            self.cursor.execute("""
                EXPLAIN (FORMAT JSON, ANALYZE FALSE)
                SELECT * FROM knowledge_points
                WHERE category = 'systematic'
                AND mastery_level < 0.5
                AND is_deleted = FALSE
            """)

            plan = self.cursor.fetchone()[0]
            if "Index Scan" in str(plan) or "Bitmap Index Scan" in str(plan):
                self.passed_tests += 1
                self.test_results.append("✅ 查詢優化: 使用索引")
            else:
                self.test_results.append("⚠️ 查詢優化: 未使用索引（可能數據量太少）")

        except Exception as e:
            self.failed_tests += 1
            self.test_results.append(f"❌ 索引測試失敗: {str(e)[:50]}")

        print()

    def print_summary(self):
        """打印測試總結"""
        print("=" * 60)
        print("📊 測試結果總結")
        print("=" * 60)

        for result in self.test_results:
            print(f"  {result}")

        print("\n" + "=" * 60)
        total = self.passed_tests + self.failed_tests
        if total > 0:
            pass_rate = (self.passed_tests / total) * 100
            print(f"✅ 通過: {self.passed_tests}/{total} ({pass_rate:.1f}%)")
            print(f"❌ 失敗: {self.failed_tests}/{total}")

            if self.failed_tests == 0:
                print("\n🎉 所有約束測試通過！")
            else:
                print("\n⚠️ 部分測試失敗，請檢查約束實現")
        else:
            print("⚠️ 沒有執行任何測試")

        print("=" * 60)

    def run_all_tests(self):
        """執行所有測試"""
        if not self.connect():
            print("❌ 無法連接到資料庫，測試中止")
            return False

        print("\n🚀 開始執行資料庫約束測試")
        print("=" * 60)

        try:
            # 準備測試數據
            self.setup_test_data()

            # 執行各類測試
            self.test_check_constraints()
            self.test_unique_constraints()
            self.test_foreign_key_constraints()
            self.test_performance_indexes()

            # 清理測試數據
            self.cleanup_test_data()

            # 打印總結
            self.print_summary()

            return self.failed_tests == 0

        except Exception as e:
            print(f"\n❌ 測試過程中發生錯誤: {e}")
            return False
        finally:
            self.disconnect()


def main():
    """主程序"""
    # 檢查環境變數
    if os.getenv("USE_DATABASE", "false").lower() != "true":
        print("⚠️ 警告：當前未啟用資料庫模式 (USE_DATABASE != true)")
        print("建議先設置環境變數：export USE_DATABASE=true")
        response = input("\n是否繼續測試？(y/N): ")
        if response.lower() != "y":
            print("測試已取消")
            return

    # 執行測試
    tester = ConstraintTester()
    success = tester.run_all_tests()

    # 返回狀態碼
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
