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
        print("Missing Telegram credentials")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# =========================
# LOAD STOCK LIST
# =========================
df = pd.read_csv("ind_niftymidcap150list.csv")

stocks = (
    df["Symbol"]
    .dropna()
    .astype(str)
    .str.strip()
    + ".NS"
).tolist()

print("TOTAL STOCKS:", len(stocks))

# =========================
# SAFE DATA CLEANER (IMPORTANT FIX)
# =========================
def clean_ohlcv(df):
    df = df.copy()

    # handle possible multi-index columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # FORCE 1D SERIES (CRITICAL FIX FOR YOUR ERROR)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype(float).values.reshape(-1)

    return df

# =========================
# SUPER TREND
# =========================
def supertrend(df, period=10, multiplier=3):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    hl2 = (high + low) / 2
    atr = AverageTrueRange(high, low, close, window=period).average_true_range()

    upper = hl2 + multiplier * atr
    lower = hl2 - multiplier * atr

    trend = [True]

    for i in range(1, len(df)):
        if close.iloc[i] > upper.iloc[i - 1]:
            trend.append(True)
        elif close.iloc[i] < lower.iloc[i - 1]:
            trend.append(False)
        else:
            trend.append(trend[-1])

    return pd.Series(trend, index=df.index)

# =========================
# SCAN FUNCTION
# =========================
def scan(symbol):
    try:
        data = yf.download(symbol, period="1y", interval="1d", progress=False)

        if data is None or data.empty or len(data) < 120:
            return None

        df = clean_ohlcv(data)

        close = df["Close"]  # NOW GUARANTEED 1D

        # =========================
        # INDICATORS (SAFE INPUT)
        # =========================
        df["EMA9"] = EMAIndicator(close, window=9).ema_indicator()
        df["EMA21"] = EMAIndicator(close, window=21).ema_indicator()
        df["EMA50"] = EMAIndicator(close, window=50).ema_indicator()
        df["RSI"] = RSIIndicator(close, window=14).rsi()

        df["VOL_AVG"] = df["Volume"].rolling(20).mean()

        df["ST"] = supertrend(df)

        df = df.dropna()

        if len(df) < 60:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        reasons = []

        # =========================
        # RSI FILTER
        # =========================
        if not (38 <= last["RSI"] <= 55):
            return None

        score += 2
        reasons.append("RSI Zone")

        # RSI recovery
        if prev["RSI"] < 40 and last["RSI"] > prev["RSI"]:
            score += 2
            reasons.append("RSI Recovery")

        # EMA crossover
        if prev["EMA9"] <= prev["EMA21"] and last["EMA9"] > last["EMA21"]:
            score += 2
            reasons.append("EMA Cross")

        # Volume spike (SAFE)
        if last["Volume"] > 1.8 * last["VOL_AVG"]:
            score += 2
            reasons.append("Volume Spike")

        # Supertrend
        if bool(last["ST"]):
            score += 2
            reasons.append("Supertrend")

        # Liquidity filter
        if last["Close"] * last["Volume"] < 5e7:
            return None

        # FINAL CONDITION
        if score >= 7:
            return f"""
MIDCAP REVERSAL ALERT

Stock: {symbol}
Price: {round(last['Close'],2)}
RSI: {round(last['RSI'],2)}

Score: {score}
Signals: {', '.join(reasons)}
"""

    except Exception as e:
        print(symbol, "ERROR:", e)

    return None

# =========================
# MAIN LOOP
# =========================
results = []

for i, s in enumerate(stocks):
    print(f"{i+1}/{len(stocks)} {s}")

    signal = scan(s)

    if signal:
        print("SIGNAL:", s)
        results.append(signal)

    time.sleep(0.15)

print("TOTAL SIGNALS:", len(results))

# =========================
# TELEGRAM OUTPUT
# =========================
for r in results[:10]:
    send_telegram(r)
    print("SENT")

print("DONE")
