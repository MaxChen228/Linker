#!/usr/bin/env python3
"""
資料遷移腳本：從 JSON 遷移到 PostgreSQL
支援完整的資料遷移和驗證功能
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import DATA_DIR
from core.database.connection import get_database_connection
from core.database.exceptions import DatabaseError
from core.database.repositories.knowledge_repository import KnowledgePointRepository
from core.error_types import ErrorCategory
from core.knowledge import KnowledgePoint, OriginalError, ReviewExample
from core.log_config import get_module_logger

logger = get_module_logger("migrate_data")


class DataMigrator:
    """資料遷移器"""

    def __init__(self):
        self.db_connection = get_database_connection()
        self.repository: Optional[KnowledgePointRepository] = None
        self.stats = {
            "total_points": 0,
            "migrated_points": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    async def initialize(self):
        """初始化資料庫連線和 Repository"""
        try:
            pool = await self.db_connection.connect()
            if not pool:
                raise DatabaseError("無法建立資料庫連線")

            self.repository = KnowledgePointRepository(pool)
            logger.info("資料庫連線初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化失敗: {e}")
            return False

    async def cleanup(self):
        """清理資源"""
        if self.db_connection:
            await self.db_connection.disconnect()

    def load_json_data(self, json_file: Path) -> Optional[Dict[str, Any]]:
        """載入 JSON 資料"""
        try:
            if not json_file.exists():
                logger.error(f"JSON 檔案不存在: {json_file}")
                return None

            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"成功載入 JSON 檔案: {json_file}")
            logger.info(f"資料版本: {data.get('version', 'unknown')}")
            logger.info(f"知識點數量: {len(data.get('data', []))}")

            return data
        except Exception as e:
            logger.error(f"載入 JSON 檔案失敗: {e}")
            return None

    def json_to_knowledge_point(self, point_data: Dict[str, Any]) -> Optional[KnowledgePoint]:
        """將 JSON 資料轉換為 KnowledgePoint 物件"""
        try:
            # 處理原始錯誤
            original_error_data = point_data.get("original_error", {})
            original_error = OriginalError(
                chinese_sentence=original_error_data.get("chinese_sentence", ""),
                user_answer=original_error_data.get("user_answer", ""),
                correct_answer=original_error_data.get("correct_answer", ""),
                timestamp=original_error_data.get("timestamp", datetime.now().isoformat()),
            )

            # 處理複習例句
            review_examples = []
            for example_data in point_data.get("review_examples", []):
                review_example = ReviewExample(
                    chinese_sentence=example_data.get("chinese_sentence", ""),
                    user_answer=example_data.get("user_answer", ""),
                    correct_answer=example_data.get("correct_answer", ""),
                    timestamp=example_data.get("timestamp", datetime.now().isoformat()),
                    is_correct=example_data.get("is_correct", False),
                )
                review_examples.append(review_example)

            # 建立 KnowledgePoint
            knowledge_point = KnowledgePoint(
                id=point_data.get("id", 0),
                key_point=point_data.get("key_point", ""),
                category=ErrorCategory.from_string(point_data.get("category", "")),
                subtype=point_data.get("subtype", ""),
                explanation=point_data.get("explanation", ""),
                original_phrase=point_data.get("original_phrase", ""),
                correction=point_data.get("correction", ""),
                original_error=original_error,
                review_examples=review_examples,
                mastery_level=float(point_data.get("mastery_level", 0.0)),
                mistake_count=int(point_data.get("mistake_count", 1)),
                correct_count=int(point_data.get("correct_count", 0)),
                created_at=point_data.get("created_at", datetime.now().isoformat()),
                last_seen=point_data.get("last_seen", datetime.now().isoformat()),
                next_review=point_data.get("next_review", ""),
                is_deleted=point_data.get("is_deleted", False),
                deleted_at=point_data.get("deleted_at", ""),
                deleted_reason=point_data.get("deleted_reason", ""),
                tags=point_data.get("tags", []),
                custom_notes=point_data.get("custom_notes", ""),
                version_history=point_data.get("version_history", []),
                last_modified=point_data.get("last_modified", datetime.now().isoformat()),
            )

            return knowledge_point

        except Exception as e:
            logger.error(f"轉換知識點資料失敗: {e}, 資料: {point_data.get('id', 'unknown')}")
            return None

    async def migrate_knowledge_points(
        self, json_data: Dict[str, Any], batch_size: int = 10
    ) -> bool:
        """遷移知識點資料"""
        if not self.repository:
            logger.error("Repository 未初始化")
            return False

        points_data = json_data.get("data", [])
        self.stats["total_points"] = len(points_data)
        self.stats["start_time"] = datetime.now()

        logger.info(f"開始遷移 {self.stats['total_points']} 個知識點...")

        # 批次處理
        for i in range(0, len(points_data), batch_size):
            batch = points_data[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(points_data) + batch_size - 1) // batch_size

            logger.info(f"處理第 {batch_num}/{total_batches} 批次 ({len(batch)} 個知識點)...")

            async with self.repository.transaction() as conn:
                for point_data in batch:
                    try:
                        # 轉換資料
                        knowledge_point = self.json_to_knowledge_point(point_data)
                        if not knowledge_point:
                            self.stats["errors"] += 1
                            continue

                        # 檢查是否已存在 (根據 key_point 判斷)
                        existing_points = await self.repository.search(knowledge_point.key_point)
                        if any(ep.key_point == knowledge_point.key_point for ep in existing_points):
                            logger.debug(f"知識點已存在，跳過: {knowledge_point.key_point}")
                            continue

                        # 插入資料庫
                        await self.repository.create(knowledge_point)
                        self.stats["migrated_points"] += 1

                        # 進度報告
                        if self.stats["migrated_points"] % 50 == 0:
                            progress = (
                                self.stats["migrated_points"] / self.stats["total_points"]
                            ) * 100
                            logger.info(
                                f"已遷移: {self.stats['migrated_points']}/{self.stats['total_points']} ({progress:.1f}%)"
                            )

                    except Exception as e:
                        logger.error(f"遷移知識點失敗: {e}")
                        self.stats["errors"] += 1

        self.stats["end_time"] = datetime.now()
        return True

    async def verify_migration(self, json_data: Dict[str, Any]) -> bool:
        """驗證遷移結果"""
        logger.info("開始驗證遷移結果...")

        if not self.repository:
            logger.error("Repository 未初始化")
            return False

        try:
            # 獲取資料庫中的統計
            db_stats = await self.repository.get_statistics()
            json_points = json_data.get("data", [])

            logger.info("遷移驗證結果:")
            logger.info(f"  JSON 中的知識點數量: {len(json_points)}")
            logger.info(f"  資料庫中的知識點數量: {db_stats.get('total_active', 0)}")
            logger.info(f"  成功遷移數量: {self.stats['migrated_points']}")
            logger.info(f"  錯誤數量: {self.stats['errors']}")

            # 檢查關鍵統計
            success_rate = (
                (self.stats["migrated_points"] / self.stats["total_points"]) * 100
                if self.stats["total_points"] > 0
                else 0
            )
            logger.info(f"  遷移成功率: {success_rate:.1f}%")

            # 驗證資料完整性 (檢查前幾個知識點)
            logger.info("驗證資料完整性...")
            sample_size = min(5, len(json_points))
            for i in range(sample_size):
                json_point = json_points[i]
                key_point = json_point.get("key_point", "")

                # 在資料庫中搜尋
                db_points = await self.repository.search(key_point)
                matching_points = [dp for dp in db_points if dp.key_point == key_point]

                if matching_points:
                    db_point = matching_points[0]
                    logger.debug(f"✓ 知識點驗證通過: {key_point}")

                    # 詳細比較 (可選)
                    if json_point.get("explanation") != db_point.explanation:
                        logger.warning(f"說明不匹配: {key_point}")
                else:
                    logger.warning(f"✗ 知識點未找到: {key_point}")

            return success_rate > 90  # 成功率超過90%視為通過

        except Exception as e:
            logger.error(f"驗證過程失敗: {e}")
            return False

    def print_migration_report(self):
        """印出遷移報告"""
        duration = None
        if self.stats["start_time"] and self.stats["end_time"]:
            duration = self.stats["end_time"] - self.stats["start_time"]

        print("\n" + "=" * 60)
        print("資料遷移完成報告")
        print("=" * 60)
        print(f"總知識點數量: {self.stats['total_points']}")
        print(f"成功遷移數量: {self.stats['migrated_points']}")
        print(f"錯誤數量: {self.stats['errors']}")

        if self.stats["total_points"] > 0:
            success_rate = (self.stats["migrated_points"] / self.stats["total_points"]) * 100
            print(f"成功率: {success_rate:.1f}%")

        if duration:
            print(f"遷移時間: {duration.total_seconds():.1f} 秒")

        if self.stats["errors"] == 0:
            print("✅ 遷移完成，無錯誤")
        else:
            print(f"⚠️  遷移完成，有 {self.stats['errors']} 個錯誤")

        print("=" * 60)


async def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="JSON 到 PostgreSQL 資料遷移工具")
    parser.add_argument("--json-file", help="指定 JSON 檔案路徑")
    parser.add_argument("--batch-size", type=int, default=10, help="批次大小")
    parser.add_argument("--dry-run", action="store_true", help="僅驗證，不執行遷移")
    parser.add_argument("--force", action="store_true", help="強制遷移，忽略現有資料")
    parser.add_argument("--verify-only", action="store_true", help="僅執行驗證")

    args = parser.parse_args()

    # 確定 JSON 檔案路徑
    if args.json_file:
        json_file = Path(args.json_file)
    else:
        json_file = DATA_DIR / "knowledge.json"

    migrator = DataMigrator()

    try:
        # 初始化
        logger.info("正在初始化資料庫連線...")
        if not await migrator.initialize():
            logger.error("初始化失敗")
            sys.exit(1)

        # 載入 JSON 資料
        logger.info(f"正在載入 JSON 資料: {json_file}")
        json_data = migrator.load_json_data(json_file)
        if not json_data:
            logger.error("載入 JSON 資料失敗")
            sys.exit(1)

        if args.verify_only:
            # 僅驗證
            logger.info("執行驗證模式...")
            success = await migrator.verify_migration(json_data)
            if success:
                logger.info("✅ 驗證通過")
                sys.exit(0)
            else:
                logger.error("❌ 驗證失敗")
                sys.exit(1)

        if args.dry_run:
            # 僅檢查，不執行
            logger.info("執行乾跑模式 (不會實際遷移資料)...")
            points_count = len(json_data.get("data", []))
            logger.info(f"將要遷移 {points_count} 個知識點")
            logger.info("乾跑完成，未執行實際遷移")
            sys.exit(0)

        # 確認遷移
        if not args.force:
            points_count = len(json_data.get("data", []))
            response = input(f"即將遷移 {points_count} 個知識點到資料庫，是否繼續？(y/N): ")
            if response.lower() != "y":
                logger.info("取消遷移")
                sys.exit(0)

        # 執行遷移
        logger.info("開始執行資料遷移...")
        success = await migrator.migrate_knowledge_points(json_data, args.batch_size)

        if success:
            # 驗證遷移結果
            verification_success = await migrator.verify_migration(json_data)

            # 印出報告
            migrator.print_migration_report()

            if verification_success:
                logger.info("🎉 遷移成功完成並通過驗證")
                sys.exit(0)
            else:
                logger.warning("⚠️  遷移完成但驗證未通過，請檢查")
                sys.exit(1)
        else:
            logger.error("❌ 遷移失敗")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("遷移被用戶中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"遷移過程發生錯誤: {e}")
        sys.exit(1)
    finally:
        await migrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
