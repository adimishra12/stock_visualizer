"""Stock Analysis workspace view.

Provides company intelligence headers, key valuation metrics, interactive
candlestick/line charts with timeframe selectors, and historical CSV export.
"""

from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

from src.config import DEFAULT_TIMEFRAME, TIMEFRAME_PRESETS
from src.services.indicators import calculate_all_indicators
from src.services.market_data import (
    fetch_stock_history,
    fetch_stock_info,
    get_stock_metrics,
)
from src.ui.charts import (
    create_atr_chart,
    create_macd_chart,
    create_price_chart,
    create_rsi_chart,
)


def format_large_number(num) -> str:
    """Format market cap and volume figures."""
    if num is None or pd.isna(num):
        return "N/A"
    if num >= 1e12:
        return f"${num/1e12:.2f}T"
    elif num >= 1e9:
        return f"${num/1e9:.2f}B"
    elif num >= 1e6:
        return f"${num/1e6:.2f}M"
    else:
        return f"${num:,.2f}"


BENCHMARK_NAMES = {
    "^GSPC": "S&P 500 Index",
    "^DJI": "Dow Jones Industrial Average",
    "^IXIC": "Nasdaq Composite Index",
    "^RUT": "Russell 2000 Index",
    "CL=F": "Crude Oil (WTI Futures)",
    "GC=F": "Gold Futures",
    "^TNX": "10-Year US Treasury Yield",
    "BTC-USD": "Bitcoin (USD)",
    "ETH-USD": "Ethereum (USD)",
}


