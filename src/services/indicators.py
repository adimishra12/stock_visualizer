"""Technical indicator calculations engine.

Provides vectorized Pandas/NumPy implementations of:
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- RSI (Relative Strength Index with Welles Wilder's smoothing)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- VWAP (Volume Weighted Average Price)
- ATR (Average True Range with Welles Wilder's smoothing)

All calculations handle edge cases: zero volume, missing bars, division-by-zero,
and avoid in-place mutations of source DataFrames.
"""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd


def calculate_sma(series: pd.Series, window: int = 20) -> pd.Series:
    """Calculate Simple Moving Average (SMA).

    Formula:
        SMA_t = (1 / n) * sum_{i=0}^{n-1} P_{t-i}
    """
    if window <= 0:
        raise ValueError("SMA window must be greater than 0.")
    if series.empty or len(series) < window:
        return pd.Series(np.nan, index=series.index, dtype=float)
    return series.rolling(window=window, min_periods=window).mean()


def calculate_ema(series: pd.Series, span: int = 20) -> pd.Series:
    """Calculate Exponential Moving Average (EMA).

    Formula:
        alpha = 2 / (span + 1)
        EMA_t = alpha * P_t + (1 - alpha) * EMA_{t-1}
    """
    if span <= 0:
        raise ValueError("EMA span must be greater than 0.")
    if series.empty or len(series) < span:
        return pd.Series(np.nan, index=series.index, dtype=float)
    return series.ewm(span=span, min_periods=span, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI) using Welles Wilder's smoothing (RMA).

    Formula:
        delta = Close_t - Close_{t-1}
        U = max(delta, 0), D = max(-delta, 0)
        AvgGain_t = (AvgGain_{t-1} * (period - 1) + U_t) / period (Wilder's RMA)
        AvgLoss_t = (AvgLoss_{t-1} * (period - 1) + D_t) / period
        RS = AvgGain / AvgLoss
        RSI = 100 - (100 / (1 + RS))
    """
    if period <= 0:
        raise ValueError("RSI period must be greater than 0.")
    if series.empty or len(series) <= period:
        return pd.Series(np.nan, index=series.index, dtype=float)

    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    # Wilder's Smoothing / RMA is an exponential moving average with alpha = 1 / period
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    # Calculate RS and RSI handling zero-loss / zero-gain conditions
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # Boundary conditions when avg_loss is 0 (pure gain -> 100) or avg_gain is 0 (pure loss -> 0)
    rsi = rsi.where(~(avg_loss == 0.0), 100.0)
    rsi = rsi.where(~(avg_gain == 0.0), 0.0)
    rsi = rsi.where(~((avg_loss == 0.0) & (avg_gain == 0.0)), 50.0)

    # Ensure NaN for periods prior to min_periods
    rsi.iloc[:period] = np.nan
    return rsi


def calculate_macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Moving Average Convergence Divergence (MACD).

    Formula:
        MACD Line = EMA(fast_period) - EMA(slow_period)
        Signal Line = EMA(MACD Line, signal_period)
        Histogram = MACD Line - Signal Line
    """
    if fast_period >= slow_period:
        raise ValueError("fast_period must be smaller than slow_period.")
    if series.empty or len(series) < slow_period:
        empty = pd.Series(np.nan, index=series.index, dtype=float)
        return empty, empty, empty

    fast_ema = series.ewm(span=fast_period, min_periods=fast_period, adjust=False).mean()
    slow_ema = series.ewm(span=slow_period, min_periods=slow_period, adjust=False).mean()
    macd_line = fast_ema - slow_ema

    signal_line = macd_line.ewm(
        span=signal_period, min_periods=signal_period, adjust=False
    ).mean()
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands.

    Formula:
        Middle Band = SMA(window)
        Upper Band = Middle Band + num_std * StdDev(window)
        Lower Band = Middle Band - num_std * StdDev(window)
    """
    if window <= 0:
        raise ValueError("Bollinger Bands window must be greater than 0.")
    if series.empty or len(series) < window:
        empty = pd.Series(np.nan, index=series.index, dtype=float)
        return empty, empty, empty

    middle_band = series.rolling(window=window, min_periods=window).mean()
    std_dev = series.rolling(window=window, min_periods=window).std()

    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)

    return upper_band, middle_band, lower_band


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate Volume Weighted Average Price (VWAP).

    Formula:
        Typical Price (TP) = (High + Low + Close) / 3
        VWAP = cumsum(TP * Volume) / cumsum(Volume)

    For intraday data (sub-daily timestamps), VWAP resets daily at the session start.
    For daily data, cumulative VWAP over the requested timeframe is calculated.
    Handles zero volume and missing bars safely.
    """
    required = {"High", "Low", "Close", "Volume"}
    if not required.issubset(df.columns) or df.empty:
        return pd.Series(np.nan, index=df.index, dtype=float)

    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    volume = df["Volume"].fillna(0.0).clip(lower=0.0)
    price_volume = typical_price * volume

    # Check if intraday: index is DatetimeIndex and has time variation across entries
    is_intraday = False
    if isinstance(df.index, pd.DatetimeIndex) and len(df) > 1:
        # Check if timestamps have non-zero hour/minute or multiple bars in one day
        dates = df.index.normalize()
        if dates.nunique() < len(df):
            is_intraday = True

    if is_intraday:
        # Session-anchored: cumulative sum grouped by calendar day
        date_groups = df.index.normalize()
        cum_pv = price_volume.groupby(date_groups).cumsum()
        cum_vol = volume.groupby(date_groups).cumsum()
    else:
        # Daily: cumulative sum across the active series
        cum_pv = price_volume.cumsum()
        cum_vol = volume.cumsum()

    # Avoid division by zero: where cum_vol == 0, fallback to Typical Price
    vwap = cum_pv / cum_vol.replace(0.0, np.nan)
    vwap = vwap.fillna(typical_price)
    return vwap


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR) with Welles Wilder's smoothing.

    Formula:
        True Range (TR) = max(
            High_t - Low_t,
            |High_t - Close_{t-1}|,
            |Low_t - Close_{t-1}|
        )
        ATR = Wilder_RMA(TR, period)
    """
    required = {"High", "Low", "Close"}
    if not required.issubset(df.columns) or df.empty or len(df) < 2:
        return pd.Series(np.nan, index=df.index, dtype=float)

    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    true_range.iloc[0] = high.iloc[0] - low.iloc[0]

    # Welles Wilder smoothing on TR
    atr = true_range.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    atr.iloc[:period] = np.nan
    return atr


def calculate_all_indicators(
    df: pd.DataFrame,
    sma_windows: Optional[List[int]] = None,
    ema_spans: Optional[List[int]] = None,
    rsi_period: int = 14,
    macd_params: Tuple[int, int, int] = (12, 26, 9),
    bb_params: Tuple[int, float] = (20, 2.0),
    atr_period: int = 14,
) -> pd.DataFrame:
    """Calculate all technical indicators on a DataFrame returning an enriched copy.

    Never modifies the original DataFrame.
    """
    if df.empty:
        return df.copy()

    if sma_windows is None:
        sma_windows = [20, 50, 200]
    if ema_spans is None:
        ema_spans = [9, 21, 50]

    res = df.copy()

    # Simple Moving Averages
    for w in sma_windows:
        res[f"MA{w}"] = calculate_sma(res["Close"], window=w)

    # Exponential Moving Averages
    for s in ema_spans:
        res[f"EMA{s}"] = calculate_ema(res["Close"], span=s)

    # RSI (Wilder's Smoothing)
    res["RSI"] = calculate_rsi(res["Close"], period=rsi_period)

    # MACD
    fast_p, slow_p, sig_p = macd_params
    macd_l, sig_l, hist = calculate_macd(
        res["Close"], fast_period=fast_p, slow_period=slow_p, signal_period=sig_p
    )
    res["MACD"] = macd_l
    res["Signal_Line"] = sig_l
    res["MACD_Histogram"] = hist

    # Bollinger Bands
    bb_window, bb_std = bb_params
    bb_up, bb_mid, bb_low = calculate_bollinger_bands(
        res["Close"], window=bb_window, num_std=bb_std
    )
    res["BB_Upper"] = bb_up
    res["BB_Middle"] = bb_mid
    res["BB_Lower"] = bb_low

    # VWAP (if Volume present)
    if "Volume" in res.columns:
        res["VWAP"] = calculate_vwap(res)

    # ATR
    res["ATR"] = calculate_atr(res, period=atr_period)

    return res
