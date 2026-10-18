"""
One settings object, loaded once from the process environment (pydantic-settings fits the FastAPI/Pydantic stack).
It holds the Anthropic key, model name, allowed image hosts, max concurrent Claude calls, fetch and Claude timeouts, max image size, the User-Agent string for fetches, and the fake-extractor flag plus its simulated delay.
It reads the environment directly, with no python-dotenv in the container. Compose supplies the variables.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # VLM ---
    CLAUDE_API_KEY:str
    CLAUDE_MODEL:str
    CLAUDE_TIMEOUT_SECONDS:int = 60
    CLAUDE_MAX_CONCURRENT_CALLS:int = 5
    
    # Image Fetch ---
    ALLOWED_IMAGE_HOSTS:list[str]
    FETCH_TIMEOUT_SECONDS:int = 15
    MAX_IMAGE_BYTES:float = 5.0e6
    FETCH_USER_AGENT:str

    # Fake extractor for testing concurrency without incurring Anthropic credits ---
    USE_FAKE_EXTRACTOR = True
    FAKE_EXTRACTOR_DELAY_SECONDS = 2

    # Server ---
    HOST_PORT=8000
    LOG_LEVEL=info

@lru_cache
def get_settings() -> Settings:
    return Settings()





