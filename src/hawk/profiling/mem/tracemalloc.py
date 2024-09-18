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

import gc
import io
import linecache
import os
import pickle
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Iterator, TypedDict, List, Union, Generator, Protocol, Mapping

from hawk.profiling.exceptions import ProfilingAlreadyStarted, ProfilingNotStarted
from hawk.profiling.renderers import RenderMode, MimeType, RenderedProfile


def format_bytes(value: int) -> str:
    formatted_value = float(value)

    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'):
        if abs(formatted_value) < 1024.0:
            return f"{formatted_value:3.1f} {unit}"

        formatted_value /= 1024.0

    return f"{formatted_value:.1f} YB"


AnyStats = Union[List[tracemalloc.Statistic], List[tracemalloc.StatisticDiff]]


class ProfileFormat(str, Enum):
    LINENO = "lineno"
    TRACEBACK = "traceback"
    PICKLE = "pickle"


@dataclass
class ProfileOptions:
    gc: bool = True
    frames: int = 30

    def __post_init__(self):
        if self.frames < 1:
            raise ValueError("Frames should be greater than 0")

    @classmethod
    def from_query_params(cls, query_params: Mapping[str, str]) -> ProfileOptions:
        return cls(
            gc=query_params.get("gc", "1").lower() in {"1", "true", "yes"},
            frames=int(query_params.get("frames", "30")),
        )


@dataclass
class IntervalProfile:
    start_heap_usage_bytes: int
    start_snapshot: tracemalloc.Snapshot
    stop_heap_usage_bytes: int
    stop_snapshot: tracemalloc.Snapshot


class IntervalProfileProxy:
    def __init__(self, start_profile: PointInTimeProfile):
        self.start_profile = start_profile
        self.stop_profile: PointInTimeProfile | None = None

        self._interval_profile: IntervalProfile | None = None

    def get(self) -> IntervalProfile:
        if self.stop_profile is None:
            raise RuntimeError("Stop profile is not set")

        if self._interval_profile is not None:
            return self._interval_profile

        self._interval_profile = IntervalProfile(
            start_heap_usage_bytes=self.start_profile.heap_usage_bytes,
            start_snapshot=self.start_profile.snapshot,
            stop_heap_usage_bytes=self.stop_profile.heap_usage_bytes,
            stop_snapshot=self.stop_profile.snapshot,
        )

        return self._interval_profile

    def stop(self, stop_profile: PointInTimeProfile) -> None:
        self.stop_profile = stop_profile


@dataclass
class PointInTimeProfile:
    heap_usage_bytes: int
    snapshot: tracemalloc.Snapshot


@dataclass
class RendererOptions:
    count: int = 10
    cumulative: bool = False

    @classmethod
    def from_query_params(cls, query_params: Mapping[str, str]) -> RendererOptions:
        return cls(
            count=int(query_params.get("count", "10")),
            cumulative=query_params.get("cumulative", "0").lower() in {"1", "true", "yes"},
        )


class HeapUsage(TypedDict):
    heap_current_bytes: int
    heap_current: str
    heap_diff_bytes: int | None
    heap_diff: str | None


class TracemallocProfiler:
    """
    Memory profiler based on the tracemalloc standard library
    References:
    - https://docs.python.org/3/library/tracemalloc.html
    """

    def __init__(self):
        self._tracemalloc_enabled_in_env = bool(os.environ.get("PYTHONTRACEMALLOC", False))

    @contextmanager
    def profile(self, opt: ProfileOptions) -> Generator[IntervalProfileProxy]:
        self.start(opt)
        profile_proxy = IntervalProfileProxy(self.snapshot())

        try:
            yield profile_proxy
        finally:
            profile_proxy.stop(self.snapshot())
            self.stop()

    def start(self, opt: ProfileOptions) -> None:
        """
        Start tracing memory allocations
        """
        if tracemalloc.is_tracing():
            raise ProfilingAlreadyStarted(
                "Profiler is already started via environment variable PYTHONTRACEMALLOC"
                if self._tracemalloc_enabled_in_env
                else "Profiler is already started",
            )

        if opt.gc:
            gc.collect()

        tracemalloc.start(opt.frames)

    def snapshot(self) -> PointInTimeProfile:
        """
        Take a snapshot of the current memory allocations
        """
        if not tracemalloc.is_tracing():
            raise ProfilingNotStarted("Profiler is not started yet")

        heap_usage, _ = tracemalloc.get_traced_memory()

        return PointInTimeProfile(
            heap_usage_bytes=heap_usage,
            snapshot=tracemalloc.take_snapshot(),
        )

    def stop(self) -> None:
        """
        Stop tracing memory allocations
        """
        if not tracemalloc.is_tracing():
            raise ProfilingNotStarted("Profiler is not started yet")

        tracemalloc.stop()


