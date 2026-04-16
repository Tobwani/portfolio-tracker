# Portfolio Tracker

Ein selbst gehosteter, open-source Portfolio Tracker für Aktien, ETFs und Kryptowährungen. Alle Daten bleiben lokal – kein Account, keine Cloud, keine Abhängigkeit von Drittanbietern.

## Features (v1)

- Aktuelle Kurse via Yahoo Finance (yfinance)
- Gewinn/Verlust je Position (absolut & prozentual)
- Gesamtportfolio-Übersicht im Terminal
- Eigenes CSV als Datenbasis

## Geplante Features

- **v2** – Streamlit Dashboard mit interaktiven Charts (Plotly), Zeitraum-Auswahl (1T/1W/1M/…), Allocation-Übersicht
- **v3** – Telegram Alert Bot: konfigurierbare Benachrichtigungen bei Kurszielen oder prozentualen Schwellen

## Installation

```bash
git clone https://github.com/<dein-username>/portfolio-tracker.git
cd portfolio-tracker
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Nutzung

```bash
python src/tracker.py
```

Das Skript liest `data/example_portfolio.csv`. Für ein eigenes Portfolio die Datei kopieren:

```bash
cp data/example_portfolio.csv data/my_portfolio.csv
```

Dann in `src/tracker.py` den Pfad anpassen:

```python
portfolio_path = DATA_DIR / "my_portfolio.csv"
```

## CSV-Format

```csv
ticker,purchase_date,purchase_price,quantity
AAPL,2024-01-15,185.50,5
MSFT,2024-03-01,415.00,3
BTC-USD,2024-06-01,67000,0.05
```

| Spalte           | Beschreibung                              |
|------------------|-------------------------------------------|
| `ticker`         | Yahoo Finance Ticker (z. B. `AAPL`, `BTC-USD`, `IWDA.AS`) |
| `purchase_date`  | Kaufdatum (YYYY-MM-DD)                    |
| `purchase_price` | Kaufkurs in USD                           |
| `quantity`       | Anzahl der Anteile / Coins                |

## Projektstruktur

```
portfolio-tracker/
├── src/
│   └── tracker.py        # CLI Portfolio Tracker
├── data/
│   └── example_portfolio.csv
├── requirements.txt
└── README.md
```

## Lizenz

MIT
