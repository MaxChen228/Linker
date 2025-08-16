"""
Knowledge management API routes (Fixed routing order)
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.exceptions import KnowledgeNotFoundError

# TASK-34: 引入統一API端點管理系統，消除硬編碼
# 注意：由於router使用prefix="/api/knowledge"，路由定義只需要相對路徑
from web.config.api_endpoints import API_ENDPOINTS
from web.dependencies import (
    get_know_service,  # TASK-31: 使用新的純異步服務
    get_logger,
)
from web.models.validation import (
    BatchReq,
    DeleteKnowReq,
    DeleteOldPointsRequest,
    EditKnowReq,
    NotesRequest,
    TagsRequest,
)

router = APIRouter(prefix="/api/knowledge")
logger = get_logger()


# TASK-34: 輔助函數，從完整API路徑提取相對路徑
def _get_relative_path(full_path: str) -> str:
    """從完整API路徑提取相對於/api/knowledge的路徑

    Args:
        full_path: 完整路徑，如 "/api/knowledge/recommendations"

    Returns:
        相對路徑，如 "/recommendations"
    """
    prefix = "/api/knowledge"
    if full_path.startswith(prefix):
        return full_path[len(prefix) :] or "/"
    return full_path


class EditKnowledgeRequest(BaseModel):
    """編輯知識點請求"""

    key_point: Optional[str] = None
    explanation: Optional[str] = None
    original_phrase: Optional[str] = None
    correction: Optional[str] = None
    category: Optional[str] = None
    subtype: Optional[str] = None
    tags: Optional[list[str]] = None
    custom_notes: Optional[str] = None


class DeleteKnowledgeRequest(BaseModel):
    """刪除知識點請求"""

    reason: str = ""


class BatchOperation(str, Enum):
    """批量操作類型"""

    DELETE = "delete"
    UPDATE = "update"
    EXPORT = "export"
    TAG = "tag"
    RESTORE = "restore"


class BatchRequest(BaseModel):
    """批量操作請求"""

    operation: BatchOperation
    ids: list[int]
    data: Optional[dict[str, Any]] = None
    options: Optional[dict[str, Any]] = None


class BatchProgress(BaseModel):
    """批量操作進度"""

    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int
    total: int
    processed: int
    errors: list[dict[str, Any]] = []
    eta: Optional[str] = None
    result: Optional[dict[str, Any]] = None


class RecommendationParams(BaseModel):
    """推薦參數"""

    include_statistics: bool = True
    max_priority_points: int = 10


# 預設為預覽模式


# 批量操作任務存儲
batch_tasks: dict[str, BatchProgress] = {}


# ==================== 固定路徑路由（必須在動態路徑之前）====================


@router.get(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_RECOMMENDATIONS))
async def get_recommendations(params: RecommendationParams = RecommendationParams()):
    """獲取學習推薦

    根據用戶的學習歷史和掌握度提供個性化推薦

    Returns:
        包含推薦內容、重點領域、建議難度等信息
    """
    km = await get_know_service()  # TASK-31: 使用純異步服務

    try:
        recommendations = await km.get_recommendations_async()

        # 根據參數調整輸出
        if not params.include_statistics:
            recommendations.pop("statistics", None)

        if params.max_priority_points < len(recommendations.get("priority_points", [])):
            recommendations["priority_points"] = recommendations["priority_points"][
                : params.max_priority_points
            ]

        return JSONResponse({"success": True, "data": recommendations})
    except Exception as e:
        logger.error(f"獲取推薦失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取推薦失敗: {str(e)}") from e


@router.get(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_TRASH_LIST))
async def get_trash_list():
    """獲取回收站中的知識點列表"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務
    deleted_points = await knowledge.get_deleted_points_async()

    # 轉換為字典列表
    trash_items = []
    for point in deleted_points:
        item = {
            "id": point.id,
            "key_point": point.key_point,
            "original_phrase": point.original_phrase,
            "correction": point.correction,
            "category": point.category.value,
            "deleted_at": point.deleted_at,
            "deleted_reason": point.deleted_reason,
            "mastery_level": point.mastery_level,
            "mistake_count": point.mistake_count,
        }
        trash_items.append(item)

    # 按刪除時間排序（最新的在前）
    trash_items.sort(key=lambda x: x["deleted_at"], reverse=True)

    return JSONResponse({"success": True, "count": len(trash_items), "items": trash_items})


