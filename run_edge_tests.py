#!/usr/bin/env python3
"""
邊界測試執行腳本

快速執行所有邊界情況測試，生成詳細報告
"""

import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.test_edge_cases.test_runner import run_edge_case_tests


async def main():
    """主執行函數"""
    print("🚀 開始執行 TASK-20B: 邊界情況完整測試覆蓋")
    print("=" * 60)
    
    try:
        success, report = await run_edge_case_tests()
        
        if success:
            print("\n🎉 TASK-20B 執行成功！")
            print("✅ 所有邊界測試套件通過")
            
            summary = report.get('summary', {})
            print(f"📊 測試總結:")
            print(f"   - 執行時間: {summary.get('total_duration', 0):.2f} 秒")
            print(f"   - 測試套件: {summary.get('passed_suites', 0)}/{summary.get('total_suites', 0)}")
            print(f"   - 總測試數: {summary.get('total_tests', 0)}")
            print(f"   - 成功率: {summary.get('success_rate', 0):.1f}%")
            
            # 性能分析
            if 'performance_analysis' in report:
                perf = report['performance_analysis']
                if perf.get('status') != 'no_data':
                    print(f"⚡ 性能評級: {perf.get('performance_grade', 'N/A')}")
            
            return 0
            
        else:
            print("\n❌ TASK-20B 執行失敗")
            if 'error' in report:
                print(f"錯誤: {report['error']}")
            return 1
            
    except Exception as e:
        print(f"\n💥 執行過程中出現異常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)