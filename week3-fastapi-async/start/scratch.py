import asyncio
import time
from unittest import result

async def slow_call(n):
    time.sleep(1)
    return n

async def one_by_one():
    for n in range(5):
        await slow_call(n)

async def together():
    await asyncio.gather(*(slow_call(n) for n in range(5)))

for job in (one_by_one, together):
    started = time.perf_counter()
    asyncio.run(job())
    print(job.__name__, round(time.perf_counter() - started, 1), "seconds")