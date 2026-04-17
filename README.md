# Portfolio Tracker

Ein selbst gehosteter, open-source Portfolio Tracker für Aktien, ETFs und Kryptowährungen. Alle Daten bleiben lokal – kein Account, keine Cloud, keine Abhängigkeit von Drittanbietern.

---

## Features (v2 – aktuell)

### Dashboard (Streamlit)
- **Live-Kurse** via Yahoo Finance, automatisch aktualisierbar (1 / 5 / 15 / 30 Min)
- **Währungsunterstützung**: Basiswährung EUR oder USD wählbar — US-Aktien (AAPL, MSFT usw.) werden automatisch per Live-Wechselkurs umgerechnet
- **Gesamtübersicht**: Gesamtwert (inkl. optionalem Barvermögen), Gesamt-G/V, Tagesänderung (positionsbezogen: Kursänderung × Stück)
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
- **Tooltips** auf allen Kennzahlen
- **SQLite-Cache** (`data/cache.db`): vermeidet unnötige API-Aufrufe
- **Ticker-Hilfe** in der Sidebar mit den häufigsten Trade Republic Instrumenten

### CLI (v1, weiterhin verfügbar)
- Terminal-Ausgabe mit G/V je Position und Portfolio-Gesamtübersicht (in EUR)

### Geplant
- **v3** – Telegram Alert Bot: Konfigurierbare Benachrichtigungen bei Kurszielen oder prozentualen Schwellen

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

Der Browser öffnet sich automatisch. Das Dashboard lädt `data/example_portfolio.csv` — über die Sidebar kann ein eigenes CSV hochgeladen werden oder die Datei direkt bearbeitet werden.

### CLI

```bash
python src/tracker.py
```

---

## CSV-Format

```csv
ticker,purchase_date,purchase_price,quantity
AAPL,2024-01-15,152.30,5
SAP.DE,2024-03-01,172.50,3
BTC-EUR,2024-06-01,61500,0.05
NVDA,2024-09-01,102.50,4
EUNL.DE,2023-11-01,68.20,15
```

| Spalte           | Beschreibung |
|------------------|--------------|
| `ticker`         | Yahoo Finance Ticker (siehe Tabelle unten) |
| `purchase_date`  | Kaufdatum (YYYY-MM-DD) – optional, aber empfohlen für Chart-Startpunkt und Renditeberechnung |
| `purchase_price` | Kaufkurs in deiner **Basiswährung** (Standard: EUR) — bei US-Aktien also den EUR-Betrag eintragen, den Trade Republic dir berechnet hat |
| `quantity`       | Anzahl der Anteile / Coins / Bruchteile |

> **Wichtig:** `purchase_price` immer in der gewählten Basiswährung (Standard: EUR) eintragen. Das ist der Betrag, den Trade Republic dir für den Kauf berechnet hat — nicht der USD-Rohpreis.

---

## Ticker-Formate (Yahoo Finance)

**Faustregel:**
- Kein Suffix → US-Börse, Preis in USD → wird automatisch in EUR umgerechnet
- `.DE` Suffix → XETRA Frankfurt, Preis direkt in EUR
- `.AS` Suffix → Amsterdam (Euronext), Preis direkt in EUR
- Krypto: `-EUR` statt `-USD` verwenden (z.B. `BTC-EUR`)

| Instrument | Yahoo Finance Ticker | Börse | Währung |
|---|---|---|---|
| Apple | `AAPL` | NASDAQ | USD → auto EUR |
| Microsoft | `MSFT` | NASDAQ | USD → auto EUR |
| NVIDIA | `NVDA` | NASDAQ | USD → auto EUR |
| Alphabet (Google) | `GOOG` | NASDAQ | USD → auto EUR |
| Amazon | `AMZN` | NASDAQ | USD → auto EUR |
| Tesla | `TSLA` | NASDAQ | USD → auto EUR |
| Meta | `META` | NASDAQ | USD → auto EUR |
| SAP | `SAP.DE` | XETRA | EUR direkt |
| Siemens | `SIE.DE` | XETRA | EUR direkt |
| BMW | `BMW.DE` | XETRA | EUR direkt |
| Allianz | `ALV.DE` | XETRA | EUR direkt |
| Deutsche Telekom | `DTE.DE` | XETRA | EUR direkt |
| ASML | `ASML.AS` | Amsterdam | EUR direkt |
| MSCI World ETF (iShares) | `EUNL.DE` | XETRA | EUR direkt |
| MSCI World ETF (iShares) alternativ | `IWDA.AS` | Amsterdam | EUR direkt |
| NASDAQ-100 ETF (iShares) | `CNDX.AS` | Amsterdam | EUR direkt |
| S&P 500 ETF (iShares) | `CSPX.AS` | Amsterdam | USD → auto EUR |
| Bitcoin | `BTC-EUR` | – | EUR direkt |
| Ethereum | `ETH-EUR` | – | EUR direkt |
| Solana | `SOL-EUR` | – | EUR direkt |

> **Tipp:** Yahoo Finance Ticker findest du auf [finance.yahoo.com](https://finance.yahoo.com) — einfach den Namen der Aktie suchen und den Ticker aus der URL ablesen.

---

## Projektstruktur

```
portfolio-tracker/
├── src/
│   ├── tracker.py          # CLI Portfolio Tracker (v1)
│   ├── data_fetcher.py     # Shared: yfinance Wrapper + SQLite Cache + Währungskonvertierung
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

| Paket | Zweck |
|---|---|
| `yfinance` | Kursdaten und Wechselkurse von Yahoo Finance |
| `pandas` | Datenverarbeitung |
| `streamlit` | Web-Dashboard |
| `plotly` | Interaktive Charts |
| `streamlit-autorefresh` | Auto-Refresh im Dashboard |

---

## Lizenz

MIT
