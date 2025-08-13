"""
Practice routes for the Linker web application. (Refactored for API-first approach)
"""
import json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from web.dependencies import (
    get_ai_service,
    get_knowledge_assets,
    get_knowledge_manager,
    get_logger,
    get_templates,
)

router = APIRouter()
logger = get_logger()

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

@router.post("/api/grade-answer", response_class=JSONResponse)
async def grade_answer_api(request: Request):
    """API 端點：批改答案"""
    ai = get_ai_service()
    knowledge = get_knowledge_manager()

    try:
        data = await request.json()
        chinese = data.get("chinese", "")
        english = data.get("english", "")
        mode = data.get("mode", "new")
        target_point_ids = data.get("target_point_ids", [])

        if not chinese or not english:
            return JSONResponse({"success": False, "error": "缺少必要參數"}, status_code=400)

        # 1. 使用 AI 進行批改
        result = ai.grade_translation(chinese=chinese, english=english)

        # 2. 更新知識點掌握度（如果是複習模式）
        is_correct = result.get("is_generally_correct", False)
        if mode == "review" and target_point_ids:
            for point_id in target_point_ids:
                knowledge.update_knowledge_point(point_id, is_correct)

        # 3. 保存錯誤記錄
        if not is_correct:
            knowledge.save_mistake(
                chinese_sentence=chinese,
                user_answer=english,
                feedback=result,
                practice_mode=mode
            )
        # 4. 如果是複習答對，也記錄下來
        elif mode == "review" and target_point_ids:
             for point_id in target_point_ids:
                knowledge.add_review_success(
                    knowledge_point_id=point_id,
                    chinese_sentence=chinese,
                    user_answer=english
                )


        # 5. 計算分數
        score = 100
        for error in result.get("error_analysis", []):
            category = error.get("category", "other")
            if category == "systematic": score -= 15
            elif category == "isolated": score -= 10
            elif category == "enhancement": score -= 5
            else: score -= 8
        score = max(0, min(100, score))

        # 6. 回傳完整結果
        return JSONResponse({
            "success": True,
            "score": score,
            "is_generally_correct": is_correct,
            "feedback": result.get("overall_suggestion", ""),
            "error_analysis": result.get("error_analysis", []),
            "detailed_feedback": result.get("detailed_feedback", "")
        })

    except Exception as e:
        logger.error(f"Error in grade_answer_api: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": "批改時發生內部錯誤"}, status_code=500)


@router.post("/api/generate-question", response_class=JSONResponse)
async def generate_question_api(request: Request):
    """API 端點：生成單個題目（支援並行調用）"""
    ai = get_ai_service()
    knowledge = get_knowledge_manager()
    assets = get_knowledge_assets()

    try:
        data = await request.json()
        mode = data.get("mode", "new")
        length = data.get("length", "short")
        level = data.get("level", 1)

        logger.info(f"API: Generating question - mode={mode}, length={length}, level={level}")

        if mode == "review":
            review_points = knowledge.get_review_candidates(max_points=5)
            if not review_points:
                return JSONResponse({"success": False, "error": "沒有待複習的知識點"})

            payload = ai.generate_review_sentence(
                knowledge_points=review_points, level=level, length=length
            )
            return JSONResponse({
                "success": True,
                "chinese": payload.get("sentence", ""),
                "hint": payload.get("hint", ""),
                "target_point_ids": payload.get("target_point_ids", []),
                "target_points": payload.get("target_points", []),
                "target_points_description": payload.get("target_points_description", "")
            })

        # 預設為新題模式
        bank = assets.get_example_bank(length=length, difficulty=level)
        payload = ai.generate_practice_sentence(
            level=level, length=length, examples=bank[:5] if bank else None
        )
        return JSONResponse({
            "success": True,
            "chinese": payload.get("sentence", ""),
            "hint": payload.get("hint", ""),
            "target_point_ids": [],
            "target_points": [],
            "target_points_description": ""
        })

    except Exception as e:
        logger.error(f"Error in generate_question_api: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": "生成題目時發生內部錯誤"}, status_code=500)