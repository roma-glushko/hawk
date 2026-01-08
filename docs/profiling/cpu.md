# CPU Profiling

Hawk supports two CPU profilers with different strengths:

| Profiler | Best For | Output Formats |
|----------|----------|----------------|
| **PyInstrument** | Async code, readable flame graphs | HTML, JSON, Speedscope |
| **Yappi** | Multi-threaded apps, precise timing | pstat, Callgrind, JSON |

## PyInstrument

Sampling profiler with native async support. Great for visualizing where time is spent.

**Install:** `pip install hawk-debug[pyinstrument]`

### Endpoints

```
GET /debug/prof/cpu/pyinstrument/           # Profile for fixed duration
GET /debug/prof/cpu/pyinstrument/start/     # Start manual profiling
GET /debug/prof/cpu/pyinstrument/stop/      # Stop and get results
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | 5 | Profiling duration in seconds |
| `format` | html | Output: `html`, `json`, `speedscope` |
| `interval` | 0.001 | Sampling interval in seconds |
| `async_mode` | enabled | Async handling: `enabled`, `disabled`, `strict` |

### Example

```bash
# Get an HTML flame graph (5 seconds)
curl "http://localhost:8000/debug/prof/cpu/pyinstrument/" > profile.html

# Profile with custom settings
curl "http://localhost:8000/debug/prof/cpu/pyinstrument/?duration=10&format=speedscope"

# Manual start/stop for targeted profiling
curl "http://localhost:8000/debug/prof/cpu/pyinstrument/start/"
# ... trigger the code path you want to profile ...
curl "http://localhost:8000/debug/prof/cpu/pyinstrument/stop/" > profile.html
```

## Yappi

Deterministic profiler with multi-threading support and CPU/wall time measurement.

**Install:** `pip install hawk-debug[yappi]`

### Endpoints

```
GET /debug/prof/cpu/yappi/           # Profile for fixed duration
GET /debug/prof/cpu/yappi/start/     # Start manual profiling
GET /debug/prof/cpu/yappi/stop/      # Stop and get results
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | 5 | Profiling duration in seconds |
| `format` | funcstats | Output: `funcstats` (JSON), `pstat`, `callgrind` |
| `clock_type` | cpu | Timing: `cpu` (CPU time) or `wall` (wall clock) |
| `builtins` | false | Include Python built-in functions |
| `multithreaded` | true | Profile all threads |

### Output Formats

- **funcstats**: JSON with per-function statistics (calls, time, subcalls)
- **pstat**: Python's standard pstats binary format, for use with `pstats` module
- **callgrind**: KCachegrind/QCachegrind compatible format for visualization

### Example

```bash
# Get JSON function stats
curl "http://localhost:8000/debug/prof/cpu/yappi/"

# Profile wall clock time across all threads
curl "http://localhost:8000/debug/prof/cpu/yappi/?clock_type=wall&duration=10"

# Export for KCachegrind visualization
curl "http://localhost:8000/debug/prof/cpu/yappi/?format=callgrind" > profile.callgrind
qcachegrind profile.callgrind
```

## When to Use Which

- **PyInstrument**: Async services, quick visualization, identifying slow code paths
- **Yappi**: Multi-threaded apps, precise CPU time measurement, integration with standard Python profiling tools
