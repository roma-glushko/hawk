# Copyright (c) 2024 Roman Hlushko and various contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class DebugMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
        static_debug_token: str | None = None,
    ):
        super().__init__(app)

        self._enabled = enabled
        self._static_debug_token = static_debug_token

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._enabled:
            return await call_next(request)

        debug_enabled = request.get("debug") or False # bool or str

        if not debug_enabled:
            # ignore the request if debug is disabled
            return await call_next(request)

        if self._static_debug_token and self._static_debug_token != debug_enabled:
            # ignore the request if token was set but it's provided invalid
            # TODO: consider logging
            return await call_next(request)

        profiler = request.get("profiler")

        if profiler is None:
            # ignore the request if profiler is not set, don't play guessing game
            # TODO: consider logging
            return await call_next(request)

        # TODO: get the profile, validate params and start profiling

        try:
            response = await call_next(request)
        finally:
            # TODO: finalize profiling and return the profile as a response
            ...

        return response
