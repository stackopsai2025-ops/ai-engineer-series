# AI Engineer Series: Build an AI Customer Operations Agent

A free, 12-week, hands-on series where you learn AI engineering by building one real project from scratch.

**The project:** an AI Customer Operations Agent. A customer says, *"I want to return my headphones."* The agent understands the request, finds the order, reads the refund policy, and prepares a refund for a person to approve.

Each week adds one new skill. Each week has a clear goal and a checker, so you always know whether you're on track.

- Full StackOps AI playlist: https://www.youtube.com/playlist?list=PLBNtuS1JMxpc
- Full AI Engineer Bano Playlist in Hindi: https://www.youtube.com/playlist?list=PLfGRoypEM_U0


## The 12 weeks

| Week | Topic | What you build | Folder | Video |
| --- | --- | --- | --- | --- |
| 1 | Python and APIs | An order lookup that lists orders, requests returns with an API key, and handles every failure | [`week1-python-apis`](./week1-python-apis) | WEEK_1_VIDEO_LINK |
| 2 | LLM APIs and structured output | Customer message to validated, structured data, with retry | [`week2-llm-structured`](./week2-llm-structured) | WEEK_2_VIDEO_LINK |
| 3 | FastAPI and async | The agent as a web service | Coming soon | |
| 4 | RAG | Answer from the refund policy | Coming soon | |
| 5 | Databases | Store orders, requests and results | Coming soon | |
| 6 | Tool calling | The model decides which tool to use | Coming soon | |
| 7 | Workflows and MCP | A controlled workflow with human approval | Coming soon | |
| 8 | Evals | Measure whether the agent is any good | Coming soon | |
| 9 | Security | Protect the agent from bad input and misuse | Coming soon | |
| 10 | Docker, AWS and CI/CD | Ship it | Coming soon | |
| 11 | Monitoring and cost | Know what it's doing and what it costs | Coming soon | |
| 12 | Portfolio | Package the project so others can see it | Coming soon | |

The weekly topics may shift slightly as the series is made. The folders and videos above are the source of truth.

## How each week works

Every week folder has the same shape:

```
weekN-topic/
  README.md       Setup, how to run it, and what "done" means for that week
  start/          Your starting point, with TODO comments
  finished/       The finished version from the video
  check.py        Tells you whether you're done
  requirements.txt
```

1. Watch the video for that week.
2. Open `start/` and fill in the TODOs as you follow along.
3. Run `python check.py start` from the week's folder. It runs the same checks every time.
4. Stuck? Compare with `finished/`.

Some weeks add extra files, like a mock order service. Each week's own README lists them.

## Getting started

You need **Python 3.10 or newer** and a code editor. I use VS Code, but any editor works.

```bash
git clone REPO_URL
cd ai-engineer-series/week1-python-apis

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then follow that week's README. Use a fresh virtual environment for each week, because the requirements change.

Each week builds on the one before, so start at Week 1 and go in order.

## API keys: please read this

From Week 2 you need an API key from an AI provider. The series uses Anthropic, and a whole week costs a few cents.

- **Never type a key into your code.**
- **Never commit a key to git.** The `.gitignore` in this repo already ignores `.env` files.
- Keep keys in environment variables, in your terminal:

```bash
export ANTHROPIC_API_KEY=your-key-here        # Windows (cmd): set ANTHROPIC_API_KEY=your-key-here
```

If you ever paste a key somewhere public by mistake, delete it in your provider's console and create a new one.

The `check.py` files are written to work **without** an API key or internet, so you can check your work for free.

## The data is fictional

All orders, customers and products in this repo are made up. There are no real customer records.

## Help

- **Stuck on a step?** Check the "If you're stuck" list in that week's README, then compare with `finished/`.
- **Found a bug or a typo?** Open an issue and say which week and file.
- **Want to ask a question?** Comment on that week's video. I read every comment.

## Folder layout

```
ai-engineer-series/
  README.md
  .gitignore
  week1-python-apis/
  week2-llm-structured/
  ...                      one folder per week, added as each video is released
```

## License

LICENSE_NAME. See the `LICENSE` file for details.

---

Made by **Anoop Mishra** for **StackOps AI** and **AI Engineer Bano**. If this helps you, subscribe so the next week shows up.