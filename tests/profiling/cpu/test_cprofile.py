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
import cProfile

import pytest

from hawk.profiling.cpu import cprofile as cp
from hawk.profiling.cpu.cprofile import (
    ProfileOptions,
    ProfileFormat,
    SortKey,
    ProfileHandler,
    CProfileProfiler,
    get_renderer,
)
from hawk.profiling.renderers import MimeType, RenderMode
from hawk.profiling.exceptions import ProfilingAlreadyStarted, ProfilingNotStarted
from hawk.profiling.trace_context import TraceContext


def _do_some_work() -> int:
    """Helper function to do some CPU-bound work for profiling."""
    total = 0
    for i in range(50000):
        total += i
    return total


class TestProfileOptions:
    def test_default_options(self) -> None:
        opt = ProfileOptions()

        assert opt.sort_key == SortKey.CUMULATIVE
        assert opt.limit == 30

    def test_from_query_params_defaults(self) -> None:
        opt = ProfileOptions.from_query_params({})

        assert opt.sort_key == SortKey.CUMULATIVE
        assert opt.limit == 30

    def test_from_query_params_custom(self) -> None:
        opt = ProfileOptions.from_query_params({
            "sort": "time",
            "limit": "50",
        })

        assert opt.sort_key == SortKey.TIME
        assert opt.limit == 50

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("cumulative", SortKey.CUMULATIVE),
            ("time", SortKey.TIME),
            ("calls", SortKey.CALLS),
            ("name", SortKey.NAME),
        ],
    )
    def test_from_query_params_sort_key(self, value: str, expected: SortKey) -> None:
        opt = ProfileOptions.from_query_params({"sort": value})

        assert opt.sort_key == expected


class TestCProfileProfiler:
    def test_is_profiling_initially_false(self) -> None:
        profiler = CProfileProfiler()

        assert profiler.is_profiling is False

    def test_start_sets_is_profiling(self) -> None:
        profiler = CProfileProfiler()

        profiler.start()

        try:
            assert profiler.is_profiling is True
        finally:
            profiler.stop()

    def test_stop_clears_is_profiling(self) -> None:
        profiler = CProfileProfiler()

        profiler.start()
        profiler.stop()

        assert profiler.is_profiling is False

    def test_start_when_already_started_raises(self) -> None:
        profiler = CProfileProfiler()

        profiler.start()

        try:
            with pytest.raises(ProfilingAlreadyStarted):
                profiler.start()
        finally:
            profiler.stop()

    def test_stop_when_not_started_raises(self) -> None:
        profiler = CProfileProfiler()

        with pytest.raises(ProfilingNotStarted):
            profiler.stop()

    def test_profile_context_manager(self) -> None:
        profiler = CProfileProfiler()

        with profiler.profile() as p:
            assert profiler.is_profiling is True
            _do_some_work()

        assert profiler.is_profiling is False
        assert isinstance(p, cProfile.Profile)

    def test_stop_returns_profile(self) -> None:
        profiler = CProfileProfiler()

        profiler.start()
        _do_some_work()
        result = profiler.stop()

        assert isinstance(result, cProfile.Profile)


