from pydantic import BaseModel, Field


class SeasonShort(BaseModel):
    id: int = Field(examples=[1])
    title: str = Field(examples=["s1"])


class EpisodeShort(BaseModel):
    id: int = Field(examples=[1])
    title: str = Field(examples=["Diversity Day"])


class Season(BaseModel):
    id: int = Field(examples=[1])
    episodes: list[EpisodeShort]


class EpisodeSceneLine(BaseModel):
    id: int = Field(examples=[1])
    person: str = Field(examples=["Michael Scott"])
    line: str = Field(examples=["That's what she said"])


class EpisodeScene(BaseModel):
    id: int = Field(examples=[1])
    lines: list[EpisodeSceneLine]


class Episode(BaseModel):
    id: int = Field(examples=[1])
    season: int = Field(examples=[1])
    title: str = Field(examples=["Diversity Day"])

    scenes: list[EpisodeScene]
