import os
import asyncio
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
import argparse
from kalman import KF
from clients import KalshiHttpClient, KalshiWebSocketClient, Environment
from vis import Visualizer
import pandas as pd
import time

parser = argparse.ArgumentParser(description="Kalshi RL Bot")

parser.add_argument(
    "--train", action="store_true",
    help="Run the system in training mode (using historical data)"
)
parser.add_argument(
    "--live", action="store_true",
    help="Run the system in live mode (using WebSocket)"
)
args = parser.parse_args()

# Load env variables
load_dotenv()
env = Environment.PROD

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

kalman = KF()
vis = Visualizer()

if args.train:
    # df=client.get_top_markets(limit=500)
    # print(df.head())
    df = client.get_all_trades("KXNBAGAME-25MAY22MINOKC-MIN")
    print(df.head())
    print(df.shape[0])
    vis.plot_market_percentages(df)

elif args.live:
    ws_client = KalshiWebSocketClient(KEYID, private_key, environment=env, kalman=kalman)
    try:
        asyncio.run(ws_client.connect())
    except Exception as e:
        print("WebSocket error:", e)
else:
    print("⚠️ Please specify --train or --live.")

