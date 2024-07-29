import asyncio
import gc
import io
import linecache
import pickle
import tracemalloc
from datetime import datetime
from enum import StrEnum
from typing import Any

from pyinstrument import Profiler
from pyinstrument.renderers.html import HTMLRenderer, JSONRenderer
from pyinstrument.renderers.speedscope import SpeedscopeRenderer

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, HTMLResponse

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
)


def format_bytes(value: int) -> str:
    for unit in ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'):
        if abs(value) < 1024.0:
            return f"{value:3.1f} {unit}"

        value /= 1024.0

    return f"{value:.1f} YB"


class ReportType(StrEnum):
    LINENO = "lineno"
    TRACEBACK = "traceback"


@router.get("/prof/mem/")
async def profile_memory(
    duration: int = 5,
    frames: int = 30,
    count: int = 10,
    report: ReportType = ReportType.LINENO,
    cumulative: bool = False
) -> dict[str, Any]:
    if tracemalloc.is_tracing():
        # throw an error that tracing should be started first
        return {}

    tracemalloc.start(frames)

    try:
        heap_usage1, _ = tracemalloc.get_traced_memory()  # current memory usage
        snapshot1 = tracemalloc.take_snapshot()

        await asyncio.sleep(duration)

        heap_usage2, _ = tracemalloc.get_traced_memory()  # current memory usage
        snapshot2 = tracemalloc.take_snapshot()
    finally:
        tracemalloc.stop()

    if report == ReportType.TRACEBACK:
        cumulative = False

    top_stats = snapshot2.compare_to(snapshot1, str(report), cumulative=cumulative)

    if report == ReportType.TRACEBACK:
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
            "heap_current": format_bytes(heap_usage2),
            "heap_diff": format_bytes(heap_usage2 - heap_usage1),
        }

    def format_lineno() -> list[dict[str, Any]]:
        stats = []

        for stat in top_stats[:count]:
            frame = stat.traceback[0]

            code_line = linecache.getline(frame.filename, frame.lineno).strip()

            stats.append({
                "stat": str(stat),
                "mem_blocks_count": stat.count,
                "mem_blocks_size_bytes": stat.size,
                "mem_blocks_size": format_bytes(stat.size),
                "filename": frame.filename,
                "lineno": frame.lineno,
                "code": code_line,
            })

        return stats

    return {
        "stats": format_lineno(),
        "heap_initial": format_bytes(heap_usage1),
        "heap_current": format_bytes(heap_usage2),
        "heap_diff": format_bytes(heap_usage2 - heap_usage1),
    }


@router.get("/prof/mem/start/")
async def start_manual_memory_profile(
    frames: int = 30,
) -> None:
    if tracemalloc.is_tracing():
        return

    tracemalloc.start(frames)


@router.get("/prof/mem/snapshot/")
async def snapshot_memory_manually(count: int = 10, cumulative: bool = False) -> dict[str, Any]:
    if not tracemalloc.is_tracing():
        # throw an error that tracing should be started first
        return {}

    snapshot = tracemalloc.take_snapshot()
    heap_usage, _ = tracemalloc.get_traced_memory()  # current memory usage

    top_stats = snapshot.statistics("lineno", cumulative=cumulative)

    return {
        "stats": (str(stat) for stat in top_stats[:count]),
        "heap_current_bytes": heap_usage,
        "heap_current": format_bytes(heap_usage),
    }


@router.get("/prof/mem/stop/")
async def stop_manual_memory_profile() -> None:
    if not tracemalloc.is_tracing():
        return

    tracemalloc.stop()


class CPUProfiler(StrEnum):
    CPROFILE = "cprofile"
    PYINSTRUMENT = "pyinstrument"


class CPUProfileFormat(StrEnum):
    HTML = "html"
    TEXT = "text"
    JSON = "json"


@router.get("/prof/cpu/")
async def profile_cpu(
    duration: int = 5,
    interval: float = 0.001,
    async_mode: str = "enabled",
    profiler: CPUProfiler = CPUProfiler.PYINSTRUMENT,
    format: str = "html",
) -> StreamingResponse:
    profile_type_to_ext = {"json": "json", "html": "html", "speedscope": "speedscope.json"}
    profile_type_to_renderer = {
        "json": JSONRenderer,
        "html": HTMLRenderer,
        "speedscope": SpeedscopeRenderer,
    }
    # https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
    profiler = Profiler(interval=interval, async_mode=async_mode)

    with profiler:
        await asyncio.sleep(duration)

    extension = profile_type_to_ext[format]
    renderer = profile_type_to_renderer[format]()

    profile_content = profiler.output(renderer=renderer)

    if format == "html":
        return HTMLResponse(content=profile_content)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"hwk_cpu_profile_{timestamp}.{extension}"

    return StreamingResponse(
        content=profile_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}",
        },
    )

    # with open(f"profile.{extension}", "w") as out:
    #     out.write(profiler.output(renderer=renderer))


@router.get("/prof/cpu/start/")
async def profile_cpu(
    duration: int = 5,
    interval: float = 0.001,
    async_mode: str = "enabled",
    profiler: CPUProfiler = CPUProfiler.PYINSTRUMENT,
) -> None:
    profiler = Profiler(interval=interval, async_mode=async_mode)
    profiler.start()


@router.get("/prof/cpu/snapshot/")
async def profile_cpu(
    duration: int = 5,
    interval: float = 0.001,
    async_mode: str = "enabled",
    profiler: CPUProfiler = CPUProfiler.PYINSTRUMENT,
) -> None:
    profiler = Profiler(interval=interval, async_mode=async_mode)
    profiler.start()


@router.get("/prof/cpu/stop/")
async def profile_cpu(
    duration: int = 5,
    interval: float = 0.001,
    async_mode: str = "enabled",
    profiler: CPUProfiler = CPUProfiler.PYINSTRUMENT,
) -> None:
    profiler = Profiler(interval=interval, async_mode=async_mode)
    profiler.stop()


@router.get("/gc/")
async def run_gc() -> None:
    gc.collect()
