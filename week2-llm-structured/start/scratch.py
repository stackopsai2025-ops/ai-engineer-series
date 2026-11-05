import requests
url = "http://127.0.0.1:8000/orders/ORD-6000"
try:
    response = requests.get(
        url,
        timeout=3
    )
except requests.exceptions.Timeout:
    print("Too slow. Try again.")
except requests.exceptions.ConnectionError:
    print("Can't reach the service.")