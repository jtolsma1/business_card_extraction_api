from time import time,sleep
from httpx2 import ConnectTimeout
from loguru import logger

from app.errors import (
    ImageMaxSizeExceeded, 
    ImageNotFound, 
    InvalidImageHost, 
    InvalidImageTypeError,
    ProcessTimeout
)

def validate_image_host(image_url,allowed_image_hosts):
    for host in allowed_image_hosts:
        if host in image_url:
            return True
    return False


async def run_image_byte_fetch(
        httpx2_client,
        request_id:str,
        image_url:str,
        max_bytes:float,
        headers:dict,
        allowed_image_hosts:list[str],
        allowed_image_types:list[str],
        max_attempts:int
        ):
    
    """
    Loads image as bytes from image url passed in API request body.

    @param httpx2_client: HTTP client needed to access the online image
    @param request_id: request id passed in the API request body; used for logging
    @param image_url: image url passed in API request body
    @param max_bytes: maximum image size; if exceeded, stops load and raises error
    @param headers: image download headers to identify this API's user-agent
    @param allowed_image_hosts: list of allowed image hosts; if image url does not match, raises error
    @param allowed_image_types: list of allowed image types; if image url does not match, raises error
    @param max_attempts: number of attempts made to load image before giving up
    @returns: image bytes, image type, image download time
    """
    
    start = time()

    # Validate image host before executing image download
    is_valid_host = validate_image_host(image_url,allowed_image_hosts)
    if is_valid_host is False:
        raise InvalidImageHost(f"Image url passed for request id {request_id} does not match any host on the image host whitelist")
    
    for _ in range(max_attempts):
        success = False
        last_error=None
        try:
            # Stream image download and break if maximum image size is exceeded
            async with httpx2_client.stream(method="GET",url=image_url,headers=headers) as response:

                if response.status_code != 200:
                    raise ImageNotFound("")

                image_type = response.headers["Content-Type"] 
                if image_type not in allowed_image_types:
                    raise InvalidImageTypeError(f"Image URL for request id {request_id} directs to unsupported image type: {image_type}")

                buf = bytearray()
                async for chunk in response.aiter_bytes():
                    buf.extend(chunk)

                    if len(buf) > max_bytes:
                        raise ImageMaxSizeExceeded(f"Image for request id {request_id} exceeds maximum size limit of {max_bytes} bytes and will not be downloaded")
            success = True
        except Exception as error:
            if isinstance(error,ImageNotFound) and response.status_code:
                logger.warning(f"Image fetch for request id {request_id} returned {response.status_code}; retrying")
                sleep(0.5)
                last_error = error
                continue
            elif isinstance(error,ConnectTimeout):
                logger.warning(f"Image fetch for request id {request_id} reached http connection timeout; retrying")
                sleep(0.5)
                last_error = error
                continue
            else:
                raise error

    
    end = time()
    download_time = end - start
    
    if success:
        return buf, image_type, download_time
    elif isinstance(last_error,ImageNotFound):
        raise ImageNotFound(f"Request to provided url for request id {request_id} returned failure status code {response.status_code}")
    elif isinstance(last_error,ConnectTimeout):
        raise ProcessTimeout(f"Request to provided url for request id {request_id} reached HTTP connection timeout")
        