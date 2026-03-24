"""Prediction endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/upcoming")
async def get_upcoming_predictions():
    """Return predictions for upcoming matches."""
    return []


@router.get("/history")
async def get_prediction_history():
    """Return past predictions with accuracy."""
    return []
