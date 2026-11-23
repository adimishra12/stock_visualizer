# 📈 Stock Visualizer — Financial Analytics & Portfolio Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.22%2B-3F4F75.svg)](https://plotly.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Persistent%20Ledger-003B57.svg)](https://www.sqlite.org/)
[![Render](https://img.shields.io/badge/Render-Live%20Demo-46E3B7.svg?logo=render&logoColor=white)](https://stock-visualizer-dewu.onrender.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🚀 **Live Demo:** [https://stock-visualizer-dewu.onrender.com](https://stock-visualizer-dewu.onrender.com)

**Stock Visualizer** is a modern, responsive, institutional-grade financial analytics and portfolio management platform. Inspired by tools like TradingView and Koyfin, it combines real-time market data, vectorized technical indicator calculations, standardized GAAP/IFRS financial statements, VADER NLP sentiment scoring, a weighted-average cost-basis SQLite portfolio ledger, and multi-asset comparative benchmarking—all wrapped in a sleek **Dual-Theme Design System** (Light Mode default, Dark Mode alternative).

---

## 🌟 Key Application Sections

The platform is organized into 7 specialized intelligence dashboards:

### 1. 📊 Market Overview
- **Multi-Asset Real-Time Benchmarks**: Tracks US major indices (S&P 500, Dow Jones, Nasdaq, Russell 2000), commodities (Crude Oil, Gold), 10-Year Treasury Yields, and cryptocurrencies (Bitcoin, Ethereum).
- **Interactive Mini-Sparklines**: Color-coded intraday price action trajectories.
- **One-Click Deep-Dive Navigation**: Seamlessly sends any benchmark instrument into the Stock Analysis studio.

### 2. 📈 Stock Analysis
- **Interactive Candlestick & Area Line Charts**: High-performance Plotly charts with integrated Volume panes, crosshairs, and date-range slider controls.
- **8 Dynamic Timeframe Presets**: `1D` (5m), `5D` (15m), `1M` (1d), `6M` (1d), `YTD` (1d), `1Y` (1d), `5Y` (1w), and `MAX` (1mo).
- **Fundamental Snapshot**: Real-time Market Cap, Trailing P/E, 52-Week Range progress bars, Beta, EPS, and Dividend Yield.
- **Recent Trading Data Explorer**: Formatted tabular view with instant CSV download.

### 3. 🔬 Technical Indicators Studio
- **Vectorized Mathematics**: NumPy-accelerated indicator calculations without in-place mutations.
- **Overlay Suite**: Simple Moving Averages (SMA 20, 50, 200), Exponential Moving Averages (EMA 9, 21), Bollinger Bands (20, 2σ), and Volume-Weighted Average Price (VWAP).
- **Synchronized Oscillators**: Relative Strength Index (RSI 14 with Welles Wilder smoothing), MACD (12, 26, 9) with signal line and histogram, and Average True Range (ATR 14).
- **Layout Precision**: Dedicated top margins and non-overlapping legend placement.

### 4. 📑 Financial Statements & Ratio Intelligence
- **GAAP / IFRS Standardization**: Dynamic row alias mapping across divergent Yahoo Finance reporting schemas.
- **Comprehensive Financial Statements**: Income Statement, Balance Sheet, and Cash Flow Statement (Annual & Quarterly).
- **7 Automated Valuation Ratios**:
  - *Gross Profit Margin*
  - *Operating Margin*
  - *Net Profit Margin*
  - *Current Ratio*
  - *Debt-to-Equity Ratio*
  - *Return on Assets (ROA)*
  - *Return on Equity (ROE)*
- **Historical Trajectory Charts**: Multi-bar and overlay line visualizations of Revenue, Net Income, and Free Cash Flow trends.
- **CSV Data Exports**: Export clean statement data tables with a single click.

### 5. 📰 Company News & Sentiment Engine
- **Editorial Coverage Feed**: Ingests breaking news articles via Yahoo Finance API, normalizing both legacy schemas and yfinance 1.8.0 nested payloads.
- **VADER NLP Sentiment Analysis**: Evaluates headline and summary compound polarity (Bullish, Bearish, Neutral).
- **Multi-Window Filtering**: Filter news across *Latest News*, *Last 24 Hours*, *Last 7 Days*, and *Last 30 Days*.
- **Aggregate Market Stance**: Sleek Plotly donut chart visualizing sentiment distribution alongside average compound scores.

### 6. 💼 Portfolio Tracker & Ledger
- **Persistent SQLite Database**: ACID-compliant transaction storage that survives application and browser restarts.
- **Weighted-Average Cost Basis Engine**:
  - Accurate average purchase price accounting across multiple tranches.
  - Precise partial sale calculations and realized gain/loss accounting.
  - Strict overselling prevention (cannot sell more shares than currently held).
- **Holdings Valuation**: Real-time evaluation of Invested Cost Basis, Current Value, Unrealized P/L, and Total Return %.
- **Visual Analytics**: Interactive Asset Allocation Donut, Cost Basis vs Current Value Grouped Bar, and Unrealized P/L by Holding charts.
- **Audit Ledger**: Comprehensive chronological transaction history log with deletion and CSV export capabilities.

### 7. ⚖️ Multi-Stock Comparative Intelligence
- **Cross-Sectional Benchmark (2 to 6 Stocks)**: Compare competitors (e.g. `AAPL`, `MSFT`, `NVDA`) simultaneously.
- **Normalized Performance (Base 100)**: Normalizes price series to 100 at the start of any selected timeframe to allow direct relative growth comparison across differently priced equities.
- **Fundamental & Technical Matrices**: Side-by-side comparison tables of valuation ratios, growth metrics, moving averages, and annualized historical volatility ($\sigma \times \sqrt{252}$).
- **Benchmark Leaders Summary**: Objective mathematical identification of Top Performer, Lowest P/E, Largest Market Cap, Highest ROE, and Lowest Volatility.

---

## 🎨 Dual-Theme Design System

- **Light Mode (Default)**: Clean white canvas (`#FFFFFF`), light violet secondary surfaces (`#F5F3FF`), deep purple accent (`#6D28D9`), high-contrast slate text (`#111827`), and subtle borders.
- **Dark Mode**: Premium deep navy backdrop (`#0F172A`), card surfaces (`#1E293B`), violet accent (`#8B5CF6`), and crisp light typography (`#F8FAFC`).
- **Cross-Session Persistence**: Synchronizes theme state seamlessly between Streamlit session state and browser `localStorage`.
- **Theme-Adaptive Visualizations**: All Plotly figures dynamically resolve background, grid, font, and trace colors to match the active theme.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Framework** | Python 3.11+, Streamlit (1.35+) |
| **Market Data** | yfinance (Yahoo Finance API) |
| **Data Processing** | Pandas, NumPy |
| **Interactive Visualizations** | Plotly Graph Objects, Subplots |
| **Database** | SQLite3 (Persistent Transaction Ledger) |
| **NLP & Sentiment** | vaderSentiment (Lexicon and Rule-Based Sentiment Analysis) |
| **Styling** | Custom Dynamic CSS with CSS Variables (`:root` tokens) |

---

## 📂 Project Architecture

```
stock_visualizer/
├── app.py                           # 7-Tab Streamlit application root
├── pyproject.toml                   # Project metadata and dependencies
├── requirements.txt                 # Frozen production requirements
├── render.yaml                      # Render Blueprint deployment definition
├── .gitignore                       # Git exclusion rules
├── .streamlit/
│   └── config.toml                  # Streamlit server & theme configuration
├── data/
│   └── portfolio.db                 # Local SQLite persistent portfolio database
├── src/
│   ├── config.py                    # Theme tokens, benchmarks, timeframe presets
│   ├── services/
│   │   ├── market_data.py          # OHLCV bars, live quotes, retry backoff, caching
│   │   ├── indicators.py           # Vectorized technical formulas (SMA, RSI, MACD, etc.)
│   │   ├── financial_service.py    # Statement standardization, formatting, ratios
│   │   ├── news_service.py         # News schema normalizer & VADER sentiment
│   │   ├── portfolio_service.py    # SQLite ledger & weighted-average cost basis engine
│   │   └── comparison_service.py   # Base-100 indexing, fundamental & technical comparison
│   └── ui/
│       ├── styles.py                # Dynamic CSS injection & localStorage bridge
│       ├── charts.py                # Theme-adaptive Plotly charting engine
│       ├── market_overview.py      # Multi-asset dashboard & sparklines
│       ├── stock_analysis.py       # Primary price action studio & key stats
│       ├── technical_dashboard.py  # Synchronized indicator oscillators
│       ├── financial_statements.py # Financial statements explorer & ratio tiles
│       ├── company_news.py         # News feed cards & sentiment donut chart
│       ├── portfolio_tracker.py    # Portfolio manager, holdings table & charts
│       └── stock_comparison.py     # Multi-stock normalized performance comparison
└── tests/
    ├── test_market_data.py         # Data validation & ticker sanitization tests
    ├── test_indicators.py          # Technical indicator formula verification
    ├── test_financial_service.py   # Statement alignment & financial ratio tests
    ├── test_news_service.py        # News schema normalization & VADER tests
    ├── test_portfolio_service.py   # Portfolio ledger, cost-basis & persistence tests
    ├── test_comparison_service.py  # Base-100 indexing & comparison tests
    └── test_ui.py                  # Chart builder & theme token tests
```

---

## 💻 Local Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Git

### 1. Clone Repository
```bash
git clone https://github.com/adimishra12/stock_visualizer.git
cd stock_visualizer
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## ⚙️ Environment Variables

| Variable | Default Value | Description |
|---|---|---|
| `STOCK_PORTFOLIO_DB` | `data/portfolio.db` | Absolute or relative filesystem path to the SQLite database. Set to a persistent disk mount path (e.g. `/var/data/portfolio.db`) in production. |
| `PORT` | Provided by host (`8501`) | HTTP port assigned dynamically by Render or container environments. |

---

## 🚀 Render Deployment Guide

Stock Visualizer is designed for **native Python deployment** on [Render](https://render.com).

- **Live Demo Application**: [https://stock-visualizer-dewu.onrender.com](https://stock-visualizer-dewu.onrender.com)

### Deployment Settings (Web Service)
- **Environment**: `Python 3`
- **Region**: Any (e.g. Oregon, Frankfurt)
- **Branch**: `main`
- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  streamlit run app.py --server.port $PORT --server.address 0.0.0.0
  ```

### Storage & Persistence on Render

> [!WARNING]
> **Ephemeral Storage Limitation on Render Free Web Services**:
> Free instances on Render utilize an ephemeral disk. When a free web service spins down due to inactivity or undergoes a redeployment, local filesystem modifications—including the default SQLite database file—are reset to the base Git commit.

#### Recommended Solutions:
1. **Render Starter Plan with Persistent Disk**:
   - Upgrade to a Starter instance (or higher).
   - Attach a **Persistent Disk** mounted at `/var/data` (1 GB size is more than sufficient).
   - Set the environment variable:
     ```
     STOCK_PORTFOLIO_DB=/var/data/portfolio.db
     ```
   - This ensures all portfolio transactions and custom holdings permanently persist across restarts, builds, and redeployments.
2. **Render Blueprints (`render.yaml`)**:
   - A pre-configured `render.yaml` file is included in the repository. Connect your GitHub repository to Render Blueprints for automated setup.

---

## 🧪 Automated Testing & Verification

The test suite runs with synthetic and mocked data to ensure reliable CI/CD verification without external network dependency:

```bash
python3 -m unittest discover tests
```

To run syntax and bytecode compilation validation:
```bash
python3 -m py_compile app.py src/config.py src/services/*.py src/ui/*.py tests/*.py
```

All 46 test cases cover:
- Ticker sanitization and timeframe validation
- Technical indicators against standard financial definitions
- GAAP/IFRS statement standardization and zero-division ratio guards
- yfinance 1.8.0 nested schemas and VADER sentiment classification
- Weighted-average cost basis accounting, partial sale P/L, overselling prevention, and SQLite connection re-opening
- Base-100 normalized indexing and missing-data resilience
- Theme token resolution and chart generation

---

## 📸 Screenshots

| View | Light Mode (Default) | Dark Mode |
|---|---|---|
| **Market Overview** | [Light Preview](screenshots/light_market_overview.png) | [Dark Preview](screenshots/dark_market_overview.png) |
| **Stock Analysis** | [Light Preview](screenshots/light_stock_analysis.png) | [Dark Preview](screenshots/dark_stock_analysis.png) |
| **Technical Indicators** | [Light Preview](screenshots/light_technical_indicators.png) | [Dark Preview](screenshots/dark_technical_indicators.png) |
| **Financial Statements** | [Light Preview](screenshots/light_financial_statements.png) | [Dark Preview](screenshots/dark_financial_statements.png) |
| **Company News** | [Light Preview](screenshots/light_company_news.png) | [Dark Preview](screenshots/dark_company_news.png) |
| **Portfolio Tracker** | [Light Preview](screenshots/light_portfolio_tracker.png) | [Dark Preview](screenshots/dark_portfolio_tracker.png) |
| **Stock Comparison** | [Light Preview](screenshots/light_stock_comparison.png) | [Dark Preview](screenshots/dark_stock_comparison.png) |

---

## ⚠️ Disclaimers & Known Limitations

- **Market Data Latency**: Market data is sourced via the `yfinance` library from Yahoo Finance. Data is provided for educational and analytical purposes only and may be delayed up to 15 minutes by exchange regulations.
- **Sentiment Analysis**: News sentiment scoring is calculated using the rule-based VADER NLP engine on English headline and summary excerpts. It does not reflect non-public information or full SEC filings.
- **Corporate Actions**: Stock splits and dividend cash payouts are not automatically posted to the SQLite transaction ledger; manual adjustment transactions should be recorded for historical corporate actions.
- **Multi-Currency Assets**: Holdings are evaluated in their native reporting currency (e.g. USD, EUR, GBP). Aggregate portfolio metrics assume single-currency accounts.
- **Not Financial Advice**: Stock Visualizer provides numerical and visual analytics. None of the calculations, leader summaries, or technical oscillators constitute financial advice, investment recommendations, or buy/sell signals.

---

## 📄 License

This project is licensed under the MIT License.
