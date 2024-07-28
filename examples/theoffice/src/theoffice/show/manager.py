import json
from pathlib import Path

from src.theoffice.show.exceptions import EpisodeNotFound, SeasonMedataCorrupted, SeasonNotFound
from src.theoffice.show.schemas import SeasonShort, Season, Episode


class ShowManager:
    def __init__(self):
        self._assets_path = Path(__file__).parent.parent / "assets"

    async def get_seasons(self) -> list[SeasonShort]:
        # find all directories under assets_path
        seasons = []

        for season_path in self._assets_path.iterdir():
            if not season_path.is_dir():
                continue

            season_id = int(season_path.name.lstrip("s"))

            seasons.append(SeasonShort(
                id=season_id,
                title=season_path.name,
            ))

        return seasons

    async def get_season(self, season_id: int) -> Season:
        season_path = self._assets_path / f"s{season_id}"

        if not season_path.is_dir():
            raise SeasonNotFound(f"Season #{season_id} not found")

        season_metadata_file = season_path / f"s{season_id}.json"

        if not season_path.is_file():
            raise SeasonMedataCorrupted("Season metadata corrupted")

        with open(season_metadata_file) as f:
            season_metadata = Season(**json.load(f))

        return season_metadata

    async def get_episode(self, season_id: int, episode_id: int) -> Episode:
        season_path = self._assets_path / f"s{season_id}"

        if not season_path.is_dir():
            raise SeasonNotFound(f"Season #{season_id} not found")

        episode_metadata_file = season_path / f"s{season_id}e{episode_id}.json"

        if not episode_metadata_file.is_file():
            raise EpisodeNotFound(f"Episode #{episode_id} not found in season #{season_id}")

        with open(episode_metadata_file) as f:
            episode_metadata = Episode(**json.load(f))

        return episode_metadata
