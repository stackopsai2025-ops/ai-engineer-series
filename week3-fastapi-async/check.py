"""Check your Week 3 solution. No API key and no internet needed.

    python check.py start       (checks the code in start/)
    python check.py finished    (checks the finished version)

The checks talk to your app in memory (no server to start), pretend to be the
model, and start the practice order API (mock_api.py) for you if it isn't
already running.
"""

import asyncio
import inspect
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

args = [a for a in sys.argv[1:] if not a.startswith("--")]
folder = Path(args[0]) if args else Path("start")
root = Path(__file__).resolve().parent

if not (folder / "main.py").exists():
    print(f"Can't find {folder}/main.py. Run this from the repo root: python check.py start")
    sys.exit(2)

sys.path.insert(0, str(folder.resolve()))
os.environ.pop("FAKE_LLM", None)
os.environ.pop("ANTHROPIC_MODEL", None)

import anthropic  # noqa: E402
import httpx  # noqa: E402

import extract  # noqa: E402
import llm  # noqa: E402
import main  # noqa: E402
import orders  # noqa: E402

results = []


def check(name, test):
    try:
        passed, detail = test()
    except Exception as error:  # a crash in your code is a failed check, not a crash of the checker
        passed, detail = False, f"{type(error).__name__}: {error}"
    results.append(passed)
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    if not passed and detail:
        print(f"       got: {detail!r}")


# ---------- helpers ----------

GOOD = '{"intent": "return", "order_id": "ORD-1001", "product": "headphones", "reason": "too small"}'
ORDER = {"order_id": "ORD-1001", "product": "Wireless Headphones", "status": "delivered"}


def scripted(*replies, delay=0.0):
    """A fake async model that gives the replies in order. A reply that is an Exception is raised."""
    calls = []

    async def ask(system, user):
        calls.append(user)
        if delay:
            await asyncio.sleep(delay)
        reply = replies[min(len(calls) - 1, len(replies) - 1)]
        if isinstance(reply, Exception):
            raise reply
        return reply

    ask.calls = calls
    return ask


def call(method, path, json=None, ask=None, lookup=None):
    """Send one request to the app, in memory. Returns the response."""

    async def go():
        main.app.dependency_overrides.clear()
        if ask is not None:
            main.app.dependency_overrides[main.get_ask] = lambda: ask
        if lookup is not None:
            main.app.dependency_overrides[main.get_order_lookup] = lambda: lookup
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, json=json)

    try:
        return asyncio.run(go())
    finally:
        main.app.dependency_overrides.clear()


def make_error(cls, status=None):
    error = cls.__new__(cls)
    Exception.__init__(error, "boom")
    if status is not None:
        error.status_code = status
    return error


class FakeAsyncClient:
    def __init__(self, behaviour, record):
        self._behaviour = behaviour
        self._record = record
        self.messages = SimpleNamespace(create=self._create)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def close(self):
        pass

    async def _create(self, **kwargs):
        self._record.update(kwargs)
        if isinstance(self._behaviour, Exception):
            raise self._behaviour
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._behaviour)])


def with_client(behaviour, key="test-key"):
    record = {}
    real = anthropic.AsyncAnthropic
    anthropic.AsyncAnthropic = lambda **kwargs: FakeAsyncClient(behaviour, record)
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key
    else:
        os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        return asyncio.run(llm.ask_model_async("SYSTEM TEXT", "USER TEXT")), record
    except Exception as error:
        return error, record
    finally:
        anthropic.AsyncAnthropic = real


def port_open(port):
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


