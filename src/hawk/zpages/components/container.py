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
from hawk.zpages.templates import merge_json


class ZContainer(ZComponent):
    def __init__(self, id: str | None = None, tag: str = "div") -> None:
        self.id = id
        self.tag = tag
        self.children: list[ZComponent] = []

    def add(self, component: ZComponent) -> None:
        self.children.append(component)

    def container(self, *args, **kwargs) -> ZContainer:
        container = ZContainer(*args, **kwargs)
        self.add(container)

        return container

    def __or__(self, other) -> "ZContainer":
        self.add(other)
        return self

    def __enter__(self) -> "ZContainer":
        return self

    # TODO: add typing
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def to_html(self) -> str:
        content = "".join([child.to_html() for child in self.children])

        return f'<{self.tag} id="{self.id or ""}" class="container">{content}</{self.tag}>'

    def to_json(self) -> dict[str, Any]:
        json = merge_json([child.to_json() for child in self.children])

        if self.id:
            return {
                self.id: json
            }

        return json

class ZMainContainer(ZContainer):
    def __init__(self, id: str | None = None) -> None:
        super().__init__(id=id, tag="main")

class ZSection(ZContainer):
    def __init__(self, id: str | None = None) -> None:
        super().__init__(id=id, tag="section")
