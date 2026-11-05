"""Week 2 (starter): one function that asks the model a question.

Build this up step by step in the video. Every TODO is one step.
"""

import os

import anthropic


DEFAULT_MODEL = "claude-haiku-5-5"   # a small, cheap model is plenty for this
MAX_TOKENS = 500                     # the longest reply we will pay for
TIMEOUT_SECONDS = 30


class LLMError(Exception):
    """Raised with a message that is safe to show to a person."""


def ask_model(system, user):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMError("Missing ANTHROPIC_API_KEY environment variable")
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
        raise LLMError("The API key is being rate limited. Try again later.")
    except anthropic.APITimeoutError as e:
        raise LLMError("The API request timed out. Try again later.")
    except anthropic.APIConnectionError as e:
        raise LLMError("The API request failed to connect. Try again later.")
    except anthropic.APIStatusError as e:
        raise LLMError(f"The API request failed with status {e.status_code}. Try again later.")

    return "".join(block.text for block in response.content if block.type == "text")


if __name__ == "__main__":
    from extract import SYSTEM_PROMPT, clean_json
    import json
    message = "Hi, I want to return my headphones because they are too small. Order ORD-1001."
    reply = ask_model(SYSTEM_PROMPT, message)
    data = json.loads(clean_json(reply))
    print(data)
    print(type(data))   



