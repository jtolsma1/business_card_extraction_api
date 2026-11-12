"""
Takes image bytes and a media type, base64-encodes them, and acquires the semaphore. The semaphore wraps only the Claude call, so downloads aren’t throttled.
It calls your existing async Claude helper and maps Anthropic’s exception types onto your domain exceptions. Retry policy: let the SDK’s built-in retries handle transient errors, back off on 429, and fail fast on 401. Don’t rebuild the client.
The media type is a parameter, not a hardcoded image/jpeg.
Fake mode sleeps for the configured delay and returns canned data, with no network involved.
"""
import json
from loguru import logger
from base64 import b64encode
from pydantic import BaseModel
from asyncio import sleep
from random import uniform
from time import time
from anthropic.types import ParsedMessage
from app.errors import VLMRateLimit, ResourceConnectionFailure, ImageMaxSizeExceeded

class BusinessCardData(BaseModel):
    business_name:str
    person_name:str
    contact_numbers:list[str]

FAKE_EXTRACTOR_SLEEP_RANGE = (2.4,4.1)
FAKE_EXTRACTOR_DATA = {""}

def _get_prompt():
    return """
    From the business card shown, extract:
    1. "business_name" = the name of the business shown on the card. If the card does not contain a business name (i.e. is for an indivual person not affiliated with a named business), return 'None'.
    2. "person_name" = the name of the person shown on the card. If the card does not contain a person's name (i.e. is generic for a business and not specific to an individual person), return 'None'.
    3. "contact_numbers" = all phone/fax numbers shown on the card. Format each contact number as '+00-1111111', where the zeroes in this example represent the country code (1-3 digits) and the ones represent the actual contact number, which can be any length. If no country code is stated, infer it from the address shown (if given) and, failing that, assume the US country code of +1. Return as a Python list of strings containing all contact numbers, e.g. ['+00-1111111','+00-1111111', ...]. The array can contain any number of elements. If the card contains no contact numbers, return [] (empty list).
    """

async def run_vlm_extraction(
        anthropic_client,
        sem,
        request_id:str,
        image_bytes:bytes,
        image_type:str,
        download_time:float,
        vlm_model:str,
        max_attempts:int
        ):

    image_b64 = b64encode(image_bytes).decode("utf-8")
    prompt = _get_prompt()
    last_error = None
    for _ in range(max_attempts):
        try:
            async with sem:
                response = await anthropic_client.messages.parse(
                    model=vlm_model,
                    max_tokens=200,
                    output_format=BusinessCardData,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": image_type,
                                        "data": image_b64,
                                    },
                                },
                                {
                                    "type":"text",
                                    "text":prompt,
                                }
                            ],
                        }
                    ],
                )

 

                if isinstance(response,ParsedMessage):
                    data = response.parsed_output

                    if data is not None:
                        vlm_response = data.model_dump()
                        vlm_response.update({"download_time":download_time})
                        return vlm_response


        except Exception as error:
            last_error = error
            continue
    raise Exception(f"VLM extraction for image passed in request id {request_id} failed due to: {last_error}")


async def run_vlm_extraction_with_fake_extractor(
        anthropic_client,
        sem,
        request_id:str,
        image_bytes:bytes,
        image_type:str,
        download_time:float,
        vlm_model:str,
        max_attempts:int,
        fake_extractor:bool,
        ):
    
    start = time()
    if fake_extractor is True:
        await sleep(uniform(FAKE_EXTRACTOR_SLEEP_RANGE[0],FAKE_EXTRACTOR_SLEEP_RANGE[1]))
        end = time()
        return {
            "business_name":"Test Business, Inc.",
            "person_name":"John Doe",
            "contact_numbers":["+1-555-555-1234","+1-555-555-5555"],
            "download_time":download_time,
            "vlm_extraction_time":end-start,
        }

    else:
        vlm_response = await run_vlm_extraction(
            anthropic_client,
            sem,
            request_id,
            image_bytes,
            image_type,
            download_time,
            vlm_model,
            max_attempts
            )
        end = time()
        vlm_response.update({"vlm_extraction_time":end-start})
        return vlm_response
