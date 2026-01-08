<div align="center">
    <img src="https://raw.githubusercontent.com/roma-glushko/hawk/main/assets/logo/hawk-debug_transparent_bg.png" width="300px" alt="Hawk Debug Toolkit For Python" />
    <h1>Hawk</h1>
    <p>Lightweight debugging & profiling toolkit <br/> for production 🐍Python services</p>
</div>

## Features

- **Memory Profiling** - tracemalloc-based allocation tracking
- **CPU Profiling** - pyinstrument sampling profiler (async-aware)
- **Debug Vars** - expose internal service state
- **ZPages** - custom debug dashboard
- **On-demand activation** - profile only when needed, download profiles for further investigation or render them in the browser
- **No elevated permissions** required (like `CAP_PTRACE`)
- Enable/disable via environment variables without **code changes**

## Installation

```bash
pip install hawk-debug
```

> [!NOTE]
> This project is under development at this moment.

## Quick Start

### FastAPI

```python
from fastapi import FastAPI
from hawk.contrib.fastapi import HawkDebugRouter

app = FastAPI()
app.include_router(HawkDebugRouter())
```

### Starlette

```python
from starlette.applications import Starlette
from hawk.contrib.starlette import HawkDebugRouter

app = Starlette(routes=[
    HawkDebugRouter(),
])
```

### Flask

```python
from flask import Flask
from hawk.contrib.flask import hawk_debug_blueprint

app = Flask(__name__)
app.register_blueprint(hawk_debug_blueprint)
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/debug/prof/cpu/pyinstrument/` | CPU profile (fixed duration) |
| `/debug/prof/cpu/pyinstrument/start/` | Start CPU profiling |
| `/debug/prof/cpu/pyinstrument/stop/` | Stop and get CPU profile |
| `/debug/prof/mem/tracemalloc/` | Memory profile (fixed duration) |
| `/debug/prof/mem/tracemalloc/start/` | Start memory profiling |
| `/debug/prof/mem/tracemalloc/snapshot/` | Take memory snapshot |
| `/debug/prof/mem/tracemalloc/stop/` | Stop memory profiling |
| `/debug/vars/` | Debug variables |
| `/debug/` | ZPages dashboard |

## Query Parameters

### CPU Profiling
- `duration` - profile duration in seconds (default: 5)
- `format` - output: `html`, `json`, `speedscope`
- `interval` - sampling interval (default: 0.001)
- `async_mode` - `enabled`, `disabled`, `strict`

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
