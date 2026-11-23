"""Plotly financial charts with centralized theme resolution.

Adapts candlestick and line charts, volume panes, RSI, MACD, ATR,
and sparklines to active Light mode (default) and Dark mode palettes.
"""

from typing import Any, Dict, List
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.config import get_theme


def get_chart_theme(theme_name: str) -> Dict[str, Any]:
    """Resolve chart styling tokens based on active theme."""
    theme = get_theme(theme_name)
    is_dark = theme["name"] == "dark"

    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font_family": "Inter, -apple-system, sans-serif",
        "font_color": theme["text_primary"],
        "muted_color": theme["text_secondary"],
        "grid_color": theme["chart_grid"],
        "border_color": theme["border"],
        "up_color": theme["positive"],
        "down_color": theme["negative"],
        "accent_primary": theme["accent_primary"],
        "accent_secondary": theme["accent_secondary"],
        "ma20_color": "#F59E0B" if not is_dark else "#FBBF24",
        "ma50_color": theme["accent_secondary"],
        "ma200_color": theme["accent_primary"],
        "bb_color": "rgba(100, 116, 139, 0.45)",
        "bb_fill": "rgba(100, 116, 139, 0.08)",
        "hover_bg": theme["bg_card"],
        "hover_border": theme["border"],
        "hover_font_color": theme["text_primary"],
        "template": theme["plotly_template"],
    }


def create_price_chart(
    df: pd.DataFrame,
    ticker: str,
    chart_type: str = "candlestick",
    show_ma20: bool = True,
    show_ma50: bool = True,
    show_ma200: bool = False,
    show_ema9: bool = False,
    show_ema21: bool = False,
    show_bb: bool = False,
    show_vwap: bool = False,
    theme_name: str = "light",
) -> go.Figure:
    """Create interactive Candlestick or Line price chart with Volume subplot and theme-aware styling."""
    ct = get_chart_theme(theme_name)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.70, 0.30],
        subplot_titles=(f"{ticker} Price Action", "Trading Volume"),
    )

    # Price Trace: Candlestick or Line
    if chart_type.lower() == "line":
        fill_color = (
            "rgba(109, 40, 217, 0.06)"
            if ct["template"] == "plotly_white"
            else "rgba(139, 92, 246, 0.1)"
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                name="Close Price",
                mode="lines",
                line=dict(color=ct["accent_primary"], width=2),
                fill="tozeroy",
                fillcolor=fill_color,
            ),
            row=1,
            col=1,
        )
    else:
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Price",
                increasing=dict(
                    line=dict(color=ct["up_color"], width=1),
                    fillcolor=ct["up_color"],
                ),
                decreasing=dict(
                    line=dict(color=ct["down_color"], width=1),
                    fillcolor=ct["down_color"],
                ),
            ),
            row=1,
            col=1,
        )

    # Simple Moving Averages
    if show_ma20 and "MA20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MA20"],
                name="SMA 20",
                line=dict(color=ct["ma20_color"], width=1.5),
            ),
            row=1,
            col=1,
        )

    if show_ma50 and "MA50" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MA50"],
                name="SMA 50",
                line=dict(color=ct["ma50_color"], width=1.5),
            ),
            row=1,
            col=1,
        )

    if show_ma200 and "MA200" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MA200"],
                name="SMA 200",
                line=dict(color=ct["ma200_color"], width=1.5),
            ),
            row=1,
            col=1,
        )

    # Exponential Moving Averages
    if show_ema9 and "EMA9" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["EMA9"],
                name="EMA 9",
                line=dict(color="#06B6D4", width=1.5),
            ),
            row=1,
            col=1,
        )

    if show_ema21 and "EMA21" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["EMA21"],
                name="EMA 21",
                line=dict(color="#EC4899", width=1.5),
            ),
            row=1,
            col=1,
        )

    # VWAP
    if show_vwap and "VWAP" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["VWAP"],
                name="VWAP",
                line=dict(color="#8B5CF6", width=1.5, dash="dot"),
            ),
            row=1,
            col=1,
        )

    # Bollinger Bands
    if show_bb and "BB_Upper" in df.columns and "BB_Lower" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_Upper"],
                name="BB Upper",
                line=dict(color=ct["bb_color"], width=1, dash="dash"),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_Lower"],
                name="BB Lower",
                line=dict(color=ct["bb_color"], width=1, dash="dash"),
                fill="tonexty",
                fillcolor=ct["bb_fill"],
            ),
            row=1,
            col=1,
        )

    # Volume Bar
    vol_colors = [
        ct["up_color"] if df["Close"].iloc[i] >= df["Open"].iloc[i] else ct["down_color"]
        for i in range(len(df))
    ]

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=vol_colors,
            opacity=0.75,
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        height=580,
        showlegend=True,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        font=dict(family=ct["font_family"], color=ct["font_color"], size=12),
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1,
            font=dict(color=ct["muted_color"], size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis_rangeslider_visible=False,
        hoverlabel=dict(
            bgcolor=ct["hover_bg"],
            bordercolor=ct["hover_border"],
            font=dict(color=ct["hover_font_color"], family=ct["font_family"]),
        ),
    )

    # Position subplot titles cleanly into dedicated non-overlapping areas
    for ann in fig["layout"]["annotations"]:
        if ann["text"] == "Trading Volume":
            ann["font"] = dict(size=12, color=ct["font_color"], family=ct["font_family"])
            ann["xanchor"] = "left"
            ann["x"] = 0.0
            ann["y"] = ann["y"] + 0.015
        elif f"{ticker} Price Action" in ann["text"]:
            ann["font"] = dict(size=13, color=ct["font_color"], family=ct["font_family"])
            ann["xanchor"] = "left"
            ann["x"] = 0.0

    # Crosshairs & Grid
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=ct["grid_color"],
        linecolor=ct["border_color"],
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=ct["muted_color"],
        spikethickness=1,
        spikedash="dot",
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor=ct["grid_color"],
        linecolor=ct["border_color"],
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=ct["muted_color"],
        spikethickness=1,
        spikedash="dot",
    )

    return fig


