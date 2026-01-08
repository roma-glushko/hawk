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

from threading import Lock
from typing import Any, Callable

_LOCK = Lock()
EXP_VARS: dict[str, Any] = {}
"""
The exposed variables registry.
"""

def expose_var(name: str, var: Any) -> None:
    """
    Expose a new debug variable.

    Parameters
    ----------
    name : str
        The name of the expvar.
    value : Any
        The value of the expvar.
    """
    with _LOCK:
        EXP_VARS[name] = var

def get_vars() -> dict[str, Any]:
    """
    Get all exposed debug variables.
    """
    with _LOCK:
        return EXP_VARS

class Str(str):
    """
    A string that can be exposed as an expvar.
    """
    def __init__(self, name: str, value: str | None = None) -> None:
        self.value = value
        expose_var(name, self)

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __str__(self) -> str:
        return self.value if self.value is not None else ""

class Int(int):
    """
    An integer that can be exposed as an expvar.
    """
    def __init__(self, name: str, value: int | None = None) -> None:
        self.value = value
        expose_var(name, self)

    def __int__(self) -> int:
        return self.value if self.value is not None else 0

class Float(float):
    """
    A float that can be exposed as an expvar.
    """
    def __init__(self, name: str, value: float | None = None) -> None:
        self.value = value
        expose_var(name, self)

    def __float__(self) -> float:
        return self.value if self.value is not None else 0.0


class Bool:
    """
    A boolean that is exposed as an expvar.
    """
    def __init__(self, name: str, value: bool | None = None) -> None:
        self.value = value
        expose_var(name, self)

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __str__(self) -> str:
        return str(self.value)

    def __bool__(self) -> bool:
        return self.value if self.value is not None else False

class Func:
    """
    A function that is exposed as an expvar.
    """
    def __init__(self, name: str, func: Callable[..., Any]) -> None:
        self.func = func
        expose_var(name, self)

    def __call__(self) -> Any:
        return self.func()