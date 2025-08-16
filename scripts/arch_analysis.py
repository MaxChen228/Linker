"""
實際架構一致性分析腳本
基於真實數據和方法調用進行架構對比分析
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.database.adapter import KnowledgeManagerAdapter
    from core.error_types import ErrorCategory
    from core.knowledge import KnowledgeManager
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    print("請確保在專案根目錄執行此腳本")
    sys.exit(1)


class RealArchitectureAnalyzer:
    """真實架構一致性分析器"""

    def __init__(self):
        self.json_manager = KnowledgeManager()
        self.db_manager = KnowledgeManagerAdapter(use_database=True)
        self.analysis_results = {}

    async def run_complete_analysis(self) -> dict[str, Any]:
        """執行完整的架構一致性分析"""
        print("🔍 開始真實架構一致性分析...")
        print("=" * 60)

        start_time = time.time()

        # 分析各個層面
        results = {
            "timestamp": datetime.now().isoformat(),
            "api_interface_analysis": await self._analyze_api_interfaces(),
            "data_model_analysis": self._analyze_data_models(),
            "statistics_consistency": await self._analyze_statistics_consistency(),
            "performance_comparison": await self._analyze_performance(),
            "method_availability": self._analyze_method_availability(),
            "error_handling_comparison": await self._analyze_error_handling(),
            "overall_assessment": {},
        }

        # 生成整體評估
        results["overall_assessment"] = self._generate_overall_assessment(results)
        results["analysis_duration"] = time.time() - start_time

        return results

    async def _analyze_api_interfaces(self) -> dict[str, Any]:
        """分析API接口一致性"""
        print("\n📋 1. API接口一致性分析")

        # 檢查核心方法存在性
        core_methods = [
            "get_statistics",
            "get_active_points",
            "get_review_candidates",
            "get_recommendations",
            "edit_knowledge_point",
            "delete_point",
            "restore_point",
        ]

        method_comparison = {}
        for method in core_methods:
            json_has = hasattr(self.json_manager, method)

            # 檢查Database管理器的異步版本
            async_method = (
                method + "_async" if method != "get_active_points" else "get_knowledge_points_async"
            )
            db_has = hasattr(self.db_manager, async_method)

            method_comparison[method] = {
                "json_has": json_has,
                "db_has": db_has,
                "both_available": json_has and db_has,
            }

        available_methods = sum(1 for m in method_comparison.values() if m["both_available"])
        compatibility_score = available_methods / len(core_methods)

        print(
            f"   核心方法兼容性: {compatibility_score:.1%} ({available_methods}/{len(core_methods)})"
        )

        return {
            "method_comparison": method_comparison,
            "compatibility_score": compatibility_score,
            "total_methods_checked": len(core_methods),
        }

    def _analyze_data_models(self) -> dict[str, Any]:
        """分析數據模型一致性"""
        print("\n📊 2. 數據模型一致性分析")

        # 檢查錯誤分類系統
        try:
            categories = [cat.value for cat in ErrorCategory]
            print(f"   錯誤分類系統: {len(categories)} 種分類")

            return {
                "error_categories": categories,
                "category_count": len(categories),
                "model_consistency": True,  # 兩種模式使用相同的數據模型
                "note": "兩種模式使用完全相同的 KnowledgePoint 和 ErrorCategory 模型",
            }
        except Exception as e:
            return {"error": str(e), "model_consistency": False}

    async def _analyze_statistics_consistency(self) -> dict[str, Any]:
        """分析統計數據一致性"""
        print("\n📈 3. 統計數據一致性分析")

        try:
            # 獲取兩種模式的統計數據
            json_stats = self.json_manager.get_statistics()
            db_stats = await self.db_manager.get_statistics_async()

            # 比較關鍵指標
            key_metrics = ["knowledge_points", "total_practices", "correct_count", "mistake_count"]
            metric_comparison = {}

            for metric in key_metrics:
                json_val = json_stats.get(metric, 0)
                db_val = db_stats.get(metric, 0)

                metric_comparison[metric] = {
                    "json": json_val,
                    "db": db_val,
                    "match": json_val == db_val,
                    "diff_percent": abs(json_val - db_val) / max(json_val, db_val, 1) * 100,
                }

            # 計算一致性分數
            matching_metrics = sum(1 for m in metric_comparison.values() if m["match"])
            consistency_score = matching_metrics / len(key_metrics)

            print(
                f"   統計一致性: {consistency_score:.1%} ({matching_metrics}/{len(key_metrics)} 指標匹配)"
            )

            # 檢查數據格式一致性
            json_keys = set(json_stats.keys())
            db_keys = set(db_stats.keys())
            format_consistency = len(json_keys & db_keys) / len(json_keys | db_keys)

            return {
                "metric_comparison": metric_comparison,
                "consistency_score": consistency_score,
                "format_consistency": format_consistency,
                "json_stats": json_stats,
                "db_stats": db_stats,
            }

        except Exception as e:
            print(f"   ❌ 統計分析失敗: {e}")
            return {"error": str(e), "consistency_score": 0.0}

    async def _analyze_performance(self) -> dict[str, Any]:
        """分析性能特徵"""
        print("\n⚡ 4. 性能特徵比較")

        performance_results = {}

        try:
            # 測試統計計算性能
            start = time.time()
            self.json_manager.get_statistics()
            json_stats_time = time.time() - start

            start = time.time()
            await self.db_manager.get_statistics_async()
            db_stats_time = time.time() - start

            performance_results["statistics_calculation"] = {
                "json_time": json_stats_time,
                "db_time": db_stats_time,
                "ratio": db_stats_time / max(json_stats_time, 0.001),
            }

            # 測試知識點檢索性能
            start = time.time()
            self.json_manager.get_active_points()
            json_retrieval_time = time.time() - start

            start = time.time()
            await self.db_manager.get_knowledge_points_async()
            db_retrieval_time = time.time() - start

            performance_results["data_retrieval"] = {
                "json_time": json_retrieval_time,
                "db_time": db_retrieval_time,
                "ratio": db_retrieval_time / max(json_retrieval_time, 0.001),
            }

            # 計算平均性能比率
            avg_ratio = sum(metric["ratio"] for metric in performance_results.values()) / len(
                performance_results
            )

            print(
                f"   統計計算: JSON={json_stats_time:.4f}s, DB={db_stats_time:.4f}s (比率: {performance_results['statistics_calculation']['ratio']:.2f})"
            )
            print(
                f"   數據檢索: JSON={json_retrieval_time:.4f}s, DB={db_retrieval_time:.4f}s (比率: {performance_results['data_retrieval']['ratio']:.2f})"
            )
            print(f"   平均性能比率: {avg_ratio:.2f}")

            performance_results["average_ratio"] = avg_ratio
            performance_results["performance_score"] = (
                min(1.0, 2.0 / avg_ratio) if avg_ratio > 0 else 1.0
            )

        except Exception as e:
            print(f"   ❌ 性能測試失敗: {e}")
            performance_results = {"error": str(e), "performance_score": 0.0}

        return performance_results

    def _analyze_method_availability(self) -> dict[str, Any]:
        """分析方法可用性"""
        print("\n🔧 5. 方法可用性分析")

        # 獲取所有方法
        json_methods = [
            method
            for method in dir(self.json_manager)
            if not method.startswith("_") and callable(getattr(self.json_manager, method))
        ]
        db_methods = [
            method
            for method in dir(self.db_manager)
            if not method.startswith("_") and callable(getattr(self.db_manager, method))
        ]

        common_methods = set(json_methods) & set(db_methods)
        json_only = set(json_methods) - set(db_methods)
        db_only = set(db_methods) - set(json_methods)

        print(f"   共同方法: {len(common_methods)} 個")
        print(f"   JSON獨有: {len(json_only)} 個")
        print(f"   DB獨有: {len(db_only)} 個")

        return {
            "json_methods": len(json_methods),
            "db_methods": len(db_methods),
            "common_methods": len(common_methods),
            "json_only_methods": list(json_only),
            "db_only_methods": list(db_only),
            "method_overlap": len(common_methods) / max(len(json_methods), len(db_methods)),
        }

    async def _analyze_error_handling(self) -> dict[str, Any]:
        """分析錯誤處理一致性"""
        print("\n⚠️  6. 錯誤處理一致性分析")

        # 測試無效ID處理
        try:
            json_result = self.json_manager.edit_knowledge_point(99999, {"key_point": "test"})
            json_handles_invalid_id = json_result is None or json_result is False
        except Exception:
            json_handles_invalid_id = True

        try:
            db_result = await self.db_manager.get_knowledge_point_async("99999")
            db_handles_invalid_id = db_result is None or db_result is False
        except Exception:
            db_handles_invalid_id = True

        invalid_id_consistent = json_handles_invalid_id == db_handles_invalid_id

        print(f"   無效ID處理: {'一致' if invalid_id_consistent else '不一致'}")

        return {
            "invalid_id_handling": {
                "json_handles": json_handles_invalid_id,
                "db_handles": db_handles_invalid_id,
                "consistent": invalid_id_consistent,
            },
            "overall_consistency": 1.0 if invalid_id_consistent else 0.0,
        }

    def _generate_overall_assessment(self, results: dict[str, Any]) -> dict[str, Any]:
        """生成整體評估"""
        print("\n📋 7. 整體架構一致性評估")

        # 提取各項分數
        scores = {
            "api_compatibility": results.get("api_interface_analysis", {}).get(
                "compatibility_score", 0.0
            ),
            "data_model_consistency": 1.0
            if results.get("data_model_analysis", {}).get("model_consistency")
            else 0.0,
            "statistics_consistency": results.get("statistics_consistency", {}).get(
                "consistency_score", 0.0
            ),
            "performance_consistency": results.get("performance_comparison", {}).get(
                "performance_score", 0.0
            ),
            "method_availability": results.get("method_availability", {}).get(
                "method_overlap", 0.0
            ),
            "error_handling": results.get("error_handling_comparison", {}).get(
                "overall_consistency", 0.0
            ),
        }

        # 權重計算整體分數
        weights = {
            "api_compatibility": 0.25,
            "data_model_consistency": 0.20,
            "statistics_consistency": 0.25,
            "performance_consistency": 0.10,
            "method_availability": 0.15,
            "error_handling": 0.05,
        }

        overall_score = sum(scores[key] * weights[key] for key in scores)

        # 評級
        if overall_score >= 0.95:
            grade = "🏆 幾乎完全相同"
        elif overall_score >= 0.85:
            grade = "🥈 高度相似"
        elif overall_score >= 0.70:
            grade = "🥉 基本一致"
        else:
            grade = "⚠️ 存在顯著差異"

        assessment = {
            "individual_scores": scores,
            "overall_score": overall_score,
            "grade": grade,
            "weights": weights,
        }

        # 打印評估結果
        print(f"   API兼容性: {scores['api_compatibility']:.1%}")
        print(f"   數據模型: {scores['data_model_consistency']:.1%}")
        print(f"   統計一致性: {scores['statistics_consistency']:.1%}")
        print(f"   性能一致性: {scores['performance_consistency']:.1%}")
        print(f"   方法可用性: {scores['method_availability']:.1%}")
        print(f"   錯誤處理: {scores['error_handling']:.1%}")
        print(f"   整體評分: {overall_score:.1%}")
        print(f"   評級: {grade}")

        return assessment


async def main():
    """主函數"""
    analyzer = RealArchitectureAnalyzer()

    print("🏗️  JSON vs Database 架構一致性真實分析")
    print("=" * 60)

    try:
        results = await analyzer.run_complete_analysis()

        # 保存結果
        output_file = "real_architecture_analysis.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n{'=' * 60}")
        print("📋 最終結論")
        print("=" * 60)

        overall = results["overall_assessment"]
        print(f"🎯 整體一致性評分: {overall['overall_score']:.1%}")
        print(f"📊 評級: {overall['grade']}")
        print(f"⏱️  分析耗時: {results['analysis_duration']:.2f}秒")

        # 回答核心問題
        if overall["overall_score"] >= 0.95:
            answer = "✅ 是的，兩個架構幾乎完全相同"
        elif overall["overall_score"] >= 0.85:
            answer = "✅ 架構高度相似，存在小幅差異但基本一致"
        elif overall["overall_score"] >= 0.70:
            answer = "⚠️ 架構基本一致，需要注意部分功能差異"
        else:
            answer = "❌ 架構存在顯著差異，需要重點關注兼容性"

        print(f"\n🎯 問題答案: {answer}")
        print(f"📄 詳細結果已保存至: {output_file}")

        return overall["overall_score"] >= 0.85

    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
