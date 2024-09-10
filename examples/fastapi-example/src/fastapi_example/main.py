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