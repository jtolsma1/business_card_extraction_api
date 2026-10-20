"""
A small family of domain exceptions and the handlers that turn each into the one error shape:
Situation	Status
Host not on allowlist = 422
URL unreachable or returns non-200 = 422
Not an image / unsupported type	= 415
Image too large	= 413
Claude rate limit or overload = 503
Claude timeout = 504
Claude connection or other failure = 502
A bad API key (401) is logged loudly and returned to the caller as a generic 500 or 502, so your credentials never leak into responses.
"""
from fastapi import Request
from fastapi.responses import JSONResponse

class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self,message:str):
        self.message = message

class ProcessTimeout(AppError):
    status_code = 504
    code = "process_timeout"


async def app_error_handler(request:Request,exc:AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code":exc.status_code,
            "message":exc.message,
            "request_id":getattr(request.state,"request_id",None)
            }
    )
