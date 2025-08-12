"""
Practice routes for the Linker web application.
"""
import json

from fastapi import APIRouter, Form, Request
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
def practice_get(request: Request, length: str = "short", level: int = 1, shuffle: int = 0, mode: str = "new"):
    """練習頁面（GET）"""
    templates = get_templates()
    ai = get_ai_service()
    knowledge = get_knowledge_manager()
    assets = get_knowledge_assets()

    # mode: "new" 為新題目，"review" 為複習題

    # 初始化變數
    review_empty_message = None
    target_points = []  # 初始化 target_points
    llm_debug_data = None  # 初始化 LLM 調試資料

    # 檢查是否要生成新題目（shuffle=1表示要出題）
    logger.info(f"Practice GET: mode={mode}, shuffle={shuffle}, length={length}, level={level}")
    logger.info(f"Practice GET: mode type={type(mode)}, mode value='{mode}'")

    if shuffle:
        if mode == "review":
            # 複習模式：從知識點生成題目
            review_points = knowledge.get_review_candidates(max_points=5)
            logger.info(f"Review mode: found {len(review_points)} review candidates")
            if review_points:
                payload = ai.generate_review_sentence(
                    knowledge_points=review_points,
                    level=level,
                    length=length
                )
                # 將知識點ID存入session或作為隱藏欄位傳遞
                target_point_ids = payload.get("target_point_ids", [])
                target_points = payload.get("target_points", [])  # 獲取完整知識點信息
                sentence = payload.get("sentence", "今天天氣很好。")
                hint = payload.get("hint")
                target_points_description = payload.get("target_points_description", "")

                # 記錄複習題目生成狀態
                if target_points:
                    logger.info(f"Review sentence generated with {len(target_points)} target points")

                # 獲取 LLM 調試資料
                llm_debug_data = ai.get_last_interaction()
            else:
                # 沒有待複習知識點，不出題，顯示提示
                sentence = ""
                hint = ""
                target_point_ids = []
                target_points = []
                target_points_description = ""
                review_empty_message = "目前沒有需要複習的知識點（單一性錯誤或可以更好類別）。請先練習新題目累積知識點。"
        else:
            # 新題模式：原有邏輯
            bank = assets.get_example_bank(length=length, difficulty=level)
            payload = ai.generate_practice_sentence(
                level=level,
                length=length,
                examples=bank[:5] if bank else None,
                shuffle=bool(shuffle)
            )
            target_point_ids = []
            target_points = []  # 新題模式沒有目標知識點
            sentence = payload.get("sentence", "今天天氣很好。")
            hint = payload.get("hint")
            target_points_description = payload.get("target_points_description", "")

            # 獲取 LLM 調試資料
            llm_debug_data = ai.get_last_interaction()
    else:
        # 第一次進入頁面，不出題
        sentence = ""
        hint = ""
        target_point_ids = []
        target_points = []
        target_points_description = ""

    return templates.TemplateResponse(
        "practice.html",
        {
            "request": request,
            "length": length,
            "level": level,
            "mode": mode,
            "chinese": sentence,
            "hint": hint,
            "target_point_ids": target_point_ids,  # 傳遞考點ID
            "target_points": target_points,  # 傳遞完整知識點信息
            "target_points_description": target_points_description,
            "review_empty_message": review_empty_message,  # 新增：空佇列提示
            "llm_debug_data": llm_debug_data,  # 新增：LLM 調試資料
            "result": None,
            "active": "practice",
        },
    )

