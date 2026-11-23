"""Configuration and design tokens for Stock Visualizer.

Supports dual-theme system (Light mode default, Dark mode alternative),
ticker shortcuts, and timeframe presets.
"""

import os
from typing import Dict, Any, List

# SQLite Database Location for Persistent Portfolio Storage
DEFAULT_DB_PATH = os.environ.get(
    "STOCK_PORTFOLIO_DB",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "portfolio.db")
)

THEMES: Dict[str, Dict[str, Any]] = {
    "light": {
        "name": "light",
        "label": "Light",
        "icon": "☀️",
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F5F3FF",
        "bg_card": "#FFFFFF",
        "text_primary": "#111827",
        "text_secondary": "#475569",
        "accent_primary": "#6D28D9",
        "accent_secondary": "#2563EB",
        "positive": "#10B981",
        "negative": "#F43F5E",
        "warning": "#F59E0B",
        "border": "#E5E7EB",
        "chart_grid": "rgba(229, 231, 235, 0.7)",
        "plotly_template": "plotly_white",
        "card_shadow": "0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)",
        "card_hover_shadow": "0 4px 6px -1px rgba(109, 40, 217, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.04)",
    },
    "dark": {
        "name": "dark",
        "label": "Dark",
        "icon": "🌙",
        "bg_primary": "#0F172A",
        "bg_secondary": "#1E293B",
        "bg_card": "#1E293B",
        "text_primary": "#F8FAFC",
        "text_secondary": "#CBD5E1",
        "accent_primary": "#8B5CF6",
        "accent_secondary": "#38BDF8",
        "positive": "#34D399",
        "negative": "#FB7185",
        "warning": "#FBBF24",
        "border": "#334155",
        "chart_grid": "rgba(51, 65, 85, 0.45)",
        "plotly_template": "plotly_dark",
        "card_shadow": "0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.2)",
        "card_hover_shadow": "0 4px 12px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(139, 92, 246, 0.25)",
    },
}

DEFAULT_THEME = "light"

POPULAR_TICKERS = [
    "AAPL",
    "NVDA",
    "MSFT",
    "AMZN",
    "GOOGL",
    "TSLA",
    "META",
    "SPY",
    "QQQ",
    "BTC-USD",
]

# Standard Market Overview Benchmarks
MARKET_OVERVIEW_SYMBOLS = [
    {"symbol": "^GSPC", "name": "S&P 500", "type": "Index"},
    {"symbol": "^DJI", "name": "Dow Jones", "type": "Index"},
    {"symbol": "^IXIC", "name": "Nasdaq", "type": "Index"},
    {"symbol": "^RUT", "name": "Russell 2000", "type": "Index"},
    {"symbol": "CL=F", "name": "Crude Oil", "type": "Commodity"},
    {"symbol": "GC=F", "name": "Gold", "type": "Commodity"},
    {"symbol": "^TNX", "name": "10Y Treasury", "type": "Rate"},
    {"symbol": "BTC-USD", "name": "Bitcoin", "type": "Crypto"},
    {"symbol": "ETH-USD", "name": "Ethereum", "type": "Crypto"},
]

# Timeframe specifications mapping label to yfinance period and interval
TIMEFRAME_PRESETS: Dict[str, Dict[str, Any]] = {
    "1D": {"label": "1D", "period": "1d", "interval": "5m", "is_intraday": True, "description": "1 Day (5-minute)"},
    "5D": {"label": "5D", "period": "5d", "interval": "15m", "is_intraday": True, "description": "5 Days (15-minute)"},
    "1M": {"label": "1M", "period": "1mo", "interval": "1d", "is_intraday": False, "description": "1 Month (Daily)"},
    "6M": {"label": "6M", "period": "6mo", "interval": "1d", "is_intraday": False, "description": "6 Months (Daily)"},
    "YTD": {"label": "YTD", "period": "ytd", "interval": "1d", "is_intraday": False, "description": "Year to Date (Daily)"},
    "1Y": {"label": "1Y", "period": "1y", "interval": "1d", "is_intraday": False, "description": "1 Year (Daily)"},
    "5Y": {"label": "5Y", "period": "5y", "interval": "1wk", "is_intraday": False, "description": "5 Years (Weekly)"},
    "MAX": {"label": "MAX", "period": "max", "interval": "1mo", "is_intraday": False, "description": "All Time (Monthly)"},
}

DEFAULT_TIMEFRAME = "1Y"

# Yahoo Finance Intraday Interval Limits (in days)
INTRADAY_MAX_DAYS: Dict[str, int] = {
    "1m": 7,
    "2m": 60,
    "5m": 60,
    "15m": 60,
    "30m": 60,
    "60m": 730,
    "1h": 730,
    "1d": 36500,
    "5d": 36500,
    "1wk": 36500,
    "1mo": 36500,
    "3mo": 36500,
}

def get_theme(theme_name: str) -> Dict[str, Any]:
    """Retrieve theme tokens by name, falling back to DEFAULT_THEME."""
    return THEMES.get(theme_name.lower(), THEMES[DEFAULT_THEME])
