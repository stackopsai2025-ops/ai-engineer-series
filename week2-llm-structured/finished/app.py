"""Provided: the command-line app. You don't need to change this file.

Usage:
    python app.py "I want to return my headphones"
    python app.py --fake "I want to return my headphones"     (no API key needed)
"""

import sys

from extract import ExtractionError, extract_request
from fake_llm import fake_ask
from llm import LLMError, ask_model
from orders import OrderError, format_order, get_order

USAGE = (
    "Usage:\n"
    '  python app.py "I want to return my headphones"\n'
    '  python app.py --fake "I want to return my headphones"   (no API key needed)'
)


def run(args: list) -> str:
    use_fake = "--fake" in args
    words = [a for a in args if a != "--fake"]
    if not words:
        raise ExtractionError(USAGE)

    ask = fake_ask if use_fake else ask_model
    request = extract_request(" ".join(words), ask=ask)

    lines = [request.model_dump_json(indent=2)]
    if request.order_id:
        lines += ["", format_order(get_order(request.order_id))]
    else:
        lines += ["", "No order number in the message, so there is nothing to look up yet."]
    return "\n".join(lines)


def main() -> int:
    try:
        print(run(sys.argv[1:]))
    except (LLMError, ExtractionError, OrderError) as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
