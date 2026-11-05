"""Week 2 (finished): one function that asks the model a question.

Everything else in the series that talks to a model goes through here.
"""

import os

import anthropic

DEFAULT_MODEL = "claude-haiku-5-5"   # a small, cheap model is plenty for this
MAX_TOKENS = 500                     # the longest reply we will pay for
TIMEOUT_SECONDS = 30


class LLMError(Exception):
    """Raised with a message that is safe to show to a person."""


def ask_model(system: str, user: str) -> str:
    """Send one message to the model and return its text reply."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("Set the ANTHROPIC_API_KEY environment variable first.")

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS)

    try:
        response = client.messages.create(
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
