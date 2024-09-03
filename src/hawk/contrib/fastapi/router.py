from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse, HTMLResponse

import src.hawk.profiling.memory as trmalloc
import src.hawk.profiling.cpu.pyinstrument as pyinstr


def get_router(
    prefix: str = "/debug",
    tags: list[str | Enum] | None = ("debug",),
    include_in_schema: bool = False,
) -> APIRouter:
    """
    Create a new FastAPI router with all debugging endpoints
    """
    router = APIRouter(
        prefix=prefix,
        tags=tags,
        include_in_schema=include_in_schema,
    )

    @router.get("/prof/mem/")
    async def profile_memory_trmalloc(
        duration: int = 5,
        frames: int = 30,
        count: int = 10,
        format: trmalloc.ProfileFormat = trmalloc.ProfileFormat.LINENO,
        cumulative: bool = False
    ) -> Response:
        """
        """
        trmalloc.profiler.start(frames=frames)

        try:
            heap_usage1, snapshot1 = trmalloc.profiler.snapshot()
            await asyncio.sleep(duration)
            heap_usage2, snapshot2 = trmalloc.profiler.snapshot()
        finally:
            trmalloc.profiler.stop()

        renderer = trmalloc.profiler.get_renderer(format)

        if format == trmalloc.ProfileFormat.PICKLE:
            return StreamingResponse(
                content=renderer.render(snapshot2),
                headers=renderer.headers()
            )

        return Response(
            content=renderer.render(
                snapshot2,
                heap_usage2,
                snapshot1,
                heap_usage1,
                count,
                cumulative
            ),
            headers=renderer.headers(),
        )


    @router.get("/prof/mem/start/")
    async def start_manual_memory_trmalloc_profile(frames: int = 30) -> None:
        trmalloc.profiler.start(frames=frames)

    @router.get("/prof/mem/snapshot/")
    async def snapshot_memory_trmalloc_manually(
        count: int = 10,
        format: trmalloc.ProfileFormat = trmalloc.ProfileFormat.LINENO,
        cumulative: bool = False,
    ) -> Response:
        heap_usage, snapshot = trmalloc.profiler.snapshot()

        renderer = trmalloc.profiler.get_renderer(format)

        if format == trmalloc.ProfileFormat.PICKLE:
            return StreamingResponse(
                content=renderer.render(snapshot),
                headers=renderer.headers()
            )

        return Response(
            content=renderer.render(
                snapshot,
                heap_usage,
                count,
                cumulative
            ),
            headers=renderer.headers(),
        )

    @router.get("/prof/mem/stop/")
    async def stop_manual_memory_profile() -> None:
        trmalloc.profiler.stop()

    @router.get("/prof/cpu/")
    async def profile_cpu_pyinst(
        duration: int = 5,
        interval: float = 0.001,
        async_mode: pyinstr.AsyncModes = pyinstr.AsyncModes.ENABLED,
        use_timing_thread: bool | None = None,
        format: pyinstr.ProfileFormat = pyinstr.ProfileFormat.HTML,
    ) -> HTMLResponse | StreamingResponse:
        pyinstr.profiler.start(interval=interval, use_timing_thread=use_timing_thread, async_mode=async_mode)
        await asyncio.sleep(duration)
        profiler = pyinstr.profiler.stop()

        profile_type_to_ext = {"json": "json", "html": "html", "speedscope": "speedscope.json"}

        extension = profile_type_to_ext[format]
        renderer = pyinstr.profiler.get_renderer(format)

        profile = profiler.output(renderer=renderer)

        if format == pyinstr.ProfileFormat.HTML:
            return HTMLResponse(content=profile)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"hwk_cpu_profile_{timestamp}.{extension}"

        return StreamingResponse(
            content=profile,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}",
            },
        )

    @router.get("/prof/cpu/start/")
    async def start_manual_cpu_pyinst_profile(
        interval: float = 0.001,
        use_timing_thread: bool | None = None,
        async_mode: pyinstr.AsyncModes = pyinstr.AsyncModes.ENABLED,
    ) -> None:
        pyinstr.profiler.start(
            interval=interval,
            use_timing_thread=use_timing_thread,
            async_mode=async_mode,
        )

    @router.get("/prof/cpu/stop/")
    async def stop_manual_cpu_pyinst_profile(
        format: pyinstr.ProfileFormat = pyinstr.ProfileFormat.HTML,
    ) -> HTMLResponse | StreamingResponse:
        profiler = pyinstr.profiler.stop()

        profile_type_to_ext = {"json": "json", "html": "html", "speedscope": "speedscope.json"}
        renderer = pyinstr.profiler.get_renderer(format)

        profile = profiler.output(renderer=renderer)

        if format == pyinstr.ProfileFormat.HTML:
            return HTMLResponse(content=profile)

        extension = profile_type_to_ext[format]

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"hwk_cpu_profile_{timestamp}.{extension}"

        return StreamingResponse(
            content=profile,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={file_name}",
            },
        )

    return router
