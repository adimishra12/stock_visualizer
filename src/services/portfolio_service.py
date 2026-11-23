"""Portfolio management service with persistent SQLite storage.

Provides portfolio creation, buy/sell transaction ledger, weighted-average cost-basis
calculation, realized and unrealized P/L derivation, and current valuation.
"""

from datetime import datetime, timezone
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from src.config import DEFAULT_DB_PATH
from src.services.market_data import get_stock_metrics, sanitize_ticker


def get_db_path(db_path: Optional[str] = None) -> str:
    """Resolve active SQLite database path."""
    resolved = db_path or os.environ.get("STOCK_PORTFOLIO_DB") or DEFAULT_DB_PATH
    dir_name = os.path.dirname(resolved)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    return resolved


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Obtain a SQLite connection with Row factory and foreign keys enabled."""
    path = get_db_path(db_path)
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the portfolio database schema and default portfolio if empty."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('BUY', 'SELL')),
                quantity REAL NOT NULL CHECK(quantity > 0),
                price_per_share REAL NOT NULL CHECK(price_per_share > 0),
                fees REAL NOT NULL DEFAULT 0.0 CHECK(fees >= 0),
                transaction_date TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
            );
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_portfolio ON transactions(portfolio_id);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_ticker ON transactions(ticker);"
        )

        # Seed default portfolio if no portfolios exist
        cursor.execute("SELECT COUNT(*) FROM portfolios;")
        if cursor.fetchone()[0] == 0:
            now_str = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                "INSERT INTO portfolios (name, description, created_at) VALUES (?, ?, ?);",
                ("Core Growth Portfolio", "Primary investment holdings and core assets", now_str),
            )
        conn.commit()


# -----------------------------------------------------------------------------
# Portfolio Management
# -----------------------------------------------------------------------------

def list_portfolios(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all available portfolios."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, created_at FROM portfolios ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_portfolio(portfolio_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve details for a single portfolio by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, created_at FROM portfolios WHERE id = ?;",
            (portfolio_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def create_portfolio(name: str, description: str = "", db_path: Optional[str] = None) -> int:
    """Create a new portfolio with unique name."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Portfolio name cannot be empty.")

    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        now_str = datetime.now(timezone.utc).isoformat()
        try:
            cursor.execute(
                "INSERT INTO portfolios (name, description, created_at) VALUES (?, ?, ?);",
                (clean_name, description.strip(), now_str),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"A portfolio named '{clean_name}' already exists.")


def delete_portfolio(portfolio_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a portfolio and all associated transactions."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolios WHERE id = ?;", (portfolio_id,))
        conn.commit()
        return cursor.rowcount > 0


# -----------------------------------------------------------------------------
# Transaction Ledger
# -----------------------------------------------------------------------------

