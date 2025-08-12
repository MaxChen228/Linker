"""
DTO 系統使用範例

展示如何正確使用數據傳輸對象進行類型安全的數據處理。
這些範例可以作為開發參考。
"""

from datetime import datetime, timedelta
from typing import List

from .common import KnowledgePointData, PracticeRecordData, ErrorData, FeedbackData
from .requests import SaveMistakeRequest, GetKnowledgePointsRequest, UpdateMasteryRequest
from .responses import SaveMistakeResponse, KnowledgePointsResponse


def example_save_mistake_workflow():
    """範例：保存錯誤的完整工作流程"""
    
    # 1. 創建保存錯誤請求
    request = SaveMistakeRequest(
        chinese_sentence="我昨天去了圖書館",
        user_answer="I go to library yesterday",
        feedback={
            "overall_score": 65,
            "is_correct": False,
            "errors": [
                {
                    "type": "grammar",
                    "category": "systematic",
                    "description": "時態錯誤",
                    "user_text": "I go",
                    "correct_text": "I went",
                    "explanation": "過去時間應使用過去式"
                },
                {
                    "type": "grammar", 
                    "category": "individual",
                    "description": "冠詞遺漏",
                    "user_text": "to library",
                    "correct_text": "to the library",
                    "explanation": "特定場所前需要定冠詞"
                }
            ]
        },
        practice_mode="new",
        duration_seconds=45
    )
    
    # 2. 驗證請求
    if not request.validate():
        print("請求驗證失敗")
        return None
    
    # 3. 模擬處理後創建響應
    response = SaveMistakeResponse(
        success=True,
        message="錯誤保存成功",
        practice_record_id="practice_001",
        knowledge_points_created=["tense_past_simple", "article_definite"],
        knowledge_points_updated=[],
        errors_processed=2
    )
    
    print("範例 1: 保存錯誤工作流程")
    print(f"- 請求有效: {request.validate()}")
    print(f"- 處理成功: {response.success}")
    print(f"- 創建知識點: {len(response.knowledge_points_created)}")
    print(f"- 處理錯誤數: {response.errors_processed}")
    
    return response


def example_knowledge_points_query():
    """範例：知識點查詢工作流程"""
    
    # 1. 創建查詢請求
    request = GetKnowledgePointsRequest(
        category="grammar",
        difficulty="medium",
        mastery_threshold=0.7,
        limit=10,
        sort_by="mastery_level",
        sort_order="asc",
        include_examples=True
    )
    
    # 2. 驗證請求
    if not request.validate():
        print("查詢請求驗證失敗")
        return None
    
    # 3. 模擬創建一些知識點數據
    knowledge_points = [
        KnowledgePointData(
            id="tense_past_simple",
            name="過去簡單式",
            category="grammar",
            description="表示過去完成的動作",
            examples=["I went to school", "She studied last night"],
            correct_count=3,
            error_count=7,
            mastery_level=0.3,
            difficulty="medium"
        ),
        KnowledgePointData(
            id="article_definite",
            name="定冠詞使用",
            category="grammar", 
            description="the 的正確使用時機",
            examples=["the library", "the first time"],
            correct_count=5,
            error_count=5,
            mastery_level=0.5,
            difficulty="medium"
        )
    ]
    
    # 4. 創建響應
    response = KnowledgePointsResponse(
        success=True,
        message="查詢完成",
        knowledge_points=knowledge_points,
        total_count=2,
        page_info={
            "current_page": 1,
            "total_pages": 1,
            "has_next": False,
            "has_previous": False
        },
        filters_applied=request.to_dict()
    )
    
    print("\n範例 2: 知識點查詢工作流程")
    print(f"- 請求有效: {request.validate()}")
    print(f"- 查詢成功: {response.success}")
    print(f"- 返回結果數: {len(response.knowledge_points)}")
    print(f"- 總數量: {response.total_count}")
    
    # 5. 展示知識點詳細資訊
    for kp in response.knowledge_points:
        print(f"  * {kp.name}: 掌握度 {kp.mastery_level:.1f} ({kp.correct_count}對/{kp.error_count}錯)")
    
    return response


def example_error_data_processing():
    """範例：錯誤數據處理"""
    
    # 1. 創建錯誤數據
    errors = [
        ErrorData(
            id="error_001",
            type="grammar",
            category="systematic", 
            description="時態使用錯誤",
            user_text="I go to school yesterday",
            correct_text="I went to school yesterday",
            explanation="過去時間標記要求使用過去式",
            severity="high",
            confidence=0.95
        ),
        ErrorData(
            id="error_002",
            type="vocabulary",
            category="individual",
            description="介詞選擇錯誤", 
            user_text="depend of",
            correct_text="depend on",
            explanation="depend 後面應該接 on",
            severity="medium",
            confidence=0.85
        )
    ]
    
    # 2. 驗證錯誤數據
    print("\n範例 3: 錯誤數據處理")
    for i, error in enumerate(errors):
        print(f"- 錯誤 {i+1} 驗證: {error.validate()}")
        print(f"  類型: {error.type}, 嚴重度: {error.severity}")
        print(f"  置信度: {error.confidence}")
    
    # 3. 展示序列化
    print("\n錯誤數據序列化範例:")
    error_dict = errors[0].to_dict()
    print(f"- 字典鍵值: {list(error_dict.keys())}")
    
    # 4. 展示反序列化
    reconstructed_error = ErrorData.from_dict(error_dict)
    print(f"- 重建成功: {reconstructed_error.id == errors[0].id}")
    
    return errors


def example_practice_record():
    """範例：練習記錄數據"""
    
    # 1. 創建練習記錄
    practice_record = PracticeRecordData(
        id="practice_001",
        timestamp=datetime.now(),
        chinese_sentence="我喜歡讀書",
        user_answer="I like read books",
        correct_answer="I like reading books",
        practice_mode="new",
        is_correct=False,
        score=75.0,
        duration_seconds=30,
        errors_found=["gerund_usage"],
        knowledge_points_used=["verb_like", "gerund_infinitive"],
        feedback={
            "main_issue": "動名詞使用",
            "suggestion": "like 後面接動名詞 -ing 形式"
        }
    )
    
    # 2. 驗證和展示
    print("\n範例 4: 練習記錄")
    print(f"- 記錄驗證: {practice_record.validate()}")
    print(f"- 練習模式: {practice_record.practice_mode}")
    print(f"- 分數: {practice_record.score}")
    print(f"- 耗時: {practice_record.duration_seconds}秒")
    print(f"- 涉及知識點: {len(practice_record.knowledge_points_used)}")
    
    return practice_record


def main():
    """執行所有範例"""
    print("=== DTO 系統使用範例 ===")
    
    # 執行各個範例
    example_save_mistake_workflow()
    example_knowledge_points_query()
    example_error_data_processing()
    example_practice_record()
    
    print("\n=== 範例執行完成 ===")
    print("所有 DTO 對象都支援:")
    print("- 數據驗證 (validate() 方法)")
    print("- 序列化 (to_dict() 方法)")
    print("- 反序列化 (from_dict() 類方法)")
    print("- 類型提示和自動完成")
    print("- 默認值和可選參數")


if __name__ == "__main__":
    main()