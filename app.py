from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components

from src.config import (
    DEFAULT_THEME,
    DEFAULT_TIMEFRAME,
    POPULAR_TICKERS,
    get_theme,
)
from src.services.market_data import sanitize_ticker
from src.ui.company_news import render_company_news
from src.ui.financial_statements import render_financial_statements
from src.ui.market_overview import render_market_overview
from src.ui.portfolio_tracker import render_portfolio_tracker
from src.ui.stock_analysis import render_stock_analysis
from src.ui.stock_comparison import render_stock_comparison
from src.ui.styles import (
    get_theme_css,
    render_tab_switch_script,
    render_theme_persistence_script,
)
from src.ui.technical_dashboard import render_technical_dashboard

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Stock Visualizer — Financial Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Theme State & Cross-Session Persistence
# -----------------------------------------------------------------------------
url_theme = st.query_params.get("theme", None)

if "theme" not in st.session_state:
    if url_theme in ["light", "dark"]:
        st.session_state.theme = url_theme
    else:
        st.session_state.theme = DEFAULT_THEME
elif url_theme in ["light", "dark"] and url_theme != st.session_state.theme:
    st.session_state.theme = url_theme

current_theme = st.session_state.theme

# Inject Dynamic CSS and localStorage Persistence Bridge
st.markdown(get_theme_css(current_theme), unsafe_allow_html=True)
components.html(render_theme_persistence_script(current_theme), height=0, width=0)

# -----------------------------------------------------------------------------
# Session State Initialization & Navigation Handling
# -----------------------------------------------------------------------------
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "NVDA", "MSFT", "AMZN"]

if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "AAPL"

if "timeframe" not in st.session_state:
    st.session_state.timeframe = DEFAULT_TIMEFRAME

if "date_mode" not in st.session_state:
    st.session_state.date_mode = "preset"

# Handle pending ticker change (from Analyze buttons, shortcuts, watchlist)
if "pending_ticker" in st.session_state and st.session_state.pending_ticker:
    new_sym = st.session_state.pop("pending_ticker")
    st.session_state.current_ticker = new_sym
    st.session_state.sidebar_ticker_input = new_sym

# Handle target tab navigation
target_tab = None
if "target_tab" in st.session_state and st.session_state.target_tab is not None:
    target_tab = st.session_state.pop("target_tab")

if target_tab is not None:
    import time as _t
    components.html(render_tab_switch_script(target_tab, nonce=_t.time()), height=0, width=0)

