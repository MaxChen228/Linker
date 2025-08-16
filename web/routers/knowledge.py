"""
Knowledge management routes for the Linker web application.
"""

from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from core.error_types import ErrorCategory, ErrorTypeSystem

# TASK-34: 引入統一API端點管理系統，消除硬編碼
from web.config.api_endpoints import API_ENDPOINTS
from web.dependencies import (
    get_know_service,  # TASK-31: 使用新的純異步服務
    get_templates,
)

router = APIRouter()


@router.get(API_ENDPOINTS.KNOWLEDGE_PAGE, response_class=HTMLResponse)
async def knowledge_points(
    request: Request, category: Optional[str] = None, mastery: Optional[str] = None
):
    """知識點瀏覽頁面"""
    templates = get_templates()
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    # 獲取所有未刪除的知識點
    if hasattr(knowledge, "get_active_points_async"):
        all_points = await knowledge.get_active_points_async()
    elif hasattr(knowledge, "get_knowledge_points_async"):
        all_points = await knowledge.get_knowledge_points_async()
        all_points = [p for p in all_points if not p.is_deleted]
    else:
        all_points = knowledge.get_active_points()

    # 根據類別篩選
    if category:
        try:
            ErrorCategory.from_string(category)
            all_points = [
                p
                for p in all_points
                if (p.category if isinstance(p.category, str) else p.category.value) == category
            ]
        except (ValueError, KeyError, AttributeError):
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

    type_system = ErrorTypeSystem()

    for point in all_points:
        # 處理 category 可能是字符串或枚舉的情況
        category_value = point.category if isinstance(point.category, str) else point.category.value

        if category_value == "systematic":
            # 系統性錯誤按subtype分組
            subtype_obj = type_system.get_subtype_by_name(point.subtype)
            group_name = subtype_obj.chinese_name if subtype_obj else point.subtype
            systematic_groups[group_name].append(point)
        elif category_value == "isolated":
            isolated_points.append(point)
        elif category_value == "enhancement":
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
    if hasattr(knowledge, "get_statistics_async"):
        stats = await knowledge.get_statistics_async()
    else:
        stats = knowledge.get_statistics()

    # 計算各類別統計
    category_counts = {
        "系統性錯誤": len(systematic_groups),  # 群組數量，不是點數量
        "單一性錯誤": len(isolated_points),
        "可以更好": len(enhancement_points),
        "其他錯誤": len(other_points),
    }

    # 獲取所有分類
    categories = ["系統性錯誤", "單一性錯誤", "可以更好", "其他錯誤"]

    # 獲取複習佇列（可以複習的知識點）
    review_queue = await knowledge.get_review_candidates(max_points=20)  # TASK-31: 添加 await

    # 統一使用資料庫數據源避免統計不一致（修復：總知識點 vs 待複習數量矛盾）
    if hasattr(knowledge, "get_review_candidates_async"):
        due_points = await knowledge.get_review_candidates_async(max_points=100)
    else:
        due_points = knowledge.get_due_points()  # JSON模式降級選項

    # 獲取當前時間供模板使用
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


@router.get(API_ENDPOINTS.KNOWLEDGE_TRASH_PAGE, response_class=HTMLResponse)
async def knowledge_trash(request: Request):
    """知識點回收站頁面"""
    templates = get_templates()
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    # 獲取所有已刪除的知識點
    if hasattr(knowledge, "get_deleted_points_async"):
        deleted_points = await knowledge.get_deleted_points_async()
    elif hasattr(knowledge, "get_knowledge_points_async"):
        all_points = await knowledge.get_knowledge_points_async()
        deleted_points = [p for p in all_points if p.is_deleted]
    else:
        deleted_points = knowledge.get_deleted_points()

    # 按刪除時間排序（最新的在前）
    deleted_points.sort(key=lambda x: x.deleted_at, reverse=True)

    # 計算刪除了多久
    from datetime import datetime

    now = datetime.now()

    for point in deleted_points:
        if point.deleted_at:
            try:
                deleted_date = datetime.fromisoformat(point.deleted_at.replace("Z", "+00:00"))
                deleted_date = deleted_date.replace(tzinfo=None)
                days_ago = (now - deleted_date).days

                if days_ago == 0:
                    point.deleted_time_display = "今天"
                elif days_ago == 1:
                    point.deleted_time_display = "昨天"
                elif days_ago < 7:
                    point.deleted_time_display = f"{days_ago} 天前"
                elif days_ago < 30:
                    weeks_ago = days_ago // 7
                    point.deleted_time_display = f"{weeks_ago} 週前"
                else:
                    point.deleted_time_display = f"{days_ago} 天前"

                # 計算剩餘天數
                point.days_until_permanent = 30 - days_ago

            except (ValueError, AttributeError):
                point.deleted_time_display = "未知"
                point.days_until_permanent = 30

    return templates.TemplateResponse(
        "knowledge-trash.html",
        {
            "request": request,
            "deleted_points": deleted_points,
            "total_count": len(deleted_points),
            "active": "knowledge",
        },
    )


