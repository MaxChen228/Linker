#!/usr/bin/env python3
"""
知識點數據遷移腳本
解決知識點重複問題，將混合的知識點拆分為獨立的知識點
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.error_types import ErrorCategory


def load_knowledge_data(file_path: Path) -> Dict[str, Any]:
    """載入知識點資料"""
    if not file_path.exists():
        print(f"❌ 找不到資料檔案: {file_path}")
        return {"version": "2.0", "data": []}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 載入了 {len(data.get('data', []))} 個知識點")
    return data


def create_backup(file_path: Path):
    """創建備份檔案"""
    if not file_path.exists():
        return
    
    backup_dir = file_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{file_path.stem}_migration_backup_{timestamp}.json"
    
    import shutil
    shutil.copy2(file_path, backup_path)
    print(f"✅ 備份已創建: {backup_path}")


def analyze_duplicates(knowledge_points: List[Dict]) -> Dict[str, List[Dict]]:
    """分析重複的知識點"""
    groups = defaultdict(list)
    
    for point in knowledge_points:
        key_point = point.get("key_point", "")
        groups[key_point].append(point)
    
    # 只返回有重複的群組
    duplicates = {key: points for key, points in groups.items() if len(points) > 1}
    
    print(f"🔍 發現 {len(duplicates)} 個重複的知識點分類:")
    for key, points in duplicates.items():
        print(f"  - '{key}': {len(points)} 個重複")
        for point in points:
            original = point.get("original_phrase", "")
            correction = point.get("correction", "")
            examples_count = len(point.get("examples", []))
            print(f"    * ID:{point['id']} {original}→{correction} ({examples_count}例句)")
    
    return duplicates


def migrate_knowledge_point(old_point: Dict) -> Dict:
    """遷移單個知識點到新格式"""
    examples = old_point.get("examples", [])
    
    # 第一個例句作為原始錯誤
    if examples:
        first_example = examples[0]
        original_error = {
            "chinese_sentence": first_example.get("chinese", ""),
            "user_answer": first_example.get("user_answer", ""),
            "correct_answer": first_example.get("correct", ""),
            "timestamp": old_point.get("created_at", datetime.now().isoformat())
        }
        
        # 其餘例句作為複習記錄
        review_examples = []
        for example in examples[1:]:
            review_examples.append({
                "chinese_sentence": example.get("chinese", ""),
                "user_answer": example.get("user_answer", ""),
                "correct_answer": example.get("correct", ""),
                "timestamp": old_point.get("last_seen", datetime.now().isoformat()),
                "is_correct": False  # 假設都是錯誤記錄
            })
    else:
        # 如果沒有例句，創建空的原始錯誤
        original_error = {
            "chinese_sentence": "",
            "user_answer": old_point.get("original_phrase", ""),
            "correct_answer": old_point.get("correction", ""),
            "timestamp": old_point.get("created_at", datetime.now().isoformat())
        }
        review_examples = []
    
    # 生成更具體的 key_point
    original_phrase = old_point.get("original_phrase", "")
    if original_phrase and original_phrase not in old_point.get("key_point", ""):
        specific_key_point = f"{old_point['key_point']}: {original_phrase}"
    else:
        specific_key_point = old_point["key_point"]
    
    # 創建新格式的知識點
    new_point = {
        "id": old_point["id"],
        "key_point": specific_key_point,
        "category": old_point.get("category", "isolated"),
        "subtype": old_point.get("subtype", "vocabulary"),
        "explanation": old_point.get("explanation", ""),
        "original_phrase": old_point.get("original_phrase", ""),
        "correction": old_point.get("correction", ""),
        "original_error": original_error,
        "review_examples": review_examples,
        "mastery_level": old_point.get("mastery_level", 0.0),
        "mistake_count": old_point.get("mistake_count", 1),
        "correct_count": old_point.get("correct_count", 0),
        "created_at": old_point.get("created_at", datetime.now().isoformat()),
        "last_seen": old_point.get("last_seen", datetime.now().isoformat()),
        "next_review": old_point.get("next_review", datetime.now().isoformat())
    }
    
    return new_point


def split_duplicate_knowledge_points(duplicates: Dict[str, List[Dict]], next_id: int) -> List[Dict]:
    """拆分重複的知識點"""
    new_points = []
    
    print("🔧 開始拆分重複的知識點...")
    
    for key_point, points in duplicates.items():
        print(f"\n處理重複分類: '{key_point}'")
        
        for i, point in enumerate(points):
            original_phrase = point.get("original_phrase", "")
            correction = point.get("correction", "")
            
            # 為每個不同的錯誤創建獨立知識點
            if i == 0:
                # 第一個保持原ID
                new_point = migrate_knowledge_point(point)
            else:
                # 其他的分配新ID
                new_point = migrate_knowledge_point(point)
                new_point["id"] = next_id
                next_id += 1
                print(f"  ✨ 創建新知識點 ID:{new_point['id']} - {original_phrase}→{correction}")
            
            new_points.append(new_point)
    
    return new_points, next_id


def migrate_all_knowledge_points(knowledge_points: List[Dict]) -> List[Dict]:
    """遷移所有知識點"""
    print("\n🔧 開始遷移所有知識點到新格式...")
    
    # 分析重複情況
    duplicates = analyze_duplicates(knowledge_points)
    
    # 獲取下一個可用的ID
    max_id = max(point["id"] for point in knowledge_points) if knowledge_points else 0
    next_id = max_id + 1
    
    # 收集所有遷移後的知識點
    migrated_points = []
    processed_ids = set()
    
    # 處理重複的知識點
    if duplicates:
        duplicate_points, next_id = split_duplicate_knowledge_points(duplicates, next_id)
        migrated_points.extend(duplicate_points)
        
        # 記錄已處理的ID
        for key_point, points in duplicates.items():
            for point in points:
                processed_ids.add(point["id"])
    
    # 處理非重複的知識點
    for point in knowledge_points:
        if point["id"] not in processed_ids:
            migrated_point = migrate_knowledge_point(point)
            migrated_points.append(migrated_point)
    
    print(f"\n✅ 遷移完成: {len(knowledge_points)} → {len(migrated_points)} 個知識點")
    
    return migrated_points


def save_migrated_data(migrated_points: List[Dict], output_path: Path):
    """儲存遷移後的資料"""
    output_data = {
        "version": "3.0",  # 升級版本號
        "migration_date": datetime.now().isoformat(),
        "data": migrated_points
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 遷移資料已儲存: {output_path}")


def main():
    """主函數"""
    print("🚀 開始知識點數據遷移...")
    
    # 設定路徑
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    knowledge_file = data_dir / "knowledge.json"
    
    # 創建備份
    create_backup(knowledge_file)
    
    # 載入現有資料
    data = load_knowledge_data(knowledge_file)
    knowledge_points = data.get("data", [])
    
    if not knowledge_points:
        print("⚠️  沒有找到需要遷移的資料")
        return
    
    # 執行遷移
    migrated_points = migrate_all_knowledge_points(knowledge_points)
    
    # 儲存結果
    save_migrated_data(migrated_points, knowledge_file)
    
    print("\n🎉 知識點數據遷移完成！")
    print("\n📋 遷移摘要:")
    print(f"  - 原始知識點數量: {len(knowledge_points)}")
    print(f"  - 遷移後知識點數量: {len(migrated_points)}")
    print(f"  - 版本: 2.0 → 3.0")
    print("\n📚 現在每個知識點都對應一個具體的錯誤模式，不再混合不同的錯誤！")


if __name__ == "__main__":
    main()