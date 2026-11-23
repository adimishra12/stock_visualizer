"""Unit tests for the Technical Indicator Engine.

Deterministic tests using synthetic OHLCV data.
Does not depend on external APIs or network calls.
"""

import unittest
import numpy as np
import pandas as pd

from src.services.indicators import (
    calculate_all_indicators,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    calculate_vwap,
)


class TestIndicators(unittest.TestCase):
    def setUp(self):
        """Generate deterministic synthetic daily OHLCV series."""
        np.random.seed(42)
        n = 100
        dates = pd.date_range("2026-01-01", periods=n, freq="D")
        close_prices = 100.0 + np.cumsum(np.random.normal(0.2, 1.5, n))
        high_prices = close_prices + np.random.uniform(0.5, 2.0, n)
        low_prices = close_prices - np.random.uniform(0.5, 2.0, n)
        open_prices = low_prices + (high_prices - low_prices) * 0.5
        volumes = np.random.randint(10000, 50000, n).astype(float)

        self.df = pd.DataFrame(
            {
                "Open": open_prices,
                "High": high_prices,
                "Low": low_prices,
                "Close": close_prices,
                "Volume": volumes,
            },
            index=dates,
        )

    def test_sma_calculation(self):
        """Test Simple Moving Average calculation and edge cases."""
        sma20 = calculate_sma(self.df["Close"], window=20)
        self.assertEqual(len(sma20), len(self.df))
        self.assertTrue(np.isnan(sma20.iloc[18]))
        self.assertFalse(np.isnan(sma20.iloc[19]))

        # Mathematical check: average of first 20 close values
        expected_first = self.df["Close"].iloc[:20].mean()
        self.assertAlmostEqual(sma20.iloc[19], expected_first, places=5)

        # Invalid window
        with self.assertRaises(ValueError):
            calculate_sma(self.df["Close"], window=0)

    def test_ema_calculation(self):
        """Test Exponential Moving Average calculation."""
        ema9 = calculate_ema(self.df["Close"], span=9)
        self.assertEqual(len(ema9), len(self.df))
        self.assertTrue(np.isnan(ema9.iloc[7]))
        self.assertFalse(np.isnan(ema9.iloc[8]))

        # Value should track close prices closely
        self.assertGreater(ema9.iloc[-1], 0)

        with self.assertRaises(ValueError):
            calculate_ema(self.df["Close"], span=-1)

    def test_rsi_wilders_smoothing(self):
        """Test RSI calculation with Welles Wilder's smoothing RMA."""
        rsi = calculate_rsi(self.df["Close"], period=14)
        self.assertEqual(len(rsi), len(self.df))

        # First 14 bars must be NaN
        self.assertTrue(np.isnan(rsi.iloc[13]))
        self.assertFalse(np.isnan(rsi.iloc[14]))

        # RSI must be strictly bounded between 0 and 100
        valid_rsi = rsi.dropna()
        self.assertTrue((valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all())

        # Test pure gain sequence (must equal 100.0)
        pure_gain = pd.Series([10.0 + i for i in range(30)])
        rsi_gain = calculate_rsi(pure_gain, period=14)
        self.assertAlmostEqual(rsi_gain.iloc[-1], 100.0, places=3)

        # Test pure loss sequence (must equal 0.0)
        pure_loss = pd.Series([100.0 - i for i in range(30)])
        rsi_loss = calculate_rsi(pure_loss, period=14)
        self.assertAlmostEqual(rsi_loss.iloc[-1], 0.0, places=3)

        # Test flat sequence (no change -> 50.0)
        flat = pd.Series([50.0] * 30)
        rsi_flat = calculate_rsi(flat, period=14)
        self.assertAlmostEqual(rsi_flat.iloc[-1], 50.0, places=3)

    def test_macd_calculation(self):
        """Test MACD, Signal line, and Histogram properties."""
        macd, signal, hist = calculate_macd(self.df["Close"], fast_period=12, slow_period=26, signal_period=9)

        self.assertEqual(len(macd), len(self.df))
        self.assertEqual(len(signal), len(self.df))
        self.assertEqual(len(hist), len(self.df))

        # Histogram must strictly equal macd - signal
        diff = (macd - signal).dropna()
        hist_valid = hist.dropna()
        np.testing.assert_allclose(diff, hist_valid, rtol=1e-5)

        with self.assertRaises(ValueError):
            calculate_macd(self.df["Close"], fast_period=26, slow_period=12)

    def test_bollinger_bands(self):
        """Test Bollinger Bands upper, middle, and lower bands."""
        upper, middle, lower = calculate_bollinger_bands(self.df["Close"], window=20, num_std=2.0)

        # Middle band should equal SMA 20
        sma20 = calculate_sma(self.df["Close"], window=20)
        np.testing.assert_allclose(middle.dropna(), sma20.dropna(), rtol=1e-5)

        # Upper > Middle > Lower at all times
        valid_idx = upper.dropna().index
        self.assertTrue((upper.loc[valid_idx] >= middle.loc[valid_idx]).all())
        self.assertTrue((middle.loc[valid_idx] >= lower.loc[valid_idx]).all())

        # Bandwidth symmetry
        bandwidth_up = upper.loc[valid_idx] - middle.loc[valid_idx]
        bandwidth_down = middle.loc[valid_idx] - lower.loc[valid_idx]
        np.testing.assert_allclose(bandwidth_up, bandwidth_down, rtol=1e-5)

    def test_vwap_calculation(self):
        """Test VWAP with typical price and zero-volume handling."""
        vwap = calculate_vwap(self.df)
        self.assertEqual(len(vwap), len(self.df))
        self.assertFalse(vwap.isna().any())

        # Test zero volume fallback
        zero_vol_df = self.df.copy()
        zero_vol_df["Volume"] = 0.0
        vwap_zero = calculate_vwap(zero_vol_df)
        expected_tp = (zero_vol_df["High"] + zero_vol_df["Low"] + zero_vol_df["Close"]) / 3.0
        np.testing.assert_allclose(vwap_zero, expected_tp, rtol=1e-5)

    def test_atr_calculation(self):
        """Test Average True Range calculation with Wilder's smoothing."""
        atr = calculate_atr(self.df, period=14)
        self.assertEqual(len(atr), len(self.df))
        self.assertTrue(np.isnan(atr.iloc[13]))
        self.assertFalse(np.isnan(atr.iloc[14]))

        # ATR must be strictly positive
        valid_atr = atr.dropna()
        self.assertTrue((valid_atr > 0.0).all())

    def test_calculate_all_indicators(self):
        """Test comprehensive indicator enrichment."""
        enriched = calculate_all_indicators(self.df)

        expected_columns = [
            "MA20", "MA50", "MA200",
            "EMA9", "EMA21", "EMA50",
            "RSI",
            "MACD", "Signal_Line", "MACD_Histogram",
            "BB_Upper", "BB_Middle", "BB_Lower",
            "VWAP", "ATR",
        ]
        for col in expected_columns:
            self.assertIn(col, enriched.columns)

        # Source DataFrame must not have been mutated
        self.assertNotIn("RSI", self.df.columns)

    def test_empty_and_insufficient_data(self):
        """Test robustness on empty and edge-case inputs."""
        empty_df = pd.DataFrame()
        res_empty = calculate_all_indicators(empty_df)
        self.assertTrue(res_empty.empty)

        one_row_df = self.df.iloc[:1].copy()
        res_one = calculate_all_indicators(one_row_df)
        self.assertEqual(len(res_one), 1)


if __name__ == "__main__":
    unittest.main()
