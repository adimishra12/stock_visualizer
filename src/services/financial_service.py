"""Financial statements service.

Retrieves, caches, standardizes, and calculates ratios for:
- Income Statement (Annual & Quarterly)
- Balance Sheet (Annual & Quarterly)
- Cash Flow Statement (Annual & Quarterly)
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from src.services.market_data import sanitize_ticker

# Alias mappings for financial statement row names across Yahoo Finance versions
INCOME_STATEMENT_METRICS = [
    ("Total Revenue", ["Total Revenue", "Operating Revenue"]),
    ("Cost of Revenue", ["Cost Of Revenue", "Reconciled Cost Of Revenue"]),
    ("Gross Profit", ["Gross Profit"]),
    ("Operating Income", ["Operating Income", "Total Operating Income As Reported"]),
    ("Operating Expenses", ["Operating Expense", "Total Expenses"]),
    ("Net Income", ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operation Net Minority Interest"]),
    ("EBITDA", ["EBITDA", "Normalized EBITDA"]),
    ("Basic EPS", ["Basic EPS", "Basic Continuous Operations EPS"]),
    ("Diluted EPS", ["Diluted EPS", "Diluted Continuous Operations EPS"]),
]

BALANCE_SHEET_METRICS = [
    ("Total Assets", ["Total Assets"]),
    ("Total Liabilities", ["Total Liabilities Net Minority Interest", "Total Liabilities"]),
    ("Total Stockholder Equity", ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"]),
    ("Cash & Cash Equivalents", ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]),
    ("Total Debt", ["Total Debt"]),
    ("Current Assets", ["Current Assets"]),
    ("Current Liabilities", ["Current Liabilities"]),
    ("Working Capital", ["Working Capital"]),
]

CASH_FLOW_METRICS = [
    ("Operating Cash Flow", ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]),
    ("Investing Cash Flow", ["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"]),
    ("Financing Cash Flow", ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"]),
    ("Capital Expenditure", ["Capital Expenditure"]),
    ("Free Cash Flow", ["Free Cash Flow"]),
    ("Changes in Cash", ["Changes In Cash"]),
]


def format_currency_value(val: Optional[float], currency_symbol: str = "$") -> str:
    """Format large monetary numbers into readable K, M, B, T notations."""
    if val is None or pd.isna(val):
        return "-"
    try:
        val = float(val)
    except (ValueError, TypeError):
        return "-"

    sign = "-" if val < 0 else ""
    abs_val = abs(val)

    if abs_val >= 1e12:
        return f"{sign}{currency_symbol}{abs_val/1e12:.2f}T"
    elif abs_val >= 1e9:
        return f"{sign}{currency_symbol}{abs_val/1e9:.2f}B"
    elif abs_val >= 1e6:
        return f"{sign}{currency_symbol}{abs_val/1e6:.2f}M"
    elif abs_val >= 1e3:
        return f"{sign}{currency_symbol}{abs_val/1e3:.2f}K"
    elif abs_val > 0:
        return f"{sign}{currency_symbol}{abs_val:.2f}"
    else:
        return f"{currency_symbol}0.00"


def _find_row_value(df: pd.DataFrame, aliases: List[str]) -> Optional[pd.Series]:
    """Find the first matching row in a statement DataFrame using alias candidates."""
    if df is None or df.empty:
        return None
    for alias in aliases:
        if alias in df.index:
            return df.loc[alias]
        # Case-insensitive substring match fallback
        matches = [idx for idx in df.index if alias.lower() in idx.lower()]
        if matches:
            return df.loc[matches[0]]
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_financial_statements(ticker: str) -> Dict[str, Any]:
    """Fetch annual and quarterly statements for a ticker from Yahoo Finance."""
    clean_ticker = sanitize_ticker(ticker)
    if not clean_ticker:
        return {}

    try:
        stock = yf.Ticker(clean_ticker)
        info = stock.info or {}
        currency = info.get("currency", "USD")

        return {
            "ticker": clean_ticker,
            "currency": currency,
            "income_annual": stock.financials,
            "income_quarterly": stock.quarterly_financials,
            "balance_annual": stock.balance_sheet,
            "balance_quarterly": stock.quarterly_balance_sheet,
            "cashflow_annual": stock.cashflow,
            "cashflow_quarterly": stock.quarterly_cashflow,
        }
    except Exception as e:
        return {"error": str(e), "ticker": clean_ticker}


def build_standardized_statement(
    df: Optional[pd.DataFrame],
    metric_definitions: List[Tuple[str, List[str]]],
    is_quarterly: bool = False,
) -> pd.DataFrame:
    """Format and standardize financial statement rows and period columns.

    Columns are ordered chronologically newest first.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Sort columns chronologically (newest first)
    cols = sorted(df.columns, reverse=True)
    formatted_cols = []
    for c in cols:
        if isinstance(c, (pd.Timestamp, str)):
            dt = pd.to_datetime(c)
            if is_quarterly:
                quarter = (dt.month - 1) // 3 + 1
                formatted_cols.append(f"{dt.year}-Q{quarter}")
            else:
                formatted_cols.append(f"FY {dt.year}")
        else:
            formatted_cols.append(str(c))

    table_data = {}
    for standard_name, aliases in metric_definitions:
        row_series = _find_row_value(df, aliases)
        if row_series is not None:
            # Reindex to sorted columns
            vals = [row_series.get(c, np.nan) for c in cols]
            table_data[standard_name] = vals
        else:
            table_data[standard_name] = [np.nan] * len(cols)

    result_df = pd.DataFrame(table_data, index=formatted_cols).T
    return result_df


