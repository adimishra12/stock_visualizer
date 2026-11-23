"""Portfolio Tracker UI module.

Provides portfolio selection and creation, transaction logging with validation,
real-time holdings valuation, weighted-average cost basis accounting,
interactive Plotly visualizations, and historical transaction auditing.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.services.market_data import fetch_stock_history, get_stock_metrics, sanitize_ticker
from src.services.portfolio_service import (
    add_transaction,
    calculate_holdings_and_performance,
    create_portfolio,
    delete_portfolio,
    delete_transaction,
    get_transactions,
    list_portfolios,
)
from src.ui.charts import get_chart_theme


# -----------------------------------------------------------------------------
# Plotly Chart Builders for Portfolio Analytics
# -----------------------------------------------------------------------------

def _create_allocation_chart(holdings: List[Dict[str, Any]], theme_name: str = "light") -> go.Figure:
    """Create a sleek donut chart visualizing portfolio allocation by current value."""
    ct = get_chart_theme(theme_name)
    if not holdings:
        fig = go.Figure()
        fig.update_layout(
            title=dict(text="Portfolio Allocation", font=dict(color=ct["font_color"], size=14)),
            height=280,
            paper_bgcolor=ct["paper_bgcolor"],
            plot_bgcolor=ct["plot_bgcolor"],
        )
        return fig

    labels = [h["ticker"] for h in holdings]
    values = [
        h["current_value"] if h["current_value"] is not None else h["invested_value"]
        for h in holdings
    ]

    palette = [
        ct["accent_primary"],
        ct["accent_secondary"],
        ct["up_color"],
        "#F59E0B",
        "#EC4899",
        "#06B6D4",
        "#84CC16",
        "#6366F1",
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=palette[: len(labels)], line=dict(color=ct["border_color"], width=1)),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
                textfont=dict(family=ct["font_family"], size=12, color=ct["font_color"]),
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="Portfolio Allocation",
            font=dict(size=13, color=ct["font_color"], family=ct["font_family"]),
            x=0.5,
            xanchor="center",
            y=0.96,
            yanchor="top",
        ),
        height=340,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=15, r=15, t=45, b=55),
        font=dict(family=ct["font_family"], color=ct["font_color"]),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=ct["font_color"], size=11),
        ),
    )
    return fig


def _create_invested_vs_current_chart(
    holdings: List[Dict[str, Any]], theme_name: str = "light"
) -> go.Figure:
    """Create a grouped bar chart comparing invested cost basis vs current market value."""
    ct = get_chart_theme(theme_name)
    tickers = [h["ticker"] for h in holdings]
    invested = [h["invested_value"] for h in holdings]
    current = [
        h["current_value"] if h["current_value"] is not None else 0.0
        for h in holdings
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=tickers,
            y=invested,
            name="Invested Capital",
            marker=dict(color=ct["accent_primary"]),
        )
    )
    fig.add_trace(
        go.Bar(
            x=tickers,
            y=current,
            name="Current Market Value",
            marker=dict(color=ct["accent_secondary"]),
        )
    )

    fig.update_layout(
        title=dict(
            text="Invested Cost Basis vs Current Value",
            font=dict(size=13, color=ct["font_color"], family=ct["font_family"]),
            x=0.5,
            xanchor="center",
            y=0.96,
            yanchor="top",
        ),
        height=340,
        barmode="group",
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=15, r=15, t=45, b=55),
        font=dict(family=ct["font_family"], color=ct["font_color"]),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=ct["font_color"], size=11),
        ),
        xaxis=dict(gridcolor=ct["grid_color"], linecolor=ct["border_color"]),
        yaxis=dict(tickprefix="$", gridcolor=ct["grid_color"], linecolor=ct["border_color"]),
    )
    return fig


def _create_holding_pl_chart(holdings: List[Dict[str, Any]], theme_name: str = "light") -> go.Figure:
    """Create bar chart showing unrealized profit or loss per holding."""
    ct = get_chart_theme(theme_name)
    tickers = [h["ticker"] for h in holdings]
    pls = [
        h["unrealized_pl"] if h["unrealized_pl"] is not None else 0.0
        for h in holdings
    ]
    colors = [ct["up_color"] if val >= 0 else ct["down_color"] for val in pls]
    bar_texts = [f"${val:+,.2f}" if val != 0 else "$0.00" for val in pls]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=tickers,
            y=pls,
            name="Unrealized P/L ($)",
            marker=dict(color=colors),
            text=bar_texts,
            textposition="auto",
            textfont=dict(family=ct["font_family"], size=11),
        )
    )

    # Visible zero reference line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color=ct["border_color"],
        line_width=1.5,
    )

    fig.update_layout(
        title=dict(
            text="Unrealized Profit / Loss by Holding ($)",
            font=dict(size=13, color=ct["font_color"], family=ct["font_family"]),
            x=0.5,
            xanchor="center",
            y=0.96,
            yanchor="top",
        ),
        height=340,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=15, r=15, t=45, b=45),
        font=dict(family=ct["font_family"], color=ct["font_color"]),
        xaxis=dict(gridcolor=ct["grid_color"], linecolor=ct["border_color"]),
        yaxis=dict(tickprefix="$", gridcolor=ct["grid_color"], linecolor=ct["border_color"]),
    )
    return fig


# -----------------------------------------------------------------------------
# Main Portfolio UI Renderer
# -----------------------------------------------------------------------------

def render_portfolio_tracker(theme_name: str = "light") -> None:
    """Render the full portfolio tracker interface."""
    st.markdown(
        """
        <div class="company-banner">
            <div>
                <div class="company-name">💼 Portfolio Tracker & Ledger</div>
                <div class="company-meta">
                    <span>SQLite Persistent Ledger</span>
                    <span>•</span>
                    <span>Weighted-Average Cost Basis</span>
                    <span>•</span>
                    <span>Real-Time Valuation & P/L Analytics</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Portfolio Selection & Workspace Management
    portfolios = list_portfolios()
    if not portfolios:
        st.warning("No portfolios found. Creating default portfolio...")
        create_portfolio("Core Growth Portfolio", "Primary investment holdings")
        portfolios = list_portfolios()

    port_names = [p["name"] for p in portfolios]
    port_map = {p["name"]: p["id"] for p in portfolios}

    col_select, col_manage = st.columns([7, 3])
    with col_select:
        selected_port_name = st.selectbox(
            "Active Portfolio",
            port_names,
            index=0,
            key="portfolio_active_select",
        )
        active_port_id = port_map[selected_port_name]

    with col_manage:
        st.markdown("<div style='height: 1.72rem;'></div>", unsafe_allow_html=True)
        with st.popover("➕ Create or Manage Portfolios", use_container_width=True):
            st.markdown("<h4 style='margin: 0 0 0.5rem 0; font-size: 0.95rem; color: var(--text-primary); font-weight: 600;'>Create New Portfolio</h4>", unsafe_allow_html=True)
            with st.form("new_portfolio_form"):
                new_p_name = st.text_input("New Portfolio Name", placeholder="e.g. Dividend Growth, Speculative Tech")
                new_p_desc = st.text_input("Description (Optional)", placeholder="Long-term core positions")
                submit_new_p = st.form_submit_button("Create Portfolio", use_container_width=True)

                if submit_new_p:
                    try:
                        create_portfolio(new_p_name, new_p_desc)
                        st.success(f"Portfolio '{new_p_name}' created successfully!")
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))

            if len(portfolios) > 1:
                st.markdown("<hr style='margin: 0.75rem 0; border: none; border-top: 1px solid var(--border-color);'>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.35rem;'>Delete active portfolio:</p>", unsafe_allow_html=True)
                if st.button(f"🗑️ Delete '{selected_port_name}'", key="btn_del_active_portfolio", use_container_width=True):
                    delete_portfolio(active_port_id)
                    st.success(f"Portfolio '{selected_port_name}' deleted.")
                    st.rerun()

    # 2. Transaction Entry Form
    with st.expander("📝 Record Buy / Sell Transaction", expanded=False):
        c_tx1, c_tx2, c_tx3, c_tx4 = st.columns([3, 2, 2, 2])
        with c_tx1:
            tx_ticker = st.text_input("Stock Symbol", placeholder="e.g. AAPL, NVDA, MSFT", key="tx_in_ticker").strip().upper()
        with c_tx2:
            tx_type = st.radio("Type", ["BUY", "SELL"], horizontal=True, key="tx_in_type")
        with c_tx3:
            tx_qty = st.number_input("Shares", min_value=0.0001, max_value=10000000.0, value=10.0, step=1.0, key="tx_in_qty")
        with c_tx4:
            tx_price = st.number_input("Price / Share ($)", min_value=0.01, max_value=1000000.0, value=150.0, step=1.0, key="tx_in_price")

        c_tx5, c_tx6, c_tx7 = st.columns([3, 3, 4])
        with c_tx5:
            tx_fee = st.number_input("Fees / Commission ($)", min_value=0.0, max_value=1000.0, value=0.0, step=0.5, key="tx_in_fee")
        with c_tx6:
            tx_date = st.date_input("Transaction Date", value=datetime.now(), key="tx_in_date")
        with c_tx7:
            tx_notes = st.text_input("Notes (Optional)", placeholder="e.g. Dollar cost averaging", key="tx_in_notes")

        # Quick price lookup helper
        if tx_ticker and st.button(f"⚡ Fetch Latest Quote for {tx_ticker}", key="fetch_quote_tx_btn"):
            res = fetch_stock_history(tx_ticker, period="5d", interval="1d")
            q_df = res[0] if isinstance(res, tuple) else res
            if q_df is not None and not q_df.empty and "Close" in q_df.columns:
                latest_price = float(q_df["Close"].dropna().iloc[-1])
                st.info(f"Latest market quote for {tx_ticker}: **${latest_price:.2f}**")
            else:
                st.warning(f"Could not fetch current market quote for {tx_ticker}.")

        if st.button("💾 Save Transaction to Ledger", key="btn_save_tx", use_container_width=True):
            try:
                date_str = tx_date.strftime("%Y-%m-%d")
                add_transaction(
                    portfolio_id=active_port_id,
                    ticker=tx_ticker,
                    transaction_type=tx_type,
                    quantity=tx_qty,
                    price_per_share=tx_price,
                    fees=tx_fee,
                    transaction_date=date_str,
                    notes=tx_notes,
                )
                st.success(f"Recorded {tx_type} {tx_qty} {tx_ticker} @ ${tx_price:.2f}")
                st.rerun()
            except ValueError as ex:
                st.error(f"Transaction failed: {str(ex)}")

    # 3. Calculate Portfolio Analytics & Performance
    with st.spinner("Valuating portfolio holdings with live market quotes..."):
        perf = calculate_holdings_and_performance(active_port_id)

    holdings = perf["holdings"]
    total_inv = perf["total_invested_capital"]
    curr_val = perf["current_portfolio_value"]
    unreal_pl = perf["unrealized_pl"]
    real_pl = perf["realized_pl"]
    tot_ret = perf["total_return_pct"]
    quote_time = perf["latest_quote_time"]

    # 4. KPI Performance Summary Tiles
    st.markdown("<div class='section-title'>Portfolio Performance Overview</div>", unsafe_allow_html=True)
    k_col1, k_col2, k_col3, k_col4, k_col5, k_col6 = st.columns(6)

    with k_col1:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Invested Capital</div>
                <div class="metric-tile-value" style="font-size: 1.35rem;">${total_inv:,.2f}</div>
                <div class="metric-tile-subtext">Remaining Cost Basis</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k_col2:
        val_str = f"${curr_val:,.2f}" if curr_val is not None else "N/A"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Current Value</div>
                <div class="metric-tile-value" style="font-size: 1.35rem;">{val_str}</div>
                <div class="metric-tile-subtext">{quote_time[11:16]} Live Quote</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k_col3:
        if unreal_pl is not None:
            sign = "+" if unreal_pl >= 0 else ""
            color_var = "var(--color-positive)" if unreal_pl >= 0 else "var(--color-negative)"
            upl_str = f"{sign}${unreal_pl:,.2f}"
        else:
            upl_str = "N/A"
            color_var = "var(--text-secondary)"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Unrealized P/L</div>
                <div class="metric-tile-value" style="font-size: 1.35rem; color: {color_var};">{upl_str}</div>
                <div class="metric-tile-subtext">Active Positions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k_col4:
        sign_r = "+" if real_pl >= 0 else ""
        color_r = "var(--color-positive)" if real_pl >= 0 else "var(--color-negative)"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Realized P/L</div>
                <div class="metric-tile-value" style="font-size: 1.35rem; color: {color_r};">{sign_r}${real_pl:,.2f}</div>
                <div class="metric-tile-subtext">Historical Sales</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k_col5:
        if tot_ret is not None:
            sign_t = "+" if tot_ret >= 0 else ""
            color_t = "var(--color-positive)" if tot_ret >= 0 else "var(--color-negative)"
            ret_str = f"{sign_t}{tot_ret:.2f}%"
        else:
            ret_str = "N/A"
            color_t = "var(--text-secondary)"
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Total Return</div>
                <div class="metric-tile-value" style="font-size: 1.35rem; color: {color_t};">{ret_str}</div>
                <div class="metric-tile-subtext">Unrealized + Realized</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k_col6:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="metric-tile-label">Holdings</div>
                <div class="metric-tile-value" style="font-size: 1.35rem;">{perf['holdings_count']}</div>
                <div class="metric-tile-subtext">Active Positions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # 5. Visualizations Section
    if holdings:
        st.markdown("<div class='section-title'>Portfolio Visualizations</div>", unsafe_allow_html=True)
        v_col1, v_col2, v_col3 = st.columns(3)
        with v_col1:
            st.plotly_chart(
                _create_allocation_chart(holdings, theme_name=theme_name),
                use_container_width=True,
                key=f"portfolio_allocation_chart_{active_port_id}",
            )
        with v_col2:
            st.plotly_chart(
                _create_invested_vs_current_chart(holdings, theme_name=theme_name),
                use_container_width=True,
                key=f"portfolio_invested_vs_current_chart_{active_port_id}",
            )
        with v_col3:
            st.plotly_chart(
                _create_holding_pl_chart(holdings, theme_name=theme_name),
                use_container_width=True,
                key=f"portfolio_holding_pl_chart_{active_port_id}",
            )

    # 6. Current Holdings Section
    st.markdown("<div class='section-title'>Current Holdings</div>", unsafe_allow_html=True)
    if not holdings:
        st.markdown(
            f"""
            <div class="fintech-card" style="text-align: center; padding: 2.5rem 1.5rem; margin-bottom: 1.5rem;">
                <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">💼</div>
                <h4 style="color: var(--text-primary); margin-bottom: 0.35rem; font-size: 1.1rem;">No Active Stock Positions</h4>
                <p style="color: var(--text-secondary); max-width: 520px; margin: 0 auto; font-size: 0.85rem;">
                    You have not added any holdings to <b>{selected_port_name}</b> yet.
                    Use the <b>Record Buy / Sell Transaction</b> panel above to record your first execution.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Dedicated Action Toolbar Row
        c_sort, c_space, c_export = st.columns([5, 4, 3])
        with c_sort:
            sort_by = st.selectbox(
                "Sort Holdings By",
                [
                    "Current Value (High to Low)",
                    "Unrealized P/L (High to Low)",
                    "Return % (High to Low)",
                    "Stock Name (A-Z)",
                ],
                index=0,
                key=f"sort_holdings_key_{active_port_id}",
            )
        with c_export:
            st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
            export_rows = [
                {
                    "Stock": h["ticker"],
                    "Quantity": f"{h['quantity']:,.4f}".rstrip("0").rstrip("."),
                    "Average Cost ($)": f"{h['average_cost']:.2f}",
                    "Current Price ($)": f"{h['current_price']:.2f}" if h["current_price"] is not None else "N/A",
                    "Invested Value ($)": f"{h['invested_value']:.2f}",
                    "Current Value ($)": f"{h['current_value']:.2f}" if h["current_value"] is not None else "N/A",
                    "Unrealized P/L ($)": f"{h['unrealized_pl']:.2f}" if h["unrealized_pl"] is not None else "N/A",
                    "Return (%)": f"{h['return_pct']:.2f}" if h["return_pct"] is not None else "N/A",
                }
                for h in holdings
            ]
            csv_data = pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Export Holdings (CSV)",
                data=csv_data,
                file_name=f"{selected_port_name.lower().replace(' ', '_')}_holdings.csv",
                mime="text/csv",
                key=f"dl_holdings_csv_{active_port_id}",
                use_container_width=True,
            )

        # Apply sort
        if sort_by == "Current Value (High to Low)":
            holdings.sort(key=lambda x: (x["current_value"] or 0.0), reverse=True)
        elif sort_by == "Unrealized P/L (High to Low)":
            holdings.sort(key=lambda x: (x["unrealized_pl"] or -1e9), reverse=True)
        elif sort_by == "Return % (High to Low)":
            holdings.sort(key=lambda x: (x["return_pct"] or -1e9), reverse=True)
        elif sort_by == "Stock Name (A-Z)":
            holdings.sort(key=lambda x: x["ticker"])

        # Render Professional Responsive HTML Table with Green/Red P/L Highlights
        table_rows_html = []
        for h in holdings:
            p_val = f"${h['current_value']:,.2f}" if h["current_value"] is not None else "N/A"
            c_price = f"${h['current_price']:,.2f}" if h["current_price"] is not None else "N/A"
            upl = h.get("unrealized_pl")
            ret_pct = h.get("return_pct")
            qty_str = f"{h['quantity']:,.4f}".rstrip("0").rstrip(".")

            if upl is not None:
                is_pos = upl >= 0
                badge_cls = "badge-positive" if is_pos else "badge-negative"
                sign_str = "+" if is_pos else ""
                upl_badge = f'<span class="badge {badge_cls}">{sign_str}${upl:,.2f}</span>'
                ret_badge = f'<span class="badge {badge_cls}">{sign_str}{ret_pct:.2f}%</span>'
            else:
                upl_badge = '<span class="badge badge-neutral">N/A</span>'
                ret_badge = '<span class="badge badge-neutral">N/A</span>'

            table_rows_html.append(
                f'<tr>'
                f'<td><b>{h["ticker"]}</b></td>'
                f'<td style="text-align: right; font-family: \'JetBrains Mono\', monospace;">{qty_str}</td>'
                f'<td style="text-align: right; font-family: \'JetBrains Mono\', monospace;">${h["average_cost"]:,.2f}</td>'
                f'<td style="text-align: right; font-family: \'JetBrains Mono\', monospace;">{c_price}</td>'
                f'<td style="text-align: right; font-family: \'JetBrains Mono\', monospace;">${h["invested_value"]:,.2f}</td>'
                f'<td style="text-align: right; font-family: \'JetBrains Mono\', monospace;"><b>{p_val}</b></td>'
                f'<td style="text-align: right;">{upl_badge}</td>'
                f'<td style="text-align: right;">{ret_badge}</td>'
                f'</tr>'
            )

        holdings_html = (
            '<div class="holdings-table-container">'
            '<table class="fintech-table">'
            '<thead>'
            '<tr>'
            '<th>Stock</th>'
            '<th style="text-align: right;">Shares</th>'
            '<th style="text-align: right;">Avg Cost</th>'
            '<th style="text-align: right;">Current Price</th>'
            '<th style="text-align: right;">Invested Capital</th>'
            '<th style="text-align: right;">Current Value</th>'
            '<th style="text-align: right;">Unrealized P/L</th>'
            '<th style="text-align: right;">Return %</th>'
            '</tr>'
            '</thead>'
            '<tbody>'
            f'{"".join(table_rows_html)}'
            '</tbody>'
            '</table>'
            '</div>'
        )
        st.markdown(holdings_html, unsafe_allow_html=True)

    # 7. Transaction Ledger & Audit Trail
    st.markdown("<div class='section-title'>Transaction Ledger & History</div>", unsafe_allow_html=True)
    transactions = get_transactions(active_port_id)

    if not transactions:
        st.info("No transaction history recorded for this portfolio.")
    else:
        tx_rows = []
        for tx in transactions:
            total_amt = (tx["quantity"] * tx["price_per_share"]) + tx["fees"]
            tx_rows.append(
                {
                    "ID": tx["id"],
                    "Date": tx["transaction_date"],
                    "Stock": tx["ticker"],
                    "Type": tx["transaction_type"],
                    "Shares": f"{tx['quantity']:,.4f}".rstrip("0").rstrip("."),
                    "Price / Share": f"${tx['price_per_share']:,.2f}",
                    "Fees": f"${tx['fees']:,.2f}",
                    "Total Amount": f"${total_amt:,.2f}",
                    "Notes": tx["notes"] or "-",
                }
            )

        df_tx = pd.DataFrame(tx_rows)
        st.dataframe(df_tx, use_container_width=True, height=240)

        col_tx_dl, col_tx_del = st.columns([8, 4])
        with col_tx_dl:
            csv_tx_data = df_tx.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Export Transactions (CSV)",
                data=csv_tx_data,
                file_name=f"{selected_port_name.lower().replace(' ', '_')}_transactions.csv",
                mime="text/csv",
                key="dl_tx_csv",
            )

        with col_tx_del:
            del_id = st.number_input("Delete Transaction ID", min_value=1, step=1, key="del_tx_id_input")
            if st.button("🗑️ Delete Selected Transaction", key="btn_del_tx"):
                if delete_transaction(int(del_id)):
                    st.success(f"Transaction #{del_id} deleted.")
                    st.rerun()
                else:
                    st.error(f"Transaction #{del_id} not found.")
