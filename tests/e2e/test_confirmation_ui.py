"""
端到端測試：知識點確認UI功能
測試批改後的確認/刪除交互流程
"""

import os
import pytest
from playwright.sync_api import Page, expect
from unittest.mock import patch

# 統一的測試URL配置
def get_test_url(path="/practice"):
    """獲取測試URL，消除localhost硬編碼"""
    test_host = os.getenv('TEST_HOST', 'localhost')
    test_port = os.getenv('TEST_PORT', '8000')
    return f"http://{test_host}:{test_port}{path}"


class TestConfirmationUI:
    """知識點確認UI測試套件"""

    @pytest.fixture
    def mock_grading_result(self):
        """模擬批改結果（包含待確認知識點）"""
        return {
            "success": True,
            "score": 65,
            "is_generally_correct": False,
            "feedback": "有一些錯誤需要改正",
            "error_analysis": [
                {
                    "category": "systematic",
                    "key_point_summary": "動詞時態錯誤",
                    "explanation": "應使用過去式",
                    "original_phrase": "I do it",
                    "correction": "I did it",
                }
            ],
            "pending_knowledge_points": [
                {
                    "id": "temp_001",
                    "error": {
                        "category": "systematic",
                        "key_point_summary": "動詞時態錯誤",
                        "explanation": "應使用過去式",
                        "original_phrase": "I do it",
                        "correction": "I did it",
                    },
                    "chinese_sentence": "我昨天做了這件事",
                    "user_answer": "I do it yesterday",
                }
            ],
            "auto_save": False,
        }

    def test_confirmation_buttons_appear(self, page: Page, mock_grading_result):
        """測試確認/刪除按鈕是否出現在批改結果中"""

        # 導航到練習頁面
        page.goto(get_test_url("/practice"))

        # 等待頁面加載
        page.wait_for_selector("#add-question-btn")

        # 新增題目
        page.click("#add-question-btn")

        # 等待題目生成
        page.wait_for_selector(".queue-item[data-status='ready']", timeout=10000)

        # 點擊題目開始作答
        page.click(".queue-item[data-status='ready']")

        # 輸入答案
        page.fill("#answer-input", "I do it yesterday")

        # 攔截批改API並返回模擬結果
        page.route(
            "**/api/grade-answer",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body=mock_grading_result
            ),
        )

        # 提交答案
        page.click("#submit-btn")

        # 等待批改結果顯示
        page.wait_for_selector(".pending-point", timeout=5000)

        # 檢查確認按鈕是否存在
        confirm_btn = page.locator(".btn-confirm-point").first
        expect(confirm_btn).to_be_visible()
        expect(confirm_btn).to_contain_text("加入知識庫")

        # 檢查忽略按鈕是否存在
        ignore_btn = page.locator(".btn-ignore-point").first
        expect(ignore_btn).to_be_visible()
        expect(ignore_btn).to_contain_text("忽略")

        # 檢查批量操作按鈕
        expect(page.locator(".btn-confirm-all")).to_be_visible()
        expect(page.locator(".btn-ignore-all")).to_be_visible()

    def test_single_point_confirmation(self, page: Page, mock_grading_result):
        """測試單個知識點的確認功能"""

        # 設置頁面（與上個測試類似的步驟）
        page.goto(get_test_url("/practice"))
        page.wait_for_selector("#add-question-btn")
        page.click("#add-question-btn")
        page.wait_for_selector(".queue-item[data-status='ready']")
        page.click(".queue-item[data-status='ready']")
        page.fill("#answer-input", "I do it yesterday")

        # 攔截批改API
        page.route(
            "**/api/grade-answer",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body=mock_grading_result
            ),
        )

        # 攔截確認API
        confirm_response = {"success": True, "confirmed_count": 1, "point_ids": [123]}
        page.route(
            "**/api/confirm-knowledge-points",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body=confirm_response
            ),
        )

        # 提交答案
        page.click("#submit-btn")
        page.wait_for_selector(".pending-point")

        # 點擊確認按鈕
        page.click(".btn-confirm-point")

        # 檢查視覺反饋
        confirmed_point = page.locator(".pending-point.confirmed").first
        expect(confirmed_point).to_be_visible()

        # 檢查成功通知
        notification = page.locator(".notification-success")
        expect(notification).to_contain_text("已加入知識庫")

    def test_single_point_ignore(self, page: Page, mock_grading_result):
        """測試單個知識點的忽略功能"""

        # 設置頁面
        page.goto(get_test_url("/practice"))
        page.wait_for_selector("#add-question-btn")
        page.click("#add-question-btn")
        page.wait_for_selector(".queue-item[data-status='ready']")
        page.click(".queue-item[data-status='ready']")
        page.fill("#answer-input", "I do it yesterday")

        page.route(
            "**/api/grade-answer",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body=mock_grading_result
            ),
        )

        page.click("#submit-btn")
        page.wait_for_selector(".pending-point")

        # 點擊忽略按鈕
        page.click(".btn-ignore-point")

        # 檢查視覺反饋
        ignored_point = page.locator(".pending-point.ignored").first
        expect(ignored_point).to_be_visible()

        # 檢查樣式變化（變灰、劃線等）
        expect(ignored_point).to_have_css("opacity", "0.5")

    def test_batch_confirm_all(self, page: Page):
        """測試批量確認所有知識點"""

        # 準備多個待確認點的結果
        multi_point_result = {
            "success": True,
            "score": 50,
            "pending_knowledge_points": [
                {
                    "id": f"temp_{i:03d}",
                    "error": {
                        "category": "systematic",
                        "key_point_summary": f"錯誤類型{i}",
                        "explanation": f"說明{i}",
                    },
                    "chinese_sentence": f"測試句子{i}",
                    "user_answer": f"Test {i}",
                }
                for i in range(3)
            ],
            "auto_save": False,
        }

        # 設置頁面
        page.goto(get_test_url("/practice"))
        page.wait_for_selector("#add-question-btn")
        page.click("#add-question-btn")
        page.wait_for_selector(".queue-item[data-status='ready']")
        page.click(".queue-item[data-status='ready']")
        page.fill("#answer-input", "Test answer")

        page.route(
            "**/api/grade-answer",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body=multi_point_result
            ),
        )

        page.route(
            "**/api/confirm-knowledge-points",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body={"success": True, "confirmed_count": 3, "point_ids": [100, 101, 102]},
            ),
        )

        page.click("#submit-btn")
        page.wait_for_selector(".pending-point")

        # 點擊全部確認
        page.click(".btn-confirm-all")

        # 檢查所有點都被標記為已確認
        confirmed_points = page.locator(".pending-point.confirmed")
        expect(confirmed_points).to_have_count(3)

        # 檢查通知
        notification = page.locator(".notification-success")
        expect(notification).to_contain_text("已加入 3 個知識點")

    def test_mixed_confirmation_and_ignore(self, page: Page):
        """測試混合確認和忽略操作"""

        # 準備多個待確認點
        multi_point_result = {
            "success": True,
            "score": 60,
            "pending_knowledge_points": [
                {"id": "temp_001", "error": {"key_point_summary": "錯誤1"}},
                {"id": "temp_002", "error": {"key_point_summary": "錯誤2"}},
                {"id": "temp_003", "error": {"key_point_summary": "錯誤3"}},
            ],
            "auto_save": False,
        }

        page.goto(get_test_url("/practice"))
        # ... 設置步驟 ...

        # 確認第一個，忽略第二個，確認第三個
        page.click(".pending-point:nth-child(1) .btn-confirm-point")
        page.wait_for_timeout(500)  # 等待動畫

        page.click(".pending-point:nth-child(2) .btn-ignore-point")
        page.wait_for_timeout(500)

        page.click(".pending-point:nth-child(3) .btn-confirm-point")

        # 檢查狀態
        expect(page.locator(".pending-point.confirmed")).to_have_count(2)
        expect(page.locator(".pending-point.ignored")).to_have_count(1)

    def test_confirmation_persists_in_session(self, page: Page):
        """測試確認狀態在會話中的持久性"""

        # 執行確認操作
        # ... 設置和確認步驟 ...

        # 切換到其他題目
        page.click("#next-btn")

        # 返回查看之前的題目
        page.click(".queue-item[data-status='completed']")

        # 檢查確認狀態是否保留
        expect(page.locator(".pending-point.confirmed")).to_be_visible()

    def test_auto_save_mode_no_confirmation_ui(self, page: Page):
        """測試自動保存模式下不顯示確認UI"""

        auto_save_result = {
            "success": True,
            "score": 70,
            "error_analysis": [{"key_point_summary": "錯誤"}],
            "auto_save": True,  # 標記為自動保存
        }

        page.goto(get_test_url("/practice"))
        # ... 設置步驟 ...

        page.route(
            "**/api/grade-answer",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body=auto_save_result
            ),
        )

        # 提交並檢查
        page.click("#submit-btn")

        # 不應該顯示確認按鈕
        expect(page.locator(".btn-confirm-point")).not_to_be_visible()
        expect(page.locator(".btn-ignore-point")).not_to_be_visible()
        expect(page.locator(".pending-point")).not_to_be_visible()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
