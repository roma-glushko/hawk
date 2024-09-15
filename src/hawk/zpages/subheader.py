from __future__ import annotations

from typing import Any

from src.hawk.zpages.components.base import ZComponent


class ZSubheader(ZComponent):
    def __init__(self, title: str, level: int = 2, id: str | None = None) -> None:
        if not 2 <= level <= 6:
            raise ValueError("Level must be between 2 and 6")

        self.title = title
        self.level = level
        self.id = id or f"subtitle_{level}"

    def to_html(self) -> str:
        return f'<h{self.level} id="{self.id}">{self.title}</h{self.level}>'

    def to_json(self) -> dict[str, Any]:
        return {
            self.id: self.title
        }
