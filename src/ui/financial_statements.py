"""Financial Statements UI module.

Renders standardized Income Statement, Balance Sheet, and Cash Flow statements,
interactive financial ratio cards, and historical statement trend charts.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.services.financial_service import (
    BALANCE_SHEET_METRICS,
    CASH_FLOW_METRICS,
    INCOME_STATEMENT_METRICS,
    build_standardized_statement,
    calculate_financial_ratios,
    extract_metric_series,
    fetch_financial_statements,
    format_currency_value,
)
from src.ui.charts import get_chart_theme


def _create_bar_trend_chart(
    series_map: Dict[str, Dict[str, Any]],
    title: str,
    theme_name: str = "light",
) -> go.Figure:
    """Create a multi-series bar/line comparison chart matching the active theme."""
    ct = get_chart_theme(theme_name)
    fig = go.Figure()

    for name, s_info in series_map.items():
        labels = s_info.get("labels", [])
        values = s_info.get("values", [])
        color = s_info.get("color", ct["accent_primary"])
        chart_type = s_info.get("type", "bar")

        if not labels or not values:
            continue

        if chart_type == "line":
            fig.add_trace(
                go.Scatter(
                    x=labels,
                    y=values,
                    name=name,
                    mode="lines+markers",
                    line=dict(color=color, width=2.5),
                    marker=dict(size=6, color=color),
                )
            )
        else:
            fig.add_trace(
                go.Bar(
                    x=labels,
                    y=values,
                    name=name,
                    marker=dict(color=color),
                )
            )

    fig.update_layout(
        title=dict(
            text=title,
            x=0.0,
            y=0.96,
            xref="container",
            yref="container",
            xanchor="left",
            yanchor="top",
            font=dict(size=14, color=ct["font_color"], family=ct["font_family"]),
        ),
        height=360,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=15, r=15, t=85, b=25),
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
        xaxis=dict(
            gridcolor=ct["grid_color"],
            linecolor=ct["border_color"],
            tickfont=dict(color=ct["muted_color"]),
        ),
        yaxis=dict(
            gridcolor=ct["grid_color"],
            linecolor=ct["border_color"],
            tickfont=dict(color=ct["muted_color"]),
        ),
        barmode="group",
        hoverlabel=dict(
            bgcolor=ct["hover_bg"],
            bordercolor=ct["hover_border"],
            font=dict(color=ct["hover_font_color"], family=ct["font_family"]),
        ),
    )

    return fig


def render_financial_statements(ticker: str, theme_name: str = "light") -> None:
    """Render the comprehensive financial statements dashboard for the given ticker."""
    st.markdown(
        f"""
        <div class="company-banner">
            <div>
                <div class="company-name">📑 Financial Statements & Ratio Intelligence</div>
                <div class="company-meta">
                    <span>Target: <b>{ticker}</b></span>
                    <span>•</span>
                    <span>Standardized GAAP / IFRS Reporting</span>
                    <span>•</span>
                    <span>Historical Performance & Ratios</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner(f"Loading financial statements for {ticker}..."):
        raw_data = fetch_financial_statements(ticker)

    if not raw_data or "error" in raw_data:
        err_msg = raw_data.get("error", "No financial statements data available.") if raw_data else "No data returned."
        st.markdown(
            f"""
            <div class="fintech-card" style="text-align: center; padding: 2rem;">
                <h3 style="color: var(--color-warning); margin-bottom: 0.5rem;">⚠️ Financial Statements Unavailable</h3>
                <p style="color: var(--text-secondary); margin: 0;">
                    Financial statements for <b>{ticker}</b> could not be retrieved from Yahoo Finance ({err_msg}).
                    Please verify the ticker symbol or check back later.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Currency and statement options
    currency = raw_data.get("currency", "USD")
    curr_sym = "$" if currency == "USD" else f"{currency} "

    # Control Bar: Annual vs Quarterly toggle
    col_toggle, col_info = st.columns([3, 7])
    with col_toggle:
        period_choice = st.radio(
            "Reporting Frequency",
            ["Annual", "Quarterly"],
            horizontal=True,
            key=f"fin_period_toggle_{ticker}",
        )
    with col_info:
        st.markdown(
            f"<div style='padding-top: 1.8rem; font-size: 0.82rem; color: var(--text-secondary); text-align: right;'>"
            f"All values reported in <b>{currency}</b>. Standardized across fiscal reporting frameworks.</div>",
            unsafe_allow_html=True,
        )

    is_quarterly = (period_choice == "Quarterly")
    inc_raw = raw_data.get("income_quarterly") if is_quarterly else raw_data.get("income_annual")
    bal_raw = raw_data.get("balance_quarterly") if is_quarterly else raw_data.get("balance_annual")
    cf_raw = raw_data.get("cashflow_quarterly") if is_quarterly else raw_data.get("cashflow_annual")

    # -------------------------------------------------------------------------
    # 1. Key Financial Ratios Bar
    # -------------------------------------------------------------------------
    st.markdown("<div class='section-title'>Key Financial Health & Valuation Ratios</div>", unsafe_allow_html=True)
    ratios = calculate_financial_ratios(inc_raw, bal_raw, cf_raw)

    cards_html = []
    for r in ratios:
        if r["is_positive"] is True:
            badge_class = "badge-positive"
            status_icon = "🟢 Healthy"
        elif r["is_positive"] is False:
            badge_class = "badge-negative"
            status_icon = "🔴 Caution"
        else:
            badge_class = "badge-neutral"
            status_icon = "⚪ N/A"

        cards_html.append(
            f'<div class="kpi-card" title="{r["description"]}">'
            f'<div class="kpi-card-label">{r["name"]}</div>'
            f'<div class="kpi-card-value">{r["value"]}</div>'
            f'<div class="kpi-card-footer">'
            f'<span class="badge {badge_class}" style="font-size: 0.72rem;">{status_icon}</span>'
            f'</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="kpi-grid">{"".join(cards_html)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. Interactive Statement Trend Visualizations
    # -------------------------------------------------------------------------
    st.markdown("<div class='section-title'>Historical Financial Trajectory</div>", unsafe_allow_html=True)
    ct = get_chart_theme(theme_name)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Chart 1: Revenue vs Net Income
        rev_lbls, rev_vals = extract_metric_series(inc_raw, ["Total Revenue", "Operating Revenue"])
        net_lbls, net_vals = extract_metric_series(inc_raw, ["Net Income", "Net Income Common Stockholders"])
        gp_lbls, gp_vals = extract_metric_series(inc_raw, ["Gross Profit"])

        chart1_map = {
            "Total Revenue": {"labels": rev_lbls, "values": rev_vals, "color": ct["accent_secondary"], "type": "bar"},
            "Gross Profit": {"labels": gp_lbls, "values": gp_vals, "color": ct["accent_primary"], "type": "bar"},
            "Net Income": {"labels": net_lbls, "values": net_vals, "color": ct["up_color"], "type": "line"},
        }
        fig_inc = _create_bar_trend_chart(
            chart1_map,
            f"{ticker} Revenue, Gross Profit & Net Income ({period_choice})",
            theme_name=theme_name,
        )
        st.plotly_chart(
            fig_inc,
            use_container_width=True,
            key=f"financial_income_chart_{ticker}_{period_choice}",
        )

    with chart_col2:
        # Chart 2: Cash Flow Dynamics (Operating vs Free Cash Flow vs CapEx)
        ocf_lbls, ocf_vals = extract_metric_series(cf_raw, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
        fcf_lbls, fcf_vals = extract_metric_series(cf_raw, ["Free Cash Flow"])
        capex_lbls, capex_vals = extract_metric_series(cf_raw, ["Capital Expenditure"])

        chart2_map = {
            "Operating Cash Flow": {"labels": ocf_lbls, "values": ocf_vals, "color": ct["up_color"], "type": "bar"},
            "Free Cash Flow": {"labels": fcf_lbls, "values": fcf_vals, "color": ct["accent_primary"], "type": "line"},
            "Capital Expenditure": {"labels": capex_lbls, "values": capex_vals, "color": ct["down_color"], "type": "bar"},
        }
        fig_cf = _create_bar_trend_chart(
            chart2_map,
            f"{ticker} Operating Cash Flow, FCF & CapEx ({period_choice})",
            theme_name=theme_name,
        )
        st.plotly_chart(
            fig_cf,
            use_container_width=True,
            key=f"financial_cashflow_chart_{ticker}_{period_choice}",
        )

    # -------------------------------------------------------------------------
    # 3. Tabular Financial Statements
    # -------------------------------------------------------------------------
    st.markdown("<div class='section-title'>Detailed Statement Explorer</div>", unsafe_allow_html=True)

    subtab_inc, subtab_bal, subtab_cf = st.tabs(
        ["📊 Income Statement", "🏛️ Balance Sheet", "💸 Cash Flow Statement"]
    )

    def render_statement_table(
        df_raw: Optional[pd.DataFrame],
        metrics: List[Any],
        statement_name: str,
    ) -> None:
        if df_raw is None or df_raw.empty:
            st.info(f"No {statement_name} data available for {ticker}.")
            return

        std_df = build_standardized_statement(df_raw, metrics, is_quarterly=is_quarterly)
        if std_df.empty:
            st.info(f"No standardized metrics available for {statement_name}.")
            return

        # Format numerical cells into readable currency strings
        formatted_df = std_df.copy()
        for col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(
                lambda val: format_currency_value(val, currency_symbol=curr_sym)
            )

        st.dataframe(
            formatted_df,
            use_container_width=True,
            height=340,
        )

        # Download raw CSV export
        csv_bytes = std_df.to_csv().encode("utf-8")
        st.download_button(
            label=f"⬇️ Export {statement_name} (CSV)",
            data=csv_bytes,
            file_name=f"{ticker}_{statement_name.lower().replace(' ', '_')}_{period_choice.lower()}.csv",
            mime="text/csv",
            key=f"dl_{statement_name}_{is_quarterly}_{ticker}",
        )

    with subtab_inc:
        render_statement_table(inc_raw, INCOME_STATEMENT_METRICS, "Income Statement")

    with subtab_bal:
        render_statement_table(bal_raw, BALANCE_SHEET_METRICS, "Balance Sheet")

    with subtab_cf:
        render_statement_table(cf_raw, CASH_FLOW_METRICS, "Cash Flow Statement")
