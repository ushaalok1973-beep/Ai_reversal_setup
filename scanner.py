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
# TELEGRAM
# =========================

BOT_TOKEN = "8345659236:AAFfZH7zy33QS7crhfVJycL_2qWJm5EKCpc"
CHAT_ID = "5835490642"

def send_telegram(msg):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
        print("Telegram status:", r.text)
    except Exception as e:
        print("Telegram error:", e)

# =========================
# LOAD CSV (CRITICAL DEBUG)
# =========================

file_path = os.path.join(os.path.dirname(__file__), "ind_niftymidcap150list.csv")

print("CSV PATH:", file_path)

df = pd.read_csv(file_path)

print("CSV LOADED")
print("Columns:", df.columns)

df.columns = df.columns.str.strip()

stocks = [s.strip() + ".NS" for s in df["Symbol"].tolist()]

print("TOTAL STOCKS:", len(stocks))
print("FIRST 5 STOCKS:", stocks[:5])

# =========================
# SCAN FUNCTION
# =========================

def scan(symbol):

    try:
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True, progress=False)

        if df is None or len(df) < 100:
            return None

        df = df.copy()

        close = df["Close"].squeeze()

        df["EMA9"] = EMAIndicator(close=close, window=9).ema_indicator()
        df["EMA21"] = EMAIndicator(close=close, window=21).ema_indicator()
        df["RSI"] = RSIIndicator(close=close, window=14).rsi()

        df["AVG_VOL"] = df["Volume"].rolling(20).mean()
        df["HIGH_10"] = df["High"].rolling(10).max()

        df.dropna(inplace=True)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        reasons = []

        rsi = float(latest["RSI"])

        if 38 <= rsi <= 55:
            score += 2
            reasons.append("RSI zone")
        else:
            return None

        if float(prev["RSI"]) < 40:
            score += 2
            reasons.append("RSI recovery")

        if float(latest["EMA9"]) > float(latest["EMA21"]):
            score += 2
            reasons.append("EMA trend")

        if float(latest["Volume"]) > 1.5 * float(latest["AVG_VOL"]):
            score += 1
            reasons.append("Volume spike")

        if score >= 4:
            print("SIGNAL FOUND:", symbol)

            return f"""
🚀 SIGNAL

Stock: {symbol}
Price: {round(float(latest['Close']),2)}
RSI: {round(rsi,2)}
Score: {score}
Signals: {', '.join(reasons)}
"""

    except Exception as e:
        print("ERROR:", symbol, e)

    return None

# =========================
# RUN SCAN (FORCE OUTPUT)
# =========================

results = []

print("START SCANNING...")

for i, s in enumerate(stocks):

    print(f"[{i+1}/{len(stocks)}] scanning {s}")

    sig = scan(s)

    if sig:
        results.append(sig)

    time.sleep(0.1)

# =========================
# FINAL OUTPUT (CRITICAL)
# =========================

print("===================================")
print("SCAN COMPLETE")
print("TOTAL SIGNALS:", len(results))
print("===================================")

for r in results:
    print(r)
    send_telegram(r)
