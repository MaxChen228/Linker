#!/usr/bin/env python3
"""
一致性測試執行腳本
運行完整的 JSON/Database 模式一致性測試套件
"""

import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path


def run_consistency_tests(test_type: str = "all", verbose: bool = False, coverage: bool = True):
    """運行一致性測試套件

    Args:
        test_type: 測試類型 ("all", "statistics", "functional", "quick")
        verbose: 是否詳細輸出
        coverage: 是否生成覆蓋率報告
    """
    print(f"🧪 開始運行一致性測試 - {datetime.now()}")
    print(f"📋 測試類型: {test_type}")
    print("=" * 60)

    # 構建 pytest 命令
    cmd = ["python3", "-m", "pytest"]

    # 選擇測試範圍
    if test_type == "all":
        cmd.append("tests/test_consistency/")
    elif test_type == "statistics":
        cmd.append("tests/test_consistency/test_statistics_consistency.py")
    elif test_type == "functional":
        cmd.append("tests/test_consistency/test_functional_consistency.py")
    elif test_type == "quick":
        cmd.extend(
            [
                "tests/test_consistency/test_statistics_consistency.py::TestStatisticsConsistency::test_knowledge_points_count_basic",
                "tests/test_consistency/test_statistics_consistency.py::TestStatisticsConsistency::test_statistics_format_consistency",
            ]
        )
    else:
        print(f"❌ 未知的測試類型: {test_type}")
        return False

    # 添加基本參數
    if verbose:
        cmd.extend(["-v", "-s"])
    else:
        cmd.extend(["-q"])

    # 測試輸出格式
    cmd.extend(
        [
            "--tb=short",
            "--durations=10",  # 顯示最慢的10個測試
            "--strict-markers",  # 嚴格檢查標記
        ]
    )

    # 覆蓋率設置
    if coverage:
        cmd.extend(
            [
                "--cov=core",
                "--cov=tests/test_consistency",
                "--cov-report=term-missing",
                "--cov-report=html:consistency_test_coverage",
                "--cov-fail-under=85",  # 要求85%以上覆蓋率
            ]
        )

    # 輸出格式
    cmd.extend(["--junit-xml=consistency_test_results.xml", "--color=yes"])

    print(f"🚀 執行命令: {' '.join(cmd)}")
    print()

    try:
        # 運行測試
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=600)

        print()
        print("=" * 60)

        if result.returncode == 0:
            print("✅ 所有一致性測試通過！")
            print("📊 覆蓋率報告已生成在 consistency_test_coverage/ 目錄")
            print("📋 測試結果已保存到 consistency_test_results.xml")
            return True
        else:
            print("❌ 一致性測試失敗")
            print(f"💬 退出代碼: {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ 測試執行超時（10分鐘）")
        return False
    except Exception as e:
        print(f"💥 執行測試時發生錯誤: {e}")
        return False


def run_test_validation():
    """運行測試驗證，確保測試套件本身正確"""
    print("🔍 驗證測試套件完整性...")

    # 檢查測試文件存在性
    test_dir = Path("tests/test_consistency")
    required_files = [
        "__init__.py",
        "conftest.py",
        "test_statistics_consistency.py",
        "test_functional_consistency.py",
        "data_generators.py",
    ]

    missing_files = []
    for file in required_files:
        if not (test_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"❌ 缺少測試文件: {missing_files}")
        return False

    # 檢查測試語法
    cmd = ["python3", "-m", "pytest", "tests/test_consistency/", "--collect-only", "-q"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        # 解析收集到的測試數量
        lines = result.stdout.strip().split("\n")
        test_count = 0
        for line in lines:
            if "collected" in line and "items" in line:
                # 查找類似 "collected 25 items" 的行
                words = line.split()
                for i, word in enumerate(words):
                    if word == "collected" and i + 1 < len(words):
                        try:
                            test_count = int(words[i + 1])
                            break
                        except ValueError:
                            continue

        print(f"✅ 測試套件驗證通過，發現 {test_count} 個測試")
        return True
    else:
        print(f"❌ 測試語法錯誤:")
        print(result.stderr)
        return False


def generate_test_report():
    """生成測試報告摘要"""
    print("\n📊 生成測試報告摘要...")

    # 檢查結果文件
    result_file = Path("consistency_test_results.xml")
    coverage_dir = Path("consistency_test_coverage")

    if result_file.exists():
        print(f"✅ 測試結果文件: {result_file}")
    else:
        print("❌ 未找到測試結果文件")

    if coverage_dir.exists():
        print(f"✅ 覆蓋率報告: {coverage_dir}/index.html")
    else:
        print("❌ 未找到覆蓋率報告")

    print("\n🎯 測試套件包含的測試類型:")
    print("  📈 統計數據一致性測試 (test_statistics_consistency.py)")
    print("    - 知識點數量一致性")
    print("    - 統計格式一致性")
    print("    - 異步/同步方法一致性")
    print("    - 分類順序一致性")
    print("    - 掌握度計算準確性")
    print()
    print("  🔧 功能行為一致性測試 (test_functional_consistency.py)")
    print("    - CRUD 操作一致性")
    print("    - 搜索功能一致性")
    print("    - 複習候選選擇一致性")
    print("    - 分類過濾一致性")
    print("    - 性能基準測試")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="運行 JSON/Database 模式一致性測試套件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
測試類型:
  all         - 運行所有一致性測試（默認）
  statistics  - 只運行統計一致性測試
  functional  - 只運行功能一致性測試  
  quick       - 運行快速驗證測試

示例:
  python scripts/run_consistency_tests.py
  python scripts/run_consistency_tests.py --type statistics --verbose
  python scripts/run_consistency_tests.py --type quick --no-coverage
        """,
    )

    parser.add_argument(
        "--type",
        "-t",
        choices=["all", "statistics", "functional", "quick"],
        default="all",
        help="測試類型 (默認: all)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")

    parser.add_argument("--no-coverage", action="store_true", help="不生成覆蓋率報告")

    parser.add_argument("--validate-only", action="store_true", help="只驗證測試套件，不運行測試")

    args = parser.parse_args()

    # 確保在正確的目錄中
    if not Path("tests/test_consistency").exists():
        print("❌ 錯誤：請在專案根目錄中運行此腳本")
        print(f"💡 當前目錄：{Path.cwd()}")
        sys.exit(1)

    # 驗證測試套件
    if not run_test_validation():
        print("❌ 測試套件驗證失敗")
        sys.exit(1)

    if args.validate_only:
        print("✅ 測試套件驗證完成")
        generate_test_report()
        sys.exit(0)

    # 運行測試
    success = run_consistency_tests(
        test_type=args.type, verbose=args.verbose, coverage=not args.no_coverage
    )

    # 生成報告
    generate_test_report()

    if success:
        print("\n🎉 一致性測試執行完成！")
        sys.exit(0)
    else:
        print("\n💥 一致性測試執行失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
