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
import pytest

from hawk.zpages.components.base import ZNoOpComponent, slugify


class TestSlugify:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Hello World", "hello-world"),
            ("hello", "hello"),
            ("UPPERCASE", "uppercase"),
            ("Multiple   Spaces", "multiple---spaces"),
            ("Already-Slugified", "already-slugified"),
            ("", ""),
        ],
    )
    def test_slugify(self, text: str, expected: str) -> None:
        assert slugify(text) == expected


class TestZNoOpComponent:
    def test_to_html_returns_empty_string(self) -> None:
        component = ZNoOpComponent()
        assert component.to_html() == ""

    def test_to_json_returns_empty_dict(self) -> None:
        component = ZNoOpComponent()
        assert component.to_json() == {}
