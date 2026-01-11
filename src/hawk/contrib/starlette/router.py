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

import asyncio
from typing import Sequence

from hawk import zpages
from hawk.expvars.zpage import register_expvars_zpage
import hawk.profiling.mem.tracemalloc as trmalloc
import hawk.profiling.cpu.pyinstrument as pyinstr
import hawk.profiling.cpu.yappi as yp
import hawk.profiling.thread.threads as th
from hawk.contrib.starlette.response import format_response
from hawk.zpages import ZPageFormat

try:
    from starlette.requests import Request
    from starlette.responses import Response, HTMLResponse, JSONResponse
    from starlette.routing import Router, BaseRoute, Middleware
except ImportError as e:
    raise ImportError(
        "Starlette is required to use the hawk.contrib.starlette packages. "
        "Please install it using 'pip install starlette'."
    ) from e


async def profile_memory_tracemalloc(request: Request) -> Response:
    query_params = request.query_params
    duration = int(query_params.get("duration", 5))
    opt = trmalloc.ProfileOptions.from_query_params(query_params)
    render_opt = trmalloc.RendererOptions.from_query_params(query_params)
    format = trmalloc.ProfileFormat(query_params.get("format", trmalloc.ProfileFormat.LINENO))

    with trmalloc.profiler.profile(opt) as profile:
        await asyncio.sleep(duration)

    renderer = trmalloc.get_renderer(format)
    rendered_profile = renderer.render(profile, render_opt)

    return format_response(rendered_profile)


async def start_manual_memory_tracemalloc_profile(request: Request) -> Response:
    opt = trmalloc.ProfileOptions.from_query_params(request.query_params)

    trmalloc.profiler.start(opt)

    return Response(content="Memory profiling started")


async def snapshot_memory_tracemalloc_manually(request: Request) -> Response:
    query_params = request.query_params
    render_opt = trmalloc.RendererOptions.from_query_params(query_params)
    format = trmalloc.ProfileFormat(query_params.get("format", trmalloc.ProfileFormat.LINENO))

    profile = trmalloc.profiler.snapshot()

    renderer = trmalloc.get_renderer(format)
    profile_content = renderer.render(profile, render_opt)

    return format_response(profile_content)


async def stop_manual_memory_tracemalloc_profile(request: Request) -> Response:
    trmalloc.profiler.stop()

    return Response(content="Memory profiling stopped")


# Pyinstrument CPU profiler endpoints
async def profile_cpu_pyinstrument(request: Request) -> Response:
    query_params = request.query_params
    duration = int(query_params.get("duration", 5))
    opt = pyinstr.ProfileOptions.from_query_params(query_params)
    format = pyinstr.ProfileFormat(query_params.get("format", pyinstr.ProfileFormat.HTML.value))

    with pyinstr.profiler.profile(opt) as profiler:
        await asyncio.sleep(duration)

    renderer = pyinstr.get_renderer(format)
    profile = renderer.render(profiler)

    return format_response(profile)


async def start_manual_cpu_pyinstrument_profile(request: Request) -> Response:
    opt = pyinstr.ProfileOptions.from_query_params(request.query_params)

    pyinstr.profiler.start(opt)

    return Response(content="Pyinstrument CPU profiling started")


async def stop_manual_cpu_pyinstrument_profile(request: Request) -> Response:
    format = pyinstr.ProfileFormat(request.query_params.get("format", pyinstr.ProfileFormat.HTML.value))

    profiler = pyinstr.profiler.stop()

    renderer = pyinstr.get_renderer(format)
    profile = renderer.render(profiler)

    return format_response(profile)


# Yappi CPU profiler endpoints
async def profile_cpu_yappi(request: Request) -> Response:
    query_params = request.query_params
    duration = int(query_params.get("duration", 5))
    opt = yp.ProfileOptions.from_query_params(query_params)
    format = yp.ProfileFormat(query_params.get("format", yp.ProfileFormat.FUNC_STATS.value))

    with yp.profiler.profile(opt) as result:
        await asyncio.sleep(duration)

    renderer = yp.get_renderer(format)
    profile = renderer.render(result)

    return format_response(profile)


