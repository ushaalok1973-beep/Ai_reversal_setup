import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import os

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = os.getenv("8345659236:AAFfZH7zy33QS7crhfVJycL_2qWJm5EKCpc")
CHAT_ID = os.getenv("5835490642")

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing Telegram credentials")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# LOAD CSV
# =========================
print("🔥 LOADING CSV...")

df = pd.read_csv("ind_niftymidcap150list.csv")
stocks = [s + ".NS" for s in df["Symbol"].tolist()]

print("TOTAL STOCKS:", len(stocks))

# =========================
# SUPERTREND
# =========================
def supertrend(df, period=10, multiplier=3):
    hl2 = (df["High"] + df["Low"]) / 2
    atr = AverageTrueRange(df["High"], df["Low"], df["Close"], window=period).average_true_range()

    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr

    trend = [True]

    for i in range(1, len(df)):
        if df["Close"].iloc[i] > upper.iloc[i-1]:
            trend.append(True)
        elif df["Close"].iloc[i] < lower.iloc[i-1]:
            trend.append(False)
        else:
            trend.append(trend[-1])

    return pd.Series(trend, index=df.index)

# =========================
# RSI DIVERGENCE
# =========================
def rsi_divergence(df):
    try:
        p = df["Low"].tail(10).values
        r = df["RSI"].tail(10).values
        return p[-1] < p[-5] and r[-1] > r[-5]
    except:
        return False

# =========================
# SCAN FUNCTION
# =========================
def scan(symbol):

    try:
        df = yf.download(symbol, period="1y", interval="1d", progress=False)

        if df is None or len(df) < 100:
            return None

        close = df["Close"]

        df["EMA9"] = EMAIndicator(close, window=9).ema_indicator()
        df["EMA21"] = EMAIndicator(close, window=21).ema_indicator()
        df["EMA50"] = EMAIndicator(close, window=50).ema_indicator()
        df["RSI"] = RSIIndicator(close, window=14).rsi()

        df["VOL_AVG"] = df["Volume"].rolling(20).mean()
        df["HIGH10"] = df["High"].rolling(10).max()
        df["ST"] = supertrend(df)

        df.dropna(inplace=True)

        if len(df) < 50:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        reasons = []

        # RSI 40–55 zone (your entry zone)
        if not (38 <= last["RSI"] <= 55):
            return None
        reasons.append("RSI Zone")
        score += 2

        # RSI recovery from 40
        if prev["RSI"] < 40 and last["RSI"] > prev["RSI"]:
            reasons.append("RSI Recovery")
            score += 2

        # EMA cross
        if prev["EMA9"] <= prev["EMA21"] and last["EMA9"] > last["EMA21"]:
            reasons.append("EMA Cross")
            score += 2

        # Volume spike
        if last["Volume"] > 1.8 * last["VOL_AVG"]:
            reasons.append("Volume Spike")
            score += 2

        # Supertrend
        if last["ST"]:
            reasons.append("Supertrend")
            score += 2

        # Liquidity filter
        if last["Close"] * last["Volume"] < 5e7:
            return None

        # FINAL
        if score >= 7:
            msg = f"""
🚀 MIDCAP REVERSAL ALERT

Stock: {symbol}
Price: {round(last['Close'],2)}
RSI: {round(last['RSI'],2)}

Score: {score}
Signals: {', '.join(reasons)}
"""
            return msg

    except Exception as e:
        print("Error:", symbol, e)

    return None

# =========================
# MAIN LOOP (IMPORTANT FIX)
# =========================
print("🔥 START SCANNING...")

results = []

for i, s in enumerate(stocks):
    print(f"Scanning {i+1}/{len(stocks)} {s}")

    signal = scan(s)

    if signal:
        print("SIGNAL FOUND:", s)
        results.append(signal)

    time.sleep(0.2)

print("TOTAL SIGNALS:", len(results))

# =========================
# SEND TELEGRAM
# =========================
for r in results[:10]:
    send_telegram(r)
    print("SENT:", r)

print("DONE")
