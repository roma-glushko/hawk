<div align="center">
    <img src="assets/logo/hawk-debug_transparent_bg.png" width="300px" alt="Hawk Debug Toolkit For Python" />
    <h1>Hawk: Debug & Profile</h1>
    <p>A lightweight debugging & profiling toolkit <br/> for production 🐍 Python microservices</p>
</div>

🦅 Hawk gives you more control over how your Python microservices run in production
with little overhead by bringing a set of internal API to help you to profile and debug your services.

Hawk is inspired by Go's `net/http/pprof` & `expvars` packages and 
OpenTelemetry Collector's ZPages which are in turn stemmed from Google's internal practices around
debugging production services.

## Features

- ⏱️**Memory Profiling** via the `tracemalloc` stdlib
- ⏱️**CPU Profiling** (incl. Asyncio services) via `pyinstrument` & `cProfile` (soon)
- 🙋‍♀️**Activate profiling on demand** in real environments
- 🔒**Control who can turn on profiling and access debug pages** via a simple session API (soon)
- 🎨**Render your profiles** right from your browser
- ⬇️**Download your profiles** for the further investigation
- 🔭**Expose internal state** of your service via debug vars (soon)
- 🔧**Create custom debug pages** (a.k.a. `ZPages`) in a simplified way (soon)
- 🔧**Controlled via environment variables**, no codebase modifications needed to enable/disable functionality completely
- 🔓**No elevated permissions needed** (`CAP_PTRACE`, etc.)
- 🔭**OpenTelemetry**-aware (soon)

<div align="center">
    <p>Integrated With:</p>
    <p align="center">
        <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" width="150px" alt="FastAPI Logo" />
        <img src="https://www.starlette.io/img/starlette.png" width="150px" alt="Starlette Logo" />
        <img src="https://flask.palletsprojects.com/en/3.0.x/_images/flask-horizontal.png" width="150px" alt="Flask Logo" />
    </p>
</div>

## References

- https://pkg.go.dev/net/http/pprof
- https://pypi.org/project/fastapi-cprofile/
- https://www.reddit.com/r/Python/comments/15jj010/how_to_profile_an_asynchronous_fastapi_server/
- https://blog.balthazar-rouberol.com/how-to-profile-a-fastapi-asynchronous-request
- https://pyinstrument.readthedocs.io/en/latest/how-it-works.html
- https://www.roguelynn.com/words/asyncio-profiling/
- https://vince.id/posts/finding-memory-leaks-in-python/
- https://medium.com/@narenandu/profiling-and-visualization-tools-in-python-89a46f578989
- https://github.com/Chia-Network/chia-blockchain/blob/18438883f18d345b777d4e726c02d56c23008584/chia/util/profiler.py#L175
- https://github.com/DataDog/dd-trace-py/blob/main/ddtrace/profiling/collector/threading.py
- https://github.com/dpsoft/flask-pypprof/tree/main
- https://gitlab.com/prologin/tech/packages/django-pypprof/-/tree/main
