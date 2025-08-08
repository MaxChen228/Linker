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
knowledge = KnowledgeManager(data_dir=str(Path(__file__).resolve().parent.parent / "data"))
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
def practice_get(request: Request, length: str = "short", level: int = 1, shuffle: int = 1):
    # 以 LLM 出題；分級例句僅用於 few-shot 輔助
    bank = assets.get_example_bank(length=length, difficulty=level)
    payload = ai.generate_practice_sentence(level=level, length=length, examples=bank[:5] if bank else None)
    sentence = payload.get("sentence", "今天天氣很好。")
    return templates.TemplateResponse(
        "practice.html",
        {
            "request": request,
            "length": length,
            "level": level,
            "chinese": sentence,
            "hint": payload.get("hint"),
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
):
    # 使用 AI 進行批改
    result = ai.grade_translation(chinese=chinese, english=english)
    # 保存至知識庫
    knowledge.save_mistake(chinese_sentence=chinese, user_answer=english, feedback=result)

    return templates.TemplateResponse(
        "practice.html",
        {
            "request": request,
            "length": length,
            "level": level,
            "chinese": chinese,
            "english": english,
            "result": result,
            "active": "practice",
        },
    )


@app.get("/reviews", response_class=HTMLResponse)
def reviews(request: Request):
    due = knowledge.get_due_points()
    return templates.TemplateResponse(
        "reviews.html",
        {
            "request": request,
            "due": due,
            "active": "reviews",
        },
    )


def create_app() -> FastAPI:
    return app


@app.get("/healthz")
def healthz():
    # 簡易健康檢查：確保模板與資料夾存在
    ok = TEMPLATES_DIR.exists() and STATIC_DIR.exists()
    return {"status": "ok" if ok else "degraded"}


