# Memory Profiling

Hawk uses Python's built-in `tracemalloc` to track memory allocations. No external dependencies required.

## Endpoints

```
GET /debug/prof/mem/tracemalloc/           # Profile for fixed duration
GET /debug/prof/mem/tracemalloc/start/     # Start memory tracing
GET /debug/prof/mem/tracemalloc/snapshot/  # Take a snapshot (while tracing)
GET /debug/prof/mem/tracemalloc/stop/      # Stop memory tracing
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | 5 | Profiling duration in seconds |
| `format` | lineno | Output: `lineno`, `traceback`, `pickle` |
| `frames` | 30 | Stack frames to capture |
| `count` | 10 | Number of top allocations to return |
| `gc` | true | Run garbage collection before profiling |
| `cumulative` | false | Show cumulative statistics |

## Output Formats

- **lineno**: JSON with per-line allocation statistics (file, line, size, count)
- **traceback**: JSON with full stack traces for each allocation
- **pickle**: Binary pickle format for offline analysis with Python's `tracemalloc` module

## Examples

```bash
# Get top 10 memory allocations (5 seconds)
curl "http://localhost:8000/debug/prof/mem/tracemalloc/"

# Get top 20 allocations with full tracebacks
curl "http://localhost:8000/debug/prof/mem/tracemalloc/?count=20&format=traceback"

# Download for offline analysis
curl "http://localhost:8000/debug/prof/mem/tracemalloc/?format=pickle" > snapshot.pkl
```

## Interval Profiling

For tracking memory growth over time, use manual start/snapshot/stop:

```bash
# Start tracing
curl "http://localhost:8000/debug/prof/mem/tracemalloc/start/"

# Take snapshots at intervals to compare
curl "http://localhost:8000/debug/prof/mem/tracemalloc/snapshot/" > t0.json
# ... wait ...
curl "http://localhost:8000/debug/prof/mem/tracemalloc/snapshot/" > t1.json

# Stop tracing
curl "http://localhost:8000/debug/prof/mem/tracemalloc/stop/"
```

## Offline Analysis

Download a pickle snapshot and analyze locally:

```python
import pickle
import tracemalloc

with open("snapshot.pkl", "rb") as f:
    snapshot = pickle.load(f)

# Show top allocations
top_stats = snapshot.statistics("lineno")
for stat in top_stats[:10]:
    print(stat)
```
