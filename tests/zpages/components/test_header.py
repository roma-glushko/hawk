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

from hawk.zpages.components.header import ZHeader


class TestZHeader:
    def test_to_json_with_title_only(self) -> None:
        header = ZHeader(title="Test Title")

        assert header.to_json() == {"title": "Test Title", "description": None}

    def test_to_json_with_title_and_description(self) -> None:
        header = ZHeader(title="Test Title", description="Test Description")

        assert header.to_json() == {
            "title": "Test Title",
            "description": "Test Description",
        }

    def test_to_html_renders_without_error(self) -> None:
        header = ZHeader(title="Test Title", description="Test Description")

        html = header.to_html()

        assert isinstance(html, str)
        assert len(html) > 0

    def test_to_html_contains_title(self) -> None:
        header = ZHeader(title="My Page Title")

        html = header.to_html()

        assert "My Page Title" in html

    @pytest.mark.parametrize(
        "title, description",
        [
            ("Simple", None),
            ("With Description", "A description"),
            ("Special <chars>", "With & symbols"),
        ],
    )
    def test_to_html_renders_various_inputs(
        self, title: str, description: str | None
    ) -> None:
        header = ZHeader(title=title, description=description)

        html = header.to_html()

        assert isinstance(html, str)