def extract_metric_series(
    df: Optional[pd.DataFrame], aliases: List[str]
) -> Tuple[List[str], List[float]]:
    """Extract a chronological (oldest to newest) time series for Plotly charting."""
    if df is None or df.empty:
        return [], []

    row = _find_row_value(df, aliases)
    if row is None:
        return [], []

    # Sort chronological (oldest to newest for charting)
    cols = sorted(df.columns)
    labels = []
    values = []

    for c in cols:
        val = row.get(c, np.nan)
        if pd.notna(val):
            dt = pd.to_datetime(c)
            labels.append(dt.strftime("%Y-%m"))
            values.append(float(val))

    return labels, values


def calculate_financial_ratios(
    income_df: Optional[pd.DataFrame],
    balance_df: Optional[pd.DataFrame],
    cashflow_df: Optional[pd.DataFrame],
) -> List[Dict[str, Any]]:
    """Calculate standard key financial ratios for the latest available reporting period."""
    ratios = []

    # Helper to get latest scalar value
    def get_latest(df: Optional[pd.DataFrame], aliases: List[str]) -> Optional[float]:
        if df is None or df.empty:
            return None
        row = _find_row_value(df, aliases)
        if row is None:
            return None
        newest_col = sorted(df.columns, reverse=True)[0]
        val = row.get(newest_col, np.nan)
        if pd.notna(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
        return None

    # Retrieve components
    revenue = get_latest(income_df, ["Total Revenue", "Operating Revenue"])
    gross_profit = get_latest(income_df, ["Gross Profit"])
    op_income = get_latest(income_df, ["Operating Income", "Total Operating Income As Reported"])
    net_income = get_latest(income_df, ["Net Income", "Net Income Common Stockholders"])
    curr_assets = get_latest(balance_df, ["Current Assets"])
    curr_liab = get_latest(balance_df, ["Current Liabilities"])
    total_debt = get_latest(balance_df, ["Total Debt"])
    equity = get_latest(balance_df, ["Stockholders Equity", "Common Stock Equity"])
    total_assets = get_latest(balance_df, ["Total Assets"])

    # 1. Gross Profit Margin
    if gross_profit is not None and revenue and revenue > 0:
        val = (gross_profit / revenue) * 100.0
        ratios.append({
            "name": "Gross Profit Margin",
            "value": f"{val:.2f}%",
            "numeric": val,
            "description": "Percentage of revenue retained after incurring direct costs of producing goods/services.",
            "is_positive": val >= 20.0,
        })
    else:
        ratios.append({"name": "Gross Profit Margin", "value": "N/A", "numeric": None, "description": "Gross Profit / Total Revenue", "is_positive": None})

    # 2. Operating Margin
    if op_income is not None and revenue and revenue > 0:
        val = (op_income / revenue) * 100.0
        ratios.append({
            "name": "Operating Margin",
            "value": f"{val:.2f}%",
            "numeric": val,
            "description": "Profitability from core business operations before interest and taxes.",
            "is_positive": val >= 10.0,
        })
    else:
        ratios.append({"name": "Operating Margin", "value": "N/A", "numeric": None, "description": "Operating Income / Total Revenue", "is_positive": None})

    # 3. Net Profit Margin
    if net_income is not None and revenue and revenue > 0:
        val = (net_income / revenue) * 100.0
        ratios.append({
            "name": "Net Profit Margin",
            "value": f"{val:.2f}%",
            "numeric": val,
            "description": "Bottom-line net earnings generated as a percentage of total revenue.",
            "is_positive": val >= 5.0,
        })
    else:
        ratios.append({"name": "Net Profit Margin", "value": "N/A", "numeric": None, "description": "Net Income / Total Revenue", "is_positive": None})

    # 4. Current Ratio
    if curr_assets is not None and curr_liab and curr_liab > 0:
        val = curr_assets / curr_liab
        ratios.append({
            "name": "Current Ratio",
            "value": f"{val:.2f}x",
            "numeric": val,
            "description": "Measures company's short-term liquidity and ability to cover short-term debt (>1.0 indicates good liquidity).",
            "is_positive": val >= 1.2,
        })
    else:
        ratios.append({"name": "Current Ratio", "value": "N/A", "numeric": None, "description": "Current Assets / Current Liabilities", "is_positive": None})

    # 5. Debt to Equity
    if total_debt is not None and equity and equity > 0:
        val = total_debt / equity
        ratios.append({
            "name": "Debt to Equity",
            "value": f"{val:.2f}x",
            "numeric": val,
            "description": "Degree of financial leverage and proportion of debt funding relative to equity.",
            "is_positive": val <= 2.0,
        })
    else:
        ratios.append({"name": "Debt to Equity", "value": "N/A", "numeric": None, "description": "Total Debt / Stockholder Equity", "is_positive": None})

    # 6. Return on Assets (ROA)
    if net_income is not None and total_assets and total_assets > 0:
        val = (net_income / total_assets) * 100.0
        ratios.append({
            "name": "Return on Assets (ROA)",
            "value": f"{val:.2f}%",
            "numeric": val,
            "description": "How efficiently company deploys its total asset base to generate earnings.",
            "is_positive": val >= 5.0,
        })
    else:
        ratios.append({"name": "Return on Assets (ROA)", "value": "N/A", "numeric": None, "description": "Net Income / Total Assets", "is_positive": None})

    # 7. Return on Equity (ROE)
    if net_income is not None and equity and equity > 0:
        val = (net_income / equity) * 100.0
        ratios.append({
            "name": "Return on Equity (ROE)",
            "value": f"{val:.2f}%",
            "numeric": val,
            "description": "Return generated on shareholder capital investment.",
            "is_positive": val >= 10.0,
        })
    else:
        ratios.append({"name": "Return on Equity (ROE)", "value": "N/A", "numeric": None, "description": "Net Income / Stockholder Equity", "is_positive": None})

    return ratios
