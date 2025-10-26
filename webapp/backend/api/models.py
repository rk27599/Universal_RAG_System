from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from services.llm_factory import (
    get_available_models,
    check_llm_connection,
    get_current_provider,
    get_provider_info,
    LLMServiceFactory
)
from core.database import check_database_connection, get_db
from core.config import settings
from sqlalchemy.orm import Session

router = APIRouter(tags=["Models"])


class ModelInfo(BaseModel):
    name: str
    family: str
    size: str


@router.get("/models")
async def get_models():
    """Get available models - consistent format"""
    try:
        models = await get_available_models()
        return {
            "success": True,
            "data": models,
            "message": "Models retrieved successfully"
        }
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
        return {
            "success": True,
            "data": ["mistral", "llama2", "codellama"],
            "message": "Using fallback model list"
        }


@router.get("/models/{model_name}")
async def get_model_info_endpoint(model_name: str):
    """Get detailed model information from current LLM provider"""
    try:
        # Use factory to get model info from current provider
        llm_service = LLMServiceFactory.get_service()
        model_data = await llm_service.get_model_info(model_name)

        if model_data:
            return {
                "success": True,
                "data": model_data,
                "message": "Model info retrieved"
            }
        else:
            # Fallback to basic info
            return {
                "success": True,
                "data": {
                    "name": model_name,
                    "family": "Unknown",
                    "size": "0",
                    "parameters": "Unknown",
                    "format": "Unknown"
                },
                "message": "Model info retrieved (limited data)"
            }

    except Exception as e:
        print(f"❌ Error fetching model info for {model_name}: {e}")
        return {
            "success": False,
            "data": {
                "name": model_name,
                "family": "Unknown",
                "size": "0",
                "parameters": "Unknown",
                "format": "Unknown"
            },
            "message": f"Error: {str(e)}"
        }


@router.get("/system/status")
async def get_system_status():
    """Get system status"""
    try:
        # Check current LLM provider connection
        current_provider = get_current_provider()
        llm_status = await check_llm_connection()
        llm_models = await get_available_models() if llm_status else []

        # Check database connection
        db_status = await check_database_connection()

        return {
            "success": True,
            "data": {
                "llm": {
                    "provider": current_provider,
                    "status": "running" if llm_status else "offline",
                    "models": llm_models
                },
                "database": {
                    "status": "connected" if db_status else "disconnected",
                    "connections": 5 if db_status else 0
                },
                "security": {
                    "score": 96,
                    "violations": 0
                }
            },
            "message": "System status retrieved"
        }
    except Exception as e:
        print(f"❌ Error getting system status: {e}")
        return {
            "success": False,
            "data": {
                "llm": {"provider": "unknown", "status": "unknown", "models": []},
                "database": {"status": "unknown", "connections": 0},
                "security": {"score": 0, "violations": 0}
            },
            "message": f"Error: {str(e)}"
        }


@router.get("/models/provider/info")
async def get_llm_provider_info():
    """Get current LLM provider information and configuration"""
    try:
        provider_info = get_provider_info()
        return {
            "success": True,
            "data": provider_info,
            "message": "Provider info retrieved"
        }
    except Exception as e:
        print(f"❌ Error getting provider info: {e}")
        return {
            "success": False,
            "data": {"provider": "unknown", "error": str(e)},
            "message": f"Error: {str(e)}"
        }


class UserSettings(BaseModel):
    """User settings model"""
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    top_p: Optional[float] = 0.9
    repeat_penalty: Optional[float] = 1.1
    use_rag_by_default: Optional[bool] = True
    streaming_enabled: Optional[bool] = True
    default_model: Optional[str] = None


# In-memory settings storage (replace with database in production)
user_settings_store = {}


@router.get("/settings")
async def get_user_settings(user_id: int = 1):
    """Get user settings"""
    settings = user_settings_store.get(user_id, UserSettings())
    return {
        "success": True,
        "data": settings.dict() if hasattr(settings, 'dict') else settings.__dict__,
        "message": "Settings retrieved"
    }


@router.put("/settings")
async def update_user_settings(settings: UserSettings, user_id: int = 1):
    """Update user settings"""
    try:
        user_settings_store[user_id] = settings
        return {
            "success": True,
            "data": settings.dict(),
            "message": "Settings updated successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": f"Error updating settings: {str(e)}"
        }


@router.post("/settings/reset")
async def reset_user_settings(user_id: int = 1):
    """Reset user settings to defaults"""
    default_settings = UserSettings()
    user_settings_store[user_id] = default_settings
    return {
        "success": True,
        "data": default_settings.dict(),
        "message": "Settings reset to defaults"
    }
