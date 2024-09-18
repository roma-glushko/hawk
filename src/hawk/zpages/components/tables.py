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
from hawk.zpages.templates import TEMPLATES


class TableStyle(str, Enum):
    STRIPPED = "stripped"
    PROPERTY = "property-table"


class ZTable(ZComponent):
    def __init__(self, cols: list[str], rows: list[list[Any]], id: str | None = None, style: TableStyle | None = None) -> None:
        self.cols = cols
        self.rows = rows

        self.id = id or "data"
        self.style = style

    def to_html(self) -> str:
        return TEMPLATES.render(
            "table.html.j2",
            cols=self.cols,
            rows=self.rows,
            style=self.style.value if self.style else None,
        )

    def to_json(self) -> dict[str, Any]:
        """
        """
        col_keys = [slugify(col) for col in self.cols]

        table_items = [
            dict(zip(col_keys, row))
            for row in self.rows
        ]

        return {self.id: table_items}

