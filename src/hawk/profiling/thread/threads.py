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

import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Generator, Mapping

from hawk.profiling.renderers import RenderMode, MimeType, RenderedProfile
from hawk.profiling.trace_context import TraceContext, profiling_span


# Maximum stack frames to record by default
_DEFAULT_MAX_DEPTH = 128


class ProfileFormat(str, Enum):
    JSON = "json"


@dataclass
class ProfileOptions:
    max_depth: int = _DEFAULT_MAX_DEPTH

    def __post_init__(self):
        if self.max_depth < 1:
            raise ValueError("max_depth should be greater than 0")

    @classmethod
    def from_query_params(cls, query_params: Mapping[str, str]) -> ProfileOptions:
        return cls(
            max_depth=int(query_params.get("max_depth", str(_DEFAULT_MAX_DEPTH))),
        )


@dataclass
class ThreadFrame:
    function: str
    filename: str
    lineno: int


@dataclass
class ThreadInfo:
    thread_id: int
    name: str | None
    daemon: bool | None
    stack: list[ThreadFrame]


@dataclass
class ThreadSnapshot:
    thread_count: int
    threads: list[ThreadInfo]


def _get_thread_name_map() -> dict[int, tuple[str, bool]]:
    """Build a mapping from thread ident to (name, daemon) for all known threads."""
    return {
        t.ident: (t.name, t.daemon)
        for t in threading.enumerate()
        if t.ident is not None
    }


def _extract_stack(frame: Any, max_depth: int) -> list[ThreadFrame]:
    """Extract the call stack from a frame object."""
    stack: list[ThreadFrame] = []
    depth = 0

    while frame is not None and depth < max_depth:
        stack.append(ThreadFrame(
            function=frame.f_code.co_name,
            filename=frame.f_code.co_filename,
            lineno=frame.f_lineno,
        ))
        frame = frame.f_back
        depth += 1

    return stack


def take_snapshot(opt: ProfileOptions | None = None) -> ThreadSnapshot:
    """
    Take a snapshot of all current thread stacks.

    Returns a ThreadSnapshot containing information about all running threads
    and their current call stacks.
    """
    opt = opt or ProfileOptions()
    thread_names = _get_thread_name_map()
    frames = sys._current_frames()

    threads: list[ThreadInfo] = []

    for thread_id, frame in frames.items():
        name, daemon = thread_names.get(thread_id, (None, None))
        stack = _extract_stack(frame, opt.max_depth)

        threads.append(ThreadInfo(
            thread_id=thread_id,
            name=name,
            daemon=daemon,
            stack=stack,
        ))

    return ThreadSnapshot(
        thread_count=len(threads),
        threads=threads,
    )


class JSONRenderer:
    mime_type: MimeType = MimeType.JSON
    file_ext: str = "json"
    render_mode: RenderMode = RenderMode.VIEW

    def get_file_name(self, trace_ctx: TraceContext) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        trace_suffix = trace_ctx.format_for_filename()

        return f"hwk_threads_snapshot_{timestamp}{trace_suffix}.{self.file_ext}"

    def render(
        self,
        snapshot: ThreadSnapshot,
        trace_ctx: TraceContext | None = None,
    ) -> RenderedProfile:
        trace_ctx = trace_ctx or TraceContext()

        threads_data = []
        for thread in snapshot.threads:
            thread_data: dict[str, Any] = {
                "thread_id": thread.thread_id,
                "name": thread.name,
                "daemon": thread.daemon,
                "stack": [
                    {
                        "function": frame.function,
                        "filename": frame.filename,
                        "lineno": frame.lineno,
                    }
                    for frame in thread.stack
                ],
            }
            threads_data.append(thread_data)

        content: dict[str, Any] = {
            "thread_count": snapshot.thread_count,
            "threads": threads_data,
        }

        metadata = None
        if trace_ctx.is_valid:
            content["trace_context"] = trace_ctx.to_dict()
            metadata = trace_ctx.to_dict()

        return RenderedProfile(
            file_name=self.get_file_name(trace_ctx),
            mime_type=self.mime_type,
            render_mode=self.render_mode,
            content=content,
            metadata=metadata,
        )


PROFILE_RENDERERS: dict[ProfileFormat, JSONRenderer] = {
    ProfileFormat.JSON: JSONRenderer(),
}


def get_renderer(format: ProfileFormat) -> JSONRenderer:
    try:
        return PROFILE_RENDERERS[format]
    except KeyError:
        raise ValueError(f"Invalid profile format: {format} (formats: {', '.join(f.value for f in PROFILE_RENDERERS)})")


class ProfileHandler:
    """HTTP handler for thread profiling following the ProfileHandler protocol."""

    def __init__(self, query_params: Mapping[str, str]) -> None:
        self._opt = ProfileOptions.from_query_params(query_params)
        self._format = ProfileFormat(query_params.get("format", ProfileFormat.JSON.value))

        self._snapshot: ThreadSnapshot | None = None
        self._trace_ctx: TraceContext | None = None

    @contextmanager
    def profile(self) -> Generator[None, None, None]:
        span_attributes = {
            "hawk.format": self._format.value,
            "hawk.max_depth": self._opt.max_depth,
        }

        with profiling_span("thread", "threads", span_attributes):
            self._trace_ctx = TraceContext.from_current_span()
            # Take snapshot immediately - this is a point-in-time capture
            self._snapshot = take_snapshot(self._opt)
            yield

    def render_profile(self) -> RenderedProfile:
        if self._snapshot is None:
            raise RuntimeError("Snapshot not taken - call profile() first")

        trace_ctx = self._trace_ctx or TraceContext()

        return get_renderer(self._format).render(self._snapshot, trace_ctx)
