"""
Practice routes for the Linker web application. (Refactored for API-first approach)
"""

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

# TASK-34: 引入統一API端點管理系統，消除硬編碼
from web.config.api_endpoints import API_ENDPOINTS
from web.dependencies import (
    get_ai_service,
    get_know_service,  # TASK-31: 使用新的純異步服務
    get_knowledge_assets,
    get_logger,
    get_templates,
)
from web.models.validation import (
    ConfirmKnowledgeRequest,
    GenerateQuestionRequest,
    GradeAnswerRequest,
)

router = APIRouter()
logger = get_logger()


def create_transparent_error_response(
    error_message: str, 
    error_code: str = "UNKNOWN_ERROR", 
    details: dict = None,
    status_code: int = 500
) -> JSONResponse:
    """
    🔥 透明化改造：統一的錯誤響應格式
    
    確保所有錯誤都被透明地報告，不隱藏任何信息！
    """
    error_response = {
        "success": False,
        "error": error_message,
        "error_code": error_code,
        "timestamp": datetime.now().isoformat(),
        "details": details or {},
        "transparency_note": "此錯誤經過透明化改造，真實反映系統狀態"
    }
    
    logger.error(f"透明錯誤報告 [{error_code}]: {error_message}")
    if details:
        logger.error(f"錯誤詳情: {details}")
        
    return JSONResponse(error_response, status_code=status_code)


@router.get("/practice", response_class=HTMLResponse)
def practice_page(request: Request):
    """
    練習頁面（GET）。
    只回傳靜態的 HTML 骨架，所有動態內容由前端 JavaScript 處理。
    """
    templates = get_templates()
    return templates.TemplateResponse(
        "practice.html",
        {
            "request": request,
            "active": "practice",
            # 不再需要傳遞題目、模式、難度等任何動態資料
        },
    )


# --------------------------------------------------------------------------
# API Endpoints - 以下 API 保持不變，它們是新架構的基石
# --------------------------------------------------------------------------


