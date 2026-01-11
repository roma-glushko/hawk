# Copyright (c) 2026 Roman Hlushko and various contributors
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

import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from threading import Lock
from dataclasses import dataclass
from typing import Generator, Protocol, Mapping, Any

from hawk.profiling.exceptions import ProfilingNotStarted, ProfilingAlreadyStarted
from hawk.profiling.renderers import RenderMode, MimeType, RenderedProfile
from hawk.profiling.trace_context import TraceContext, profiling_span

try:
    import yappi  # type: ignore[import-untyped]
    from yappi import YFuncStats, YThreadStats  # type: ignore[import-untyped]
except ModuleNotFoundError:
    yappi = None  # type: ignore[assignment]
    YFuncStats = None  # type: ignore[assignment, misc]
    YThreadStats = None  # type: ignore[assignment, misc]


class ProfileFormat(str, Enum):
    PSTAT = "pstat"
    CALLGRIND = "callgrind"
    FUNC_STATS = "funcstats"


class ClockType(str, Enum):
    CPU = "cpu"
    WALL = "wall"


@dataclass
class ProfileOptions:
    clock_type: ClockType = ClockType.CPU
    builtins: bool = False
    multithreaded: bool = True

    @classmethod
    def from_query_params(cls, query_params: Mapping[str, str]) -> ProfileOptions:
        clock_type = ClockType(query_params.get("clock_type", ClockType.CPU.value))

        builtins = query_params.get("builtins", "false").lower() in {"true", "1", "yes"}
        multithreaded = query_params.get("multithreaded", "true").lower() in {"true", "1", "yes"}

        return ProfileOptions(
            clock_type=clock_type,
            builtins=builtins,
            multithreaded=multithreaded,
        )


@dataclass
class ProfileResult:
    func_stats: "YFuncStats"
    thread_stats: "YThreadStats"


class YappiProfiler:
    def __init__(self) -> None:
        self._profiler_lock = Lock()
        self._is_profiling: bool = False

    @property
    def is_profiling(self) -> bool:
        return self._is_profiling

    @contextmanager
    def profile(self, opt: ProfileOptions) -> Generator[ProfileResult]:
        self.start(opt)

        try:
            result = ProfileResult(
                func_stats=None,  # type: ignore[arg-type]
                thread_stats=None,  # type: ignore[arg-type]
            )
            yield result
        finally:
            stopped = self.stop()
            result.func_stats = stopped.func_stats
            result.thread_stats = stopped.thread_stats

    def start(self, opt: ProfileOptions) -> None:
        if self._is_profiling:
            raise ProfilingAlreadyStarted("Profiler is already started")

        with self._profiler_lock:
            if self._is_profiling:
                raise ProfilingAlreadyStarted("Profiler is already started")

            yappi.set_clock_type(opt.clock_type.value)
            yappi.start(builtins=opt.builtins, profile_threads=opt.multithreaded)
            self._is_profiling = True

    def stop(self) -> ProfileResult:
        if not self._is_profiling:
            raise ProfilingNotStarted("Profiler is not started yet")

        with self._profiler_lock:
            if not self._is_profiling:
                raise ProfilingNotStarted("Profiler is not started yet")

            func_stats = yappi.get_func_stats()
            thread_stats = yappi.get_thread_stats()

            yappi.stop()
            yappi.clear_stats()
            self._is_profiling = False

        return ProfileResult(func_stats=func_stats, thread_stats=thread_stats)


class Renderer(Protocol):
    def render(self, result: ProfileResult, trace_ctx: TraceContext | None = None) -> RenderedProfile:
        ...


class PStatRenderer:
    mime_type: MimeType = MimeType.BINARY
    file_ext: str = "pstat"
    render_mode: RenderMode = RenderMode.DOWNLOAD

    def __init__(self) -> None:
        if yappi is None:
            raise ImportError("yappi is not installed")

    def get_filename(self, trace_ctx: TraceContext) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        trace_suffix = trace_ctx.format_for_filename()

        return f"hwk_cpu_yappi_profile_{timestamp}{trace_suffix}.{self.file_ext}"

    def render(self, result: ProfileResult, trace_ctx: TraceContext | None = None) -> RenderedProfile:
        trace_ctx = trace_ctx or TraceContext()

        # Yappi's pstat save requires a file path, not a file object
        fd, temp_path = tempfile.mkstemp(suffix=".pstat")
        try:
            os.close(fd)
            result.func_stats.save(temp_path, type="pstat")
            with open(temp_path, "rb") as f:
                content = f.read()
        finally:
            os.unlink(temp_path)

        metadata = trace_ctx.to_dict() if trace_ctx.is_valid else None

        return RenderedProfile(
            file_name=self.get_filename(trace_ctx),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=content,
            metadata=metadata,
        )


