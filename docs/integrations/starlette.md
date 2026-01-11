# Starlette Integration

<div align="center" style="display: flex; justify-content: center; align-items: center">
    <img src="assets/contrib/starlette.svg" width="300px" alt="Starlette Logo" />
</div>

Debug and profiling support for [Starlette applications](https://starlette.dev/).

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

### Memory Profiling (tracemalloc)

```
GET /debug/prof/mem/tracemalloc/           # Fixed duration profile
GET /debug/prof/mem/tracemalloc/start/     # Start tracing
GET /debug/prof/mem/tracemalloc/snapshot/  # Take snapshot
GET /debug/prof/mem/tracemalloc/stop/      # Stop tracing
```

### CPU Profiling (PyInstrument)

Requires: `pip install hawk-debug[pyinstrument]`

```
GET /debug/prof/cpu/pyinstrument/          # Fixed duration profile
GET /debug/prof/cpu/pyinstrument/start/    # Start profiling
GET /debug/prof/cpu/pyinstrument/stop/     # Stop and get results
```

### CPU Profiling (Yappi)

Requires: `pip install hawk-debug[yappi]`

```
GET /debug/prof/cpu/yappi/                 # Fixed duration profile
GET /debug/prof/cpu/yappi/start/           # Start profiling
GET /debug/prof/cpu/yappi/stop/            # Stop and get results
```

### Thread Inspection

```
GET /debug/prof/threads/                   # Snapshot all thread stacks
```

### ZPages

```
GET /debug/<page_route>/                   # Access registered ZPages
GET /debug/vars/                           # Debug variables (if enabled)
```

## Example

```python
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import PlainTextResponse
from hawk.contrib.starlette import get_router

async def homepage(request):
    return PlainTextResponse("Hello!")

app = Starlette(routes=[
    Route("/", homepage),
    Mount("/debug", app=get_router()),
])
```

Profile your app:

```bash
# Memory profiling
curl "http://localhost:8000/debug/prof/mem/tracemalloc/?duration=10&count=20"

# CPU profiling with PyInstrument
curl "http://localhost:8000/debug/prof/cpu/pyinstrument/?duration=5"

# Thread inspection
curl "http://localhost:8000/debug/prof/threads/"
```

See [Profiling](../profiling/index.md) for detailed parameter documentation.
