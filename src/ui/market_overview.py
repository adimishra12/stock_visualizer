"""Market Overview dashboard view.

Presents live snapshot cards with sparkline trends for major global benchmarks,
US indices, commodities, yields, and cryptocurrencies.
"""

from datetime import datetime
from typing import List
import streamlit as st

from src.services.market_data import get_market_overview_data
from src.ui.charts import create_sparkline_chart


def format_overview_price(symbol: str, price: float) -> str:
    """Format prices intelligently depending on asset class."""
    if symbol == "^TNX":
        return f"{price:.3f}%"
    elif price >= 1000:
        return f"${price:,.2f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:,.4f}"


def render_market_overview(theme_name: str = "light"):
    """Render the full Market Overview section."""
    st.markdown(
        """
        <div style="margin-bottom: 1.25rem;">
            <div style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.2rem;">
                Global Market Overview
            </div>
            <div style="font-size: 0.85rem; color: var(--text-secondary);">
                Snapshot of major equity indices, benchmark interest rates, commodities, and digital assets.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Loading global market telemetry..."):
        overview_data = get_market_overview_data()

    if not overview_data:
        st.warning("Market overview data is temporarily unavailable. Please retry shortly.")
        return

    # Categorize items
    categories = {
        "Major Equity Indices": [d for d in overview_data if d["type"] == "Index"],
        "Commodities & Benchmark Rates": [
            d for d in overview_data if d["type"] in ("Commodity", "Rate")
        ],
        "Digital Currencies": [d for d in overview_data if d["type"] == "Crypto"],
    }

    for cat_title, items in categories.items():
        if not items:
            continue

        st.markdown(
            f"""
            <div style="font-size: 0.95rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin: 1.2rem 0 0.6rem 0; padding-bottom: 0.3rem; border-bottom: 1px solid var(--border-color);">
                {cat_title}
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns(len(items))
        for idx, item in enumerate(items):
            with cols[idx]:
                sym = item["symbol"]
                name = item["name"]
                price = item["current_price"]
                change = item["change"]
                change_pct = item["change_pct"]
                sparkline = item.get("sparkline", [])

                is_pos = change >= 0
                badge_class = "badge-positive" if is_pos else "badge-negative"
                change_arrow = "▲" if is_pos else "▼"

                st.markdown(
                    f"""
                    <div class="metric-tile" style="margin-bottom: 0.5rem; padding: 0.9rem;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.25rem;">
                            <span style="font-weight: 600; font-size: 0.85rem; color: var(--text-primary);">{name}</span>
                            <span class="badge badge-neutral" style="font-size: 0.7rem; font-weight: 600;">{sym}</span>
                        </div>
                        <div style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); font-family: 'JetBrains Mono', monospace;">
                            {format_overview_price(sym, price)}
                        </div>
                        <div style="margin-top: 0.35rem; display: flex; align-items: center; gap: 0.4rem;">
                            <span class="badge {badge_class}" style="font-size: 0.75rem;">
                                {change_arrow} {abs(change):,.2f} ({change_pct:+.2f}%)
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Render sparkline trendline
                if sparkline and len(sparkline) >= 2:
                    spark_fig = create_sparkline_chart(
                        series=sparkline, is_positive=is_pos, theme_name=theme_name
                    )
                    st.plotly_chart(
                        spark_fig,
                        use_container_width=True,
                        config={"displayModeBar": False},
                        key=f"market_overview_sparkline_{sym}",
                    )

                # Inspect button to jump directly to this ticker in Stock Analysis
                if st.button(f"Analyze {sym}", key=f"ov_inspect_{sym}", use_container_width=True):
                    st.session_state.pending_ticker = sym
                    st.session_state.target_tab = 1  # Index of Stock Analysis tab
                    st.rerun()

    # Telemetry timestamp & disclaimer footer
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(
        f"""
        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 1.5rem; text-align: right;">
            Telemetry timestamp: {now_str} • Market data delayed up to 15 minutes by provider.
        </div>
        """,
        unsafe_allow_html=True,
    )
