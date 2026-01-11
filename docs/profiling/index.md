# Profiling

Hawk provides on-demand profiling for production services.

## Profilers

| Type | Profiler | Use Case |
|------|----------|----------|
| [Memory](memory.md) | tracemalloc | Track memory allocations, find leaks |
| [CPU](cpu.md) | cProfile | Built-in, no dependencies, standard tooling |
| [CPU](cpu.md) | PyInstrument | Async-aware sampling, flame graphs |
| [CPU](cpu.md) | Yappi | Multi-threaded, precise timing |
| [Threads](threads.md) | threads | Inspect thread stacks, debug deadlocks |

## Profiling Modes

### Fixed Duration

Profile for a set duration and get results:

```bash
curl "http://localhost:8000/debug/prof/cpu/pyinstrument/?duration=10"
```

### Manual Start/Stop

Control profiling programmatically for targeted analysis:

```bash
# Start
curl "http://localhost:8000/debug/prof/cpu/pyinstrument/start/"

# ... trigger the code you want to profile ...

# Stop and get results
curl "http://localhost:8000/debug/prof/cpu/pyinstrument/stop/"
```

## Output Formats

Each profiler supports multiple output formats:

- **HTML/JSON**: View in browser or process programmatically
- **Binary**: Download for offline analysis (pstat, pickle)
- **External tools**: Speedscope, KCachegrind/QCachegrind
