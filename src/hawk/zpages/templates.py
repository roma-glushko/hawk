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
import functools
from pathlib import Path
from typing import Any, Sequence

try:
    import jinja2
except ModuleNotFoundError:  # pragma: nocover
    jinja2 = None  # type: ignore[assignment]


TEMPLATES_PATH = (Path(__file__).parent / "templates").resolve()

def merge_json(json_parts: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """
    Merges dictionaries.
    """
    if not json_parts:
        return {}

    return functools.reduce(lambda x, y: {**(x or {}), **(y or {})}, json_parts)


class Jinja2Templates:
    """
    Renders ZComponent HTML templates using Jinja2.
    """
    def __init__(self, loader: jinja2.BaseLoader) -> None:
        if jinja2 is None:
            raise ImportError("Jinja2 must be installed to use ZPages")

        self._env = jinja2.Environment(loader=loader)

    def render(self, template_name: str, **context: Any) -> str:
        template = self._env.get_template(template_name)

        return template.render(**context)


TEMPLATES = Jinja2Templates(jinja2.FileSystemLoader(TEMPLATES_PATH))

def set_templates(templates: Jinja2Templates) -> None:
    """
    Override the default Jinja2 Templates Renderer
    """
    global TEMPLATES

    TEMPLATES = templates