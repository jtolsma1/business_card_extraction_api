from loguru import logger
from base64 import b64encode
from pydantic import BaseModel
from asyncio import sleep
from random import uniform
from time import time
from anthropic.types import ParsedMessage
from app.errors import AppError,VLMRateLimit,ProcessTimeout
from anthropic import AuthenticationError,RateLimitError,APITimeoutError,InternalServerError

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
    """
    Extracts information described in the prompt from the business card image using the VLM. Executes multiple retries.

    @param anthropic_client: async Anthropic client used to access VLM
    @param sem: semaphore created to limit simultaneous VLM calls
    @param request_id: request id passed in the API request body; used for logging
    @param image_bytes: image bytes loaded and validated using the fetcher service
    @param vlm_model: model type (e.g.'claude-haiku-5') used to complete extraction
    @param max_attemps: number of attempts made to load image before giving up
    @returns: business name, person name, contact numbers on card image
    """

    image_b64 = b64encode(image_bytes).decode("utf-8")
    prompt = _get_prompt()
    last_error = None

    """
    RETRY POLICY
    - If authentication error, log quietly and return a generic error to the caller
    - If rate limit (429) or internal server error (500), retry until retries are exhausted
    - For all other errors: fail immediately
    """

    for _ in range(max_attempts):
        try:
            async with sem:
                response = await anthropic_client.messages.parse(
                    model=vlm_model,
                    max_tokens=1024,
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
            if isinstance(error,AuthenticationError):
                logger.error(f"VLM extraction for request id {request_id} encountered an authentication error; check Claude credentials in env file")
                raise AppError("VLM extraction encountered an internal server error; contact administrator for assistance")
            if isinstance(error,RateLimitError):
                last_error = error
                logger.warning(f"VLM extraction operation for request id {request_id} encountered rate limit error; backing off and retrying")
                await sleep(1)
                continue
            elif isinstance(error,InternalServerError):
                last_error = error
                logger.warning(f"VLM extraction encountered an internal server error (status 500); retrying")
                await sleep(0.5)
                continue
            elif isinstance(error,APITimeoutError):
                raise ProcessTimeout(f"VLM extraction operation for request id {request_id} encountered a timeout error and will not be retried")
            else:
                raise error
    
    if isinstance(last_error,RateLimitError):
        raise VLMRateLimit("VLM extraction encountered rate limit error and could not be completed")
    if isinstance(last_error,InternalServerError):
        raise AppError("VLM extraction encountered an internal server error; contact administrator for assistance")


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
    """
    Wrapper for run_vlm_extraction that adds a 'fake extractor'. When fake extractor flag is true (set in env file), 
    vlm extraction function does not call the model and instead sleeps for a random interval to simulate vlm call.
    This saves tokens when testing wiring and asynch functionality.

    Net-new params on top of run_vlm_extraction:
    @param fake_extractor: boolean that turns fake extractor on and off
    @param fake_extractor_sleep_range: range of time, in fractional seconds, to sleep as VLM simulation
    @returns: same as run_vlm_extraction plus vlm extraction time
    """
    
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
