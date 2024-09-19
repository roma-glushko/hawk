# Copyright (c) 2024 Roman Hlushko and various contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from enum import Enum
from typing import Any

from hawk.zpages.components.base import ZComponent, slugify
from hawk.zpages.components.container import ZContainer, ZMainContainer
from hawk.zpages.components.header import ZHeader
from hawk.zpages.templates import TEMPLATES, merge_json
from hawk.zpages.theme import ThemeColor, THEME_COLOR

class ZPageFormat(str, Enum):
    HTML = "html"
    JSON = "json"

class ZPage:
    """
    A high-level page container that holds all other page components.
    The components are rendered in the order they were added.

    ZPage can render its content hierarchy to HTML and JSON.

    **Example**

    ```python

    ```
    """
    def __init__(
        self,
        title: str,
        description: str | None = None,
        id: str | None = None,
        theme_color: ThemeColor | None = None,
    ) -> None:
        self.id = id or slugify(title)
        self.title = f"{title} • Hawk"
        self.description = description
        self.theme_color = theme_color or THEME_COLOR

        self.auto_refresh: int | None = None # seconds

        self.header = ZHeader(title, description)
        self.main_container = ZMainContainer()

    def add(self, component: ZComponent) -> None:
        """
        Add a new component to the page.
        """
        self.main_container.add(component)

    def container(self) -> ZContainer:
        """
        Add a new container to the page and return it.
        """
        return self.main_container.container()

    def render(self, format: ZPageFormat) -> Any:
        """
        Render the page in the specified format.

        Returns:
            The rendered page content or JSON dict.

        Raises:
            ValueError: When the format is not supported.
        """
        if format == ZPageFormat.HTML:
            return self.to_html()

        if format == ZPageFormat.JSON:
            return self.to_json()

        raise ValueError(f"Unsupported format: {format}")

    def to_html(self) -> str:
        """
        Render the page as HTML. This is a human-friendly representation of the page.
        """
        html_parts: list[str] = [
            self.header.to_html(),
            self.main_container.to_html(),
        ]

        return TEMPLATES.render(
            "page.html.j2",
            id=self.id,
            title=self.title,
            description=self.description,
            theme_color=self.theme_color.value,
            auto_refresh=self.auto_refresh,
            content="".join(html_parts),
        )

    def to_json(self) -> dict[str, Any]:
        """
        Render the page as JSON. This is useful for automations and any other machine-readable processing.
        """
        json_parts: list[dict[str, Any]] = [
            {
                "id": self.id,
            },
            self.header.to_json(),
            self.main_container.to_json(),
        ]

        return merge_json(json_parts)
