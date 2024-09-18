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

import time

from flask import Blueprint, request, Response

from hawk.profiling.mem.tracemalloc import ProfileFormat, profiler as mem_profiler


def create_debug_blueprint(
    prefix: str = "/debug",
) -> Blueprint:
    """
    Create a new Flask Blueprint with all debugging endpoints
    """
    bp = Blueprint(
        "hawk_debug",
        __name__,
        url_prefix=prefix,
    )

    @bp.route('/prof/mem/', methods=['GET'])
    def profile_memory():
        duration = int(request.args.get("duration", 5))
        frames = int(request.args.get("frames", 30))
        count = int(request.args.get("count", 10))
        format = ProfileFormat(request.args.get("format", ProfileFormat.LINENO))
        cumulative = request.args.get("cumulative", "false").lower() in ("true", "1")

        mem_profiler.start(frames=frames)

        try:
            heap_usage1, snapshot1 = mem_profiler.snapshot()
            time.sleep(duration)
            heap_usage2, snapshot2 = mem_profiler.snapshot()
        finally:
            mem_profiler.stop()

        renderer = mem_profiler.get_renderer(format)

        if format == ProfileFormat.PICKLE:
            return Response(
                renderer.render(snapshot2),
                headers=renderer.headers(),
                content_type='application/octet-stream'
            )

        return Response(
            renderer.render(
                snapshot2,
                heap_usage2,
                snapshot1,
                heap_usage1,
                count,
                cumulative
            ),
            headers=renderer.headers(),
        )

    @bp.route('/prof/mem/start/', methods=['GET'])
    def start_manual_memory_profile():
        frames = int(request.args.get("frames", 30))

        mem_profiler.start(frames=frames)

        return Response("Memory profiling started", content_type='text/plain')

    @bp.route('/prof/mem/snapshot/', methods=['GET'])
    def snapshot_memory_manually():
        count = int(request.args.get("count", 10))
        format = ProfileFormat(request.args.get("format", ProfileFormat.LINENO))
        cumulative = request.args.get("cumulative", "false").lower() in ["true", "1"]

        heap_usage, snapshot = mem_profiler.snapshot()

        renderer = mem_profiler.get_renderer(format)

        if format == ProfileFormat.PICKLE:
            return Response(
                renderer.render(snapshot),
                headers=renderer.headers(),
                content_type='application/octet-stream'
            )

        return Response(
            renderer.render(
                snapshot,
                heap_usage,
                count,
                cumulative
            ),
            headers=renderer.headers(),
        )

    @bp.route('/prof/mem/stop/', methods=['GET'])
    def stop_manual_memory_profile():
        mem_profiler.stop()

        return Response("Memory profiling stopped", content_type='text/plain')

    return bp
