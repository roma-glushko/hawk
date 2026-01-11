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

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator

try:
    from opentelemetry import trace  # type: ignore[import-not-found]
    from opentelemetry.trace import INVALID_SPAN_ID, INVALID_TRACE_ID, Span, Tracer  # type: ignore[import-not-found]
    _otel_available = True
except ImportError:
    _otel_available = False
    Span = None  # type: ignore[assignment, misc]
    Tracer = None  # type: ignore[assignment, misc]


def get_tracer(name: str = "hawk.profiling") -> "Tracer | None":
    """
    Get an OpenTelemetry tracer for hawk profiling.

    Returns None if OpenTelemetry is not installed.
    """
    if not _otel_available:
        return None

    return trace.get_tracer(name)


@dataclass
class TraceContext:
    """
    Trace context for linking profiles to distributed traces.

    When OpenTelemetry is installed and a span is active, trace context
    is automatically extracted from the current span.
    """
    trace_id: str | None = None
    span_id: str | None = None

    @classmethod
    def from_current_span(cls) -> TraceContext:
        """
        Extract trace context from the current OpenTelemetry span.

        Returns an empty TraceContext if:
        - OpenTelemetry is not installed
        - No span is currently active
        - The span context is invalid
        """
        if not _otel_available:
            return cls()

        span = trace.get_current_span()
        if span is None:
            return cls()

        span_context = span.get_span_context()
        if span_context is None:
            return cls()

        trace_id = span_context.trace_id
        span_id = span_context.span_id

        # Check for invalid/unset trace context
        if trace_id == INVALID_TRACE_ID or span_id == INVALID_SPAN_ID:
            return cls()

        return cls(
            trace_id=format(trace_id, "032x"),
            span_id=format(span_id, "016x"),
        )

    @property
    def is_valid(self) -> bool:
        """Check if trace context has valid trace and span IDs."""
        return self.trace_id is not None and self.span_id is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert trace context to a dictionary for JSON serialization."""
        if not self.is_valid:
            return {}

        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }

    def format_for_filename(self) -> str:
        """
        Format trace context for inclusion in filenames.

        Returns empty string if trace context is not valid.
        Example output: "_trace-abc123def456_span-789xyz"
        """
        if not self.is_valid:
            return ""

        return f"_trace-{self.trace_id}_span-{self.span_id}"


@contextmanager
def profiling_span(
    profiler_type: str,
    profiler_name: str,
    attributes: dict[str, Any] | None = None,
) -> Generator["Span | None", None, None]:
    """
    Create an OpenTelemetry span for a profiling session.

    This context manager creates a span that wraps the profiling session,
    allowing profiling to appear in distributed traces.

    Args:
        profiler_type: Type of profiler ("cpu" or "mem")
        profiler_name: Name of the profiler ("pyinstrument", "yappi", "tracemalloc")
        attributes: Additional attributes to set on the span

    Yields:
        The created span, or None if OpenTelemetry is not available.

    Example:
        with profiling_span("cpu", "pyinstrument", {"hawk.format": "html"}) as span:
            with profiler.profile():
                # ... profiled code ...
    """
    tracer = get_tracer()

    if tracer is None:
        yield None
        return

    span_name = f"hawk.profile.{profiler_type}"

    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("hawk.profiler", profiler_name)
        span.set_attribute("hawk.profiler.type", profiler_type)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        yield span
