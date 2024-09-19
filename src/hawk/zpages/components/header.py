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

from typing import Any

from hawk.zpages.components.base import ZComponent
from hawk.zpages.templates import TEMPLATES


class ZHeader(ZComponent):
    def __init__(self, title: str, description: str | None = None) -> None:
        self._title = title
        self._description = description

    def to_html(self) -> str:
        return TEMPLATES.render(
            "header.html.j2",
            title=self._title,
            description=self._description,
        )

    def to_json(self) -> dict[str, Any]:
        return {"title": self._title, "description": self._description}
