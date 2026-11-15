import asyncio
from contextlib import asynccontextmanager
from anthropic import AsyncAnthropic
from httpx2 import AsyncClient
from fastapi import FastAPI

from app.errors import AppError,app_error_handler,unhandled_error_handler
from app.routers.routers import router
from app.settings import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    app.state.httpx2_client = AsyncClient(timeout=settings.FETCH_TIMEOUT_SECONDS)
    app.state.anthropic_client = AsyncAnthropic(
        api_key = settings.CLAUDE_API_KEY,
        max_retries=0, # use retry structure created in this app
        timeout=settings.CLAUDE_TIMEOUT_SECONDS
        )
    app.state.semaphore = asyncio.Semaphore(
        value=settings.CLAUDE_MAX_CONCURRENT_CALLS
        )
    app.state.settings = settings

    yield

    await app.state.httpx2_client.aclose()
    await app.state.anthropic_client.close()

app = FastAPI(
    title="Business Card Extraction API",
    summary="Extract names and phone numbers from business card images.",
    description="""
Send an image URL, get back the business name, person name and contact numbers.

## How it works
- The image is downloaded (allowlisted hosts only), then read by a vision model.
- Requests run concurrently on one event loop.

## Errors
Every error returns `{"code", "message", "request_id"}`.
""",
    version="1.0.0",
    contact={"name": "Joe Tolsma", "url": "https://github.com/jtolsma1/business_card_extraction_api"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    lifespan=lifespan,
)
app.include_router(router)
app.add_exception_handler(AppError,app_error_handler) # type: ignore
app.add_exception_handler(AppError,unhandled_error_handler) # type: ignore
