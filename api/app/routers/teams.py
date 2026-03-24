"""Team endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_teams():
    """List all teams."""
    return []


@router.get("/{team_id}")
async def get_team(team_id: int):
    """Get team profile with Elo history and recent form."""
    return {"id": team_id}
