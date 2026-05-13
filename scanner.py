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
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

# =========================
# LOAD MIDCAP CSV (FIXED)
# =========================

try:
    file_path = os.path.join(os.path.dirname(__file__), "ind_niftymidcap150list.csv")
    df = pd.read_csv(file_path)

    df.columns = df.columns.str.strip()

    print("CSV Columns:", df.columns)
    print("CSV loaded successfully")

    if "Symbol" not in df.columns:
        raise Exception("Symbol column not found in CSV")

    symbols = df["Symbol"].dropna().astype(str).tolist()
    stocks = [s.strip() + ".NS" for s in symbols]

    print("Total stocks loaded:", len(stocks))

except Exception as e:
    print("ERROR loading CSV:", e)
    stocks = []

# =========================
# SCAN FUNCTION
# =========================

def scan(symbol):
    try:
        data = yf.download(symbol, period="1y", interval="1d", auto_adjust=True, progress=False)

        if data is None or len(data) < 100:
            return None

        data = data.copy()

        close = data["Close"].squeeze()

        data["EMA9"] = EMAIndicator(close=close, window=9).ema_indicator()
        data["EMA21"] = EMAIndicator(close=close, window=21).ema_indicator()
        data["RSI"] = RSIIndicator(close=close, window=14).rsi()

        data["AVG_VOL"] = data["Volume"].rolling(20).mean()
        data["HIGH_10"] = data["High"].rolling(10).max()

        data.dropna(inplace=True)

        if len(data) < 2:
            return None

        latest = data.iloc[-1]
        prev = data.iloc[-2]

        score = 0
        reasons = []

        # =========================
        # RSI ZONE FILTER (CORE EDGE)
        # =========================

        if not (38 <= float(latest["RSI"]) <= 55):
            return None

        score += 2
        reasons.append("RSI Zone")

        # RSI recovery from oversold zone
        if float(prev["RSI"]) < 40 and float(latest["RSI"]) > float(prev["RSI"]):
            score += 2
            reasons.append("RSI Recovery")

        # EMA crossover
        if float(prev["EMA9"]) <= float(prev["EMA21"]) and float(latest["EMA9"]) > float(latest["EMA21"]):
            score += 2
            reasons.append("EMA Cross")

        # Volume spike
        if float(latest["Volume"]) > 1.5 * float(latest["AVG_VOL"]):
            score += 2
            reasons.append("Volume Spike")

        # Near breakout
        if float(latest["Close"]) > 0.97 * float(data["HIGH_10"].iloc[-2]):
            score += 2
            reasons.append("Near Breakout")

        # Liquidity filter
        if float(latest["Close"]) * float(latest["Volume"]) < 5e7:
            return None

        # =========================
        # FINAL SIGNAL
        # =========================

        if score >= 6:
            return f"""
🚀 REVERSAL ALERT

Stock: {symbol}
Price: ₹{round(float(latest['Close']), 2)}
RSI: {round(float(latest['RSI']), 2)}

Score: {score}

Signals:
{', '.join(reasons)}
"""

    except Exception as e:
        print(f"Error in {symbol}: {e}")

    return None

# =========================
# RUN SCANNER (SAFE)
# =========================

results = []

if len(stocks) == 0:
    print("No stocks loaded — STOP")
else:
    for s in stocks:
        try:
            print("Scanning:", s)
            signal = scan(s)
            if signal:
                results.append(signal)
        except Exception as e:
            print("Stock error:", s, e)

        time.sleep(0.2)

print("Signals found:", len(results))

for r in results:
    print(r)
    send_telegram(r)
