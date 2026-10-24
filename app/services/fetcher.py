"""
Check the host against the allowlist (it must include the web.cs.wpi.edu host) and GET with your descriptive User-Agent.
Don’t follow redirects blindly. A redirect can send you to a host you never allowed.
Reject private IP ranges, enforce the size cap, and verify the content type.
Return the bytes, the media type, and the download time.
"""
from time import time
from httpx2 import AsyncClient
from errors import (
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


async def fetch_image_bytes(
        httpx2_client:AsyncClient,
        image_url:str,
        max_bytes:float,
        allowed_image_hosts:list[str],
        allowed_image_types:list[str]
        ):
    
    start = time()

    # Validate image host before executing image download
    is_valid_host = validate_image_host(image_url,allowed_image_hosts)
    if is_valid_host is False:
        raise InvalidImageHost("Image url does not match any host on the image host whitelist")
    
    # Stream image download and break if maximum image size is exceeded
    async with httpx2_client.stream("GET",image_url) as response:

        if response.status_code != 200:
            raise ImageNotFound(f"Request to provided url returned failure status code {response.status_code}")

        image_type = response.headers["Content-Type"] 
        if image_type not in allowed_image_types:
            raise InvalidImageTypeError(f"Image URL directs to unsupported image type: {image_type}")

        buf = bytearray()
        async for chunk in response.aiter_bytes():
            buf.extend(chunk)

            if len(buf) > max_bytes:
                raise ImageMaxSizeExceeded(f"Image exceeds maximum size limit of {max_bytes} bytes and will not be downloaded")
            
    end = time()
    download_time_ms = (end - start)*1000

    return buf, image_type, download_time_ms
        