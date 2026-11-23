"""Unit tests for the Stock Comparison Service.

Tests ticker validation, normalized relative performance calculation (Base 100),
missing data handling, fundamental metric alignment, technical indicators extraction,
and cross-sectional benchmark summary generation with mocked data.
"""

from unittest.mock import patch
import unittest
import numpy as np
import pandas as pd

from src.services.comparison_service import (
    fetch_comparison_fundamentals,
    fetch_comparison_performance,
    fetch_comparison_technicals,
    generate_comparison_summary,
    validate_comparison_tickers,
)


class TestComparisonService(unittest.TestCase):
    def test_validate_comparison_tickers(self):
        """Test sanitization, deduplication, and bounds checking (2 to 6 stocks)."""
        # Valid 2 to 3 tickers
        clean, err = validate_comparison_tickers(["aapl", "  msft  ", "nvda"])
        self.assertEqual(clean, ["AAPL", "MSFT", "NVDA"])
        self.assertIsNone(err)

        # Deduplication
        clean, err = validate_comparison_tickers(["AAPL", "aapl", "MSFT", "msft"])
        self.assertEqual(clean, ["AAPL", "MSFT"])
        self.assertIsNone(err)

        # Truncate to maximum 6
        clean, err = validate_comparison_tickers(["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA", "META"])
        self.assertEqual(len(clean), 6)
        self.assertEqual(clean, ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA"])
        self.assertIsNone(err)

        # Insufficient tickers (< 2)
        clean, err = validate_comparison_tickers(["AAPL"])
        self.assertIsNotNone(err)
        self.assertIn("at least 2 distinct", err)

        clean, err = validate_comparison_tickers(["", "   ", "TOOLONGTICKER"])
        self.assertIsNotNone(err)

    @patch("src.services.comparison_service.fetch_stock_history")
    def test_normalized_performance_calculation(self, mock_history):
        """Test Base 100 indexing and relative return calculations."""
        # Create synthetic price series
        dates = pd.date_range("2026-01-01", periods=3, freq="D")
        df_aapl = pd.DataFrame({"Close": [100.0, 110.0, 120.0]}, index=dates)
        df_msft = pd.DataFrame({"Close": [200.0, 190.0, 180.0]}, index=dates)

        def side_effect(ticker, period=None, interval=None):
            if ticker == "AAPL":
                return df_aapl
            elif ticker == "MSFT":
                return df_msft
            return pd.DataFrame()

        mock_history.side_effect = side_effect

        perf = fetch_comparison_performance(["AAPL", "MSFT"], timeframe="1M")
        self.assertNotIn("error", perf)
        self.assertIn("AAPL", perf["chart_series"])
        self.assertIn("MSFT", perf["chart_series"])

        aapl_series = perf["chart_series"]["AAPL"]
        msft_series = perf["chart_series"]["MSFT"]

        # Base 100 normalization:
        # AAPL: 100/100*100 = 100.0, 110/100*100 = 110.0, 120/100*100 = 120.0 (+20%)
        # MSFT: 200/200*100 = 100.0, 190/200*100 = 95.0, 180/200*100 = 90.0 (-10%)
        self.assertEqual(aapl_series["values"], [100.0, 110.0, 120.0])
        self.assertEqual(msft_series["values"], [100.0, 95.0, 90.0])
        self.assertEqual(aapl_series["return_pct"], 20.0)
        self.assertEqual(msft_series["return_pct"], -10.0)

        # Leaders
        self.assertEqual(perf["best_performer"]["ticker"], "AAPL")
        self.assertEqual(perf["best_performer"]["return_pct"], 20.0)
        self.assertEqual(perf["worst_performer"]["ticker"], "MSFT")
        self.assertEqual(perf["worst_performer"]["return_pct"], -10.0)

    @patch("src.services.comparison_service.fetch_stock_history")
    def test_missing_or_empty_historical_data(self, mock_history):
        """Test graceful handling when one or more stocks have missing historical data."""
        dates = pd.date_range("2026-01-01", periods=3, freq="D")
        mock_history.side_effect = lambda t, **kwargs: (
            pd.DataFrame({"Close": [100.0, 105.0, 110.0]}, index=dates)
            if t == "AAPL"
            else pd.DataFrame()
        )

        perf = fetch_comparison_performance(["AAPL", "BADTICKER"], timeframe="1M")
        self.assertIn("error", perf)
        self.assertIn("Insufficient historical data", perf["error"])

    @patch("src.services.comparison_service.fetch_stock_info")
    def test_comparison_fundamentals_missing_values(self, mock_info):
        """Test fundamental metric alignment and preservation of None (no zero substitution)."""
        mock_info.side_effect = lambda t: {
            "shortName": f"{t} Inc",
            "marketCap": 2500000000000 if t == "AAPL" else 1800000000000,
            "trailingPE": 32.5 if t == "AAPL" else None,  # Missing P/E
            "dividendYield": 0.0055 if t == "AAPL" else None,
            "currency": "USD",
        }

        funds = fetch_comparison_fundamentals(["AAPL", "NVDA"])
        self.assertEqual(len(funds), 2)

        aapl = next(f for f in funds if f["ticker"] == "AAPL")
        nvda = next(f for f in funds if f["ticker"] == "NVDA")

        self.assertEqual(aapl["pe_ratio"], 32.5)
        self.assertIsNone(nvda["pe_ratio"])  # Must be None, not 0
        self.assertEqual(aapl["dividend_yield"], 0.55)
        self.assertIsNone(nvda["dividend_yield"])

    @patch("src.services.comparison_service.fetch_stock_history")
    def test_comparison_technicals_computation(self, mock_history):
        """Test technical comparison calculation across tickers."""
        dates = pd.date_range("2025-01-01", periods=200, freq="D")
        prices = np.linspace(100, 150, 200)
        df = pd.DataFrame(
            {
                "Open": prices,
                "High": prices + 1.0,
                "Low": prices - 1.0,
                "Close": prices,
                "Volume": [1000000] * 200,
            },
            index=dates,
        )
        mock_history.return_value = df

        techs = fetch_comparison_technicals(["AAPL", "MSFT"])
        self.assertEqual(len(techs), 2)
        for t in techs:
            self.assertTrue(t["has_data"])
            self.assertIsNotNone(t["rsi"])
            self.assertIsNotNone(t["sma50"])
            self.assertIsNotNone(t["annualized_volatility"])

    def test_generate_comparison_summary(self):
        """Test summary leader derivation."""
        perf_data = {
            "best_performer": {"ticker": "NVDA", "return_pct": 145.2},
            "worst_performer": {"ticker": "MSFT", "return_pct": 12.5},
        }

        fundamentals = [
            {"ticker": "AAPL", "pe_ratio": 30.2, "market_cap": 3.2e12, "market_cap_formatted": "$3.20T", "roe": 140.0},
            {"ticker": "MSFT", "pe_ratio": 35.1, "market_cap": 3.0e12, "market_cap_formatted": "$3.00T", "roe": 38.5},
            {"ticker": "NVDA", "pe_ratio": 45.0, "market_cap": 2.8e12, "market_cap_formatted": "$2.80T", "roe": 95.0},
        ]

        technicals = [
            {"ticker": "AAPL", "annualized_volatility": 18.5},
            {"ticker": "MSFT", "annualized_volatility": 16.2},
            {"ticker": "NVDA", "annualized_volatility": 42.1},
        ]

        summary = generate_comparison_summary(perf_data, fundamentals, technicals)

        self.assertIn("NVDA", summary["best_performer"])
        self.assertIn("AAPL", summary["lowest_pe"])  # 30.2x is lowest
        self.assertIn("AAPL", summary["highest_mcap"])  # $3.20T is highest
        self.assertIn("AAPL", summary["highest_roe"])  # 140% is highest
        self.assertIn("MSFT", summary["lowest_volatility"])  # 16.2% is lowest


if __name__ == "__main__":
    unittest.main()
