# Flask Integration

<div align="center" style="display: flex; justify-content: center; align-items: center">
    <img src="assets/contrib/flask.png" width="300px" alt="Flask Logo" />
</div>

Debug and profiling support for [Flask applications](https://flask.palletsprojects.com/en/stable/).

## Setup

```python
from flask import Flask
from hawk.contrib.flask import get_blueprint

app = Flask(__name__)
app.register_blueprint(get_blueprint(), url_prefix="/debug")
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
from flask import Flask
from hawk.contrib.flask import get_blueprint

app = Flask(__name__)
app.register_blueprint(get_blueprint(), url_prefix="/debug")

@app.route("/")
def index():
    return "Hello!"

if __name__ == "__main__":
    app.run(debug=True)
```

Profile your app:

```bash
# Memory profiling
curl "http://localhost:5000/debug/prof/mem/tracemalloc/?duration=10&count=20"

# CPU profiling with PyInstrument
curl "http://localhost:5000/debug/prof/cpu/pyinstrument/?duration=5"

# Thread inspection
curl "http://localhost:5000/debug/prof/threads/"
```

See [Profiling](../profiling/index.md) for detailed parameter documentation.
