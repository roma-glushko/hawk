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

import cProfile
import io
import os
import pstats
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, Generator, Mapping, Protocol

from hawk.profiling.exceptions import ProfilingAlreadyStarted, ProfilingNotStarted
from hawk.profiling.renderers import MimeType, RenderMode, RenderedProfile
from hawk.profiling.trace_context import TraceContext, profiling_span


class ProfileFormat(str, Enum):
    PSTAT = "pstat"
    TEXT = "text"
    JSON = "json"


class SortKey(str, Enum):
    CUMULATIVE = "cumulative"
    TIME = "time"
    CALLS = "calls"
    NAME = "name"


@dataclass
class ProfileOptions:
    sort_key: SortKey = SortKey.CUMULATIVE
    limit: int = 30

    @classmethod
    def from_query_params(cls, query_params: Mapping[str, str]) -> ProfileOptions:
        sort_key = SortKey(query_params.get("sort", SortKey.CUMULATIVE.value))
        limit = int(query_params.get("limit", "30"))

        return ProfileOptions(
            sort_key=sort_key,
            limit=limit,
        )


class CProfileProfiler:
    def __init__(self) -> None:
        self._profiler_lock = Lock()
        self._curr_profiler: cProfile.Profile | None = None

    @property
    def is_profiling(self) -> bool:
        return self._curr_profiler is not None

    @contextmanager
    def profile(self) -> Generator[cProfile.Profile]:
        profiler = self.start()

        try:
            yield profiler
        finally:
            self.stop()

    def start(self) -> cProfile.Profile:
        if self._curr_profiler:
            raise ProfilingAlreadyStarted("Profiler is already started")

        with self._profiler_lock:
            if self._curr_profiler:
                raise ProfilingAlreadyStarted("Profiler is already started")

            profiler = cProfile.Profile()
            profiler.enable()
            self._curr_profiler = profiler

        return profiler

    def stop(self) -> cProfile.Profile:
        if not self._curr_profiler:
            raise ProfilingNotStarted("Profiler is not started yet")

        with self._profiler_lock:
            if not self._curr_profiler:
                raise ProfilingNotStarted("Profiler is not started yet")

            self._curr_profiler.disable()
            profiler, self._curr_profiler = self._curr_profiler, None

        return profiler


class Renderer(Protocol):
    def render(self, profiler: cProfile.Profile, opt: ProfileOptions, trace_ctx: TraceContext | None = None) -> RenderedProfile:
        ...


class TextRenderer:
    mime_type: MimeType = MimeType.TEXT
    file_ext: str = "txt"
    render_mode: RenderMode = RenderMode.VIEW

    def get_filename(self, trace_ctx: TraceContext) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        trace_suffix = trace_ctx.format_for_filename()

        return f"hwk_cpu_cprofile_profile_{timestamp}{trace_suffix}.{self.file_ext}"

    def render(self, profiler: cProfile.Profile, opt: ProfileOptions, trace_ctx: TraceContext | None = None) -> RenderedProfile:
        trace_ctx = trace_ctx or TraceContext()

        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats(opt.sort_key.value)
        ps.print_stats(opt.limit)
        content = s.getvalue()

        metadata = trace_ctx.to_dict() if trace_ctx.is_valid else None

        return RenderedProfile(
            file_name=self.get_filename(trace_ctx),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=content,
            metadata=metadata,
        )


class PStatRenderer:
    mime_type: MimeType = MimeType.BINARY
    file_ext: str = "pstat"
    render_mode: RenderMode = RenderMode.DOWNLOAD

    def get_filename(self, trace_ctx: TraceContext) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        trace_suffix = trace_ctx.format_for_filename()

        return f"hwk_cpu_cprofile_profile_{timestamp}{trace_suffix}.{self.file_ext}"

    def render(self, profiler: cProfile.Profile, opt: ProfileOptions, trace_ctx: TraceContext | None = None) -> RenderedProfile:
        trace_ctx = trace_ctx or TraceContext()

        # pstats.dump_stats requires a file path
        fd, temp_path = tempfile.mkstemp(suffix=".pstat")
        try:
            os.close(fd)
            ps = pstats.Stats(profiler)
            ps.dump_stats(temp_path)
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


