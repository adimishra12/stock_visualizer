import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import re

st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    .header-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        pointer-events: none;
    }
    
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    .sub-header {
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.7);
        text-align: center;
        margin-bottom: 0;
        font-weight: 400;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .company-header {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .company-name {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.25rem;
    }
    
    .company-ticker {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.6);
        font-weight: 500;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #1e1e2f 0%, #252540 100%);
        padding: 1.25rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .metric-value-large {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .metric-change-positive {
        color: #00d26a;
        font-size: 0.95rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .metric-change-negative {
        color: #ff6b6b;
        font-size: 0.95rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .price-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #1e2235 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.25);
    }
    
    .price-card-primary {
        background: linear-gradient(145deg, #252540 0%, #2d2d50 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .chart-container {
        background: linear-gradient(145deg, #1a1a2e 0%, #1e2235 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.2);
        margin-bottom: 1.5rem;
    }
    
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .data-table-container {
        background: linear-gradient(145deg, #1a1a2e 0%, #1e2235 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 25px rgba(0, 0, 0, 0.2);
    }
    
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
        margin: 2rem 0;
        border: none;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }
    
    .sidebar-section {
        background: rgba(255, 255, 255, 0.03);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .sidebar-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .sidebar-subtitle {
        font-size: 0.95rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    [data-testid="stSidebar"] .stCheckbox label {
        color: rgba(255, 255, 255, 0.8);
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .watchlist-item {
        background: rgba(255, 255, 255, 0.05);
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    
    .watchlist-item:hover {
        background: rgba(102, 126, 234, 0.2);
    }
    
    .stMetric {
        background: linear-gradient(145deg, #1e1e2f 0%, #252540 100%);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .stMetric:hover {
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    
    .footer-container {
        background: linear-gradient(145deg, #0d0d15 0%, #1a1a2e 100%);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        margin-top: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        text-align: center;
    }
    
    .footer-text {
        color: rgba(255, 255, 255, 0.4);
        font-size: 0.85rem;
        margin: 0.25rem 0;
    }
    
    .footer-disclaimer {
        color: rgba(255, 200, 100, 0.6);
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    .indicator-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .badge-green {
        background: rgba(0, 210, 106, 0.15);
        color: #00d26a;
        border: 1px solid rgba(0, 210, 106, 0.3);
    }
    
    .badge-red {
        background: rgba(255, 107, 107, 0.15);
        color: #ff6b6b;
        border: 1px solid rgba(255, 107, 107, 0.3);
    }
    
    .metrics-grid {
        display: grid;
        gap: 1rem;
    }
    
    .info-card {
        background: linear-gradient(145deg, #1e1e2f 0%, #252540 100%);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        border-color: rgba(102, 126, 234, 0.3);
        transform: translateY(-2px);
    }
    
    .info-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    .empty-state {
        text-align: center;
        padding: 3rem;
        background: linear-gradient(145deg, #1a1a2e 0%, #1e2235 100%);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .empty-state-text {
        color: rgba(255, 255, 255, 0.6);
        font-size: 1.1rem;
    }
    
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
    }
    
    .stSpinner > div {
        border-color: #667eea transparent transparent transparent;
    }
</style>
""", unsafe_allow_html=True)

def sanitize_ticker(ticker):
    """Sanitize and validate ticker symbol input."""
    if not ticker:
        return None
    ticker = ticker.strip().upper()
    ticker = re.sub(r'[^A-Z0-9.\-^]', '', ticker)
    if len(ticker) > 10 or len(ticker) < 1:
        return None
    return ticker

@st.cache_data(ttl=300)
def get_stock_data(ticker, start_date, end_date):
    """Fetch stock price data with caching and error handling."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, timeout=10)
        if df.empty:
            return None, "No data available for this ticker and date range."
        return df, None
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            return None, "Request timed out. Please try again."
        elif "not found" in error_msg.lower() or "404" in error_msg:
            return None, "Ticker symbol not found. Please check and try again."
        else:
            return None, f"Error fetching data: {error_msg}"

@st.cache_data(ttl=300)
def get_stock_info(ticker):
    """Fetch company info separately to handle partial failures gracefully."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info, None
    except Exception as e:
        return None, f"Could not fetch company info: {str(e)}"

def calculate_technical_indicators(df):
    """Calculate technical indicators for the stock data."""
    df = df.copy()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']
    
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    bb_std = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df

def create_price_chart(df, ticker, show_ma20, show_ma50, show_ma200, show_bb):
    """Create interactive price chart with optional indicators."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{ticker} Stock Price', 'Trading Volume')
    )
    
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#00d26a',
            decreasing_line_color='#ff6b6b'
        ),
        row=1, col=1
    )
    
    if show_ma20 and 'MA20' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA20'], name='MA20', 
                      line=dict(color='#ffa726', width=1.5)),
            row=1, col=1
        )
    
    if show_ma50 and 'MA50' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA50'], name='MA50', 
                      line=dict(color='#42a5f5', width=1.5)),
            row=1, col=1
        )
    
    if show_ma200 and 'MA200' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA200'], name='MA200', 
                      line=dict(color='#ab47bc', width=1.5)),
            row=1, col=1
        )
    
    if show_bb and 'BB_Upper' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Upper',
                      line=dict(color='rgba(156, 163, 175, 0.7)', width=1, dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Lower',
                      line=dict(color='rgba(156, 163, 175, 0.7)', width=1, dash='dash'),
                      fill='tonexty', fillcolor='rgba(156, 163, 175, 0.1)'),
            row=1, col=1
        )
    
    colors = ['#00d26a' if df['Close'].iloc[i] >= df['Open'].iloc[i] 
              else '#ff6b6b' for i in range(len(df))]
    
    fig.add_trace(
        go.Bar(x=df.index, y=df['Volume'], name='Volume',
               marker_color=colors, opacity=0.7),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0e0e0')
        ),
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26, 26, 46, 0.8)',
        margin=dict(l=10, r=10, t=40, b=10),
        font=dict(color='#e0e0e0')
    )
    
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(128, 128, 128, 0.15)',
        linecolor='rgba(128, 128, 128, 0.2)'
    )
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(128, 128, 128, 0.15)',
        linecolor='rgba(128, 128, 128, 0.2)'
    )
    
    return fig

