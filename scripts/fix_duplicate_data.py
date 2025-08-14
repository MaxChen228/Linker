#!/usr/bin/env python3
"""
修復 knowledge.json 中的重複數據問題
- 修復重複的 ID
- 移除完全相同的知識點
- 保留最早創建的版本
"""

import json
import os
import shutil
import sys
from datetime import datetime
from typing import Any


def load_knowledge_data(file_path: str) -> dict[str, Any]:
    """載入知識點數據"""
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        sys.exit(1)

    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


def save_knowledge_data(data: dict[str, Any], file_path: str) -> None:
    """保存知識點數據"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def backup_file(file_path: str) -> str:
    """備份原始檔案"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ 已備份至: {backup_path}")
    return backup_path


def fix_duplicate_ids(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """修復重複的 ID"""
    seen_ids = set()
    max_id = 0
    fixed_points = []

    for point in points:
        current_id = point.get('id', 0)

        # 追蹤最大 ID
        if current_id > max_id:
            max_id = current_id

        # 如果 ID 重複，分配新 ID
        if current_id in seen_ids:
            max_id += 1
            point['id'] = max_id
            print(f"  修復重複 ID: {current_id} → {max_id}")

        seen_ids.add(point['id'])
        fixed_points.append(point)

    return fixed_points


def remove_duplicate_content(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """移除內容完全相同的知識點，保留最早的"""
    unique_points = {}
    duplicates_removed = 0

    for point in points:
        # 生成內容鍵（用於識別重複）
        content_key = (
            point.get('key_point', ''),
            point.get('original_phrase', ''),
            point.get('correction', '')
        )

        if content_key in unique_points:
            # 比較創建時間，保留較早的
            existing = unique_points[content_key]
            existing_time = datetime.fromisoformat(existing.get('created_at', '2099-12-31'))
            current_time = datetime.fromisoformat(point.get('created_at', '2099-12-31'))

            if current_time < existing_time:
                # 當前的更早，替換
                print(f"  替換重複: ID {existing['id']} → ID {point['id']} (較早)")
                unique_points[content_key] = point
            else:
                print(f"  移除重複: ID {point['id']} ('{content_key[0][:30]}...')")

            duplicates_removed += 1
        else:
            unique_points[content_key] = point

    return list(unique_points.values()), duplicates_removed


def analyze_data_quality(points: list[dict[str, Any]]) -> None:
    """分析數據質量"""
    print("\n📊 數據質量分析:")
    print(f"  總記錄數: {len(points)}")

    # 檢查 ID 唯一性
    ids = [p.get('id') for p in points]
    unique_ids = set(ids)
    print(f"  唯一 ID 數: {len(unique_ids)}")

    # 檢查內容唯一性
    content_keys = set()
    for p in points:
        key = (p.get('key_point', ''), p.get('original_phrase', ''), p.get('correction', ''))
        content_keys.add(key)
    print(f"  唯一內容數: {len(content_keys)}")

    # 檢查類別分布
    categories = {}
    for p in points:
        if not p.get('is_deleted', False):
            cat = p.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

    print("\n  類別分布:")
    for cat, count in sorted(categories.items()):
        valid = '✓' if cat in ['systematic', 'isolated', 'enhancement', 'other'] else '✗'
        print(f"    {cat}: {count} {valid}")

    # 檢查無效數據
    invalid_mastery = sum(1 for p in points
                          if p.get('mastery_level', 0) < 0 or p.get('mastery_level', 0) > 1)
    negative_counts = sum(1 for p in points
                          if p.get('mistake_count', 0) < 0 or p.get('correct_count', 0) < 0)

    print("\n  數據問題:")
    print(f"    無效掌握度: {invalid_mastery}")
    print(f"    負數計數: {negative_counts}")


def main():
    """主程序"""
    file_path = 'data/knowledge.json'

    print("🔧 知識點數據修復工具")
    print("=" * 50)

    # 載入數據
    print("\n1️⃣ 載入數據...")
    data = load_knowledge_data(file_path)
    points = data.get('data', data.get('knowledge_points', []))
    original_count = len(points)

    print(f"  載入 {original_count} 條記錄")

    # 分析原始數據
    print("\n2️⃣ 分析原始數據...")
    analyze_data_quality(points)

    # 自動繼續（非互動模式）
    print("\n自動模式：繼續修復...")

    # 備份原始檔案
    print("\n3️⃣ 備份原始檔案...")
    backup_path = backup_file(file_path)

    # 修復重複 ID
    print("\n4️⃣ 修復重複 ID...")
    points = fix_duplicate_ids(points)

    # 移除重複內容
    print("\n5️⃣ 移除重複內容...")
    points, duplicates_removed = remove_duplicate_content(points)

    # 重新排序 ID
    print("\n6️⃣ 重新排序 ID...")
    points.sort(key=lambda x: x.get('created_at', ''))
    for i, point in enumerate(points, 1):
        if point['id'] != i:
            print(f"  重新編號: ID {point['id']} → {i}")
            point['id'] = i

    # 更新數據結構
    data['data'] = points
    data['last_updated'] = datetime.now().isoformat()

    # 保存修復後的數據
    print("\n7️⃣ 保存修復後的數據...")
    save_knowledge_data(data, file_path)

    # 最終分析
    print("\n8️⃣ 修復後的數據分析:")
    analyze_data_quality(points)

    # 總結
    print("\n" + "=" * 50)
    print("✅ 修復完成!")
    print(f"  原始記錄數: {original_count}")
    print(f"  修復後記錄數: {len(points)}")
    print(f"  移除重複: {original_count - len(points)}")
    print(f"  備份檔案: {backup_path}")

    # 驗證建議
    print("\n💡 建議後續操作:")
    print("  1. 檢查修復後的數據: cat data/knowledge.json | python -m json.tool | head -50")
    print("  2. 如果有問題，恢復備份: cp " + backup_path + " data/knowledge.json")
    print("  3. 測試應用程式是否正常運行")


if __name__ == "__main__":
    main()
