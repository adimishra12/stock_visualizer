"""Company News and Sentiment Analysis UI module.

Renders real-time news articles, multi-window timeframe filters,
NLP sentiment score breakdown, and an interactive sentiment distribution donut chart.
"""

from typing import Any, Dict, List
import plotly.graph_objects as go
import streamlit as st

from src.services.news_service import (
    calculate_sentiment_summary,
    fetch_company_news,
    filter_news_by_time,
)
from src.ui.charts import get_chart_theme


def _create_sentiment_donut_chart(
    summary: Dict[str, Any], theme_name: str = "light"
) -> go.Figure:
    """Create a sleek donut chart visualizing positive, neutral, and negative sentiment."""
    ct = get_chart_theme(theme_name)

    labels = ["Bullish / Positive", "Neutral", "Bearish / Negative"]
    values = [
        summary.get("positive_count", 0),
        summary.get("neutral_count", 0),
        summary.get("negative_count", 0),
    ]

    colors = [ct["up_color"], ct["muted_color"], ct["down_color"]]

    # Guard against all-zero values
    if sum(values) == 0:
        labels = ["No Data"]
        values = [1]
        colors = [ct["muted_color"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color=ct["border_color"], width=1.5)),
                textinfo="percent",
                hoverinfo="label+value+percent",
                textposition="inside",
                insidetextorientation="horizontal",
                textfont=dict(family=ct["font_family"], size=12, color="#FFFFFF"),
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="Sentiment Breakdown",
            font=dict(size=14, color=ct["font_color"], family=ct["font_family"]),
            x=0.5,
            xanchor="center",
            y=0.96,
            yanchor="top",
        ),
        height=320,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=15, r=15, t=45, b=55),
        font=dict(family=ct["font_family"], color=ct["font_color"]),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.06,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=ct["font_color"], size=11, family=ct["font_family"]),
            itemclick=False,
            itemdoubleclick=False,
        ),
    )

    return fig