@router.post(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_TRASH_CLEAR))
async def clear_old_trash(days: int = 30):
    """清理超過指定天數的回收站項目"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    deleted_count = await knowledge.permanent_delete_old_points(days)  # TASK-31: 添加 await

    logger.info(f"清理回收站：永久刪除了 {deleted_count} 個知識點")

    return JSONResponse(
        {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"已永久刪除 {deleted_count} 個超過 {days} 天的知識點",
        }
    )


@router.post(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_BATCH))
async def batch_operation(request: BatchReq, background_tasks: BackgroundTasks):
    """批量操作端點"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    # 將字符串操作轉換為枚舉
    try:
        operation_enum = BatchOperation(request.operation)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"不支持的操作類型: {request.operation}"
        ) from None

    # 生成任務 ID
    task_id = str(uuid.uuid4())

    # 創建任務記錄
    task = BatchProgress(
        task_id=task_id,
        status="pending",
        progress=0,
        total=len(request.ids),
        processed=0,
        errors=[],
    )
    batch_tasks[task_id] = task

    # 判斷是否需要異步處理
    if len(request.ids) > 50 or (request.options and request.options.get("async")):
        # 異步處理
        background_tasks.add_task(
            process_batch,
            task_id,
            operation_enum,
            request.ids,
            request.data,
            knowledge,
        )

        return JSONResponse(
            {
                "success": True,
                "async": True,
                "task_id": task_id,
                "message": f"批量操作已開始，共 {len(request.ids)} 項",
            }
        )

    else:
        # 同步處理
        await process_batch(task_id, operation_enum, request.ids, request.data, knowledge)

        task = batch_tasks[task_id]

        return JSONResponse(
            {
                "success": task.status == "completed",
                "async": False,
                "task_id": task_id,
                "processed": task.processed,
                "errors": task.errors,
                "result": task.result,
            }
        )


@router.get(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_BATCH_PROGRESS))
async def get_batch_progress(task_id: str):
    """查詢批量操作進度"""
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="任務不存在")

    task = batch_tasks[task_id]

    return JSONResponse(task.dict())


@router.delete(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_BATCH_DELETE))
async def cancel_batch(
    task_id: str = Path(..., min_length=8, max_length=100, description="批量任務ID"),
):
    """取消批量操作"""
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="任務不存在")

    task = batch_tasks[task_id]

    if task.status == "processing":
        # TODO: 實作取消邏輯
        return JSONResponse({"success": False, "message": "暫不支援取消進行中的任務"})

    # 清理已完成的任務
    del batch_tasks[task_id]

    return JSONResponse({"success": True, "message": "任務已清理"})


@router.post(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_DELETE_OLD))
async def delete_old_points(request: DeleteOldPointsRequest):
    """永久刪除舊的已刪除知識點

    清理回收站中超過指定天數的知識點，但保留高價值知識點

    Args:
        days_old: 刪除多少天前的知識點
        dry_run: 是否只是預覽不實際刪除

    Returns:
        刪除統計信息
    """
    km = await get_know_service()  # TASK-31: 使用純異步服務

    try:
        result = await km.permanent_delete_old_points(
            days_old=request.days_old, dry_run=request.dry_run
        )  # TASK-31: 添加 await

        return JSONResponse(
            {
                "success": True,
                "data": result,
                "message": "預覽完成" if request.dry_run else "刪除完成",
            }
        )
    except Exception as e:
        logger.error(f"刪除舊知識點失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除失敗: {str(e)}") from e


# ==================== 動態路徑路由（必須在固定路徑之後）====================


