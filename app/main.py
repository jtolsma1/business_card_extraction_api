"""
Builds the app and defines the lifespan. On startup it creates the httpx2 async client (with timeouts and a connection limit), the AsyncAnthropic client, and the semaphore sized from settings, and stores them on app state. On shutdown it closes both clients.
It registers the routers and error handlers.
Optionally, a middleware assigns each request an ID and logs start and finish.
"""
from fastapi import FastAPI
from anthropic import AsyncAnthropic
import asyncio
import httpx2
from contextlib import asynccontextmanager
from app.settings import get_settings
from app.routers.routers import router
from app.errors import AppError,app_error_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    app.state.httpx2_client = httpx2.AsyncClient(timeout=settings.FETCH_TIMEOUT_SECONDS)
    app.state.anthropic_client = AsyncAnthropic(
        api_key = settings.CLAUDE_API_KEY,
        timeout=settings.CLAUDE_TIMEOUT_SECONDS
        )
    app.state.semaphore = asyncio.Semaphore(
        value=settings.CLAUDE_MAX_CONCURRENT_CALLS
        )
    app.state.settings = settings

    yield

    await app.state.httpx2_client.aclose()
    await app.state.anthropic_client.close()

app = FastAPI(lifespan=lifespan)
app.include_router(router)
app.add_exception_handler(AppError,app_error_handler) # type: ignore
