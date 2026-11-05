"""Week 2 (starter): turn a customer message into validated, structured data.

Build this up step by step in the video. Every TODO is one step.
"""

import json
import re
from typing import Callable, Literal, Optional

from pydantic import BaseModel, ValidationError, field_validator

from llm import ask_model

MAX_ATTEMPTS = 2


class ExtractionError(Exception):
    """Raised with a message that is safe to show to a person."""


SYSTEM_PROMPT = """You read messages from customers of an online shop and pull out the details.
Reply with ONE JSON object and nothing else. No explanation, no code fences.

The object has exactly these keys:
- "intent": "return" if they want to return or refund something,
            "order_status" if they ask where an order is or what its status is,
            "other" for anything else.
- "order_id": the order number if they gave one (it looks like ORD-1234), otherwise null.
- "product": the product they mention, in plain words, otherwise null.
- "reason": why they want a return, in a few words, otherwise null.

Never invent an order number or a reason. If it is not in the message, use null."""


def clean_json(text):
    """Models sometimes wrap JSON in code fences. Strip them."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()

class CustomerRequest(BaseModel):
    intent: Literal["return", "order_status", "other"]
    order_id: Optional[str] = None
    product: Optional[str] = None
    reason: Optional[str] = None

    @field_validator("order_id")
    @classmethod
    def check_order_id(cls, value):
        if value is None:
            return None
        value = value.strip().upper()
        if not re.fullmatch(r"ORD-\d{4}", value):
            raise ValueError("order_id must look like ORD-1234, or be null")
        return value


def parse_request(text):
    try:
        data = json.loads(clean_json(text))
    except ValueError:
        raise ExtractionError("The reply was not valid JSON.")

    try:
        return CustomerRequest.model_validate(data)
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(str(p) for p in e['loc']) or 'reply'}: {e['msg']}"
            for e in error.errors()
        )
        raise ExtractionError(f"The reply did not match the schema ({problems}).")


def extract_request(message, ask=ask_model):
    if not message.strip():
        raise ExtractionError("Please type a customer message.")

    prompt = message
    last_error = None

    for _ in range(MAX_ATTEMPTS):
        reply = ask(SYSTEM_PROMPT, prompt)
        try:
            return parse_request(reply)
        except ExtractionError as error:
            last_error = error
            prompt = (
                f"{message}\n\n"
                f"Your last reply was:\n{reply}\n\n"
                f"It was rejected: {error}\n"
                "Reply again with only the corrected JSON object."
            )

    raise ExtractionError(
        f"Couldn't get a valid answer from the model after {MAX_ATTEMPTS} tries. {last_error}"
    )