class TestRenderers:
    @pytest.fixture
    def profile_result(self) -> cProfile.Profile:
        profiler = CProfileProfiler()

        with profiler.profile() as p:
            _do_some_work()

        return p

    def test_text_renderer(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.TEXT)
        opt = ProfileOptions()
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert rendered.mime_type == MimeType.TEXT
        assert rendered.render_mode == RenderMode.VIEW
        assert rendered.file_name.endswith(".txt")
        assert rendered.file_name.startswith("hwk_cpu_cprofile_profile_")
        assert isinstance(rendered.content, str)
        assert len(rendered.content) > 0
        # Should contain typical cProfile output
        assert "ncalls" in rendered.content or "function calls" in rendered.content

    def test_pstat_renderer(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.PSTAT)
        opt = ProfileOptions()
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert rendered.mime_type == MimeType.BINARY
        assert rendered.render_mode == RenderMode.DOWNLOAD
        assert rendered.file_name.endswith(".pstat")
        assert rendered.file_name.startswith("hwk_cpu_cprofile_profile_")
        assert isinstance(rendered.content, bytes)
        assert len(rendered.content) > 0

    def test_json_renderer(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        opt = ProfileOptions()
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert rendered.mime_type == MimeType.JSON
        assert rendered.render_mode == RenderMode.VIEW
        assert rendered.file_name.endswith(".json")
        assert rendered.file_name.startswith("hwk_cpu_cprofile_profile_")
        assert isinstance(rendered.content, dict)
        assert "func_stats" in rendered.content
        assert "total_calls" in rendered.content
        assert "total_time" in rendered.content
        assert isinstance(rendered.content["func_stats"], list)

    def test_json_renderer_content_structure(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        opt = ProfileOptions()
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert isinstance(rendered.content, dict)
        func_stats = rendered.content["func_stats"]
        assert len(func_stats) > 0

        # Check func_stats structure
        for stat in func_stats:
            assert "filename" in stat
            assert "lineno" in stat
            assert "function" in stat
            assert "ncalls" in stat
            assert "totcalls" in stat
            assert "tottime" in stat
            assert "cumtime" in stat
            assert "percall_tottime" in stat
            assert "percall_cumtime" in stat

    def test_json_renderer_respects_limit(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        opt = ProfileOptions(limit=5)
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert isinstance(rendered.content, dict)
        func_stats = rendered.content["func_stats"]
        assert len(func_stats) <= 5

    def test_get_renderer_invalid_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid profile format"):
            get_renderer("invalid")  # type: ignore[arg-type]


class TestProfileHandler:
    def test_init_with_defaults(self) -> None:
        handler = ProfileHandler({})

        assert handler._format == ProfileFormat.TEXT
        assert handler._opt.sort_key == SortKey.CUMULATIVE
        assert handler._opt.limit == 30

    def test_init_with_custom_params(self) -> None:
        handler = ProfileHandler({
            "format": "json",
            "sort": "time",
            "limit": "50",
        })

        assert handler._format == ProfileFormat.JSON
        assert handler._opt.sort_key == SortKey.TIME
        assert handler._opt.limit == 50

    def test_profile_context_manager(self) -> None:
        handler = ProfileHandler({})

        with handler.profile():
            _do_some_work()

        assert handler._profiler is not None

    def test_render_profile_text(self) -> None:
        handler = ProfileHandler({"format": "text"})

        with handler.profile():
            _do_some_work()

        rendered = handler.render_profile()

        assert rendered.mime_type == MimeType.TEXT
        assert isinstance(rendered.content, str)

    def test_render_profile_pstat(self) -> None:
        handler = ProfileHandler({"format": "pstat"})

        with handler.profile():
            _do_some_work()

        rendered = handler.render_profile()

        assert rendered.mime_type == MimeType.BINARY
        assert isinstance(rendered.content, bytes)

    def test_render_profile_json(self) -> None:
        handler = ProfileHandler({"format": "json"})

        with handler.profile():
            _do_some_work()

        rendered = handler.render_profile()

        assert rendered.mime_type == MimeType.JSON
        assert isinstance(rendered.content, dict)
        assert "func_stats" in rendered.content

    def test_render_profile_without_profiling_raises(self) -> None:
        handler = ProfileHandler({})

        with pytest.raises(ProfilingNotStarted):
            handler.render_profile()


class TestProfilerRegistry:
    def test_cprofile_registered_in_profilers(self) -> None:
        from hawk.profiling.profilers import ProfilerType, PROFILERS, get_profiler

        assert ProfilerType.CPROFILE in ProfilerType
        assert ProfilerType.CPROFILE in PROFILERS
        assert get_profiler(ProfilerType.CPROFILE) == ProfileHandler


class TestGlobalProfilerInstance:
    def test_global_profiler_exists(self) -> None:
        assert cp.profiler is not None
        assert isinstance(cp.profiler, CProfileProfiler)

    def test_global_profiler_can_be_used(self) -> None:
        with cp.profiler.profile() as p:
            _do_some_work()

        assert isinstance(p, cProfile.Profile)


class TestTraceContext:
    @pytest.fixture
    def profile_result(self) -> cProfile.Profile:
        profiler = CProfileProfiler()

        with profiler.profile() as p:
            _do_some_work()

        return p

    def test_text_renderer_with_valid_trace_context(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.TEXT)
        opt = ProfileOptions()
        trace_ctx = TraceContext(trace_id="abc123", span_id="def456")

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert "_trace-abc123_span-def456" in rendered.file_name
        assert rendered.metadata == {"trace_id": "abc123", "span_id": "def456"}

    def test_pstat_renderer_with_valid_trace_context(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.PSTAT)
        opt = ProfileOptions()
        trace_ctx = TraceContext(trace_id="abc123", span_id="def456")

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert "_trace-abc123_span-def456" in rendered.file_name
        assert rendered.metadata == {"trace_id": "abc123", "span_id": "def456"}

    def test_json_renderer_with_valid_trace_context(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        opt = ProfileOptions()
        trace_ctx = TraceContext(trace_id="abc123", span_id="def456")

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert "_trace-abc123_span-def456" in rendered.file_name
        assert rendered.metadata == {"trace_id": "abc123", "span_id": "def456"}
        assert isinstance(rendered.content, dict)
        assert "trace_context" in rendered.content
        assert rendered.content["trace_context"] == {"trace_id": "abc123", "span_id": "def456"}

    def test_json_renderer_without_trace_context(self, profile_result: cProfile.Profile) -> None:
        renderer = get_renderer(ProfileFormat.JSON)
        opt = ProfileOptions()
        trace_ctx = TraceContext()  # Empty/invalid context

        rendered = renderer.render(profile_result, opt, trace_ctx)

        assert "_trace-" not in rendered.file_name
        assert rendered.metadata is None
        assert isinstance(rendered.content, dict)
        assert "trace_context" not in rendered.content

    def test_profile_handler_captures_trace_context(self) -> None:
        handler = ProfileHandler({"format": "json"})

        with handler.profile():
            _do_some_work()

        # Without OTel configured, trace context should be empty
        assert handler._trace_ctx is not None
        # Note: trace_ctx will be invalid (empty) without active OTel span
        rendered = handler.render_profile()
        assert rendered is not None