class Renderer(Protocol):
    file_ext: str

    def render(
        self,
        profile: PointInTimeProfile | IntervalProfile | IntervalProfileProxy,
        opt: RendererOptions
    ) -> RenderedProfile:
        ...


class LinenoSnapshotRenderer:
    mime_type: MimeType = MimeType.JSON
    file_ext: str = "json"
    render_mode: RenderMode = RenderMode.VIEW

    def get_file_name(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_mem_tracemalloc_snapshot_{timestamp}.{self.file_ext}"

    def render(
        self,
        profile: PointInTimeProfile | IntervalProfile | IntervalProfileProxy,
        opt: RendererOptions,
    ) -> RenderedProfile:
        if isinstance(profile, PointInTimeProfile):
            return self._render_point_in_time_profile(profile, opt.count, opt.cumulative)

        if isinstance(profile, IntervalProfile):
            return self._render_interval_profile(profile, opt.count, opt.cumulative)

        if isinstance(profile, IntervalProfileProxy):
            return self._render_interval_profile(profile.get(), opt.count, opt.cumulative)

        raise ValueError("Invalid profile type")

    def _render_point_in_time_profile(
        self,
        profile: PointInTimeProfile,
        count: int = 10,
        cumulative: bool = False,
    ) -> RenderedProfile:
        top_stats = profile.snapshot.statistics("lineno", cumulative=cumulative)

        heap_usage = {
            "heap_current_bytes": profile.heap_usage_bytes,
            "heap_current": format_bytes(profile.heap_usage_bytes),
        }

        return RenderedProfile(
            file_name=self.get_file_name(),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content={
                "stats": list(self._format_lineno(top_stats, count=count)),
                **heap_usage,
            },
        )

    def _render_interval_profile(
        self,
        profile: IntervalProfile,
        count: int = 10,
        cumulative: bool = False,
    ) -> RenderedProfile:
        top_stats = profile.stop_snapshot.compare_to(
            profile.start_snapshot,
            "lineno",
            cumulative=cumulative,
        )

        heap_diff_bytes = profile.stop_heap_usage_bytes - profile.start_heap_usage_bytes

        heap_usage = {
            "heap_current_bytes": profile.stop_heap_usage_bytes,
            "heap_current": format_bytes(profile.stop_heap_usage_bytes),
            "heap_diff_bytes": heap_diff_bytes,
            "heap_diff": format_bytes(heap_diff_bytes),
        }

        return RenderedProfile(
            file_name=self.get_file_name(),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content={
                "stats": list(self._format_lineno(top_stats, count=count)),
                **heap_usage,
            },
        )

    def _format_lineno(self, top_stats: AnyStats, count: int = 10) -> Iterator[dict[str, Any]]:
        for stat in top_stats[:count]:
            frame = stat.traceback[0]

            code_line = linecache.getline(frame.filename, frame.lineno).strip()

            yield {
                "stat": str(stat),
                "mem_blocks_count": stat.count,
                "mem_blocks_size_bytes": stat.size,
                "mem_blocks_size": format_bytes(stat.size),
                "filename": frame.filename,
                "lineno": frame.lineno,
                "code": code_line,
            }


class TracebackSnapshotRender:
    mime_type: MimeType = MimeType.JSON
    file_ext: str = "json"
    render_mode: RenderMode = RenderMode.VIEW

    def get_file_name(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_mem_tracemalloc_snapshot_{timestamp}.{self.file_ext}"

    def render(
        self,
        profile: PointInTimeProfile | IntervalProfile | IntervalProfileProxy,
        opt: RendererOptions,
    ) -> RenderedProfile:
        """
        Render the snapshot in a human-readable format
        """
        if isinstance(profile, PointInTimeProfile):
            return self._render_point_in_time_profile(profile, opt.count)

        if isinstance(profile, IntervalProfile):
            return self._render_interval_profile(profile, opt.count)

        if isinstance(profile, IntervalProfileProxy):
            return self._render_interval_profile(profile.get(), opt.count)

        raise ValueError("Invalid profile type")

    def _render_point_in_time_profile(
        self,
        profile: PointInTimeProfile,
        count: int = 10,
    ) -> RenderedProfile:
        top_stats = profile.snapshot.statistics("traceback")

        heap_usage = {
            "heap_current_bytes": profile.heap_usage_bytes,
            "heap_current": format_bytes(profile.heap_usage_bytes),
        }

        return RenderedProfile(
            file_name=self.get_file_name(),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content={
                "stats": list(self._format_traceback(top_stats, count=count)),
                **heap_usage,
            },
        )

    def _render_interval_profile(
        self,
        profile: IntervalProfile,
        count: int = 10,
    ) -> RenderedProfile:
        top_stats = profile.stop_snapshot.compare_to(
            profile.start_snapshot,
            "traceback",
        )

        heap_diff_bytes = profile.stop_heap_usage_bytes - profile.start_heap_usage_bytes

        heap_usage = {
            "heap_current_bytes": profile.stop_heap_usage_bytes,
            "heap_current": format_bytes(profile.stop_heap_usage_bytes),
            "heap_diff_bytes": heap_diff_bytes,
            "heap_diff": format_bytes(heap_diff_bytes),
        }

        return RenderedProfile(
            file_name=self.get_file_name(),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content={
                "stats": list(self._format_traceback(top_stats, count=count)),
                **heap_usage,
            },
        )

    def _format_traceback(self, top_stats: AnyStats, count: int = 10) -> Iterator[dict[str, Any]]:
        for stat in top_stats[:count]:
            yield {
                "mem_blocks_count": stat.count,
                "mem_blocks_size_bytes": stat.size,
                "mem_blocks_size": format_bytes(stat.size),
                "traceback": stat.traceback.format(),
            }


class PickleSnapshotRenderer:
    mime_type: MimeType = MimeType.BINARY
    file_ext: str = "pkl"
    render_mode: RenderMode = RenderMode.DOWNLOAD

    def get_file_name(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        return f"hwk_mem_tracemalloc_snapshot_{timestamp}.{self.file_ext}"

    def render(
        self,
        profile: PointInTimeProfile | IntervalProfile | IntervalProfileProxy,
        opt: RendererOptions,
    ) -> RenderedProfile:
        """
        Pickling the snapshot class to be able to analyze it later via loading it with `Snapshot.load()`
        """
        snapshot: tracemalloc.Snapshot

        if isinstance(profile, PointInTimeProfile):
            snapshot = profile.snapshot
        elif isinstance(profile, IntervalProfile):
            snapshot = profile.stop_snapshot
        elif isinstance(profile, IntervalProfileProxy):
            snapshot = profile.get().stop_snapshot
        else:
            raise ValueError("Invalid profile type")

        snapshot_content = io.BytesIO()
        pickle.dump(
            snapshot,
            snapshot_content,
            pickle.HIGHEST_PROTOCOL,
        )

        snapshot_content.seek(0)

        return RenderedProfile(
            file_name=self.get_file_name(),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=snapshot_content.getvalue(),
        )


PROFILE_RENDERERS: dict[str, Renderer] = {
    ProfileFormat.LINENO: LinenoSnapshotRenderer(),
    ProfileFormat.TRACEBACK: TracebackSnapshotRender(),
    ProfileFormat.PICKLE: PickleSnapshotRenderer(),
}


def get_renderer(format: ProfileFormat) -> Renderer:
    try:
        return PROFILE_RENDERERS[format]
    except KeyError:
        raise ValueError(f"Invalid profile format: {format} (formats: {', '.join(PROFILE_RENDERERS)})")


profiler = TracemallocProfiler()


class ProfileHandler:
    def __init__(self, query_params: Mapping[str, str]) -> None:
        self._opt = ProfileOptions.from_query_params(query_params)
        self._renderer_opt = RendererOptions.from_query_params(query_params)
        self._format = ProfileFormat(query_params.get("format", ProfileFormat.LINENO))

        self._interval_profile: IntervalProfileProxy | None = None

    @contextmanager
    def profile(self) -> Generator[None, None, None]:
        with profiler.profile(self._opt) as profile_proxy:
            self._interval_profile = profile_proxy
            yield

    def render_profile(self) -> RenderedProfile:
        if self._interval_profile is None:
            raise RuntimeError("Interval profile is not set")

        return get_renderer(self._format).render(
            self._interval_profile,
            self._renderer_opt,
        )
