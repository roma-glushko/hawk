from __future__ import annotations

from enum import StrEnum
from threading import Lock
from typing import Type

PYINSTRUMENT_INSTALLED: bool = True

try:
    from pyinstrument import Profiler
    from pyinstrument.renderers import JSONRenderer, HTMLRenderer, SpeedscopeRenderer
except ImportError:
    PYINSTRUMENT_INSTALLED = False


class ProfileFormat(StrEnum):
    HTML = "html"
    JSON = "json"
    SPEEDSCOPE = "speedscope"


class PyInstrumentProfiler:
    def __init__(self) -> None:
        self._profiler_lock = Lock()
        self._curr_profiler: "Profiler" | None = None

    def start(self, interval: float = 0.001, async_mode: bool = True) -> "Profiler":
        if self._curr_profiler:
            # TODO: raise error
            ...

        with self._profiler_lock:
            # https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
            profiler = Profiler(interval=interval, async_mode=async_mode)
            profiler.start()
            self._curr_profiler = profiler

        return self._curr_profiler

    def is_profiling(self) -> bool:
        return bool(self._curr_profiler)

    def stop(self) -> "Profiler":
        if not self._curr_profiler:
            # TODO: raise error
            ...

        with self._profiler_lock:
            if not self._curr_profiler:
                # TODO: throw error
                ...

            self._curr_profiler.stop()
            profiler, self._curr_profiler = self._curr_profiler, None

        return profiler


PROFILE_RENDERERS = {
    ProfileFormat.JSON: JSONRenderer,
    ProfileFormat.HTML: HTMLRenderer,
    ProfileFormat.SPEEDSCOPE: SpeedscopeRenderer,
}


def get_renderer(format: ProfileFormat) -> Type[JSONRenderer | HTMLRenderer | SpeedscopeRenderer]:
    return PROFILE_RENDERERS[format]


profiler = PyInstrumentProfiler()
