"""
POST /v1/extractions, with an async def handler. It stays thin: start a monotonic timer, make a request ID, call the fetcher, call the extractor, and assemble the response with timings. No business logic lives here.
"""
from app.schemas import LookupResponse, LookupRequest
from app.dependencies import get_httpx2_client,get_anthropic_client,get_semaphore
from fastapi import APIRouter, Depends
import time

router = APIRouter(prefix="/v1")

@router.get("/health")
async def liveliness_check():
    return {"status":"ok"}

@router.post("/contact_info_extract",response_model=LookupResponse)
async def extract_contact_info(
    body:LookupRequest,
    httpx2_client=Depends(get_httpx2_client),
    anthropic_client=Depends(get_anthropic_client),
    semaphore=Depends(get_semaphore)
    ):
    
    start = time.time()

    # VLM function goes here

    end = time.time()

    return LookupResponse(
        request_id=body.request_id,
        business_name=business_name,
        person_name=person_name,
        contact_numbers=contact_numbers,
        response_time_ms=end-start,
    )