@router.get(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_DETAIL))
async def get_knowledge_point(point_id: int):
    """獲取單個知識點詳情"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    try:
        point = await knowledge.get_knowledge_point_async(str(point_id))  # TASK-31: 使用異步方法
    except KnowledgeNotFoundError as e:
        return JSONResponse(
            status_code=404,
            content={"error_code": e.error_code, "detail": e.message, "point_id": e.point_id},
        )

    if not point:
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "KNOWLEDGE_NOT_FOUND",
                "detail": "知識點不存在",
                "point_id": str(point_id),
            },
        )

    if point.is_deleted:
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "KNOWLEDGE_NOT_FOUND",
                "detail": "知識點已被刪除",
                "point_id": str(point_id),
            },
        )

    # TASK-31: KnowledgePoint 是 dataclass，需要處理 ErrorCategory Enum 序列化
    from dataclasses import asdict

    point_dict = asdict(point)
    # ErrorCategory 是 Enum，需要轉換為字符串
    if "category" in point_dict and hasattr(point_dict["category"], "value"):
        point_dict["category"] = point_dict["category"].value
    return JSONResponse(point_dict)


@router.put(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_DETAIL))
async def edit_knowledge_point(
    request: EditKnowReq,
    point_id: int = Path(..., ge=1, le=1000000, description="知識點ID"),
):
    """編輯知識點"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    # 過濾掉 None 值
    updates = {k: v for k, v in request.dict().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="沒有提供要更新的內容")

    history = await knowledge.edit_knowledge_point_async(point_id, updates)

    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")

    logger.info(f"編輯知識點 {point_id} 成功: {list(updates.keys())}")

    return JSONResponse({"success": True, "message": "知識點已更新", "history": history})


@router.delete(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_DETAIL))
async def delete_point(
    request: DeleteKnowReq,
    point_id: int = Path(..., ge=1, le=1000000, description="知識點ID"),
):
    """軟刪除知識點"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    success = await knowledge.delete_point_async(point_id, request.reason)

    if not success:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")

    logger.info(f"刪除知識點 {point_id} 成功")

    return JSONResponse({"success": True, "message": "知識點已移至回收站"})


@router.post(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_RESTORE))
async def restore_point(
    point_id: int = Path(..., ge=1, le=1000000, description="知識點ID"),
):
    """復原刪除的知識點"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    success = await knowledge.restore_point_async(point_id)

    if not success:
        raise HTTPException(status_code=404, detail="找不到已刪除的知識點")

    logger.info(f"復原知識點 {point_id} 成功")

    return JSONResponse({"success": True, "message": "知識點已復原"})


