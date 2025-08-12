"""
Tag system routes for the Linker web application.
"""
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from web.dependencies import get_ai_service, get_logger

router = APIRouter()
logger = get_logger()

@router.post("/api/generate-tagged-question", response_class=JSONResponse)
async def generate_tagged_question_api(request: Request):
    """API 端點：生成標籤題目"""
    ai = get_ai_service()

    try:
        data = await request.json()
        tags = data.get("tags", [])
        combination_mode = data.get("combinationMode", "all")
        length = data.get("length", "medium")
        level = data.get("level", 2)

        logger.info(f"Generate tagged question: tags={tags}, mode={combination_mode}")

        # 生成標籤題目
        result = ai.generate_tagged_sentence(
            tags=tags,
            level=level,
            length=length,
            combination_mode=combination_mode
        )

        return JSONResponse({
            "success": True,
            "chinese": result.get("sentence", ""),
            "hint": result.get("hint", ""),
            "covered_points": result.get("covered_points", []),
            "expected_patterns": result.get("expected_patterns", []),
            "tags": result.get("tags", []),
            "combination_mode": result.get("combination_mode", "")
        })

    except Exception as e:
        logger.error(f"Error generating tagged question: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/api/preview-tagged-question", response_class=JSONResponse)
async def preview_tagged_question(request: Request):
    """預覽標籤組合題目"""
    ai = get_ai_service()

    try:
        data = await request.json()
        tags = data.get("tags", [])
        mode = data.get("mode", "all")

        # 生成預覽題目
        preview = ai.generate_tagged_preview(
            tags=tags,
            combination_mode=mode
        )

        return JSONResponse({
            "success": True,
            "chinese": preview.get("sentence", ""),
            "hint": preview.get("hint", ""),
            "covered_points": preview.get("covered_points", []),
            "expected_patterns": preview.get("expected_patterns", []),
            "stats": {
                "estimated_difficulty": preview.get("difficulty", 2),
                "question_variety": preview.get("variety_score", 50)
            }
        })
    except Exception as e:
        logger.error(f"Error previewing tagged question: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/api/tags", response_class=JSONResponse)
async def get_tags(request: Request, type: Optional[str] = None, category: Optional[str] = None):
    """獲取可用標籤列表"""
    try:
        from core.tag_system import TagType, tag_manager

        if type:
            try:
                tag_type = TagType(type)
                tags = tag_manager.get_tags_by_type(tag_type)
            except ValueError:
                tags = []
        elif category:
            tags = tag_manager.get_tags_by_category(category)
        else:
            tags = list(tag_manager.tags.values())

        # 轉換為可序列化格式
        tags_data = []
        for tag in tags:
            tags_data.append({
                "id": tag.id,
                "type": tag.type.value,
                "name": tag.name,
                "description": tag.description,
                "category": tag.category,
                "complexity": tag.complexity,
                "usage_count": tag.usage_count,
                "success_rate": round(tag.success_rate, 2)
            })

        return JSONResponse({
            "success": True,
            "tags": tags_data
        })
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.post("/api/validate-tag-combination", response_class=JSONResponse)
async def validate_tag_combination(request: Request):
    """驗證標籤組合的合理性"""
    try:
        from core.tag_system import tag_manager

        data = await request.json()
        tag_ids = data.get("tags", [])

        validation = tag_manager.validate_combination(tag_ids)

        return JSONResponse({
            "success": True,
            "validation": validation
        })
    except Exception as e:
        logger.error(f"Error validating tag combination: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/api/tag-templates", response_class=JSONResponse)
async def get_tag_templates(request: Request):
    """獲取標籤組合模板"""
    try:
        from core.tag_system import tag_manager

        templates = tag_manager.get_all_templates()

        # 轉換為可序列化格式
        templates_data = {}
        for name, template in templates.items():
            templates_data[name] = {
                "name": name,
                "description": template.description,
                "tags": [{"id": t.id, "name": t.name} for t in template.tags],
                "mode": template.mode.value
            }

        return JSONResponse({
            "success": True,
            "templates": templates_data
        })
    except Exception as e:
        logger.error(f"Error getting tag templates: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
