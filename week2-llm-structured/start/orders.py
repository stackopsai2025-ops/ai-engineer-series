"""Provided: the order lookup you built in Week 1.

You don't need to change this file. It is the Week 1 code, trimmed down to
what Week 2 needs.
"""

import requests

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 3


class OrderError(Exception):
    """Raised with a message that is safe to show to a person."""


def get_order(order_id: str) -> dict:
    try:
        response = requests.get(f"{BASE_URL}/orders/{order_id}", timeout=TIMEOUT_SECONDS)
    except requests.exceptions.ConnectionError:
        raise OrderError("Can't reach the order service. Is mock_api.py running?")
    except requests.exceptions.Timeout:
        raise OrderError("The order service took too long to respond. Try again.")

    if response.status_code == 404:
        raise OrderError(f"Order {order_id} was not found.")
    if response.status_code != 200:
        raise OrderError(f"The order service had a problem (status {response.status_code}).")
    return response.json()


def format_order(order: dict) -> str:
    return (
        f"Order {order['order_id']}\n"
        f"  Product:   {order['product']}\n"
        f"  Purchased: {order['purchase_date']}\n"
        f"  Status:    {order['status']}"
    )
