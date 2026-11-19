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


# TODO 5: write MessageIn, the shape of the request body.
#   one field, `message: str`, at least 1 and at most 500 characters:
#       message: str = Field(min_length=1, max_length=500)
#   plus a @field_validator("message") that rejects a message that is only
#   spaces (raise ValueError) and returns value.strip() otherwise.
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


# TODO 1: add GET /health. It returns {"status": "ok"}.
@app.get("/health")
async def health():
    return {"status": "ok"}


# TODO 6: add POST /extract (response_model=CustomerRequest).
# Take `body: MessageIn` and `ask=Depends(get_ask)`.
# Call `await extract_request(body.message, ask=ask)` and return the result.
# If it raises LLMError or ExtractionError, raise
# HTTPException(status_code=502, detail=str(error)).

@app.post("/extract", response_model=CustomerRequest)
async def extract(body: MessageIn, ask=Depends(get_ask)):
    try:
        return await extract_request(body.message, ask=ask)
    except (LLMError, ExtractionError) as error:
        raise HTTPException(status_code=502, detail=str(error))


# TODO 7: add POST /handle (response_model=HandleOut).
# Take body, ask=Depends(get_ask), lookup=Depends(get_order_lookup).
#   1. extract the request exactly like /extract (502 on failure)
#   2. no order_id?  return HandleOut(request=request, note="No order number found in the message.")
#   3. otherwise `order = await lookup(request.order_id)`
#      OrderError -> HTTPException(status_code=error.status_code, detail=str(error))
#   4. return HandleOut(request=request, order=order)

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


# TODO 8: add POST /batch (response_model=BatchOut).
# Take `body: BatchIn` and `ask=Depends(get_ask)`.
#   outcomes = await asyncio.gather(
#       *(extract_request(m, ask=ask) for m in body.messages),
#       return_exceptions=True,
#   )
# Then build one BatchItem per message (zip body.messages with outcomes):
#   a CustomerRequest         -> BatchItem(message=m, ok=True, request=outcome)
#   LLMError/ExtractionError  -> BatchItem(message=m, ok=False, error=str(outcome))
#   anything else             -> BatchItem(message=m, ok=False, error="Something went wrong.")
# Return BatchOut(results=results).

@app.post("/batch", response_model=BatchOut)
async def batch(body: BatchIn, ask=Depends(get_ask)):
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

