"""
Repository Mock 實現
模擬數據訪問層的各種行為和狀態
"""

from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock
from datetime import datetime
import uuid

from core.knowledge import KnowledgePoint, OriginalError, ReviewExample
from core.response import APIResponse
from tests.factories.knowledge_factory import (
    create_knowledge_points_for_review,
    create_mastered_knowledge_points,
    KnowledgePointFactory
)
from tests.factories.practice_factory import (
    PracticeRecordFactory,
    create_practice_history
)


class MockKnowledgeRepository:
    """知識點 Repository Mock 實現"""
    
    def __init__(self, initial_data: Optional[List[KnowledgePoint]] = None):
        self.knowledge_points: Dict[str, KnowledgePoint] = {}
        self.operation_history: List[Dict[str, Any]] = []
        self.save_error_rate = 0.0  # 保存錯誤率
        self.load_error_rate = 0.0  # 載入錯誤率
        
        # 初始化數據
        if initial_data:
            for kp in initial_data:
                self.knowledge_points[str(kp.id)] = kp
    
    def load_all(self) -> List[KnowledgePoint]:
        """載入所有知識點"""
        self._record_operation("load_all")
        
        if self._should_error("load"):
            return []
        
        return list(self.knowledge_points.values())
    
    def get_by_id(self, knowledge_point_id: Union[str, int]) -> Optional[KnowledgePoint]:
        """根據 ID 獲取知識點"""
        self._record_operation("get_by_id", {"id": knowledge_point_id})
        
        if self._should_error("load"):
            return None
        
        return self.knowledge_points.get(str(knowledge_point_id))
    
    def save(self, knowledge_point: KnowledgePoint) -> APIResponse:
        """保存知識點"""
        self._record_operation("save", {"id": knowledge_point.id})
        
        if self._should_error("save"):
            return APIResponse(success=False, message="保存失敗：模擬錯誤")
        
        # 更新時間戳
        knowledge_point.last_seen = datetime.now().isoformat()
        self.knowledge_points[str(knowledge_point.id)] = knowledge_point
        
        return APIResponse(success=True, message="保存成功")
    
    def delete(self, knowledge_point_id: str) -> APIResponse:
        """刪除知識點"""
        self._record_operation("delete", {"id": knowledge_point_id})
        
        if knowledge_point_id not in self.knowledge_points:
            return APIResponse(success=False, message=f"知識點不存在：{knowledge_point_id}")
        
        del self.knowledge_points[knowledge_point_id]
        return APIResponse(success=True, message="刪除成功")
    
    def find_by_tags(self, tags: List[str]) -> List[KnowledgePoint]:
        """根據標籤查找知識點"""
        self._record_operation("find_by_tags", {"tags": tags})
        
        results = []
        for kp in self.knowledge_points.values():
            if any(tag in kp.tags for tag in tags):
                results.append(kp)
        
        return results
    
    def find_by_category(self, category: str) -> List[KnowledgePoint]:
        """根據分類查找知識點"""
        self._record_operation("find_by_category", {"category": category})
        
        return [kp for kp in self.knowledge_points.values() 
                if kp.error_category == category]
    
    def get_review_candidates(self, limit: int = 10) -> List[KnowledgePoint]:
        """獲取需要複習的知識點"""
        self._record_operation("get_review_candidates", {"limit": limit})
        
        # 模擬複習算法：返回掌握度最低的知識點
        candidates = sorted(
            self.knowledge_points.values(),
            key=lambda x: (x.mastery_level, x.last_seen)
        )
        
        return candidates[:limit]
    
    def update_mastery(self, knowledge_point_id: str, is_correct: bool) -> APIResponse:
        """更新掌握度"""
        self._record_operation("update_mastery", {
            "id": knowledge_point_id, 
            "is_correct": is_correct
        })
        
        kp = self.knowledge_points.get(knowledge_point_id)
        if not kp:
            return APIResponse(success=False, message=f"知識點不存在：{knowledge_point_id}")
        
        # 更新統計
        if is_correct:
            kp.correct_count += 1
        else:
            kp.mistake_count += 1
        
        # 重新計算掌握度
        total = kp.correct_count + kp.mistake_count
        kp.mastery_level = kp.correct_count / total if total > 0 else 0.0
        kp.last_seen = datetime.now().isoformat()
        
        return APIResponse(success=True, message="掌握度更新成功")
    
    def _record_operation(self, operation: str, params: Optional[Dict] = None):
        """記錄操作歷史"""
        self.operation_history.append({
            "operation": operation,
            "params": params or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def _should_error(self, operation_type: str) -> bool:
        """根據錯誤率決定是否應該出錯"""
        import random
        error_rate = self.save_error_rate if operation_type == "save" else self.load_error_rate
        return random.random() < error_rate
    
    def set_error_rate(self, save_error_rate: float = 0.0, load_error_rate: float = 0.0):
        """設置錯誤率"""
        self.save_error_rate = save_error_rate
        self.load_error_rate = load_error_rate
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        total_ops = len(self.operation_history)
        op_counts = {}
        
        for op in self.operation_history:
            op_type = op["operation"]
            op_counts[op_type] = op_counts.get(op_type, 0) + 1
        
        return {
            "total_knowledge_points": len(self.knowledge_points),
            "total_operations": total_ops,
            "operation_counts": op_counts,
            "recent_operations": self.operation_history[-5:],
            "error_rates": {
                "save": self.save_error_rate,
                "load": self.load_error_rate
            }
        }
    
    def clear(self):
        """清空所有數據"""
        self.knowledge_points.clear()
        self.operation_history.clear()


class MockPracticeRepository:
    """練習記錄 Repository Mock 實現"""
    
    def __init__(self, initial_records: Optional[List[Dict[str, Any]]] = None):
        self.practice_records: List[Dict[str, Any]] = initial_records or []
        self.operation_history: List[Dict[str, Any]] = []
        self.save_error_rate = 0.0
    
    def load_all(self) -> List[Dict[str, Any]]:
        """載入所有練習記錄"""
        self._record_operation("load_all")
        return self.practice_records.copy()
    
    def save_record(self, record: Dict[str, Any]) -> APIResponse:
        """保存練習記錄"""
        self._record_operation("save_record", {"id": record.get("id")})
        
        if self._should_error():
            return APIResponse(success=False, message="保存記錄失敗：模擬錯誤")
        
        # 添加 ID 和時間戳
        if "id" not in record:
            record["id"] = str(uuid.uuid4())
        
        if "timestamp" not in record:
            record["timestamp"] = datetime.now().isoformat()
        
        self.practice_records.append(record.copy())
        return APIResponse(success=True, message="記錄保存成功")
    
    def get_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根據會話 ID 獲取記錄"""
        self._record_operation("get_by_session", {"session_id": session_id})
        
        return [record for record in self.practice_records 
                if record.get("session_id") == session_id]
    
    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """根據日期範圍獲取記錄"""
        self._record_operation("get_by_date_range", {
            "start_date": start_date, 
            "end_date": end_date
        })
        
        results = []
        for record in self.practice_records:
            timestamp = record.get("timestamp", "")
            if start_date <= timestamp <= end_date:
                results.append(record)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取練習統計"""
        if not self.practice_records:
            return {
                "total_records": 0,
                "correct_count": 0,
                "accuracy": 0.0,
                "avg_score": 0.0
            }
        
        total = len(self.practice_records)
        correct = sum(1 for r in self.practice_records if r.get("is_correct", False))
        total_score = sum(r.get("score", 0) for r in self.practice_records)
        
        return {
            "total_records": total,
            "correct_count": correct,
            "accuracy": correct / total,
            "avg_score": total_score / total
        }
    
    def _record_operation(self, operation: str, params: Optional[Dict] = None):
        """記錄操作歷史"""
        self.operation_history.append({
            "operation": operation,
            "params": params or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def _should_error(self) -> bool:
        """根據錯誤率決定是否出錯"""
        import random
        return random.random() < self.save_error_rate
    
    def set_error_rate(self, error_rate: float):
        """設置錯誤率"""
        self.save_error_rate = error_rate
    
    def clear(self):
        """清空所有記錄"""
        self.practice_records.clear()
        self.operation_history.clear()


def create_mock_knowledge_repository(scenario: str = "normal") -> MockKnowledgeRepository:
    """
    創建不同場景的知識點 Repository Mock
    
    Args:
        scenario: 場景類型 ("empty", "normal", "review_heavy", "mastered", "error_prone")
    """
    if scenario == "empty":
        return MockKnowledgeRepository()
    
    elif scenario == "normal":
        # 混合狀態的知識點
        kps = KnowledgePointFactory.build_batch(10)
        repo = MockKnowledgeRepository(kps)
        return repo
    
    elif scenario == "review_heavy":
        # 大量需要複習的知識點
        kps = create_knowledge_points_for_review(15)
        kps.extend(create_mastered_knowledge_points(5))
        repo = MockKnowledgeRepository(kps)
        return repo
    
    elif scenario == "mastered":
        # 大部分已掌握的知識點
        kps = create_mastered_knowledge_points(20)
        kps.extend(create_knowledge_points_for_review(3))
        repo = MockKnowledgeRepository(kps)
        return repo
    
    elif scenario == "error_prone":
        # 容易出錯的 Repository
        repo = MockKnowledgeRepository()
        repo.set_error_rate(save_error_rate=0.3, load_error_rate=0.1)
        return repo
    
    else:
        return MockKnowledgeRepository()


class MockKnowledgeManager:
    """知識點管理器 Mock 實現"""
    
    def __init__(self, initial_data: Optional[List[KnowledgePoint]] = None):
        self.knowledge_points: List[KnowledgePoint] = initial_data or []
        self.practice_history: List[Dict[str, Any]] = []
        self.operation_history: List[Dict[str, Any]] = []
        
    def get_knowledge_points(self) -> List[KnowledgePoint]:
        """獲取所有知識點"""
        self._record_operation("get_knowledge_points")
        return self.knowledge_points.copy()
    
    def get_knowledge_point_by_id(self, kp_id: int) -> Optional[KnowledgePoint]:
        """根據 ID 獲取知識點"""
        self._record_operation("get_knowledge_point_by_id", {"id": kp_id})
        for kp in self.knowledge_points:
            if kp.id == kp_id:
                return kp
        return None
    
    def add_knowledge_point(self, knowledge_point: KnowledgePoint) -> bool:
        """添加知識點"""
        self._record_operation("add_knowledge_point", {"id": knowledge_point.id})
        self.knowledge_points.append(knowledge_point)
        return True
    
    def update_mastery(self, kp_id: int, is_correct: bool) -> bool:
        """更新掌握度"""
        self._record_operation("update_mastery", {"id": kp_id, "is_correct": is_correct})
        
        for kp in self.knowledge_points:
            if kp.id == kp_id:
                if is_correct:
                    kp.correct_count += 1
                else:
                    kp.mistake_count += 1
                
                total = kp.correct_count + kp.mistake_count
                kp.mastery_level = kp.correct_count / total if total > 0 else 0.0
                kp.last_seen = datetime.now().isoformat()
                return True
        
        return False
    
    def get_review_candidates(self, limit: int = 10) -> List[KnowledgePoint]:
        """獲取需要複習的知識點"""
        self._record_operation("get_review_candidates", {"limit": limit})
        
        # 根據掌握度和最後見到時間排序
        candidates = sorted(
            self.knowledge_points,
            key=lambda x: (x.mastery_level, x.last_seen)
        )
        
        return candidates[:limit]
    
    def save_mistake(self, mistake_data: Dict[str, Any]) -> Dict[str, Any]:
        """保存錯誤（模擬）"""
        self._record_operation("save_mistake", mistake_data)
        
        # 創建新的知識點
        new_id = max([kp.id for kp in self.knowledge_points], default=0) + 1
        
        # 返回模擬的保存結果
        return {
            "success": True,
            "knowledge_point_id": new_id,
            "message": "錯誤已保存"
        }
    
    def log_practice(self, practice_data: Dict[str, Any]):
        """記錄練習歷史"""
        self._record_operation("log_practice", practice_data)
        self.practice_history.append({
            **practice_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def _record_operation(self, operation: str, params: Optional[Dict] = None):
        """記錄操作歷史"""
        self.operation_history.append({
            "operation": operation,
            "params": params or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def clear(self):
        """清空所有數據"""
        self.knowledge_points.clear()
        self.practice_history.clear()
        self.operation_history.clear()


def create_mock_practice_repository(scenario: str = "normal") -> MockPracticeRepository:
    """
    創建不同場景的練習記錄 Repository Mock
    
    Args:
        scenario: 場景類型 ("empty", "normal", "rich_history", "error_prone")
    """
    if scenario == "empty":
        return MockPracticeRepository()
    
    elif scenario == "normal":
        records = PracticeRecordFactory.build_batch(20)
        return MockPracticeRepository(records)
    
    elif scenario == "rich_history":
        # 豐富的歷史記錄
        records = create_practice_history(days=30)
        return MockPracticeRepository(records)
    
    elif scenario == "error_prone":
        repo = MockPracticeRepository()
        repo.set_error_rate(0.2)
        return repo
    
    else:
        return MockPracticeRepository()