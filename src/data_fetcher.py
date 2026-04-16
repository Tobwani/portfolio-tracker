"""
Shared data-fetching layer used by both tracker.py (CLI) and app.py (Streamlit).

Caches price history in a local SQLite database to avoid redundant API calls
within the same session.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

DB_PATH = Path(__file__).parent.parent / "data" / "cache.db"

PERIOD_MAP = {
    "1T": ("1d", "5m"),
    "1W": ("5d", "1h"),
    "1M": ("1mo", "1d"),
    "3M": ("3mo", "1d"),
    "1J": ("1y", "1wk"),
    "MAX": ("max", "1mo"),
}


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS price_cache (
            ticker TEXT,
            date   TEXT,
            period TEXT,
            close  REAL,
            PRIMARY KEY (ticker, date, period)
        )"""
    )
    conn.commit()
    return conn


def get_current_price(ticker: str) -> float | None:
    try:
        price = yf.Ticker(ticker).fast_info["last_price"]
        if price is None:
            raise ValueError("no price")
        return round(float(price), 2)
    except Exception:
        return None


def get_price_history(ticker: str, period_key: str) -> pd.DataFrame:
    """Return a DataFrame with columns [Date, Close] for the given period."""
    yf_period, yf_interval = PERIOD_MAP.get(period_key, ("1mo", "1d"))

    conn = _get_conn()

    # Use cache only for daily+ intervals (intraday data changes too fast)
    use_cache = yf_interval not in ("5m", "1h")
    cache_key = f"{yf_period}_{yf_interval}"

    if use_cache:
        today = date.today().isoformat()
        rows = conn.execute(
            "SELECT date, close FROM price_cache WHERE ticker=? AND period=? AND date=?",
            (ticker, cache_key, today),
        ).fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=["Date", "Close"])
            df["Date"] = pd.to_datetime(df["Date"])
            conn.close()
            return df

    try:
        raw = yf.Ticker(ticker).history(period=yf_period, interval=yf_interval)
        if raw.empty:
            conn.close()
            return pd.DataFrame(columns=["Date", "Close"])

        df = raw[["Close"]].reset_index()
        df.columns = ["Date", "Close"]
        df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)

        if use_cache:
            today = date.today().isoformat()
            conn.executemany(
                "INSERT OR REPLACE INTO price_cache (ticker, date, period, close) VALUES (?,?,?,?)",
                [(ticker, today, cache_key, float(row.Close)) for row in df.itertuples()],
            )
            conn.commit()
    except Exception:
        df = pd.DataFrame(columns=["Date", "Close"])
    finally:
        conn.close()

    return df


def load_portfolio(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"ticker", "purchase_price", "quantity"}
    if not required.issubset(df.columns):
        raise ValueError(f"Fehlende Spalten: {required - set(df.columns)}")
    return df
