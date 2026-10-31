"""Week 1 (starter): talk to the mock order API.

Build this up step by step in the video. Every TODO is one step.

Usage:
    python order_lookup.py ORD-1001
    python order_lookup.py list [STATUS]
    python order_lookup.py return ORD-1001 "reason"     (needs ORDER_API_KEY)
"""

from datetime import date
import os
import sys
from urllib import response

import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 3

class OrderError(Exception):
    """Raised with a message that is safe to show to a person."""

def call_api(method, path, **kwargs):
    try:
        return requests.request(
            method, f"{BASE_URL}{path}", timeout=TIMEOUT_SECONDS, **kwargs
        )
    except requests.exceptions.ConnectionError:
        raise OrderError("Can't reach the order service. Is mock_api.py running?")
    except requests.exceptions.Timeout:
        raise OrderError("The order service took too long to respond. Try again.") 

def get_order(order_id):
    url = f"{BASE_URL}/orders/{order_id}"
    response = call_api("GET", f"/orders/{order_id}")
    if response.status_code == 404:
        raise OrderError(f"Order {order_id} was not found.")
    if response.status_code != 200:
        raise OrderError(f"The order service had a problem (status {response.status_code}).")
    return read_json(response)  

def read_json(response):
    try:
        return response.json()
    except ValueError:
        raise OrderError("The order service sent a reply we couldn't read.")

def list_orders(status=None):
    params = {"status": status} if status else {}
    response = call_api("GET", "/orders", params=params)
    if response.status_code != 200:
        raise OrderError(f"The order service had a problem (status {response.status_code}).")
    return read_json(response)["orders"]


def create_return(order_id, reason):
    api_key = os.environ.get("ORDER_API_KEY")
    if not api_key:
        raise OrderError("Set the ORDER_API_KEY environment variable first.")

    response = call_api(
        "POST",
        "/returns",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"order_id": order_id, "reason": reason},
    )

    if response.status_code == 401:
        raise OrderError("The API key was rejected. Check ORDER_API_KEY.")
    if response.status_code == 404:
        raise OrderError(f"Order {order_id} was not found.")
    if response.status_code == 400:
        raise OrderError("The return request was not valid. Give an order number and a reason.")
    if response.status_code != 201:
        raise OrderError(f"The order service had a problem (status {response.status_code}).")
    return read_json(response) 

def days_since(purchase_date):
    purchased = date.fromisoformat(purchase_date)
    return (date.today() - purchased).days
def format_order(order):
    return (
        f"Order {order['order_id']}\n"
        f"  Product:   {order['product']}\n"
        f"  Purchased: {order['purchase_date']}\n"
        f"  Status:    {order['status']}"
    )
def format_order_list(orders):
    if not orders:
        return "No orders found."
    return "\n".join(f"{o['order_id']}  {o['product']:<22} {o['status']}" for o in orders)


USAGE = (
    "Usage:\n"
    "  python order_lookup.py ORDER_NUMBER\n"
    "  python order_lookup.py list [STATUS]\n"
    '  python order_lookup.py return ORDER_NUMBER "reason"'
)


def run(args):
    """Work out what the person asked for and return the text to print."""
    if len(args) == 1 and args[0].lower() not in ("list", "return"):
        return format_order(get_order(args[0].strip().upper()))
    if args and args[0].lower() == "list" and len(args) <= 2:
        status = args[1].strip().lower() if len(args) == 2 else None
        return format_order_list(list_orders(status))
    if len(args) == 3 and args[0].lower() == "return":
        record = create_return(args[1].strip().upper(), args[2])
        return f"Return {record['return_id']} requested for {record['order_id']}."
    raise OrderError(USAGE)


def main():
    try:
        print(run(sys.argv[1:]))
    except OrderError as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())