@router.post(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_TAGS))
async def update_tags(
    request: TagsRequest, point_id: int = Path(..., ge=1, le=1000000, description="知識點ID")
):
    """更新知識點標籤"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    history = await knowledge.edit_knowledge_point_async(point_id, {"tags": request.tags})

    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")

    return JSONResponse({"success": True, "message": "標籤已更新", "tags": request.tags})


@router.post(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_NOTES))
async def update_notes(
    request: NotesRequest, point_id: int = Path(..., ge=1, le=1000000, description="知識點ID")
):
    """更新知識點筆記"""
    knowledge = await get_know_service()  # TASK-31: 使用純異步服務

    history = await knowledge.edit_knowledge_point_async(point_id, {"custom_notes": request.notes})

    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")

    return JSONResponse({"success": True, "message": "筆記已更新", "notes": request.notes})


# ==================== 批量操作處理函數 ====================


async def process_batch(
    task_id: str,
    operation: BatchOperation,
    ids: list[int],
    data: Optional[dict[str, Any]],
    knowledge_manager,
):
    """異步處理批量操作"""
    task = batch_tasks[task_id]
    task.status = "processing"

    try:
        if operation == BatchOperation.DELETE:
            # 批量刪除
            reason = data.get("reason", "") if data else ""
            for i, point_id in enumerate(ids):
                try:
                    success = await knowledge_manager.delete_point_async(point_id, reason)
                    if not success:
                        task.errors.append({"id": point_id, "error": "刪除失敗"})
                except Exception as e:
                    task.errors.append({"id": point_id, "error": str(e)})

                task.processed = i + 1
                task.progress = int((task.processed / task.total) * 100)

                # 避免阻塞
                if i % 10 == 0:
                    await asyncio.sleep(0.1)

        elif operation == BatchOperation.UPDATE:
            # 批量更新
            updates = data or {}
            for i, point_id in enumerate(ids):
                try:
                    history = await knowledge_manager.edit_knowledge_point_async(point_id, updates)
                    if not history:
                        task.errors.append({"id": point_id, "error": "更新失敗"})
                except Exception as e:
                    task.errors.append({"id": point_id, "error": str(e)})

                task.processed = i + 1
                task.progress = int((task.processed / task.total) * 100)

                if i % 10 == 0:
                    await asyncio.sleep(0.1)

        elif operation == BatchOperation.TAG:
            # 批量添加標籤
            tags = data.get("tags", []) if data else []
            for i, point_id in enumerate(ids):
                try:
                    point = await knowledge_manager.get_knowledge_point_async(point_id)
                    if point:
                        existing_tags = point.tags or []
                        new_tags = list(set(existing_tags + tags))
                        await knowledge_manager.edit_knowledge_point_async(
                            point_id, {"tags": new_tags}
                        )
                    else:
                        task.errors.append({"id": point_id, "error": "知識點不存在"})
                except Exception as e:
                    task.errors.append({"id": point_id, "error": str(e)})

                task.processed = i + 1
                task.progress = int((task.processed / task.total) * 100)

                if i % 10 == 0:
                    await asyncio.sleep(0.1)

        elif operation == BatchOperation.EXPORT:
            # 批量導出
            export_data = []
            for i, point_id in enumerate(ids):
                try:
                    point = await knowledge_manager.get_knowledge_point_async(point_id)
                    if point:
                        export_data.append(point.to_dict())
                    else:
                        task.errors.append({"id": point_id, "error": "知識點不存在"})
                except Exception as e:
                    task.errors.append({"id": point_id, "error": str(e)})

                task.processed = i + 1
                task.progress = int((task.processed / task.total) * 100)

            task.result = {
                "data": export_data,
                "format": data.get("format", "json") if data else "json",
            }

        elif operation == BatchOperation.RESTORE:
            # 批量復原
            for i, point_id in enumerate(ids):
                try:
                    success = await knowledge_manager.restore_point_async(point_id)
                    if not success:
                        task.errors.append({"id": point_id, "error": "復原失敗"})
                except Exception as e:
                    task.errors.append({"id": point_id, "error": str(e)})

                task.processed = i + 1
                task.progress = int((task.processed / task.total) * 100)

                if i % 10 == 0:
                    await asyncio.sleep(0.1)

        task.status = "completed"
        task.eta = datetime.now().isoformat()

    except Exception as e:
        task.status = "failed"
        task.errors.append({"error": f"批量操作失敗: {str(e)}"})
        logger.error(f"批量操作失敗: {e}")


# ==================== TASK-32: 每日知識點上限功能 ====================


class LimitConfigReq(BaseModel):
    """每日限額配置請求"""

    daily_limit: Optional[int] = None
    limit_enabled: Optional[bool] = None


@router.get(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_DAILY_LIMIT_STATUS))
async def get_daily_limit_status():
    """獲取每日限額狀態"""
    knowledge = await get_know_service()

    try:
        # 獲取今日狀態（假設是 isolated 類型來獲取狀態）
        limit_status = await knowledge.check_daily_limit("isolated")
        config = await knowledge.get_daily_limit_config()

        return JSONResponse(
            {
                "date": limit_status.get("date", ""),
                "limit_enabled": config["limit_enabled"],
                "daily_limit": config["daily_knowledge_limit"],
                "used_count": limit_status.get("used_count", 0),
                "remaining": limit_status.get("remaining", config["daily_knowledge_limit"]),
                "can_add_more": limit_status.get("can_add", True),
                "breakdown": limit_status.get("breakdown", {"isolated": 0, "enhancement": 0}),
                "status": "normal" if limit_status.get("can_add", True) else "exceeded",
            }
        )

    except Exception as e:
        logger.error(f"獲取每日限額狀態失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取限額狀態失敗") from e


@router.get(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_DAILY_LIMIT_CONFIG))
async def get_daily_limit_config():
    """獲取每日限額配置"""
    knowledge = await get_know_service()
    try:
        config = await knowledge.get_daily_limit_config()
        # 讓 FastAPI 自動處理序列化，而不是手動使用 JSONResponse
        return config
    except Exception as e:
        logger.error(f"獲取每日限額配置失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取配置失敗") from e


@router.put(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_DAILY_LIMIT_CONFIG))
async def update_daily_limit_config(request: LimitConfigReq):
    """更新每日限額配置"""
    knowledge = await get_know_service()

    try:
        result = await knowledge.update_daily_limit_config(
            daily_limit=request.daily_limit, limit_enabled=request.limit_enabled
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        logger.info(f"每日限額配置已更新: {result['config']}")
        return JSONResponse(result)

    except Exception as e:
        logger.error(f"更新每日限額配置失敗: {e}")
        raise HTTPException(status_code=500, detail="配置更新失敗") from e


@router.get(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_DAILY_LIMIT_STATS))
async def get_daily_limit_stats(days: int = 7):
    """獲取每日限額使用統計

    Args:
        days: 查詢天數 (1-30)
    """
    if not (1 <= days <= 30):
        raise HTTPException(status_code=400, detail="天數範圍應在 1-30 之間")

    knowledge = await get_know_service()

    try:
        stats = await knowledge.get_daily_limit_stats(days)

        # 計算建議上限
        summary = stats["summary"]
        avg_usage = summary["avg_daily_usage"]
        current_limit = summary["current_limit"]

        suggested_limit = current_limit
        if avg_usage > 0:
            if avg_usage >= current_limit * 0.9:
                suggested_limit = min(50, int(avg_usage * 1.2))
            elif avg_usage <= current_limit * 0.5:
                suggested_limit = max(5, int(avg_usage * 1.5))

        return JSONResponse(
            {"stats": stats["stats"], "summary": {**summary, "suggested_limit": suggested_limit}}
        )

    except Exception as e:
        logger.error(f"獲取每日限額統計失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取統計數據失敗") from e


@router.post(_get_relative_path(API_ENDPOINTS.KNOWLEDGE_SAVE_WITH_LIMIT))
async def save_with_limit(knowledge_point: dict):
    """帶限額檢查的知識點儲存

    這是一個新的API端點，用於從前端練習頁面儲存知識點時進行限額檢查
    """
    knowledge = await get_know_service()

    try:
        # 這裡需要將 dict 轉換為 KnowledgePoint 物件
        # 簡化版本，實際使用時需要完整的轉換邏輯
        from core.error_types import ErrorCategory
        from core.models import KnowledgePoint, OriginalError

        # 創建 OriginalError 物件
        original_error = OriginalError(
            chinese_sentence=knowledge_point.get("chinese_sentence", ""),
            user_answer=knowledge_point.get("user_answer", ""),
            correct_answer=knowledge_point.get("correct_answer", ""),
            timestamp=knowledge_point.get("timestamp", ""),
        )

        # 創建 KnowledgePoint 物件
        kp = KnowledgePoint(
            id=0,  # 新建時為 0
            key_point=knowledge_point.get("key_point", ""),
            category=ErrorCategory(knowledge_point.get("category", "other")),
            subtype=knowledge_point.get("subtype", ""),
            explanation=knowledge_point.get("explanation", ""),
            original_phrase=knowledge_point.get("original_phrase", ""),
            correction=knowledge_point.get("correction", ""),
            original_error=original_error,
        )

        # 使用帶限額檢查的儲存方法
        result = await knowledge.save_with_limit(kp)

        if result["success"]:
            return JSONResponse(
                {
                    "success": True,
                    "message": result["message"],
                    "limit_status": result["limit_status"],
                }
            )
        else:
            # 達到上限或其他錯誤
            return JSONResponse(
                status_code=200,  # 不是伺服器錯誤，是業務邏輯
                content={
                    "success": False,
                    "reason": result["reason"],
                    "message": result["message"],
                    "limit_status": result["limit_status"],
                    "suggestion": result.get("suggestion", ""),
                },
            )

    except Exception as e:
        logger.error(f"帶限額檢查的知識點儲存失敗: {e}")
        raise HTTPException(status_code=500, detail="知識點儲存失敗") from e
