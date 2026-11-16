from time import time
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from app.schemas import ErrorResponse

class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self,message:str):
        self.message = message

class ImageNotFound(AppError):
    status_code = 422
    code = "image_not_found"

class InvalidImageTypeError(AppError):
    status_code = 415
    code = "invalid_image_type"

class InvalidImageHost(AppError):
    status_code = 422
    code = "invalid_image_host"

class ProcessTimeout(AppError):
    status_code = 504
    code = "process_timeout"

class ImageMaxSizeExceeded(AppError):
    status_code = 413
    code = "image_max_size_exceeded"

class VLMRateLimit(AppError):
    status_code = 503
    code = "vlm_rate_limit"

def build_error_response(request:Request,status_code:int,code:str,message:str):
    start = getattr(request.state,"start_time",None)
    end=time()
    body = ErrorResponse(
        request_id=getattr(request.state,"request_id",None),
        code=code,
        error_message=message,
        total_response_time=end-start if start is not None else None
    )
    return JSONResponse(status_code=status_code,content=body.model_dump())

async def app_error_handler(request:Request,exc:AppError):
    return build_error_response(request,exc.status_code,exc.code,exc.message)

async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc!r}")
    return build_error_response(request,500,"internal_server_error","Internal server error")