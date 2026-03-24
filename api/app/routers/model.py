"""Model performance endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/accuracy")
async def get_model_accuracy():
    """Return rolling accuracy metrics."""
    return {}


@router.get("/features")
async def get_feature_importance():
    """Return feature importance rankings."""
    return {}