def create_rsi_chart(df):
    """Create RSI indicator chart."""
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(x=df.index, y=df['RSI'], name='RSI',
                  line=dict(color='#667eea', width=2),
                  fill='tozeroy', fillcolor='rgba(102, 126, 234, 0.1)')
    )
    
    fig.add_hline(y=70, line_dash="dash", line_color="#ff6b6b", 
                  annotation_text="Overbought (70)", 
                  annotation_font_color="#ff6b6b")
    fig.add_hline(y=30, line_dash="dash", line_color="#00d26a",
                  annotation_text="Oversold (30)",
                  annotation_font_color="#00d26a")
    fig.add_hline(y=50, line_dash="dot", line_color="rgba(255,255,255,0.2)")
    
    fig.update_layout(
        title=dict(
            text='Relative Strength Index (RSI)',
            font=dict(size=16, color='#e0e0e0')
        ),
        height=300,
        template='plotly_dark',
        yaxis=dict(range=[0, 100], gridcolor='rgba(128, 128, 128, 0.15)'),
        xaxis=dict(gridcolor='rgba(128, 128, 128, 0.15)'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26, 26, 46, 0.8)',
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(color='#e0e0e0')
    )
    
    return fig

def create_macd_chart(df):
    """Create MACD indicator chart."""
    fig = go.Figure()
    
    fig.add_trace(
        go.Scatter(x=df.index, y=df['MACD'], name='MACD',
                  line=dict(color='#667eea', width=2))
    )
    
    fig.add_trace(
        go.Scatter(x=df.index, y=df['Signal_Line'], name='Signal Line',
                  line=dict(color='#ffa726', width=2))
    )
    
    colors = ['#00d26a' if val >= 0 else '#ff6b6b' for val in df['MACD_Histogram']]
    fig.add_trace(
        go.Bar(x=df.index, y=df['MACD_Histogram'], name='Histogram',
               marker_color=colors, opacity=0.7)
    )
    
    fig.update_layout(
        title=dict(
            text='MACD (Moving Average Convergence Divergence)',
            font=dict(size=16, color='#e0e0e0')
        ),
        height=300,
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26, 26, 46, 0.8)',
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(color='#e0e0e0'),
        xaxis=dict(gridcolor='rgba(128, 128, 128, 0.15)'),
        yaxis=dict(gridcolor='rgba(128, 128, 128, 0.15)'),
        legend=dict(bgcolor='rgba(0,0,0,0)')
    )
    
    return fig

def format_large_number(num):
    """Format large numbers for display."""
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

def format_number(num, prefix="", suffix="", decimals=2):
    """Format numbers consistently."""
    if num is None or pd.isna(num):
        return "N/A"
    return f"{prefix}{num:,.{decimals}f}{suffix}"

