from fastapi import APIRouter, Request
from typing import Dict, Any
from loguru import logger

router = APIRouter()


@router.get(
    "/ping",
    tags=["Health Check"],
    description="检查服务可用性",
    response_description="pong",
)
def ping(request: Request) -> str:
    return "pong"


@router.get(
    "/health",
    tags=["Health Check"],
    description="Comprehensive health check with dependency status",
    response_description="Health status of API and dependencies",
)
def health_check(request: Request) -> Dict[str, Any]:
    """
    Check API and dependencies health
    Returns status and component details
    """
    health = {
        "status": "healthy",
        "components": {}
    }
    
    # Check semantic model
    try:
        from app.services.relevance import get_scorer
        scorer = get_scorer()
        # Check if model is loaded
        if scorer._model is not None:
            health["components"]["semantic_model"] = {
                "status": "ok",
                "loaded": True,
                "model": scorer.model_name
            }
        else:
            health["components"]["semantic_model"] = {
                "status": "ok",
                "loaded": False,
                "model": scorer.model_name
            }
    except Exception as e:
        health["components"]["semantic_model"] = {
            "status": "unavailable",
            "error": str(e)
        }
        health["status"] = "degraded"
    
    # Check video APIs (basic connectivity)
    try:
        from app.config import config
        pexels_keys = config.app.get("pexels_api_keys")
        pixabay_keys = config.app.get("pixabay_api_keys")
        
        health["components"]["video_apis"] = {
            "status": "ok",
            "pexels_configured": bool(pexels_keys),
            "pixabay_configured": bool(pixabay_keys)
        }
        
        if not pexels_keys and not pixabay_keys:
            health["components"]["video_apis"]["status"] = "unavailable"
            health["status"] = "degraded"
    except Exception as e:
        health["components"]["video_apis"] = {
            "status": "error",
            "error": str(e)
        }
        health["status"] = "degraded"
    
    # Check LLM provider
    try:
        from app.config import config
        llm_provider = config.app.get("llm_provider", "openai")
        health["components"]["llm"] = {
            "status": "ok",
            "provider": llm_provider
        }
    except Exception as e:
        health["components"]["llm"] = {
            "status": "error",
            "error": str(e)
        }
        health["status"] = "degraded"
    
    # Check storage directories
    try:
        from app.utils import utils
        import os
        
        task_dir = utils.task_dir()
        storage_dir = utils.storage_dir()
        
        health["components"]["storage"] = {
            "status": "ok",
            "task_dir_exists": os.path.exists(task_dir),
            "storage_dir_exists": os.path.exists(storage_dir),
            "task_dir_writable": os.access(task_dir, os.W_OK),
            "storage_dir_writable": os.access(storage_dir, os.W_OK)
        }
        
        if not (os.path.exists(task_dir) and os.access(task_dir, os.W_OK)):
            health["components"]["storage"]["status"] = "unavailable"
            health["status"] = "unhealthy"
    except Exception as e:
        health["components"]["storage"] = {
            "status": "error",
            "error": str(e)
        }
        health["status"] = "unhealthy"
    
    return health
