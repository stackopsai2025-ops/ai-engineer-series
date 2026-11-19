"""Week 3 (finished): the agent as a web service.

Run it:   FAKE_LLM=1 uvicorn main:app --port 8001 --reload
Docs:     http://127.0.0.1:8001/docs   (port 8000 belongs to mock_api.py)
"""

import asyncio
import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from extract import CustomerRequest, ExtractionError, extract_request
from fake_llm import fake_ask
from llm import LLMError, ask_model_async
from orders import OrderError, get_order

app = FastAPI(title="AI Customer Operations Agent")


# ---------- what comes in, what goes out ----------


class MessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)

    @field_validator("message")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("message must not be blank")
        return value.strip()


class HandleOut(BaseModel):
    request: CustomerRequest
    order: Optional[dict] = None
    note: Optional[str] = None


class BatchIn(BaseModel):
    messages: list[str] = Field(min_length=1, max_length=20)


class BatchItem(BaseModel):
    message: str
    ok: bool
    request: Optional[CustomerRequest] = None
    error: Optional[str] = None


class BatchOut(BaseModel):
    results: list[BatchItem]


# ---------- dependencies: the pieces tests can swap out ----------


def get_ask():
    """The model function. FAKE_LLM=1 gives you the free pretend model."""
    return fake_ask if os.environ.get("FAKE_LLM") == "1" else ask_model_async


def get_order_lookup():
    return get_order


# ---------- endpoints ----------


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/extract", response_model=CustomerRequest)
async def extract(body: MessageIn, ask=Depends(get_ask)):
    try:
        return await extract_request(body.message, ask=ask)
    except (LLMError, ExtractionError) as error:
        raise HTTPException(status_code=502, detail=str(error))


@app.post("/handle", response_model=HandleOut)
async def handle(body: MessageIn, ask=Depends(get_ask), lookup=Depends(get_order_lookup)):
    try:
        request = await extract_request(body.message, ask=ask)
    except (LLMError, ExtractionError) as error:
        raise HTTPException(status_code=502, detail=str(error))

    if request.order_id is None:
        return HandleOut(request=request, note="No order number found in the message.")

    try:
        order = await lookup(request.order_id)
    except OrderError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error))

    return HandleOut(request=request, order=order)


@app.post("/batch", response_model=BatchOut)
async def batch(body: BatchIn, ask=Depends(get_ask)):
    # Start every extraction at once. return_exceptions=True means one failure
    # comes back as a value instead of cancelling the rest.
    outcomes = await asyncio.gather(
        *(extract_request(message, ask=ask) for message in body.messages),
        return_exceptions=True,
    )

    results = []
    for message, outcome in zip(body.messages, outcomes):
        if isinstance(outcome, CustomerRequest):
            results.append(BatchItem(message=message, ok=True, request=outcome))
        elif isinstance(outcome, (LLMError, ExtractionError)):
            results.append(BatchItem(message=message, ok=False, error=str(outcome)))
        else:
            results.append(BatchItem(message=message, ok=False, error="Something went wrong."))
    return BatchOut(results=results)