def render_company_news(ticker: str, theme_name: str = "light") -> None:
    """Render real-time news headlines and sentiment analytics for a given ticker."""
    st.markdown(
        f"""
        <div class="company-banner">
            <div>
                <div class="company-name">📰 Real-Time Company News & Sentiment</div>
                <div class="company-meta">
                    <span>Target: <b>{ticker}</b></span>
                    <span>•</span>
                    <span>Financial Headlines & Editorial Coverage</span>
                    <span>•</span>
                    <span>VADER NLP Sentiment Scoring</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Timeframe and filter controls
    col_filter, col_refresh = st.columns([4, 6])
    with col_filter:
        timeframe_filter = st.selectbox(
            "Publication Timeframe",
            ["Latest News", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
            index=0,
            key=f"news_filter_{ticker}",
        )

    with col_refresh:
        st.markdown(
            "<div style='padding-top: 1.8rem; font-size: 0.82rem; color: var(--text-secondary); text-align: right;'>"
            "Headlines scored with compound polarity thresholds (-1.0 to +1.0).</div>",
            unsafe_allow_html=True,
        )

    with st.spinner(f"Retrieving latest news for {ticker}..."):
        raw_news = fetch_company_news(ticker)

    if not raw_news:
        st.markdown(
            f"""
            <div class="fintech-card" style="text-align: center; padding: 2.5rem;">
                <h3 style="color: var(--text-secondary); margin-bottom: 0.5rem;">🗞️ No News Articles Found</h3>
                <p style="color: var(--text-secondary); margin: 0;">
                    There are currently no recent news articles indexed for <b>{ticker}</b> via the Yahoo Finance API.
                    Please check back later or search another symbol.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Filter articles by selected window
    filtered_news = filter_news_by_time(raw_news, timeframe_filter)
    summary = calculate_sentiment_summary(filtered_news)

    # -------------------------------------------------------------------------
    # 1. Sentiment Analytics Dashboard
    # -------------------------------------------------------------------------
    st.markdown("<div class='section-title'>Market Sentiment Overview</div>", unsafe_allow_html=True)

    col_stats, col_donut = st.columns([6, 4])

    with col_stats:
        # Determine stance badge
        overall_stance = summary.get("overall_label", "Neutral")
        if "Bullish" in overall_stance:
            stance_class = "badge-positive"
        elif "Bearish" in overall_stance:
            stance_class = "badge-negative"
        else:
            stance_class = "badge-warning"

        avg_comp = summary.get("average_compound", 0.0)
        sign_str = "+" if avg_comp > 0 else ""

        # Stance Card
        st.markdown(
            f"""
            <div class="fintech-card" style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary); font-weight: 600; text-transform: uppercase;">
                            Aggregate Market Stance
                        </div>
                        <div style="font-size: 1.35rem; font-weight: 700; color: var(--text-primary); margin-top: 0.25rem;">
                            {overall_stance}
                        </div>
                    </div>
                    <div>
                        <span class="badge {stance_class}" style="font-size: 0.9rem; padding: 0.35rem 0.8rem;">
                            Score: {sign_str}{avg_comp:.2f}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Metrics 4-tile grid
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">Articles</div>
                    <div class="metric-tile-value">{summary['total_articles']}</div>
                    <div class="metric-tile-subtext">Analyzed</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col2:
            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">Bullish</div>
                    <div class="metric-tile-value" style="color: var(--color-positive);">{summary['positive_pct']}%</div>
                    <div class="metric-tile-subtext">{summary['positive_count']} items</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col3:
            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">Neutral</div>
                    <div class="metric-tile-value" style="color: var(--text-secondary);">{summary['neutral_pct']}%</div>
                    <div class="metric-tile-subtext">{summary['neutral_count']} items</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col4:
            st.markdown(
                f"""
                <div class="metric-tile">
                    <div class="metric-tile-label">Bearish</div>
                    <div class="metric-tile-value" style="color: var(--color-negative);">{summary['negative_pct']}%</div>
                    <div class="metric-tile-subtext">{summary['negative_count']} items</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_donut:
        fig_donut = _create_sentiment_donut_chart(summary, theme_name=theme_name)
        st.plotly_chart(
            fig_donut,
            use_container_width=True,
            key=f"news_sentiment_chart_{ticker}_{timeframe_filter}",
        )

    # -------------------------------------------------------------------------
    # 2. News Article Feed
    # -------------------------------------------------------------------------
    st.markdown(
        f"<div class='section-title'>Latest Headlines & Intelligence ({len(filtered_news)} Articles)</div>",
        unsafe_allow_html=True,
    )

    for item in filtered_news:
        sent = item.get("sentiment", {})
        label = sent.get("label", "Neutral")
        compound = sent.get("compound", 0.0)
        c_sign = "+" if compound > 0 else ""

        if label == "Positive":
            badge_cls = "badge-positive"
            badge_icon = "🟢 Bullish"
        elif label == "Negative":
            badge_cls = "badge-negative"
            badge_icon = "🔴 Bearish"
        else:
            badge_cls = "badge-neutral"
            badge_icon = "⚪ Neutral"

        publisher = item.get("publisher", "Financial News")
        pub_time = item.get("published_at", "Recent")
        title = item.get("title", "Untitled Article")
        summary_text = item.get("summary", "")
        article_url = item.get("url", "#")

        # Fallback if summary is empty
        display_summary = summary_text if summary_text else "No article excerpt available. Click below to read the complete article coverage."

        st.markdown(
            f"""
            <div class="fintech-card" style="padding: 1.15rem 1.25rem; margin-bottom: 0.85rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.45rem;">
                    <div style="font-size: 0.8rem; color: var(--text-secondary); font-weight: 500;">
                        <span style="font-weight: 600; color: var(--accent-primary);">{publisher}</span>
                        <span style="margin: 0 0.4rem;">•</span>
                        <span>{pub_time}</span>
                    </div>
                    <div>
                        <span class="badge {badge_cls}" style="font-size: 0.72rem;">
                            {badge_icon} ({c_sign}{compound:.2f})
                        </span>
                    </div>
                </div>
                <div style="font-size: 1.05rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.4rem; line-height: 1.35;">
                    <a href="{article_url}" target="_blank" style="text-decoration: none; color: inherit;">
                        {title}
                    </a>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.45; margin-bottom: 0.6rem;">
                    {display_summary}
                </div>
                <div style="text-align: right;">
                    <a href="{article_url}" target="_blank" style="text-decoration: none; font-size: 0.8rem; font-weight: 600; color: var(--accent-secondary);">
                        Read Full Article ↗
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
