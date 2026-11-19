"""Provided: a pretend model, so you can run the service without an API key.

It is NOT smart. It looks for a few keywords and answers in the same JSON
shape the real model is asked for. It also WAITS before answering, the way a
real model does, so you can see what async buys you.

Turn it on with:   FAKE_LLM=1 uvicorn main:app --port 8001 --reload
Change the wait:   FAKE_DELAY=2   (seconds, default 1)
"""

import asyncio
import json
import os
import re

PRODUCTS = ["headphones", "keyboard", "charger", "laptop stand"]


async def fake_ask(system: str, user: str) -> str:
    # asyncio.sleep lets other requests run while we wait.
    # time.sleep would freeze the whole server. That is the whole lesson.
    await asyncio.sleep(float(os.environ.get("FAKE_DELAY", "1")))

    text = user.lower()

    match = re.search(r"ord-\d{4}", text)
    order_id = match.group(0).upper() if match else None
    product = next((p for p in PRODUCTS if p in text), None)

    reason = None
    if "because" in text:
        reason = user[text.index("because") + len("because"):].split("\n")[0].strip(" .")

    if "return" in text or "refund" in text or "send back" in text:
        intent = "return"
    elif "where is" in text or "status" in text or "track" in text:
        intent = "order_status"
    else:
        intent = "other"

    return json.dumps(
        {"intent": intent, "order_id": order_id, "product": product, "reason": reason}
    )