def add_transaction(
    portfolio_id: int,
    ticker: str,
    transaction_type: str,
    quantity: float,
    price_per_share: float,
    fees: float = 0.0,
    transaction_date: Optional[str] = None,
    notes: str = "",
    db_path: Optional[str] = None,
) -> int:
    """Add a validated BUY or SELL transaction to the ledger.

    Enforces weighted-average cost basis invariants and prevents overselling.
    """
    clean_ticker = sanitize_ticker(ticker)
    if not clean_ticker:
        raise ValueError(f"Invalid stock ticker: '{ticker}'")

    clean_type = transaction_type.upper().strip()
    if clean_type not in ("BUY", "SELL"):
        raise ValueError(f"Transaction type must be 'BUY' or 'SELL', got '{transaction_type}'")

    try:
        qty = float(quantity)
        price = float(price_per_share)
        fee = float(fees)
    except (ValueError, TypeError):
        raise ValueError("Quantity, price, and fees must be numeric.")

    if qty <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if price <= 0:
        raise ValueError("Price per share must be greater than zero.")
    if fee < 0:
        raise ValueError("Fees cannot be negative.")

    if not transaction_date or not transaction_date.strip():
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = transaction_date.strip()

    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Verify portfolio exists
        cursor.execute("SELECT id FROM portfolios WHERE id = ?;", (portfolio_id,))
        if not cursor.fetchone():
            raise ValueError(f"Portfolio ID {portfolio_id} does not exist.")

        # If SELL transaction, enforce non-overselling constraint
        if clean_type == "SELL":
            cursor.execute(
                """
                SELECT transaction_type, quantity
                FROM transactions
                WHERE portfolio_id = ? AND ticker = ?
                ORDER BY transaction_date ASC, id ASC;
                """,
                (portfolio_id, clean_ticker),
            )
            txs = cursor.fetchall()
            held = sum(
                r["quantity"] if r["transaction_type"] == "BUY" else -r["quantity"]
                for r in txs
            )
            # Floating point tolerance
            if qty > (held + 1e-9):
                raise ValueError(
                    f"Cannot sell {qty:.4f} shares of {clean_ticker}. Currently held: {held:.4f} shares."
                )

        now_str = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT INTO transactions (
                portfolio_id, ticker, transaction_type, quantity,
                price_per_share, fees, transaction_date, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                portfolio_id,
                clean_ticker,
                clean_type,
                qty,
                price,
                fee,
                date_str,
                notes.strip(),
                now_str,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def delete_transaction(transaction_id: int, db_path: Optional[str] = None) -> bool:
    """Delete a transaction by ID."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?;", (transaction_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_transactions(portfolio_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all transactions for a portfolio ordered chronologically."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, portfolio_id, ticker, transaction_type, quantity,
                   price_per_share, fees, transaction_date, notes, created_at
            FROM transactions
            WHERE portfolio_id = ?
            ORDER BY transaction_date DESC, id DESC;
            """,
            (portfolio_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# -----------------------------------------------------------------------------
# Portfolio Calculation Engine (Weighted-Average Cost Basis)
# -----------------------------------------------------------------------------

def calculate_holdings_and_performance(
    portfolio_id: int,
    current_prices: Optional[Dict[str, Optional[float]]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate positions, cost basis, realized and unrealized P/L for a portfolio.

    Methodology:
    - Weighted-Average Cost Basis:
        * BUY: Total Cost = Prev Cost + (Qty * Price) + Fees
               Avg Cost = Total Cost / Held Shares
        * SELL: Realized Gain = (Qty * Sell Price - Fees) - (Qty * Avg Cost)
                Remaining Cost = Prev Cost - (Qty * Avg Cost)
                Held Shares = Prev Shares - Qty
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        # Retrieve all transactions chronologically (oldest first)
        cursor.execute(
            """
            SELECT id, ticker, transaction_type, quantity, price_per_share,
                   fees, transaction_date, notes
            FROM transactions
            WHERE portfolio_id = ?
            ORDER BY transaction_date ASC, id ASC;
            """,
            (portfolio_id,),
        )
        transactions = [dict(r) for r in cursor.fetchall()]

    # State tracking per ticker
    positions: Dict[str, Dict[str, Any]] = {}

    for tx in transactions:
        t = tx["ticker"]
        if t not in positions:
            positions[t] = {
                "ticker": t,
                "held_shares": 0.0,
                "invested_cost": 0.0,  # Remaining cost basis
                "realized_pl": 0.0,
                "total_bought_shares": 0.0,
                "total_bought_cost": 0.0,
                "total_sold_shares": 0.0,
                "total_sold_proceeds": 0.0,
                "total_fees": 0.0,
                "last_tx_date": tx["transaction_date"],
            }

        pos = positions[t]
        pos["last_tx_date"] = tx["transaction_date"]
        tx_type = tx["transaction_type"]
        qty = tx["quantity"]
        price = tx["price_per_share"]
        fee = tx["fees"]
        pos["total_fees"] += fee

        if tx_type == "BUY":
            cost_addition = (qty * price) + fee
            pos["held_shares"] += qty
            pos["invested_cost"] += cost_addition
            pos["total_bought_shares"] += qty
            pos["total_bought_cost"] += cost_addition

        elif tx_type == "SELL":
            # Current average cost per share
            if pos["held_shares"] > 1e-9:
                avg_cost = pos["invested_cost"] / pos["held_shares"]
            else:
                avg_cost = 0.0

            cost_of_sold = qty * avg_cost
            proceeds = (qty * price) - fee
            realized_pl_tx = proceeds - cost_of_sold

            pos["realized_pl"] += realized_pl_tx
            pos["held_shares"] -= qty
            pos["invested_cost"] = max(0.0, pos["invested_cost"] - cost_of_sold)

            # Floating point zero guard
            if pos["held_shares"] <= 1e-9:
                pos["held_shares"] = 0.0
                pos["invested_cost"] = 0.0

            pos["total_sold_shares"] += qty
            pos["total_sold_proceeds"] += proceeds

    # Fetch live quotes for active positions if current_prices not provided
    active_tickers = [t for t, p in positions.items() if p["held_shares"] > 1e-9]

    resolved_prices: Dict[str, Optional[float]] = {}
    if current_prices is not None:
        resolved_prices = dict(current_prices)
    else:
        for t in active_tickers:
            try:
                metrics = get_stock_metrics(t)
                resolved_prices[t] = metrics.get("current_price")
            except Exception:
                resolved_prices[t] = None

    # Compile holdings list
    holdings: List[Dict[str, Any]] = []
    total_invested_capital = 0.0
    total_current_value = 0.0
    total_realized_pl = sum(p["realized_pl"] for p in positions.values())
    all_priced = True
    unpriced_count = 0

    for t, p in positions.items():
        held = p["held_shares"]
        if held <= 1e-9:
            continue  # Fully closed position

        inv_cost = p["invested_cost"]
        avg_cost = inv_cost / held if held > 0 else 0.0
        c_price = resolved_prices.get(t)

        if c_price is not None and c_price > 0:
            c_val = held * c_price
            u_pl = c_val - inv_cost
            ret_pct = (u_pl / inv_cost * 100.0) if inv_cost > 0 else 0.0
            total_current_value += c_val
        else:
            c_val = None
            u_pl = None
            ret_pct = None
            all_priced = False
            unpriced_count += 1

        total_invested_capital += inv_cost

        holdings.append(
            {
                "ticker": t,
                "quantity": round(held, 4),
                "average_cost": round(avg_cost, 2),
                "current_price": round(c_price, 2) if c_price is not None else None,
                "invested_value": round(inv_cost, 2),
                "current_value": round(c_val, 2) if c_val is not None else None,
                "unrealized_pl": round(u_pl, 2) if u_pl is not None else None,
                "return_pct": round(ret_pct, 2) if ret_pct is not None else None,
                "realized_pl": round(p["realized_pl"], 2),
                "last_tx_date": p["last_tx_date"],
            }
        )

    # Sort holdings descending by current value / invested value
    holdings.sort(
        key=lambda h: (h["current_value"] if h["current_value"] is not None else h["invested_value"]),
        reverse=True,
    )

    # Portfolio-level Return Metrics
    if all_priced and holdings:
        total_unrealized_pl = total_current_value - total_invested_capital
        total_p_val: Optional[float] = round(total_current_value, 2)
        total_u_pl: Optional[float] = round(total_unrealized_pl, 2)
        total_return_pct: Optional[float] = (
            round(((total_unrealized_pl + total_realized_pl) / total_invested_capital) * 100.0, 2)
            if total_invested_capital > 0
            else 0.0
        )
    else:
        total_p_val = round(total_current_value, 2) if total_current_value > 0 else None
        total_u_pl = None
        total_return_pct = None

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "portfolio_id": portfolio_id,
        "total_invested_capital": round(total_invested_capital, 2),
        "current_portfolio_value": total_p_val,
        "unrealized_pl": total_u_pl,
        "realized_pl": round(total_realized_pl, 2),
        "total_return_pct": total_return_pct,
        "holdings_count": len(holdings),
        "all_priced": all_priced,
        "unpriced_count": unpriced_count,
        "holdings": holdings,
        "latest_quote_time": now_iso,
    }
