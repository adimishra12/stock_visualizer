# Stock Market Dashboard

A comprehensive, production-ready stock market visualization and analysis dashboard built with Streamlit and Python.

## Features

### Real-Time Stock Data
- Live stock price data from Yahoo Finance
- Support for any publicly traded stock ticker
- Customizable date range selection

### Interactive Price Charts
- Candlestick charts with OHLC data
- Trading volume visualization
- Zoom, pan, and hover functionality

### Technical Indicators
- **Moving Averages**: 20-day, 50-day, and 200-day
- **RSI (Relative Strength Index)**: Momentum oscillator with overbought/oversold levels
- **MACD**: Moving Average Convergence Divergence with signal line and histogram
- **Bollinger Bands**: Volatility indicator with upper and lower bands

### Company Metrics Dashboard
- Market Capitalization
- P/E Ratio
- 52-Week High/Low
- Dividend Yield
- Beta
- Average Volume
- Earnings Per Share (EPS)

### Portfolio Management
- Personal watchlist functionality
- Quick access to saved stocks
- Session-based portfolio tracking

### Data Export
- Download historical data as CSV
- View recent trading data in tabular format

## Tech Stack

- **Frontend**: Streamlit
- **Data Source**: Yahoo Finance (yfinance)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib
- **Language**: Python 3.11+

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stock-market-dashboard.git
cd stock-market-dashboard
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install streamlit yfinance pandas matplotlib plotly
```

4. Run the application:
```bash
streamlit run app.py
```

5. Open your browser and navigate to `http://localhost:8501`

## Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Select the main file (`app.py`)
5. Click "Deploy"

Your app will be available at: `https://[your-app-name].streamlit.app`

### Render.com (Backup)

1. Create a `render.yaml` file:
```yaml
services:
  - type: web
    name: stock-dashboard
    env: python
    buildCommand: pip install streamlit yfinance pandas matplotlib plotly
    startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

2. Connect your GitHub repo to Render
3. Deploy as a Web Service

## Project Structure

```
stock-market-dashboard/
├── app.py              # Main Streamlit application
├── .streamlit/
│   └── config.toml     # Streamlit configuration
├── README.md           # Project documentation
├── .gitignore          # Git ignore file
└── pyproject.toml      # Python project configuration
```

## Usage

1. **Enter a Ticker**: Type a valid stock symbol (e.g., AAPL, GOOGL, MSFT) in the sidebar
2. **Select Date Range**: Choose your analysis period
3. **Toggle Indicators**: Enable/disable technical indicators using checkboxes
4. **Add to Watchlist**: Save frequently viewed stocks for quick access
5. **Download Data**: Export historical data as CSV for further analysis

## Error Handling

The application includes robust error handling for:
- Invalid ticker symbols
- API timeouts
- Empty data responses
- Network connectivity issues
- Date validation

## Disclaimer

This dashboard is for **educational and informational purposes only**. It does not constitute financial advice. Always consult with a qualified financial advisor before making investment decisions.

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
