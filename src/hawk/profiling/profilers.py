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
from typing import Protocol

from src.hawk.profiling.renderers import RenderedProfile


class Profiler(str, Enum):
    TRACEMALLOC = "tracemalloc"
    PYINSTRUMENT = "pyinstrument"


class ProfileHandler(Protocol):
    @contextlib.contextmanager
    def profile(self) -> RenderedProfile:
        ...


PROFILERS: dict[str, ProfileHandler] = {
    Profiler.TRACEMALLOC: None,
    Profiler.PYINSTRUMENT: None,
}


def get_profiler(profiler: str) -> ProfileHandler:
    try:
        return PROFILERS.get(profiler)
    except KeyError:
        raise ValueError(f"Profiler {profiler} is not supported (available: {', '.join(PROFILERS)})")
