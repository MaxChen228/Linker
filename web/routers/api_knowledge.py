"""
Knowledge management API routes
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from web.dependencies import get_knowledge_manager, get_logger

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


@router.get("/{point_id}")
async def get_knowledge_point(point_id: int):
    """獲取單個知識點詳情"""
    knowledge = get_knowledge_manager()
    point = knowledge.get_knowledge_point(str(point_id))
    
    if not point:
        raise HTTPException(status_code=404, detail="知識點不存在")
    
    if point.is_deleted:
        raise HTTPException(status_code=404, detail="知識點已被刪除")
    
    return JSONResponse(point.to_dict())


@router.put("/{point_id}")
async def edit_knowledge_point(point_id: int, request: EditKnowledgeRequest):
    """編輯知識點"""
    knowledge = get_knowledge_manager()
    
    # 過濾掉 None 值
    updates = {k: v for k, v in request.dict().items() if v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="沒有提供要更新的內容")
    
    history = knowledge.edit_knowledge_point(point_id, updates)
    
    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")
    
    logger.info(f"編輯知識點 {point_id} 成功: {list(updates.keys())}")
    
    return JSONResponse({
        "success": True,
        "message": "知識點已更新",
        "history": history
    })


@router.delete("/{point_id}")
async def delete_knowledge_point(point_id: int, request: DeleteKnowledgeRequest):
    """軟刪除知識點"""
    knowledge = get_knowledge_manager()
    
    success = knowledge.delete_knowledge_point(point_id, request.reason)
    
    if not success:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")
    
    logger.info(f"刪除知識點 {point_id} 成功")
    
    return JSONResponse({
        "success": True,
        "message": "知識點已移至回收站"
    })


@router.post("/{point_id}/restore")
async def restore_knowledge_point(point_id: int):
    """復原刪除的知識點"""
    knowledge = get_knowledge_manager()
    
    success = knowledge.restore_knowledge_point(point_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="找不到已刪除的知識點")
    
    logger.info(f"復原知識點 {point_id} 成功")
    
    return JSONResponse({
        "success": True,
        "message": "知識點已復原"
    })


@router.get("/trash/list")
async def get_trash_list():
    """獲取回收站中的知識點列表"""
    knowledge = get_knowledge_manager()
    deleted_points = knowledge.get_deleted_points()
    
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
            "mistake_count": point.mistake_count
        }
        trash_items.append(item)
    
    # 按刪除時間排序（最新的在前）
    trash_items.sort(key=lambda x: x["deleted_at"], reverse=True)
    
    return JSONResponse({
        "success": True,
        "count": len(trash_items),
        "items": trash_items
    })


@router.post("/trash/clear")
async def clear_old_trash(days: int = 30):
    """清理超過指定天數的回收站項目"""
    knowledge = get_knowledge_manager()
    
    deleted_count = knowledge.permanent_delete_old_points(days)
    
    logger.info(f"清理回收站：永久刪除了 {deleted_count} 個知識點")
    
    return JSONResponse({
        "success": True,
        "deleted_count": deleted_count,
        "message": f"已永久刪除 {deleted_count} 個超過 {days} 天的知識點"
    })


@router.post("/{point_id}/tags")
async def update_tags(point_id: int, tags: list[str]):
    """更新知識點標籤"""
    knowledge = get_knowledge_manager()
    
    history = knowledge.edit_knowledge_point(point_id, {"tags": tags})
    
    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")
    
    return JSONResponse({
        "success": True,
        "message": "標籤已更新",
        "tags": tags
    })


@router.post("/{point_id}/notes")
async def update_notes(point_id: int, notes: str):
    """更新知識點筆記"""
    knowledge = get_knowledge_manager()
    
    history = knowledge.edit_knowledge_point(point_id, {"custom_notes": notes})
    
    if not history:
        raise HTTPException(status_code=404, detail="知識點不存在或已被刪除")
    
    return JSONResponse({
        "success": True,
        "message": "筆記已更新",
        "notes": notes
    })