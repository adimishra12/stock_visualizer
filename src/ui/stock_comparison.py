"""Stock Comparison UI module.

Provides multi-stock ticker management (2 to 6 stocks), normalized performance indexing,
comparative fundamental analysis, cross-sectional technical comparison, and objective leaders summary.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import TIMEFRAME_PRESETS
from src.services.comparison_service import (
    fetch_comparison_fundamentals,
    fetch_comparison_performance,
    fetch_comparison_technicals,
    generate_comparison_summary,
    validate_comparison_tickers,
)
from src.ui.charts import get_chart_theme


# Preset peer groups for one-click comparison
COMPARISON_PRESETS = {
    "Big Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"],
    "Cloud & AI": ["MSFT", "GOOGL", "AMZN", "META", "NVDA", "ORCL"],
    "Semiconductors": ["NVDA", "AMD", "AVGO", "QCOM", "INTC", "TSM"],
    "Index ETFs": ["SPY", "QQQ", "DIA", "IWM", "VTI", "VOO"],
}


def _create_normalized_performance_chart(
    perf_data: Dict[str, Any], theme_name: str = "light"
) -> go.Figure:
    """Create a multi-trace normalized line chart starting at 100 for all stocks."""
    ct = get_chart_theme(theme_name)
    fig = go.Figure()

    chart_series = perf_data.get("chart_series", {})
    palette = [
        ct["accent_primary"],
        ct["accent_secondary"],
        ct["up_color"],
        "#F59E0B",
        "#EC4899",
        "#06B6D4",
    ]

    for idx, (ticker, s_data) in enumerate(chart_series.items()):
        color = palette[idx % len(palette)]
        dates = s_data["dates"]
        values = s_data["values"]
        ret = s_data["return_pct"]
        sign = "+" if ret >= 0 else ""

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                name=f"{ticker} ({sign}{ret:.2f}%)",
                mode="lines",
                line=dict(color=color, width=2.2),
                hovertemplate=f"<b>{ticker}</b><br>Index: %{{y:.2f}}<br>Date: %{{x}}<extra></extra>",
            )
        )

    # Reference 100 baseline line
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color=ct["border_color"],
        annotation_text="Base 100",
        annotation_font_color=ct["muted_color"],
        annotation_position="bottom right",
    )

    fig.update_layout(
        title=dict(
            text=f"Normalized Relative Performance (Base = 100) — {perf_data.get('timeframe', '1Y')}",
            x=0.0,
            y=0.96,
            xref="container",
            yref="container",
            xanchor="left",
            yanchor="top",
            font=dict(size=14, color=ct["font_color"], family=ct["font_family"]),
        ),
        height=380,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=15, r=15, t=80, b=15),
        font=dict(family=ct["font_family"], color=ct["font_color"]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=ct["muted_color"], size=11),
        ),
        xaxis=dict(gridcolor=ct["grid_color"], linecolor=ct["border_color"]),
        yaxis=dict(
            gridcolor=ct["grid_color"],
            linecolor=ct["border_color"],
            title=dict(text="Normalized Index", font=dict(color=ct["muted_color"], size=11)),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=ct["hover_bg"],
            bordercolor=ct["hover_border"],
            font=dict(color=ct["hover_font_color"], family=ct["font_family"]),
        ),
    )
    return fig


def render_stock_comparison(theme_name: str = "light") -> None:
    """Render the comprehensive stock comparison dashboard."""
    st.markdown(
        """
        <div class="company-banner">
            <div>
                <div class="company-name">⚖️ Multi-Stock Comparative Intelligence</div>
                <div class="company-meta">
                    <span>Cross-Sectional Benchmark (2 to 6 Stocks)</span>
                    <span>•</span>
                    <span>Normalized Performance (Base 100)</span>
                    <span>•</span>
                    <span>Fundamentals & Technicals Alignment</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Comparison Ticker Selection & Session State
    if "comparison_tickers" not in st.session_state:
        st.session_state.comparison_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"]

    # Preset shortcut pills
    st.markdown("<div style='font-size:0.78rem; color:var(--text-secondary); font-weight:600; margin-bottom:0.35rem;'>POPULAR PEER GROUPS</div>", unsafe_allow_html=True)
    p_cols = st.columns(len(COMPARISON_PRESETS))
    for idx, (p_name, p_ticks) in enumerate(COMPARISON_PRESETS.items()):
        with p_cols[idx]:
            if st.button(f"⚡ {p_name}", key=f"btn_comp_preset_{p_name}", use_container_width=True):
                st.session_state.comparison_tickers = list(p_ticks)
                st.rerun()

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Ticker management input bar
    col_input, col_add, col_tf = st.columns([5, 2, 3])
    with col_input:
        new_ticker = st.text_input(
            "Add Stock Symbol to Comparison (Max 6)",
            placeholder="e.g. AMZN, GOOGL, TSLA",
            key="comp_add_ticker_input",
        ).strip().upper()

    with col_add:
        st.markdown("<div style='height: 1.75rem;'></div>", unsafe_allow_html=True)
        if st.button("➕ Add Symbol", key="btn_add_comp_ticker", use_container_width=True):
            if new_ticker:
                valid, _ = validate_comparison_tickers([new_ticker], max_tickers=6)
                if not valid:
                    st.error(f"'{new_ticker}' is not a valid stock symbol.")
                elif new_ticker in st.session_state.comparison_tickers:
                    st.warning(f"'{new_ticker}' is already included in the comparison.")
                elif len(st.session_state.comparison_tickers) >= 6:
                    st.error("Maximum 6 stocks can be compared simultaneously.")
                else:
                    st.session_state.comparison_tickers.append(new_ticker)
                    st.rerun()

    with col_tf:
        comp_timeframe = st.selectbox(
            "Comparison Timeframe",
            list(TIMEFRAME_PRESETS.keys()),
            index=list(TIMEFRAME_PRESETS.keys()).index("1Y"),
            key="comp_timeframe_select",
        )

    # Active Ticker Badges with Remove Action
    current_tickers = st.session_state.comparison_tickers
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

    badge_cols = st.columns(len(current_tickers))
    for idx, t_sym in enumerate(current_tickers):
        with badge_cols[idx]:
            if st.button(f"✕ Remove {t_sym}", key=f"btn_rem_{t_sym}_{idx}", use_container_width=True):
                if len(st.session_state.comparison_tickers) <= 2:
                    st.error("At least 2 stocks are required for comparison.")
                else:
                    st.session_state.comparison_tickers.remove(t_sym)
                    st.rerun()

    valid_tickers, err = validate_comparison_tickers(st.session_state.comparison_tickers)
    if err:
        st.error(err)
        return

    # 2. Performance Intelligence
    with st.spinner(f"Computing normalized comparative performance across {len(valid_tickers)} instruments..."):
        perf_data = fetch_comparison_performance(valid_tickers, timeframe=comp_timeframe)

    if "error" in perf_data:
        st.error(perf_data["error"])
        return

    # 3. Performance Summary KPI Row
    st.markdown("<div class='section-title'>Historical Performance Overview</div>", unsafe_allow_html=True)
    best_p = perf_data.get("best_performer")
    worst_p = perf_data.get("worst_performer")
    ret_map = perf_data.get("returns_map", {})

    kpi_cols = st.columns(len(valid_tickers) + 2)
    with kpi_cols[0]:
        st.markdown(
            f"""
            <div class="metric-tile" style="border-color: var(--color-positive);">
                <div class="metric-tile-label">Top Performer</div>
                <div class="metric-tile-value" style="font-size: 1.25rem; color: var(--color-positive);">{best_p['ticker']}</div>
                <div class="metric-tile-subtext">{best_p['return_pct']:+.2f}% ({comp_timeframe})</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_cols[1]:
        st.markdown(
            f"""
            <div class="metric-tile" style="border-color: var(--color-negative);">
                <div class="metric-tile-label">Lagging Performer</div>
                <div class="metric-tile-value" style="font-size: 1.25rem; color: var(--color-negative);">{worst_p['ticker']}</div>
                <div class="metric-tile-subtext">{worst_p['return_pct']:+.2f}% ({comp_timeframe})</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for idx, t in enumerate(valid_tickers):
        ret = ret_map.get(t, 0.0)
        c_var = "var(--color-positive)" if ret >= 0 else "var(--color-negative)"
        with kpi_cols[idx + 2]:
            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">{t} Return</div>
                    <div class="metric-tile-value" style="font-size: 1.25rem; color: {c_var};">{ret:+.2f}%</div>
                    <div class="metric-tile-subtext">{comp_timeframe} Change</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # 4. Normalized Performance Chart
    fig_norm = _create_normalized_performance_chart(perf_data, theme_name=theme_name)
    st.plotly_chart(
        fig_norm,
        use_container_width=True,
        key=f"comparison_performance_chart_{'_'.join(valid_tickers)}_{comp_timeframe}",
    )

    # 5. Cross-Sectional Fundamentals Comparison
    st.markdown("<div class='section-title'>Fundamental Metrics Comparison</div>", unsafe_allow_html=True)
    with st.spinner("Retrieving valuation and financial fundamentals..."):
        fundamentals = fetch_comparison_fundamentals(valid_tickers)

    fund_rows = []
    for f in fundamentals:
        pe_str = f"{f['pe_ratio']:.2f}x" if f["pe_ratio"] is not None else "N/A"
        fwd_pe_str = f"{f['forward_pe']:.2f}x" if f["forward_pe"] is not None else "N/A"
        eps_str = f"${f['eps']:.2f}" if f["eps"] is not None else "N/A"
        pm_str = f"{f['profit_margin']:.2f}%" if f["profit_margin"] is not None else "N/A"
        roe_str = f"{f['roe']:.2f}%" if f["roe"] is not None else "N/A"
        dte_str = f"{f['debt_to_equity']:.2f}x" if f["debt_to_equity"] is not None else "N/A"
        div_str = f"{f['dividend_yield']:.2f}%" if f["dividend_yield"] is not None else "0.00%"
        beta_str = f"{f['beta']:.2f}" if f["beta"] is not None else "N/A"

        fund_rows.append(
            {
                "Stock": f["ticker"],
                "Market Cap": f["market_cap_formatted"],
                "P/E (TTM)": pe_str,
                "Forward P/E": fwd_pe_str,
                "Diluted EPS": eps_str,
                "Revenue (TTM)": f["revenue_formatted"],
                "Net Income": f["net_income_formatted"],
                "Profit Margin": pm_str,
                "ROE": roe_str,
                "Debt / Equity": dte_str,
                "Div Yield": div_str,
                "Beta": beta_str,
            }
        )

    df_fund = pd.DataFrame(fund_rows)
    st.dataframe(df_fund, use_container_width=True, height=220)

    # CSV Download for fundamentals
    st.download_button(
        "⬇️ Export Fundamental Comparison (CSV)",
        data=df_fund.to_csv(index=False).encode("utf-8"),
        file_name=f"stock_comparison_fundamentals_{'-'.join(valid_tickers)}.csv",
        mime="text/csv",
        key="dl_fund_csv",
    )

    # 6. Technical Indicators Comparison
    st.markdown("<div class='section-title'>Technical Indicators & Volatility Comparison</div>", unsafe_allow_html=True)
    with st.spinner("Computing technical momentum and volatility indicators..."):
        technicals = fetch_comparison_technicals(valid_tickers)

    tech_rows = []
    for t in technicals:
        if not t.get("has_data"):
            tech_rows.append({"Stock": t["ticker"], "Status": "Insufficient Data"})
            continue

        rsi_str = f"{t['rsi']:.1f}" if t.get("rsi") is not None else "N/A"
        macd_str = f"{t['macd']:.2f} ({t['macd_status']})" if t.get("macd") is not None else "N/A"
        sma50_str = f"${t['sma50']:.2f} ({t['vs_sma50']})" if t.get("sma50") is not None else "N/A"
        sma200_str = f"${t['sma200']:.2f} ({t['vs_sma200']})" if t.get("sma200") is not None else "N/A"
        bb_str = f"{t['bb_percent_b']:.2f}" if t.get("bb_percent_b") is not None else "N/A"
        vol_str = f"{t['annualized_volatility']:.2f}%" if t.get("annualized_volatility") is not None else "N/A"

        tech_rows.append(
            {
                "Stock": t["ticker"],
                "Price": f"${t['latest_price']:.2f}",
                "RSI (14)": rsi_str,
                "MACD": macd_str,
                "SMA 50": sma50_str,
                "SMA 200": sma200_str,
                "BB %B Position": bb_str,
                "Annualized Volatility": vol_str,
            }
        )

    df_tech = pd.DataFrame(tech_rows)
    st.dataframe(df_tech, use_container_width=True, height=220)

    # 7. Comparison Summary & Leaders
    st.markdown("<div class='section-title'>Cross-Sectional Benchmark Summary</div>", unsafe_allow_html=True)
    summary_leaders = generate_comparison_summary(perf_data, fundamentals, technicals)

    lead_cols = st.columns(5)
    with lead_cols[0]:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Top Return ({comp_timeframe})</div>
                <div class="metric-tile-value" style="font-size: 1.1rem; color: var(--color-positive);">{summary_leaders.get('best_performer', 'N/A')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with lead_cols[1]:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Lowest P/E Valuation</div>
                <div class="metric-tile-value" style="font-size: 1.1rem; color: var(--accent-primary);">{summary_leaders.get('lowest_pe', 'N/A')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with lead_cols[2]:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Largest Market Cap</div>
                <div class="metric-tile-value" style="font-size: 1.1rem; color: var(--accent-secondary);">{summary_leaders.get('highest_mcap', 'N/A')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with lead_cols[3]:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Highest ROE</div>
                <div class="metric-tile-value" style="font-size: 1.1rem; color: var(--color-positive);">{summary_leaders.get('highest_roe', 'N/A')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with lead_cols[4]:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Lowest Volatility</div>
                <div class="metric-tile-value" style="font-size: 1.1rem; color: var(--color-warning);">{summary_leaders.get('lowest_volatility', 'N/A')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="margin-top: 1rem; padding: 0.85rem 1.15rem; background-color: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; font-size: 0.78rem; color: var(--text-secondary); line-height: 1.45;">
            <b>Financial Analytics Disclaimer:</b> Benchmark metrics, rankings, and leader summaries presented above represent purely factual, objective mathematical calculations based on historical data. They do not constitute an endorsement, price target, investment advice, or recommendation to buy or sell securities.
        </div>
        """,
        unsafe_allow_html=True,
    )
