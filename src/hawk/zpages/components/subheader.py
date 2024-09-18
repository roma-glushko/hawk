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
