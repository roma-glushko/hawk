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

from io import BytesIO

from src.hawk.profiling.renderers import RenderMode, MimeType, Renderer

try:
    from fastapi import Response
    from fastapi.responses import StreamingResponse, HTMLResponse
except ImportError as e:
    raise ImportError(
        "FastAPI is required to use the hawk.contrib.fastapi packages. "
        "Please install it using 'pip install fastapi'."
    ) from e


def format_response(renderer: Renderer, profile_content: bytes | str | BytesIO) -> Response:
    headers = {
        "Content-Type": renderer.mime_type,
    }

    if renderer.render_mode == RenderMode.DOWNLOAD:
        file_name = renderer.get_file_name()
        headers["Content-Disposition"] = f"attachment; filename={file_name}"

    if renderer.mime_type == MimeType.HTML:
        return HTMLResponse(content=profile_content, headers=headers)

    return StreamingResponse(content=profile_content, headers=headers)
