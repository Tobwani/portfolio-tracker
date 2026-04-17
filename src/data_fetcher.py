"""
Shared data-fetching layer used by both tracker.py (CLI) and app.py (Streamlit).

Price history is cached in a local SQLite database (data/cache.db).
Each historical data point is stored with the actual historical date as key,
plus a 'fetched' timestamp for cache invalidation.
"""

import sqlite3
from datetime import date
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
    "MAX": ("max", "1wk"),
}


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    cols = {row[1] for row in conn.execute("PRAGMA table_info(price_cache)").fetchall()}
    if cols and "hist_date" not in cols:
        conn.execute("DROP TABLE price_cache")

    conn.execute(
        """CREATE TABLE IF NOT EXISTS price_cache (
            ticker    TEXT,
            period    TEXT,
            hist_date TEXT,
            close     REAL,
            fetched   TEXT,
            PRIMARY KEY (ticker, period, hist_date)
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


def get_daily_change(ticker: str) -> tuple[float, float] | None:
    """Return (raw_price_change_per_unit, change_pct) for today.

    raw_price_change is the per-unit price delta — multiply by quantity in the caller.
    Returns None on error.
    """
    try:
        fi = yf.Ticker(ticker).fast_info
        prev = fi["previous_close"]
        curr = fi["last_price"]
        if prev and curr:
            chg = round(curr - prev, 4)
            chg_pct = round((chg / prev) * 100, 2)
            return chg, chg_pct
    except Exception:
        pass
    return None


def get_ticker_info(ticker: str) -> dict:
    """Return static info: name, sector, 52W high/low, currency."""
    result: dict = {}
    try:
        info = yf.Ticker(ticker).info
        result["name"] = info.get("longName") or info.get("shortName", ticker)
        result["sector"] = info.get("sector", "—")
        result["week52_high"] = info.get("fiftyTwoWeekHigh")
        result["week52_low"] = info.get("fiftyTwoWeekLow")
        result["currency"] = info.get("currency", "USD")
    except Exception:
        pass
    return result


def get_price_history(ticker: str, period_key: str) -> pd.DataFrame:
    """Return DataFrame with columns [Date, Close] for the given period.

    Uses daily cache for intervals >= 1d. Intraday data (5m, 1h) is always live.
    """
    yf_period, yf_interval = PERIOD_MAP.get(period_key, ("1mo", "1d"))

    conn = _get_conn()
    use_cache = yf_interval not in ("5m", "1h")
    cache_key = f"{yf_period}_{yf_interval}"
    today = date.today().isoformat()

    if use_cache:
        rows = conn.execute(
            """SELECT hist_date, close FROM price_cache
               WHERE ticker=? AND period=? AND fetched=?
               ORDER BY hist_date""",
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
            conn.executemany(
                """INSERT OR REPLACE INTO price_cache
                   (ticker, period, hist_date, close, fetched)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    (ticker, cache_key, str(row.Date.date()), float(row.Close), today)
                    for row in df.itertuples()
                ],
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
