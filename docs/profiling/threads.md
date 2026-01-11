# Thread Inspection

Hawk provides thread inspection to capture stack traces from all running threads. Useful for debugging deadlocks, identifying stuck threads, or understanding concurrent behavior.

## Endpoint

```
GET /debug/prof/threads/    # Take a snapshot of all thread stacks
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `format` | json | Output format: `json` |
| `max_depth` | 128 | Maximum stack frames to capture per thread |

## Output

The JSON output includes:

- **thread_count**: Total number of threads
- **threads**: List of thread information, each containing:
  - **thread_id**: Python thread identifier
  - **name**: Thread name (if set)
  - **daemon**: Whether the thread is a daemon thread
  - **stack**: List of stack frames (function, filename, line number)

## Example

```bash
# Get all thread stacks
curl "http://localhost:8000/debug/prof/threads/"

# Limit stack depth
curl "http://localhost:8000/debug/prof/threads/?max_depth=20"
```

### Sample Output

```json
{
  "thread_count": 3,
  "threads": [
    {
      "thread_id": 123456789,
      "name": "MainThread",
      "daemon": false,
      "stack": [
        {
          "function": "run",
          "filename": "/app/server.py",
          "lineno": 45
        },
        {
          "function": "handle_request",
          "filename": "/app/handlers.py",
          "lineno": 123
        }
      ]
    },
    {
      "thread_id": 987654321,
      "name": "WorkerThread-1",
      "daemon": true,
      "stack": [
        {
          "function": "wait",
          "filename": "/usr/lib/python3.12/threading.py",
          "lineno": 320
        }
      ]
    }
  ]
}
```

## Use Cases

- **Deadlock detection**: Identify threads waiting on locks
- **Stuck thread diagnosis**: Find threads blocked on I/O or long computations
- **Concurrency debugging**: Understand what each thread is doing at a point in time
