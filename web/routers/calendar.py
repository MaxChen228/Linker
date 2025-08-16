"""
學習日曆路由模組
提供日曆視圖和學習進度追蹤
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.database.calendar_db import CalendarDB
from core.log_config import get_module_logger

# TASK-34: 引入統一API端點管理系統，消除硬編碼
from web.dependencies import get_know_service  # TASK-31: 使用純異步服務

router = APIRouter(prefix="/calendar", tags=["calendar"])
templates = Jinja2Templates(directory="web/templates")
logger = get_module_logger(__name__)

# 建立全域日曆管理器實例
calendar_manager = CalendarDB()

# 資料檔案路徑（保留用於遷移）
DATA_DIR = Path("data")
CALENDAR_FILE = DATA_DIR / "learning_calendar.json"
PRACTICE_LOG_FILE = DATA_DIR / "practice_log.json"


async def migrate_json_to_db():
    """一次性遷移 JSON 資料到數據庫"""
    if CALENDAR_FILE.exists():
        try:
            with open(CALENDAR_FILE, encoding="utf-8") as f:
                json_data = json.load(f)

            success = await calendar_manager.migrate_from_json(json_data)
            if success:
                # 重命名檔案作為備份
                backup_file = CALENDAR_FILE.with_suffix(".json.migrated")
                if not backup_file.exists():
                    CALENDAR_FILE.rename(backup_file)
                    logger.info(
                        f"Migrated calendar data from JSON to database, backup saved as {backup_file}"
                    )
            return success
        except Exception as e:
            logger.error(f"Failed to migrate calendar data: {e}")
            return False
    return True  # 沒有檔案需要遷移


async def get_month_data(year: int, month: int) -> dict:
    """獲取指定月份的日曆資料"""
    # 嘗試遷移舊資料（如果存在）
    await migrate_json_to_db()

    km = await get_know_service()  # TASK-31: 使用純異步服務
    knowledge_points = await km.get_knowledge_points_async()

    # 計算月份的第一天和最後一天
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # 建立月份資料結構
    month_data = {
        "year": year,
        "month": month,
        "month_name": first_day.strftime("%B"),
        "days": [],
        "weeks": [],
        "stats": {"total_reviews_pending": 0, "total_completed": 0, "streak_days": 0},
    }

    # 計算第一週的空白天數（週一為0，週日為6）
    first_weekday = first_day.weekday()

    # 添加月份開始前的空白天
    current_week = []
    for _ in range(first_weekday):
        current_week.append(None)

    # 獲取整月的記錄
    monthly_records = await calendar_manager.get_daily_records(first_day, last_day)
    records_dict = {r["record_date"].isoformat(): r for r in monthly_records}

    # 填充每一天的資料
    current_date = first_day
    today = date.today()

    while current_date <= last_day:
        date_str = current_date.isoformat()

        # 獲取該日的待複習知識點
        due_reviews = []
        for kp in knowledge_points:
            if hasattr(kp, "next_review") and kp.next_review:
                review_date = datetime.fromisoformat(kp.next_review).date()
                if review_date == current_date:
                    due_reviews.append(
                        {
                            "id": kp.id,
                            "key_point": kp.key_point,
                            "mastery_level": kp.mastery_level
                            if hasattr(kp, "mastery_level")
                            else 0,
                        }
                    )

        # 從數據庫記錄中獲取已完成的記錄
        daily_record = records_dict.get(date_str, {})
        completed_reviews = daily_record.get("completed_reviews", []) if daily_record else []
        new_practices = daily_record.get("new_practices", 0) if daily_record else 0

        day_info = {
            "date": current_date.day,
            "date_str": date_str,
            "is_today": current_date == today,
            "is_future": current_date > today,
            "is_past": current_date < today,
            "weekday": current_date.strftime("%a"),
            "reviews_pending": len(due_reviews),
            "reviews_completed": len(completed_reviews),
            "new_practices": new_practices,
            "study_intensity": calc_intensity(daily_record),
            "has_activity": bool(completed_reviews or new_practices),
        }

        month_data["days"].append(day_info)
        current_week.append(day_info)

        # 更新統計
        month_data["stats"]["total_reviews_pending"] += len(due_reviews)
        month_data["stats"]["total_completed"] += len(completed_reviews)

        # 如果一週結束或月份結束，添加到週列表
        if current_date.weekday() == 6 or current_date == last_day:
            # 填充週末的空白天
            while len(current_week) < 7:
                current_week.append(None)
            month_data["weeks"].append(current_week)
            current_week = []

        current_date += timedelta(days=1)

    return month_data


def calc_intensity(daily_record: dict) -> str:
    """計算學習強度等級"""
    if not daily_record:
        return "none"

    completed_reviews = daily_record.get("completed_reviews", [])
    new_practices = daily_record.get("new_practices", 0)

    total_activities = (len(completed_reviews) if completed_reviews else 0) + new_practices

    if total_activities == 0:
        return "none"
    elif total_activities <= 2:
        return "light"
    elif total_activities <= 5:
        return "medium"
    else:
        return "heavy"


@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse)  # 修復 307 重定向：同時支持 /calendar 和 /calendar/
async def calendar_page(request: Request, year: Optional[int] = None, month: Optional[int] = None):
    """日曆主頁面"""
    # 默認顯示當前月份
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month

    # 獲取月份資料
    month_data = await get_month_data(year, month)  # TASK-31: 調用異步函數

    # 計算上一月和下一月
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "active": "calendar",
            "month_data": month_data,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "current_year": now.year,
            "current_month": now.month,
        },
    )


# 注意：由於router使用了prefix="/calendar"，這裡只需要定義/api/day/{date}部分
@router.get("/api/day/{date}")
async def get_day_details(date_str: str):
    """獲取特定日期的詳細資料"""
    try:
        target_date = datetime.fromisoformat(date_str).date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format") from e

    km = await get_know_service()  # TASK-31: 使用純異步服務
    knowledge_points = await km.get_knowledge_points_async()

    # 獲取該日的待複習知識點
    due_reviews = []
    for kp in knowledge_points:
        if hasattr(kp, "next_review") and kp.next_review:
            review_date = datetime.fromisoformat(kp.next_review).date()
            if review_date == target_date:
                due_reviews.append(
                    {
                        "id": kp.id,
                        "key_point": kp.key_point,
                        "original_phrase": kp.original_phrase
                        if hasattr(kp, "original_phrase")
                        else "",
                        "correction": kp.correction if hasattr(kp, "correction") else "",
                        "mastery_level": kp.mastery_level if hasattr(kp, "mastery_level") else 0,
                        "category": kp.category.value if hasattr(kp, "category") else "other",
                        "mistake_count": kp.mistake_count if hasattr(kp, "mistake_count") else 0,
                    }
                )

    # 從數據庫獲取已完成的記錄
    daily_record = await calendar_manager.get_day_details(target_date)

    return {
        "date": date_str,
        "due_reviews": due_reviews,
        "completed_reviews": daily_record.get("completed_reviews", []),
        "new_practices": daily_record.get("new_practices", 0),
        "total_mistakes": daily_record.get("total_mistakes", 0),
        "study_minutes": daily_record.get("study_minutes", 0),
        "mastery_improvement": daily_record.get("mastery_improvement", 0),
        "study_sessions": daily_record.get("study_sessions", []),
    }


@router.post("/api/complete-review/{point_id}")
async def mark_review_complete(point_id: int):
    """標記複習完成"""
    today = date.today()
    success = await calendar_manager.mark_review_complete(point_id, today)

    if success:
        return {"status": "success", "point_id": point_id, "date": today.isoformat()}
    else:
        return {"status": "already_completed", "point_id": point_id, "date": today.isoformat()}


@router.get("/api/stats/streak")
async def get_streak_stats():
    """獲取連續學習統計"""
    stats = await calendar_manager.get_streak_stats()
    return stats


@router.get("/api/stats")
async def get_calendar_stats():
    """獲取日曆統計資料"""
    stats = await calendar_manager.get_streak_stats()

    # 可以添加更多統計資料
    return {
        "streak": stats,
        "summary": {
            "current_streak": stats["current_streak"],
            "best_streak": stats["best_streak"],
            "month_active_days": stats["month_active_days"],
        },
    }
