# Starlette Integration

Memory profiling support for Starlette applications.

## Setup

```python
from starlette.applications import Starlette
from starlette.routing import Mount
from hawk.contrib.starlette import get_router

app = Starlette(routes=[
    Mount("/debug", app=get_router()),
])
```

## Available Endpoints

```
GET /debug/prof/mem/tracemalloc/           # Fixed duration profile
GET /debug/prof/mem/tracemalloc/start/     # Start tracing
GET /debug/prof/mem/tracemalloc/snapshot/  # Take snapshot
GET /debug/prof/mem/tracemalloc/stop/      # Stop tracing
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | 5 | Profiling duration in seconds |
| `format` | lineno | Output: `lineno`, `traceback`, `pickle` |
| `frames` | 30 | Stack frames to capture |
| `count` | 10 | Number of top allocations |
| `gc` | true | Run GC before profiling |
| `cumulative` | false | Show cumulative stats |

## Middleware

For request-level profiling:

```python
from hawk.contrib.starlette import DebugMiddleware

app = Starlette(middleware=[
    Middleware(DebugMiddleware),
])
```
