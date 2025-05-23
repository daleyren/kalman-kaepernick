import requests

url = "https://trading-api.kalshi.com/trade-api/v2/markets"
try:
    r = requests.get(url, timeout=10)
    print(r.status_code)
    print(r.json())
except Exception as e:
    print("Request failed:", e)