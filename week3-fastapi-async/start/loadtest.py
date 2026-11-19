"""Provided: fire many requests at your running service at the same time.

    python loadtest.py            (10 requests to /extract)
    python loadtest.py 25         (25 requests)

Start the service first, in another terminal:
    FAKE_LLM=1 FAKE_DELAY=1 uvicorn main:app --port 8001
With async working, 10 requests that each wait 1 second finish in about
1 second in total. With blocking code they take about 10.
"""

import asyncio
import sys
import time

import httpx

URL = "http://127.0.0.1:8001/extract"
MESSAGE = "I want to return my headphones from ORD-1001 because they are too small"


async def main(count: int) -> None:
    async with httpx.AsyncClient(timeout=60) as client:
        started = time.perf_counter()
        replies = await asyncio.gather(
            *(client.post(URL, json={"message": MESSAGE}) for _ in range(count))
        )
        total = time.perf_counter() - started

    ok = sum(1 for r in replies if r.status_code == 200)
    print(f"{count} requests, {ok} succeeded, {total:.1f} seconds in total")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 10))
