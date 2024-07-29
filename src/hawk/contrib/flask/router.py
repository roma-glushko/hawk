from __future__ import annotations

import time

from flask import Blueprint, request, Response

from src.hawk.profiling.memory import FormatType, profiler as mem_profiler


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
        format = FormatType(request.args.get("format", FormatType.LINENO))
        cumulative = request.args.get("cumulative", "false").lower() in ("true", "1")

        mem_profiler.start(frames=frames)

        try:
            heap_usage1, snapshot1 = mem_profiler.snapshot()
            time.sleep(duration)
            heap_usage2, snapshot2 = mem_profiler.snapshot()
        finally:
            mem_profiler.stop()

        renderer = mem_profiler.get_renderer(format)

        if format == FormatType.PICKLE:
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
        format = FormatType(request.args.get("format", FormatType.LINENO))
        cumulative = request.args.get("cumulative", "false").lower() in ["true", "1"]

        heap_usage, snapshot = mem_profiler.snapshot()

        renderer = mem_profiler.get_renderer(format)

        if format == FormatType.PICKLE:
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
