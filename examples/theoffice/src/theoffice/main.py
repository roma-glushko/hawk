from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.theoffice.show.exceptions import BaseHTTPException
from src.theoffice.show.manager import ShowManager
from src.theoffice.show.router import router as show_router
from src.theoffice.health import router as health_router

app = FastAPI(
    title="The Office API",
)

app.include_router(show_router)
app.include_router(health_router)


class WelcomeResponse(BaseModel):
    message: str
    api_docs_url: str


@app.get("/")
async def welcome() -> WelcomeResponse:
    return WelcomeResponse(
        message="Welcome to The Office API 👔",
        api_docs_url="/docs",
    )


@app.exception_handler(BaseHTTPException)
async def exception_handler(request: Request, exc: BaseHTTPException):
    return JSONResponse(
        status_code=exc.status,
        content={"message": exc.args[0]},
    )


@app.on_event("startup")
async def on_startup() -> None:
    app.state.show_manager = ShowManager()
