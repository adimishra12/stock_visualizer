"""Market data ingestion, caching, and financial metrics calculation service.

Uses yfinance with robust retry handling, exponential backoff, Streamlit caching,
and strict validation. Derives core price metrics directly from historical price
bars so the dashboard remains functional even when company metadata is throttled.
"""

from datetime import datetime, timedelta
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from src.config import (
    INTRADAY_MAX_DAYS,
    MARKET_OVERVIEW_SYMBOLS,
    TIMEFRAME_PRESETS,
)


def sanitize_ticker(ticker: Optional[str]) -> Optional[str]:
    """Sanitize and validate stock ticker symbols.

    Allows standard tickers, indices (^GSPC), commodities (CL=F),
    and crypto pairs (BTC-USD).
    """
    if not ticker:
        return None
    cleaned = ticker.strip().upper()
    cleaned = re.sub(r"[^A-Z0-9.\-^=]", "", cleaned)
    if len(cleaned) < 1 or len(cleaned) > 12:
        return None
    return cleaned


def validate_timeframe_interval(
    period: Optional[str] = None,
    interval: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Tuple[bool, Optional[str]]:
    """Validate timeframe and interval combinations against Yahoo Finance limitations."""
    interval = (interval or "1d").lower()

    # Determine date span in days
    days_span = 365
    if start_date and end_date:
        if start_date >= end_date:
            return False, "Start date must be strictly before end date."
        days_span = (end_date - start_date).days
    elif period:
        period_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 31,
            "3mo": 92,
            "6mo": 183,
            "ytd": 365,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
            "10y": 3650,
            "max": 36500,
        }
        days_span = period_map.get(period.lower(), 365)

    max_allowed_days = INTRADAY_MAX_DAYS.get(interval, 36500)
    if days_span > max_allowed_days:
        return (
            False,
            f"The '{interval}' interval is limited to {max_allowed_days} days of history by the data provider (requested span: {days_span} days).",
        )

    return True, None


