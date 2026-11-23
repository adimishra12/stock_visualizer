"""Unit tests for the Market Data Service.

Validates ticker sanitization, timeframe validation, metric extraction,
and resilience against missing data without live network calls.
"""

import unittest
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from src.services.market_data import (
    get_stock_metrics,
    sanitize_ticker,
    validate_timeframe_interval,
)


class TestMarketDataService(unittest.TestCase):
    def test_sanitize_ticker(self):
        """Test ticker sanitization rules."""
        self.assertEqual(sanitize_ticker("aapl"), "AAPL")
        self.assertEqual(sanitize_ticker("  msft  "), "MSFT")
        self.assertEqual(sanitize_ticker("brk.b"), "BRK.B")
        self.assertEqual(sanitize_ticker("brk-b"), "BRK-B")
        self.assertEqual(sanitize_ticker("^gspc"), "^GSPC")
        self.assertEqual(sanitize_ticker("cl=f"), "CL=F")
        self.assertEqual(sanitize_ticker("btc-usd"), "BTC-USD")

        # Invalid symbols
        self.assertIsNone(sanitize_ticker(""))
        self.assertIsNone(sanitize_ticker("   "))
        self.assertIsNone(sanitize_ticker(None))
        self.assertIsNone(sanitize_ticker("TOOLONGTICKERNAME"))

    def test_validate_timeframe_interval(self):
        """Test timeframe and interval compatibility rules."""
        # Valid standard requests
        valid, err = validate_timeframe_interval(period="1d", interval="5m")
        self.assertTrue(valid)
        self.assertIsNone(err)

        valid, err = validate_timeframe_interval(period="1y", interval="1d")
        self.assertTrue(valid)
        self.assertIsNone(err)

        # Invalid 1m over 7 days
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        valid, err = validate_timeframe_interval(interval="1m", start_date=start, end_date=end)
        self.assertFalse(valid)
        self.assertIn("limited to 7 days", err)

        # Invalid start >= end
        valid, err = validate_timeframe_interval(start_date=end, end_date=start)
        self.assertFalse(valid)
        self.assertIn("before end date", err)

    def test_get_stock_metrics_pure_historical(self):
        """Test deriving metrics directly from historical price bars without stock.info."""
        dates = pd.date_range("2026-01-01", periods=10, freq="D")
        closes = [100.0, 102.0, 101.0, 105.0, 104.0, 108.0, 107.0, 110.0, 112.0, 115.0]
        highs = [c + 2.0 for c in closes]
        lows = [c - 2.0 for c in closes]
        vols = [10000.0] * 10

        df = pd.DataFrame(
            {"Open": closes, "High": highs, "Low": lows, "Close": closes, "Volume": vols},
            index=dates,
        )

        metrics = get_stock_metrics(df, info=None)

        self.assertAlmostEqual(metrics["current_price"], 115.0)
        self.assertAlmostEqual(metrics["previous_close"], 112.0)
        self.assertAlmostEqual(metrics["price_change"], 3.0)
        self.assertAlmostEqual(metrics["price_change_pct"], (3.0 / 112.0) * 100.0)
        self.assertAlmostEqual(metrics["day_high"], 117.0)
        self.assertAlmostEqual(metrics["day_low"], 113.0)
        self.assertAlmostEqual(metrics["volume"], 10000.0)
        self.assertAlmostEqual(metrics["fifty_two_week_high"], 117.0)
        self.assertAlmostEqual(metrics["fifty_two_week_low"], 98.0)

    def test_get_stock_metrics_enrichment(self):
        """Test optional enrichment from info."""
        dates = pd.date_range("2026-01-01", periods=2, freq="D")
        df = pd.DataFrame(
            {"Open": [100, 105], "High": [102, 107], "Low": [99, 104], "Close": [101, 106], "Volume": [1000, 1500]},
            index=dates,
        )
        info = {
            "marketCap": 2500000000000,
            "trailingPE": 28.5,
            "dividendYield": 0.015,
            "longName": "Apple Inc.",
            "sector": "Technology",
        }

        metrics = get_stock_metrics(df, info=info)
        self.assertEqual(metrics["market_cap"], 2500000000000)
        self.assertEqual(metrics["trailing_pe"], 28.5)
        self.assertEqual(metrics["company_name"], "Apple Inc.")
        self.assertEqual(metrics["sector"], "Technology")

    def test_empty_dataframe_metrics(self):
        """Test graceful return when DataFrame is empty."""
        metrics = get_stock_metrics(pd.DataFrame(), info=None)
        self.assertEqual(metrics, {})


if __name__ == "__main__":
    unittest.main()
