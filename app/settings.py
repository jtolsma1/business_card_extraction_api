from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # VLM ---
    CLAUDE_API_KEY:str
    CLAUDE_MODEL:str
    CLAUDE_TIMEOUT_SECONDS:int|float = 20
    CLAUDE_MAX_CONCURRENT_CALLS:int = 5
    
    # Image Fetch ---
    ALLOWED_IMAGE_HOSTS:list[str]
    ALLOWED_IMAGE_TYPES:list[str]
    FETCH_TIMEOUT_SECONDS:int|float= 10
    MAX_IMAGE_BYTES:int|float = 10.0e6
    FETCH_USER_AGENT:str

    # Fake extractor for testing concurrency without incurring Anthropic credits ---
    USE_FAKE_EXTRACTOR:bool= True
    FAKE_EXTRACTOR_SLEEP_RANGE:str="2.4,4.1"

    # Other ---
    MAX_ATTEMPTS:int=2 # maximum number of times to attempt io functions

@lru_cache
def get_settings() -> Settings:
    return Settings() # type:ignore
