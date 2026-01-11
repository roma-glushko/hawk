# FastAPI Integration

<div align="center" style="display: flex; justify-content: center; align-items: center">
    <img src="assets/contrib/fastapi.png" width="300px" alt="FastAPI Logo" />
</div>

Full-featured [FastAPI integration](https://fastapi.tiangolo.com/) with all Hawk capabilities.

## Setup

```python
from fastapi import FastAPI
from hawk.contrib.fastapi import get_router

app = FastAPI()
app.include_router(get_router())
```

## Configuration

```python
router = get_router(
    prefix="/debug",           # URL prefix (default: "/debug")
    tags=["debug"],            # OpenAPI tags
    include_in_schema=False,   # Hide from OpenAPI docs (default)
    register_expvars=True,     # Auto-register /debug/vars/ (default)
)
```

## Available Endpoints

All endpoints are prefixed with your configured prefix (default: `/debug`).

### Memory Profiling

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
GET /debug/vars/                           # Debug variables
GET /debug/{page_route}/                   # Custom ZPages
```

## Example

```python
from fastapi import FastAPI
from hawk.contrib.fastapi import get_router
from hawk.expvars import Str, Int
from hawk.zpages import ZPage, add_page
from hawk.zpages.components import ZTable

app = FastAPI()

# Expose debug variables
app_version = Str("app.version", "1.0.0")
request_count = Int("requests.total", 0)

# Add a custom status page
status_page = ZPage("Status")
status_page.add(ZTable(
    cols=["Service", "Status"],
    rows=[["API", "healthy"], ["DB", "healthy"]]
))
add_page("status", status_page)

# Mount Hawk router
app.include_router(get_router())
```

Access your debug endpoints:
- `http://localhost:8000/debug/vars/` - Debug variables
- `http://localhost:8000/debug/status/` - Custom status page
- `http://localhost:8000/debug/prof/mem/tracemalloc/` - Memory profile
