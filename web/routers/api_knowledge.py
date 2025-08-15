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
from web.dependencies import (
    get_async_knowledge_service,  # TASK-31: 使用新的純異步服務
    get_knowledge_manager,
    get_knowledge_manager_async_dependency,  # 保留以備向後相容
    get_logger,
)
from web.models.validation import (
    DeleteOldPointsRequest,
    EnhancedBatchRequest,
    EnhancedDeleteKnowledgeRequest,
    EnhancedEditKnowledgeRequest,
    NotesRequest,
    TagsRequest,
)

router = APIRouter(prefix="/api/knowledge")
logger = get_logger()


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


@router.get("/recommendations")
async def get_learning_recommendations(params: RecommendationParams = RecommendationParams()):
    """獲取學習推薦

    根據用戶的學習歷史和掌握度提供個性化推薦

    Returns:
        包含推薦內容、重點領域、建議難度等信息
    """
    km = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    try:
        recommendations = await km.get_learning_recommendations_async()

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


@router.get("/trash/list")
async def get_trash_list():
    """獲取回收站中的知識點列表"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務
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


@router.post("/trash/clear")
async def clear_old_trash(days: int = 30):
    """清理超過指定天數的回收站項目"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    deleted_count = await knowledge.permanent_delete_old_points(days)  # TASK-31: 添加 await

    logger.info(f"清理回收站：永久刪除了 {deleted_count} 個知識點")

    return JSONResponse(
        {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"已永久刪除 {deleted_count} 個超過 {days} 天的知識點",
        }
    )


@router.post("/batch")
async def batch_operation(request: EnhancedBatchRequest, background_tasks: BackgroundTasks):
    """批量操作端點"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    # 將字符串操作轉換為枚舉
    try:
        operation_enum = BatchOperation(request.operation)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的操作類型: {request.operation}"
        )

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
            process_batch_operation,
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
        await process_batch_operation(
            task_id, operation_enum, request.ids, request.data, knowledge
        )

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


@router.get("/batch/{task_id}/progress")
async def get_batch_progress(task_id: str):
    """查詢批量操作進度"""
    if task_id not in batch_tasks:
        raise HTTPException(status_code=404, detail="任務不存在")

    task = batch_tasks[task_id]

    return JSONResponse(task.dict())


@router.delete("/batch/{task_id}")
async def cancel_batch_operation(
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


@router.post("/maintenance/delete-old-points")
async def delete_old_knowledge_points(request: DeleteOldPointsRequest):
    """永久刪除舊的已刪除知識點

    清理回收站中超過指定天數的知識點，但保留高價值知識點

    Args:
        days_old: 刪除多少天前的知識點
        dry_run: 是否只是預覽不實際刪除

    Returns:
        刪除統計信息
    """
    km = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    try:
        result = await km.permanent_delete_old_points(days_old=request.days_old, dry_run=request.dry_run)  # TASK-31: 添加 await

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


@router.get("/{point_id}")
async def get_knowledge_point(point_id: int):
    """獲取單個知識點詳情"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

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
    if 'category' in point_dict and hasattr(point_dict['category'], 'value'):
        point_dict['category'] = point_dict['category'].value
    return JSONResponse(point_dict)


@router.put("/{point_id}")
async def edit_knowledge_point(
    request: EnhancedEditKnowledgeRequest,
    point_id: int = Path(..., ge=1, le=1000000, description="知識點ID"),
):
    """編輯知識點"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    # 過濾掉 None 值
    updates = {k: v for k, v in request.dict().items() if v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="沒有提供要更新的內容")

    history = await knowledge.edit_knowledge_point_async(point_id, updates)

    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")

    logger.info(f"編輯知識點 {point_id} 成功: {list(updates.keys())}")

    return JSONResponse({"success": True, "message": "知識點已更新", "history": history})


@router.delete("/{point_id}")
async def delete_knowledge_point(
    request: EnhancedDeleteKnowledgeRequest,
    point_id: int = Path(..., ge=1, le=1000000, description="知識點ID"),
):
    """軟刪除知識點"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    success = await knowledge.delete_knowledge_point_async(point_id, request.reason)

    if not success:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")

    logger.info(f"刪除知識點 {point_id} 成功")

    return JSONResponse({"success": True, "message": "知識點已移至回收站"})


@router.post("/{point_id}/restore")
async def restore_knowledge_point(
    point_id: int = Path(..., ge=1, le=1000000, description="知識點ID"),
):
    """復原刪除的知識點"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    success = await knowledge.restore_knowledge_point_async(point_id)

    if not success:
        raise HTTPException(status_code=404, detail="找不到已刪除的知識點")

    logger.info(f"復原知識點 {point_id} 成功")

    return JSONResponse({"success": True, "message": "知識點已復原"})


@router.post("/{point_id}/tags")
async def update_tags(
    request: TagsRequest, point_id: int = Path(..., ge=1, le=1000000, description="知識點ID")
):
    """更新知識點標籤"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    history = await knowledge.edit_knowledge_point_async(point_id, {"tags": request.tags})

    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")

    return JSONResponse({"success": True, "message": "標籤已更新", "tags": request.tags})


@router.post("/{point_id}/notes")
async def update_notes(
    request: NotesRequest, point_id: int = Path(..., ge=1, le=1000000, description="知識點ID")
):
    """更新知識點筆記"""
    knowledge = await get_async_knowledge_service()  # TASK-31: 使用純異步服務

    history = await knowledge.edit_knowledge_point_async(point_id, {"custom_notes": request.notes})

    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")

    return JSONResponse({"success": True, "message": "筆記已更新", "notes": request.notes})


# ==================== 批量操作處理函數 ====================


async def process_batch_operation(
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
                    success = await knowledge_manager.delete_knowledge_point_async(point_id, reason)
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
                        await knowledge_manager.edit_knowledge_point_async(point_id, {"tags": new_tags})
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
                    success = await knowledge_manager.restore_knowledge_point_async(point_id)
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
