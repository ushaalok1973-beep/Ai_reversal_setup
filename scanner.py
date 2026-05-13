import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

# =========================
# TELEGRAM CONFIG
# =========================

BOT_TOKEN = "8345659236:AAFfZH7zy33QS7crhfVJycL_2qWJm5EKCpc"
CHAT_ID = "5835490642"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

# =========================
# STOCK LIST
# =========================

df = pd.read_csv("midcap.csv")
stocks = [symbol + ".NS" for symbol in df["Symbol"].tolist()]

print("Stocks loaded:", len(stocks))

# =========================
# SCAN FUNCTION
# =========================

def scan(symbol):

    try:
        data = yf.download(symbol, period="1y", interval="1d", auto_adjust=True, progress=False)

        if len(data) < 100:
            return None

        data = data.copy()

        close = data["Close"].squeeze()

        data["EMA9"] = EMAIndicator(close=close, window=9).ema_indicator()
        data["EMA21"] = EMAIndicator(close=close, window=21).ema_indicator()
        data["RSI"] = RSIIndicator(close=close, window=14).rsi()

        data["AVG_VOL"] = data["Volume"].rolling(20).mean()
        data["HIGH_10"] = data["High"].rolling(10).max()

        data.dropna(inplace=True)

        latest = data.iloc[-1]
        prev = data.iloc[-2]

        score = 0
        reasons = []

        # =========================
        # RSI EARLY REVERSAL ZONE
        # =========================

        if not (38 <= float(latest["RSI"]) <= 55):
            return None

        score += 2
        reasons.append("RSI Zone")

        # =========================
        # RSI RECOVERY FROM 40
        # =========================

        if float(prev["RSI"]) < 40 and float(latest["RSI"]) > float(prev["RSI"]):
            score += 2
            reasons.append("RSI Recovery")

        # =========================
        # EMA CROSS
        # =========================

        if float(prev["EMA9"]) <= float(prev["EMA21"]) and float(latest["EMA9"]) > float(latest["EMA21"]):
            score += 2
            reasons.append("EMA Cross")

        # =========================
        # VOLUME SPIKE
        # =========================

        if float(latest["Volume"]) > 1.5 * float(latest["AVG_VOL"]):
            score += 2
            reasons.append("Volume Spike")

        # =========================
        # NEAR BREAKOUT
        # =========================

        if float(latest["Close"]) > 0.97 * float(data["HIGH_10"].iloc[-2]):
            score += 2
            reasons.append("Near Breakout")

        # =========================
        # LIQUIDITY FILTER
        # =========================

        if float(latest["Close"]) * float(latest["Volume"]) < 5e7:
            return None

        # =========================
        # FINAL SIGNAL
        # =========================

        if score >= 6:

            msg = f"""
🚀 REVERSAL ALERT

Stock: {symbol}
Price: ₹{round(float(latest['Close']), 2)}
RSI: {round(float(latest['RSI']), 2)}

Score: {score}

Signals:
{', '.join(reasons)}
"""

            return msg

    except Exception as e:
        print(symbol, e)

    return None

# =========================
# RUN SCAN
# =========================

results = []

for s in stocks:
    print("Scanning", s)
    signal = scan(s)
    if signal:
        results.append(signal)
    time.sleep(0.2)

print("Signals found:", len(results))

for r in results:
    print(r)
    send_telegram(r)
