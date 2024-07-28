from __future__ import annotations

import io
import linecache
import os
import pickle
import tracemalloc
from datetime import datetime
from enum import Enum
from typing import Any, Iterator, TypedDict, List, Union, Protocol


def format_bytes(value: int) -> str:
    formatted_value = float(value)

    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'):
        if abs(formatted_value) < 1024.0:
            return f"{formatted_value:3.1f} {unit}"

        formatted_value /= 1024.0

    return f"{formatted_value:.1f} YB"


AnyStats = Union[List[tracemalloc.Statistic], List[tracemalloc.StatisticDiff]]


class FormatType(str, Enum):
    LINENO = "lineno"
    TRACEBACK = "traceback"
    PICKLE = "pickle"


class HeapUsage(TypedDict):
    heap_current_bytes: int
    heap_current: str
    heap_diff_bytes: int | None
    heap_diff: str | None


class Renderer(Protocol):
    def render(
        self,
        snapshot: tracemalloc.Snapshot,
        heap_usage_bytes: int,
        initial_snapshot: tracemalloc.Snapshot | None = None,
        initial_heap_usage_bytes: int | None = None,
        count: int = 10,
        cumulative: bool = False,
    ) -> Any:
        ...

    def headers(self) -> dict[str, str]:
        ...


class LinenoSnapshotRenderer:
    def render(
            self,
            snapshot: tracemalloc.Snapshot,
            heap_usage_bytes: int,
            initial_snapshot: tracemalloc.Snapshot | None = None,
            initial_heap_usage_bytes: int | None = None,
            count: int = 10,
            cumulative: bool = False,
    ) -> dict[str, Any]:
        top_stats: AnyStats

        if not initial_snapshot:
            top_stats = snapshot.statistics("lineno", cumulative=cumulative)
        else:
            top_stats = snapshot.compare_to(initial_snapshot, "lineno", cumulative=cumulative)

        heap_usage = {
            "heap_current_bytes": heap_usage_bytes,
            "heap_current": format_bytes(heap_usage_bytes),
        }

        if initial_heap_usage_bytes:
            heap_diff_bytes = heap_usage_bytes - initial_heap_usage_bytes

            heap_usage |= {
                "heap_diff_bytes": heap_diff_bytes,
                "heap_diff": format_bytes(heap_diff_bytes),
            }

        return {
            "stats": list(self._format_lineno(top_stats, count=count)),
            **heap_usage,
        }

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
    _headers = {
        "Content-Type": "application/json",
    }

    def render(
        self,
        snapshot: tracemalloc.Snapshot,
        heap_usage_bytes: int,
        initial_snapshot: tracemalloc.Snapshot | None = None,
        initial_heap_usage_bytes: int | None = None,
        count: int = 10,
        cumulative: bool = False,  # not supported by traceback
    ) -> dict[str, Any]:
        """
        Render the snapshot in a human-readable format
        """
        top_stats: list[tracemalloc.Statistic] | list[tracemalloc.StatisticDiff]

        if not initial_snapshot:
            top_stats = snapshot.statistics("traceback")
        else:
            top_stats = snapshot.compare_to(initial_snapshot, "traceback")

        heap_usage: HeapUsage = {
            "heap_current_bytes": heap_usage_bytes,
            "heap_current": format_bytes(heap_usage_bytes),
            "heap_diff_bytes": None,
            "heap_diff": None,
        }

        if initial_heap_usage_bytes:
            heap_diff_bytes = heap_usage_bytes - initial_heap_usage_bytes

            heap_usage |= {
                "heap_diff_bytes": heap_diff_bytes,
                "heap_diff": format_bytes(heap_diff_bytes),
            }

        return {
            "stats": (
                {
                    "mem_blocks_count": stat.count,
                    "mem_blocks_size_bytes": stat.size,
                    "mem_blocks_size": format_bytes(stat.size),
                    "traceback": stat.traceback.format(),
                }
                for stat in top_stats[:count]
            ),
            **heap_usage,
        }

    def headers(self) -> dict[str, str]:
        return self._headers


class PickleSnapshotRenderer:
    def render(self, snapshot: tracemalloc.Snapshot) -> io.BytesIO:
        """
        Pickling the snapshot class to be able to analyze it later via loading it with `Snapshot.load()`
        """
        snapshot_content = io.BytesIO()
        pickle.dump(
            snapshot,
            snapshot_content,
            pickle.HIGHEST_PROTOCOL,
        )
        snapshot_content.seek(0)

        return snapshot_content

    def headers(self) -> dict[str, str]:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"hwk_mem_snapshot_{timestamp}.pkl"

        return {
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f"attachment; filename={file_name}"
        }


class TracemallocProfiler:
    def __init__(self):
        self._tracemalloc_enabled_in_env = bool(os.environ.get("PYTHONTRACEMALLOC", False))

    def start(self, frames: int = 30) -> None:
        """
        Start tracing memory allocations
        """
        if tracemalloc.is_tracing():
            # Tracing has already started
            ...

        tracemalloc.start(frames)

    def snapshot(self) -> tuple[int, tracemalloc.Snapshot]:
        """
        Take a snapshot of the current memory allocations
        """
        if not tracemalloc.is_tracing():
            ...

        heap_usage, _ = tracemalloc.get_traced_memory()
        snapshot = tracemalloc.take_snapshot()

        return heap_usage, snapshot

    def stop(self) -> None:
        """
        Stop tracing memory allocations
        """
        if not tracemalloc.is_tracing():
            ...

        tracemalloc.stop()


renderers = {
    FormatType.LINENO: LinenoSnapshotRenderer(),
    FormatType.TRACEBACK: TracebackSnapshotRender(),
    FormatType.PICKLE: PickleSnapshotRenderer(),
}


def get_renderer(format: FormatType) -> Union[Renderer, PickleSnapshotRenderer]:
    return renderers[format]


profiler = TracemallocProfiler()