def create_rsi_chart(df: pd.DataFrame, theme_name: str = "light") -> go.Figure:
    """Create interactive RSI chart matching the active theme."""
    ct = get_chart_theme(theme_name)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["RSI"],
            name="RSI (14)",
            line=dict(color=ct["accent_primary"], width=2),
        )
    )

    fig.add_hline(
        y=70,
        line_dash="dash",
        line_color=ct["down_color"],
        line_width=1,
        annotation_text="Overbought (70)",
        annotation_font_color=ct["down_color"],
        annotation_position="top right",
    )
    fig.add_hline(
        y=30,
        line_dash="dash",
        line_color=ct["up_color"],
        line_width=1,
        annotation_text="Oversold (30)",
        annotation_font_color=ct["up_color"],
        annotation_position="bottom right",
    )
    fig.add_hline(
        y=50,
        line_dash="dot",
        line_color=ct["border_color"],
        line_width=1,
    )

    fig.update_layout(
        title=dict(
            text="Relative Strength Index (RSI 14)",
            font=dict(size=14, color=ct["font_color"], family=ct["font_family"]),
        ),
        height=280,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=10, r=10, t=55, b=10),
        font=dict(family=ct["font_family"], color=ct["font_color"]),
        yaxis=dict(
            range=[0, 100],
            gridcolor=ct["grid_color"],
            linecolor=ct["border_color"],
            tickfont=dict(color=ct["muted_color"]),
        ),
        xaxis=dict(
            gridcolor=ct["grid_color"],
            linecolor=ct["border_color"],
            tickfont=dict(color=ct["muted_color"]),
        ),
        hoverlabel=dict(
            bgcolor=ct["hover_bg"],
            bordercolor=ct["hover_border"],
            font=dict(color=ct["hover_font_color"], family=ct["font_family"]),
        ),
    )

    return fig


def create_macd_chart(df: pd.DataFrame, theme_name: str = "light") -> go.Figure:
    """Create interactive MACD chart matching the active theme."""
    ct = get_chart_theme(theme_name)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MACD"],
            name="MACD",
            line=dict(color=ct["accent_secondary"], width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Signal_Line"],
            name="Signal",
            line=dict(color=ct["ma20_color"], width=1.5),
        )
    )

    hist_colors = [
        ct["up_color"] if val >= 0 else ct["down_color"]
        for val in df["MACD_Histogram"]
    ]

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["MACD_Histogram"],
            name="Histogram",
            marker_color=hist_colors,
            opacity=0.75,
        )
    )

    fig.update_layout(
        title=dict(
            text="MACD (12, 26, 9)",
            font=dict(size=14, color=ct["font_color"], family=ct["font_family"]),
        ),
        height=280,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=10, r=10, t=55, b=10),
        font=dict(family=ct["font_family"], color=ct["font_color"]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.06,
            xanchor="right",
            x=1,
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
        hoverlabel=dict(
            bgcolor=ct["hover_bg"],
            bordercolor=ct["hover_border"],
            font=dict(color=ct["hover_font_color"], family=ct["font_family"]),
        ),
    )

    return fig


def create_atr_chart(df: pd.DataFrame, theme_name: str = "light") -> go.Figure:
    """Create interactive ATR volatility chart matching the active theme."""
    ct = get_chart_theme(theme_name)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["ATR"],
            name="ATR (14)",
            line=dict(color="#F59E0B", width=2),
            fill="tozeroy",
            fillcolor="rgba(245, 158, 11, 0.08)",
        )
    )

    fig.update_layout(
        title=dict(
            text="Average True Range (ATR 14) — Volatility",
            font=dict(size=14, color=ct["font_color"], family=ct["font_family"]),
        ),
        height=280,
        template=ct["template"],
        paper_bgcolor=ct["paper_bgcolor"],
        plot_bgcolor=ct["plot_bgcolor"],
        margin=dict(l=10, r=10, t=55, b=10),
        font=dict(family=ct["font_family"], color=ct["font_color"]),
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
        hoverlabel=dict(
            bgcolor=ct["hover_bg"],
            bordercolor=ct["hover_border"],
            font=dict(color=ct["hover_font_color"], family=ct["font_family"]),
        ),
    )

    return fig


def create_sparkline_chart(
    series: List[float], is_positive: bool, theme_name: str = "light"
) -> go.Figure:
    """Create a minimalist, borderless sparkline chart for asset overview cards."""
    ct = get_chart_theme(theme_name)
    color = ct["up_color"] if is_positive else ct["down_color"]
    fillcolor = "rgba(16, 185, 129, 0.12)" if is_positive else "rgba(244, 63, 94, 0.12)"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=series,
            mode="lines",
            line=dict(color=color, width=1.8),
            fill="tozeroy",
            fillcolor=fillcolor,
            hoverinfo="none",
        )
    )
    fig.update_layout(
        height=45,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, showgrid=False),
        yaxis=dict(visible=False, showgrid=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig
