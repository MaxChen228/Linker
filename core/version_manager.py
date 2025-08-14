"""
版本管理系統 - 統一管理所有資料檔案的版本控制與遷移
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core.log_config import get_module_logger

logger = get_module_logger(__name__)


class DataVersion(Enum):
    """資料版本定義"""

    V1_0 = "1.0"  # 原始格式（無版本標記）
    V2_0 = "2.0"  # 第一次擴充（PatternEnrichmentService）
    V3_0 = "3.0"  # 完整擴充版（含所有進階欄位）
    V3_1 = "3.1"  # 修正版本不一致問題後的版本
    V4_0 = "4.0"  # 知識點管理系統擴充（編輯、刪除、回收站）


class FileType(Enum):
    """檔案類型"""

    PATTERNS_BASIC = "patterns_basic"  # grammar_patterns.json
    PATTERNS_ENRICHED = "patterns_enriched"  # patterns_enriched_complete.json
    KNOWLEDGE = "knowledge"  # knowledge.json
    PRACTICE_LOG = "practice_log"  # practice_log.json


class VersionManager:
    """統一版本管理器"""

    # 版本遷移路徑定義
    MIGRATION_PATHS = {
        FileType.PATTERNS_BASIC: {
            None: DataVersion.V1_0,  # 無版本標記視為 v1.0
            DataVersion.V1_0: DataVersion.V2_0,
            DataVersion.V2_0: DataVersion.V3_0,
            DataVersion.V3_0: DataVersion.V3_1,
        },
        FileType.PATTERNS_ENRICHED: {
            DataVersion.V2_0: DataVersion.V3_0,
            DataVersion.V3_0: DataVersion.V3_1,
        },
        FileType.KNOWLEDGE: {
            None: DataVersion.V1_0,
            DataVersion.V1_0: DataVersion.V2_0,
            DataVersion.V2_0: DataVersion.V3_0,
            DataVersion.V3_0: DataVersion.V4_0,
        },
    }

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # 備份目錄
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def detect_version(self, file_path: Path) -> Optional[DataVersion]:
        """檢測檔案版本"""
        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # 檢查是否有版本標記
            if isinstance(data, dict) and "version" in data:
                version_str = data["version"]
                # 嘗試匹配已知版本
                for v in DataVersion:
                    if v.value == version_str:
                        return v
                logger.warning(f"Unknown version: {version_str} in {file_path}")
                return None

            # 無版本標記，視為 v1.0
            return None

        except Exception as e:
            logger.error(f"Failed to detect version for {file_path}: {e}")
            return None

    def needs_migration(
        self, file_path: Path, file_type: FileType
    ) -> tuple[bool, Optional[DataVersion]]:
        """檢查是否需要遷移"""
        current_version = self.detect_version(file_path)

        # 獲取目標版本（最新版本）
        migration_path = self.MIGRATION_PATHS.get(file_type, {})
        if not migration_path:
            return False, None

        # 找出最新版本
        latest_version = DataVersion.V4_0 if file_type == FileType.KNOWLEDGE else DataVersion.V3_1

        # 檢查是否需要遷移
        if current_version == latest_version:
            return False, current_version

        # 檢查是否有遷移路徑
        if current_version in migration_path or current_version is None:
            return True, current_version

        return False, current_version

    def backup_file(self, file_path: Path) -> Path:
        """備份檔案"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name

        import shutil

        shutil.copy2(file_path, backup_path)
        logger.info(f"Backed up {file_path} to {backup_path}")

        return backup_path

    def migrate_patterns_v1_to_v2(self, data: Any) -> dict:
        """句型資料 v1.0 -> v2.0"""
        logger.info("Migrating patterns from v1.0 to v2.0")

        # v1 是純陣列，v2 加入元數據
        patterns = data if isinstance(data, list) else data.get("patterns", [])

        return {
            "version": DataVersion.V2_0.value,
            "generated_at": datetime.now().isoformat(),
            "total_patterns": len(patterns),
            "patterns": patterns,
        }

    def migrate_patterns_v2_to_v3(self, data: dict) -> dict:
        """句型資料 v2.0 -> v3.0"""
        logger.info("Migrating patterns from v2.0 to v3.0")

        # v3 增加 enrichment_summary
        if "enrichment_summary" not in data:
            data["enrichment_summary"] = {
                "completed": len(data.get("patterns", [])),
                "failed": 0,
                "model": "gemini-2.5-pro",
                "temperature": 0.7,
                "description": "Migrated from v2.0",
            }

        data["version"] = DataVersion.V3_0.value
        return data

    def migrate_patterns_v3_to_v3_1(self, data: dict) -> dict:
        """句型資料 v3.0 -> v3.1（修正版本）"""
        logger.info("Migrating patterns from v3.0 to v3.1")

        # 標準化所有欄位
        data["version"] = DataVersion.V3_1.value
        data["last_migration"] = datetime.now().isoformat()

        # 確保所有句型都有必要欄位
        for pattern in data.get("patterns", []):
            # 確保有 ID
            if "id" not in pattern:
                pattern["id"] = pattern.get("pattern", "unknown").replace(" ", "_")

            # 確保有基本欄位
            pattern.setdefault("category", "uncategorized")
            pattern.setdefault("difficulty", 3)
            pattern.setdefault("examples", [])

        return data

    def migrate_knowledge_v1_to_v2(self, data: Any) -> dict:
        """知識點資料 v1.0 -> v2.0"""
        logger.info("Migrating knowledge from v1.0 to v2.0")

        points = data if isinstance(data, list) else data.get("knowledge_points", [])

        return {
            "version": DataVersion.V2_0.value,
            "generated_at": datetime.now().isoformat(),
            "total_points": len(points),
            "knowledge_points": points,
        }

    def migrate_knowledge_v2_0_to_v3_0(self, data: dict) -> dict:
        """知識點資料 v2.0 -> v3.0"""
        logger.info("Migrating knowledge from v2.0 to v3.0")

        # v3.0 添加了額外的元數據欄位
        data["version"] = DataVersion.V3_0.value
        data["last_updated"] = datetime.now().isoformat()
        return data

    def migrate_knowledge_v3_0_to_v4_0(self, data: dict) -> dict:
        """知識點資料 v3.0 -> v4.0"""
        logger.info("Migrating knowledge from v3.0 to v4.0")

        # v4.0 支援編輯、刪除、回收站功能
        # 知識點本身的遷移已在 knowledge.py 中處理
        data["version"] = DataVersion.V4_0.value
        data["features"] = {"edit": True, "delete": True, "trash": True, "version_history": True}
        return data

    def migrate_file(self, file_path: Path, file_type: FileType) -> bool:
        """執行檔案遷移"""
        needs_migration, current_version = self.needs_migration(file_path, file_type)

        if not needs_migration:
            logger.info(f"{file_path} is already at the latest version")
            return False

        # 備份原始檔案
        self.backup_file(file_path)

        # 載入資料
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # 執行遷移鏈
        migration_path = self.MIGRATION_PATHS[file_type]
        current = current_version
        target_version = DataVersion.V4_0 if file_type == FileType.KNOWLEDGE else DataVersion.V3_1

        while current != target_version:
            # 找出下一個版本
            next_version = migration_path.get(current)
            if not next_version:
                logger.error(f"No migration path from {current} for {file_type}")
                break

            # 執行對應的遷移函數
            current_str = "v1" if current is None else f"v{current.value.replace('.', '_')}"
            next_str = f"v{next_version.value.replace('.', '_')}"

            # 統一使用 patterns 作為函數名稱前綴
            if file_type in [FileType.PATTERNS_BASIC, FileType.PATTERNS_ENRICHED]:
                func_prefix = "patterns"
            else:
                func_prefix = file_type.value

            migration_func_name = f"migrate_{func_prefix}_{current_str}_to_{next_str}"
            migration_func = getattr(self, migration_func_name, None)

            if migration_func:
                logger.info(f"Applying migration: {migration_func_name}")
                data = migration_func(data)
            else:
                logger.warning(f"Migration function not found: {migration_func_name}")
                # 至少更新版本號
                if isinstance(data, dict):
                    data["version"] = next_version.value
                else:
                    # 如果資料不是字典（例如陣列），轉換為字典格式
                    data = {"version": next_version.value, "data": data}

            current = next_version

            # 防止無限循環
            if current == target_version:
                break

        # 儲存遷移後的資料
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Successfully migrated {file_path} to {current.value if current else 'unknown'}"
        )
        return True

    def check_and_migrate_all(self) -> dict[str, bool]:
        """檢查並遷移所有資料檔案"""
        results = {}

        # 定義檔案映射
        file_mappings = {
            FileType.PATTERNS_BASIC: self.data_dir / "grammar_patterns.json",
            FileType.PATTERNS_ENRICHED: self.data_dir / "patterns_enriched_complete.json",
            FileType.KNOWLEDGE: self.data_dir / "knowledge.json",
            FileType.PRACTICE_LOG: self.data_dir / "practice_log.json",
        }

        for file_type, file_path in file_mappings.items():
            if file_path.exists():
                try:
                    results[str(file_path)] = self.migrate_file(file_path, file_type)
                except Exception as e:
                    logger.error(f"Failed to migrate {file_path}: {e}")
                    results[str(file_path)] = False
            else:
                logger.info(f"File not found: {file_path}")
                results[str(file_path)] = None

        return results

    def get_version_report(self) -> dict[str, Any]:
        """生成版本報告"""
        report = {"timestamp": datetime.now().isoformat(), "files": {}}

        file_mappings = {
            FileType.PATTERNS_BASIC: self.data_dir / "grammar_patterns.json",
            FileType.PATTERNS_ENRICHED: self.data_dir / "patterns_enriched_complete.json",
            FileType.KNOWLEDGE: self.data_dir / "knowledge.json",
            FileType.PRACTICE_LOG: self.data_dir / "practice_log.json",
        }

        for file_type, file_path in file_mappings.items():
            if file_path.exists():
                version = self.detect_version(file_path)
                needs_migration, _ = self.needs_migration(file_path, file_type)

                report["files"][str(file_path)] = {
                    "type": file_type.value,
                    "version": version.value if version else "unknown",
                    "needs_migration": needs_migration,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                }

        return report


# CLI 測試工具
if __name__ == "__main__":
    import sys

    manager = VersionManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            # 檢查所有檔案版本
            report = manager.get_version_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))

        elif command == "migrate":
            # 執行遷移
            results = manager.check_and_migrate_all()
            print("\n遷移結果：")
            for file, result in results.items():
                status = (
                    "✅ 已遷移" if result else "⏭️  已是最新" if result is False else "❌ 檔案不存在"
                )
                print(f"  {file}: {status}")

        elif command == "backup":
            # 備份所有檔案
            for file in [
                "grammar_patterns.json",
                "patterns_enriched_complete.json",
                "knowledge.json",
            ]:
                file_path = Path("data") / file
                if file_path.exists():
                    backup_path = manager.backup_file(file_path)
                    print(f"✅ Backed up {file} to {backup_path}")

    else:
        print("使用方式：")
        print("  python version_manager.py check    # 檢查版本狀態")
        print("  python version_manager.py migrate  # 執行版本遷移")
        print("  python version_manager.py backup   # 備份所有檔案")
