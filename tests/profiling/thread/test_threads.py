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
import threading
import time

import pytest

from hawk.profiling.thread.threads import (
    ProfileOptions,
    ProfileFormat,
    ProfileHandler,
    ThreadSnapshot,
    take_snapshot,
    get_renderer,
)
from hawk.profiling.renderers import MimeType, RenderMode
from hawk.profiling.trace_context import TraceContext


class TestProfileOptions:
    def test_default_options(self) -> None:
        opt = ProfileOptions()

        assert opt.max_depth == 128

    def test_from_query_params_defaults(self) -> None:
        opt = ProfileOptions.from_query_params({})

        assert opt.max_depth == 128

    def test_from_query_params_custom(self) -> None:
        opt = ProfileOptions.from_query_params({
            "max_depth": "64",
        })

        assert opt.max_depth == 64

    def test_invalid_max_depth_raises(self) -> None:
        with pytest.raises(ValueError, match="max_depth should be greater than 0"):
            ProfileOptions(max_depth=0)

    def test_negative_max_depth_raises(self) -> None:
        with pytest.raises(ValueError, match="max_depth should be greater than 0"):
            ProfileOptions(max_depth=-1)


class TestTakeSnapshot:
    def test_snapshot_captures_main_thread(self) -> None:
        snapshot = take_snapshot()

        assert snapshot.thread_count >= 1
        assert len(snapshot.threads) >= 1

        # Find main thread
        main_thread = next(
            (t for t in snapshot.threads if t.name == "MainThread"),
            None,
        )
        assert main_thread is not None
        assert main_thread.daemon is False

    def test_snapshot_captures_thread_stacks(self) -> None:
        snapshot = take_snapshot()

        for thread in snapshot.threads:
            assert isinstance(thread.thread_id, int)
            assert isinstance(thread.stack, list)
            assert len(thread.stack) > 0

            for frame in thread.stack:
                assert isinstance(frame.function, str)
                assert isinstance(frame.filename, str)
                assert isinstance(frame.lineno, int)

    def test_snapshot_captures_spawned_threads(self) -> None:
        def worker():
            time.sleep(0.5)

        thread = threading.Thread(target=worker, name="TestWorker", daemon=True)
        thread.start()

        try:
            # Give thread time to start
            time.sleep(0.1)
            snapshot = take_snapshot()

            worker_thread = next(
                (t for t in snapshot.threads if t.name == "TestWorker"),
                None,
            )
            assert worker_thread is not None
            assert worker_thread.daemon is True
        finally:
            thread.join(timeout=1)

    def test_snapshot_respects_max_depth(self) -> None:
        opt = ProfileOptions(max_depth=3)
        snapshot = take_snapshot(opt)

        for thread in snapshot.threads:
            assert len(thread.stack) <= 3

    def test_snapshot_with_default_options(self) -> None:
        snapshot = take_snapshot()

        assert isinstance(snapshot, ThreadSnapshot)
        assert snapshot.thread_count == len(snapshot.threads)


class TestJSONRenderer:
    @pytest.fixture
    def snapshot(self) -> ThreadSnapshot:
        return take_snapshot()

    def test_json_renderer(self, snapshot: ThreadSnapshot) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        trace_ctx = TraceContext()

        rendered = renderer.render(snapshot, trace_ctx)

        assert rendered.mime_type == MimeType.JSON
        assert rendered.render_mode == RenderMode.VIEW
        assert rendered.file_name.endswith(".json")
        assert rendered.file_name.startswith("hwk_threads_snapshot_")
        assert isinstance(rendered.content, dict)

    def test_json_renderer_content_structure(self, snapshot: ThreadSnapshot) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        trace_ctx = TraceContext()

        rendered = renderer.render(snapshot, trace_ctx)

        assert isinstance(rendered.content, dict)
        assert "thread_count" in rendered.content
        assert "threads" in rendered.content
        assert isinstance(rendered.content["threads"], list)
        assert rendered.content["thread_count"] == len(rendered.content["threads"])

    def test_json_renderer_thread_structure(self, snapshot: ThreadSnapshot) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        trace_ctx = TraceContext()

        rendered = renderer.render(snapshot, trace_ctx)

        assert isinstance(rendered.content, dict)
        threads = rendered.content["threads"]
        assert len(threads) > 0

        for thread in threads:
            assert "thread_id" in thread
            assert "name" in thread
            assert "daemon" in thread
            assert "stack" in thread
            assert isinstance(thread["stack"], list)

            for frame in thread["stack"]:
                assert "function" in frame
                assert "filename" in frame
                assert "lineno" in frame

    def test_get_renderer_invalid_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid profile format"):
            get_renderer("invalid")  # type: ignore[arg-type]


class TestProfileHandler:
    def test_init_with_defaults(self) -> None:
        handler = ProfileHandler({})

        assert handler._format == ProfileFormat.JSON
        assert handler._opt.max_depth == 128

    def test_init_with_custom_params(self) -> None:
        handler = ProfileHandler({
            "format": "json",
            "max_depth": "64",
        })

        assert handler._format == ProfileFormat.JSON
        assert handler._opt.max_depth == 64

    def test_profile_context_manager(self) -> None:
        handler = ProfileHandler({})

        with handler.profile():
            pass

        assert handler._snapshot is not None

    def test_render_profile_json(self) -> None:
        handler = ProfileHandler({"format": "json"})

        with handler.profile():
            pass

        rendered = handler.render_profile()

        assert rendered.mime_type == MimeType.JSON
        assert isinstance(rendered.content, dict)
        assert "thread_count" in rendered.content
        assert "threads" in rendered.content

    def test_render_profile_without_profiling_raises(self) -> None:
        handler = ProfileHandler({})

        with pytest.raises(RuntimeError, match="Snapshot not taken"):
            handler.render_profile()


class TestProfilerRegistry:
    def test_threads_registered_in_profilers(self) -> None:
        from hawk.profiling.profilers import ProfilerType, PROFILERS, get_profiler

        assert ProfilerType.THREADS in ProfilerType
        assert ProfilerType.THREADS in PROFILERS
        assert get_profiler(ProfilerType.THREADS) == ProfileHandler


class TestTraceContext:
    @pytest.fixture
    def snapshot(self) -> ThreadSnapshot:
        return take_snapshot()

    def test_json_renderer_with_valid_trace_context(self, snapshot: ThreadSnapshot) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        trace_ctx = TraceContext(trace_id="abc123", span_id="def456")

        rendered = renderer.render(snapshot, trace_ctx)

        assert "_trace-abc123_span-def456" in rendered.file_name
        assert rendered.metadata == {"trace_id": "abc123", "span_id": "def456"}
        assert isinstance(rendered.content, dict)
        assert "trace_context" in rendered.content
        assert rendered.content["trace_context"] == {"trace_id": "abc123", "span_id": "def456"}

    def test_json_renderer_without_trace_context(self, snapshot: ThreadSnapshot) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        trace_ctx = TraceContext()  # Empty/invalid context

        rendered = renderer.render(snapshot, trace_ctx)

        assert "_trace-" not in rendered.file_name
        assert rendered.metadata is None
        assert isinstance(rendered.content, dict)
        assert "trace_context" not in rendered.content

    def test_profile_handler_captures_trace_context(self) -> None:
        handler = ProfileHandler({"format": "json"})

        with handler.profile():
            pass

        # Without OTel configured, trace context should be empty
        assert handler._trace_ctx is not None
        rendered = handler.render_profile()
        assert rendered is not None
