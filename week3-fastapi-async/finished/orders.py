"""Week 3 (finished): the Week 1 order lookup, made async with httpx."""

import httpx

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 3


class OrderError(Exception):
    """Raised with a message that is safe to show, plus the status code to send back."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


async def get_order(order_id: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(f"{BASE_URL}/orders/{order_id}")
    except httpx.TimeoutException:
        raise OrderError("The order service took too long to respond. Try again.")
    except httpx.ConnectError:
        raise OrderError("Can't reach the order service. Is mock_api.py running?")
    except httpx.HTTPError:
        raise OrderError("Something went wrong talking to the order service.")

    if response.status_code == 404:
        raise OrderError(f"Order {order_id} was not found.", status_code=404)
    if response.status_code != 200:
        raise OrderError(f"The order service had a problem (status {response.status_code}).")
    return response.json()
