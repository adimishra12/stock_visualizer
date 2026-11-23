"""Unit tests for the Financial Statements Service.

Validates currency formatting, standardized statement table synthesis,
metric series extraction, and financial ratio calculations with zero-division guards.
"""

import unittest
import numpy as np
import pandas as pd

from src.services.financial_service import (
    BALANCE_SHEET_METRICS,
    INCOME_STATEMENT_METRICS,
    build_standardized_statement,
    calculate_financial_ratios,
    extract_metric_series,
    format_currency_value,
)


class TestFinancialService(unittest.TestCase):
    def test_format_currency_value(self):
        """Test large number notation formatting with custom currency symbols."""
        self.assertEqual(format_currency_value(None), "-")
        self.assertEqual(format_currency_value(np.nan), "-")
        self.assertEqual(format_currency_value("invalid"), "-")
        self.assertEqual(format_currency_value(0), "$0.00")
        self.assertEqual(format_currency_value(1.234e12), "$1.23T")
        self.assertEqual(format_currency_value(3.85e9), "$3.85B")
        self.assertEqual(format_currency_value(-4.50e6), "-$4.50M")
        self.assertEqual(format_currency_value(75000), "$75.00K")
        self.assertEqual(format_currency_value(42.5), "$42.50")
        self.assertEqual(format_currency_value(1.5e9, currency_symbol="€"), "€1.50B")

    def test_build_standardized_statement_annual(self):
        """Test building standardized financial statements for annual periods."""
        cols = [pd.Timestamp("2023-12-31"), pd.Timestamp("2022-12-31")]
        data = {
            cols[0]: [1000000.0, 400000.0, 200000.0],
            cols[1]: [800000.0, 350000.0, 150000.0],
        }
        df = pd.DataFrame(data, index=["Operating Revenue", "Cost Of Revenue", "Net Income"])

        std_df = build_standardized_statement(df, INCOME_STATEMENT_METRICS, is_quarterly=False)

        # Columns should be formatted as FY YYYY in descending order
        self.assertEqual(list(std_df.columns), ["FY 2023", "FY 2022"])

        # 'Total Revenue' should match 'Operating Revenue' via alias map
        self.assertIn("Total Revenue", std_df.index)
        self.assertEqual(std_df.loc["Total Revenue", "FY 2023"], 1000000.0)
        self.assertEqual(std_df.loc["Total Revenue", "FY 2022"], 800000.0)

        # 'Cost of Revenue' should match
        self.assertEqual(std_df.loc["Cost of Revenue", "FY 2023"], 400000.0)

        # Unmatched metric should be NaN
        self.assertTrue(pd.isna(std_df.loc["EBITDA", "FY 2023"]))

    def test_build_standardized_statement_quarterly(self):
        """Test building standardized financial statements for quarterly periods."""
        cols = [pd.Timestamp("2023-09-30"), pd.Timestamp("2023-06-30")]
        data = {
            cols[0]: [500000.0],
            cols[1]: [450000.0],
        }
        df = pd.DataFrame(data, index=["Total Revenue"])

        std_df = build_standardized_statement(df, INCOME_STATEMENT_METRICS, is_quarterly=True)
        self.assertEqual(list(std_df.columns), ["2023-Q3", "2023-Q2"])
        self.assertEqual(std_df.loc["Total Revenue", "2023-Q3"], 500000.0)

    def test_extract_metric_series(self):
        """Test extracting chronological time series for Plotly charts."""
        cols = [pd.Timestamp("2023-12-31"), pd.Timestamp("2021-12-31"), pd.Timestamp("2022-12-31")]
        data = {
            cols[0]: 300.0,
            cols[1]: 100.0,
            cols[2]: 200.0,
        }
        df = pd.DataFrame([data], index=["Total Revenue"])

        labels, values = extract_metric_series(df, ["Total Revenue", "Operating Revenue"])

        # Must be chronological (oldest to newest)
        self.assertEqual(labels, ["2021-12", "2022-12", "2023-12"])
        self.assertEqual(values, [100.0, 200.0, 300.0])

        # Missing metric returns empty lists
        empty_lbl, empty_val = extract_metric_series(df, ["NonExistentMetric"])
        self.assertEqual(empty_lbl, [])
        self.assertEqual(empty_val, [])

    def test_calculate_financial_ratios_standard(self):
        """Test standard financial ratio calculations."""
        p_latest = pd.Timestamp("2023-12-31")
        p_prev = pd.Timestamp("2022-12-31")

        inc_df = pd.DataFrame(
            {
                p_latest: [1000.0, 600.0, 200.0, 150.0],
                p_prev: [800.0, 480.0, 160.0, 120.0],
            },
            index=["Total Revenue", "Gross Profit", "Operating Income", "Net Income"],
        )

        bal_df = pd.DataFrame(
            {
                p_latest: [2000.0, 800.0, 400.0, 400.0, 1000.0],
                p_prev: [1800.0, 700.0, 350.0, 300.0, 900.0],
            },
            index=[
                "Total Assets",
                "Current Assets",
                "Current Liabilities",
                "Total Debt",
                "Stockholders Equity",
            ],
        )

        ratios = calculate_financial_ratios(inc_df, bal_df, None)
        ratio_map = {r["name"]: r for r in ratios}

        self.assertEqual(len(ratios), 7)

        # Gross Margin = (600 / 1000) * 100 = 60.0%
        self.assertAlmostEqual(ratio_map["Gross Profit Margin"]["numeric"], 60.0)
        self.assertTrue(ratio_map["Gross Profit Margin"]["is_positive"])

        # Operating Margin = (200 / 1000) * 100 = 20.0%
        self.assertAlmostEqual(ratio_map["Operating Margin"]["numeric"], 20.0)
        self.assertTrue(ratio_map["Operating Margin"]["is_positive"])

        # Net Profit Margin = (150 / 1000) * 100 = 15.0%
        self.assertAlmostEqual(ratio_map["Net Profit Margin"]["numeric"], 15.0)

        # Current Ratio = 800 / 400 = 2.0x
        self.assertAlmostEqual(ratio_map["Current Ratio"]["numeric"], 2.0)
        self.assertTrue(ratio_map["Current Ratio"]["is_positive"])

        # Debt to Equity = 400 / 1000 = 0.4x
        self.assertAlmostEqual(ratio_map["Debt to Equity"]["numeric"], 0.4)
        self.assertTrue(ratio_map["Debt to Equity"]["is_positive"])

        # ROA = (150 / 2000) * 100 = 7.5%
        self.assertAlmostEqual(ratio_map["Return on Assets (ROA)"]["numeric"], 7.5)

        # ROE = (150 / 1000) * 100 = 15.0%
        self.assertAlmostEqual(ratio_map["Return on Equity (ROE)"]["numeric"], 15.0)

    def test_calculate_financial_ratios_division_by_zero_and_missing(self):
        """Test financial ratio calculations with zero or missing denominators."""
        p_latest = pd.Timestamp("2023-12-31")

        inc_zero = pd.DataFrame({p_latest: [0.0, 0.0, 0.0, 0.0]}, index=["Total Revenue", "Gross Profit", "Operating Income", "Net Income"])
        bal_zero = pd.DataFrame({p_latest: [0.0, 0.0, 0.0, 0.0, 0.0]}, index=["Total Assets", "Current Assets", "Current Liabilities", "Total Debt", "Stockholders Equity"])

        ratios = calculate_financial_ratios(inc_zero, bal_zero, None)
        for r in ratios:
            self.assertEqual(r["value"], "N/A")
            self.assertIsNone(r["numeric"])
            self.assertIsNone(r["is_positive"])

        # Empty inputs should not crash
        empty_ratios = calculate_financial_ratios(None, None, None)
        self.assertEqual(len(empty_ratios), 7)
        for r in empty_ratios:
            self.assertEqual(r["value"], "N/A")


if __name__ == "__main__":
    unittest.main()
