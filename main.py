import os
import asyncio
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization

from clients import KalshiHttpClient, KalshiWebSocketClient, Environment

# Load env variables
load_dotenv()
env = Environment.DEMO

KEYID = os.getenv("DEMO_KEYID") if env == Environment.DEMO else os.getenv("PROD_KEYID")
KEYFILE = os.getenv("DEMO_KEYFILE") if env == Environment.DEMO else os.getenv("PROD_KEYFILE")

print("Using Key ID:", KEYID)

# Load RSA private key
try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
        print("Private key loaded.")
except Exception as e:
    raise Exception(f"Error loading private key: {e}")

# Initialize and test HTTP client
client = KalshiHttpClient(KEYID, private_key, environment=env)

try:
    balance = client.get_balance()
    print("Balance:", balance)
except Exception as e:
    print("Error fetching balance:", e)

# Initialize and run WebSocket client
ws_client = KalshiWebSocketClient(KEYID, private_key, environment=env)

try:
    asyncio.run(ws_client.connect())
except Exception as e:
    print("WebSocket error:", e)
