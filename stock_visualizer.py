# stock_visualizer.py

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ----------------- STREAMLIT APP -----------------
st.set_page_config(page_title="Stock Price Visualizer", layout="wide")

st.title("📊 Stock Price Visualizer")
st.markdown("Visualize historical stock prices with moving averages and volume.")

# User Inputs
ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL, TSLA, MSFT):", "AAPL")
start_date = pd.to_datetime(st.date_input("Start Date", pd.to_datetime("2023-01-01")))
end_date = pd.to_datetime(st.date_input("End Date", pd.to_datetime("2023-12-31")))
add_ma = st.checkbox("Show Moving Averages (50 & 200 days)")
add_volume = st.checkbox("Show Volume Data")

# Fetch Data
if st.button("Get Stock Data"):
    try:
        if start_date > end_date:
            st.error("❌ Start Date cannot be after End Date.")
        else:
            data = yf.download(ticker, start=start_date, end=end_date)

            if data.empty:
                st.error("⚠️ No data found! Please check the ticker or date range.")
            else:
                st.success(f"✅ Showing data for {ticker}")
                st.dataframe(data.tail())  # Show last few rows

                # Plot Stock Price
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(data.index, data["Close"], label="Close Price", color="blue")

                # Moving Averages
                if add_ma:
                    data["50MA"] = data["Close"].rolling(window=50).mean()
                    data["200MA"] = data["Close"].rolling(window=200).mean()
                    ax.plot(data.index, data["50MA"], label="50-Day MA", color="orange")
                    ax.plot(data.index, data["200MA"], label="200-Day MA", color="red")

                ax.set_title(f"{ticker} Stock Price")
                ax.set_xlabel("Date")
                ax.set_ylabel("Price (USD)")
                ax.legend()
                st.pyplot(fig)

                # Volume Chart
                if add_volume:
                    fig, ax = plt.subplots(figsize=(12, 3))
                    ax.bar(data.index, data["Volume"], color="gray")
                    ax.set_title(f"{ticker} Trading Volume")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Volume")
                    st.pyplot(fig)

    except Exception as e:
        st.error(f"Error: {e}")