@router.post("/practice", response_class=HTMLResponse)
def practice_post(
    request: Request,
    chinese: str = Form(...),
    english: str = Form(...),
    length: str = Form("short"),
    level: int = Form(1),
    mode: str = Form("new"),
    target_point_ids: str = Form(""),  # JSON string of point IDs
):
    """練習頁面（POST）"""
    templates = get_templates()
    ai = get_ai_service()
    knowledge = get_knowledge_manager()

    # 使用 AI 進行批改
    result = ai.grade_translation(chinese=chinese, english=english)

    # 如果是複習模式，更新相關知識點的掌握度
    if mode == "review" and target_point_ids:
        try:
            point_ids = json.loads(target_point_ids)
            is_correct = result.get("is_generally_correct", False)

            # 更新每個相關知識點的掌握狀態
            for point_id in point_ids:
                knowledge.update_knowledge_point(point_id, is_correct)

            # 記錄複習結果到日誌
            logger.info(
                "review_practice",
                mode="review",
                target_points=point_ids,
                is_correct=is_correct,
                chinese=chinese[:50],
                english=english[:50]
            )
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse target_point_ids: {e}")

    # 保存結果到知識庫（區分新題和複習模式）
    if not result.get("is_generally_correct", False):
        # 錯誤情況：新題會創建新知識點，複習會更新現有知識點
        knowledge.save_mistake(
            chinese_sentence=chinese,
            user_answer=english,
            feedback=result,
            practice_mode=mode
        )
    elif mode == "review" and target_point_ids:
        # 複習模式答對：為相關知識點添加成功記錄
        try:
            point_ids = json.loads(target_point_ids)
            for point_id in point_ids:
                knowledge.add_review_success(
                    knowledge_point_id=point_id,
                    chinese_sentence=chinese,
                    user_answer=english
                )
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to process review success: {e}")

    return templates.TemplateResponse(
        "practice.html",
        {
            "request": request,
            "length": length,
            "level": level,
            "mode": mode,
            "chinese": chinese,
            "english": english,
            "result": result,
            "target_point_ids": target_point_ids,
            "active": "practice",
        },
    )

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
            return JSONResponse({
                "success": False,
                "error": "缺少必要參數"
            })

        # 使用 AI 進行批改
        result = ai.grade_translation(chinese=chinese, english=english)

        # 如果是複習模式，更新知識點
        if mode == "review" and target_point_ids:
            is_correct = result.get("is_generally_correct", False)
            for point_id in target_point_ids:
                knowledge.update_knowledge_point(point_id, is_correct)

        # 保存錯誤到知識庫（如果有錯誤）
        if not result.get("is_generally_correct", False):
            knowledge.save_mistake(
                chinese_sentence=chinese,
                user_answer=english,
                feedback=result
            )

        # 計算分數
        score = 100
        errors = result.get("error_analysis", [])
        for error in errors:
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

        return JSONResponse({
            "success": True,
            "score": score,
            "is_generally_correct": result.get("is_generally_correct", False),
            "feedback": result.get("overall_suggestion", ""),
            "error_analysis": result.get("error_analysis", []),
            "detailed_feedback": result.get("detailed_feedback", "")
        })

    except Exception as e:
        logger.error(f"Error grading answer: {e}")

        # 提供更具體的錯誤訊息
        error_message = str(e)
        if "GEMINI_API_KEY" in error_message:
            error_message = "AI 服務未正確配置，請檢查 GEMINI_API_KEY 環境變數設置"
        elif "ImportError" in error_message:
            error_message = "AI 服務依賴未安裝，請執行 pip install google-generativeai"
        elif "NetworkError" in error_message:
            error_message = "網路連線失敗，請檢查網路連線"

        return JSONResponse({
            "success": False,
            "error": error_message
        }, status_code=500)

@router.post("/api/generate-question", response_class=JSONResponse)
async def generate_question_api(request: Request):
    """API 端點：生成單個題目（支援並行調用）"""
    ai = get_ai_service()
    knowledge = get_knowledge_manager()
    assets = get_knowledge_assets()

    try:
        # 從 request body 讀取參數
        data = await request.json()
        mode = data.get("mode", "new")
        length = data.get("length", "short")
        level = data.get("level", 1)

        logger.info(f"Generate question API: mode={mode}, length={length}, level={level}")

        if mode == "review":
            # 複習模式：從知識點生成題目
            review_points = knowledge.get_review_candidates(max_points=5)
            if not review_points:
                return JSONResponse({
                    "success": False,
                    "error": "沒有待複習的知識點"
                })

            payload = ai.generate_review_sentence(
                knowledge_points=review_points,
                level=level,
                length=length
            )

            return JSONResponse({
                "success": True,
                "chinese": payload.get("sentence", ""),
                "hint": payload.get("hint", ""),
                "target_point_ids": payload.get("target_point_ids", []),
                "target_points": payload.get("target_points", []),
                "target_points_description": payload.get("target_points_description", "")
            })
        # 新題模式
        bank = assets.get_example_bank(length=length, difficulty=level)
        payload = ai.generate_practice_sentence(
            level=level,
            length=length,
            examples=bank[:5] if bank else None,
            shuffle=True
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
        logger.error(f"Error generating question: {e}")

        # 提供更具體的錯誤訊息
        error_message = str(e)
        if "GEMINI_API_KEY" in error_message:
            error_message = "AI 服務未正確配置，請檢查 GEMINI_API_KEY 環境變數設置"
        elif "ImportError" in error_message:
            error_message = "AI 服務依賴未安裝，請執行 pip install google-generativeai"
        elif "NetworkError" in error_message:
            error_message = "網路連線失敗，請檢查網路連線"

        return JSONResponse({
            "success": False,
            "error": error_message
        }, status_code=500)
