"""
Grammar patterns routes for the Linker web application.
"""
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from web.dependencies import get_knowledge_assets, get_logger, get_templates

router = APIRouter()
logger = get_logger()

@router.get("/patterns", response_class=HTMLResponse)
def patterns(request: Request, category: Optional[str] = None, q: Optional[str] = None):
    """文法句型列表頁面（預設版本）"""
    templates = get_templates()
    assets = get_knowledge_assets()

    # 載入所有擴充的句型資料
    enriched_file = Path("data/patterns_enriched_complete.json")
    if enriched_file.exists():
        with open(enriched_file, encoding='utf-8') as f:
            data = json.load(f)
            # 支援新舊兩種格式
            patterns = data.get('patterns', data.get('data', []))
    else:
        # 降級使用原始資料
        grammar_file = Path("data/grammar_patterns.json")
        if grammar_file.exists():
            with open(grammar_file, encoding='utf-8') as f:
                data = json.load(f)
                # 支援新舊兩種格式
                if isinstance(data, dict):
                    patterns = data.get('patterns', data.get('data', []))
                else:
                    patterns = data  # 舊格式純陣列
        else:
            # 使用 assets 作為最後的後備
            all_patterns = assets.get_grammar_patterns()
            patterns = [
                {
                    'id': p.id or f"GP{i:03d}",
                    'pattern': p.pattern,
                    'category': p.category,
                    'explanation': p.explanation,
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

@router.get("/patterns/{pattern_id}", response_class=HTMLResponse)
def pattern_detail(request: Request, pattern_id: str):
    """句型詳情頁面"""
    templates = get_templates()

    # 載入擴充資料
    enriched_file = Path("data/patterns_enriched_complete.json")
    if enriched_file.exists():
        with open(enriched_file, encoding='utf-8') as f:
            data = json.load(f)
            # 支援新舊兩種格式
            patterns = data.get('patterns', data.get('data', []))
    else:
        # 嘗試從 grammar_patterns.json 載入
        grammar_file = Path("data/grammar_patterns.json")
        if grammar_file.exists():
            with open(grammar_file, encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    patterns = data.get('patterns', data.get('data', []))
                else:
                    patterns = data
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

@router.get("/api/patterns", response_class=JSONResponse)
def get_all_patterns_api():
    """API 端點：獲取所有文法句型列表，用於練習模式選擇。"""
    try:
        enriched_file = Path("data/patterns_enriched_complete.json")
        if not enriched_file.exists():
            return JSONResponse({"success": False, "error": "Patterns data not found."}, status_code=404)

        with open(enriched_file, encoding='utf-8') as f:
            data = json.load(f)
            patterns = data.get('patterns', data.get('data', []))

        # 只回傳必要的資訊以減小傳輸量
        patterns_summary = [
            {
                "id": p.get("id"),
                "pattern": p.get("pattern"),
                "category": p.get("category", "未分類"),
                "formula": p.get("formula", ""),
                "core_concept": p.get("core_concept", "")
            }
            for p in patterns if p.get("id") and p.get("pattern")
        ]
        
        return JSONResponse({"success": True, "patterns": patterns_summary})

    except Exception as e:
        logger.error(f"Error fetching patterns API: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": "Internal server error."}, status_code=500)
