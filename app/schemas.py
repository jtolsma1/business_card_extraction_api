from pydantic import BaseModel, Field

from app.settings import get_settings

settings = get_settings()

class CardUrlError(Exception):
    def __init__(self,message):
        super().__init__(message)

class CardFileTypeError(Exception):
    def __init__(self,message):
        super().__init__(message)
class LookupRequest(BaseModel):
    request_id:str = Field(min_length=1,max_length=64,description="unique alphanumeric identifier for the request")
    source_system:str = Field(min_length=1,max_length=32,description="system making the request")
    card_url:str = Field(min_length=1,max_length=256,description="full url of the business card image")

class LookupResponse(BaseModel):
    request_id:str=Field(description="unique alphanumeric identifier for the request")
    business_name:str=Field(default="",description="name of the business shown on the business card or 'none' if the card represents an individual person")
    person_name:str=Field(default="",description="name of the person shown on the business card or 'none' if the card generically represents a business and not an individual person")
    contact_numbers:list[str]=Field(default=[],description="list of contact numbers (phone/fax/etc.) printed on the business card")
    download_time:float=Field(description="time, in seconds, needed to load image bytes from the image url provided")
    vlm_response_time:float=Field(description="time, in seconds, needed to extract all requested information from the business card using the VLM")
    total_response_time:float=Field(description="server time, in seconds, needed to process the entire load-and-extract request")

class ErrorResponse(BaseModel):
    request_id:str=Field(description="unique alphanumeric identifier for the request")
    error_message:str=Field(description="description of the error encountered")
    total_response_time:float=Field(description="server time, in seconds, needed to process the entire load-and-extract request until the error was encountered")
