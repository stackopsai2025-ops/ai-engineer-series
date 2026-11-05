# Week 2: LLMs and Structured Output

Part of the 12-week series: build an **AI Customer Operations Agent**.

Last week you wrote Python that talks to an order API. This week the AI model
arrives. You'll send a customer's message to a language model and get back
**structured data your code can trust**, even when the model replies badly.

**Done when:** `python check.py start` says all 16 checks passed, and
`python app.py "I want to return my headphones"` prints a structured request.

## What's here

| File | What it is |
| --- | --- |
| `mock_api.py` | The Week 1 order service. Run it and leave it running. |
| `start/llm.py` | **Yours:** one function that asks the model. TODOs 1 and 2. |
| `start/extract.py` | **Yours:** schema, prompt, parsing, retry. TODOs 3 to 7. |
| `start/app.py`, `orders.py`, `fake_llm.py` | Provided. You don't change these. |
| `finished/` | The finished version from the video. |
| `check.py` | Free, offline checks. They pretend to be the model. |

## Setup

You need Python 3.10 or newer and a finished Week 1 (or just use the files here).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Your API key

Get a key from the Anthropic Console (console.anthropic.com), and add a few
dollars of credit. This whole week costs a few cents.

**Never put the key in your code or commit it to git.** Set it in your terminal:

```bash
export ANTHROPIC_API_KEY=your-key-here        # Windows (cmd): set ANTHROPIC_API_KEY=your-key-here
```

Optional: pick a different model with `ANTHROPIC_MODEL` (the default is a small, cheap one).

## Run it

**Terminal 1:** start the order service and leave it running:

```bash
python mock_api.py
```

**Terminal 2:**

```bash
cd start
python app.py "I want to return my headphones"
python app.py "Where is my order ORD-1003?"
```

No key yet? Use the pretend model. It is not smart, it just lets you see the
whole flow:

```bash
python app.py --fake "Where is my order ORD-1003?"
```

## Check your work

From the repo root:

```bash
python check.py start
```

The checks need no API key and no internet. To also try your code on the real
model (costs a fraction of a cent): `python check.py start --live`

## If you're stuck

- **"Set the ANTHROPIC_API_KEY environment variable first"**: set the key in the *same* terminal you run the app from.
- **"The API key was rejected"**: the key is wrong, or has no credit.
- **`ModuleNotFoundError`**: activate your virtual environment, then `pip install -r requirements.txt`.
- **"Can't reach the order service"**: Terminal 1 isn't running `mock_api.py`.
- **Still stuck**: compare with `finished/`.

The data in this repo is fictional.
