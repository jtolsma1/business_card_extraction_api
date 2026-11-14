"""
Takes image bytes and a media type, base64-encodes them, and acquires the semaphore. The semaphore wraps only the Claude call, so downloads aren’t throttled.
It calls your existing async Claude helper and maps Anthropic’s exception types onto your domain exceptions. Retry policy: let the SDK’s built-in retries handle transient errors, back off on 429, and fail fast on 401. Don’t rebuild the client.
The media type is a parameter, not a hardcoded image/jpeg.
Fake mode sleeps for the configured delay and returns canned data, with no network involved.
"""
from loguru import logger
from base64 import b64encode
from pydantic import BaseModel
from asyncio import sleep
from random import uniform
from time import time
from anthropic.types import ParsedMessage
from app.errors import VLMRateLimit, ProcessTimeout
from anthropic import RateLimitError,APITimeoutError,InternalServerError

class BusinessCardData(BaseModel):
    business_name:str
    person_name:str
    contact_numbers:list[str]

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
        vlm_model:str,
        max_attempts:int
        ):

    image_b64 = b64encode(image_bytes).decode("utf-8")
    prompt = _get_prompt()
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
                        business_name = data.business_name
                        person_name = data.person_name
                        contact_numbers = data.contact_numbers
                        return business_name,person_name,contact_numbers


        except Exception as error:
            if isinstance(error,RateLimitError):
                logger.warning(f"VLM extraction operation for request id {request_id} encountered rate limit error; backing off and retrying")
                await sleep(1)
                continue
            elif isinstance(error,InternalServerError):
                logger.warning(f"VLM extraction encountered an internal server error (status 500); retrying")
                await sleep(0.5)
                continue
            elif isinstance(error,APITimeoutError):
                raise ProcessTimeout(f"VLM extraction operation for request id {request_id} encountered a timeout error and will not be retried")
            else:
                raise error


async def run_vlm_extraction_with_fake_extractor(
        anthropic_client,
        sem,
        request_id:str,
        image_bytes:bytes,
        image_type:str,
        vlm_model:str,
        max_attempts:int,
        fake_extractor:bool,
        fake_extractor_sleep_range,
        ):
    
    start = time()
    if fake_extractor is True:
        fake_extractor_sleep_range = fake_extractor_sleep_range.split(",")
        sleep_values = [float(val) for val in fake_extractor_sleep_range]
        await sleep(uniform(sleep_values[0],sleep_values[1]))
        end = time()
        vlm_response_time = end-start
        return (
            "Test Business, Inc.",
            "John Doe",
            ["+1-555-555-1234","+1-555-555-5555"],
            vlm_response_time,
        )

    else:
        business_name,person_name,contact_numbers = await run_vlm_extraction(
            anthropic_client,
            sem,
            request_id,
            image_bytes,
            image_type,
            vlm_model,
            max_attempts,
        ) # type: ignore
        end = time()
        vlm_response_time = end-start
        return business_name,person_name,contact_numbers,vlm_response_time
