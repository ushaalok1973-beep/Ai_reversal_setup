import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

# ==========================================================
# TELEGRAM
# ==========================================================

BOT_TOKEN = "8345659236:AAFfZH7zy33QS7crhfVJycL_2qWJm5EKCpc"
CHAT_ID = "5835490642"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# ==========================================================
# STOCK LIST (LOCAL FILE - GITHUB SAFE)
# ==========================================================

import os

file_path = os.path.join(os.path.dirname(__file__), "ind_niftymidcap150list.csv")
df_midcap = pd.read_csv(file_path)

df_midcap.columns = df_midcap.columns.str.strip()

stocks = [s.strip() + ".NS" for s in df_midcap["Symbol"].tolist()]

print("Stocks loaded:", len(stocks))

# ==========================================================
# SUPERTREND
# ==========================================================

def supertrend(df, period=10, multiplier=3):

    hl2 = (df["High"] + df["Low"]) / 2

    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=period
    ).average_true_range()

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    trend = pd.Series(index=df.index, dtype="bool")
    trend.iloc[0] = True

    for i in range(1, len(df)):
        if df["Close"].iloc[i] > upperband.iloc[i-1]:
            trend.iloc[i] = True
        elif df["Close"].iloc[i] < lowerband.iloc[i-1]:
            trend.iloc[i] = False
        else:
            trend.iloc[i] = trend.iloc[i-1]

    return trend

# ==========================================================
# SCAN FUNCTION (COLAB LOGIC PRESERVED)
# ==========================================================

def scan_stock(symbol):

    try:
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True, progress=False)

        if df is None or len(df) < 100:
            return None

        df = df.copy()

        close = df["Close"].squeeze()

        df["EMA9"] = EMAIndicator(close=close, window=9).ema_indicator()
        df["EMA21"] = EMAIndicator(close=close, window=21).ema_indicator()
        df["EMA50"] = EMAIndicator(close=close, window=50).ema_indicator()

        df["RSI"] = RSIIndicator(close=close, window=14).rsi()

        df["AVG_VOL"] = df["Volume"].rolling(20).mean()
        df["HIGH_10"] = df["High"].rolling(10).max()

        df["SUPERTREND"] = supertrend(df)

        df.dropna(inplace=True)

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]

        score = 0
        reasons = []

        # ==================================================
        # SAME CORE COLAB LOGIC
        # ==================================================

        # RSI early reversal zone
        if not (38 <= float(latest["RSI"]) <= 55):
            return None

        score += 2
        reasons.append("RSI Zone")

        # RSI recovery
        if float(prev["RSI"]) < 40 and float(latest["RSI"]) > float(prev["RSI"]):
            score += 2
            reasons.append("RSI Recovery")

        # EMA cross
        if float(prev["EMA9"]) <= float(prev["EMA21"]) and float(latest["EMA9"]) > float(latest["EMA21"]):
            score += 2
            reasons.append("EMA Cross")

        # Volume breakout (COLAB STYLE 1.8x)
        if float(latest["Volume"]) > 1.8 * float(latest["AVG_VOL"]):
            score += 2
            reasons.append("Volume Spike")

        # 10-day breakout
        if float(latest["Close"]) > float(df["HIGH_10"].iloc[-2]):
            score += 2
            reasons.append("Breakout")

        # Liquidity filter (same)
        traded_value = float(latest["Close"]) * float(latest["Volume"])
        if traded_value < 5e7:
            return None

        # Supertrend confirmation
        if latest["SUPERTREND"]:
            score += 2
            reasons.append("Supertrend")

        # ==================================================
        # COLAB THRESHOLD (IMPORTANT)
        # ==================================================

        if score >= 6:

            msg = f"""
🚀 AI REVERSAL ALERT

Stock: {symbol}
Price: ₹{round(float(latest['Close']),2)}
RSI: {round(float(latest['RSI']),2)}

Score: {score}

Signals:
{', '.join(reasons)}
"""

            return msg

    except Exception as e:
        print("Error:", symbol, e)

    return None

# ==========================================================
# RUN SCAN
# ==========================================================

results = []

print("Scanning Midcap...")

for s in stocks:
    try:
        sig = scan_stock(s)
        if sig:
            results.append(sig)
    except Exception as e:
        print("Error:", s, e)

    time.sleep(0.2)

print("Signals found:", len(results))

for r in results[:10]:
    print(r)
    send_telegram(r)

print("DONE")
