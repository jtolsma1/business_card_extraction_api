import os
import sys
import asyncio
from time import time

# async def square(x):
#     await asyncio.sleep(x)
#     return x**2

# def print_square(square_result):
#     print(f"The squared number is {square_result}")

# async def do_everything(x):
#     square_result = await square(x)
#     print_square(square_result)

# async def main(y):
#     start = time()
#     async with asyncio.TaskGroup() as tg:
#         for x in range(1,y+1):
#             tg.create_task(do_everything(x))
#     end = time()
#     print(f"Execution of {y} squaring operations took {end-start} seconds")

# if __name__ == "__main__":
#     asyncio.run(main(5))


from httpx2 import AsyncClient

from dotenv import load_dotenv
load_dotenv()
PROJECT_DIR = os.environ.get("PROJECT_DIR")
sys.path.insert(0,PROJECT_DIR)

from app.services.fetcher import run_image_byte_fetch
from app.settings import get_settings

async def main(client:AsyncClient,iterable,settings):
    start = time()
    tasks = []
    for request_id,url in iterable:
        image_fetch_task = asyncio.create_task(run_image_byte_fetch(
            httpx2_client=client,
            request_id=request_id,
            image_url=url,
            max_bytes=settings.MAX_IMAGE_BYTES,
            allowed_image_hosts=settings.ALLOWED_IMAGE_HOSTS,
            allowed_image_types=settings.ALLOWED_IMAGE_TYPES,
            max_attempts=2
            ))
        
        tasks.append(image_fetch_task)
        
    results = await asyncio.gather(*tasks)

    end = time()
    for image_result in results:
        print("Request ID:",image_result[0])
        print("Image Type:",image_result[2])
        print("Fetch Time:",image_result[3])
        print("-"*50)
    print("Completion time:",end-start)

if __name__ == "__main__":
    httpx2_client = AsyncClient()
    settings = get_settings()
    request_ids = ["A1","B2","C3","D4","E5"]
    urls = [
    "https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/001.jpg",
    "https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/002.jpg",
    "https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/003.jpg",
    "https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/004.jpg",
    "https://web.cs.wpi.edu/~claypool/mmsys-dataset/2011/stanford/mvs_images/business_cards/Reference/005.jpg",
    ]   

    iterable = zip(request_ids,urls)

    asyncio.run(main(httpx2_client,iterable,settings))
