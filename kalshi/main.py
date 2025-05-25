import os
import asyncio
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
import argparse
from clients import KalshiHttpClient, KalshiWebSocketClient, Environment
from vis import Visualizer
import pandas as pd
from datetime import datetime, timedelta
import time
from datetime import datetime
import re
from itertools import chain

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

vis = Visualizer()

def agg_ticker_data():
    start_date = datetime(2024, 5, 1)
    end_date = datetime(2024, 5, 23)

    top_markets = []

    current_date = start_date
    while current_date <= end_date:
        for hour in chain([0], range(9, 24)):  # 0 to 23
            print(str(current_date.day))
            timestamp = current_date.replace(hour=hour)
            ticker = f"KXBTC-25MAY{timestamp.day:02}{hour:02}"
            print(ticker)
            market_tickers = client.get("/trade-api/v2/markets", params={"event_ticker":ticker})
            print(market_tickers)
            markets = market_tickers['markets']
            top5 = sorted(markets, key=lambda x: x.get('volume', 0), reverse=True)[:3]
            top_markets.extend(top5)
        current_date += timedelta(days=1)
    df = pd.DataFrame(top_markets)
    df.to_csv("filtered.csv")
    return df

def extract_two_numbers(text):
    # Match numbers with optional $, commas, and decimals
    numbers = re.findall(r'\$?[\d,]+(?:\.\d+)?', text)
    # Remove $ and commas, then convert to float
    cleaned = [float(n.replace('$', '').replace(',', '')) for n in numbers]
    if len(cleaned) >= 2:
        return cleaned[0], cleaned[1]
    else:
        raise ValueError("Less than two numbers found.")

def agg_time_series_data():
    df = pd.read_csv("filtered.csv")
    df2 = pd.read_csv("datasets/may_filtered.csv")
    df2['Timestamp'] = pd.to_datetime(df2['Timestamp'])

    episodes = []
    for i in range(0, len(df), 3):
        row = df.iloc[i]
        ticker = row['ticker']
        result = row['result']
        low, high = extract_two_numbers(row['yes_sub_title'])
        open_time = int(pd.to_datetime(row['open_time']).timestamp())
        close_time = int(pd.to_datetime(row['close_time']).timestamp())

        path = f"/trade-api/v2/series/KXBTC/markets/{ticker}/candlesticks"
        series = client.get(path, params={
            "start_ts": open_time,
            "end_ts": close_time,
            "period_interval": 1
        })

        candlesticks = series['candlesticks']
        df_candle = pd.DataFrame(candlesticks)
        df_candle['end_period_ts'] = pd.to_datetime(df_candle['end_period_ts'], unit='s')
        print(df_candle['yes_bid'])
        states = []
        for j in range(len(df_candle)):
            t = df_candle['end_period_ts'].iloc[j] - pd.Timedelta(minutes=1)
            match = df2.loc[df2['Timestamp'] == t, 'Open']
            truth = match.iloc[0] if not match.empty else None

            yes_bid_open = df_candle['yes_bid'].iloc[j].get('open') if isinstance(df_candle['yes_bid'].iloc[j], dict) else None
            yes_ask_open = df_candle['yes_ask'].iloc[j].get('open') if isinstance(df_candle['yes_ask'].iloc[j], dict) else None
            no_bid_open = 100-yes_bid_open
            no_ask_open = 100-yes_ask_open

            state = [j, yes_bid_open, yes_ask_open, no_bid_open, no_ask_open, low, high, truth]
            states.append(state)

        episodes.append({'result': result, 'states': states})

    # Save to JSON instead of malformed DataFrame
    import json
    with open("may.json", "w") as f:
        json.dump(episodes, f, indent=2)

    return episodes


    #pd.DataFrame(episodes).to_csv("episodes.csv"
    ret = {}
    ret['episodes'] = episodes
    pd.DataFrame(ret).to_csv("may.csv", index=False)
    return episodes  # List of episode DataFrames



def func():
    df = pd.read_csv("filtered.csv")
    s = df.head(5)
    print(s.keys())

if args.train:
    agg_time_series_data()
elif args.live:
    ws_client = KalshiWebSocketClient(KEYID, private_key, environment=env)
    try:
        asyncio.run(ws_client.connect())
    except Exception as e:
        print("WebSocket error:", e)
else:
    print("⚠️ Please specify --train or --live.")

