"""
POST /v1/extractions, with an async def handler. It stays thin: start a monotonic timer, make a request ID, call the fetcher, call the extractor, and assemble the response with timings. No business logic lives here.
"""
from app.schemas import LookupResponse, LookupRequest
from app.dependencies import get_httpx2_client,get_anthropic_client,get_semaphore, get_settings
from fastapi import APIRouter, Depends
from app.services.fetcher import run_image_byte_fetch
from app.services.extractor import run_vlm_extraction_with_fake_extractor
import time

router = APIRouter(prefix="/v1")

@router.get("/health",tags=["health"])
async def liveliness_check():
    return {"status":"ok"}

@router.post("/contact_info_extract",response_model=LookupResponse,tags=["contact_info_extract"])
async def extract_contact_info(
    body:LookupRequest,
    httpx2_client=Depends(get_httpx2_client),
    anthropic_client=Depends(get_anthropic_client),
    semaphore=Depends(get_semaphore),
    settings=Depends(get_settings),
    ):
    
    start = time.time()

    buf, image_type, download_time = await run_image_byte_fetch(
        httpx2_client=httpx2_client,
        request_id=body.request_id,
        image_url=body.card_url,
        max_bytes=settings.MAX_IMAGE_BYTES,
        allowed_image_hosts=settings.ALLOWED_IMAGE_HOSTS,
        allowed_image_types=settings.ALLOWED_IMAGE_TYPES,
        max_attempts=settings.MAX_ATTEMPTS,
    )

    business_name,person_name,contact_numbers,vlm_response_time = await run_vlm_extraction_with_fake_extractor(
        anthropic_client=anthropic_client,
        sem=semaphore,
        request_id=body.request_id,
        image_bytes=buf,
        image_type=image_type,
        vlm_model=settings.CLAUDE_MODEL,
        max_attempts=settings.MAX_ATTEMPTS,
        fake_extractor=settings.USE_FAKE_EXTRACTOR,
    )

    end = time.time()

    return LookupResponse(
        request_id=body.request_id,
        business_name=business_name,
        person_name=person_name,
        contact_numbers=contact_numbers,
        download_time=download_time,
        vlm_response_time=vlm_response_time,
        total_response_time=end-start,
    )


