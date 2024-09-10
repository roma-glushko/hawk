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

from fastapi import FastAPI
from pydantic import BaseModel

from hawk.contrib.fastapi import DebugMiddleware, get_router

app = FastAPI(
    title="Hawk: FastAPI Example",
)

app.add_middleware(
    DebugMiddleware,
    static_debug_token="debug",
)

app.include_router(get_router(
    prefix="/debug",
    tags=["debug"],
    include_in_schema=True,
))

class WelcomeResponse(BaseModel):
    message: str
    api_docs_url: str


@app.get("/")
async def welcome() -> WelcomeResponse:
    await asyncio.sleep(1)

    return WelcomeResponse(
        message="Welcome to Hawk: FastAPI Example",
        api_docs_url="/docs",
    )