# Flask Integration

Memory profiling support for Flask applications.

## Setup

```python
from flask import Flask
from hawk.contrib.flask import create_debug_blueprint

app = Flask(__name__)
app.register_blueprint(create_debug_blueprint(), url_prefix="/debug")
```

## Available Endpoints

```
GET /debug/prof/mem/                # Fixed duration profile
GET /debug/prof/mem/start/          # Start tracing
GET /debug/prof/mem/snapshot/       # Take snapshot
GET /debug/prof/mem/stop/           # Stop tracing
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration` | 5 | Profiling duration in seconds |
| `format` | lineno | Output: `lineno`, `traceback`, `pickle` |
| `frames` | 30 | Stack frames to capture |
| `count` | 10 | Number of top allocations |
| `cumulative` | false | Show cumulative stats |

## Example

```python
from flask import Flask
from hawk.contrib.flask import create_debug_blueprint

app = Flask(__name__)
app.register_blueprint(create_debug_blueprint(), url_prefix="/debug")

@app.route("/")
def index():
    return "Hello!"

if __name__ == "__main__":
    app.run(debug=True)
```

Profile your app:

```bash
curl "http://localhost:5000/debug/prof/mem/?duration=10&count=20"
```
