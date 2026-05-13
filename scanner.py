import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import os

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = "8345659236:AAFfZH7zy33QS7crhfVJycL_2qWJm5EKCpc"
CHAT_ID = "5835490642"

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# =========================
# LOAD STOCK LIST
# =========================
df = pd.read_csv("ind_niftymidcap150list.csv")
stocks = [s + ".NS" for s in df["Symbol"].tolist()]

print("Stocks loaded:", len(stocks))


# =========================
# SCAN FUNCTION
# =========================
def scan(symbol):

    try:
        data = yf.download(symbol, period="1y", interval="1d", progress=False)

        if data is None or len(data) < 120:
            return None

        # fix possible multi-index issue
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna()

        close = data["Close"]

        # =========================
        # INDICATORS
        # =========================
        data["EMA9"] = EMAIndicator(close, window=9).ema_indicator()
        data["EMA16"] = EMAIndicator(close, window=16).ema_indicator()
        data["EMA40"] = EMAIndicator(close, window=40).ema_indicator()
        data["RSI"] = RSIIndicator(close, window=14).rsi()

        data["VOL_AVG"] = data["Volume"].rolling(20).mean()

        data = data.dropna()

        if len(data) < 60:
            return None

        last = data.iloc[-1]
        prev = data.iloc[-2]

        score = 0
        reasons = []

        # =========================
        # EMA CROSS (9 above 16)
        # =========================
        if prev["EMA9"] <= prev["EMA16"] and last["EMA9"] > last["EMA16"]:
            score += 4
            reasons.append("EMA9 Cross EMA16")

        # EMA trend strength
        if last["EMA9"] > last["EMA40"]:
            score += 2
            reasons.append("EMA9 > EMA40")

        # =========================
        # RSI CONDITION
        # =========================
        if 38 <= last["RSI"] <= 45:
            score += 2
            reasons.append("RSI Near 40")

        if last["RSI"] > prev["RSI"]:
            score += 2
            reasons.append("RSI Rising")

        # =========================
        # VOLUME FILTER
        # =========================
        if last["Volume"] >= 1.3 * last["VOL_AVG"]:
            score += 3
            reasons.append("Volume Spike")

        # =========================
        # LIQUIDITY FILTER
        # =========================
        if last["Close"] * last["Volume"] < 3e7:
            return None

        # =========================
        # FINAL RULE
        # =========================
        if score >= 7:

            msg = f"""
🚀 MIDCAP REVERSAL SETUP

Stock: {symbol}
Price: {round(last['Close'],2)}
RSI: {round(last['RSI'],2)}

Score: {score}

Signals:
{", ".join(reasons)}
"""

            return msg

    except Exception as e:
        print("Error:", symbol, e)

    return None


# =========================
# MAIN LOOP
# =========================
print("Scanning started...")

results = []

for i, s in enumerate(stocks):
    print(f"{i+1}/{len(stocks)} {s}")

    signal = scan(s)

    if signal:
        print("SIGNAL:", s)
        results.append(signal)

    time.sleep(0.12)

print("TOTAL SIGNALS:", len(results))


# =========================
# TELEGRAM OUTPUT
# =========================
for r in results[:20]:
    send_telegram(r)
    print("SENT")

print("DONE")
