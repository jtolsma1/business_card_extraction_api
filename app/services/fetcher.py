"""
Check the host against the allowlist (it must include the web.cs.wpi.edu host) and GET with your descriptive User-Agent.
Don’t follow redirects blindly. A redirect can send you to a host you never allowed.
Reject private IP ranges, enforce the size cap, and verify the content type.
Return the bytes, the media type, and the download time.
"""
from time import time,sleep
from loguru import logger
from app.errors import (
    ImageMaxSizeExceeded, 
    ImageNotFound, 
    InvalidImageHost, 
    InvalidImageTypeError
)

def validate_image_host(image_url,allowed_image_hosts):
    for host in allowed_image_hosts:
        if host in image_url:
            return True
    return False


async def run_image_byte_fetch(
        httpx2_client,
        request_id,
        image_url:str,
        max_bytes:float,
        allowed_image_hosts:list[str],
        allowed_image_types:list[str],
        max_attempts:int
        ):
    
    start = time()

    # Validate image host before executing image download
    is_valid_host = validate_image_host(image_url,allowed_image_hosts)
    if is_valid_host is False:
        raise InvalidImageHost(f"Image url passed for request id {request_id} does not match any host on the image host whitelist")
    
    for _ in range(max_attempts):
        success = False
        try:
            # Stream image download and break if maximum image size is exceeded
            async with httpx2_client.stream("GET",image_url) as response:

                if response.status_code != 200:
                    raise ImageNotFound(f"Request to provided url for request id {request_id} returned failure status code {response.status_code}")

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
            if type(error).__name__ == "ImageNotFound" and response.status_code:
                logger.warning(f"Image fetch for request id {request_id} returned {response.status_code}; retrying")
                sleep(0.5)
                continue
            else:
                raise error

    
    end = time()
    download_time_ms = end - start
    
    if success:
        return request_id, buf, image_type, download_time_ms
    else:
        raise ImageNotFound(f"Request to provided url for request id {request_id} returned failure status code {response.status_code}")
        