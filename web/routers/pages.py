"""
Basic page routes for the Linker web application.
"""

from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

# TASK-34: 引入統一API端點管理系統，消除硬編碼
from web.config.api_endpoints import API_ENDPOINTS
from web.dependencies import (
    get_know_service,  # TASK-31: 使用新的純異步服務
    get_templates,
)

router = APIRouter()


@router.get(API_ENDPOINTS.HOME, response_class=HTMLResponse)
async def home(request: Request):
    """主頁路由"""
    templates = get_templates()
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

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
                "category": point.category.to_chinese()
                if hasattr(point.category, "to_chinese")
                else point.category,
                "category_value": point.category.value
                if hasattr(point.category, "value")
                else point.category,
                "mastery_level": round(point.mastery_level * 100),
                "mistake_count": point.mistake_count,
                "next_review": point.next_review,
                "is_due": point.next_review <= datetime.now().isoformat()
                if point.next_review
                else False,
            }
        )

    # 獲取每日目標進度數據（為了更好的初始載入體驗）
    try:
        status_data = await knowledge.check_daily_limit("isolated")
        config_data = await knowledge.get_daily_limit_config()
        
        # 🔥 數據標準化：統一字段名，與API端點保持一致
        from core.config import DEFAULT_DAILY_LIMIT
        daily_progress = {
            'status': status_data,
            'config': {
                **config_data,
                'daily_limit': config_data.get('daily_knowledge_limit', config_data.get('daily_limit', DEFAULT_DAILY_LIMIT))
            }
        }
        
        # 移除舊字段名避免混淆
        daily_progress['config'].pop('daily_knowledge_limit', None)
        
    except Exception as e:
        # 如果獲取每日進度失敗，記錄錯誤並設為None，讓前端組件自行載入
        print(f"主頁路由獲取每日進度失敗: {e}")
        daily_progress = None

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "stats": stats, 
            "review_items": review_items,
            "daily_progress": daily_progress,
            "active": "home"
        },
    )


@router.get(API_ENDPOINTS.SETTINGS_PAGE, response_class=HTMLResponse)
async def settings(request: Request):
    """簡化設定頁面路由 - 使用 DailyGoalWidget 組件動態載入數據"""
    templates = get_templates()

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "active": "settings",
        },
    )
