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
from datetime import datetime


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
    # 獲取複習列表（最多顯示10個）
    review_queue = knowledge.get_review_candidates(max_points=10)
    
    # 修正統計資料，讓「待複習」顯示實際可複習的數量
    stats = knowledge.get_statistics()
    # 計算實際可複習的知識點數量（單一性錯誤和可以更好類別中已到期的）
    reviewable_points = knowledge.get_review_candidates(max_points=100)  # 獲取所有可複習的
    stats['due_reviews'] = len(reviewable_points)  # 覆蓋原本的統計
    
    # 為每個知識點準備顯示資料
    review_items = []
    for point in review_queue:
        review_items.append({
            "id": point.id,
            "key_point": point.key_point,
            "category": point.category.to_chinese(),
            "category_value": point.category.value,
            "mastery_level": round(point.mastery_level * 100),
            "mistake_count": point.mistake_count,
            "next_review": point.next_review,
            "is_due": point.next_review <= datetime.now().isoformat() if point.next_review else False
        })
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "stats": stats, 
            "review_items": review_items,
            "active": "home"
        },
    )




@app.get("/patterns", response_class=HTMLResponse)
def patterns(request: Request, category: Optional[str] = None, q: Optional[str] = None):
    """文法句型列表頁面（預設版本）"""
    import json
    from pathlib import Path
    
    # 載入所有擴充的句型資料
    enriched_file = Path("data/patterns_enriched_complete.json")
    if enriched_file.exists():
        with open(enriched_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            patterns = data.get('patterns', [])
    else:
        # 降級使用原始資料
        all_patterns = assets.get_grammar_patterns()
        patterns = [
            {
                'id': p.id or f"GP{i:03d}",
                'pattern': p.pattern,
                'category': p.category,
                'explanation': p.explanation,
                'difficulty': 3,  # 預設中等難度
                'frequency': 'medium',
                'examples': [
                    {'zh': p.example_zh, 'en': p.example_en}
                ] if p.example_zh or p.example_en else []
            }
            for i, p in enumerate(all_patterns, 1)
        ]
    
    # 提取分類
    categories = sorted({p.get('category') for p in patterns if p.get('category')})
    
    # 篩選
    filtered_patterns = patterns
    if category:
        filtered_patterns = [p for p in filtered_patterns if p.get('category') == category]
    if q:
        query = q.strip().lower()
        filtered_patterns = [
            p for p in filtered_patterns
            if (query in p.get('pattern', '').lower())
            or (query in p.get('formula', '').lower())
            or (query in p.get('explanation', '').lower())
            or any(query in ex.get('zh', '').lower() or query in ex.get('en', '').lower() 
                   for ex in p.get('examples', []))
        ]
    
    return templates.TemplateResponse(
        "patterns.html",
        {
            "request": request,
            "patterns": filtered_patterns[:200],
            "category": category or "",
            "categories": categories,
            "q": q or "",
            "active": "patterns",
        },
    )




@app.get("/patterns/{pattern_id}", response_class=HTMLResponse)
def pattern_detail(request: Request, pattern_id: str):
    """句型詳情頁面"""
    import json
    from pathlib import Path
    
    # 載入擴充資料
    enriched_file = Path("data/patterns_enriched_complete.json")
    if enriched_file.exists():
        with open(enriched_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            patterns = data.get('patterns', [])
    else:
        patterns = []
    
    # 尋找指定句型
    pattern = None
    for p in patterns:
        if p.get('id') == pattern_id:
            pattern = p
            break
    
    if not pattern:
        # 如果找不到，返回列表頁
        return RedirectResponse(url="/patterns", status_code=302)
    
    return templates.TemplateResponse(
        "pattern-detail.html",
        {
            "request": request,
            "pattern": pattern,
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


@app.get("/knowledge/{point_id}", response_class=HTMLResponse)
def knowledge_detail(request: Request, point_id: str):
    """知識點詳情頁面"""
    # 獲取指定的知識點
    point = knowledge.get_knowledge_point(point_id)
    
    if not point:
        # 如果找不到知識點，重定向到知識點列表頁
        return RedirectResponse(url="/knowledge", status_code=303)
    
    # 獲取相關的錯誤記錄（最近的10個）
    related_mistakes = []
    all_mistakes = knowledge.get_all_mistakes()
    for mistake in all_mistakes[-50:] if len(all_mistakes) > 50 else all_mistakes:  # 檢查最近50個錯誤
        if mistake.get("knowledge_points"):
            for kp in mistake["knowledge_points"]:
                if kp.get("id") == point_id:
                    # 添加必要的字段以兼容模板
                    if "feedback" in mistake:
                        mistake["correct_answer"] = mistake["feedback"].get("overall_suggestion", "")
                        mistake["explanation"] = mistake["feedback"].get("detailed_feedback", "")
                    related_mistakes.append(mistake)
                    break
        if len(related_mistakes) >= 10:
            break
    
    # 獲取錯誤類型系統，以顯示子類型的中文名稱
    from core.error_types import ErrorTypeSystem
    type_system = ErrorTypeSystem()
    subtype_obj = type_system.get_subtype_by_name(point.subtype) if point.subtype else None
    
    # 計算下次複習時間
    from datetime import datetime
    next_review_display = None
    if point.next_review:
        try:
            next_review_date = datetime.fromisoformat(point.next_review.replace("Z", "+00:00"))
            now = datetime.now(next_review_date.tzinfo)
            if next_review_date > now:
                days_until = (next_review_date - now).days
                if days_until == 0:
                    next_review_display = "今天"
                elif days_until == 1:
                    next_review_display = "明天"
                else:
                    next_review_display = f"{days_until} 天後"
            else:
                next_review_display = "已到期"
        except:
            pass
    
    # 為模板準備point對象，添加缺少的屬性
    point_dict = {
        "id": point.id,
        "title": point.key_point,  # 使用 key_point 作為 title
        "key_point": point.key_point,
        "category": {
            "value": point.category.value,
            "chinese_name": point.category.to_chinese()
        },
        "subtype": point.subtype,
        "description": point.explanation,  # 使用 explanation 作為 description
        "original_phrase": point.original_phrase,  # 原始錯誤句子
        "correction": point.correction,  # 修正後的句子
        "mastery_level": point.mastery_level,
        "mistake_count": point.mistake_count,
        "correct_count": point.correct_count,
        "next_review": point.next_review,
        "improvement_suggestion": "",  # 保留為空或其他用途
    }
    
    return templates.TemplateResponse(
        "knowledge-detail.html",
        {
            "request": request,
            "point": point_dict,
            "subtype_display": subtype_obj.chinese_name if subtype_obj else point.subtype,
            "related_mistakes": related_mistakes,
            "next_review_display": next_review_display,
            "active": "knowledge",
        },
    )




@app.get("/healthz")
def healthz():
    # 簡易健康檢查：確保模板與資料夾存在
    ok = TEMPLATES_DIR.exists() and STATIC_DIR.exists()
    return {"status": "ok" if ok else "degraded"}