mock = None
if not port_open(8000):
    mock = subprocess.Popen(
        [sys.executable, str(root / "mock_api.py")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        if port_open(8000):
            break
        time.sleep(0.1)

# ---------- the app: basics ----------


def t_health():
    r = call("GET", "/health")
    return r.status_code == 200 and r.json() == {"status": "ok"}, (r.status_code, r.text)


def t_extract_ok():
    r = call("POST", "/extract", {"message": "Return my headphones ORD-1001"}, ask=scripted(GOOD))
    body = r.json() if r.status_code == 200 else {}
    ok = r.status_code == 200 and body.get("intent") == "return" and body.get("order_id") == "ORD-1001"
    return ok, (r.status_code, r.text)


def t_empty():
    r = call("POST", "/extract", {"message": ""}, ask=scripted(GOOD))
    return r.status_code == 422, (r.status_code, r.text)


def t_blank():
    r = call("POST", "/extract", {"message": "     "}, ask=scripted(GOOD))
    return r.status_code == 422, (r.status_code, r.text)


def t_too_long():
    r = call("POST", "/extract", {"message": "x" * 501}, ask=scripted(GOOD))
    return r.status_code == 422, (r.status_code, r.text)


def t_model_down():
    ask = scripted(llm.LLMError("The model took too long to respond. Try again."))
    r = call("POST", "/extract", {"message": "hello"}, ask=ask)
    ok = r.status_code == 502 and "too long" in r.text
    return ok, (r.status_code, r.text)


def t_garbage():
    r = call("POST", "/extract", {"message": "hello"}, ask=scripted("not json", "still not json"))
    return r.status_code == 502, (r.status_code, r.text)


check("GET /health says ok", t_health)
check("POST /extract returns the structured request", t_extract_ok)
check("An empty message is rejected with 422", t_empty)
check("A blank message is rejected with 422", t_blank)
check("A message over 500 characters is rejected with 422", t_too_long)
check("If the model fails, /extract answers 502 with the reason", t_model_down)
check("If the model keeps sending garbage, /extract answers 502", t_garbage)

# ---------- async conversion ----------


def t_extract_async():
    return inspect.iscoroutinefunction(extract.extract_request), "extract_request is not 'async def'"


def t_llm_async():
    return inspect.iscoroutinefunction(llm.ask_model_async), "ask_model_async is not 'async def'"


def t_llm_works():
    result, record = with_client("Hello there")
    ok = (
        result == "Hello there"
        and record.get("system") == "SYSTEM TEXT"
        and record.get("messages") == [{"role": "user", "content": "USER TEXT"}]
        and isinstance(record.get("max_tokens"), int)
        and bool(record.get("model"))
    )
    return ok, (result, record)


def t_llm_errors():
    result, _ = with_client("x", key=None)
    if not (isinstance(result, llm.LLMError) and "ANTHROPIC_API_KEY" in str(result)):
        return False, f"missing key -> {result!r}"
    for cls, status in [
        (anthropic.AuthenticationError, 401),
        (anthropic.RateLimitError, 429),
        (anthropic.APITimeoutError, None),
        (anthropic.APIConnectionError, None),
        (anthropic.InternalServerError, 500),
    ]:
        result, _ = with_client(make_error(cls, status))
        if not isinstance(result, llm.LLMError):
            return False, f"{cls.__name__} -> {result!r}"
    return True, None


def t_orders_async():
    return inspect.iscoroutinefunction(orders.get_order), "get_order is not 'async def'"


def t_order_found():
    order = asyncio.run(orders.get_order("ORD-1001"))
    return isinstance(order, dict) and order.get("order_id") == "ORD-1001", order


def t_order_missing():
    try:
        asyncio.run(orders.get_order("ORD-9999"))
    except orders.OrderError as error:
        return error.status_code == 404, (str(error), error.status_code)
    return False, "no OrderError was raised"


check("extract_request is async", t_extract_async)
check("ask_model_async is async", t_llm_async)
check("ask_model_async sends the right request and returns the text", t_llm_works)
check("ask_model_async turns every failure into an LLMError", t_llm_errors)
check("get_order is async", t_orders_async)
check("get_order finds a real order (practice API)", t_order_found)
check("get_order raises OrderError with status 404 for an unknown order", t_order_missing)

# ---------- /handle ----------


def t_handle_order():
    async def lookup(order_id):
        return ORDER

    r = call("POST", "/handle", {"message": "Return ORD-1001"}, ask=scripted(GOOD), lookup=lookup)
    body = r.json() if r.status_code == 200 else {}
    ok = r.status_code == 200 and body.get("order") == ORDER and body["request"]["intent"] == "return"
    return ok, (r.status_code, r.text)


def t_handle_no_order():
    reply = '{"intent": "other", "order_id": null, "product": null, "reason": null}'

    async def lookup(order_id):
        raise AssertionError("lookup should not run without an order id")

    r = call("POST", "/handle", {"message": "Hi there"}, ask=scripted(reply), lookup=lookup)
    body = r.json() if r.status_code == 200 else {}
    ok = r.status_code == 200 and body.get("order") is None and bool(body.get("note"))
    return ok, (r.status_code, r.text)


def t_handle_unknown():
    async def lookup(order_id):
        raise orders.OrderError(f"Order {order_id} was not found.", status_code=404)

    r = call("POST", "/handle", {"message": "Return ORD-1001"}, ask=scripted(GOOD), lookup=lookup)
    return r.status_code == 404 and "not found" in r.text, (r.status_code, r.text)


def t_handle_order_down():
    async def lookup(order_id):
        raise orders.OrderError("Can't reach the order service.")

    r = call("POST", "/handle", {"message": "Return ORD-1001"}, ask=scripted(GOOD), lookup=lookup)
    return r.status_code == 502, (r.status_code, r.text)


check("/handle extracts the request and looks up the order", t_handle_order)
check("/handle without an order number returns a note and no order", t_handle_no_order)
check("/handle answers 404 when the order does not exist", t_handle_unknown)
check("/handle answers 502 when the order service is down", t_handle_order_down)

# ---------- /batch ----------


def t_batch_order():
    async def ask(system, user):
        if "headphones" in user:
            return GOOD
        return '{"intent": "order_status", "order_id": "ORD-1002", "product": null, "reason": null}'

    r = call("POST", "/batch", {"messages": ["return headphones", "where is ORD-1002", "return headphones again"]}, ask=ask)
    items = r.json()["results"] if r.status_code == 200 else []
    intents = [i.get("request", {}).get("intent") for i in items]
    return intents == ["return", "order_status", "return"], (r.status_code, r.text)


def t_batch_partial():
    async def ask(system, user):
        if "boom" in user:
            raise llm.LLMError("The model took too long to respond. Try again.")
        return GOOD

    r = call("POST", "/batch", {"messages": ["fine", "boom", "fine too"]}, ask=ask)
    items = r.json()["results"] if r.status_code == 200 else []
    flags = [i.get("ok") for i in items]
    ok = r.status_code == 200 and flags == [True, False, True] and "too long" in (items[1].get("error") or "")
    return ok, (r.status_code, r.text)


def t_batch_empty():
    r = call("POST", "/batch", {"messages": []}, ask=scripted(GOOD))
    return r.status_code == 422, (r.status_code, r.text)


def t_batch_concurrent():
    ask = scripted(GOOD, delay=0.5)
    started = time.perf_counter()
    r = call("POST", "/batch", {"messages": [f"message {i}" for i in range(6)]}, ask=ask)
    took = time.perf_counter() - started
    ok = r.status_code == 200 and len(r.json()["results"]) == 6 and took < 1.5
    return ok, f"{took:.1f}s (6 calls of 0.5s should take about 0.5s, not 3s)"


check("/batch returns one result per message, in order", t_batch_order)
check("/batch: one failing message does not fail the others", t_batch_partial)
check("/batch rejects an empty list with 422", t_batch_empty)
check("/batch runs the model calls at the same time", t_batch_concurrent)

# ---------- done ----------

if mock:
    mock.terminate()

passed = sum(results)
print(f"\n{passed} of {len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)
