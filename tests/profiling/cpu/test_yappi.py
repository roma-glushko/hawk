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
import pytest

from hawk.profiling.cpu import yappi as yp
from hawk.profiling.cpu.yappi import (
    ProfileOptions,
    ProfileFormat,
    ClockType,
    ProfileHandler,
    YappiProfiler,
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

        assert opt.clock_type == ClockType.CPU
        assert opt.builtins is False
        assert opt.multithreaded is True

    def test_from_query_params_defaults(self) -> None:
        opt = ProfileOptions.from_query_params({})

        assert opt.clock_type == ClockType.CPU
        assert opt.builtins is False
        assert opt.multithreaded is True

    def test_from_query_params_custom(self) -> None:
        opt = ProfileOptions.from_query_params({
            "clock_type": "wall",
            "builtins": "true",
            "multithreaded": "false",
        })

        assert opt.clock_type == ClockType.WALL
        assert opt.builtins is True
        assert opt.multithreaded is False

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
        ],
    )
    def test_from_query_params_boolean_parsing(self, value: str, expected: bool) -> None:
        opt = ProfileOptions.from_query_params({"builtins": value})

        assert opt.builtins is expected


class TestYappiProfiler:
    def test_is_profiling_initially_false(self) -> None:
        profiler = YappiProfiler()

        assert profiler.is_profiling is False

    def test_start_sets_is_profiling(self) -> None:
        profiler = YappiProfiler()
        opt = ProfileOptions()

        profiler.start(opt)

        try:
            assert profiler.is_profiling is True
        finally:
            profiler.stop()

    def test_stop_clears_is_profiling(self) -> None:
        profiler = YappiProfiler()
        opt = ProfileOptions()

        profiler.start(opt)
        profiler.stop()

        assert profiler.is_profiling is False

    def test_start_when_already_started_raises(self) -> None:
        profiler = YappiProfiler()
        opt = ProfileOptions()

        profiler.start(opt)

        try:
            with pytest.raises(ProfilingAlreadyStarted):
                profiler.start(opt)
        finally:
            profiler.stop()

    def test_stop_when_not_started_raises(self) -> None:
        profiler = YappiProfiler()

        with pytest.raises(ProfilingNotStarted):
            profiler.stop()

    def test_profile_context_manager(self) -> None:
        profiler = YappiProfiler()
        opt = ProfileOptions()

        with profiler.profile(opt) as result:
            assert profiler.is_profiling is True
            _do_some_work()

        assert profiler.is_profiling is False
        assert result.func_stats is not None
        assert result.thread_stats is not None

    def test_profile_context_manager_with_wall_clock(self) -> None:
        profiler = YappiProfiler()
        opt = ProfileOptions(clock_type=ClockType.WALL)

        with profiler.profile(opt) as result:
            _do_some_work()

        assert result.func_stats is not None
        assert len(result.func_stats) > 0

    def test_profile_context_manager_with_builtins(self) -> None:
        profiler = YappiProfiler()
        opt = ProfileOptions(builtins=True)

        with profiler.profile(opt) as result:
            _do_some_work()

        assert result.func_stats is not None

    def test_stop_returns_profile_result(self) -> None:
        profiler = YappiProfiler()
        opt = ProfileOptions()

        profiler.start(opt)
        _do_some_work()
        result = profiler.stop()

        assert result.func_stats is not None
        assert result.thread_stats is not None


