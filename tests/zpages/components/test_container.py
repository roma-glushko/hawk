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
from typing import Any

import pytest

from hawk.zpages.components.container import ZContainer

@pytest.mark.parametrize(
    "params, expected_html, expected_json",
    [
        (
            {},
            '<div id="" class="container"></div>',
            {},
        ),
        (
            {"id": "container-id"},
            '<div id="container-id" class="container"></div>',
            {"container-id": {}},
        ),
    ],
)
def test__zpages_container__params(params: dict[str, Any], expected_html: str, expected_json: dict[str, Any]) -> None:
    container = ZContainer(**params)

    assert container.to_html() == expected_html
    assert container.to_json() == expected_json


def test__zpages_container__ctx_manager() -> None:
    c = ZContainer()

    with c:
        c.add(ZContainer())
        c |= ZContainer()

    assert c.to_html() == '<div id="" class="container"><div id="" class="container"></div><div id="" class="container"></div></div>'
    assert c.to_json() == {}
