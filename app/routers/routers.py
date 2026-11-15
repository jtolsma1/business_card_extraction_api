import time
from fastapi import APIRouter, Depends
from loguru import logger

from app.schemas import LookupResponse, LookupRequest
from app.dependencies import get_httpx2_client,get_anthropic_client,get_semaphore, get_settings
from app.services.fetcher import run_image_byte_fetch
from app.services.extractor import run_vlm_extraction_with_fake_extractor


router = APIRouter(prefix="/v1")

@router.get("/health",tags=["health"],summary="Returns health status of the app")
async def liveliness_check():
    return {"status":"ok"}

@router.post("/contact_info_extract",
    response_model=LookupResponse,
    tags=["contact_info_extract"],
    summary="Get the business name, person name, and contact numbers from a business card image",
    responses={
    422: {"description":"Image not found at the url provided or the url provided is not on the allowlist"},
    413: {"description":"Image maximum size exceeded"},
    415: {"description":"Image type is not valid for vlm extraction"},
    504: {"description":"Image download or VLM extraction encountered timeout condition"},
    503: {"description":"VLM encountered a rate limit condition and was unable to respond"},
    },
)

async def extract_contact_info(
    body:LookupRequest,
    httpx2_client=Depends(get_httpx2_client),
    anthropic_client=Depends(get_anthropic_client),
    semaphore=Depends(get_semaphore),
    settings=Depends(get_settings),
    ):
    """
    Returns the business card fields extracted by the VLM. 

    When given an image URL, validates the host against a host allowlist, loads the image as bytes, passes to
    the VLM, and returns the extracted fields along with time taken for each step. Inputs are:

    - **request_id**: unique alphanumeric identifier for the request
    - **source_system**: system making the request
    - **card_url**: full url of the business card image 
    - **returns**: business name, person name, contact numbers, and time taken for each step

    Errors are returned as {"status_code","message","request_id"}.

    """
    
    start = time.time()
    logger.info(f"Starting extraction for request id = {body.request_id} from source system = {body.source_system}")
    logger.info(f"URL passed for request id {body.request_id} = {body.card_url}")
    image_download_headers = {"User-Agent":settings.FETCH_USER_AGENT}

    buf, image_type, download_time = await run_image_byte_fetch(
        httpx2_client=httpx2_client,
        request_id=body.request_id,
        image_url=body.card_url,
        max_bytes=settings.MAX_IMAGE_BYTES,
        headers=image_download_headers,
        allowed_image_hosts=settings.ALLOWED_IMAGE_HOSTS,
        allowed_image_types=settings.ALLOWED_IMAGE_TYPES,
        max_attempts=settings.MAX_ATTEMPTS, 
    ) # type: ignore

    business_name,person_name,contact_numbers,vlm_response_time = await run_vlm_extraction_with_fake_extractor(
        anthropic_client=anthropic_client,
        sem=semaphore,
        request_id=body.request_id,
        image_bytes=buf,
        image_type=image_type,
        vlm_model=settings.CLAUDE_MODEL,
        max_attempts=settings.MAX_ATTEMPTS,
        fake_extractor=settings.USE_FAKE_EXTRACTOR,
        fake_extractor_sleep_range=settings.FAKE_EXTRACTOR_SLEEP_RANGE,
    )

    end = time.time()

    logger.info(f"Extraction for request id = {body.request_id} from source system = {body.source_system} successfully completed")

    return LookupResponse(
        request_id=body.request_id,
        business_name=business_name,
        person_name=person_name,
        contact_numbers=contact_numbers,
        download_time=download_time,
        vlm_response_time=vlm_response_time,
        total_response_time=end-start,
    )