@router.get(API_ENDPOINTS.KNOWLEDGE_DETAIL_PAGE, response_class=HTMLResponse)
async def knowledge_detail(request: Request, point_id: str):
    """知識點詳情頁面"""
    templates = get_templates()
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    # 獲取指定的知識點
    try:
        point_id_int = int(point_id)
    except ValueError:
        return RedirectResponse(url="/knowledge", status_code=303)

    if hasattr(knowledge, "get_knowledge_point_async"):
        point = await knowledge.get_knowledge_point_async(point_id_int)
    else:
        point = knowledge.get_knowledge_point(point_id_int)

    if not point:
        # 如果找不到知識點，重定向到知識點列表頁
        return RedirectResponse(url="/knowledge", status_code=303)

    # 獲取相關的錯誤記錄（最近的10個）
    related_mistakes = []
    # TASK-31: KnowService 暫時不提供 get_all_mistakes，返回空列表
    if hasattr(knowledge, "get_all_mistakes_async"):
        all_mistakes = await knowledge.get_all_mistakes_async()
    elif hasattr(knowledge, "get_all_mistakes"):
        all_mistakes = knowledge.get_all_mistakes()
    else:
        all_mistakes = []
    for mistake in (
        all_mistakes[-50:] if len(all_mistakes) > 50 else all_mistakes
    ):  # 檢查最近50個錯誤
        if mistake.get("knowledge_points"):
            for kp in mistake["knowledge_points"]:
                if kp.get("id") == point_id_int:
                    # 添加必要的字段以兼容模板
                    if "feedback" in mistake:
                        mistake["correct_answer"] = mistake["feedback"].get(
                            "overall_suggestion", ""
                        )
                        mistake["explanation"] = mistake["feedback"].get("detailed_feedback", "")
                    related_mistakes.append(mistake)
                    break
        if len(related_mistakes) >= 10:
            break

    # 獲取錯誤類型系統，以顯示子類型的中文名稱
    type_system = ErrorTypeSystem()
    subtype_obj = type_system.get_subtype_by_name(point.subtype) if point.subtype else None

    # 計算下次複習時間
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
        except (ValueError, TypeError, AttributeError):
            pass

    # 為模板準備point對象，添加缺少的屬性
    # 從 original_error 中取得完整的句子
    full_user_answer = ""
    full_correct_answer = ""
    if hasattr(point, "original_error") and point.original_error:
        full_user_answer = point.original_error.user_answer
        full_correct_answer = point.original_error.correct_answer

    point_dict = {
        "id": point.id,
        "title": point.key_point,  # 保留 key_point 作為描述性標題
        "key_point": point.key_point,
        "category": {
            "value": point.category if isinstance(point.category, str) else point.category.value,
            "chinese_name": ErrorCategory.from_string(
                point.category if isinstance(point.category, str) else point.category.value
            ).to_chinese(),
        },
        "subtype": point.subtype,
        "description": point.explanation,  # 使用 explanation 作為 description
        "original_phrase": point.original_phrase,  # 錯誤片段
        "correction": point.correction,  # 修正片段
        "full_user_answer": full_user_answer,  # 完整的用戶答案
        "full_correct_answer": full_correct_answer,  # 完整的正確答案
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
