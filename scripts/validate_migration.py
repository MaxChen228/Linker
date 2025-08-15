#!/usr/bin/env python3
"""
遷移驗證測試腳本
執行完整的數據和功能驗證，確保 JSON 到資料庫遷移成功
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import psycopg2
import requests

from core.config import DATABASE_URL


class MigrationValidator:
    """遷移驗證器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        self.errors = []
        self.start_time = time.time()

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """記錄測試結果"""
        self.results[test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        if not success:
            self.errors.append(f"{test_name}: {details}")

    def validate_data_integrity(self) -> bool:
        """驗證數據完整性"""
        print("📊 驗證數據完整性...")

        try:
            # 連接資料庫
            parsed = urlparse(DATABASE_URL)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],
            )
            cursor = conn.cursor()

            # 1. 記錄總數檢查
            cursor.execute("SELECT COUNT(*) FROM knowledge_points WHERE is_deleted = false;")
            db_count = cursor.fetchone()[0]

            # 檢查 JSON 檔案
            knowledge_file = Path("data/knowledge.json")
            if knowledge_file.exists():
                with open(knowledge_file, encoding="utf-8") as f:
                    json_data = json.load(f)
                json_count = len(json_data.get("knowledge_points", json_data))

                # 允許差異在 5% 以內
                diff_percent = abs(db_count - json_count) / max(json_count, 1) * 100
                success = diff_percent <= 5
                self.log_test(
                    "data_integrity_count",
                    success,
                    f"資料庫: {db_count}, JSON: {json_count}, 差異: {diff_percent:.1f}%",
                )
            else:
                self.log_test("data_integrity_count", False, "knowledge.json 不存在")

            # 2. 必填欄位檢查
            cursor.execute(
                "SELECT COUNT(*) FROM knowledge_points WHERE key_point IS NULL OR key_point = '';"
            )
            null_key_points = cursor.fetchone()[0]
            self.log_test(
                "data_integrity_required_fields",
                null_key_points == 0,
                f"{null_key_points} 個空的 key_point",
            )

            # 3. 外鍵完整性
            cursor.execute("""
                SELECT COUNT(*) FROM knowledge_point_tags kpt 
                LEFT JOIN knowledge_points kp ON kpt.knowledge_point_id = kp.id 
                WHERE kp.id IS NULL;
            """)
            invalid_fk = cursor.fetchone()[0]
            self.log_test(
                "data_integrity_foreign_keys", invalid_fk == 0, f"{invalid_fk} 個無效外鍵"
            )

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            self.log_test("data_integrity", False, f"資料庫連接錯誤: {e}")
            return False

    def validate_api_endpoints(self) -> bool:
        """驗證 API 端點"""
        print("🔌 驗證 API 端點...")

        endpoints = [
            ("GET", "/api/knowledge/recommendations", 200),
            ("GET", "/api/knowledge/1", 200),
            ("GET", "/api/patterns", 200),
            ("GET", "/calendar/api/stats/streak", 200),
            ("POST", "/api/generate-question", 200, {"mode": "new", "level": 1}),
        ]

        all_success = True
        for method, endpoint, expected_status, *data in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                if method == "GET":
                    response = requests.get(url, timeout=10)
                else:
                    payload = data[0] if data else {}
                    response = requests.post(url, json=payload, timeout=10)

                success = response.status_code == expected_status
                self.log_test(
                    f"api_{method.lower()}_{endpoint.replace('/', '_')}",
                    success,
                    f"狀態碼: {response.status_code}, 預期: {expected_status}",
                )
                all_success = all_success and success

            except Exception as e:
                self.log_test(f"api_{method.lower()}_{endpoint}", False, str(e))
                all_success = False

        return all_success

    def validate_web_ui(self) -> bool:
        """驗證 Web UI"""
        print("🌐 驗證 Web UI...")

        pages = ["/", "/practice", "/knowledge", "/patterns"]

        all_success = True
        for page in pages:
            try:
                url = f"{self.base_url}{page}"
                response = requests.get(url, timeout=10)
                success = response.status_code == 200
                self.log_test(
                    f"web_ui{page.replace('/', '_') or '_home'}",
                    success,
                    f"狀態碼: {response.status_code}",
                )
                all_success = all_success and success

            except Exception as e:
                self.log_test(f"web_ui{page}", False, str(e))
                all_success = False

        return all_success

    def validate_performance(self) -> bool:
        """驗證效能"""
        print("⚡ 驗證效能...")

        # 單一查詢效能
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/api/knowledge/1", timeout=10)
            duration = time.time() - start

            success = duration < 0.5 and response.status_code == 200
            self.log_test("performance_single_query", success, f"查詢時間: {duration:.3f}s")

            # 併發測試（簡化版）
            start = time.time()
            responses = []
            for _ in range(5):
                resp = requests.get(f"{self.base_url}/api/knowledge/recommendations", timeout=10)
                responses.append(resp)
            duration = time.time() - start

            all_200 = all(r.status_code == 200 for r in responses)
            success = duration < 2.0 and all_200
            self.log_test(
                "performance_concurrent",
                success,
                f"5 個併發請求時間: {duration:.3f}s, 全部成功: {all_200}",
            )

            return success

        except Exception as e:
            self.log_test("performance", False, str(e))
            return False

    def validate_error_handling(self) -> bool:
        """驗證錯誤處理"""
        print("❌ 驗證錯誤處理...")

        error_tests = [
            ("GET", "/api/knowledge/999", 404),  # 不存在的資源
            ("POST", "/api/generate-question", 200, {}),  # 空請求應該有默認值
            ("GET", "/nonexistent", 404),  # 不存在的路由
        ]

        all_success = True
        for method, endpoint, expected_status, *data in error_tests:
            try:
                url = f"{self.base_url}{endpoint}"
                if method == "GET":
                    response = requests.get(url, timeout=10)
                else:
                    payload = data[0] if data else {}
                    response = requests.post(url, json=payload, timeout=10)

                success = response.status_code == expected_status
                self.log_test(
                    f"error_handling_{endpoint.replace('/', '_')}",
                    success,
                    f"狀態碼: {response.status_code}, 預期: {expected_status}",
                )
                all_success = all_success and success

            except Exception as e:
                self.log_test(f"error_handling_{endpoint}", False, str(e))
                all_success = False

        return all_success

    async def run_all_tests(self):
        """執行所有驗證測試"""
        print("🔍 開始遷移驗證測試...\n")

        tests = [
            ("數據完整性", self.validate_data_integrity),
            ("API 端點", self.validate_api_endpoints),
            ("Web UI", self.validate_web_ui),
            ("效能基準", self.validate_performance),
            ("錯誤處理", self.validate_error_handling),
        ]

        for test_name, test_func in tests:
            try:
                success = test_func()
                print(f"{'✅' if success else '❌'} {test_name}: {'通過' if success else '失敗'}")
            except Exception as e:
                print(f"❌ {test_name}: 執行錯誤 - {e}")
                self.errors.append(f"{test_name}: 執行錯誤 - {e}")

        print()

    def generate_report(self) -> Dict[str, Any]:
        """生成驗證報告"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["success"])

        return {
            "timestamp": datetime.now().isoformat(),
            "duration": time.time() - self.start_time,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests else 0,
            },
            "results": self.results,
            "errors": self.errors,
            "status": "PASS" if not self.errors else "FAIL",
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> List[str]:
        """生成改進建議"""
        recommendations = []

        if any("performance" in error for error in self.errors):
            recommendations.append("考慮添加資料庫索引以提升查詢效能")
            recommendations.append("評估資料庫連接池配置")

        if any("api" in error for error in self.errors):
            recommendations.append("檢查 API 路由配置和錯誤處理")

        if any("data_integrity" in error for error in self.errors):
            recommendations.append("重新執行數據遷移並檢查數據一致性")

        if not self.errors:
            recommendations.append("遷移驗證完全通過，系統可以切換到資料庫模式")

        return recommendations


async def main():
    """主執行函數"""
    validator = MigrationValidator()

    # 執行測試
    await validator.run_all_tests()

    # 生成報告
    report = validator.generate_report()

    # 顯示結果
    print("=" * 60)
    print("📋 遷移驗證報告")
    print("=" * 60)
    print(f"總測試數: {report['summary']['total_tests']}")
    print(f"通過: {report['summary']['passed']}")
    print(f"失敗: {report['summary']['failed']}")
    print(f"成功率: {report['summary']['success_rate']:.1f}%")
    print(f"執行時間: {report['duration']:.2f}s")
    print(f"整體狀態: {'✅ 通過' if report['status'] == 'PASS' else '❌ 失敗'}")

    if report["errors"]:
        print("\n❌ 失敗的測試:")
        for error in report["errors"]:
            print(f"  - {error}")

    if report["recommendations"]:
        print("\n💡 建議:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

    # 儲存報告
    report_file = Path("data") / f"migration_validation_{int(time.time())}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 詳細報告已儲存至: {report_file}")

    return report["status"] == "PASS"


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  測試被中斷")
        exit(1)
    except Exception as e:
        print(f"\n💥 測試執行失敗: {e}")
        exit(1)
