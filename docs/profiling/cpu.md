# CPU Profiling

Hawk supports three CPU profilers with different strengths:

| Profiler | Best For | Output Formats | Install |
|----------|----------|----------------|---------|
| **cProfile** | Quick profiling, no dependencies | Text, JSON, pstat | Built-in |
| **PyInstrument** | Async code, readable flame graphs | HTML, JSON, Speedscope | Extra |
| **Yappi** | Multi-threaded apps, precise timing | pstat, Callgrind, JSON | Extra |

## cProfile

Python's built-in deterministic profiler. Zero dependencies, always available.

**Install:** Included with Python (no extra installation needed)

### Endpoints

```
GET /debug/prof/cpu/cprofile/           # Profile for fixed duration
GET /debug/prof/cpu/cprofile/start/     # Start manual profiling
GET /debug/prof/cpu/cprofile/stop/      # Stop and get results
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | 5 | Profiling duration in seconds |
| `format` | text | Output: `text`, `json`, `pstat` |
| `sort` | cumulative | Sort by: `cumulative`, `time`, `calls`, `name` |
| `limit` | 30 | Number of functions to show |

### Output Formats

- **text**: Human-readable pstats output, viewable in browser
- **json**: Structured JSON with per-function statistics
- **pstat**: Binary pstats format for use with `pstats` module or tools like snakeviz

### Example

```bash
# Get text output (default)
curl "http://localhost:8000/debug/prof/cpu/cprofile/"

# Get JSON with top 50 functions sorted by total time
curl "http://localhost:8000/debug/prof/cpu/cprofile/?format=json&sort=time&limit=50"

# Export for snakeviz visualization
curl "http://localhost:8000/debug/prof/cpu/cprofile/?format=pstat" > profile.pstat
snakeviz profile.pstat
```

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

- **cProfile**: Quick profiling with no setup, standard Python tooling, works everywhere
- **PyInstrument**: Async services, quick visualization, identifying slow code paths
- **Yappi**: Multi-threaded apps, precise CPU time measurement, per-thread statistics
