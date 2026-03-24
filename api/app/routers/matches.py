"""Match endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_matches():
    """List recent match results."""
    return []


@router.get("/{match_id}")
async def get_match(match_id: int):
    """Get match detail with map scores and stats."""
    return {"id": match_id}