def display_company_info(info, current_price, prev_price):
    """Display company information metrics with enhanced styling."""
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
    change_class = "metric-change-positive" if price_change >= 0 else "metric-change-negative"
    change_arrow = "▲" if price_change >= 0 else "▼"
    badge_class = "badge-green" if price_change >= 0 else "badge-red"
    
    week_high = info.get('fiftyTwoWeekHigh')
    week_high_display = f"${week_high:.2f}" if week_high else "N/A"
    week_low = info.get('fiftyTwoWeekLow')
    week_low_display = f"${week_low:.2f}" if week_low else "N/A"
    day_high = info.get('dayHigh')
    day_high_display = f"${day_high:.2f}" if day_high else "N/A"
    day_low = info.get('dayLow')
    day_low_display = f"${day_low:.2f}" if day_low else "N/A"
    
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
        <div class="price-card price-card-primary">
            <div class="metric-label">Current Price</div>
            <div class="metric-value-large">${current_price:.2f}</div>
            <div class="{change_class}" style="margin-top: 0.5rem;">
                <span class="indicator-badge {badge_class}">
                    {change_arrow} {abs(price_change):.2f} ({abs(price_change_pct):.2f}%)
                </span>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div class="info-card">
                <div class="metric-label">52-Week High</div>
                <div class="metric-value">{week_high_display}</div>
            </div>
            <div class="info-card">
                <div class="metric-label">52-Week Low</div>
                <div class="metric-value">{week_low_display}</div>
            </div>
            <div class="info-card">
                <div class="metric-label">Day High</div>
                <div class="metric-value" style="color: #00d26a;">{day_high_display}</div>
            </div>
            <div class="info-card">
                <div class="metric-label">Day Low</div>
                <div class="metric-value" style="color: #ff6b6b;">{day_low_display}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        market_cap = info.get('marketCap', None)
        st.markdown(f"""
        <div class="metric-card">
            <div class="info-icon">💰</div>
            <div class="metric-label">Market Cap</div>
            <div class="metric-value">{format_large_number(market_cap)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pe_ratio = info.get('trailingPE', None)
        pe_display = f"{pe_ratio:.2f}" if pe_ratio else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="info-icon">📊</div>
            <div class="metric-label">P/E Ratio</div>
            <div class="metric-value">{pe_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        dividend_yield = info.get('dividendYield', None)
        div_display = f"{dividend_yield*100:.2f}%" if dividend_yield else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="info-icon">💵</div>
            <div class="metric-label">Dividend Yield</div>
            <div class="metric-value">{div_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        eps = info.get('trailingEps', None)
        eps_display = f"${eps:.2f}" if eps else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="info-icon">📈</div>
            <div class="metric-label">EPS</div>
            <div class="metric-value">{eps_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        avg_volume = info.get('averageVolume', None)
        vol_display = f"{avg_volume:,.0f}" if avg_volume else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="info-icon">📉</div>
            <div class="metric-label">Avg Volume</div>
            <div class="metric-value" style="font-size: 1.2rem;">{vol_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        beta = info.get('beta', None)
        beta_display = f"{beta:.2f}" if beta else "N/A"
        beta_color = "#ffa726" if beta and beta > 1 else "#00d26a" if beta else "#e0e0e0"
        st.markdown(f"""
        <div class="metric-card">
            <div class="info-icon">⚡</div>
            <div class="metric-label">Beta</div>
            <div class="metric-value" style="color: {beta_color};">{beta_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col7:
        forward_pe = info.get('forwardPE', None)
        fpe_display = f"{forward_pe:.2f}" if forward_pe else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="info-icon">🔮</div>
            <div class="metric-label">Forward P/E</div>
            <div class="metric-value">{fpe_display}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col8:
        price_to_book = info.get('priceToBook', None)
        pb_display = f"{price_to_book:.2f}" if price_to_book else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <div class="info-icon">📚</div>
            <div class="metric-label">Price/Book</div>
            <div class="metric-value">{pb_display}</div>
        </div>
        """, unsafe_allow_html=True)

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = "AAPL"

st.markdown("""
<div class="header-container">
    <h1 class="main-header">📈 Stock Market Dashboard</h1>
    <p class="sub-header">Real-time stock analysis with technical indicators</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-title">📊 Dashboard Controls</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    ticker_input = st.text_input(
        "Enter Stock Ticker",
        value=st.session_state.current_ticker,
        key="ticker_input_field",
        help="Enter a valid stock ticker symbol (e.g., AAPL, GOOGL, MSFT)"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    ticker = sanitize_ticker(ticker_input)
    
    if not ticker:
        st.error("Please enter a valid ticker symbol")
    
    st.markdown('<div class="sidebar-subtitle">📅 Date Range</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        default_start = datetime.now() - timedelta(days=365)
        start_date = st.date_input("Start Date", value=default_start)
    
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    if start_date >= end_date:
        st.error("Start date must be before end date")
    
    st.markdown('<div class="sidebar-subtitle">📉 Technical Indicators</div>', unsafe_allow_html=True)
    show_ma20 = st.checkbox("20-Day Moving Average", value=True)
    show_ma50 = st.checkbox("50-Day Moving Average", value=True)
    show_ma200 = st.checkbox("200-Day Moving Average", value=False)
    show_bb = st.checkbox("Bollinger Bands", value=False)
    show_rsi = st.checkbox("RSI Chart", value=True)
    show_macd = st.checkbox("MACD Chart", value=True)
    
    st.markdown('<div class="sidebar-subtitle">⭐ Watchlist</div>', unsafe_allow_html=True)
    
    if ticker and st.button("➕ Add to Watchlist", use_container_width=True):
        if ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(ticker)
            st.success(f"Added {ticker} to watchlist!")
        else:
            st.warning(f"{ticker} is already in watchlist")
    
    if st.session_state.watchlist:
        st.markdown("<div style='margin-top: 0.5rem;'>", unsafe_allow_html=True)
        for i, watch_ticker in enumerate(st.session_state.watchlist):
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"📌 {watch_ticker}", key=f"watch_{i}", use_container_width=True):
                    st.session_state.current_ticker = watch_ticker
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state.watchlist.remove(watch_ticker)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No stocks in watchlist")
    
    if ticker_input and ticker_input != st.session_state.current_ticker:
        st.session_state.current_ticker = ticker_input

if ticker and start_date < end_date:
    with st.spinner(f"Fetching data for {ticker}..."):
        df, price_error = get_stock_data(ticker, start_date, end_date)
        info, info_error = get_stock_info(ticker)
    
    if price_error:
        st.error(f"⚠️ {price_error}")
    elif df is not None and not df.empty:
        df = calculate_technical_indicators(df)
        
        company_name = info.get('longName', ticker) if info else ticker
        sector = info.get('sector', '') if info else ''
        industry = info.get('industry', '') if info else ''
        
        st.markdown(f"""
        <div class="company-header">
            <div class="company-name">{company_name}</div>
            <div class="company-ticker">{ticker} {'• ' + sector if sector else ''} {'• ' + industry if industry else ''}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if info_error:
            st.warning(f"Note: {info_error}")
        
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        
        if info:
            display_company_info(info, current_price, prev_price)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="chart-container">
            <div class="chart-title">📈 Price Chart & Volume</div>
        </div>
        """, unsafe_allow_html=True)
        
        price_chart = create_price_chart(df, ticker, show_ma20, show_ma50, show_ma200, show_bb)
        st.plotly_chart(price_chart, width="stretch")
        
        if show_rsi or show_macd:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-header">📊 Technical Analysis</div>', unsafe_allow_html=True)
            
            if show_rsi and show_macd:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    rsi_chart = create_rsi_chart(df)
                    st.plotly_chart(rsi_chart, width="stretch")
                    st.markdown('</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    macd_chart = create_macd_chart(df)
                    st.plotly_chart(macd_chart, width="stretch")
                    st.markdown('</div>', unsafe_allow_html=True)
            elif show_rsi:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                rsi_chart = create_rsi_chart(df)
                st.plotly_chart(rsi_chart, width="stretch")
                st.markdown('</div>', unsafe_allow_html=True)
            elif show_macd:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                macd_chart = create_macd_chart(df)
                st.plotly_chart(macd_chart, width="stretch")
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="data-table-container">
            <div class="chart-title">📋 Recent Trading Data</div>
        </div>
        """, unsafe_allow_html=True)
        
        display_df = df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10).copy()
        display_df = display_df.round(2)
        display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{x:,.0f}")
        display_df.index = display_df.index.strftime('%Y-%m-%d')
        
        st.dataframe(display_df, width="stretch")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            csv = df.to_csv()
            st.download_button(
                label="📥 Download Full Data (CSV)",
                data=csv,
                file_name=f"{ticker}_stock_data.csv",
                mime="text/csv",
                width="stretch"
            )

else:
    if not ticker:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📊</div>
            <div class="empty-state-text">Enter a valid stock ticker symbol in the sidebar to get started</div>
        </div>
        """, unsafe_allow_html=True)
    elif start_date >= end_date:
        st.warning("Please select a valid date range (start date must be before end date).")

st.markdown("""
<div class="footer-container">
    <p class="footer-text">Stock Market Dashboard | Data provided by Yahoo Finance</p>
    <p class="footer-disclaimer">⚠️ This is for educational purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
