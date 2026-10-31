# Week 1: Python and APIs

Part of the 12-week series: build an **AI Customer Operations Agent**.

This week has no AI yet. You'll write a Python program that talks to an API:
it looks up an order, lists orders, and requests a return with an API key. It
handles every way a request can fail, and never shows a raw error.

**Done when:** `python check.py start` says all 11 checks passed.

## What's here

| File | What it is |
| --- | --- |
| `mock_api.py` | A fake order service. Run it and leave it running. Nothing to install. |
| `start/order_lookup.py` | Your starting point, with TODOs. |
| `finished/order_lookup.py` | The finished version from the video. |
| `check.py` | Runs your program and checks the "done when" tests. |

## Setup

You need Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run it

**Terminal 1**: start the mock order service and leave it running:

```bash
python mock_api.py
```

Check it in a browser: <http://127.0.0.1:8000/orders/ORD-1001>

**Terminal 2**: work on your program:

```bash
cd start
python order_lookup.py ORD-1001
python order_lookup.py list shipped
export ORDER_API_KEY=demo-key-123        # Windows: set ORDER_API_KEY=demo-key-123
python order_lookup.py return ORD-1001 "Too small"
```

When you think you're done, check your work (from the repo root):

```bash
python check.py start
```

## Orders to try

| Order | What happens |
| --- | --- |
| `ORD-1001`, `ORD-1002`, `ORD-1003` | Normal orders |
| `ORD-9999` | Doesn't exist, so you get a 404 |
| `ORD-5000` | The service is "down", so you get a 503 |
| `ORD-6000` | The service is slow (8 seconds), so you need a timeout |

The API key for the mock service is `demo-key-123`. In real projects, keep keys in
environment variables, never in your code or on GitHub.

## If you're stuck

- **"Can't reach the order service"**: Terminal 1 isn't running `mock_api.py`.
- **`ModuleNotFoundError: requests`**: activate your virtual environment, then `pip install -r requirements.txt`.
- **Port 8000 already in use**: stop the other program, or change `PORT` in `mock_api.py` and `BASE_URL` in your code.
- **Still stuck**: compare with `finished/order_lookup.py`.

The data in this repo is fictional.
