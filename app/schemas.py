"""
Request model: one field, the image URL, validated as a real URL.
Response model: request ID, business name, person name, contact numbers, timings (total, download, Claude), and token usage.
Error model: a machine-readable error code, a human message, and the request ID.
Your existing business-card model lives here. A failed extraction must produce an error response, never the empty-but-valid card your pipeline used as a fallback.
"""
from pydantic import BaseModel, HttpUrl, Field

class LookupRequest(BaseModel):
    request_id:str = Field(min_length=1,max_length=64)
    card_url: HttpUrl
    source_system:str = Field(min_length=1,max_length=32)

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
