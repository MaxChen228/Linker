#!/usr/bin/env python3
"""
測試版本遷移系統
"""

import json
from pathlib import Path

from core.version_manager import VersionManager


def test_migration():
    """測試版本遷移功能"""

    print("=== 版本遷移測試 ===\n")

    manager = VersionManager()

    # 1. 顯示當前狀態
    print("1. 檢查當前版本狀態：")
    report = manager.get_version_report()
    for file_path, info in report["files"].items():
        print(f"   {Path(file_path).name}:")
        print(f"     - 版本: {info['version']}")
        print(f"     - 需要遷移: {info['needs_migration']}")

    # 2. 測試 grammar_patterns.json 遷移
    print("\n2. 測試 grammar_patterns.json 遷移：")
    patterns_file = Path("data/grammar_patterns.json")

    # 載入原始資料
    with open(patterns_file, encoding="utf-8") as f:
        original_data = json.load(f)

    print(f"   原始資料類型: {type(original_data)}")
    print(f"   原始資料長度: {len(original_data) if isinstance(original_data, list) else 'N/A'}")

    # 手動執行遷移鏈
    print("\n   執行遷移鏈：")

    # v1 -> v2
    v2_data = manager.migrate_patterns_v1_to_v2(original_data)
    print("   ✓ v1.0 -> v2.0: 添加版本標記和元數據")
    print(f"     - version: {v2_data.get('version')}")
    print(f"     - total_patterns: {v2_data.get('total_patterns')}")

    # v2 -> v3
    v3_data = manager.migrate_patterns_v2_to_v3(v2_data)
    print("   ✓ v2.0 -> v3.0: 添加 enrichment_summary")
    print(f"     - version: {v3_data.get('version')}")
    print(f"     - enrichment_summary: {bool(v3_data.get('enrichment_summary'))}")

    # v3 -> v3.1
    v3_1_data = manager.migrate_patterns_v3_to_v3_1(v3_data)
    print("   ✓ v3.0 -> v3.1: 標準化欄位")
    print(f"     - version: {v3_1_data.get('version')}")
    print(f"     - last_migration: {bool(v3_1_data.get('last_migration'))}")

    # 3. 驗證遷移結果
    print("\n3. 驗證遷移結果：")
    print(f"   最終版本: {v3_1_data.get('version')}")
    print(f"   句型數量: {len(v3_1_data.get('patterns', []))}")

    # 檢查第一個句型的結構
    if v3_1_data.get("patterns"):
        first_pattern = v3_1_data["patterns"][0]
        print("   第一個句型結構:")
        print(f"     - id: {first_pattern.get('id')}")
        print(f"     - category: {first_pattern.get('category')}")
        print(f"     - difficulty: {first_pattern.get('difficulty')}")
        print(f"     - examples 數量: {len(first_pattern.get('examples', []))}")

    # 4. 儲存測試結果
    test_output = Path("data/test_migration_result.json")
    with open(test_output, "w", encoding="utf-8") as f:
        json.dump(v3_1_data, f, ensure_ascii=False, indent=2)
    print(f"\n4. 測試結果已儲存到: {test_output}")

    return v3_1_data


def test_auto_migration():
    """測試自動遷移功能"""
    print("\n=== 自動遷移測試 ===\n")

    manager = VersionManager()

    # 執行自動遷移
    results = manager.check_and_migrate_all()

    print("遷移結果：")
    for file_path, result in results.items():
        status = "✅ 已遷移" if result else "⏭️ 已是最新" if result is False else "❌ 檔案不存在"
        print(f"  {Path(file_path).name}: {status}")

    # 再次檢查版本
    print("\n遷移後的版本狀態：")
    report = manager.get_version_report()
    for file_path, info in report["files"].items():
        print(f"  {Path(file_path).name}: v{info['version']} (需要遷移: {info['needs_migration']})")


if __name__ == "__main__":
    # 執行測試
    print("開始版本遷移測試...\n")

    # 測試手動遷移
    migrated_data = test_migration()

    # 測試自動遷移
    test_auto_migration()

    print("\n測試完成！")
