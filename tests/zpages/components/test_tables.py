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

from hawk.zpages.components.tables import TableStyle, ZTable


class TestTableStyle:
    def test_stripped_value(self) -> None:
        assert TableStyle.STRIPPED.value == "stripped"

    def test_property_value(self) -> None:
        assert TableStyle.PROPERTY.value == "property-table"


class TestZTable:
    def test_default_id(self) -> None:
        table = ZTable(cols=["A"], rows=[])

        assert table.id == "data"

    def test_custom_id(self) -> None:
        table = ZTable(cols=["A"], rows=[], id="custom-table")

        assert table.id == "custom-table"

    def test_to_json_empty_table(self) -> None:
        table = ZTable(cols=["Name", "Value"], rows=[])

        assert table.to_json() == {"data": []}

    def test_to_json_with_rows(self) -> None:
        table = ZTable(
            cols=["Name", "Value"],
            rows=[
                ["foo", 1],
                ["bar", 2],
            ],
        )

        assert table.to_json() == {
            "data": [
                {"name": "foo", "value": 1},
                {"name": "bar", "value": 2},
            ]
        }

    def test_to_json_slugifies_column_names(self) -> None:
        table = ZTable(
            cols=["Column Name", "Another Column"],
            rows=[["val1", "val2"]],
        )

        result = table.to_json()

        assert "data" in result
        assert result["data"][0] == {"column-name": "val1", "another-column": "val2"}

    def test_to_json_with_custom_id(self) -> None:
        table = ZTable(
            cols=["A", "B"],
            rows=[["x", "y"]],
            id="my-table",
        )

        result = table.to_json()

        assert "my-table" in result
        assert result["my-table"] == [{"a": "x", "b": "y"}]

    def test_to_json_with_various_types(self) -> None:
        table = ZTable(
            cols=["String", "Int", "Float", "Bool"],
            rows=[["text", 42, 3.14, True]],
        )

        result = table.to_json()

        assert result["data"][0] == {
            "string": "text",
            "int": 42,
            "float": 3.14,
            "bool": True,
        }

    def test_to_html_renders_without_error(self) -> None:
        table = ZTable(
            cols=["Name", "Value"],
            rows=[["foo", "bar"]],
        )

        html = table.to_html()

        assert isinstance(html, str)
        assert len(html) > 0

    def test_to_html_contains_column_headers(self) -> None:
        table = ZTable(
            cols=["Column A", "Column B"],
            rows=[],
        )

        html = table.to_html()

        assert "Column A" in html
        assert "Column B" in html

    def test_to_html_contains_row_data(self) -> None:
        table = ZTable(
            cols=["Name"],
            rows=[["Test Value"]],
        )

        html = table.to_html()

        assert "Test Value" in html

    @pytest.mark.parametrize(
        "style",
        [TableStyle.STRIPPED, TableStyle.PROPERTY, None],
    )
    def test_to_html_with_styles(self, style: TableStyle | None) -> None:
        table = ZTable(
            cols=["A"],
            rows=[["B"]],
            style=style,
        )

        html = table.to_html()

        assert isinstance(html, str)
