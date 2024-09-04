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
from typing import Sequence

from starlette.applications import Request, Response
from starlette.responses import StreamingResponse
from starlette.routing import Router, BaseRoute, Middleware

from src.hawk.profiling.mem.tracemalloc import ProfileFormat, profiler as mem_profiler


async def profile_memory(request: Request) -> Response:
    duration = int(request.query_params.get("duration", 5))
    frames = int(request.query_params.get("frames", 30))
    count = int(request.query_params.get("count", 10))
    format = ProfileFormat(request.query_params.get("format", ProfileFormat.LINENO))
    cumulative = request.query_params.get("cumulative", "false").lower() in ["true", "1"]

    mem_profiler.start(frames=frames)

    try:
        heap_usage1, snapshot1 = mem_profiler.snapshot()
        await asyncio.sleep(duration)
        heap_usage2, snapshot2 = mem_profiler.snapshot()
    finally:
        mem_profiler.stop()

    renderer = mem_profiler.get_renderer(format)

    if format == ProfileFormat.PICKLE:
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

async def start_manual_memory_profile(request: Request) -> Response:
    frames = int(request.query_params.get("frames", 30))

    mem_profiler.start(frames=frames)

    return Response(content="Memory profiling started")

async def snapshot_memory_manually(request: Request) -> Response:
    count = int(request.query_params.get("count", 10))
    format = ProfileFormat(request.query_params.get("format", ProfileFormat.LINENO))
    cumulative = request.query_params.get("cumulative", "false").lower() in ["true", "1"]

    heap_usage, snapshot = mem_profiler.snapshot()

    renderer = mem_profiler.get_renderer(format)

    if format == ProfileFormat.PICKLE:
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

async def stop_manual_memory_profile(request: Request) -> Response:
    mem_profiler.stop()

    return Response(content="Memory profiling stopped")


def get_router(
    routes: Sequence[BaseRoute] | None = None,
    redirect_slashes: bool = True,
    *,
    middleware: Sequence[Middleware] | None = None,
) -> Router:
    router = Router(
        routes=routes,
        redirect_slashes=redirect_slashes,
        middleware=middleware,
    )

    router.add_route('/prof/mem/', profile_memory, methods=['GET'])
    router.add_route('/prof/mem/start/', start_manual_memory_profile, methods=['GET'])
    router.add_route('/prof/mem/snapshot/', snapshot_memory_manually, methods=['GET'])
    router.add_route('/prof/mem/stop/', stop_manual_memory_profile, methods=['GET'])

    return router
