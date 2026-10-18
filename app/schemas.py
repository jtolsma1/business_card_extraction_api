"""
Request model: one field, the image URL, validated as a real URL.
Response model: request ID, business name, person name, contact numbers, timings (total, download, Claude), and token usage.
Error model: a machine-readable error code, a human message, and the request ID.
Your existing business-card model lives here. A failed extraction must produce an error response, never the empty-but-valid card your pipeline used as a fallback.
"""
from pydantic import BaseModel, HttpUrl, Field,field_validator
from app.settings import get_settings

settings = get_settings()

class CardUrlError(Exception):
    def __init__(self,message):
        super().__init__(message)

class CardFileTypeError(Exception):
    def __init__(self,message):
        super().__init__(message)
class LookupRequest(BaseModel):
    request_id:str = Field(min_length=1,max_length=64)
    source_system:str = Field(min_length=1,max_length=32)
    card_url: HttpUrl

    @field_validator("card_url")
    @classmethod
    def validate_card_url(cls,url):
        url = str(url)
        file_type = url.rsplit(".",1)[1]
        for host in settings.ALLOWED_IMAGE_HOSTS:
            if host in url:
                if file_type in settings.ALLOWED_IMAGE_TYPES:
                    return url
                else:
                    raise CardFileTypeError(message=f"url file type '{file_type.upper()}' not in list of approved file types")
        if len(url) > 100:
            url = f"{url[:100]}..."
        raise CardUrlError(message=f"card URL is not in the list of approved hosts: {url}")

class LookupResponse(BaseModel):
    request_id:str
    business_name:str = ""
    person_name:str = ""
    contact_numbers:list[str] = []
    response_time_ms:float

class ErrorResponse(BaseModel):
    request_id:str
    error_message:str
    response_time_ms:float
