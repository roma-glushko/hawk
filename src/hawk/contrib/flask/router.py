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

import time

from hawk import zpages
from hawk.expvars.zpage import register_expvars_zpage
import hawk.profiling.mem.tracemalloc as trmalloc
import hawk.profiling.cpu.pyinstrument as pyinstr
import hawk.profiling.cpu.yappi as yp
from hawk.contrib.flask.response import format_response
from hawk.zpages import ZPageFormat

try:
    from flask import Blueprint, request, Response, jsonify
except ImportError as e:
    raise ImportError(
        "Flask is required to use the hawk.contrib.flask packages. "
        "Please install it using 'pip install flask'."
    ) from e


def get_blueprint(
    prefix: str = "/debug",
    register_expvars: bool = True,
) -> Blueprint:
    """
    Create a new Flask Blueprint with all debugging endpoints.

    Parameters
    ----------
    prefix : str
        URL prefix for all debug endpoints (default: "/debug").
    register_expvars : bool
        Whether to register the expvars ZPage at /debug/vars/ (default: True).
    """
    if register_expvars:
        register_expvars_zpage()

    bp = Blueprint(
        "hawk_debug",
        __name__,
        url_prefix=prefix,
    )

    # Memory profiler routes (tracemalloc)
    @bp.route('/prof/mem/tracemalloc/', methods=['GET'])
    def profile_memory_tracemalloc():
        duration = int(request.args.get("duration", 5))
        frames = int(request.args.get("frames", 30))
        gc = request.args.get("gc", "true").lower() in ["true", "1"]
        count = int(request.args.get("count", 10))
        format = trmalloc.ProfileFormat(request.args.get("format", trmalloc.ProfileFormat.LINENO))
        cumulative = request.args.get("cumulative", "false").lower() in ["true", "1"]

        opt = trmalloc.ProfileOptions(frames=frames, gc=gc)

        with trmalloc.profiler.profile(opt) as profile:
            time.sleep(duration)

        render_opt = trmalloc.RendererOptions(count=count, cumulative=cumulative)
        renderer = trmalloc.get_renderer(format)

        rendered_profile = renderer.render(profile, render_opt)

        return format_response(rendered_profile)

    @bp.route('/prof/mem/tracemalloc/start/', methods=['GET'])
    def start_manual_memory_tracemalloc_profile():
        frames = int(request.args.get("frames", 30))
        gc = request.args.get("gc", "true").lower() in ["true", "1"]

        opt = trmalloc.ProfileOptions(frames=frames, gc=gc)

        trmalloc.profiler.start(opt)

        return Response("Memory profiling started", content_type='text/plain')

    @bp.route('/prof/mem/tracemalloc/snapshot/', methods=['GET'])
    def snapshot_memory_tracemalloc_manually():
        count = int(request.args.get("count", 10))
        format = trmalloc.ProfileFormat(request.args.get("format", trmalloc.ProfileFormat.LINENO))
        cumulative = request.args.get("cumulative", "false").lower() in ["true", "1"]

        profile = trmalloc.profiler.snapshot()

        opt = trmalloc.RendererOptions(count=count, cumulative=cumulative)
        renderer = trmalloc.get_renderer(format)

        rendered_profile = renderer.render(profile, opt)

        return format_response(rendered_profile)

    @bp.route('/prof/mem/tracemalloc/stop/', methods=['GET'])
    def stop_manual_memory_tracemalloc_profile():
        trmalloc.profiler.stop()

        return Response("Memory profiling stopped", content_type='text/plain')

    # CPU profiler routes (pyinstrument) - only if available
    if pyinstr.pyinstrument is not None:
        @bp.route('/prof/cpu/pyinstrument/', methods=['GET'])
        def profile_cpu_pyinstrument():
            duration = int(request.args.get("duration", 5))
            interval = float(request.args.get("interval", 0.001))
            async_mode = pyinstr.AsyncModes(request.args.get("async_mode", pyinstr.AsyncModes.ENABLED.value))
            use_timing_thread_param = request.args.get("use_timing_thread")
            use_timing_thread = None if use_timing_thread_param is None else use_timing_thread_param.lower() in ["true", "1"]
            format = pyinstr.ProfileFormat(request.args.get("format", pyinstr.ProfileFormat.HTML.value))

            opt = pyinstr.ProfileOptions(
                interval=interval,
                use_timing_thread=use_timing_thread,
                async_mode=async_mode,
            )

            with pyinstr.profiler.profile(opt) as profiler:
                time.sleep(duration)

            renderer = pyinstr.get_renderer(format)
            profile = renderer.render(profiler)

            return format_response(profile)

        @bp.route('/prof/cpu/pyinstrument/start/', methods=['GET'])
        def start_manual_cpu_pyinstrument_profile():
            interval = float(request.args.get("interval", 0.001))
            async_mode = pyinstr.AsyncModes(request.args.get("async_mode", pyinstr.AsyncModes.ENABLED.value))
            use_timing_thread_param = request.args.get("use_timing_thread")
            use_timing_thread = None if use_timing_thread_param is None else use_timing_thread_param.lower() in ["true", "1"]

            opt = pyinstr.ProfileOptions(
                interval=interval,
                use_timing_thread=use_timing_thread,
                async_mode=async_mode,
            )

            pyinstr.profiler.start(opt)

            return Response("Pyinstrument CPU profiling started", content_type='text/plain')

        @bp.route('/prof/cpu/pyinstrument/stop/', methods=['GET'])
        def stop_manual_cpu_pyinstrument_profile():
            format = pyinstr.ProfileFormat(request.args.get("format", pyinstr.ProfileFormat.HTML.value))

            profiler = pyinstr.profiler.stop()

            renderer = pyinstr.get_renderer(format)
            profile = renderer.render(profiler)

            return format_response(profile)

    # CPU profiler routes (yappi) - only if available
    if yp.yappi is not None:
        @bp.route('/prof/cpu/yappi/', methods=['GET'])
        def profile_cpu_yappi():
            duration = int(request.args.get("duration", 5))
            clock_type = yp.ClockType(request.args.get("clock_type", yp.ClockType.CPU.value))
            builtins = request.args.get("builtins", "false").lower() in ["true", "1"]
            multithreaded = request.args.get("multithreaded", "true").lower() in ["true", "1"]
            format = yp.ProfileFormat(request.args.get("format", yp.ProfileFormat.FUNC_STATS.value))

            opt = yp.ProfileOptions(
                clock_type=clock_type,
                builtins=builtins,
                multithreaded=multithreaded,
            )

            with yp.profiler.profile(opt) as result:
                time.sleep(duration)

            renderer = yp.get_renderer(format)
            profile = renderer.render(result)

            return format_response(profile)

        @bp.route('/prof/cpu/yappi/start/', methods=['GET'])
        def start_manual_cpu_yappi_profile():
            clock_type = yp.ClockType(request.args.get("clock_type", yp.ClockType.CPU.value))
            builtins = request.args.get("builtins", "false").lower() in ["true", "1"]
            multithreaded = request.args.get("multithreaded", "true").lower() in ["true", "1"]

            opt = yp.ProfileOptions(
                clock_type=clock_type,
                builtins=builtins,
                multithreaded=multithreaded,
            )

            yp.profiler.start(opt)

            return Response("Yappi CPU profiling started", content_type='text/plain')

        @bp.route('/prof/cpu/yappi/stop/', methods=['GET'])
        def stop_manual_cpu_yappi_profile():
            format = yp.ProfileFormat(request.args.get("format", yp.ProfileFormat.FUNC_STATS.value))

            result = yp.profiler.stop()

            renderer = yp.get_renderer(format)
            profile = renderer.render(result)

            return format_response(profile)

    # ZPages route - catch-all for dynamic page routes
    @bp.route('/<path:page_route>/', methods=['GET'])
    @bp.route('/', methods=['GET'], defaults={'page_route': ''})
    def get_zpage(page_route: str):
        format_param = request.args.get("format", ZPageFormat.HTML.value)
        format = ZPageFormat(format_param)
        refresh_param = request.args.get("refresh")
        refresh = int(refresh_param) if refresh_param else None

        # Handle empty route - show available pages
        if not page_route:
            available_routes = zpages.get_page_routes()
            if format == ZPageFormat.JSON:
                return jsonify({"available_pages": available_routes})
            return Response(
                f"Available ZPages: {available_routes}",
                content_type='text/plain',
            )

        try:
            zpage = zpages.get_page(page_route)
        except zpages.ZPageNotFound:
            return Response(
                f"ZPage not found (available pages: {zpages.get_page_routes()})",
                status=404,
                content_type='text/plain',
            )

        zpage.auto_refresh = refresh

        content = zpage.render(format)

        if format == ZPageFormat.JSON:
            return jsonify(content)

        # HTML rendering
        return Response(content, content_type='text/html')

    return bp
