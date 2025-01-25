import os
import pandas as pd
from alpaca_trade_api.rest import REST, TimeFrame
from ta.momentum import RSIIndicator
from ta.trend import MACD

# Alpaca API Credentials (Set these as environment variables in AWS Lambda)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# Alpaca client
alpaca = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

# XRP Trading Symbol
XRP_SYMBOL = "XRP/USD"

# Fetch historical prices
def get_xrp_prices():
    bars = alpaca.get_crypto_bars(XRP_SYMBOL, TimeFrame.Hour, limit=50).df
    bars = bars.reset_index()[["timestamp", "close"]].rename(columns={"timestamp": "time"})
    return bars

# Calculate RSI & MACD
def calculate_indicators(df):
    df["RSI"] = RSIIndicator(df["close"], window=14).rsi()
    df["MACD"] = MACD(df["close"], window_slow=26, window_fast=12, window_sign=9).macd()
    return df

# Generate buy/sell signals
def generate_signal(df):
    latest = df.iloc[-1]
    if latest["RSI"] > 50 and latest["MACD"] > 0:
        return "BUY"
    elif latest["RSI"] < 50 and latest["MACD"] < 0:
        return "SELL"
    return "HOLD"

# Execute trade
def place_trade(action, quantity=10):
    if action == "BUY":
        order = alpaca.submit_order(symbol=XRP_SYMBOL, qty=quantity, side="buy", type="market", time_in_force="gtc")
        return {"status": "BUY executed", "order_id": order.id}
    elif action == "SELL":
        order = alpaca.submit_order(symbol=XRP_SYMBOL, qty=quantity, side="sell", type="market", time_in_force="gtc")
        return {"status": "SELL executed", "order_id": order.id}
    return {"status": "No trade executed"}

# Main trading function (entry point for AWS Lambda)
def lambda_handler(event, context):
    df = get_xrp_prices()
    df = calculate_indicators(df)
    action = generate_signal(df)
    result = place_trade(action)
    return {"action": action, "result": result}