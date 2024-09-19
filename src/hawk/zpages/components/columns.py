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
from hawk.zpages.components.container import ZContainer
from hawk.zpages.templates import merge_json


class ZColumns(ZComponent):
    def __init__(self, columns: int = 2, id: str | None = None) -> None:
        if columns < 1:
            raise ValueError("Columns must be greater than 0")

        if columns > 5:
            raise ValueError("Columns must be less than or equal to 5")

        self.id = id
        self.columns: list[ZComponent] = [ZContainer() for _ in range(columns)]

    def __enter__(self) -> list[ZComponent]:
        return self.columns

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def to_html(self) -> str:
        return "".join([column.to_html() for column in self.columns])

    def to_json(self) -> dict[str, Any]:
        # TODO: finalize the JSON structure
        return merge_json([column.to_json() for column in self.columns])