class JSONRenderer:
    mime_type: MimeType = MimeType.JSON
    file_ext: str = "json"
    render_mode: RenderMode = RenderMode.VIEW

    def get_filename(self, trace_ctx: TraceContext) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        trace_suffix = trace_ctx.format_for_filename()

        return f"hwk_cpu_cprofile_profile_{timestamp}{trace_suffix}.{self.file_ext}"

    def render(self, profiler: cProfile.Profile, opt: ProfileOptions, trace_ctx: TraceContext | None = None) -> RenderedProfile:
        trace_ctx = trace_ctx or TraceContext()

        ps = pstats.Stats(profiler)
        ps.sort_stats(opt.sort_key.value)

        func_stats: list[dict[str, Any]] = []
        for key, value in ps.stats.items():  # type: ignore[attr-defined]
            filename, lineno, func_name = key
            ncalls, totcalls, tottime, cumtime, callers = value

            func_stats.append({
                "filename": filename,
                "lineno": lineno,
                "function": func_name,
                "ncalls": ncalls,
                "totcalls": totcalls,
                "tottime": tottime,
                "cumtime": cumtime,
                "percall_tottime": tottime / ncalls if ncalls > 0 else 0,
                "percall_cumtime": cumtime / ncalls if ncalls > 0 else 0,
            })

        # Sort by the appropriate key
        sort_key_map = {
            SortKey.CUMULATIVE: lambda x: x["cumtime"],
            SortKey.TIME: lambda x: x["tottime"],
            SortKey.CALLS: lambda x: x["ncalls"],
            SortKey.NAME: lambda x: x["function"],
        }
        func_stats.sort(key=sort_key_map[opt.sort_key], reverse=opt.sort_key != SortKey.NAME)

        # Apply limit
        func_stats = func_stats[: opt.limit]

        content: dict[str, Any] = {
            "total_calls": ps.total_calls,  # type: ignore[attr-defined]
            "total_time": ps.total_tt,  # type: ignore[attr-defined]
            "func_stats": func_stats,
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


PROFILE_RENDERERS: dict[ProfileFormat, Renderer] = {
    ProfileFormat.TEXT: TextRenderer(),
    ProfileFormat.PSTAT: PStatRenderer(),
    ProfileFormat.JSON: JSONRenderer(),
}


def get_renderer(format: ProfileFormat) -> Renderer:
    try:
        return PROFILE_RENDERERS[format]
    except KeyError:
        raise ValueError(f"Invalid profile format: {format} (formats: {', '.join(f.value for f in ProfileFormat)})")


profiler = CProfileProfiler()


class ProfileHandler:
    def __init__(self, query_params: Mapping[str, str]) -> None:
        self._opt = ProfileOptions.from_query_params(query_params)
        self._format = ProfileFormat(query_params.get("format", ProfileFormat.TEXT.value))

        self._profiler: cProfile.Profile | None = None
        self._trace_ctx: TraceContext | None = None

    @contextmanager
    def profile(self) -> Generator[None, None, None]:
        span_attributes = {
            "hawk.format": self._format.value,
            "hawk.sort": self._opt.sort_key.value,
            "hawk.limit": self._opt.limit,
        }

        with profiling_span("cpu", "cprofile", span_attributes):
            # Capture trace context at the start of profiling (inside the span)
            self._trace_ctx = TraceContext.from_current_span()

            with profiler.profile() as p:
                self._profiler = p
                yield

    def render_profile(self) -> RenderedProfile:
        if not self._profiler:
            raise ProfilingNotStarted("Profiler is not started yet")

        renderer = get_renderer(self._format)
        trace_ctx = self._trace_ctx or TraceContext()

        return renderer.render(self._profiler, self._opt, trace_ctx)
