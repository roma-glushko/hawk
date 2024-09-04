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

from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from threading import Lock
from dataclasses import dataclass
from typing import Protocol, Generator

from src.hawk.profiling.exceptions import ProfilingNotStarted, ProfilingAlreadyStarted

PYINSTRUMENT_INSTALLED: bool = True

try:
    from pyinstrument import Profiler
    from pyinstrument import renderers as pyinstr_renderers
except ImportError:
    PYINSTRUMENT_INSTALLED = False


class ProfileFormat(str, Enum):
    HTML = "html"
    JSON = "json"
    SPEEDSCOPE = "speedscope"


class AsyncModes(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    STRICT = "strict"

@dataclass
class ProfileOptions:
    interval: float = 0.001
    use_timing_thread: bool | None = None
    async_mode: AsyncModes = AsyncModes.ENABLED


class PyInstrumentProfiler:
    def __init__(self) -> None:
        self._profiler_lock = Lock()
        self._curr_profiler: "Profiler" | None = None

    @property
    def is_profiling(self) -> bool:
        return bool(self._curr_profiler)

    @contextmanager
    def profile(self, config: ProfileOptions) -> Generator["Profiler"]:
        profiler = self.start(config)

        try:
            yield profiler
        finally:
            self.stop()

    def start(
        self,
        config: ProfileOptions,
    ) -> "Profiler":
        if self._curr_profiler:
            raise ProfilingAlreadyStarted("Profiler is already started")

        with self._profiler_lock:
            # https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
            profiler = Profiler(
                interval=config.interval,
                use_timing_thread=config.use_timing_thread,
                async_mode=config.async_mode,
            )
            profiler.start()
            self._curr_profiler = profiler

        return self._curr_profiler

    def stop(self) -> "Profiler":
        if not self._curr_profiler:
            raise ProfilingNotStarted("Profiler is not started yet")

        with self._profiler_lock:
            if not self._curr_profiler:
                raise ProfilingNotStarted("Profiler is not started yet")

            self._curr_profiler.stop()
            profiler, self._curr_profiler = self._curr_profiler, None

        return profiler


class Renderer(Protocol):
    file_ext: str

    def get_filename(self) -> str:
        ...

    def render(self, profiler: Profiler) -> str:
        ...


class JSONRenderer:
    file_ext: str = "json"

    def __init__(self):
        self._renderer = pyinstr_renderers.JSONRenderer()

    def get_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_cpu_pyinstr_profile_{timestamp}.{self.file_ext}"

    def render(self, profiler: Profiler) -> str:
        return profiler.output(renderer=self._renderer)


class HTMLRenderer:
    file_ext: str = "html"

    def __init__(self):
        self._renderer = pyinstr_renderers.HTMLRenderer()

    def get_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_cpu_pyinstr_profile_{timestamp}.{self.file_ext}"

    def render(self, profiler: Profiler) -> str:
        return profiler.output(renderer=self._renderer)


class SpeedscopeRenderer:
    file_ext: str = "speedscope.json"

    def __init__(self):
        self._renderer = pyinstr_renderers.SpeedscopeRenderer()

    def get_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_cpu_pyinstr_profile_{timestamp}.{self.file_ext}"

    def render(self, profiler: Profiler) -> str:
        return profiler.output(renderer=self._renderer)


PROFILE_RENDERERS: dict[ProfileFormat, Renderer] = {
    ProfileFormat.JSON: JSONRenderer(),
    ProfileFormat.HTML: HTMLRenderer(),
    ProfileFormat.SPEEDSCOPE: SpeedscopeRenderer(),
}


def get_renderer(format: ProfileFormat) -> Renderer:
    try:
        return PROFILE_RENDERERS[format]
    except KeyError:
        raise ValueError(f"Invalid profile format: {format} (formats: {', '.join(PROFILE_RENDERERS)})")


profiler = PyInstrumentProfiler()
