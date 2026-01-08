# Copyright (c) 2025 Roman Hlushko and various contributors
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

from typing import Any

from hawk import zpages
from hawk.expvars.vars import get_vars, Func
from hawk.zpages.components import ZTable, TableStyle
from hawk.zpages.components.base import ZComponent


def _get_var_value(var: Any) -> Any:
    """
    Get the value of a variable, calling it if it's a Func.
    """
    if isinstance(var, Func):
        return var()

    if hasattr(var, "value"):
        return var.value

    return var


def _get_var_type(var: Any) -> str:
    """
    Get a human-readable type name for a variable.
    """
    if isinstance(var, Func):
        return "func"

    return type(var).__name__.lower()


class ZExpVarsTable(ZComponent):
    """
    A dynamic table component that renders the current state of exposed variables.
    Values are fetched at render time to ensure up-to-date information.
    """

    def _get_rows(self) -> list[list[Any]]:
        """
        Get the current rows for the table.
        """
        vars_dict = get_vars()
        return [
            [name, _get_var_type(var), _get_var_value(var)]
            for name, var in sorted(vars_dict.items())
        ]

    def to_html(self) -> str:
        table = ZTable(
            id="expvars",
            cols=["Name", "Type", "Value"],
            rows=self._get_rows(),
            style=TableStyle.STRIPPED,
        )
        return table.to_html()

    def to_json(self) -> dict[str, Any]:
        table = ZTable(
            id="expvars",
            cols=["Name", "Type", "Value"],
            rows=self._get_rows(),
            style=TableStyle.STRIPPED,
        )
        return table.to_json()


def create_expvars_zpage() -> zpages.ZPage:
    """
    Create a ZPage that displays all exposed variables.
    """
    zp = zpages.ZPage(
        title="Exposed Variables",
        description="Internal application state exposed via expvars",
    )

    with zp.container() as c:
        c.add(ZExpVarsTable())

    return zp


def register_expvars_zpage(route: str = "vars") -> None:
    """
    Register the expvars ZPage at the specified route.

    Parameters
    ----------
    route : str
        The route to register the ZPage at (default: "vars").
        The page will be accessible at /debug/{route}/.
    """
    zpages.add_page(route, create_expvars_zpage())
