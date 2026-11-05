"""Check your Week 2 solution. No API key and no internet needed.

    python check.py start        (checks start/llm.py and start/extract.py)
    python check.py finished     (checks the finished version)
    python check.py start --live (also tries your code on the real model; needs ANTHROPIC_API_KEY)

The checks pretend to be the model, so they are free, fast, and always give the
same answer. They test YOUR code: how it handles good replies, bad replies and
failures.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

args = [a for a in sys.argv[1:] if not a.startswith("--")]
live = "--live" in sys.argv
folder = Path(args[0]) if args else Path("start")

if not (folder / "extract.py").exists():
    print(f"Can't find {folder}/extract.py. Run this from the repo root: python check.py start")
    sys.exit(2)

sys.path.insert(0, str(folder.resolve()))
os.environ.pop("ANTHROPIC_MODEL", None)

import anthropic  # noqa: E402

import extract  # noqa: E402
import llm  # noqa: E402

results = []


def check(name, test):
    try:
        passed, detail = test()
    except Exception as error:  # a crash in the student's code is a failed check
        passed, detail = False, f"{type(error).__name__}: {error}"
    results.append(passed)
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    if not passed and detail:
        print(f"       got: {detail!r}")


# ---------- helpers ----------


def make_error(cls, status=None):
    """Build an Anthropic exception without needing a real HTTP response."""
    error = cls.__new__(cls)
    Exception.__init__(error, "boom")
    if status is not None:
        error.status_code = status
    return error


class FakeClient:
    """Stands in for anthropic.Anthropic. Records the call, then replies or raises."""

    def __init__(self, behaviour, record):
        self._behaviour = behaviour
        self._record = record
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self._record.update(kwargs)
        if isinstance(self._behaviour, Exception):
            raise self._behaviour
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._behaviour)])


def with_client(behaviour, key="test-key"):
    """Run llm.ask_model against a fake client. Returns (result_or_exception, call_record)."""
    record = {}
    real_client = anthropic.Anthropic
    anthropic.Anthropic = lambda **kwargs: FakeClient(behaviour, record)
    if key:
        os.environ["ANTHROPIC_API_KEY"] = key
    else:
        os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        return llm.ask_model("SYSTEM TEXT", "USER TEXT"), record
    except Exception as error:
        return error, record
    finally:
        anthropic.Anthropic = real_client


def scripted(*replies):
    """A fake model that gives the replies in order, and remembers what it was asked."""
    calls = []

    def ask(system, user):
        calls.append((system, user))
        return replies[min(len(calls) - 1, len(replies) - 1)]

    ask.calls = calls
    return ask


GOOD = '{"intent": "return", "order_id": "ORD-1001", "product": "headphones", "reason": "too small"}'

# ---------- llm.py ----------


def t_missing_key():
    result, record = with_client("hi", key=None)
    ok = isinstance(result, llm.LLMError) and "ANTHROPIC_API_KEY" in str(result) and not record
    return ok, result


def t_success():
    result, record = with_client("Hello there")
    ok = (
        result == "Hello there"
        and record.get("system") == "SYSTEM TEXT"
        and record.get("messages") == [{"role": "user", "content": "USER TEXT"}]
        and isinstance(record.get("max_tokens"), int)
        and bool(record.get("model"))
    )
    return ok, (result, record)


def error_case(cls, status=None, word=None):
    def test():
        result, _ = with_client(make_error(cls, status))
        ok = isinstance(result, llm.LLMError) and str(result).strip() != ""
        if ok and word:
            ok = word in str(result).lower()
        return ok, f"{type(result).__name__}: {result}"

    return test


check("A missing API key tells you to set ANTHROPIC_API_KEY", t_missing_key)
check("A good call sends the system prompt and message, and returns the text", t_success)
check("A rejected key gives a clear message", error_case(anthropic.AuthenticationError, 401, "key"))
check("A rate limit gives a clear message", error_case(anthropic.RateLimitError, 429))
check("A timeout gives a clear message", error_case(anthropic.APITimeoutError))
check("A connection failure gives a clear message", error_case(anthropic.APIConnectionError))
check("Any other API error gives a clear message", error_case(anthropic.InternalServerError, 500))

# ---------- extract.py ----------


def t_valid():
    ask = scripted(GOOD)
    r = extract.extract_request("I want to return my headphones", ask=ask)
    ok = (r.intent, r.order_id, r.product, r.reason) == ("return", "ORD-1001", "headphones", "too small")
    return ok and len(ask.calls) == 1, r


def t_fences():
    r = extract.extract_request("x", ask=scripted("```json\n" + GOOD + "\n```"))
    return r.intent == "return" and r.order_id == "ORD-1001", r


def t_nulls():
    r = extract.extract_request("hi", ask=scripted('{"intent": "other", "order_id": null, "product": null, "reason": null}'))
    return r.intent == "other" and r.order_id is None, r


def t_uppercase():
    r = extract.extract_request("x", ask=scripted('{"intent": "order_status", "order_id": "ord-1003"}'))
    return r.order_id == "ORD-1003", r


def t_retry_works():
    ask = scripted("Sure! Here you go: not json at all", GOOD)
    r = extract.extract_request("return my headphones", ask=ask)
    second_prompt = ask.calls[1][1] if len(ask.calls) > 1 else ""
    ok = len(ask.calls) == 2 and r.intent == "return" and "not json at all" in second_prompt
    return ok, f"calls={len(ask.calls)}"


def t_bad_intent():
    ask = scripted('{"intent": "refund", "order_id": null}')
    try:
        extract.extract_request("x", ask=ask)
    except extract.ExtractionError as error:
        return len(ask.calls) == 2 and str(error).strip() != "", f"calls={len(ask.calls)}"
    return False, "no ExtractionError was raised"


def t_bad_order_id():
    ask = scripted('{"intent": "return", "order_id": "ORDER 7"}')
    try:
        extract.extract_request("x", ask=ask)
    except extract.ExtractionError:
        return True, ""
    return False, "an order_id like 'ORDER 7' was accepted"


def t_empty():
    ask = scripted(GOOD)
    try:
        extract.extract_request("   ", ask=ask)
    except extract.ExtractionError:
        return len(ask.calls) == 0, f"calls={len(ask.calls)}"
    return False, "no ExtractionError was raised"


def t_prompt():
    p = extract.SYSTEM_PROMPT
    ok = all(w in p for w in ["JSON", "intent", "order_id", "product", "reason", "null"])
    return ok, "the prompt should mention JSON, the four keys, and null"


check("A good reply becomes a CustomerRequest", t_valid)
check("JSON wrapped in code fences is accepted", t_fences)
check("Missing details can be null", t_nulls)
check("A lowercase order number is fixed to uppercase", t_uppercase)
check("A bad reply is retried once, and the retry shows the model its mistake", t_retry_works)
check("An intent that isn't allowed is rejected after the retry", t_bad_intent)
check("An order number that isn't like ORD-1234 is rejected", t_bad_order_id)
check("An empty message is rejected without calling the model", t_empty)
check("The system prompt asks for JSON with the four keys", t_prompt)

# ---------- optional: the real model ----------

if live:
    print("\nLive checks (these call the real model and cost a fraction of a cent):")
    cases = [
        ("I want to return my headphones", "return", None),
        ("Where is my order ORD-1003?", "order_status", "ORD-1003"),
        ("What time do you open?", "other", None),
    ]

    def live_case(message, intent, order_id):
        def test():
            r = extract.extract_request(message)
            return r.intent == intent and r.order_id == order_id, r

        return test

    for message, intent, order_id in cases:
        check(f"Live: {message!r}", live_case(message, intent, order_id))

print()
if all(results):
    print(f"All {len(results)} checks passed. Week 2 is done.")
    sys.exit(0)
print(f"{results.count(False)} of {len(results)} checks failed.")
sys.exit(1)
