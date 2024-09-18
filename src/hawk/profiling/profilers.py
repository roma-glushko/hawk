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

import contextlib
from enum import Enum
from typing import Protocol, Generator, Type, Mapping

from hawk.profiling.renderers import RenderedProfile
from hawk.profiling.mem import tracemalloc
from hawk.profiling.cpu import pyinstrument


class ProfilerType(str, Enum):
    TRACEMALLOC = "tracemalloc"
    PYINSTRUMENT = "pyinstrument"


class ProfileHandler(Protocol):
    def __init__(self, query_params: Mapping[str, str]) -> None:
        ...

    @contextlib.contextmanager
    def profile(self) -> Generator[None, None, None]:
        ...

    def render_profile(self) -> RenderedProfile:
        ...


PROFILERS: dict[ProfilerType, Type[ProfileHandler]] = {
    ProfilerType.TRACEMALLOC: tracemalloc.ProfileHandler,
    ProfilerType.PYINSTRUMENT: pyinstrument.ProfileHandler,
}


def get_profiler(profiler: ProfilerType) -> Type[ProfileHandler]:
    try:
        return PROFILERS[profiler]
    except KeyError:
        raise ValueError(f"Profiler {profiler} is not supported (available: {', '.join(PROFILERS)})")
