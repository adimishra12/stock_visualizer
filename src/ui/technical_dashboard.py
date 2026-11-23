"""Technical Indicators dedicated workspace.

Interactive analysis suite supporting configurable parameters, synchronized
chart panels, quantitative signals, and educational tooltips for RSI, MACD,
Moving Averages, Bollinger Bands, VWAP, and ATR.
"""

from typing import Tuple
import pandas as pd
import streamlit as st

from src.services.indicators import (
    calculate_all_indicators,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    calculate_vwap,
)
from src.services.market_data import fetch_stock_history
from src.ui.charts import (
    create_atr_chart,
    create_macd_chart,
    create_price_chart,
    create_rsi_chart,
)


def render_technical_dashboard(ticker: str, theme_name: str = "light"):
    """Render the full Technical Indicators workspace."""
    if not ticker:
        st.info("Select a stock ticker in the sidebar to perform technical analysis.")
        return

    timeframe = st.session_state.get("timeframe", "1Y")

    st.markdown(
        f"""
        <div style="margin-bottom: 1.25rem;">
            <div style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.2rem;">
                🔬 Technical Analysis & Oscillators — {ticker}
            </div>
            <div style="font-size: 0.85rem; color: var(--text-secondary);">
                Deep quantitative indicator inspection with customizable parameters, volatility bands, and momentum oscillators.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Indicator Parameters & Configuration Drawer
    with st.expander("⚙️ Indicator Parameter Configuration", expanded=False):
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            rsi_period = st.slider("RSI Period (Wilder RMA)", min_value=5, max_value=30, value=14)
            atr_period = st.slider("ATR Period", min_value=5, max_value=30, value=14)
        with c_p2:
            bb_window = st.slider("Bollinger Bands Window", min_value=10, max_value=50, value=20)
            bb_std = st.slider("Bollinger Std Dev", min_value=1.0, max_value=3.5, value=2.0, step=0.1)
        with c_p3:
            fast_macd = st.slider("MACD Fast EMA", min_value=5, max_value=20, value=12)
            slow_macd = st.slider("MACD Slow EMA", min_value=21, max_value=40, value=26)
            sig_macd = st.slider("MACD Signal Line", min_value=5, max_value=15, value=9)

    # Fetch 1-year historical data for high-fidelity indicator computation
    with st.spinner(f"Computing quantitative indicators for {ticker}..."):
        df, err = fetch_stock_history(ticker=ticker, period="1y", interval="1d")

    if err or df is None or df.empty:
        st.error(f"⚠️ Could not load data for indicators: {err or 'Empty dataset'}")
        return

    # Calculate customized indicators
    df = calculate_all_indicators(
        df,
        sma_windows=[20, 50, 200],
        ema_spans=[9, 21, 50],
        rsi_period=rsi_period,
        macd_params=(fast_macd, slow_macd, sig_macd),
        bb_params=(bb_window, bb_std),
        atr_period=atr_period,
    )

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    # Current Indicator Signal Bar
    curr_rsi = latest.get("RSI")
    curr_macd = latest.get("MACD")
    curr_sig = latest.get("Signal_Line")
    curr_atr = latest.get("ATR")
    curr_close = latest["Close"]
    curr_bb_up = latest.get("BB_Upper")
    curr_bb_low = latest.get("BB_Lower")

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        if curr_rsi is not None and not pd.isna(curr_rsi):
            if curr_rsi >= 70:
                rsi_badge = "badge-negative"
                rsi_state = "Overbought"
            elif curr_rsi <= 30:
                rsi_badge = "badge-positive"
                rsi_state = "Oversold"
            else:
                rsi_badge = "badge-neutral"
                rsi_state = "Neutral"

            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">RSI ({rsi_period})</div>
                    <div class="metric-tile-value">{curr_rsi:.1f}</div>
                    <div style="margin-top: 0.35rem;">
                        <span class="badge {rsi_badge}">{rsi_state}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_s2:
        if curr_macd is not None and curr_sig is not None and not pd.isna(curr_macd):
            is_bull = curr_macd >= curr_sig
            macd_badge = "badge-positive" if is_bull else "badge-negative"
            macd_state = "Bullish Momentum" if is_bull else "Bearish Momentum"

            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">MACD Line / Signal</div>
                    <div class="metric-tile-value">{curr_macd:.2f}</div>
                    <div style="margin-top: 0.35rem;">
                        <span class="badge {macd_badge}">{macd_state}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_s3:
        if curr_bb_up is not None and not pd.isna(curr_bb_up):
            if curr_close >= curr_bb_up:
                bb_state = "Piercing Upper Band"
                bb_badge = "badge-negative"
            elif curr_close <= curr_bb_low:
                bb_state = "Piercing Lower Band"
                bb_badge = "badge-positive"
            else:
                bb_state = "Inside Bands"
                bb_badge = "badge-neutral"

            bandwidth = ((curr_bb_up - curr_bb_low) / latest["BB_Middle"]) * 100.0

            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">Bollinger Bandwidth</div>
                    <div class="metric-tile-value">{bandwidth:.1f}%</div>
                    <div style="margin-top: 0.35rem;">
                        <span class="badge {bb_badge}">{bb_state}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_s4:
        if curr_atr is not None and not pd.isna(curr_atr):
            atr_pct = (curr_atr / curr_close) * 100.0
            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">Average True Range (14)</div>
                    <div class="metric-tile-value">${curr_atr:.2f}</div>
                    <div style="margin-top: 0.35rem;">
                        <span class="badge badge-neutral">±{atr_pct:.1f}% Daily Volatility</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Active Overlay Selection
    c_tog1, c_tog2, c_tog3 = st.columns(3)
    with c_tog1:
        show_sma = st.checkbox("Show SMAs (20, 50, 200)", value=True, key="td_sma")
    with c_tog2:
        show_ema = st.checkbox("Show EMAs (9, 21)", value=True, key="td_ema")
    with c_tog3:
        show_bb = st.checkbox("Show Bollinger Bands", value=True, key="td_bb")

    # Primary Synchronized Price Chart with Active Overlays
    price_fig = create_price_chart(
        df=df,
        ticker=ticker,
        chart_type="candlestick",
        show_ma20=show_sma,
        show_ma50=show_sma,
        show_ma200=show_sma,
        show_ema9=show_ema,
        show_ema21=show_ema,
        show_bb=show_bb,
        show_vwap=True,
        theme_name=theme_name,
    )
    st.plotly_chart(price_fig, use_container_width=True, key=f"technical_price_chart_{ticker}_{timeframe}")

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Synchronized Oscillators
    col_osc1, col_osc2 = st.columns(2)
    with col_osc1:
        st.plotly_chart(
            create_rsi_chart(df, theme_name=theme_name),
            use_container_width=True,
            key=f"technical_rsi_chart_{ticker}",
        )
    with col_osc2:
        st.plotly_chart(
            create_macd_chart(df, theme_name=theme_name),
            use_container_width=True,
            key=f"technical_macd_chart_{ticker}",
        )

    st.plotly_chart(
        create_atr_chart(df, theme_name=theme_name),
        use_container_width=True,
        key=f"technical_atr_chart_{ticker}",
    )

    # Educational Indicator Guide
    with st.expander("📖 Indicator Methodology & Mathematical Formulas", expanded=False):
        st.markdown(
            """
            * **RSI (Relative Strength Index)**: Momentum oscillator measuring speed and change of price movements on a scale from 0 to 100 with Welles Wilder exponential smoothing. Values above 70 indicate overbought conditions; values below 30 indicate oversold conditions.
            * **MACD (Moving Average Convergence Divergence)**: Trend-following momentum indicator displaying the relationship between two exponential moving averages ($12\\text{ EMA} - 26\\text{ EMA}$) with a $9\\text{ EMA}$ signal trigger line.
            * **Bollinger Bands**: Volatility bands placed 2 standard deviations above and below a 20-day simple moving average. Bands contract during low volatility and expand during high volatility.
            * **VWAP (Volume Weighted Average Price)**: Benchmark representing the average price weighted by cumulative volume, calculated as $\\frac{\\sum (\\text{Typical Price} \\times \\text{Volume})}{\\sum \\text{Volume}}$.
            * **ATR (Average True Range)**: Technical volatility indicator based on Welles Wilder's smoothing of the true price range over 14 sessions.
            """
        )
