"""Unit tests for the Portfolio Service and Weighted-Average Cost Basis Engine.

Tests portfolio lifecycle, buy/sell transactions, cost basis tracking, partial sales,
realized and unrealized P/L, overselling guards, fee accounting, and SQLite persistence.
"""

import os
import tempfile
import unittest

from src.services.portfolio_service import (
    add_transaction,
    calculate_holdings_and_performance,
    create_portfolio,
    delete_portfolio,
    delete_transaction,
    get_portfolio,
    get_transactions,
    init_db,
    list_portfolios,
)


class TestPortfolioService(unittest.TestCase):
    def setUp(self):
        """Create a temporary SQLite database for each test to ensure test isolation."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_portfolio.db")
        init_db(self.db_path)

    def tearDown(self):
        """Clean up temporary test directory."""
        self.temp_dir.cleanup()

    def test_portfolio_lifecycle(self):
        """Test portfolio creation, retrieval, and deletion."""
        port_id = create_portfolio("Retirement Fund", "Long-term index and blue chip portfolio", db_path=self.db_path)
        self.assertIsInstance(port_id, int)

        port = get_portfolio(port_id, db_path=self.db_path)
        self.assertIsNotNone(port)
        self.assertEqual(port["name"], "Retirement Fund")

        # Duplicate name should raise ValueError
        with self.assertRaises(ValueError):
            create_portfolio("Retirement Fund", db_path=self.db_path)

        # Empty name should raise ValueError
        with self.assertRaises(ValueError):
            create_portfolio("   ", db_path=self.db_path)

        # Deletion
        deleted = delete_portfolio(port_id, db_path=self.db_path)
        self.assertTrue(deleted)
        self.assertIsNone(get_portfolio(port_id, db_path=self.db_path))

    def test_transaction_input_validation(self):
        """Test input validation for invalid tickers, quantities, prices, and fees."""
        port_id = create_portfolio("Alpha Portfolio", db_path=self.db_path)

        # Invalid ticker
        with self.assertRaises(ValueError):
            add_transaction(port_id, "", "BUY", 10, 150.0, db_path=self.db_path)

        # Invalid type
        with self.assertRaises(ValueError):
            add_transaction(port_id, "AAPL", "INVALID", 10, 150.0, db_path=self.db_path)

        # Zero or negative quantity
        with self.assertRaises(ValueError):
            add_transaction(port_id, "AAPL", "BUY", 0, 150.0, db_path=self.db_path)
        with self.assertRaises(ValueError):
            add_transaction(port_id, "AAPL", "BUY", -5, 150.0, db_path=self.db_path)

        # Zero or negative price
        with self.assertRaises(ValueError):
            add_transaction(port_id, "AAPL", "BUY", 10, 0, db_path=self.db_path)
        with self.assertRaises(ValueError):
            add_transaction(port_id, "AAPL", "BUY", 10, -100.0, db_path=self.db_path)

        # Negative fees
        with self.assertRaises(ValueError):
            add_transaction(port_id, "AAPL", "BUY", 10, 150.0, fees=-5.0, db_path=self.db_path)

    def test_overselling_prevention(self):
        """Test that selling more shares than currently held is strictly rejected."""
        port_id = create_portfolio("Beta Portfolio", db_path=self.db_path)

        # Selling without owning any shares
        with self.assertRaises(ValueError) as ctx:
            add_transaction(port_id, "NVDA", "SELL", 5, 120.0, db_path=self.db_path)
        self.assertIn("Cannot sell", str(ctx.exception))

        # Buy 10 shares
        add_transaction(port_id, "NVDA", "BUY", 10, 100.0, db_path=self.db_path)

        # Try selling 15 shares (more than 10 held)
        with self.assertRaises(ValueError) as ctx:
            add_transaction(port_id, "NVDA", "SELL", 15, 120.0, db_path=self.db_path)
        self.assertIn("Currently held: 10.0000", str(ctx.exception))

        # Successfully sell exact 10 shares
        tx_id = add_transaction(port_id, "NVDA", "SELL", 10, 120.0, db_path=self.db_path)
        self.assertIsInstance(tx_id, int)

        # Now held shares is 0, trying to sell 1 share should fail
        with self.assertRaises(ValueError):
            add_transaction(port_id, "NVDA", "SELL", 1, 120.0, db_path=self.db_path)

    def test_weighted_average_cost_and_realized_pl(self):
        """Validate accurate weighted-average cost basis and partial sale P/L."""
        port_id = create_portfolio("Value Portfolio", db_path=self.db_path)

        # 1. Buy 10 AAPL @ $150, fee = $5 -> Total cost = $1,505, avg = $150.50
        add_transaction(
            port_id, "AAPL", "BUY", 10, 150.0, fees=5.0, transaction_date="2026-01-10", db_path=self.db_path
        )

        # 2. Buy 10 AAPL @ $170, fee = $5 -> Total cost = $1505 + $1705 = $3210, 20 shares, avg = $160.50
        add_transaction(
            port_id, "AAPL", "BUY", 10, 170.0, fees=5.0, transaction_date="2026-02-15", db_path=self.db_path
        )

        # 3. Sell 5 AAPL @ $180, fee = $2
        # Cost of sold = 5 * $160.50 = $802.50
        # Proceeds = (5 * 180) - 2 = $898.00
        # Realized P/L = $898.00 - $802.50 = +$95.50
        # Remaining shares = 15
        # Remaining cost basis = $3210 - $802.50 = $2407.50
        add_transaction(
            port_id, "AAPL", "SELL", 5, 180.0, fees=2.0, transaction_date="2026-03-20", db_path=self.db_path
        )

        # Current price = $200.00
        # Current value = 15 * 200 = $3000.00
        # Unrealized P/L = $3000.00 - $2407.50 = +$592.50
        # Return % = ($592.50 / $2407.50) * 100 = 24.61%
        perf = calculate_holdings_and_performance(
            port_id, current_prices={"AAPL": 200.0}, db_path=self.db_path
        )

        self.assertEqual(perf["holdings_count"], 1)
        h = perf["holdings"][0]
        self.assertEqual(h["ticker"], "AAPL")
        self.assertEqual(h["quantity"], 15.0)
        self.assertEqual(h["average_cost"], 160.50)
        self.assertEqual(h["invested_value"], 2407.50)
        self.assertEqual(h["current_price"], 200.0)
        self.assertEqual(h["current_value"], 3000.00)
        self.assertEqual(h["unrealized_pl"], 592.50)
        self.assertAlmostEqual(h["return_pct"], 24.61, places=1)
        self.assertEqual(h["realized_pl"], 95.50)

        # Portfolio aggregate
        self.assertEqual(perf["total_invested_capital"], 2407.50)
        self.assertEqual(perf["current_portfolio_value"], 3000.00)
        self.assertEqual(perf["unrealized_pl"], 592.50)
        self.assertEqual(perf["realized_pl"], 95.50)

    def test_sqlite_persistence_across_connections(self):
        """Test that data safely persists across new database connections."""
        port_id = create_portfolio("Persistence Test", db_path=self.db_path)
        add_transaction(port_id, "MSFT", "BUY", 25, 400.0, fees=0.0, db_path=self.db_path)

        # Query using a distinct fresh connection
        txs = get_transactions(port_id, db_path=self.db_path)
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]["ticker"], "MSFT")
        self.assertEqual(txs[0]["quantity"], 25.0)

        # Delete transaction
        deleted = delete_transaction(txs[0]["id"], db_path=self.db_path)
        self.assertTrue(deleted)
        self.assertEqual(len(get_transactions(port_id, db_path=self.db_path)), 0)

    def test_missing_current_price_handling(self):
        """Test that missing current price yields None/N/A rather than zero."""
        port_id = create_portfolio("Unpriced Portfolio", db_path=self.db_path)
        add_transaction(port_id, "AAPL", "BUY", 10, 150.0, db_path=self.db_path)

        # Explicitly pass None for current price
        perf = calculate_holdings_and_performance(
            port_id, current_prices={"AAPL": None}, db_path=self.db_path
        )

        h = perf["holdings"][0]
        self.assertIsNone(h["current_price"])
        self.assertIsNone(h["current_value"])
        self.assertIsNone(h["unrealized_pl"])
        self.assertIsNone(h["return_pct"])
        self.assertFalse(perf["all_priced"])
        self.assertEqual(perf["unpriced_count"], 1)


if __name__ == "__main__":
    unittest.main()
