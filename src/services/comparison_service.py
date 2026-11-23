"""Stock comparison service.

Provides multi-stock normalized performance indexing (base 100),
comparative fundamental ratios extraction, cross-sectional technical indicators,
and objective numerical summary analysis across 2 to 6 instruments.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import streamlit as st

from src.config import TIMEFRAME_PRESETS
from src.services.financial_service import format_currency_value
from src.services.indicators import calculate_all_indicators
from src.services.market_data import (
    fetch_stock_history,
    fetch_stock_info,
    sanitize_ticker,
)


def validate_comparison_tickers(raw_tickers: List[str], max_tickers: int = 6) -> Tuple[List[str], Optional[str]]:
    """Sanitize, deduplicate, and validate a list of tickers for comparison (2 to 6)."""
    sanitized: List[str] = []
    seen = set()

    for item in raw_tickers:
        clean = sanitize_ticker(item)
        if clean and clean not in seen:
            seen.add(clean)
            sanitized.append(clean)

    if len(sanitized) < 2:
        return sanitized, "Please provide at least 2 distinct valid stock symbols for comparison."
    if len(sanitized) > max_tickers:
        sanitized = sanitized[:max_tickers]

    return sanitized, None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_comparison_performance(
    tickers: List[str], timeframe: str = "1Y"
) -> Dict[str, Any]:
    """Fetch and align normalized price performance (Base = 100 at period start)."""
    clean_tickers, err = validate_comparison_tickers(tickers)
    if err or not clean_tickers:
        return {"error": err or "Invalid ticker selection."}

    preset = TIMEFRAME_PRESETS.get(timeframe, TIMEFRAME_PRESETS["1Y"])
    period = preset["period"]
    interval = preset["interval"]

    price_series_dict: Dict[str, pd.Series] = {}
    returns_map: Dict[str, float] = {}
    chart_series: Dict[str, Dict[str, Any]] = {}

    for t in clean_tickers:
        res = fetch_stock_history(t, period=period, interval=interval)
        df = res[0] if isinstance(res, tuple) else res
        if df is not None and not df.empty and "Close" in df.columns:
            close = df["Close"].dropna()
            if len(close) > 1:
                p0 = float(close.iloc[0])
                p_end = float(close.iloc[-1])
                if p0 > 0:
                    normalized = (close / p0) * 100.0
                    price_series_dict[t] = normalized
                    ret_pct = ((p_end - p0) / p0) * 100.0
                    returns_map[t] = round(ret_pct, 2)

                    # Prepare date labels & values
                    dates = [
                        idx.strftime("%Y-%m-%d %H:%M") if hasattr(idx, "strftime") else str(idx)
                        for idx in normalized.index
                    ]
                    chart_series[t] = {
                        "dates": dates,
                        "values": [round(float(v), 2) for v in normalized.values],
                        "initial_price": round(p0, 2),
                        "latest_price": round(p_end, 2),
                        "return_pct": round(ret_pct, 2),
                    }

    if len(chart_series) < 2:
        return {
            "error": "Insufficient historical data available to compare the selected stocks."
        }

    # Best and worst performer
    sorted_by_ret = sorted(returns_map.items(), key=lambda x: x[1], reverse=True)
    best_performer = sorted_by_ret[0]
    worst_performer = sorted_by_ret[-1]

    return {
        "timeframe": timeframe,
        "tickers": list(chart_series.keys()),
        "chart_series": chart_series,
        "returns_map": returns_map,
        "best_performer": {"ticker": best_performer[0], "return_pct": best_performer[1]},
        "worst_performer": {"ticker": worst_performer[0], "return_pct": worst_performer[1]},
    }


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_comparison_fundamentals(tickers: List[str]) -> List[Dict[str, Any]]:
    """Fetch comparative fundamental metrics across selected stocks."""
    clean_tickers, _ = validate_comparison_tickers(tickers)
    results = []

    for t in clean_tickers:
        info_res = fetch_stock_info(t)
        info = (info_res[0] if isinstance(info_res, tuple) else info_res) or {}
        currency = info.get("currency", "USD")
        curr_sym = "$" if currency == "USD" else f"{currency} "

        mcap = info.get("marketCap")
        pe = info.get("trailingPE")
        fwd_pe = info.get("forwardPE")
        eps = info.get("trailingEps")
        rev = info.get("totalRevenue")
        net_inc = info.get("netIncomeToCommon")
        pm = info.get("profitMargins")
        roe = info.get("returnOnEquity")
        dte = info.get("debtToEquity")
        div_yield = info.get("dividendYield")
        beta = info.get("beta")

        results.append(
            {
                "ticker": t,
                "name": info.get("shortName") or info.get("longName") or t,
                "currency": currency,
                "currency_symbol": curr_sym,
                "market_cap": mcap,
                "market_cap_formatted": format_currency_value(mcap, curr_sym) if mcap else "N/A",
                "pe_ratio": round(float(pe), 2) if pe and pd.notna(pe) else None,
                "forward_pe": round(float(fwd_pe), 2) if fwd_pe and pd.notna(fwd_pe) else None,
                "eps": round(float(eps), 2) if eps and pd.notna(eps) else None,
                "revenue": rev,
                "revenue_formatted": format_currency_value(rev, curr_sym) if rev else "N/A",
                "net_income": net_inc,
                "net_income_formatted": format_currency_value(net_inc, curr_sym) if net_inc else "N/A",
                "profit_margin": round(float(pm) * 100.0, 2) if pm and pd.notna(pm) else None,
                "roe": round(float(roe) * 100.0, 2) if roe and pd.notna(roe) else None,
                "debt_to_equity": round(float(dte) / 100.0, 2) if dte and pd.notna(dte) else None,
                "dividend_yield": round(float(div_yield) * 100.0, 2) if div_yield and pd.notna(div_yield) else None,
                "beta": round(float(beta), 2) if beta and pd.notna(beta) else None,
            }
        )
    return results


@st.cache_data(ttl=300, show_spinner=False)
def fetch_comparison_technicals(tickers: List[str], timeframe: str = "1Y") -> List[Dict[str, Any]]:
    """Compute and align technical indicators across selected stocks."""
    clean_tickers, _ = validate_comparison_tickers(tickers)
    results = []

    for t in clean_tickers:
        res = fetch_stock_history(t, period="1y", interval="1d")
        df = res[0] if isinstance(res, tuple) else res
        if df is None or df.empty or len(df) < 50:
            results.append({"ticker": t, "has_data": False})
            continue

        df_ind = calculate_all_indicators(df)
        last_row = df_ind.iloc[-1]
        prev_row = df_ind.iloc[-2] if len(df_ind) > 1 else last_row

        close_val = float(last_row["Close"])
        rsi_val = float(last_row["RSI"]) if "RSI" in last_row and pd.notna(last_row["RSI"]) else None
        macd_val = float(last_row["MACD"]) if "MACD" in last_row and pd.notna(last_row["MACD"]) else None
        
        # MACD Signal
        sig_col = "Signal_Line" if "Signal_Line" in last_row else ("MACD_Signal" if "MACD_Signal" in last_row else None)
        signal_val = float(last_row[sig_col]) if sig_col and pd.notna(last_row[sig_col]) else None
        
        # SMA 50 and 200
        sma50_col = "MA50" if "MA50" in last_row else ("SMA50" if "SMA50" in last_row else None)
        sma50_val = float(last_row[sma50_col]) if sma50_col and pd.notna(last_row[sma50_col]) else None

        sma200_col = "MA200" if "MA200" in last_row else ("SMA200" if "SMA200" in last_row else None)
        sma200_val = float(last_row[sma200_col]) if sma200_col and pd.notna(last_row[sma200_col]) else None

        # Bollinger Band %B
        upper_bb = float(last_row.get("BB_Upper", np.nan))
        lower_bb = float(last_row.get("BB_Lower", np.nan))
        if pd.notna(upper_bb) and pd.notna(lower_bb) and (upper_bb - lower_bb) > 0:
            pct_b = (close_val - lower_bb) / (upper_bb - lower_bb)
        else:
            pct_b = None

        # Annualized Historical Volatility (252-day log return std)
        log_rets = np.log(df["Close"] / df["Close"].shift(1)).dropna()
        if len(log_rets) > 20:
            ann_vol = float(log_rets.std() * np.sqrt(252) * 100.0)
        else:
            ann_vol = None

        results.append(
            {
                "ticker": t,
                "has_data": True,
                "latest_price": round(close_val, 2),
                "rsi": round(rsi_val, 1) if rsi_val is not None else None,
                "macd": round(macd_val, 2) if macd_val is not None else None,
                "macd_signal": round(signal_val, 2) if signal_val is not None else None,
                "macd_status": "Bullish" if (macd_val and signal_val and macd_val > signal_val) else "Bearish",
                "sma50": round(sma50_val, 2) if sma50_val is not None else None,
                "sma200": round(sma200_val, 2) if sma200_val is not None else None,
                "vs_sma50": "Above" if (sma50_val and close_val > sma50_val) else "Below",
                "vs_sma200": "Above" if (sma200_val and close_val > sma200_val) else "Below",
                "bb_percent_b": round(pct_b, 2) if pct_b is not None else None,
                "annualized_volatility": round(ann_vol, 2) if ann_vol is not None else None,
            }
        )

    return results


def generate_comparison_summary(
    performance_data: Dict[str, Any],
    fundamentals: List[Dict[str, Any]],
    technicals: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Identify cross-sectional benchmark leaders with strict disclaimer guards."""
    summary: Dict[str, Any] = {}

    # 1. Best Historical Performer
    best_p = performance_data.get("best_performer")
    if best_p:
        summary["best_performer"] = f"{best_p['ticker']} ({best_p['return_pct']:+.2f}%)"

    # 2. Lowest P/E Ratio (positive trailing P/E only)
    positive_pes = [
        (f["ticker"], f["pe_ratio"])
        for f in fundamentals
        if f.get("pe_ratio") is not None and f["pe_ratio"] > 0
    ]
    if positive_pes:
        positive_pes.sort(key=lambda x: x[1])
        summary["lowest_pe"] = f"{positive_pes[0][0]} ({positive_pes[0][1]:.2f}x)"

    # 3. Highest Market Capitalization
    valid_mcaps = [
        (f["ticker"], f["market_cap"], f.get("market_cap_formatted"))
        for f in fundamentals
        if f.get("market_cap") is not None
    ]
    if valid_mcaps:
        valid_mcaps.sort(key=lambda x: x[1], reverse=True)
        summary["highest_mcap"] = f"{valid_mcaps[0][0]} ({valid_mcaps[0][2]})"

    # 4. Highest ROE
    valid_roes = [
        (f["ticker"], f["roe"])
        for f in fundamentals
        if f.get("roe") is not None
    ]
    if valid_roes:
        valid_roes.sort(key=lambda x: x[1], reverse=True)
        summary["highest_roe"] = f"{valid_roes[0][0]} ({valid_roes[0][1]:+.2f}%)"

    # 5. Lowest Volatility
    valid_vols = [
        (t["ticker"], t["annualized_volatility"])
        for t in technicals
        if t.get("annualized_volatility") is not None
    ]
    if valid_vols:
        valid_vols.sort(key=lambda x: x[1])
        summary["lowest_volatility"] = f"{valid_vols[0][0]} ({valid_vols[0][1]:.2f}%)"

    return summary
