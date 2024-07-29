from __future__ import annotations

import asyncio
from typing import List

from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from src.hawk.profiling.memory import FormatType, profiler as mem_profiler

def get_router(
    prefix: str = "/debug",
    tags: List[str] | None = ("debug",),
    include_in_schema: bool = True,
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
    async def profile_memory(
        duration: int = 5,
        frames: int = 30,
        count: int = 10,
        format: FormatType = FormatType.LINENO,
        cumulative: bool = False
    ) -> Response:
        """
        """
        mem_profiler.start(frames=frames)

        try:
            heap_usage1, snapshot1 = mem_profiler.snapshot()
            await asyncio.sleep(duration)
            heap_usage2, snapshot2 = mem_profiler.snapshot()
        finally:
            mem_profiler.stop()

        renderer = mem_profiler.get_renderer(format)

        if format == FormatType.PICKLE:
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
    async def start_manual_memory_profile(
        frames: int = 30,
    ) -> None:
        mem_profiler.start(frames=frames)


    @router.get("/prof/mem/snapshot/")
    async def snapshot_memory_manually(
        count: int = 10,
        format: FormatType = FormatType.LINENO,
        cumulative: bool = False,
    ) -> Response:
        heap_usage, snapshot = mem_profiler.snapshot()

        renderer = mem_profiler.get_renderer(format)

        if format == FormatType.PICKLE:
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
        mem_profiler.stop()

    return router