class CallgrindRenderer:
    mime_type: MimeType = MimeType.BINARY
    file_ext: str = "callgrind"
    render_mode: RenderMode = RenderMode.DOWNLOAD

    def __init__(self) -> None:
        if yappi is None:
            raise ImportError("yappi is not installed")

    def get_filename(self, trace_ctx: TraceContext) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        trace_suffix = trace_ctx.format_for_filename()

        return f"hwk_cpu_yappi_profile_{timestamp}{trace_suffix}.{self.file_ext}"

    def render(self, result: ProfileResult, trace_ctx: TraceContext | None = None) -> RenderedProfile:
        trace_ctx = trace_ctx or TraceContext()

        # Yappi's callgrind save requires a file path, not a file object
        fd, temp_path = tempfile.mkstemp(suffix=".callgrind")
        try:
            os.close(fd)
            result.func_stats.save(temp_path, type="callgrind")
            with open(temp_path, "rb") as f:
                content = f.read()
        finally:
            os.unlink(temp_path)

        metadata = trace_ctx.to_dict() if trace_ctx.is_valid else None

        return RenderedProfile(
            file_name=self.get_filename(trace_ctx),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=content,
            metadata=metadata,
        )


class FuncStatsRenderer:
    mime_type: MimeType = MimeType.JSON
    file_ext: str = "json"
    render_mode: RenderMode = RenderMode.VIEW

    def __init__(self) -> None:
        if yappi is None:
            raise ImportError("yappi is not installed")

    def get_filename(self, trace_ctx: TraceContext) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        trace_suffix = trace_ctx.format_for_filename()

        return f"hwk_cpu_yappi_profile_{timestamp}{trace_suffix}.{self.file_ext}"

    def render(self, result: ProfileResult, trace_ctx: TraceContext | None = None) -> RenderedProfile:
        trace_ctx = trace_ctx or TraceContext()

        func_stats_list: list[dict[str, Any]] = []

        for stat in result.func_stats:
            func_stats_list.append({
                "name": stat.name,
                "module": stat.module,
                "lineno": stat.lineno,
                "ncall": stat.ncall,
                "nactualcall": stat.nactualcall,
                "builtin": stat.builtin,
                "ttot": stat.ttot,
                "tsub": stat.tsub,
                "tavg": stat.tavg,
            })

        thread_stats_list: list[dict[str, Any]] = []

        for stat in result.thread_stats:
            thread_stats_list.append({
                "name": stat.name,
                "id": stat.id,
                "tid": stat.tid,
                "ttot": stat.ttot,
                "sched_count": stat.sched_count,
            })

        content: dict[str, Any] = {
            "func_stats": func_stats_list,
            "thread_stats": thread_stats_list,
        }

        metadata = None
        if trace_ctx.is_valid:
            content["trace_context"] = trace_ctx.to_dict()
            metadata = trace_ctx.to_dict()

        return RenderedProfile(
            file_name=self.get_filename(trace_ctx),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=content,
            metadata=metadata,
        )


PROFILE_RENDERERS: dict[ProfileFormat, Renderer] = {}


def _init_renderers() -> None:
    global PROFILE_RENDERERS
    if yappi is not None and not PROFILE_RENDERERS:
        PROFILE_RENDERERS = {
            ProfileFormat.PSTAT: PStatRenderer(),
            ProfileFormat.CALLGRIND: CallgrindRenderer(),
            ProfileFormat.FUNC_STATS: FuncStatsRenderer(),
        }


def get_renderer(format: ProfileFormat) -> Renderer:
    _init_renderers()

    try:
        return PROFILE_RENDERERS[format]
    except KeyError:
        raise ValueError(f"Invalid profile format: {format} (formats: {', '.join(f.value for f in ProfileFormat)})")


profiler = YappiProfiler()


class ProfileHandler:
    def __init__(self, query_params: Mapping[str, str]) -> None:
        if yappi is None:
            raise ImportError("yappi is not installed")

        self._opt = ProfileOptions.from_query_params(query_params)
        self._format = ProfileFormat(query_params.get("format", ProfileFormat.FUNC_STATS.value))

        self._result: ProfileResult | None = None
        self._trace_ctx: TraceContext | None = None

    @contextmanager
    def profile(self) -> Generator[None, None, None]:
        span_attributes = {
            "hawk.format": self._format.value,
            "hawk.clock_type": self._opt.clock_type.value,
            "hawk.builtins": self._opt.builtins,
            "hawk.multithreaded": self._opt.multithreaded,
        }

        with profiling_span("cpu", "yappi", span_attributes):
            # Capture trace context at the start of profiling (inside the span)
            self._trace_ctx = TraceContext.from_current_span()

            with profiler.profile(self._opt) as result:
                self._result = result
                yield

    def render_profile(self) -> RenderedProfile:
        if not self._result or not self._result.func_stats:
            raise ProfilingNotStarted("Profiler is not started yet")

        renderer = get_renderer(self._format)
        trace_ctx = self._trace_ctx or TraceContext()

        return renderer.render(self._result, trace_ctx)