async def start_manual_cpu_yappi_profile(request: Request) -> Response:
    opt = yp.ProfileOptions.from_query_params(request.query_params)

    yp.profiler.start(opt)

    return Response(content="Yappi CPU profiling started")


async def stop_manual_cpu_yappi_profile(request: Request) -> Response:
    format = yp.ProfileFormat(request.query_params.get("format", yp.ProfileFormat.FUNC_STATS.value))

    result = yp.profiler.stop()

    renderer = yp.get_renderer(format)
    profile = renderer.render(result)

    return format_response(profile)


# Thread profiler endpoint (snapshot-based)
async def snapshot_threads(request: Request) -> Response:
    query_params = request.query_params
    opt = th.ProfileOptions.from_query_params(query_params)
    format = th.ProfileFormat(query_params.get("format", th.ProfileFormat.JSON.value))

    snapshot = th.take_snapshot(opt)

    renderer = th.get_renderer(format)
    rendered_profile = renderer.render(snapshot)

    return format_response(rendered_profile)


# ZPages endpoint
async def get_zpage(request: Request) -> Response:
    page_route = request.path_params.get("page_route", "")
    format_param = request.query_params.get("format", ZPageFormat.HTML.value)
    format = ZPageFormat(format_param)
    refresh_param = request.query_params.get("refresh")
    refresh = int(refresh_param) if refresh_param else None

    try:
        zpage = zpages.get_page(page_route)
    except zpages.ZPageNotFound:
        return Response(
            status_code=404,
            content=f"ZPage not found (available pages: {zpages.get_page_routes()})",
        )

    zpage.auto_refresh = refresh

    content = zpage.render(format)

    if format == ZPageFormat.JSON:
        return JSONResponse(content=content)

    # HTML rendering
    return HTMLResponse(content=content)


def get_router(
    routes: Sequence[BaseRoute] | None = None,
    redirect_slashes: bool = True,
    *,
    middleware: Sequence[Middleware] | None = None,
    register_expvars: bool = True,
) -> Router:
    """
    Create a new Starlette router with all debugging endpoints.

    Parameters
    ----------
    routes : Sequence[BaseRoute] | None
        Additional routes to include in the router.
    redirect_slashes : bool
        Whether to redirect trailing slashes (default: True).
    middleware : Sequence[Middleware] | None
        Middleware to apply to the router.
    register_expvars : bool
        Whether to register the expvars ZPage at /debug/vars/ (default: True).
    """
    if register_expvars:
        register_expvars_zpage()

    router = Router(
        routes=routes,
        redirect_slashes=redirect_slashes,
        middleware=middleware,
    )

    # Memory profiler routes (tracemalloc)
    router.add_route('/prof/mem/tracemalloc/', profile_memory_tracemalloc, methods=['GET'])
    router.add_route('/prof/mem/tracemalloc/start/', start_manual_memory_tracemalloc_profile, methods=['GET'])
    router.add_route('/prof/mem/tracemalloc/snapshot/', snapshot_memory_tracemalloc_manually, methods=['GET'])
    router.add_route('/prof/mem/tracemalloc/stop/', stop_manual_memory_tracemalloc_profile, methods=['GET'])

    # CPU profiler routes (pyinstrument) - only if available
    if pyinstr.pyinstrument is not None:
        router.add_route('/prof/cpu/pyinstrument/', profile_cpu_pyinstrument, methods=['GET'])
        router.add_route('/prof/cpu/pyinstrument/start/', start_manual_cpu_pyinstrument_profile, methods=['GET'])
        router.add_route('/prof/cpu/pyinstrument/stop/', stop_manual_cpu_pyinstrument_profile, methods=['GET'])

    # CPU profiler routes (yappi) - only if available
    if yp.yappi is not None:
        router.add_route('/prof/cpu/yappi/', profile_cpu_yappi, methods=['GET'])
        router.add_route('/prof/cpu/yappi/start/', start_manual_cpu_yappi_profile, methods=['GET'])
        router.add_route('/prof/cpu/yappi/stop/', stop_manual_cpu_yappi_profile, methods=['GET'])

    # Thread profiler route (snapshot-based)
    router.add_route('/prof/threads/', snapshot_threads, methods=['GET'])

    # ZPages route - catch-all for dynamic page routes
    router.add_route('/{page_route:path}/', get_zpage, methods=['GET'])

    return router
