# Integrations

Hawk integrates with popular Python web frameworks and observability tools.

## Frameworks

| Framework | Status | Features |
|-----------|--------|----------|
| [FastAPI](fastapi.md) | Full | Memory, CPU (PyInstrument, Yappi), ZPages, Expvars |
| [Starlette](starlette.md) | Partial | Memory profiling |
| [Flask](flask.md) | Partial | Memory profiling |

## Observability

| Tool | Status | Features |
|------|--------|----------|
| [OpenTelemetry](opentelemetry.md) | Optional | Trace linking, profiling spans |

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

## Feature Matrix

| Feature | FastAPI | Starlette | Flask |
|---------|---------|-----------|-------|
| Memory profiling | Yes | Yes | Yes |
| CPU (PyInstrument) | Yes | - | - |
| CPU (Yappi) | Yes | - | - |
| Debug variables | Yes | - | - |
| Custom ZPages | Yes | - | - |
| OpenTelemetry | Yes | Yes | Yes |
