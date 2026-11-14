import asyncio

def set_config():
    "Set constants used by this script where where needed"
    pass

async def call_vlm_once():
    "Use httpx2 client to make a post request to the VLM"
    pass

async def call_vlm_in_sequence():
    "Force the script to call each image url synchronously"
    pass

async def call_vlm_asynchronously():
    "Allow the VLM calls to be made simultaneously"
    pass

def create_report():
    "Create a printout of the function results - time taken, failures/successes, etc."
    pass

async def main():
    pass

if __name__ == "__main__":
    asyncio.run(main())



"Reference - asynchronous functions with and without forced synchronousness"
from asyncio import sleep
from time import time

async def do_some_sleeping(val):
    await sleep(val)

# FORCED SYNCHRONOUSNESS
start = time()
for val in range(10):
    await do_some_sleeping(val)
end = time()
print(end-start)

# FULLY ASYNCHRONOUS
start = time()
sleepy_tasks = []
for val in range(10):
    sleepy_tasks.append(do_some_sleeping(val))
await gather(*sleepy_tasks)
end = time()
print(end-start)
