"""Week 3: the Week 2 model call, made async.

Same job, same errors. The only difference is that while we wait for the
model, Python is free to do other work.
"""

import os

import anthropic

DEFAULT_MODEL = "claude-haiku-5-5"
MAX_TOKENS = 500
TIMEOUT_SECONDS = 30


class LLMError(Exception):
    """Raised with a message that is safe to show to a person."""


# TODO 2: write ask_model_async(system, user) -> str.
#
# It is your Week 2 ask_model with three changes:
#   - it is `async def`
#   - the client is anthropic.AsyncAnthropic, used as: async with anthropic.AsyncAnthropic(...) as client:
#   - the call is awaited:  response = await client.messages.create(...)
# Keep everything else: the key check, the model name, the five except blocks,
# and the empty-reply check. Look at your Week 2 llm.py.

async def ask_model_async(system: str, user: str) -> str:
    """Send one message to the model and return its text reply."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("Set the ANTHROPIC_API_KEY environment variable first.")

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

    try:
        async with anthropic.AsyncAnthropic(api_key=api_key, timeout=TIMEOUT_SECONDS) as client:
            response = await client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
    except anthropic.AuthenticationError:
        raise LLMError("The API key was rejected. Check ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        raise LLMError("The model service is busy or you hit a rate limit. Try again soon.")
    except anthropic.APITimeoutError:
        raise LLMError("The model took too long to respond. Try again.")
    except anthropic.APIConnectionError:
        raise LLMError("Can't reach the model service. Check your internet connection.")
    except anthropic.APIStatusError as error:
        raise LLMError(f"The model service had a problem (status {error.status_code}).")

    text = "".join(block.text for block in response.content if block.type == "text")
    if not text.strip():
        raise LLMError("The model sent back an empty reply.")
    return text