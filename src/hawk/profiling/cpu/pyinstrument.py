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
from typing import Generator, Protocol, Mapping

from hawk.profiling.exceptions import ProfilingNotStarted, ProfilingAlreadyStarted
from hawk.profiling.renderers import RenderMode, MimeType, RenderedProfile

try:
    import pyinstrument
except ModuleNotFoundError:
    pyinstrument = None # type: ignore[assignment]


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

    @classmethod
    def from_query_params(cls, query_params: Mapping[str, str]) -> ProfileOptions:
        interval = float(query_params.get("interval", 0.001))
        async_mode = AsyncModes(query_params.get("async_mode", AsyncModes.ENABLED))

        use_timing_thread: bool | None = None

        if use_thead := query_params.get("use_timing_thread", None):
            use_timing_thread = use_thead.lower() in {"true", "1", "yes"}

        return ProfileOptions(
            interval=interval,
            use_timing_thread=use_timing_thread,
            async_mode=async_mode,
        )


class PyInstrumentProfiler:
    def __init__(self) -> None:
        self._profiler_lock = Lock()
        self._curr_profiler: "pyinstrument.Profiler" | None = None

    @property
    def is_profiling(self) -> bool:
        return bool(self._curr_profiler)

    @contextmanager
    def profile(self, opt: ProfileOptions) -> Generator["pyinstrument.Profiler"]:
        profiler = self.start(opt)

        try:
            yield profiler
        finally:
            self.stop()

    def start(
        self,
        opt: ProfileOptions,
    ) -> "pyinstrument.Profiler":
        if self._curr_profiler:
            raise ProfilingAlreadyStarted("Profiler is already started")

        with self._profiler_lock:
            # https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
            profiler = pyinstrument.Profiler(
                interval=opt.interval,
                use_timing_thread=opt.use_timing_thread,
                async_mode=opt.async_mode,
            )
            profiler.start()
            self._curr_profiler = profiler

        return self._curr_profiler

    def stop(self) -> "pyinstrument.Profiler":
        if not self._curr_profiler:
            raise ProfilingNotStarted("Profiler is not started yet")

        with self._profiler_lock:
            if not self._curr_profiler:
                raise ProfilingNotStarted("Profiler is not started yet")

            self._curr_profiler.stop()
            profiler, self._curr_profiler = self._curr_profiler, None

        return profiler


class Renderer(Protocol):
    def render(self, profiler: "pyinstrument.Profiler") -> RenderedProfile:
        ...


class JSONRenderer:
    mime_type: MimeType = MimeType.JSON
    file_ext: str = "json"
    render_mode: RenderMode = RenderMode.DOWNLOAD

    def __init__(self):
        if pyinstrument is None:
            raise ImportError("pyinstrument is not installed")

        self._renderer = pyinstrument.renderers.JSONRenderer()

    def get_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_cpu_pyinstr_profile_{timestamp}.{self.file_ext}"

    def render(self, profiler: "pyinstrument.Profiler") -> RenderedProfile:
        content = profiler.output(renderer=self._renderer)

        return RenderedProfile(
            file_name=self.get_filename(),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=content,
        )


class HTMLRenderer:
    mime_type: MimeType = MimeType.HTML
    file_ext: str = "html"
    render_mode: RenderMode = RenderMode.VIEW

    def __init__(self):
        if pyinstrument is None:
            raise ImportError("pyinstrument is not installed")

        self._renderer = pyinstrument.renderers.HTMLRenderer()

    def get_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_cpu_pyinstr_profile_{timestamp}.{self.file_ext}"

    def render(self, profiler: "pyinstrument.Profiler") -> RenderedProfile:
        content = profiler.output(renderer=self._renderer)

        return RenderedProfile(
            file_name=self.get_filename(),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=content,
        )


class SpeedscopeRenderer:
    mime_type: MimeType = MimeType.JSON
    file_ext: str = "speedscope.json"
    render_mode: RenderMode = RenderMode.DOWNLOAD

    def __init__(self):
        if pyinstrument is None:
            raise ImportError("pyinstrument is not installed")

        self._renderer = pyinstrument.renderers.SpeedscopeRenderer()

    def get_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_cpu_pyinstr_profile_{timestamp}.{self.file_ext}"

    def render(self, profiler: "pyinstrument.Profiler") -> RenderedProfile:
        content = profiler.output(renderer=self._renderer)

        return RenderedProfile(
            file_name=self.get_filename(),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=content,
        )


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


class ProfileHandler:
    def __init__(self, query_params: Mapping[str, str]) -> None:
        if pyinstrument is None:
            raise ImportError("pyinstrument is not installed")

        self._opt = ProfileOptions.from_query_params(query_params)
        self._format = ProfileFormat(query_params.get("format", ProfileFormat.HTML))

        self._profiler: "pyinstrument.Profiler" | None = None

    @contextmanager
    def profile(self) -> Generator[None, None, None]:
        with profiler.profile(self._opt) as p:
            self._profiler = p
            yield

    def render_profile(self) -> RenderedProfile:
        if not self._profiler:
            raise ProfilingNotStarted("Profiler is not started yet")

        renderer = get_renderer(self._format)

        return renderer.render(self._profiler)
