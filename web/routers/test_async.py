"""
測試異步服務層 - TASK-31 概念驗證
用於驗證新的純異步架構是否正常工作
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from web.dependencies import get_async_knowledge_service, get_logger
from core.services import AsyncKnowledgeService

router = APIRouter(prefix="/api/test", tags=["test"])
logger = get_logger()


@router.get("/async-stats")
async def test_async_stats(
    service: AsyncKnowledgeService = Depends(get_async_knowledge_service)
):
    """測試異步統計功能
    
    這是一個簡單的測試端點，用於驗證：
    1. 異步服務可以正常初始化
    2. 沒有事件循環衝突
    3. 可以正確獲取統計資料
    """
    try:
        logger.info("測試異步統計 API - 開始")
        
        # 獲取統計資料
        stats = await service.get_statistics_async()
        
        logger.info(f"成功獲取統計資料: {stats}")
        
        return JSONResponse({
            "success": True,
            "message": "異步服務正常運作",
            "stats": stats,
            "service_type": "AsyncKnowledgeService"
        })
        
    except Exception as e:
        logger.error(f"測試異步統計失敗: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/async-review-candidates")
async def test_async_review_candidates(
    service: AsyncKnowledgeService = Depends(get_async_knowledge_service)
):
    """測試異步獲取複習候選
    
    這個端點測試更複雜的功能，涉及資料庫查詢和排序
    """
    try:
        logger.info("測試異步複習候選 API - 開始")
        
        # 獲取複習候選
        candidates = await service.get_review_candidates_async(max_points=5)
        
        # 轉換為可序列化格式
        result = []
        for point in candidates:
            result.append({
                "id": point.id,
                "key_point": point.key_point,
                "mastery_level": point.mastery_level,
                "last_seen": point.last_seen,
                "next_review": point.next_review
            })
        
        logger.info(f"成功獲取 {len(result)} 個複習候選")
        
        return JSONResponse({
            "success": True,
            "message": "異步複習候選功能正常",
            "count": len(result),
            "candidates": result,
            "service_type": "AsyncKnowledgeService"
        })
        
    except Exception as e:
        logger.error(f"測試異步複習候選失敗: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/service-health")
async def test_service_health(
    service: AsyncKnowledgeService = Depends(get_async_knowledge_service)
):
    """測試服務健康狀態"""
    try:
        health = await service.health_check()
        
        return JSONResponse({
            "success": True,
            "health": health,
            "message": "服務健康檢查完成"
        })
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)