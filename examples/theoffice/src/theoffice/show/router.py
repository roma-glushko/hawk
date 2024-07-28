from fastapi import APIRouter, Request

from src.theoffice.show.manager import ShowManager
from src.theoffice.show.schemas import SeasonShort, Season

router = APIRouter()


@router.get("/show/seasons/", tags=["show"])
async def get_seasons(request: Request) -> list[SeasonShort]:
    """
    Get the list of all The Office seasons
    """
    show_manager: ShowManager = request.app.state.show_manager

    return await show_manager.get_seasons()


@router.get("/show/seasons/{season_id}/", tags=["show"])
async def get_season(request: Request, season_id: int) -> Season:
    show_manager: ShowManager = request.app.state.show_manager

    return await show_manager.get_season(season_id)


@router.get("/show/seasons/{season_id}/episodes/{episode_id}/", tags=["show"])
async def get_episode(request: Request, season_id: int, episode_id: int):
    show_manager: ShowManager = request.app.state.show_manager

    return await show_manager.get_episode(season_id, episode_id)
