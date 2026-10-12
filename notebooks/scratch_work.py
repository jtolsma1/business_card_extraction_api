import asyncio
from time import time

async def square(x):
    await asyncio.sleep(x)
    return x**2

def print_square(square_result):
    print(f"The squared number is {square_result}")

async def do_everything(x):
    square_result = await square(x)
    print_square(square_result)

async def main(y):
    start = time()
    async with asyncio.TaskGroup() as tg:
        for x in range(1,y+1):
            tg.create_task(do_everything(x))
    end = time()
    print(f"Execution of {y} squaring operations took {end-start} seconds")

if __name__ == "__main__":
    asyncio.run(main(5))