@router.post(API_ENDPOINTS.GRADE_ANSWER, response_class=JSONResponse)
async def grade_answer_api(request: GradeAnswerRequest):
    """API 端點：批改答案"""
    import os

    # Read configuration dynamically to allow runtime changes
    auto_save_knowledge_points = os.getenv("AUTO_SAVE_KNOWLEDGE_POINTS", "false").lower() == "true"
    show_confirmation_ui = os.getenv("SHOW_CONFIRMATION_UI", "true").lower() == "true"
    import uuid

    ai = get_ai_service()
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    try:
        # 輸入已通過 Pydantic 驗證
        chinese = request.chinese
        english = request.english
        mode = request.mode
        target_point_ids = request.target_point_ids

        # 1. 使用 AI 進行批改
        result = ai.grade_translation(chinese=chinese, english=english)

        # 檢查 AI 服務是否真的成功（檢測 fallback response）
        if result.get("service_error") or "AI 服務暫時不可用" in result.get(
            "overall_suggestion", ""
        ):
            logger.warning("AI service unavailable, returning error response")
            return JSONResponse(
                {
                    "success": False,
                    "error": "AI 批改服務暫時不可用，請稍後再試",
                    "score": 0,
                    "is_generally_correct": False,
                    "feedback": "服務暫時無法使用",
                    "error_analysis": [],
                }
            )

        # 2. 更新知識點掌握度（如果是複習模式）
        is_correct = result.get("is_generally_correct", False)
        if mode == "review" and target_point_ids:
            for point_id in target_point_ids:
                await knowledge.update_knowledge_point(point_id, is_correct)  # TASK-31: 添加 await

        # 3. 根據配置決定是自動保存還是返回待確認點
        pending_knowledge_points = []
        
        # 🔥 修復核心邏輯：只要有錯誤分析，就應該讓用戶選擇是否保存知識點
        # 不再依賴 is_correct，因為 AI 可能判斷「大致正確」但仍有可學習的錯誤
        error_analysis = result.get("error_analysis", [])
        
        if error_analysis:  # 改為：只要有錯誤分析就生成待確認點
            if auto_save_knowledge_points:
                # 舊邏輯：自動保存錯誤記錄
                if hasattr(knowledge, "_save_mistake_async"):
                    await knowledge._save_mistake_async(
                        chinese_sentence=chinese,
                        user_answer=english,
                        feedback=result,
                        practice_mode=mode,
                    )
                else:
                    knowledge.save_mistake(
                        chinese_sentence=chinese,
                        user_answer=english,
                        feedback=result,
                        practice_mode=mode,
                    )
            else:
                # 新邏輯：生成待確認的知識點數據
                for error in error_analysis:
                    pending_knowledge_points.append(
                        {
                            "id": f"temp_{uuid.uuid4().hex[:8]}",
                            "error": error,
                            "chinese_sentence": chinese,
                            "user_answer": english,
                            "correct_answer": result.get("overall_suggestion", ""),
                        }
                    )

        # 4. 如果是複習模式且答對，也記錄下來（獨立於錯誤分析）
        if mode == "review" and target_point_ids and is_correct:
            for point_id in target_point_ids:
                # 使用異步方法
                if hasattr(knowledge, "add_review_success_async"):
                    await knowledge.add_review_success_async(
                        knowledge_point_id=point_id, chinese_sentence=chinese, user_answer=english
                    )
                else:
                    knowledge.add_review_success(
                        knowledge_point_id=point_id, chinese_sentence=chinese, user_answer=english
                    )

        # 5. 計算分數
        score = 100
        for error in error_analysis:
            category = error.get("category", "other")
            if category == "systematic":
                score -= 15
            elif category == "isolated":
                score -= 10
            elif category == "enhancement":
                score -= 5
            else:
                score -= 8
        score = max(0, min(100, score))

        # 6. 回傳完整結果
        response_data = {
            "success": True,
            "score": score,
            "is_generally_correct": is_correct,
            "feedback": result.get("overall_suggestion", ""),
            "error_analysis": error_analysis,  # 使用已提取的變數
            "detailed_feedback": result.get("detailed_feedback", ""),
        }

        # 🔥 詳細調試信息
        logger.info(f"🔍 Environment Variables:")
        logger.info(f"   SHOW_CONFIRMATION_UI: {os.getenv('SHOW_CONFIRMATION_UI', 'not set')} -> {show_confirmation_ui}")
        logger.info(f"   AUTO_SAVE_KNOWLEDGE_POINTS: {os.getenv('AUTO_SAVE_KNOWLEDGE_POINTS', 'not set')} -> {auto_save_knowledge_points}")
        
        logger.info(f"🔍 Data Analysis:")
        logger.info(f"   Error analysis count: {len(error_analysis)}")
        logger.info(f"   Error analysis content: {[e.get('key_point_summary', 'no summary') for e in error_analysis]}")
        logger.info(f"   Pending points count: {len(pending_knowledge_points)}")
        
        logger.info(f"🔍 Condition Check:")
        logger.info(f"   show_confirmation_ui: {show_confirmation_ui}")
        logger.info(f"   not auto_save_knowledge_points: {not auto_save_knowledge_points}")
        logger.info(f"   Combined condition: {show_confirmation_ui and not auto_save_knowledge_points}")

        if show_confirmation_ui and not auto_save_knowledge_points:
            response_data["pending_knowledge_points"] = pending_knowledge_points
            response_data["auto_save"] = False
            logger.info(f"🔍 -> Using confirmation UI mode, pending_points added: {len(pending_knowledge_points)}")
        else:
            response_data["auto_save"] = auto_save_knowledge_points
            logger.info(f"🔍 -> Using auto_save mode: {auto_save_knowledge_points}")

        return JSONResponse(response_data)

    except Exception as e:
        logger.error(f"Error in grade_answer_api: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": "批改時發生內部錯誤"}, status_code=500)


