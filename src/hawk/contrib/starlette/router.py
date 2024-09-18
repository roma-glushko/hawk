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
from starlette.routing import Router, BaseRoute, Middleware

import hawk.profiling.mem.tracemalloc as trmalloc
from hawk.contrib.starlette.response import format_response


async def profile_memory_tracemalloc(request: Request) -> Response:
    duration = int(request.query_params.get("duration", 5))
    frames = int(request.query_params.get("frames", 30))
    gc = request.query_params.get("gc", "true").lower() in ["true", "1"]
    count = int(request.query_params.get("count", 10))
    format = trmalloc.ProfileFormat(request.query_params.get("format", trmalloc.ProfileFormat.LINENO))
    cumulative = request.query_params.get("cumulative", "false").lower() in ["true", "1"]

    opt = trmalloc.ProfileOptions(frames=frames, gc=gc)

    with trmalloc.profiler.profile(opt) as profile:
        await asyncio.sleep(duration)

    render_opt = trmalloc.RendererOptions(count=count, cumulative=cumulative)
    renderer = trmalloc.get_renderer(format)

    rendered_profile = renderer.render(profile, render_opt)

    return format_response(rendered_profile)


async def start_manual_memory_tracemalloc_profile(request: Request) -> Response:
    frames = int(request.query_params.get("frames", 30))
    gc = request.query_params.get("gc", "true").lower() in ["true", "1"]

    opt = trmalloc.ProfileOptions(frames=frames, gc=gc)

    trmalloc.profiler.start(opt)

    return Response(content="Memory profiling started")


async def snapshot_memory_tracemalloc_manually(request: Request) -> Response:
    count = int(request.query_params.get("count", 10))
    format = trmalloc.ProfileFormat(request.query_params.get("format", trmalloc.ProfileFormat.LINENO))
    cumulative = request.query_params.get("cumulative", "false").lower() in ["true", "1"]

    profile = trmalloc.profiler.snapshot()

    opt = trmalloc.RendererOptions(count=count, cumulative=cumulative)
    renderer = trmalloc.get_renderer(format)

    profile_content = renderer.render(profile, opt)

    return format_response(profile_content)


async def stop_manual_memory_tracemalloc_profile(request: Request) -> Response:
    trmalloc.profiler.stop()

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

    router.add_route('/prof/mem/tracemalloc/', profile_memory_tracemalloc, methods=['GET'])
    router.add_route('/prof/mem/tracemalloc/start/', start_manual_memory_tracemalloc_profile, methods=['GET'])
    router.add_route('/prof/mem/tracemalloc/snapshot/', snapshot_memory_tracemalloc_manually, methods=['GET'])
    router.add_route('/prof/mem/tracemalloc/stop/', stop_manual_memory_tracemalloc_profile, methods=['GET'])

    return router
