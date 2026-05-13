# ==========================================================
# AI REVERSAL SCANNER PRO - GITHUB STABLE (COLAB MATCHED)
# ==========================================================

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
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram Error:", e)

# ==========================================================
# STOCK LIST (IDENTICAL TO COLAB)
# ==========================================================

url = "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv"
df_midcap = pd.read_csv(url)

stocks = [str(s).strip() + ".NS" for s in df_midcap["Symbol"].tolist()]

print("Stocks loaded:", len(stocks))

# ==========================================================
# SAFE DATA CLEANER (IMPORTANT FIX)
# ==========================================================

def clean_df(df):
    if df is None or len(df) == 0:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()
    return df if len(df) > 50 else None

# ==========================================================
# SUPERTREND (UNCHANGED LOGIC)
# ==========================================================

def calculate_supertrend(df, period=10, multiplier=3):

    df = df.copy()

    hl2 = (df["High"] + df["Low"]) / 2

    atr = AverageTrueRange(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        window=period
    ).average_true_range()

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    st = pd.Series(index=df.index, dtype="bool")
    st.iloc[0] = True

    for i in range(1, len(df)):
        if df["Close"].iloc[i] > upperband.iloc[i - 1]:
            st.iloc[i] = True
        elif df["Close"].iloc[i] < lowerband.iloc[i - 1]:
            st.iloc[i] = False
        else:
            st.iloc[i] = st.iloc[i - 1]

    return st

# ==========================================================
# SCAN STOCK (COLAB IDENTICAL LOGIC)
# ==========================================================

def scan_stock(symbol):

    try:
        df = yf.download(symbol, period="1y", interval="1d", auto_adjust=True, progress=False)
        df = clean_df(df)

        if df is None or len(df) < 100:
            return None

        weekly = yf.download(symbol, period="2y", interval="1wk", auto_adjust=True, progress=False)
        weekly = clean_df(weekly)

        if weekly is None:
            return None

        close = df["Close"]

        df["EMA9"] = EMAIndicator(close, window=9).ema_indicator()
        df["EMA21"] = EMAIndicator(close, window=21).ema_indicator()
        df["EMA50"] = EMAIndicator(close, window=50).ema_indicator()

        df["RSI"] = RSIIndicator(close, window=14).rsi()

        df["AVG_VOL"] = df["Volume"].rolling(20).mean()
        df["HIGH_10"] = df["High"].rolling(10).max()

        df["SUPERTREND"] = calculate_supertrend(df)

        weekly_close = weekly["Close"]
        weekly["EMA20"] = EMAIndicator(weekly_close, window=20).ema_indicator()

        df.dropna(inplace=True)
        weekly.dropna(inplace=True)

        if len(df) < 3:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        reasons = []

        # ==================================================
        # RSI ZONE (UNCHANGED)
        # ==================================================
        if not (38 <= float(latest["RSI"]) <= 55):
            return None

        score += 2
        reasons.append("RSI Early Zone")

        # RSI recovery
        if float(prev["RSI"]) < 40 and float(latest["RSI"]) > float(prev["RSI"]):
            score += 2
            reasons.append("RSI Recovering from ~40")

        # EMA CROSS
        if float(prev["EMA9"]) <= float(prev["EMA21"]) and float(latest["EMA9"]) > float(latest["EMA21"]):
            score += 2
            reasons.append("EMA Cross")

        # EMA alignment
        if float(latest["EMA9"]) > float(latest["EMA21"]) > float(latest["EMA50"]):
            score += 2
            reasons.append("EMA Trend Alignment")

        # breakout
        if float(latest["Close"]) > 0.97 * float(df["HIGH_10"].iloc[-2]):
            score += 2
            reasons.append("Near Breakout")

        # volume FIXED SAFE
        if float(latest["Volume"]) > 1.8 * float(latest["AVG_VOL"]):
            score += 2
            reasons.append("Volume Spike")

        # supertrend
        if latest["SUPERTREND"]:
            score += 2
            reasons.append("Supertrend Bullish")

        # weekly trend
        if weekly["Close"].iloc[-1] > weekly["EMA20"].iloc[-1]:
            score += 2
            reasons.append("Weekly Uptrend")

        # liquidity
        if float(latest["Close"]) * float(latest["Volume"]) < 5e7:
            return None

        # FINAL SCORE RULE (UNCHANGED)
        if score >= 7:

            msg = f"""
🚀 AI EARLY REVERSAL ALERT

Stock: {symbol}
Price: ₹{round(float(latest['Close']),2)}

Score: {score}/15

Signals:
{', '.join(reasons)}

RSI: {round(float(latest['RSI']),2)}
Volume Ratio: {round(float(latest['Volume'])/float(latest['AVG_VOL']),2)}x
"""

            return {"symbol": symbol, "score": score, "message": msg}

    except Exception as e:
        print("Error:", symbol, e)

    return None

# ==========================================================
# MAIN LOOP
# ==========================================================

results = []

print("Scanning...")

for i, s in enumerate(stocks):
    print(i+1, s)

    sig = scan_stock(s)
    if sig:
        results.append(sig)

    time.sleep(0.15)

results = sorted(results, key=lambda x: x["score"], reverse=True)

for r in results[:10]:
    print(r["message"])
    send_telegram(r["message"])

print("DONE")
