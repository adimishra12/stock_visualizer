"""Unit tests for UI rendering helpers and charts."""

import unittest
import numpy as np
import pandas as pd

from src.ui.charts import (
    create_atr_chart,
    create_macd_chart,
    create_price_chart,
    create_rsi_chart,
    create_sparkline_chart,
    get_chart_theme,
)
from src.ui.market_overview import format_overview_price


class TestUIComponents(unittest.TestCase):
    def setUp(self):
        dates = pd.date_range("2026-01-01", periods=30, freq="D")
        self.df = pd.DataFrame(
            {
                "Open": np.linspace(100, 130, 30),
                "High": np.linspace(102, 132, 30),
                "Low": np.linspace(98, 128, 30),
                "Close": np.linspace(101, 131, 30),
                "Volume": [10000.0] * 30,
                "MA20": np.linspace(100, 125, 30),
                "MA50": np.linspace(95, 120, 30),
                "MA200": np.linspace(90, 115, 30),
                "EMA9": np.linspace(101, 130, 30),
                "EMA21": np.linspace(99, 127, 30),
                "VWAP": np.linspace(100, 130, 30),
                "BB_Upper": np.linspace(105, 135, 30),
                "BB_Middle": np.linspace(100, 125, 30),
                "BB_Lower": np.linspace(95, 115, 30),
                "RSI": [55.0] * 30,
                "MACD": [1.2] * 30,
                "Signal_Line": [1.0] * 30,
                "MACD_Histogram": [0.2] * 30,
                "ATR": [2.5] * 30,
            },
            index=dates,
        )

    def test_chart_theme_tokens(self):
        for theme_name in ["light", "dark"]:
            ct = get_chart_theme(theme_name)
            self.assertIn("up_color", ct)
            self.assertIn("down_color", ct)
            self.assertIn("font_color", ct)

    def test_price_chart_candlestick_and_line(self):
        for theme in ["light", "dark"]:
            fig_candle = create_price_chart(
                self.df,
                "TEST",
                chart_type="candlestick",
                show_ma20=True,
                show_ma50=True,
                show_ma200=True,
                show_ema9=True,
                show_ema21=True,
                show_bb=True,
                show_vwap=True,
                theme_name=theme,
            )
            self.assertIsNotNone(fig_candle)
            # Traces: Candle (1) + MA20 (1) + MA50 (1) + MA200 (1) + EMA9 (1) + EMA21 (1) + VWAP (1) + BB Upper/Lower (2) + Vol (1) = 10
            self.assertEqual(len(fig_candle.data), 10)

            fig_line = create_price_chart(
                self.df, "TEST", chart_type="line", show_vwap=False, theme_name=theme
            )
            self.assertIsNotNone(fig_line)
            self.assertEqual(fig_line.data[0].type, "scatter")

    def test_sparkline_chart(self):
        series = [100.0, 102.0, 105.0, 104.0, 108.0]
        for theme in ["light", "dark"]:
            fig_pos = create_sparkline_chart(series, is_positive=True, theme_name=theme)
            self.assertIsNotNone(fig_pos)
            fig_neg = create_sparkline_chart(series, is_positive=False, theme_name=theme)
            self.assertIsNotNone(fig_neg)

    def test_atr_and_oscillators(self):
        for theme in ["light", "dark"]:
            fig_atr = create_atr_chart(self.df, theme_name=theme)
            self.assertIsNotNone(fig_atr)
            fig_rsi = create_rsi_chart(self.df, theme_name=theme)
            self.assertIsNotNone(fig_rsi)
            fig_macd = create_macd_chart(self.df, theme_name=theme)
            self.assertIsNotNone(fig_macd)

    def test_format_overview_price(self):
        self.assertEqual(format_overview_price("^TNX", 4.321), "4.321%")
        self.assertEqual(format_overview_price("AAPL", 225.5), "$225.50")
        self.assertEqual(format_overview_price("BTC-USD", 95123.456), "$95,123.46")

    def test_portfolio_and_comparison_charts(self):
        from src.ui.portfolio_tracker import (
            _create_allocation_chart,
            _create_holding_pl_chart,
            _create_invested_vs_current_chart,
        )
        from src.ui.stock_comparison import _create_normalized_performance_chart

        holdings = [
            {"ticker": "AAPL", "invested_value": 1500.0, "current_value": 1800.0, "unrealized_pl": 300.0},
            {"ticker": "NVDA", "invested_value": 2000.0, "current_value": 2600.0, "unrealized_pl": 600.0},
        ]
        for theme in ["light", "dark"]:
            fig_alloc = _create_allocation_chart(holdings, theme_name=theme)
            self.assertIsNotNone(fig_alloc)
            fig_inv = _create_invested_vs_current_chart(holdings, theme_name=theme)
            self.assertIsNotNone(fig_inv)
            fig_pl = _create_holding_pl_chart(holdings, theme_name=theme)
            self.assertIsNotNone(fig_pl)

            perf_data = {
                "timeframe": "1Y",
                "chart_series": {
                    "AAPL": {"dates": ["2026-01-01", "2026-01-02"], "values": [100.0, 110.0], "return_pct": 10.0},
                    "NVDA": {"dates": ["2026-01-01", "2026-01-02"], "values": [100.0, 125.0], "return_pct": 25.0},
                },
            }
            fig_norm = _create_normalized_performance_chart(perf_data, theme_name=theme)
            self.assertIsNotNone(fig_norm)



if __name__ == "__main__":
    unittest.main()
