# Week 3: FastAPI and async

Part of the **AI Engineer** series. This week you turn the Week 2 extractor into a **web service** and learn **async**, so many slow model calls can run at the same time.

Watch the video: `WEEK_3_VIDEO_LINK`

## What you build

A small service with four endpoints:

| Endpoint | What it does |
|---|---|
| `GET /health` | Says the service is alive |
| `POST /extract` | Customer message in, structured request out (Week 2, as an API) |
| `POST /handle` | Extract, then look up the order (Week 1 + Week 2 together) |
| `POST /batch` | Many messages at once, handled **concurrently** |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

You do **not** need an API key to finish this week. `FAKE_LLM=1` turns on a pretend model that waits like a real one.

## Folders

- `start/` has TODOs 1 to 8. This is where you work.
- `finished/` is the finished version. Peek if you get stuck.
- `check.py` tests your code. `mock_api.py` is the practice order API from Week 1.

## Work through it

```bash
python check.py start
```

At the start most checks fail. Fix one TODO at a time and run it again. The checks don't need a key, a server or the internet. They start `mock_api.py` for you if it isn't running.

| TODO | File | What |
|---|---|---|
| 1 | `main.py` | `GET /health` |
| 2 | `llm.py` | `ask_model_async` with `AsyncAnthropic` |
| 3 | `extract.py` | `extract_request` becomes `async` |
| 4 | `orders.py` | async `get_order` with `httpx` |
| 5 | `main.py` | `MessageIn` request model |
| 6 | `main.py` | `POST /extract` and error mapping |
| 7 | `main.py` | `POST /handle` |
| 8 | `main.py` | `POST /batch` with `asyncio.gather` |

## Run the service

Use three terminals, from inside `start/` (or `finished/`):

```bash
# 1. the practice order API (port 8000)
python ../mock_api.py

# 2. your service (port 8001)
FAKE_LLM=1 FAKE_DELAY=1 uvicorn main:app --port 8001 --reload
# Windows PowerShell:  $env:FAKE_LLM="1"; $env:FAKE_DELAY="1"; uvicorn main:app --port 8001 --reload

# 3. fire 10 requests at once
python loadtest.py 10
```

Open http://127.0.0.1:8001/docs to try every endpoint in the browser.

Done right, 10 requests that each wait 1 second finish in about **1 second**, not 10.

## Using the real model

```bash
export ANTHROPIC_API_KEY="your-key"   # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key"
uvicorn main:app --port 8001 --reload
```

Never put your key in the code or in git.

## Status codes this service uses

| Code | Meaning here |
|---|---|
| 200 | It worked |
| 404 | The order doesn't exist |
| 422 | The request body is wrong (FastAPI and Pydantic do this for you) |
| 502 | The model or the order service failed |

## Next: Week 4

RAG: give the agent your refund policy so it answers from your documents.
