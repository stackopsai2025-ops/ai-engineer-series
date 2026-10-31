"""Check your Week 1 solution against the "done when" tests.

1. In one terminal:   python mock_api.py
2. In another:        python check.py start      (checks start/order_lookup.py)
                      python check.py finished   (checks finished/order_lookup.py)

It runs your program the way a person would and checks what it prints.
"""

import os
import subprocess
import sys
from pathlib import Path

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
script = folder / "order_lookup.py"

if not script.exists():
    print(f"Can't find {script}")
    sys.exit(2)


def run(*args, key=None):
    env = {k: v for k, v in os.environ.items() if k != "ORDER_API_KEY"}
    if key:
        env["ORDER_API_KEY"] = key
    result = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


results = []


def check(name, passed, detail=""):
    results.append(passed)
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name}")
    if not passed and detail:
        print(f"       got: {detail!r}")


code, out = run("ORD-1001")
check(
    "A valid order prints product, purchase date, and status",
    code == 0 and "Wireless Headphones" in out and "2026-09-20" in out and "delivered" in out,
    out,
)

code, out = run("ord-1001")
check("Lowercase order numbers still work", code == 0 and "Wireless Headphones" in out, out)

code, out = run("ORD-9999")
check(
    "An unknown order gives a clear message, not a crash",
    "Traceback" not in out and "not found" in out.lower(),
    out,
)

code, out = run("ORD-5000")
check(
    "A service outage (503) gives a clear message, not a crash",
    "Traceback" not in out and out != "",
    out,
)

code, out = run("ORD-6000")
check(
    "A slow service times out with a clear message, not a hang",
    "Traceback" not in out and ("too long" in out.lower() or "timed out" in out.lower() or "slow" in out.lower()),
    out,
)

code, out = run()
check("No order number prints usage help", "usage" in out.lower() and "Traceback" not in out, out)

code, out = run("list", "shipped")
check(
    "list shipped shows only shipped orders",
    code == 0 and "ORD-1003" in out and "ORD-1001" not in out,
    out,
)

code, out = run("return", "ORD-1001", "Too small")
check(
    "A return with no API key tells you to set ORDER_API_KEY",
    "Traceback" not in out and "ORDER_API_KEY" in out and code != 0,
    out,
)

code, out = run("return", "ORD-1001", "Too small", key="wrong-key")
check(
    "A return with a wrong key says the key was rejected",
    "Traceback" not in out and "rejected" in out.lower() and code != 0,
    out,
)

code, out = run("return", "ORD-1001", "Too small", key="demo-key-123")
check(
    "A return with the right key succeeds and shows a return number",
    code == 0 and "RET-" in out,
    out,
)

code, out = run("return", "ORD-9999", "Too small", key="demo-key-123")
check(
    "A return for an unknown order gives a clear message",
    "Traceback" not in out and "not found" in out.lower(),
    out,
)

print()
if all(results):
    print(f"All {len(results)} checks passed. Week 1 is done.")
    sys.exit(0)
print(f"{results.count(False)} of {len(results)} checks failed.")
sys.exit(1)