class TestRenderers:
    @pytest.fixture
    def profile_result(self) -> yp.ProfileResult:
        profiler = YappiProfiler()
        opt = ProfileOptions()

        with profiler.profile(opt) as result:
            _do_some_work()

        return result

    def test_pstat_renderer(self, profile_result: yp.ProfileResult) -> None:
        renderer = get_renderer(ProfileFormat.PSTAT)
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, trace_ctx)

        assert rendered.mime_type == MimeType.BINARY
        assert rendered.render_mode == RenderMode.DOWNLOAD
        assert rendered.file_name.endswith(".pstat")
        assert rendered.file_name.startswith("hwk_cpu_yappi_profile_")
        assert isinstance(rendered.content, bytes)
        assert len(rendered.content) > 0

    def test_callgrind_renderer(self, profile_result: yp.ProfileResult) -> None:
        renderer = get_renderer(ProfileFormat.CALLGRIND)
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, trace_ctx)

        assert rendered.mime_type == MimeType.BINARY
        assert rendered.render_mode == RenderMode.DOWNLOAD
        assert rendered.file_name.endswith(".callgrind")
        assert rendered.file_name.startswith("hwk_cpu_yappi_profile_")
        assert isinstance(rendered.content, bytes)
        assert len(rendered.content) > 0

    def test_funcstats_renderer(self, profile_result: yp.ProfileResult) -> None:
        renderer = get_renderer(ProfileFormat.FUNC_STATS)
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, trace_ctx)

        assert rendered.mime_type == MimeType.JSON
        assert rendered.render_mode == RenderMode.VIEW
        assert rendered.file_name.endswith(".json")
        assert rendered.file_name.startswith("hwk_cpu_yappi_profile_")
        assert isinstance(rendered.content, dict)
        assert "func_stats" in rendered.content
        assert "thread_stats" in rendered.content
        assert isinstance(rendered.content["func_stats"], list)
        assert isinstance(rendered.content["thread_stats"], list)

    def test_funcstats_renderer_content_structure(self, profile_result: yp.ProfileResult) -> None:
        renderer = get_renderer(ProfileFormat.FUNC_STATS)
        trace_ctx = TraceContext()

        rendered = renderer.render(profile_result, trace_ctx)

        assert isinstance(rendered.content, dict)
        func_stats = rendered.content["func_stats"]
        assert len(func_stats) > 0

        # Check func_stats structure
        for stat in func_stats:
            assert "name" in stat
            assert "module" in stat
            assert "lineno" in stat
            assert "ncall" in stat
            assert "nactualcall" in stat
            assert "builtin" in stat
            assert "ttot" in stat
            assert "tsub" in stat
            assert "tavg" in stat

        thread_stats = rendered.content["thread_stats"]
        assert len(thread_stats) > 0

        # Check thread_stats structure
        for stat in thread_stats:
            assert "name" in stat
            assert "id" in stat
            assert "tid" in stat
            assert "ttot" in stat
            assert "sched_count" in stat

    def test_get_renderer_invalid_format(self) -> None:
        with pytest.raises(ValueError, match="Invalid profile format"):
            get_renderer("invalid")  # type: ignore[arg-type]


class TestProfileHandler:
    def test_init_with_defaults(self) -> None:
        handler = ProfileHandler({})

        assert handler._format == ProfileFormat.FUNC_STATS
        assert handler._opt.clock_type == ClockType.CPU
        assert handler._opt.builtins is False
        assert handler._opt.multithreaded is True

    def test_init_with_custom_params(self) -> None:
        handler = ProfileHandler({
            "format": "pstat",
            "clock_type": "wall",
            "builtins": "true",
            "multithreaded": "false",
        })

        assert handler._format == ProfileFormat.PSTAT
        assert handler._opt.clock_type == ClockType.WALL
        assert handler._opt.builtins is True
        assert handler._opt.multithreaded is False

    def test_profile_context_manager(self) -> None:
        handler = ProfileHandler({})

        with handler.profile():
            _do_some_work()

        assert handler._result is not None
        assert handler._result.func_stats is not None

    def test_render_profile_funcstats(self) -> None:
        handler = ProfileHandler({"format": "funcstats"})

        with handler.profile():
            _do_some_work()

        rendered = handler.render_profile()

        assert rendered.mime_type == MimeType.JSON
        assert isinstance(rendered.content, dict)
        assert "func_stats" in rendered.content

    def test_render_profile_pstat(self) -> None:
        handler = ProfileHandler({"format": "pstat"})

        with handler.profile():
            _do_some_work()

        rendered = handler.render_profile()

        assert rendered.mime_type == MimeType.BINARY
        assert isinstance(rendered.content, bytes)

    def test_render_profile_callgrind(self) -> None:
        handler = ProfileHandler({"format": "callgrind"})

        with handler.profile():
            _do_some_work()

        rendered = handler.render_profile()

        assert rendered.mime_type == MimeType.BINARY
        assert isinstance(rendered.content, bytes)

    def test_render_profile_without_profiling_raises(self) -> None:
        handler = ProfileHandler({})

        with pytest.raises(ProfilingNotStarted):
            handler.render_profile()


class TestProfilerRegistry:
    def test_yappi_registered_in_profilers(self) -> None:
        from hawk.profiling.profilers import ProfilerType, PROFILERS, get_profiler

        assert ProfilerType.YAPPI in ProfilerType
        assert ProfilerType.YAPPI in PROFILERS
        assert get_profiler(ProfilerType.YAPPI) == ProfileHandler


class TestGlobalProfilerInstance:
    def test_global_profiler_exists(self) -> None:
        assert yp.profiler is not None
        assert isinstance(yp.profiler, YappiProfiler)

    def test_global_profiler_can_be_used(self) -> None:
        opt = ProfileOptions()

        with yp.profiler.profile(opt) as result:
            _do_some_work()

        assert result.func_stats is not None
