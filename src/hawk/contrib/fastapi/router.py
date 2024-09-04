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

import asyncio
from enum import Enum

import src.hawk.profiling.mem.tracemalloc as trmalloc
import src.hawk.profiling.cpu.pyinstrument as pyinstr

try:
    from fastapi import APIRouter, Response
    from fastapi.responses import StreamingResponse, HTMLResponse
except ImportError as e:
    raise ImportError(
        "FastAPI is required to use the hawk.contrib.fastapi packages. "
        "Please install it using 'pip install fastapi'."
    ) from e


def get_router(
    prefix: str = "/debug",
    tags: list[str | Enum] | None = None,
    include_in_schema: bool = False,
) -> APIRouter:
    """
    Create a new FastAPI router with all debugging endpoints
    """
    if tags is None:
        tags = ["debug"]

    router = APIRouter(
        prefix=prefix,
        tags=tags,
        include_in_schema=include_in_schema,
    )

    @router.get("/prof/mem/tracemalloc/")
    async def profile_memory_tracemalloc(
        duration: int = 5,
        frames: int = 30,
        gc: bool = True,
        format: trmalloc.ProfileFormat = trmalloc.ProfileFormat.LINENO,
        count: int = 10,
        cumulative: bool = False
    ) -> Response:
        """
        """
        opt = trmalloc.ProfileOptions(frames=frames, gc=gc)

        with trmalloc.profiler.profile(opt) as profile:
            await asyncio.sleep(duration)

        render_opt = trmalloc.RendererOptions(count=count, cumulative=cumulative)
        renderer = trmalloc.get_renderer(format)

        if format == trmalloc.ProfileFormat.PICKLE:
            file_name = renderer.get_file_name()

            return StreamingResponse(
                content=renderer.render(profile, render_opt),
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Disposition": f"attachment; filename={file_name}"
                }
            )

        return Response(
            headers={
                "Content-Type": "application/json",
            },
            content=renderer.render(profile, render_opt),
        )

    @router.get("/prof/mem/tracemalloc/start/")
    async def start_manual_memory_tracemalloc_profile(frames: int = 30, gc: bool = True) -> None:
        opt = trmalloc.ProfileOptions(frames=frames, gc=gc)

        trmalloc.profiler.start(opt)

    @router.get("/prof/mem/tracemalloc/snapshot/")
    async def snapshot_memory_tracemalloc_manually(
        format: trmalloc.ProfileFormat = trmalloc.ProfileFormat.LINENO,
        count: int = 10,
        cumulative: bool = False,
    ) -> Response:
        profile = trmalloc.profiler.snapshot()

        opt = trmalloc.RendererOptions(count=count, cumulative=cumulative)
        renderer = trmalloc.get_renderer(format)

        if format == trmalloc.ProfileFormat.PICKLE:
            file_name = renderer.get_file_name()

            return StreamingResponse(
                content=renderer.render(profile, opt),
                headers={
                    "Content-Type": "application/octet-stream",
                    "Content-Disposition": f"attachment; filename={file_name}"
                }
            )

        return Response(
            headers={
                "Content-Type": "application/json",
            },
            content=renderer.render(profile, opt),
        )

    @router.get("/prof/mem/tracemalloc/stop/")
    async def stop_manual_memory_tracemalloc_profile() -> None:
        trmalloc.profiler.stop()

    if pyinstr.PYINSTRUMENT_INSTALLED:
        @router.get("/prof/cpu/pyinstrument/")
        async def profile_cpu_pyinst(
            duration: int = 5,
            interval: float = 0.001,
            async_mode: pyinstr.AsyncModes = pyinstr.AsyncModes.ENABLED,
            use_timing_thread: bool | None = None,
            format: pyinstr.ProfileFormat = pyinstr.ProfileFormat.HTML,
        ) -> HTMLResponse | StreamingResponse:
            opt = pyinstr.ProfileOptions(
                interval=interval,
                use_timing_thread=use_timing_thread,
                async_mode=async_mode,
            )

            with pyinstr.profiler.profile(opt) as profiler:
                await asyncio.sleep(duration)

            renderer = pyinstr.get_renderer(format)

            filename = renderer.get_filename()
            profile = renderer.render(profiler)

            if format == pyinstr.ProfileFormat.HTML:
                return HTMLResponse(content=profile)

            return StreamingResponse(
                content=profile,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                },
            )

        @router.get("/prof/cpu/pyinstrument/start/")
        async def start_manual_cpu_pyinst_profile(
            interval: float = 0.001,
            use_timing_thread: bool | None = None,
            async_mode: pyinstr.AsyncModes = pyinstr.AsyncModes.ENABLED,
        ) -> None:
            opt = pyinstr.ProfileOptions(
                interval=interval,
                use_timing_thread=use_timing_thread,
                async_mode=async_mode,
            )

            pyinstr.profiler.start(opt)

        @router.get("/prof/cpu/pyinstrument/stop/")
        async def stop_manual_cpu_pyinst_profile(
            format: pyinstr.ProfileFormat = pyinstr.ProfileFormat.HTML,
        ) -> HTMLResponse | StreamingResponse:
            profiler = pyinstr.profiler.stop()

            renderer = pyinstr.get_renderer(format)

            filename = renderer.get_filename()
            profile = renderer.render(profiler)

            if format == pyinstr.ProfileFormat.HTML:
                return HTMLResponse(content=profile)

            return StreamingResponse(
                content=profile,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                },
            )

    return router
