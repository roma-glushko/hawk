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

import json

from hawk.profiling.renderers import RenderMode, RenderedProfile

try:
    from flask import Response
except ImportError as e:
    raise ImportError(
        "Flask is required to use the hawk.contrib.flask packages. "
        "Please install it using 'pip install flask'."
    ) from e


def format_response(profile: RenderedProfile) -> Response:
    headers = {
        "Content-Type": profile.mime_type.value,
    }

    if profile.render_mode == RenderMode.DOWNLOAD:
        headers["Content-Disposition"] = f"attachment; filename={profile.file_name}"

    content = profile.content
    if isinstance(content, dict):
        content = json.dumps(content)

    return Response(
        response=content,
        headers=headers,
    )
