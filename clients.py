import requests
import base64
import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import certifi

from requests.exceptions import HTTPError
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

import websockets

class Environment(Enum):
    DEMO = "demo"
    PROD = "prod"

class KalshiBaseClient:
    def __init__(self, key_id: str, private_key: rsa.RSAPrivateKey, environment: Environment = Environment.DEMO):
        self.key_id = key_id
        self.private_key = private_key
        self.environment = environment
        self.last_api_call = datetime.now()

        if self.environment == Environment.DEMO:
            self.HTTP_BASE_URL = "https://demo-api.kalshi.co"
            self.WS_BASE_URL = "wss://demo-api.kalshi.co"
        elif self.environment == Environment.PROD:
            self.HTTP_BASE_URL = "https://api.elections.kalshi.com"
            self.WS_BASE_URL = "wss://api.elections.kalshi.com"
        else:
            raise ValueError("Invalid environment")

    def request_headers(self, method: str, path: str) -> Dict[str, Any]:
        current_time_milliseconds = int(time.time() * 1000)
        timestamp_str = str(current_time_milliseconds)
        path_parts = path.split('?')
        msg_string = timestamp_str + method + path_parts[0]
        signature = self.sign_pss_text(msg_string)

        return {
            "Content-Type": "application/json",
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
        }

    def sign_pss_text(self, text: str) -> str:
        message = text.encode('utf-8')
        try:
            signature = self.private_key.sign(
                message,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

class KalshiHttpClient(KalshiBaseClient):
    def __init__(self, key_id: str, private_key: rsa.RSAPrivateKey, environment: Environment = Environment.DEMO):
        super().__init__(key_id, private_key, environment)
        self.host = self.HTTP_BASE_URL
        self.exchange_url = "/trade-api/v2/exchange"
        self.markets_url = "/trade-api/v2/markets"
        self.portfolio_url = "/trade-api/v2/portfolio"

    def rate_limit(self):
        threshold_ms = 100
        now = datetime.now()
        if now - self.last_api_call < timedelta(milliseconds=threshold_ms):
            time.sleep(threshold_ms / 1000)
        self.last_api_call = datetime.now()

    def raise_if_bad_response(self, response: requests.Response):
        if response.status_code not in range(200, 299):
            print("RESPONSE TEXT:", response.text)
            response.raise_for_status()

    def get(self, path: str, params: Dict[str, Any] = {}):
        self.rate_limit()
        response = requests.get(
            self.host + path,
            headers=self.request_headers("GET", path),
            params=params,
            verify=certifi.where()
        )
        self.raise_if_bad_response(response)
        return response.json()

    def post(self, path: str, body: dict):
        self.rate_limit()
        response = requests.post(
            self.host + path,
            json=body,
            headers=self.request_headers("POST", path),
            verify=certifi.where()
        )
        self.raise_if_bad_response(response)
        return response.json()

    def delete(self, path: str, params: Dict[str, Any] = {}):
        self.rate_limit()
        response = requests.delete(
            self.host + path,
            headers=self.request_headers("DELETE", path),
            params=params,
            verify=certifi.where()
        )
        self.raise_if_bad_response(response)
        return response.json()

    def get_balance(self):
        return self.get(self.portfolio_url + "/balance")

class KalshiWebSocketClient(KalshiBaseClient):
    def __init__(self, key_id: str, private_key: rsa.RSAPrivateKey, environment: Environment = Environment.DEMO):
        super().__init__(key_id, private_key, environment)
        self.ws = None
        self.url_suffix = "/trade-api/ws/v2"
        self.message_id = 1

    async def connect(self):
        """Establishes a WebSocket connection using authentication."""
        import ssl
        import certifi

        ssl_context = ssl.create_default_context(cafile=certifi.where())

        host = self.WS_BASE_URL + self.url_suffix
        auth_headers = self.request_headers("GET", self.url_suffix)

        async with websockets.connect(host, additional_headers=auth_headers, ssl=ssl_context) as websocket:
            self.ws = websocket
            await self.on_open()
            await self.handler()


    async def on_open(self):
        print("WebSocket connection opened.")
        await self.subscribe_to_tickers()

    async def subscribe_to_tickers(self):
        subscription_message = {
            "id": self.message_id,
            "cmd": "subscribe",
            "params": {
                "channels": ["ticker"]
            }
        }
        await self.ws.send(json.dumps(subscription_message))
        self.message_id += 1

    async def handler(self):
        try:
            async for message in self.ws:
                await self.on_message(message)
        except websockets.ConnectionClosed as e:
            await self.on_close(e.code, e.reason)
        except Exception as e:
            await self.on_error(e)

    async def on_message(self, message):
        print("Received message:", message)

    async def on_error(self, error):
        print("WebSocket error:", error)

    async def on_close(self, close_status_code, close_msg):
        print("WebSocket closed:", close_status_code, close_msg)
