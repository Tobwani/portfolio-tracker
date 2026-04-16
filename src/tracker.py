import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).parent.parent / "data"


def round_float(number: float) -> float:
    return round(float(number), 2)


def load_portfolio(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"ticker", "purchase_price", "quantity"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        print(f"Fehler: Fehlende Spalten in CSV: {missing}")
        sys.exit(1)
    return df


def get_current_price(ticker: str) -> float | None:
    try:
        info = yf.Ticker(ticker).fast_info
        price = info["last_price"]
        if price is None:
            raise ValueError("Kein Preis verfügbar")
        return round_float(price)
    except Exception as e:
        print(f"Warnung: Preis für '{ticker}' konnte nicht abgerufen werden ({e})")
        return None


def calculate_performance(df: pd.DataFrame) -> dict:
    performance = {}

    for idx, ticker in enumerate(df["ticker"]):
        current_price = get_current_price(ticker)
        if current_price is None:
            continue

        purchase_price = round_float(df["purchase_price"].iloc[idx])
        quantity = df["quantity"].iloc[idx]

        profit_loss = round_float((current_price - purchase_price) * quantity)
        profit_loss_percent = round_float(
            ((current_price - purchase_price) / purchase_price) * 100
        )
        current_value = round_float(current_price * quantity)

        performance[ticker] = {
            "current_price": current_price,
            "purchase_price": purchase_price,
            "quantity": quantity,
            "profit_loss": profit_loss,
            "profit_loss_percent": profit_loss_percent,
            "current_value": current_value,
        }

    return performance


def show_results(performance: dict) -> None:
    print("=" * 40)
    print("  Portfolio Übersicht")
    print("=" * 40)

    total_value = 0.0
    total_pl = 0.0

    for ticker, info in performance.items():
        sign = "+" if info["profit_loss"] >= 0 else ""
        print(f"\n{ticker}")
        print(f"  Aktueller Kurs:  ${info['current_price']}")
        print(f"  Kaufkurs:        ${info['purchase_price']}")
        print(f"  Stück:           {info['quantity']}")
        print(f"  Positionswert:   ${info['current_value']}")
        print(f"  Gewinn/Verlust:  {sign}{info['profit_loss']}$ ({sign}{info['profit_loss_percent']}%)")
        total_value += info["current_value"]
        total_pl += info["profit_loss"]

    print("\n" + "=" * 40)
    sign = "+" if total_pl >= 0 else ""
    print(f"  Gesamtwert:      ${round_float(total_value)}")
    print(f"  Gesamt G/V:      {sign}{round_float(total_pl)}$")
    print("=" * 40)


if __name__ == "__main__":
    portfolio_path = DATA_DIR / "example_portfolio.csv"
    df = load_portfolio(portfolio_path)
    performance = calculate_performance(df)
    show_results(performance)
