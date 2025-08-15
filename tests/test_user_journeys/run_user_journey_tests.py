"""
用戶操作路徑一致性測試執行器
整合所有用戶路徑測試，生成一致性報告
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List

import pytest

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class UserJourneyTestRunner:
    """用戶路徑測試執行器"""

    def __init__(self):
        self.test_results: List[Dict] = []
        self.start_time = None
        self.end_time = None

    async def run_all_tests(self) -> Dict:
        """執行所有用戶路徑測試"""
        print("🚀 開始執行用戶操作路徑一致性驗證...")
        self.start_time = time.time()

        # 定義測試模組
        test_modules = [
            "test_new_user_experience",
            "test_daily_practice_flow",
            "test_knowledge_management",
            "test_search_and_statistics"
        ]

        overall_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'execution_time': 0,
            'consistency_score': 0.0
        }

        for module in test_modules:
            print(f"\n📋 執行測試模組: {module}")
            module_result = await self._run_test_module(module)
            overall_results['test_details'].append(module_result)
            overall_results['total_tests'] += module_result['total']
            overall_results['passed_tests'] += module_result['passed']
            overall_results['failed_tests'] += module_result['failed']

        self.end_time = time.time()
        overall_results['execution_time'] = self.end_time - self.start_time

        # 計算一致性分數
        if overall_results['total_tests'] > 0:
            overall_results['consistency_score'] = overall_results['passed_tests'] / overall_results['total_tests']

        self._generate_report(overall_results)

        return overall_results

    async def _run_test_module(self, module_name: str) -> Dict:
        """執行單個測試模組"""
        module_result = {
            'module': module_name,
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': [],
            'execution_time': 0
        }

        start_time = time.time()

        try:
            # 使用 pytest 執行測試
            test_file = f"tests/test_user_journeys/{module_name}.py"

            # 執行 pytest 並捕獲結果
            result = pytest.main([
                test_file,
                "-v",
                "--tb=short",
                "-x"  # 遇到第一個失敗就停止
            ])

            # 簡化結果處理
            if result == 0:
                module_result['passed'] = 1
                module_result['total'] = 1
                print(f"✅ {module_name}: 通過")
            else:
                module_result['failed'] = 1
                module_result['total'] = 1
                module_result['errors'].append(f"模組 {module_name} 執行失敗")
                print(f"❌ {module_name}: 失敗")

        except Exception as e:
            module_result['failed'] = 1
            module_result['total'] = 1
            module_result['errors'].append(str(e))
            print(f"❌ {module_name}: 異常 - {e}")

        module_result['execution_time'] = time.time() - start_time
        return module_result

    def _generate_report(self, results: Dict) -> None:
        """生成測試報告"""
        print(f"\n{'='*60}")
        print("📊 用戶操作路徑一致性驗證報告")
        print(f"{'='*60}")

        print(f"⏱️  執行時間: {results['execution_time']:.2f} 秒")
        print(f"📈 測試總數: {results['total_tests']}")
        print(f"✅ 通過測試: {results['passed_tests']}")
        print(f"❌ 失敗測試: {results['failed_tests']}")
        print(f"🎯 一致性分數: {results['consistency_score']:.1%}")

        # 一致性評級
        if results['consistency_score'] >= 0.95:
            consistency_grade = "🏆 優秀"
        elif results['consistency_score'] >= 0.85:
            consistency_grade = "🥈 良好"
        elif results['consistency_score'] >= 0.70:
            consistency_grade = "🥉 及格"
        else:
            consistency_grade = "⚠️ 需改進"

        print(f"📋 一致性評級: {consistency_grade}")

        print(f"\n{'='*30} 詳細結果 {'='*30}")

        for detail in results['test_details']:
            status = "✅" if detail['failed'] == 0 else "❌"
            print(f"{status} {detail['module']}: {detail['passed']}/{detail['total']} 通過 ({detail['execution_time']:.2f}s)")

            if detail['errors']:
                for error in detail['errors']:
                    print(f"   ⚠️ {error}")

        print(f"\n{'='*60}")

        # 給出建議
        if results['consistency_score'] < 0.85:
            print("🔧 建議:")
            print("   - 檢查失敗的測試案例")
            print("   - 分析兩種模式間的差異原因")
            print("   - 優化統計計算邏輯的一致性")
            print("   - 檢查數據同步機制")
        else:
            print("🎉 系統一致性表現優秀！")
            print("   - 用戶體驗在兩種模式下高度一致")
            print("   - 可以安全地在兩種模式間切換")


async def main():
    """主執行函數"""
    runner = UserJourneyTestRunner()

    try:
        results = await runner.run_all_tests()

        # 返回適當的退出代碼
        if results['consistency_score'] >= 0.7:
            print("\n🎉 用戶操作路徑一致性驗證完成！")
            return 0
        else:
            print("\n⚠️ 一致性驗證發現問題，需要進一步改進")
            return 1

    except Exception as e:
        print(f"\n❌ 測試執行器發生錯誤: {e}")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
