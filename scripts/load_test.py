"""Load test for the business card extraction API.

Measures whether the API handles requests concurrently by sending the same
batch of business card image URLs twice and comparing wall-clock times:

1. Sequential pass: one request at a time, each awaited before the next starts.
2. Concurrent pass: all requests created up front and awaited together
   with asyncio.gather on a single shared event loop.

If the API is truly asynchronous, the concurrent total should be close to
the slowest single request (or ceil(N / semaphore_size) waves of the model
call), far below the sequential total.

The batch contains card images from the Stanford business-card dataset.

For each pass, a report prints:
    - total duration in seconds
    - successful and failed responses, with the failing status codes
    - counts of business names, person names and contact numbers extracted
      (the string "none" is not counted as a value)

Matching counts between the two passes show that concurrency did not change
the results.

Configuration lives in set_config(): API endpoint, image host and file list,
and client timeout. The API must already be running, e.g.
`docker compose up -d`, before this script is started.

Usage:
    python scripts/load_test.py
"""

import asyncio
import json
import os
from time import time
import uuid
from httpx2 import AsyncClient
from collections import namedtuple

from dotenv import load_dotenv
load_dotenv()

def set_config():

    api_url = "http://localhost:8000/v1/contact_info_extract"

    base_url = "https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/"

    image_files = (
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg",
        "015.jpg",
        "016.jpg",
        "017.jpg",
        "018.jpg",
        "019.jpg",
        "020.jpg",
    )

    client_timeout = 600 # seconds
    
    ConfigStore = namedtuple("ConfigStore",["api_url","base_url","image_files","client_timeout"])
    config = ConfigStore(
        api_url=api_url,
        base_url=base_url,
        image_files=image_files,
        client_timeout=client_timeout,
    )
    return config

async def call_vlm_once(httpx2_client:AsyncClient,api_url:str,image_url:str):
    payload = {
        "request_id":str(uuid.uuid4()),
        "source_system":"testing_call",
        "card_url":image_url
    }
    return await httpx2_client.post(url=api_url,json=payload)

async def call_vlm_in_sequence(httpx2_client:AsyncClient, api_url:str, image_urls:list):
    responses = []
    for image_url in image_urls:
        responses.append(await call_vlm_once(httpx2_client,api_url,image_url))
    return responses

async def call_vlm_asynchronously(httpx2_client:AsyncClient, api_url:str, image_urls:list):
    vlm_call_tasks = []
    for image_url in image_urls:
        vlm_call_tasks.append(call_vlm_once(httpx2_client,api_url,image_url))
    responses = await asyncio.gather(*vlm_call_tasks)
    return responses

def create_report(response_list,duration):
    (successes, fails, businesses, people, contact_numbers) = 0,0,0,0,0
    fail_status_codes = []

    for resp in response_list:
        if resp.status_code == 200:
            successes+=1
            parsed_dict = json.loads(resp.text)
            if parsed_dict["business_name"].strip().lower() != "none":
                businesses += 1
            if parsed_dict["person_name"].strip().lower() != "none":
                people += 1
            contact_numbers += len(parsed_dict["contact_numbers"])
        else:
            fails+=1
            fail_status_codes.append(str(resp.status_code))
        
    print("Total Duration (s):", duration)
    print("Successful API Responses:", successes)
    print("Failed API Calls:",fails)
    if len(fail_status_codes) > 0:
        print("Fail Status Codes:",", ".join(fail_status_codes))
    print("Business Names Extracted:",businesses)
    print("Person Names Extracted:",people)
    print("Contact Numbers Extracted:",contact_numbers)
    print("-"*50)
    print("")

async def main():
    config = set_config()
    httpx2_client = AsyncClient(timeout=config.client_timeout)
    image_urls = [config.base_url+file for file in config.image_files]
    print("Image URLs to Extract")
    for i,url in enumerate(image_urls):
        print(f"{i+1}) {url}")
    print("")
    print("Total Count of Image URLs:",len(image_urls))
    print("")

    sync_start = time()
    responses_sync = await call_vlm_in_sequence(httpx2_client,config.api_url,image_urls)
    sync_end = time()
    sync_duration = sync_end-sync_start

    async_start = time()
    responses_async = await call_vlm_asynchronously(httpx2_client,config.api_url,image_urls)
    async_end = time()
    async_duration = async_end-async_start

    print("-- SYNCHRONOUS RESULTS --")
    create_report(responses_sync,sync_duration)

    print("-- ASYNCHRONOUS RESULTS --")
    create_report(responses_async,async_duration)

if __name__ == "__main__":
    asyncio.run(main())