@st.cache_data(ttl=900, show_spinner=False)
def fetch_stock_history(
    ticker: str,
    period: Optional[str] = None,
    interval: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    max_retries: int = 2,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Fetch and validate historical OHLCV stock data with caching and exponential retry.

    Returns:
        (df, None) on success, or (None, error_message) on failure.
    """
    clean_ticker = sanitize_ticker(ticker)
    if not clean_ticker:
        return None, f"Invalid ticker symbol: '{ticker}'."

    is_valid, validation_error = validate_timeframe_interval(
        period=period, interval=interval, start_date=start_date, end_date=end_date
    )
    if not is_valid:
        return None, validation_error

    last_error: Optional[str] = None

    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(clean_ticker)

            if start_date and end_date:
                df = stock.history(
                    start=start_date,
                    end=end_date,
                    interval=interval or "1d",
                    auto_adjust=False,
                    timeout=10,
                )
            elif period:
                df = stock.history(
                    period=period,
                    interval=interval or "1d",
                    auto_adjust=False,
                    timeout=10,
                )
            else:
                # Default fallback: 1 year daily
                df = stock.history(
                    period="1y",
                    interval="1d",
                    auto_adjust=False,
                    timeout=10,
                )

            if df is None or df.empty:
                last_error = f"No price records returned for '{clean_ticker}' within the selected timeframe."
                continue

            # Validate required columns
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            missing_cols = [c for c in required_cols if c not in df.columns]
            if missing_cols:
                last_error = f"Corrupted market data: missing columns {missing_cols} for '{clean_ticker}'."
                continue

            # Clean and sanitize dataframe
            df = df.copy()
            df = df[required_cols]

            # Convert to numeric, replace infs and drop rows where Close is NaN
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=["Close"])

            if df.empty:
                last_error = f"All price entries were invalid or empty for '{clean_ticker}'."
                continue

            # Ensure DatetimeIndex is sorted and tz-aware is consistently formatted
            if isinstance(df.index, pd.DatetimeIndex):
                df = df.sort_index()
                # Remove timezone offset for seamless Plotly synchronization
                if df.index.tz is not None:
                    df.index = df.index.tz_localize(None)

            return df, None

        except Exception as e:
            err_str = str(e)
            if "timeout" in err_str.lower():
                last_error = f"Request timed out while contacting Yahoo Finance (attempt {attempt + 1}/{max_retries})."
            elif "not found" in err_str.lower() or "404" in err_str:
                return None, f"Ticker '{clean_ticker}' was not found. Please verify the symbol."
            elif "too many requests" in err_str.lower() or "429" in err_str:
                last_error = "Rate limit reached on Yahoo Finance API. Please wait a moment before refreshing."
            else:
                last_error = f"Data acquisition error: {err_str}"

            if attempt < max_retries - 1:
                time.sleep(0.5 * (2**attempt))

    return None, last_error or "Unable to retrieve stock data."


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_stock_info(
    ticker: str, max_retries: int = 1
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch company metadata separately as optional enrichment."""
    clean_ticker = sanitize_ticker(ticker)
    if not clean_ticker:
        return None, "Invalid ticker symbol."

    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(clean_ticker)
            info = stock.info
            if not info or not isinstance(info, dict) or len(info) < 2:
                return None, f"No profile metadata found for '{clean_ticker}'."
            return info, None
        except Exception as e:
            err_str = str(e)
            if attempt == max_retries - 1:
                return None, f"Could not fetch company info: {err_str}"
            time.sleep(0.3)

    return None, "Metadata service temporarily unavailable."


def get_stock_metrics(
    df: pd.DataFrame, info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Calculate comprehensive stock metrics from historical OHLCV data.

    Historical price data is the primary truth. Metadata from info is used
    strictly as secondary enrichment, ensuring metrics never crash when info is throttled.
    """
    if df is None or df.empty:
        return {}

    info = info or {}

    # Primary price figures derived from df
    current_price = float(df["Close"].iloc[-1])
    if len(df) > 1:
        prev_close = float(df["Close"].iloc[-2])
    else:
        prev_close = float(info.get("previousClose") or current_price)

    price_change = current_price - prev_close
    price_change_pct = (price_change / prev_close) * 100.0 if prev_close != 0.0 else 0.0

    # Day range from recent session
    day_high = float(df["High"].iloc[-1])
    day_low = float(df["Low"].iloc[-1])
    volume = float(df["Volume"].iloc[-1])

    # If intraday data with multiple bars on the same day, take today's true high/low
    if isinstance(df.index, pd.DatetimeIndex) and len(df) > 1:
        last_date = df.index[-1].date()
        today_bars = df[df.index.date == last_date]
        if not today_bars.empty:
            day_high = float(today_bars["High"].max())
            day_low = float(today_bars["Low"].min())
            volume = float(today_bars["Volume"].sum())

    # 52-Week Range calculation from data
    rolling_252 = df.tail(252)
    calc_52w_high = float(rolling_252["High"].max())
    calc_52w_low = float(rolling_252["Low"].min())

    # Prefer info if it has official 52w extremes, else fallback to calculated
    fifty_two_week_high = float(info.get("fiftyTwoWeekHigh") or calc_52w_high)
    fifty_two_week_low = float(info.get("fiftyTwoWeekLow") or calc_52w_low)

    return {
        "current_price": current_price,
        "previous_close": prev_close,
        "price_change": price_change,
        "price_change_pct": price_change_pct,
        "day_high": day_high,
        "day_low": day_low,
        "volume": volume,
        "fifty_two_week_high": fifty_two_week_high,
        "fifty_two_week_low": fifty_two_week_low,
        # Secondary enrichment from info
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "eps": info.get("trailingEps"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "average_volume": info.get("averageVolume"),
        "price_to_book": info.get("priceToBook"),
        "company_name": info.get("longName"),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "currency": info.get("currency", "USD"),
        "summary": info.get("longBusinessSummary", ""),
    }


@st.cache_data(ttl=300, show_spinner=False)
def get_market_overview_data(
    symbols: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, Any]]:
    """Fetch snapshot data for major market indices, commodities, and benchmarks."""
    target_symbols = symbols or MARKET_OVERVIEW_SYMBOLS
    results = []

    for item in target_symbols:
        sym = item["symbol"]
        name = item.get("name", sym)
        sym_type = item.get("type", "Asset")

        try:
            ticker_obj = yf.Ticker(sym)
            hist = ticker_obj.history(period="5d", interval="1d", timeout=5)
            if hist is not None and len(hist) >= 2:
                curr = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                chg = curr - prev
                chg_pct = (chg / prev) * 100.0 if prev != 0 else 0.0

                sparkline = hist["Close"].tolist()

                results.append(
                    {
                        "symbol": sym,
                        "name": name,
                        "type": sym_type,
                        "current_price": curr,
                        "change": chg,
                        "change_pct": chg_pct,
                        "sparkline": sparkline,
                    }
                )
        except Exception:
            # Skip or gracefully omit failed snapshot symbols without breaking dashboard
            continue

    return results
