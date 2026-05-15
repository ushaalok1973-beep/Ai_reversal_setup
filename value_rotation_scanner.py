import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

stocks = [
    "BEL.NS",
    "RVNL.NS",
    "HAL.NS",
    "KAYNES.NS",
    "CGPOWER.NS"
]

print("Loaded Stock Universe:")

for stock in stocks:
    print(stock)

results = []

for stock in stocks:

    try:

        print(f"\nDownloading data for {stock}...")

        df = yf.download(
            stock,
            period="6mo",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            print(f"No data for {stock}")
            continue

        # Convert columns to proper Series
        close_series = df["Close"].squeeze()
        volume_series = df["Volume"].squeeze()

        # RSI
        rsi = RSIIndicator(
            close=close_series,
            window=14
        ).rsi()

        latest_close = round(
            float(close_series.iloc[-1]),
            2
        )

        prev_close = round(
            float(close_series.iloc[-2]),
            2
        )

        latest_rsi = round(
            float(rsi.iloc[-1]),
            2
        )

        latest_volume = int(
            volume_series.iloc[-1]
        )

        avg_volume = int(
            volume_series.rolling(20).mean().iloc[-1]
        )

        price_change = round(
            ((latest_close - prev_close) / prev_close) * 100,
            2
        )

        volume_ratio = round(
            latest_volume / avg_volume,
            2
        )

        score = 0

        if latest_rsi > 55:
            score += 1

        if price_change > 1:
            score += 1

        if volume_ratio > 1.2:
            score += 1

        results.append({
            "Stock": stock,
            "Close": latest_close,
            "RSI": latest_rsi,
            "Price Change %": price_change,
            "Volume Ratio": volume_ratio,
            "Score": score
        })

        print(f"Processed: {stock}")

    except Exception as e:
        print(f"Error in {stock}: {e}")

if len(results) > 0:

    result_df = pd.DataFrame(results)

    result_df = result_df.sort_values(
        by="Score",
        ascending=False
    )

    print("\nVALUE ROTATION RESULTS\n")

    print(result_df.to_string(index=False))

    result_df.to_csv(
        "value_rotation_results.csv",
        index=False
    )

    print("\nCSV saved successfully.")

else:

    print("\nNo valid stocks processed.")
