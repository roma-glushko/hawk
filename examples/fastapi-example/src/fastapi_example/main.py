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
import time
from contextlib import asynccontextmanager

from hawk import zpages
from fastapi import FastAPI
from pydantic import BaseModel

from hawk.contrib.fastapi import DebugMiddleware, get_router
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
async def lifespan(app: FastAPI):
    zpages.add_page("test", create_test_zpage())
    yield

app = FastAPI(
    title="Hawk: FastAPI Example",
    lifespan=lifespan,
)

app.add_middleware(
    DebugMiddleware,
)

app.include_router(get_router(
    prefix="/debug",
    tags=["debug"],
    include_in_schema=True,
))

class WelcomeResponse(BaseModel):
    message: str
    api_docs_url: str


async def busy_wait(duration):
    end_time = time.time() + duration

    while time.time() < end_time:
        await asyncio.sleep(0.1)

@app.get("/")
async def welcome() -> WelcomeResponse:
    await busy_wait(1)

    return WelcomeResponse(
        message="Welcome to Hawk: FastAPI Example",
        api_docs_url="/docs",
    )