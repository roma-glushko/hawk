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

from hawk.zpages.components.subheader import ZSubheader


class TestZSubheader:
    def test_default_level_is_2(self) -> None:
        subheader = ZSubheader(title="Test")

        assert subheader.level == 2
        assert subheader.to_html() == '<h2 id="subtitle_2">Test</h2>'

    def test_default_id_uses_level(self) -> None:
        subheader = ZSubheader(title="Test", level=3)

        assert subheader.id == "subtitle_3"

    def test_custom_id(self) -> None:
        subheader = ZSubheader(title="Test", id="custom-id")

        assert subheader.id == "custom-id"
        assert subheader.to_html() == '<h2 id="custom-id">Test</h2>'

    @pytest.mark.parametrize("level", [2, 3, 4, 5, 6])
    def test_valid_levels(self, level: int) -> None:
        subheader = ZSubheader(title="Test", level=level)

        assert subheader.level == level
        assert f"<h{level}" in subheader.to_html()
        assert f"</h{level}>" in subheader.to_html()

    @pytest.mark.parametrize("level", [0, 1, 7, 10, -1])
    def test_invalid_levels_raise_error(self, level: int) -> None:
        with pytest.raises(ValueError, match="Level must be between 2 and 6"):
            ZSubheader(title="Test", level=level)

    def test_to_html_format(self) -> None:
        subheader = ZSubheader(title="Section Title", level=3, id="section-1")

        assert subheader.to_html() == '<h3 id="section-1">Section Title</h3>'

    def test_to_json_format(self) -> None:
        subheader = ZSubheader(title="Section Title", level=3, id="section-1")

        assert subheader.to_json() == {"section-1": "Section Title"}

    def test_to_json_with_default_id(self) -> None:
        subheader = ZSubheader(title="Test", level=4)

        assert subheader.to_json() == {"subtitle_4": "Test"}
