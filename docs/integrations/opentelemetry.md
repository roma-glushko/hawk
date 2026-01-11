# OpenTelemetry Integration

<div align="center" style="display: flex; justify-content: center; align-items: center">
    <img src="assets/contrib/opentelemetry.svg" width="300px" alt="OpenTelemetry Logo" />
</div>

Hawk integrates with [OpenTelemetry](https://opentelemetry.io/) to link profiling data with distributed traces. This allows you to correlate performance profiles with specific requests and trace spans.

## Installation

OpenTelemetry integration is optional. Install the OpenTelemetry API package:

```bash
pip install opentelemetry-api
```

For full tracing support, you'll also need the SDK and an exporter:

```bash
pip install opentelemetry-sdk opentelemetry-exporter-otlp
```

## Features

When OpenTelemetry is installed and configured, Hawk automatically:

1. **Links profiles to traces** - Profile filenames and JSON content include trace context
2. **Emits profiling spans** - Each profiling session creates a span in your distributed trace

If OpenTelemetry is not installed, Hawk works normally without any trace integration.

## Trace Context in Profiles

### Filenames

When a profile is captured within an active trace, the filename includes trace context:

```
# Without OTel
hwk_cpu_pyinstr_profile_2024-01-09_12-30-45.json

# With OTel (trace active)
hwk_cpu_pyinstr_profile_2024-01-09_12-30-45_trace-abc123..._span-def456....json
```

This makes it easy to find profiles associated with specific traces.

### JSON Content

For JSON output formats, trace context is included in the content:

```json
{
  "trace_context": {
    "trace_id": "abc123def456...",
    "span_id": "789xyz..."
  },
  "stats": [...],
  "heap_current_bytes": 10485760
}
```

### Metadata Field

The `RenderedProfile` dataclass includes a `metadata` field for programmatic access:

```python
rendered = handler.render_profile()
if rendered.metadata:
    trace_id = rendered.metadata.get("trace_id")
    span_id = rendered.metadata.get("span_id")
```

## Profiling Spans

Each profiling session automatically creates an OpenTelemetry span, making profiling visible in your distributed traces.

### Span Names

| Profiler Type | Span Name |
|---------------|-----------|
| CPU (pyinstrument, yappi) | `hawk.profile.cpu` |
| Memory (tracemalloc) | `hawk.profile.mem` |

### Span Attributes

All profiling spans include these common attributes:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `hawk.profiler` | Profiler name | `"pyinstrument"`, `"yappi"`, `"tracemalloc"` |
| `hawk.profiler.type` | Profiler category | `"cpu"`, `"mem"` |
| `hawk.format` | Output format | `"html"`, `"json"`, `"speedscope"` |

#### PyInstrument-specific Attributes

| Attribute | Description |
|-----------|-------------|
| `hawk.interval` | Sampling interval in seconds |
| `hawk.async_mode` | Async mode (`"enabled"`, `"disabled"`, `"strict"`) |

#### Yappi-specific Attributes

| Attribute | Description |
|-----------|-------------|
| `hawk.clock_type` | Clock type (`"cpu"`, `"wall"`) |
| `hawk.builtins` | Whether builtins are profiled |
| `hawk.multithreaded` | Whether multithreading is enabled |

#### Tracemalloc-specific Attributes

| Attribute | Description |
|-----------|-------------|
| `hawk.frames` | Number of frames to capture |
| `hawk.gc` | Whether GC runs before profiling |

## Example: Tracing a Profile Request

When you request a profile via HTTP, the span hierarchy looks like:

```
HTTP GET /debug/prof/cpu/pyinstrument/
└── hawk.profile.cpu
    ├── hawk.profiler: "pyinstrument"
    ├── hawk.profiler.type: "cpu"
    ├── hawk.format: "html"
    └── hawk.interval: 0.001
```

The profile output will reference this span's trace context, allowing you to:

1. Find the profile file by trace ID
2. See profiling duration in your trace visualization
3. Correlate slow traces with their CPU/memory profiles

## Configuration

No special configuration is needed. Hawk automatically detects OpenTelemetry and uses it when available.

### Tracer Name

Hawk uses the tracer name `hawk.profiling` for all profiling spans. You can configure this tracer in your OpenTelemetry setup if needed:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

provider = TracerProvider()
trace.set_tracer_provider(provider)

# Hawk will automatically use this provider
```

## Use Cases

### Debugging Slow Requests

1. Find a slow trace in your observability platform
2. Copy the trace ID
3. Search for profile files containing that trace ID
4. Analyze the profile to understand the performance issue

### Continuous Profiling Correlation

If you have continuous profiling enabled, you can:

1. Trigger profiling during a specific request
2. Use the trace context to correlate the on-demand profile with continuous profiling data
3. Compare baseline vs. problematic request profiles

### Automated Profiling

Programmatically trigger profiling for specific traces:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def handle_request():
    with tracer.start_as_current_span("my-operation"):
        # Profile will be linked to this span
        handler = ProfileHandler({"format": "json", "duration": "5"})
        async with handler.profile():
            await do_work()

        profile = handler.render_profile()
        # profile.metadata contains trace_id and span_id
```
