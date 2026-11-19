"""A tiny mock order API for the AI Engineer series (Week 1).

Run it in its own terminal and leave it running:

    python mock_api.py

Then open http://127.0.0.1:8000/orders/ORD-1001 in a browser.

It uses only the Python standard library, so there is nothing to install.
The data is fictional.
"""

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
PORT = 8000

ORDERS = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_id": "CUST-001",
        "product": "Wireless Headphones",
        "purchase_date": "2026-09-20",
        "status": "delivered",
        "price": 129.00,
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "customer_id": "CUST-002",
        "product": "Mechanical Keyboard",
        "purchase_date": "2026-08-02",
        "status": "delivered",
        "price": 89.50,
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "customer_id": "CUST-001",
        "product": "USB-C Charger",
        "purchase_date": "2026-10-12",
        "status": "shipped",
        "price": 24.99,
    },
    # A real order that the service is slow to return (see SLOW_ORDER below).
    "ORD-6000": {
        "order_id": "ORD-6000",
        "customer_id": "CUST-003",
        "product": "Laptop Stand",
        "purchase_date": "2026-10-01",
        "status": "delivered",
        "price": 39.00,
    },
}

# Special order numbers that misbehave on purpose, so you can practise
# handling failures.
OUTAGE_ORDER = "ORD-5000"  # the "service" returns a 503 error
SLOW_ORDER = "ORD-6000"  # the "service" takes 8 seconds to answer

# Creating a return needs an API key, sent as:  Authorization: Bearer demo-key-123
API_KEY = "demo-key-123"
RETURNS = []  # return requests created while the server is running


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body):
        payload = json.dumps(body).encode("utf-8")
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            # The client gave up waiting (for example, on the slow order).
            # That's expected, so don't print a scary error.
            pass

    def do_GET(self):
        url = urlparse(self.path)
        parts = url.path.strip("/").split("/")
        query = parse_qs(url.query)

        if parts == ["health"]:
            self._send(200, {"status": "ok"})
            return

        # GET /orders or GET /orders?status=shipped
        if parts == ["orders"]:
            orders = list(ORDERS.values())
            if "status" in query:
                orders = [o for o in orders if o["status"] == query["status"][0]]
            self._send(200, {"orders": orders})
            return

        if len(parts) == 2 and parts[0] == "orders":
            order_id = parts[1].upper()

            if order_id == OUTAGE_ORDER:
                self._send(503, {"error": "Order service is temporarily unavailable"})
                return

            if order_id == SLOW_ORDER:
                time.sleep(8)

            order = ORDERS.get(order_id)
            if order is None:
                self._send(404, {"error": f"Order {order_id} not found"})
                return

            self._send(200, order)
            return

        self._send(404, {"error": "Not found"})

    def do_POST(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if parts != ["returns"]:
            self._send(404, {"error": "Not found"})
            return

        if self.headers.get("Authorization") != f"Bearer {API_KEY}":
            self._send(401, {"error": "Missing or invalid API key"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self._send(400, {"error": "Body must be valid JSON"})
            return

        order_id = str(body.get("order_id", "")).upper()
        reason = str(body.get("reason", "")).strip()
        if not order_id or not reason:
            self._send(400, {"error": "order_id and reason are required"})
            return
        if order_id not in ORDERS:
            self._send(404, {"error": f"Order {order_id} not found"})
            return

        record = {
            "return_id": f"RET-{len(RETURNS) + 1:04d}",
            "order_id": order_id,
            "reason": reason,
            "status": "requested",
        }
        RETURNS.append(record)
        self._send(201, record)

    def log_message(self, fmt, *args):
        # Print one short line per request, so viewers can see calls arrive.
        print(f"{self.command} {self.path} -> {args[1]}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Mock order API running at http://{HOST}:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
