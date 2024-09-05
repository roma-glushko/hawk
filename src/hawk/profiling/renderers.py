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

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RenderMode(str, Enum):
    VIEW = "view"
    DOWNLOAD = "download"


class MimeType(str, Enum):
    JSON = "application/json"
    HTML = "text/html"
    BINARY = "application/octet-stream"


@dataclass
class RenderedProfile:
    file_name: str
    mime_type: MimeType
    render_mode: RenderMode
    content: bytes | str | dict[str, Any]
