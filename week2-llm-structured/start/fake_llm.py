"""Provided: a pretend model, so you can run the app without an API key.

It is NOT smart. It looks for a few keywords and answers in the same JSON
shape the real model is asked for. Use it with:  python app.py --fake "..."
"""

import json
import re

PRODUCTS = ["headphones", "keyboard", "charger", "laptop stand"]


def fake_ask(system: str, user: str) -> str:
    text = user.lower()

    match = re.search(r"ord-\d{4}", text)
    order_id = match.group(0).upper() if match else None
    product = next((p for p in PRODUCTS if p in text), None)

    reason = None
    if "because" in text:
        reason = user[text.index("because") + len("because"):].strip(" .")

    if "return" in text or "refund" in text or "send back" in text:
        intent = "return"
    elif "where is" in text or "status" in text or "track" in text:
        intent = "order_status"
    else:
        intent = "other"

    return json.dumps(
        {"intent": intent, "order_id": order_id, "product": product, "reason": reason}
    )
