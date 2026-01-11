<div align="center">
    <img src="https://raw.githubusercontent.com/roma-glushko/hawk/main/assets/logo/hawk-debug_transparent_bg.png" width="300px" alt="Hawk Debug Toolkit For Python" />
    <h1>Hawk</h1>
    <p>Lightweight debugging & profiling toolkit <br/> for production 🐍Python services</p>
</div>

## Features

- **Memory Profiling** - tracemalloc-based allocation tracking
- **CPU Profiling** - cProfile (built-in), pyinstrument (async-aware), yappi (multi-threaded)
- **Debug Vars** - expose internal service state
- **ZPages** - custom debug dashboard
- **On-demand activation** - profile only when needed, download profiles for further investigation or render them in the browser
- **No elevated permissions** required (like `CAP_PTRACE`)
- Enable/disable via environment variables without **code changes**

## Installation

```bash
pip install hawk-debug
```

Optional dependencies for CPU profiling:

```bash
pip install hawk-debug[pyinstrument]  # async-aware sampling profiler
pip install hawk-debug[yappi]          # multi-threaded CPU/wall time profiler
```

> [!NOTE]
> This project is under development at this moment.

## Quick Start

### FastAPI

```python
from fastapi import FastAPI
from hawk.contrib.fastapi import get_router

app = FastAPI()
app.include_router(get_router())
```

### Starlette

```python
from starlette.applications import Starlette
from starlette.routing import Mount
from hawk.contrib.starlette import get_router

app = Starlette(routes=[
    Mount("/debug", app=get_router()),
])
```

### Flask

```python
from flask import Flask
from hawk.contrib.flask import create_debug_blueprint

app = Flask(__name__)
app.register_blueprint(create_debug_blueprint(), url_prefix="/debug")
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/debug/prof/cpu/cprofile/` | CPU profile with cProfile (fixed duration) |
| `/debug/prof/cpu/cprofile/start/` | Start cProfile CPU profiling |
| `/debug/prof/cpu/cprofile/stop/` | Stop and get cProfile CPU profile |
| `/debug/prof/cpu/pyinstrument/` | CPU profile with pyinstrument (fixed duration) |
| `/debug/prof/cpu/pyinstrument/start/` | Start pyinstrument CPU profiling |
| `/debug/prof/cpu/pyinstrument/stop/` | Stop and get pyinstrument CPU profile |
| `/debug/prof/cpu/yappi/` | CPU profile with yappi (fixed duration) |
| `/debug/prof/cpu/yappi/start/` | Start yappi CPU profiling |
| `/debug/prof/cpu/yappi/stop/` | Stop and get yappi CPU profile |
| `/debug/prof/mem/tracemalloc/` | Memory profile (fixed duration) |
| `/debug/prof/mem/tracemalloc/start/` | Start memory profiling |
| `/debug/prof/mem/tracemalloc/snapshot/` | Take memory snapshot |
| `/debug/prof/mem/tracemalloc/stop/` | Stop memory profiling |
| `/debug/vars/` | Debug variables |
| `/debug/` | ZPages dashboard |

## Query Parameters

### CPU Profiling (cProfile)
- `duration` - profile duration in seconds (default: 5)
- `format` - output: `text`, `json`, `pstat` (binary)
- `sort` - sort by: `cumulative`, `time`, `calls`, `name`
- `limit` - number of functions to show (default: 30)

### CPU Profiling (pyinstrument)
- `duration` - profile duration in seconds (default: 5)
- `format` - output: `html`, `json`, `speedscope`
- `interval` - sampling interval (default: 0.001)
- `async_mode` - `enabled`, `disabled`, `strict`

### CPU Profiling (yappi)
- `duration` - profile duration in seconds (default: 5)
- `format` - output: `funcstats` (JSON), `pstat` (binary), `callgrind` (for KCachegrind)
- `clock_type` - `cpu` (CPU time) or `wall` (wall clock time)
- `builtins` - profile built-in functions (default: false)
- `multithreaded` - profile all threads (default: true)

### Memory Profiling
- `duration` - profile duration in seconds (default: 5)
- `format` - output: `lineno`, `traceback`, `pickle`
- `frames` - stack frames to capture (default: 30)
- `count` - top N allocations (default: 10)
- `gc` - run GC before profiling (default: true)

## Integrations

<p align="center">
    <img src="https://raw.githubusercontent.com/roma-glushko/hawk/main/assets/contrib/fastapi.png" width="100px" alt="FastAPI" />
    <img src="https://raw.githubusercontent.com/roma-glushko/hawk/main/assets/contrib/starlette.svg" width="100px" alt="Starlette" />
    <img src="https://raw.githubusercontent.com/roma-glushko/hawk/main/assets/contrib/flask.png" width="100px" alt="Flask" />
</p>

## Inspiration

Inspired by Go's `net/http/pprof`, `expvars`, and OpenTelemetry Collector's ZPages.
