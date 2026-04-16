# Portfolio Tracker

Ein selbst gehosteter, open-source Portfolio Tracker für Aktien, ETFs und Kryptowährungen. Alle Daten bleiben lokal – kein Account, keine Cloud, keine Abhängigkeit von Drittanbietern.

---

## Features (v2 – aktuell)

### Dashboard (Streamlit)
- **Live-Kurse** via Yahoo Finance, automatisch aktualisierbar (1 / 5 / 15 / 30 Min)
- **Gesamtübersicht**: Gesamtwert (inkl. optionalem Barvermögen), Gesamt-G/V, Tagesänderung (positionsbezogen)
- **Portfolio-Entwicklung**: Interaktiver Chart mit Zeitraum-Auswahl (1T / 1W / 1M / 3M / 1J / MAX), startet korrekt ab dem jeweiligen Kaufdatum
- **Allocation Pie**: Aufteilung des Portfolios inkl. Barvermögen
- **Positionskarten**: Schnellübersicht je Position mit G/V, Tagesänderung und Link zur Detailansicht
- **Detailansicht je Position** (eigene Seite per Klick):
  - Kursverlauf ab Kaufdatum mit Kaufpunkt-Marker und Einstiegspreis-Linie
  - 52-Wochen-Spanne als Gauge-Chart
  - Rendite nach Zeitraum (1T / 1W / 1M / 3M / 1J)
  - Annualisierte Rendite, Tage gehalten, Sektor
- **Investiert vs. Wert**: Gruppenbalken-Chart je Position
- **Positionstabelle**: Farbcodiert (grün/rot), beste und schwächste Position hervorgehoben
- **CSV-Upload**: Eigenes Portfolio als Datei hochladen
- **Tooltips** auf allen Kennzahlen (Hover-Erklärung)
- **SQLite-Cache** (`data/cache.db`): vermeidet unnötige API-Aufrufe

### CLI (v1, weiterhin verfügbar)
- Terminal-Ausgabe mit G/V je Position und Portfolio-Gesamtübersicht

### Geplant
- **v3** – Telegram Alert Bot: Konfigurierbare Benachrichtigungen bei Kurszielen oder prozentualen Schwellen, steuerbar per Chat-Commands

---

## Installation

```bash
git clone https://github.com/Tobwani/portfolio-tracker.git
cd portfolio-tracker
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Nutzung

### Dashboard (empfohlen)

```bash
streamlit run src/app.py
```

Der Browser öffnet sich automatisch. Das Dashboard lädt `data/example_portfolio.csv` — über die Sidebar kann ein eigenes CSV hochgeladen werden.

### CLI

```bash
python src/tracker.py
```

Liest standardmäßig `data/example_portfolio.csv`. Für ein eigenes Portfolio:

```bash
cp data/example_portfolio.csv data/my_portfolio.csv
# Dann in src/tracker.py: portfolio_path = DATA_DIR / "my_portfolio.csv"
python src/tracker.py
```

---

## CSV-Format

```csv
ticker,purchase_date,purchase_price,quantity
AAPL,2024-01-15,185.50,5
MSFT,2024-03-01,415.00,3
BTC-USD,2024-06-01,67000,0.05
ETH-USD,2024-08-01,2800,0.5
IWDA.AS,2024-02-01,95.00,10
```

| Spalte           | Beschreibung                                                    |
|------------------|-----------------------------------------------------------------|
| `ticker`         | Yahoo Finance Ticker (z. B. `AAPL`, `BTC-USD`, `IWDA.AS`)      |
| `purchase_date`  | Kaufdatum (YYYY-MM-DD) – für Chart-Startpunkt und Laufzeit      |
| `purchase_price` | Kaufkurs in der Handelswährung der Aktie                        |
| `quantity`       | Anzahl der Anteile / Coins                                      |

> **Tipp:** `purchase_date` ist optional – ohne Datum wird kein Kaufpunkt-Marker im Chart angezeigt und die Laufzeit-Kennzahlen entfallen.

---

## Projektstruktur

```
portfolio-tracker/
├── src/
│   ├── tracker.py          # CLI Portfolio Tracker (v1)
│   ├── data_fetcher.py     # Shared: yfinance Wrapper + SQLite Cache
│   └── app.py              # Streamlit Dashboard (v2)
├── data/
│   ├── example_portfolio.csv
│   └── cache.db            # Auto-generiert – nicht committen
├── .streamlit/
│   └── config.toml         # Dark Theme + Server-Einstellungen
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Abhängigkeiten

| Paket                  | Zweck                                  |
|------------------------|----------------------------------------|
| `yfinance`             | Kursdaten von Yahoo Finance            |
| `pandas`               | Datenverarbeitung                      |
| `streamlit`            | Web-Dashboard                          |
| `plotly`               | Interaktive Charts                     |
| `streamlit-autorefresh`| Auto-Refresh im Dashboard              |

---

## Lizenz

MIT
