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

from enum import StrEnum
from threading import Lock
from typing import Type

PYINSTRUMENT_INSTALLED: bool = True

try:
    from pyinstrument import Profiler
    from pyinstrument.renderers import JSONRenderer, HTMLRenderer, SpeedscopeRenderer
except ImportError:
    PYINSTRUMENT_INSTALLED = False


class ProfileFormat(StrEnum):
    HTML = "html"
    JSON = "json"
    SPEEDSCOPE = "speedscope"


class AsyncModes(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    STRICT = "strict"


class PyInstrumentProfiler:
    def __init__(self) -> None:
        self._profiler_lock = Lock()
        self._curr_profiler: "Profiler" | None = None

    def start(self, interval: float = 0.001, use_timing_thread: bool | None = None, async_mode: AsyncModes = AsyncModes.ENABLED) -> "Profiler":
        if self._curr_profiler:
            # TODO: raise error
            ...

        with self._profiler_lock:
            # https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
            profiler = Profiler(interval=interval, use_timing_thread=use_timing_thread, async_mode=async_mode)
            profiler.start()
            self._curr_profiler = profiler

        return self._curr_profiler

    def is_profiling(self) -> bool:
        return bool(self._curr_profiler)

    def stop(self) -> "Profiler":
        if not self._curr_profiler:
            # TODO: raise error
            ...

        with self._profiler_lock:
            if not self._curr_profiler:
                # TODO: throw error
                ...

            self._curr_profiler.stop()
            profiler, self._curr_profiler = self._curr_profiler, None

        return profiler


PROFILE_RENDERERS = {
    ProfileFormat.JSON: JSONRenderer,
    ProfileFormat.HTML: HTMLRenderer,
    ProfileFormat.SPEEDSCOPE: SpeedscopeRenderer,
}


def get_renderer(format: ProfileFormat) -> Type[JSONRenderer | HTMLRenderer | SpeedscopeRenderer]:
    return PROFILE_RENDERERS[format]


profiler = PyInstrumentProfiler()
