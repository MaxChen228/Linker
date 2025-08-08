from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.knowledge_assets import KnowledgeAssets
from core.knowledge import KnowledgeManager
from core.ai_service import AIService
from core.error_types import ErrorCategory
from core.config import DATA_DIR
import random
import time
from uuid import uuid4
from core.logger import get_logger


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(title="Linker", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


assets = KnowledgeAssets()
knowledge = KnowledgeManager(data_dir=str(DATA_DIR))
ai = AIService()
logger = get_logger("web")


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.time()
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = None
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.log_exception(e, context={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        })
        raise
    finally:
        duration = time.time() - start
        logger.info(
            "http_access",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            query=str(request.url.query)[:200],
            status_code=getattr(response, "status_code", 0),
            duration_ms=int(duration * 1000),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:200],
        )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    stats = knowledge.get_statistics()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "stats": stats, "active": "home"},
    )


@app.get("/patterns", response_class=HTMLResponse)
def patterns(request: Request, category: Optional[str] = None, q: Optional[str] = None):
    all_patterns = assets.get_grammar_patterns()
    categories = sorted({p.category for p in all_patterns if p.category})

    data = all_patterns
    if category:
        data = [p for p in data if p.category == category]
    if q:
        query = q.strip().lower()
        data = [
            p
            for p in data
            if (query in (p.pattern or "").lower())
            or (query in (p.explanation or "").lower())
            or (query in (p.example_en or "").lower())
            or (query in (p.example_zh or "").lower())
        ]

    data = data[:200]
    return templates.TemplateResponse(
        "patterns.html",
        {
            "request": request,
            "patterns": data,
            "category": category or "",
            "categories": categories,
            "q": q or "",
            "active": "patterns",
        },
    )


# 分級例句頁面不對使用者展示；仍保留 API 給日後管理用途（暫時移出導覽，不渲染）


@app.get("/practice", response_class=HTMLResponse)
def practice_get(request: Request, length: str = "short", level: int = 1, shuffle: int = 0, mode: str = "new"):
    # mode: "new" 為新題目，"review" 為複習題
    
    # 初始化變數
    review_empty_message = None
    target_points = []  # 初始化 target_points
    llm_debug_data = None  # 初始化 LLM 調試資料
    
    # 檢查是否要生成新題目（shuffle=1表示要出題）
    logger.info(f"Practice GET: mode={mode}, shuffle={shuffle}, length={length}, level={level}")
    
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


@app.post("/practice", response_class=HTMLResponse)
def practice_post(
    request: Request,
    chinese: str = Form(...),
    english: str = Form(...),
    length: str = Form("short"),
    level: int = Form(1),
    mode: str = Form("new"),
    target_point_ids: str = Form(""),  # JSON string of point IDs
):
    # 使用 AI 進行批改
    result = ai.grade_translation(chinese=chinese, english=english)
    
    # 如果是複習模式，更新相關知識點的掌握度
    if mode == "review" and target_point_ids:
        try:
            import json
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
    
    # 保存錯誤到知識庫（新題和複習題都要保存）
    if not result.get("is_generally_correct", False):
        knowledge.save_mistake(chinese_sentence=chinese, user_answer=english, feedback=result)

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


@app.get("/knowledge", response_class=HTMLResponse)
def knowledge_points(request: Request, category: Optional[str] = None, mastery: Optional[str] = None):
    """知識點瀏覽頁面"""
    from collections import defaultdict
    
    # 獲取所有知識點
    all_points = knowledge.knowledge_points
    
    # 根據類別篩選
    if category:
        try:
            cat_enum = ErrorCategory.from_string(category)
            all_points = [p for p in all_points if p.category == cat_enum]
        except:
            pass
    
    # 根據掌握度篩選
    if mastery:
        if mastery == "low":
            all_points = [p for p in all_points if p.mastery_level < 0.3]
        elif mastery == "medium":
            all_points = [p for p in all_points if 0.3 <= p.mastery_level < 0.7]
        elif mastery == "high":
            all_points = [p for p in all_points if p.mastery_level >= 0.7]
    
    # 分組處理知識點
    systematic_groups = defaultdict(list)  # 系統性錯誤按subtype分組
    isolated_points = []  # 單一性錯誤保持獨立
    enhancement_points = []  # 可以更好保持獨立
    other_points = []  # 其他錯誤保持獨立
    
    from core.error_types import ErrorTypeSystem
    type_system = ErrorTypeSystem()
    
    for point in all_points:
        if point.category.value == "systematic":
            # 系統性錯誤按subtype分組
            subtype_obj = type_system.get_subtype_by_name(point.subtype)
            group_name = subtype_obj.chinese_name if subtype_obj else point.subtype
            systematic_groups[group_name].append(point)
        elif point.category.value == "isolated":
            isolated_points.append(point)
        elif point.category.value == "enhancement":
            enhancement_points.append(point)
        else:
            other_points.append(point)
    
    # 構建知識群組數據
    knowledge_groups = []
    
    # 處理系統性錯誤群組
    for group_name, points in systematic_groups.items():
        group = {
            "type": "systematic",
            "name": group_name,
            "points": sorted(points, key=lambda x: x.mastery_level),
            "count": len(points),
            "avg_mastery": sum(p.mastery_level for p in points) / len(points) if points else 0,
            "total_mistakes": sum(p.mistake_count for p in points),
        }
        knowledge_groups.append(group)
    
    # 排序群組（按錯誤次數降序）
    knowledge_groups.sort(key=lambda x: x["total_mistakes"], reverse=True)
    
    # 獲取統計資料
    stats = knowledge.get_statistics()
    
    # 計算各類別統計
    category_counts = {
        "系統性錯誤": len(systematic_groups),  # 群組數量，不是點數量
        "單一性錯誤": len(isolated_points),
        "可以更好": len(enhancement_points),
        "其他錯誤": len(other_points)
    }
    
    # 獲取所有分類
    categories = ["系統性錯誤", "單一性錯誤", "可以更好", "其他錯誤"]
    
    # 獲取複習佇列（可以複習的知識點）
    review_queue = knowledge.get_review_candidates(max_points=20)
    due_points = knowledge.get_due_points()  # 已到期的知識點
    
    # 獲取當前時間供模板使用
    from datetime import datetime
    now = datetime.now().isoformat()
    
    return templates.TemplateResponse(
        "knowledge.html",
        {
            "request": request,
            "knowledge_groups": knowledge_groups,
            "isolated_points": isolated_points,
            "enhancement_points": enhancement_points,
            "other_points": other_points,
            "points": all_points,  # 保留原始數據以兼容
            "categories": categories,
            "category_counts": category_counts,
            "current_category": category,
            "current_mastery": mastery,
            "stats": stats,
            "review_queue": review_queue,  # 複習佇列
            "due_points": due_points,  # 已到期的知識點
            "now": now,  # 當前時間
            "active": "knowledge",
        },
    )


def create_app() -> FastAPI:
    return app


@app.get("/healthz")
def healthz():
    # 簡易健康檢查：確保模板與資料夾存在
    ok = TEMPLATES_DIR.exists() and STATIC_DIR.exists()
    return {"status": "ok" if ok else "degraded"}


