import pandas as pd
import yfinance as yf

# ====================================
# LOAD STOCK UNIVERSE
# ====================================

universe = pd.read_csv("data/stock_universe.csv")

WATCHLIST = universe["SYMBOL"].tolist()

print("\nLoaded Stock Universe:\n")

for stock in WATCHLIST:
    print(stock)

print(f"\nTotal Stocks Loaded: {len(WATCHLIST)}")

# ====================================
# TEST DATA DOWNLOAD
# ====================================

print("\nDownloading sample data...\n")

for stock in WATCHLIST:

    try:

        df = yf.download(
            stock,
            period="6mo",
            interval="1wk"
        )

        if len(df) == 0:
            print(f"{stock} -> No Data")
            continue

        latest_close = round(
            float(df["Close"].iloc[-1]), 2
        )

        print(
            f"{stock} -> Latest Price: {latest_close}"
        )

    except Exception as e:

        print(f"Error in {stock}: {e}")
