from fastapi import Request
from fastapi.responses import JSONResponse

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

async def app_error_handler(request:Request,exc:AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code":exc.status_code,
            "message":exc.message,
            "request_id":getattr(request.state,"request_id",None)
            }
    )
