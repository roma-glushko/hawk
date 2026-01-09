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

from hawk.zpages.components.columns import ZColumns
from hawk.zpages.components.container import ZContainer


class TestZColumns:
    def test_default_columns_is_2(self) -> None:
        columns = ZColumns()

        assert len(columns.columns) == 2

    @pytest.mark.parametrize("num_columns", [1, 2, 3, 4, 5])
    def test_valid_column_counts(self, num_columns: int) -> None:
        columns = ZColumns(columns=num_columns)

        assert len(columns.columns) == num_columns

    def test_columns_less_than_1_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Columns must be greater than 0"):
            ZColumns(columns=0)

    def test_columns_greater_than_5_raises_error(self) -> None:
        with pytest.raises(ValueError, match="Columns must be less than or equal to 5"):
            ZColumns(columns=6)

    def test_columns_are_zcontainer_instances(self) -> None:
        columns = ZColumns(columns=3)

        for col in columns.columns:
            assert isinstance(col, ZContainer)

    def test_context_manager_returns_columns_list(self) -> None:
        zcolumns = ZColumns(columns=2)

        with zcolumns as cols:
            assert cols is zcolumns.columns
            assert len(cols) == 2

    def test_context_manager_allows_adding_to_columns(self) -> None:
        zcolumns = ZColumns(columns=2)

        with zcolumns as [col1, col2]:
            col1.add(ZContainer(id="left-content"))
            col2.add(ZContainer(id="right-content"))

        assert len(zcolumns.columns[0].children) == 1
        assert len(zcolumns.columns[1].children) == 1

    def test_to_html_renders_all_columns(self) -> None:
        zcolumns = ZColumns(columns=2)

        html = zcolumns.to_html()

        assert isinstance(html, str)
        # Should contain two container divs
        assert html.count('<div id=""') == 2

    def test_to_html_with_content(self) -> None:
        zcolumns = ZColumns(columns=2)

        with zcolumns as [col1, col2]:
            col1.add(ZContainer(id="col1-content"))
            col2.add(ZContainer(id="col2-content"))

        html = zcolumns.to_html()

        assert "col1-content" in html
        assert "col2-content" in html

    def test_to_json_without_id(self) -> None:
        zcolumns = ZColumns(columns=2)

        result = zcolumns.to_json()

        assert "column_0" in result
        assert "column_1" in result
        assert result["column_0"] == {}
        assert result["column_1"] == {}

    def test_to_json_with_id(self) -> None:
        zcolumns = ZColumns(columns=2, id="my-columns")

        result = zcolumns.to_json()

        assert "my-columns" in result
        assert "column_0" in result["my-columns"]
        assert "column_1" in result["my-columns"]

    def test_to_json_with_content(self) -> None:
        zcolumns = ZColumns(columns=2)

        with zcolumns as [col1, col2]:
            col1.add(ZContainer(id="left"))
            col2.add(ZContainer(id="right"))

        result = zcolumns.to_json()

        assert result["column_0"] == {"left": {}}
        assert result["column_1"] == {"right": {}}

    def test_to_json_column_indices_are_sequential(self) -> None:
        zcolumns = ZColumns(columns=5)

        result = zcolumns.to_json()

        for i in range(5):
            assert f"column_{i}" in result