@router.post(API_ENDPOINTS.CONFIRM_KNOWLEDGE, response_class=JSONResponse)
async def confirm_knowledge_points(request: ConfirmKnowledgeRequest):
    """API 端點：確認並保存選中的知識點"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    try:
        confirmed_ids = []

        for point_data in request.confirmed_points:
            # 為每個錯誤創建知識點
            error = point_data.error

            # 調用現有的 _process_error 邏輯或直接添加知識點
            if hasattr(knowledge, "add_knowledge_point_from_error"):
                point_id = await knowledge.add_knowledge_point_from_error(  # TASK-31: 添加 await
                    chinese_sentence=point_data.chinese_sentence,
                    user_answer=point_data.user_answer,
                    error=error,
                    correct_answer=point_data.correct_answer,
                )
            else:
                # 如果方法不存在，使用現有的添加知識點邏輯
                from datetime import datetime

                from core.knowledge import KnowledgePoint

                point = KnowledgePoint(
                    id=knowledge._get_next_id()
                    if hasattr(knowledge, "_get_next_id")
                    else len(knowledge.knowledge_points) + 1,
                    key_point=error.get("key_point_summary", "未知錯誤"),
                    original_phrase=error.get("original_phrase", point_data.user_answer),
                    correction=error.get("correction", point_data.correct_answer),
                    explanation=error.get("explanation", ""),
                    category=error.get("category", "other"),
                    subtype=error.get("subtype", "general"),
                    mastery_level=0.1,
                    mistake_count=1,
                    correct_count=0,
                    last_seen=datetime.now().isoformat(),
                    next_review=datetime.now().isoformat(),
                    created_at=datetime.now().isoformat(),
                    original_error={
                        "chinese_sentence": point_data.chinese_sentence,
                        "user_answer": point_data.user_answer,
                        "correct_answer": point_data.correct_answer,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                if hasattr(knowledge, "knowledge_points"):
                    knowledge.knowledge_points.append(point)
                    point_id = point.id
                else:
                    # 使用適配器的方法
                    point_id = await knowledge.add_knowledge_point_async(point)

            confirmed_ids.append(point_id)

        logger.info(f"Confirmed {len(confirmed_ids)} knowledge points: {confirmed_ids}")

        return JSONResponse(
            {"success": True, "confirmed_count": len(confirmed_ids), "point_ids": confirmed_ids}
        )

    except Exception as e:
        logger.error(f"Error in confirm_knowledge_points: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": "確認知識點時發生錯誤"}, status_code=500)


@router.post(API_ENDPOINTS.GENERATE_QUESTION, response_class=JSONResponse)
async def generate_question_api(request: GenerateQuestionRequest):
    """API 端點：生成單個題目（支援並行調用）"""
    ai = get_ai_service()
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務
    assets = get_knowledge_assets()

    try:
        # 輸入已通過 Pydantic 驗證
        mode = request.mode
        length = request.length
        level = request.level
        pattern_id = request.pattern_id

        logger.info(
            f"API: Generating question - mode={mode}, length={length}, level={level}, pattern_id={pattern_id}"
        )

        if mode == "review":
            review_points = await knowledge.get_review_candidates(
                max_points=5
            )  # TASK-31: 添加 await
            if not review_points:
                return JSONResponse({"success": False, "error": "沒有待複習的知識點"})

            payload = ai.generate_review_sentence(
                knowledge_points=review_points, level=level, length=length
            )
            
            # 🔥 透明化改造：Review 模式也不能說謊！
            if payload.get("service_error"):
                logger.error("AI 服務不可用（Review 模式），拒絕返回虛假成功")
                return JSONResponse(
                    {
                        "success": False,
                        "error": "AI 服務暫時不可用，無法生成複習題目",
                        "error_code": "AI_SERVICE_UNAVAILABLE"
                    },
                    status_code=503
                )
            
            return JSONResponse(
                {
                    "success": True,
                    "chinese": payload.get("sentence", ""),
                    "hint": payload.get("hint", ""),
                    "target_point_ids": payload.get("target_point_ids", []),
                    "target_points": payload.get("target_points", []),
                    "target_points_description": payload.get("target_points_description", ""),
                }
            )

        # 文法句型模式 - 現在支援隨機選擇
        elif mode == "pattern":
            # 載入句型資料
            enriched_file = Path("assets/patterns_enriched_complete.json")
            if not enriched_file.exists():
                return JSONResponse(
                    {"success": False, "error": "Patterns data not found."}, status_code=404
                )

            with open(enriched_file, encoding="utf-8") as f:
                patterns_data = json.load(f)
                all_patterns = patterns_data.get("patterns", patterns_data.get("data", []))

            # 如果沒有指定 pattern_id，隨機選擇一個
            if not pattern_id:
                import random

                target_pattern = random.choice(all_patterns)
                logger.info(
                    f"Randomly selected pattern: {target_pattern.get('id')} - {target_pattern.get('pattern')}"
                )
            else:
                # 尋找指定的句型
                target_pattern = next((p for p in all_patterns if p.get("id") == pattern_id), None)
                if not target_pattern:
                    return JSONResponse(
                        {"success": False, "error": "找不到指定的句型"}, status_code=404
                    )

            # 呼叫 AI Service 生成與句型相關的題目
            payload = ai.generate_sentence_for_pattern(
                pattern_data=target_pattern, level=level, length=length
            )

            # 🔥 透明化改造：Pattern 模式也不能說謊！
            if payload.get("service_error"):
                logger.error("AI 服務不可用（Pattern 模式），拒絕返回虛假成功")
                return JSONResponse(
                    {
                        "success": False,
                        "error": "AI 服務暫時不可用，無法生成句型練習",
                        "error_code": "AI_SERVICE_UNAVAILABLE"
                    },
                    status_code=503
                )

            return JSONResponse(
                {
                    "success": True,
                    "chinese": payload.get("sentence", ""),
                    "hint": f"練習句型：{target_pattern.get('pattern')}",
                    "target_point_ids": [],
                    "target_points": [],
                    "target_points_description": target_pattern.get("core_concept", ""),
                }
            )

        # 預設為新題模式
        bank = assets.get_example_bank(length=length, difficulty=level)
        payload = ai.generate_practice_sentence(
            level=level, length=length, examples=bank[:5] if bank else None
        )
        
        # 🔥 透明化改造：檢查真實的服務狀態，不再說謊！
        if payload.get("service_error"):
            logger.error("AI 服務不可用，拒絕返回虛假成功響應")
            return JSONResponse(
                {
                    "success": False,
                    "error": "AI 服務暫時不可用，請稍後再試",
                    "error_code": "AI_SERVICE_UNAVAILABLE"
                },
                status_code=503  # Service Unavailable - 誠實地報告服務問題！
            )
        
        # 只有真正成功時才返回成功響應
        return JSONResponse(
            {
                "success": True,
                "chinese": payload.get("sentence", ""),
                "hint": payload.get("hint", ""),
                "target_point_ids": [],
                "target_points": [],
                "target_points_description": "",
            }
        )

    except Exception as e:
        logger.error(f"Error in generate_question_api: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": "生成題目時發生內部錯誤"}, status_code=500)


@router.get("/api/health", response_class=JSONResponse)
async def ai_service_health_check():
    """
    🔥 透明化改造：AI 服務健康檢查端點
    
    提供真實的 AI 服務健康狀況，不再隱藏問題！
    """
    ai = get_ai_service()
    health_report = ai.health_check()
    
    # 根據真實的健康狀況返回適當的 HTTP 狀態碼
    status_code_map = {
        "healthy": 200,      # OK
        "degraded": 200,     # OK but with warnings
        "unavailable": 503,  # Service Unavailable
        "failed": 503,       # Service Unavailable
        "unknown": 500       # Internal Server Error
    }
    
    status_code = status_code_map.get(health_report["status"], 500)
    
    # 添加簡化的狀態信息用於快速檢查
    health_report["simple_status"] = {
        "is_healthy": health_report["status"] == "healthy",
        "can_generate": health_report["status"] in ["healthy", "degraded"],
        "needs_attention": health_report["status"] in ["unavailable", "failed", "unknown"]
    }
    
    logger.info(f"AI 服務健康檢查：{health_report['status']} - {health_report.get('last_error', '正常')}")
    
    return JSONResponse(health_report, status_code=status_code)


@router.get("/api/test-transparency", response_class=JSONResponse)
async def test_transparency():
    """
    🔥 透明化驗證端點
    
    這個端點證明我們的透明化改造成功：
    - 當 AI 服務失敗時，現在返回 503，不再是 200 OK
    - 錯誤信息清晰可見，不再隱藏
    """
    ai = get_ai_service()
    
    # 模擬一個可能失敗的請求
    fake_request = GenerateQuestionRequest(
        mode="new",
        length="medium", 
        level=2,
        pattern_id=None
    )
    
    # 嘗試生成問題
    try:
        payload = ai.generate_practice_sentence(
            level=fake_request.level, 
            length=fake_request.length,
            examples=["透明化測試例句"]
        )
        
        # 🔥 關鍵檢查：如果 service_error 為 True，返回真實錯誤
        if payload.get("service_error"):
            return create_transparent_error_response(
                error_message="AI 服務驗證失敗 - 透明化改造生效！",
                error_code="TRANSPARENCY_TEST_FAILED",
                details={
                    "ai_error": payload.get("error_message"),
                    "verification": "這證明系統不再隱藏 AI 服務失敗",
                    "before_fix": "以前會返回 HTTP 200 + 預設句子",
                    "after_fix": "現在正確返回 HTTP 503 + 真實錯誤"
                },
                status_code=503
            )
        
        # 如果成功，返回成功響應
        return JSONResponse({
            "success": True,
            "message": "AI 服務正常運行",
            "test_result": "TRANSPARENCY_VERIFICATION_PASSED",
            "generated_content": payload.get("sentence"),
            "proof": "這個成功響應證明 AI 服務真的在工作，不是降級內容",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return create_transparent_error_response(
            error_message=f"透明化測試期間發生異常: {str(e)}",
            error_code="TRANSPARENCY_TEST_EXCEPTION",
            details={"exception_type": type(e).__name__},
            status_code=500
        )