def render_company_header(metrics: dict, ticker: str, timeframe_label: str, theme_name: str):
    """Render the top company intelligence header."""
    raw_name = metrics.get("company_name")
    company_name = raw_name if (raw_name and raw_name != ticker) else (BENCHMARK_NAMES.get(ticker) or ticker)
    sector = metrics.get("sector", "")
    industry = metrics.get("industry", "")
    currency = metrics.get("currency", "USD")

    st.markdown(
        f"""
        <div class="company-banner">
            <div>
                <div class="company-name">{company_name}</div>
                <div class="company-meta">
                    <span class="badge badge-neutral" style="font-weight:700;">{ticker}</span>
                    <span>{'• ' + sector if sector else ''}</span>
                    <span>{'• ' + industry if industry else ''}</span>
                    <span>• Currency: {currency}</span>
                    <span>• Resolution: {timeframe_label}</span>
                </div>
            </div>
            <div>
                <span class="badge badge-neutral">Mode: {theme_name.capitalize()}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics_grid(metrics: dict):
    """Render financial metrics grid using clean fintech cards."""
    current_price = metrics["current_price"]
    prev_price = metrics["previous_close"]
    price_change = metrics["price_change"]
    price_change_pct = metrics["price_change_pct"]
    is_positive = price_change >= 0
    badge_class = "badge-positive" if is_positive else "badge-negative"
    change_arrow = "▲" if is_positive else "▼"

    week_high_disp = f"${metrics['fifty_two_week_high']:,.2f}"
    week_low_disp = f"${metrics['fifty_two_week_low']:,.2f}"
    day_high_disp = f"${metrics['day_high']:,.2f}"
    day_low_disp = f"${metrics['day_low']:,.2f}"

    # Price Hero & Session Summaries
    col_hero, col_ranges = st.columns([1, 1])

    with col_hero:
        st.markdown(
            f"""
            <div class="price-hero">
                <div class="metric-tile-label">Current Market Price</div>
                <div class="price-hero-value">${current_price:,.2f}</div>
                <div style="margin-top: 0.6rem;">
                    <span class="badge {badge_class}">
                        {change_arrow} ${abs(price_change):,.2f} ({price_change_pct:+.2f}%)
                    </span>
                    <span style="font-size: 0.8rem; color: var(--text-secondary); margin-left: 0.5rem;">
                        Prev Close: ${prev_price:,.2f}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_ranges:
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(
                f"""
                <div class="metric-tile" style="margin-bottom: 0.75rem;">
                    <div class="metric-tile-label">Session High</div>
                    <div class="metric-tile-value" style="font-size: 1.25rem; color: var(--color-positive);">{day_high_disp}</div>
                </div>
                <div class="metric-tile">
                    <div class="metric-tile-label">52-Week High</div>
                    <div class="metric-tile-value" style="font-size: 1.25rem;">{week_high_disp}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r2:
            st.markdown(
                f"""
                <div class="metric-tile" style="margin-bottom: 0.75rem;">
                    <div class="metric-tile-label">Session Low</div>
                    <div class="metric-tile-value" style="font-size: 1.25rem; color: var(--color-negative);">{day_low_disp}</div>
                </div>
                <div class="metric-tile">
                    <div class="metric-tile-label">52-Week Low</div>
                    <div class="metric-tile-value" style="font-size: 1.25rem;">{week_low_disp}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Fundamental Financials
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Market Capitalization</div>
                <div class="metric-tile-value">{format_large_number(metrics.get('market_cap'))}</div>
                <div class="metric-tile-subtext">Total valuation</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        pe_val = metrics.get("trailing_pe")
        pe_disp = f"{pe_val:.2f}" if pe_val else "N/A"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Trailing P/E</div>
                <div class="metric-tile-value">{pe_disp}</div>
                <div class="metric-tile-subtext">Price to earnings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        div_val = metrics.get("dividend_yield")
        div_disp = f"{div_val*100:.2f}%" if div_val else "N/A"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Dividend Yield</div>
                <div class="metric-tile-value">{div_disp}</div>
                <div class="metric-tile-subtext">Annual payout</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        eps_val = metrics.get("eps")
        eps_disp = f"${eps_val:.2f}" if eps_val else "N/A"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Diluted EPS (TTM)</div>
                <div class="metric-tile-value">{eps_disp}</div>
                <div class="metric-tile-subtext">Earnings per share</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        vol = metrics.get("volume")
        vol_disp = f"{vol:,.0f}" if vol else "N/A"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Recent Volume</div>
                <div class="metric-tile-value" style="font-size: 1.25rem;">{vol_disp}</div>
                <div class="metric-tile-subtext">Session volume</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c6:
        beta_val = metrics.get("beta")
        beta_disp = f"{beta_val:.2f}" if beta_val else "N/A"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Beta (5Y Monthly)</div>
                <div class="metric-tile-value">{beta_disp}</div>
                <div class="metric-tile-subtext">Market sensitivity</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c7:
        fpe_val = metrics.get("forward_pe")
        fpe_disp = f"{fpe_val:.2f}" if fpe_val else "N/A"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Forward P/E</div>
                <div class="metric-tile-value">{fpe_disp}</div>
                <div class="metric-tile-subtext">Projected ratio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c8:
        pb_val = metrics.get("price_to_book")
        pb_disp = f"{pb_val:.2f}" if pb_val else "N/A"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Price to Book</div>
                <div class="metric-tile-value">{pb_disp}</div>
                <div class="metric-tile-subtext">Asset valuation</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_stock_analysis(ticker: str, theme_name: str = "light"):
    """Render the full Stock Analysis workspace."""
    if not ticker:
        st.info("Select or enter a stock ticker symbol to begin analysis.")
        return

    # Timeframe Selector Bar
    col_tf_btns, col_chart_type = st.columns([7, 3])

    with col_tf_btns:
        st.markdown(
            "<div style='font-size:0.75rem; color:var(--text-secondary); font-weight:600; margin-bottom:0.25rem;'>TIMEFRAME</div>",
            unsafe_allow_html=True,
        )
        tf_keys = list(TIMEFRAME_PRESETS.keys())
        cols = st.columns(len(tf_keys))
        for idx, key in enumerate(tf_keys):
            with cols[idx]:
                is_sel = (
                    st.session_state.get("timeframe") == key
                    and st.session_state.get("date_mode", "preset") == "preset"
                )
                btn_txt = f"● {key}" if is_sel else key
                if st.button(btn_txt, key=f"sa_tf_{key}", use_container_width=True):
                    st.session_state.timeframe = key
                    st.session_state.date_mode = "preset"
                    st.rerun()

    with col_chart_type:
        st.markdown(
            "<div style='font-size:0.75rem; color:var(--text-secondary); font-weight:600; margin-bottom:0.25rem;'>CHART STYLE</div>",
            unsafe_allow_html=True,
        )
        chart_style = st.radio(
            "Chart Type",
            options=["Candlestick", "Line"],
            index=0 if st.session_state.get("chart_style", "Candlestick") == "Candlestick" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="sa_chart_style_radio",
        )
        st.session_state.chart_style = chart_style

    # Resolve active period / interval
    date_mode = st.session_state.get("date_mode", "preset")
    if date_mode == "preset":
        tf_key = st.session_state.get("timeframe", DEFAULT_TIMEFRAME)
        tf_info = TIMEFRAME_PRESETS.get(tf_key, TIMEFRAME_PRESETS[DEFAULT_TIMEFRAME])
        f_period = tf_info["period"]
        f_interval = tf_info["interval"]
        f_start = None
        f_end = None
        tf_label = tf_info["description"]
        selected_timeframe = tf_key
    else:
        f_period = None
        f_interval = "1d"
        f_start = st.session_state.get("custom_start_date")
        f_end = st.session_state.get("custom_end_date")
        tf_label = "Custom Date Range"
        tf_info = {
            "period": None,
            "interval": "1d",
            "is_intraday": False,
            "description": "Custom Date Range",
        }
        selected_timeframe = f"custom_{f_start}_{f_end}"

    # Fetch data
    with st.spinner(f"Fetching data for {ticker}..."):
        df, price_err = fetch_stock_history(
            ticker=ticker,
            period=f_period,
            interval=f_interval,
            start_date=f_start,
            end_date=f_end,
        )
        info, info_err = fetch_stock_info(ticker)

    if price_err:
        st.error(f"⚠️ {price_err}")
        return

    if df is None or df.empty:
        st.warning("No price action records found for this period.")
        return

    # Calculate indicators & derive metrics
    df = calculate_all_indicators(df)
    metrics = get_stock_metrics(df, info)

    # Render header & metrics
    render_company_header(metrics, ticker, tf_label, theme_name)
    render_metrics_grid(metrics)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Chart Controls & Overlay Options
    with st.expander("Chart Overlays & Indicator Settings", expanded=False):
        c_ov1, c_ov2, c_ov3, c_ov4 = st.columns(4)
        with c_ov1:
            show_ma20 = st.checkbox("20-Day SMA", value=True, key="sa_ma20")
            show_ma50 = st.checkbox("50-Day SMA", value=True, key="sa_ma50")
            show_ma200 = st.checkbox("200-Day SMA", value=False, key="sa_ma200")
        with c_ov2:
            show_ema9 = st.checkbox("9-Period EMA", value=False, key="sa_ema9")
            show_ema21 = st.checkbox("21-Period EMA", value=False, key="sa_ema21")
            show_vwap = st.checkbox("VWAP", value=False, key="sa_vwap")
        with c_ov3:
            show_bb = st.checkbox("Bollinger Bands", value=False, key="sa_bb")
            show_rsi = st.checkbox("RSI Oscillator", value=True, key="sa_rsi")
        with c_ov4:
            show_macd = st.checkbox("MACD Oscillator", value=True, key="sa_macd")
            show_atr = st.checkbox("ATR Volatility", value=False, key="sa_atr")

    # Main Interactive Price & Volume Chart
    price_chart = create_price_chart(
        df=df,
        ticker=ticker,
        chart_type=chart_style.lower(),
        show_ma20=show_ma20,
        show_ma50=show_ma50,
        show_ma200=show_ma200,
        show_ema9=show_ema9,
        show_ema21=show_ema21,
        show_bb=show_bb,
        show_vwap=show_vwap,
        theme_name=theme_name,
    )
    st.plotly_chart(
        price_chart,
        use_container_width=True,
        key=f"stock_analysis_price_chart_{ticker}_{selected_timeframe}",
    )

    # Secondary Oscillators
    active_osc = [show_rsi, show_macd, show_atr]
    if any(active_osc):
        st.markdown(
            "<div class='section-title'>📊 Indicator Oscillators</div>",
            unsafe_allow_html=True,
        )
        osc_count = sum(active_osc)
        if osc_count == 1:
            if show_rsi:
                st.plotly_chart(
                    create_rsi_chart(df, theme_name=theme_name),
                    use_container_width=True,
                    key=f"stock_analysis_rsi_single_{ticker}",
                )
            elif show_macd:
                st.plotly_chart(
                    create_macd_chart(df, theme_name=theme_name),
                    use_container_width=True,
                    key=f"stock_analysis_macd_single_{ticker}",
                )
            elif show_atr:
                st.plotly_chart(
                    create_atr_chart(df, theme_name=theme_name),
                    use_container_width=True,
                    key=f"stock_analysis_atr_single_{ticker}",
                )
        elif osc_count == 2:
            co1, co2 = st.columns(2)
            figs = []
            if show_rsi:
                figs.append((create_rsi_chart(df, theme_name=theme_name), f"stock_analysis_rsi_duo_{ticker}"))
            if show_macd:
                figs.append((create_macd_chart(df, theme_name=theme_name), f"stock_analysis_macd_duo_{ticker}"))
            if show_atr:
                figs.append((create_atr_chart(df, theme_name=theme_name), f"stock_analysis_atr_duo_{ticker}"))
            with co1:
                st.plotly_chart(figs[0][0], use_container_width=True, key=figs[0][1])
            with co2:
                st.plotly_chart(figs[1][0], use_container_width=True, key=figs[1][1])
        else:
            co1, co2, co3 = st.columns(3)
            with co1:
                st.plotly_chart(
                    create_rsi_chart(df, theme_name=theme_name),
                    use_container_width=True,
                    key=f"stock_analysis_rsi_tri_{ticker}",
                )
            with co2:
                st.plotly_chart(
                    create_macd_chart(df, theme_name=theme_name),
                    use_container_width=True,
                    key=f"stock_analysis_macd_tri_{ticker}",
                )
            with co3:
                st.plotly_chart(
                    create_atr_chart(df, theme_name=theme_name),
                    use_container_width=True,
                    key=f"stock_analysis_atr_tri_{ticker}",
                )

    # Recent Data Table & Export
    st.markdown("<div class='section-title'>📋 Recent Trading Data</div>", unsafe_allow_html=True)
    table_df = df[["Open", "High", "Low", "Close", "Volume"]].tail(10).copy()
    table_df = table_df.round(2)
    table_df["Volume"] = table_df["Volume"].apply(lambda x: f"{x:,.0f}")
    table_df.index = table_df.index.strftime(
        "%Y-%m-%d %H:%M" if tf_info.get("is_intraday") else "%Y-%m-%d"
    )
    st.dataframe(table_df, use_container_width=True)

    c_e1, c_e2, c_e3 = st.columns([1, 1, 1])
    with c_e2:
        csv_bytes = df.to_csv()
        st.download_button(
            label="📥 Export Full Historical Data (CSV)",
            data=csv_bytes,
            file_name=f"{ticker}_{st.session_state.get('timeframe', '1Y')}_history.csv",
            mime="text/csv",
            use_container_width=True,
        )