# -----------------------------------------------------------------------------
# Section 1 – Top Branding (Logo, Title & Tagline)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="header-branding-section">
        <h1 class="brand-title">
            📈 Stock <span>Visualizer</span>
        </h1>
        <p class="brand-subtitle">
            Real-Time Market Analytics & Technical Intelligence
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Section 2 – Popular Shortcuts (Evenly Distributed Horizontal Row)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="shortcuts-header-label">
        Popular Shortcuts
    </div>
    """,
    unsafe_allow_html=True,
)

popular_subset = ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "TSLA", "META"]
pop_cols = st.columns(len(popular_subset))

for idx, p_tick in enumerate(popular_subset):
    with pop_cols[idx]:
        is_active = (p_tick == st.session_state.current_ticker)
        label = f"● {p_tick}" if is_active else p_tick
        if st.button(label, key=f"quick_nav_{p_tick}", use_container_width=True):
            st.session_state.pending_ticker = p_tick
            st.session_state.target_tab = 1
            st.rerun()

st.markdown("<div style='height: 0.85rem;'></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar: Global Navigation, Instrument Search & Watchlist
# -----------------------------------------------------------------------------
with st.sidebar:
    is_dark_active = (current_theme == "dark")
    toggle_label = "🌙 Dark Mode" if is_dark_active else "☀️ Light Mode"
    switch_val = st.toggle(
        toggle_label,
        value=is_dark_active,
        key="theme_pill_toggle",
        help="Switch to Light Mode" if is_dark_active else "Switch to Dark Mode",
    )

    if switch_val != is_dark_active:
        new_theme = "dark" if switch_val else "light"
        st.session_state.theme = new_theme
        st.query_params["theme"] = new_theme
        st.rerun()

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title' style='margin-top:0;'>🔍 Instrument Search</div>", unsafe_allow_html=True)

    if "sidebar_ticker_input" not in st.session_state:
        st.session_state.sidebar_ticker_input = st.session_state.current_ticker

    ticker_input = st.text_input(
        "Search Symbol",
        key="sidebar_ticker_input",
        help="Enter any stock symbol (e.g. AAPL, NVDA, TSLA, MSFT, BTC-USD)",
    )

    clean_sym = sanitize_ticker(ticker_input)
    if not clean_sym:
        st.error("Please enter a valid stock symbol")
    elif clean_sym != st.session_state.current_ticker:
        st.session_state.current_ticker = clean_sym

    active_ticker = st.session_state.current_ticker

    st.markdown("<div class='section-title'>📅 Date Range Filter</div>", unsafe_allow_html=True)
    default_start = datetime.now() - timedelta(days=365)
    c_start = st.date_input("Start Date", value=default_start, key="sb_start_date")
    c_end = st.date_input("End Date", value=datetime.now(), key="sb_end_date")

    if c_start < c_end:
        st.session_state.custom_start_date = c_start
        st.session_state.custom_end_date = c_end
    else:
        st.error("Start date must be before end date")

    st.markdown("<div class='section-title'>⭐ Personal Watchlist</div>", unsafe_allow_html=True)

    if active_ticker and st.button(f"➕ Add {active_ticker} to Watchlist", use_container_width=True):
        if active_ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(active_ticker)
            st.success(f"Added {active_ticker} to watchlist")
        else:
            st.info(f"{active_ticker} is already in your watchlist")

    if st.session_state.watchlist:
        st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
        for i, w_sym in enumerate(st.session_state.watchlist):
            c_wl_btn, c_wl_del = st.columns([4, 1])
            with c_wl_btn:
                is_current = (w_sym == active_ticker)
                wl_label = f"● {w_sym}" if is_current else f"📌 {w_sym}"
                if st.button(wl_label, key=f"wl_select_{i}_{w_sym}", use_container_width=True):
                    st.session_state.pending_ticker = w_sym
                    st.session_state.target_tab = 1
                    st.rerun()
            with c_wl_del:
                if st.button("✕", key=f"wl_remove_{i}_{w_sym}", help=f"Remove {w_sym}", use_container_width=True):
                    st.session_state.watchlist.remove(w_sym)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Watchlist is empty. Add symbols using the button above.")

# -----------------------------------------------------------------------------
# Main Application Tabs
# -----------------------------------------------------------------------------
tab_overview, tab_analysis, tab_technicals, tab_financials, tab_news, tab_portfolio, tab_comparison = st.tabs(
    [
        "📊 Market Overview",
        "📈 Stock Analysis",
        "🔬 Technical Indicators",
        "📑 Financial Statements",
        "📰 Company News",
        "💼 Portfolio Tracker",
        "⚖️ Stock Comparison",
    ]
)

with tab_overview:
    render_market_overview(theme_name=current_theme)

with tab_analysis:
    render_stock_analysis(ticker=active_ticker, theme_name=current_theme)

with tab_technicals:
    render_technical_dashboard(ticker=active_ticker, theme_name=current_theme)

with tab_financials:
    render_financial_statements(ticker=active_ticker, theme_name=current_theme)

with tab_news:
    render_company_news(ticker=active_ticker, theme_name=current_theme)

with tab_portfolio:
    render_portfolio_tracker(theme_name=current_theme)

with tab_comparison:
    render_stock_comparison(theme_name=current_theme)

# -----------------------------------------------------------------------------
# Global Footer
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="footer-bar">
        Stock Visualizer • Financial Analytics Platform • Data via Yahoo Finance API • Theme: {current_theme.capitalize()} Mode
    </div>
    """,
    unsafe_allow_html=True,
)
