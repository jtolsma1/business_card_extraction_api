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

class BusinessCardData(BaseModel):
    business_name:str
    person_name:str
    contact_numbers:list[str]

FAKE_EXTRACTOR_SLEEP_RANGE = (1.4,3.1)
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
        request_id:str,
        image_bytes:bytes,
        image_type:str,
        vlm_model:str,
        max_attempts:int
        ):

    image_b64 = b64encode(image_bytes)
    prompt = _get_prompt()
    last_error = None
    for _ in range(max_attempts):
        try:
            message = await anthropic_client.messages.parse(
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
            vlm_response = json.loads(message.content[0].text)
            return vlm_response
        except Exception as error:
            last_error = error
            continue
    raise Exception(f"VLM extraction for image passed in request id {request_id} failed due to: {last_error}")


async def run_vlm_extraction_with_fake_extractor(
        anthropic_client,
        request_id:str,
        image_bytes:bytes,
        image_type:str,
        vlm_model:str,
        max_attempts:int,
        fake_extractor:bool,
        ):
    if fake_extractor is True:
        await sleep(uniform(FAKE_EXTRACTOR_SLEEP_RANGE[0],FAKE_EXTRACTOR_SLEEP_RANGE[1]))
        return {
            "business_name":"Test Business, Inc.",
            "person_name":"John Doe",
            "contact_numbers":["+1-555-555-1234","+1-555-555-5555"]
        }

    else:
        vlm_response = await run_vlm_extraction(anthropic_client,request_id,image_bytes,image_type,vlm_model,max_attempts)
