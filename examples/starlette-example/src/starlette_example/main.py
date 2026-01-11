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
import asyncio
import json
import time
from contextlib import asynccontextmanager

from hawk import zpages
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

from hawk.contrib.starlette import DebugMiddleware, get_router
from hawk.zpages.components import ZTable, TableStyle


def create_test_zpage() -> zpages.ZPage:
    zp = zpages.ZPage(
        title="Test Page",
        description="A test ZPage",
    )

    with zp.container() as c:
        c.add(ZTable(
            cols=["Property", "Value"],
            rows=[
                ["Name", "Test Page"],
                ["Description", "A test ZPage"],
                ["Author", "Roman Hlushko"],
            ],
            style=TableStyle.PROPERTY,
        ))

    return zp


@asynccontextmanager
async def lifespan(app: Starlette):
    zpages.add_page("test", create_test_zpage())
    yield


async def busy_wait(duration: float) -> None:
    end_time = time.time() + duration

    while time.time() < end_time:
        await asyncio.sleep(0.1)


async def welcome(request: Request) -> JSONResponse:
    await busy_wait(1)

    return JSONResponse({
        "message": "Welcome to Hawk: Starlette Example",
        "debug_url": "/debug/",
    })


routes = [
    Route("/", welcome),
    Mount("/debug", app=get_router()),
]

app = Starlette(
    debug=True,
    routes=routes,
    lifespan=lifespan,
)

app.add_middleware(DebugMiddleware)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
