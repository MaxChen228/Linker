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

from web.dependencies import get_knowledge_manager

router = APIRouter(prefix="/calendar", tags=["calendar"])
templates = Jinja2Templates(directory="web/templates")

# 資料檔案路徑
DATA_DIR = Path("data")
CALENDAR_FILE = DATA_DIR / "learning_calendar.json"
PRACTICE_LOG_FILE = DATA_DIR / "practice_log.json"


def ensure_calendar_file():
    """確保日曆資料檔案存在"""
    if not CALENDAR_FILE.exists():
        initial_data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "daily_records": {},
            "weekly_goals": {},
            "study_sessions": [],
        }
        with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)


def load_calendar_data() -> dict:
    """載入日曆資料"""
    ensure_calendar_file()
    with open(CALENDAR_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_calendar_data(data: dict):
    """儲存日曆資料"""
    data["last_updated"] = datetime.now().isoformat()
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_month_calendar_data(year: int, month: int) -> dict:
    """獲取指定月份的日曆資料"""
    km = get_knowledge_manager()
    knowledge_points = km.knowledge_points
    calendar_data = load_calendar_data()

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

        # 從日曆資料中獲取已完成的記錄
        daily_record = calendar_data["daily_records"].get(date_str, {})

        day_info = {
            "date": current_date.day,
            "date_str": date_str,
            "is_today": current_date == today,
            "is_future": current_date > today,
            "is_past": current_date < today,
            "weekday": current_date.strftime("%a"),
            "reviews_pending": len(due_reviews),
            "reviews_completed": len(daily_record.get("completed_reviews", [])),
            "new_practices": daily_record.get("new_practices", 0),
            "study_intensity": calculate_study_intensity(daily_record),
            "has_activity": bool(daily_record),
        }

        month_data["days"].append(day_info)
        current_week.append(day_info)

        # 更新統計
        month_data["stats"]["total_reviews_pending"] += len(due_reviews)
        month_data["stats"]["total_completed"] += len(daily_record.get("completed_reviews", []))

        # 如果一週結束或月份結束，添加到週列表
        if current_date.weekday() == 6 or current_date == last_day:
            # 填充週末的空白天
            while len(current_week) < 7:
                current_week.append(None)
            month_data["weeks"].append(current_week)
            current_week = []

        current_date += timedelta(days=1)

    return month_data


def calculate_study_intensity(daily_record: dict) -> str:
    """計算學習強度等級"""
    if not daily_record:
        return "none"

    total_activities = len(daily_record.get("completed_reviews", [])) + daily_record.get(
        "new_practices", 0
    )

    if total_activities == 0:
        return "none"
    elif total_activities <= 2:
        return "light"
    elif total_activities <= 5:
        return "medium"
    else:
        return "heavy"


@router.get("/", response_class=HTMLResponse)
async def calendar_page(request: Request, year: Optional[int] = None, month: Optional[int] = None):
    """日曆主頁面"""
    # 默認顯示當前月份
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month

    # 獲取月份資料
    month_data = get_month_calendar_data(year, month)

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


@router.get("/api/day/{date_str}")
async def get_day_details(date_str: str):
    """獲取特定日期的詳細資料"""
    try:
        target_date = datetime.fromisoformat(date_str).date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date format") from e

    km = get_knowledge_manager()
    knowledge_points = km.knowledge_points
    calendar_data = load_calendar_data()

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

    # 獲取已完成的記錄
    daily_record = calendar_data["daily_records"].get(date_str, {})

    return {
        "date": date_str,
        "due_reviews": due_reviews,
        "completed_reviews": daily_record.get("completed_reviews", []),
        "new_practices": daily_record.get("new_practices", 0),
        "total_mistakes": daily_record.get("total_mistakes", 0),
        "study_minutes": daily_record.get("study_minutes", 0),
        "mastery_improvement": daily_record.get("mastery_improvement", 0),
        "study_sessions": [
            s for s in calendar_data.get("study_sessions", []) if s.get("date") == date_str
        ],
    }


@router.post("/api/complete-review/{point_id}")
async def mark_review_complete(point_id: int):
    """標記複習完成"""
    today = date.today().isoformat()
    calendar_data = load_calendar_data()

    # 確保當日記錄存在
    if today not in calendar_data["daily_records"]:
        calendar_data["daily_records"][today] = {
            "planned_reviews": [],
            "completed_reviews": [],
            "new_practices": 0,
            "total_mistakes": 0,
            "study_minutes": 0,
            "mastery_improvement": 0,
        }

    # 添加到已完成列表（避免重複）
    if point_id not in calendar_data["daily_records"][today]["completed_reviews"]:
        calendar_data["daily_records"][today]["completed_reviews"].append(point_id)

    save_calendar_data(calendar_data)

    return {"status": "success", "point_id": point_id, "date": today}


@router.get("/api/stats/streak")
async def get_streak_stats():
    """獲取連續學習統計"""
    calendar_data = load_calendar_data()
    today = date.today()

    # 計算連續學習天數
    streak = 0
    current_date = today

    while True:
        date_str = current_date.isoformat()
        if date_str in calendar_data["daily_records"]:
            record = calendar_data["daily_records"][date_str]
            if record.get("completed_reviews") or record.get("new_practices"):
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        else:
            break

    # 計算本月學習天數
    month_start = date(today.year, today.month, 1)
    month_days = 0
    current_date = month_start

    while current_date <= today:
        date_str = current_date.isoformat()
        if date_str in calendar_data["daily_records"]:
            record = calendar_data["daily_records"][date_str]
            if record.get("completed_reviews") or record.get("new_practices"):
                month_days += 1
        current_date += timedelta(days=1)

    return {
        "current_streak": streak,
        "month_active_days": month_days,
        "best_streak": calculate_best_streak(calendar_data),
    }


def calculate_best_streak(calendar_data: dict) -> int:
    """計算最長連續學習天數"""
    if not calendar_data["daily_records"]:
        return 0

    # 按日期排序所有記錄
    sorted_dates = sorted(calendar_data["daily_records"].keys())

    best_streak = 0
    current_streak = 0
    prev_date = None

    for date_str in sorted_dates:
        record = calendar_data["daily_records"][date_str]
        if record.get("completed_reviews") or record.get("new_practices"):
            current_date = datetime.fromisoformat(date_str).date()

            if prev_date and (current_date - prev_date).days == 1:
                current_streak += 1
            else:
                current_streak = 1

            best_streak = max(best_streak, current_streak)
            prev_date = current_date

    return best_streak
