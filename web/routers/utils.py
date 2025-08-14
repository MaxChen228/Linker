"""
Utility routes for the Linker web application.
"""

from fastapi import APIRouter

from web.dependencies import STATIC_DIR, TEMPLATES_DIR

router = APIRouter()


@router.get("/healthz")
def healthz():
    """健康檢查端點"""
    # 簡易健康檢查：確保模板與資料夾存在
    ok = TEMPLATES_DIR.exists() and STATIC_DIR.exists()
    return {"status": "ok" if ok else "degraded"}
