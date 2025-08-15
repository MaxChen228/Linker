"""
Basic page routes for the Linker web application.
"""

from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from web.dependencies import (
    get_async_knowledge_service,  # TASK-31: 使用新的純異步服務
    get_knowledge_manager,
    get_knowledge_manager_async_dependency,  # 保留以備向後相容
    get_templates,
)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """主頁路由"""
    templates = get_templates()
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    # 獲取複習列表（最多顯示10個）
    if hasattr(knowledge, "get_review_candidates_async"):
        review_queue = await knowledge.get_review_candidates_async(max_points=10)
    else:
        review_queue = knowledge.get_review_candidates(max_points=10)

    # 修正統計資料，讓「待複習」顯示實際可複習的數量
    if hasattr(knowledge, "get_statistics_async"):
        stats = await knowledge.get_statistics_async()
    else:
        stats = knowledge.get_statistics()
    # 計算實際可複習的知識點數量（單一性錯誤和可以更好類別中已到期的）
    if hasattr(knowledge, "get_review_candidates_async"):
        reviewable_points = await knowledge.get_review_candidates_async(
            max_points=100
        )  # 獲取所有可複習的
    else:
        reviewable_points = knowledge.get_review_candidates(max_points=100)  # 獲取所有可複習的
    stats["due_reviews"] = len(reviewable_points)  # 覆蓋原本的統計

    # 為每個知識點準備顯示資料
    review_items = []
    for point in review_queue:
        review_items.append(
            {
                "id": point.id,
                "key_point": point.key_point,
                # TASK-31: 處理 ErrorCategory 可能是 enum 或字符串
                "category": point.category.to_chinese() if hasattr(point.category, 'to_chinese') else point.category,
                "category_value": point.category.value if hasattr(point.category, 'value') else point.category,
                "mastery_level": round(point.mastery_level * 100),
                "mistake_count": point.mistake_count,
                "next_review": point.next_review,
                "is_due": point.next_review <= datetime.now().isoformat()
                if point.next_review
                else False,
            }
        )

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "stats": stats, "review_items": review_items, "active": "home"},
    )
