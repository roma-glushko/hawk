# Debug Variables

Debug variables (expvars) let you expose internal application state for debugging. Inspired by Go's `expvar` package.

## Quick Start

```python
from hawk.expvars import Str, Int, Float, Bool, Func

# Typed variables (auto-registered)
app_version = Str("app.version", "1.2.3")
request_count = Int("requests.total", 0)
cache_hit_ratio = Float("cache.hit_ratio", 0.95)
debug_mode = Bool("debug.enabled", True)

# Dynamic values via functions
Func("runtime.goroutines", lambda: threading.active_count())
```

Access at `GET /debug/vars/` to see all exposed variables.

## Variable Types

### Str, Int, Float, Bool

Type-safe wrappers that auto-register on creation:

```python
from hawk.expvars import Str, Int, Float, Bool

db_host = Str("db.host", "localhost")
port = Int("db.port", 5432)
timeout = Float("db.timeout", 30.0)
connected = Bool("db.connected", False)
```

### Func

Wrap a callable for dynamic values evaluated at request time:

```python
from hawk.expvars import Func
import psutil

Func("system.cpu_percent", psutil.cpu_percent)
Func("system.memory_mb", lambda: psutil.virtual_memory().used // 1024 // 1024)
```

## Manual Registration

For existing objects or custom logic:

```python
from hawk.expvars import expose_var, get_vars

# Register any value
expose_var("config.max_connections", 100)
expose_var("feature.flags", {"new_ui": True, "beta": False})

# Get all registered variables
all_vars = get_vars()
```

## Endpoint

The expvars page is auto-registered at `/debug/vars/` when using `get_router()`.

```bash
# Get as HTML table
curl "http://localhost:8000/debug/vars/"

# Get as JSON
curl "http://localhost:8000/debug/vars/?format=json"
```

## Use Cases

- Expose configuration values for verification
- Track runtime counters (requests, errors, cache hits)
- Monitor dynamic system metrics
- Debug feature flags and toggles
