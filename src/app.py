"""
Portfolio Tracker – Streamlit Dashboard (v2)

Run with:  streamlit run src/app.py
"""

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from streamlit_autorefresh import st_autorefresh

from data_fetcher import (
    PERIOD_MAP,
    get_current_price,
    get_daily_change,
    get_price_history,
    get_ticker_info,
    load_portfolio,
)

st.set_page_config(page_title="Portfolio Tracker", page_icon="📈", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data"

# ── Session state ─────────────────────────────────────────────────────────────
if "detail_ticker" not in st.session_state:
    st.session_state["detail_ticker"] = None


# ── Helpers ───────────────────────────────────────────────────────────────────
def days_held(purchase_date_str: str) -> int:
    try:
        return (date.today() - date.fromisoformat(str(purchase_date_str))).days
    except Exception:
        return 0


def annualized_return(pl_pct: float, days: int) -> float | None:
    if days <= 0:
        return None
    return round(((1 + pl_pct / 100) ** (365 / days) - 1) * 100, 2)


def period_return_from_history(hist: pd.DataFrame, days_back: int) -> float | None:
    """Return % change over the last `days_back` calendar days from a history df."""
    if hist.empty or len(hist) < 2:
        return None
    cutoff = pd.Timestamp.today() - pd.Timedelta(days=days_back)
    before = hist[hist["Date"] <= cutoff]
    if before.empty:
        return None
    ref_price = float(before["Close"].iloc[-1])
    curr_price = float(hist["Close"].iloc[-1])
    if ref_price == 0:
        return None
    return round(((curr_price - ref_price) / ref_price) * 100, 2)


# ── Cached data builders ──────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner="Kurse werden geladen …")
def build_performance(
    tickers: tuple,
    purchases: tuple,
    quantities: tuple,
    purchase_dates: tuple,
) -> pd.DataFrame:
    rows = []
    for ticker, purchase_price, quantity, pdate in zip(
        tickers, purchases, quantities, purchase_dates
    ):
        price = get_current_price(ticker)
        if price is None:
            continue
        daily = get_daily_change(ticker)
        pl = round((price - purchase_price) * quantity, 2)
        pl_pct = round(((price - purchase_price) / purchase_price) * 100, 2)
        value = round(price * quantity, 2)
        cost = round(purchase_price * quantity, 2)
        d_held = days_held(pdate) if pdate else None
        ann = annualized_return(pl_pct, d_held) if d_held else None
        rows.append({
            "Ticker": ticker,
            "Kaufkurs ($)": purchase_price,
            "Aktuell ($)": price,
            "Stück": quantity,
            "Invest ($)": cost,
            "Wert ($)": value,
            "G/V ($)": pl,
            "G/V (%)": pl_pct,
            "Heute ($)": round(daily[0] * quantity, 2) if daily else None,
            "Heute (%)": daily[1] if daily else None,
            "Tage": d_held,
            "Ann. Rendite (%)": ann,
            "_purchase_date": pdate,
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=60, show_spinner=False)
def build_history(
    tickers: tuple,
    purchases: tuple,
    quantities: tuple,
    purchase_dates: tuple,
    period_key: str,
) -> pd.DataFrame:
    combined: dict[str, pd.Series] = {}
    for ticker, purchase_price, quantity, pdate in zip(
        tickers, purchases, quantities, purchase_dates,
    ):
        hist = get_price_history(ticker, period_key)
        if hist.empty:
            continue
        series = hist.set_index("Date")["Close"]
        if pdate:
            series = series[series.index >= pd.to_datetime(pdate)]
        if series.empty:
            continue
        combined[ticker] = series * quantity

    if not combined:
        return pd.DataFrame()

    port_df = pd.DataFrame(combined)
    port_df["Portfolio"] = port_df.fillna(0).sum(axis=1)
    return port_df


@st.cache_data(ttl=3600, show_spinner=False)
def cached_ticker_info(ticker: str) -> dict:
    return get_ticker_info(ticker)


@st.cache_data(ttl=300, show_spinner=False)
def cached_max_history(ticker: str) -> pd.DataFrame:
    return get_price_history(ticker, "MAX")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Portfolio Tracker")
    st.divider()

    uploaded = st.file_uploader("CSV hochladen", type="csv")
    if uploaded:
        df_raw = pd.read_csv(uploaded)
    else:
        csv_path = DATA_DIR / "example_portfolio.csv"
        df_raw = load_portfolio(csv_path)
        st.caption("Nutzt `data/example_portfolio.csv`")

    cash = st.number_input(
        "Barvermögen ($)",
        min_value=0.0,
        value=0.0,
        step=100.0,
        help="Dein Bargeld / Guthaben das noch nicht investiert ist. Wird zum Gesamtwert addiert.",
    )

    st.divider()
    period_key = st.radio("Zeitraum", list(PERIOD_MAP.keys()), index=2, horizontal=True)
    st.divider()

    REFRESH_OPTIONS = {
        "Aus": 0,
        "1 Min": 60,
        "5 Min": 300,
        "15 Min": 900,
        "30 Min": 1800,
    }
    refresh_label = st.selectbox(
        "Auto-Refresh",
        list(REFRESH_OPTIONS.keys()),
        index=2,
        help="Wie oft sollen die Kurse automatisch aktualisiert werden? Yahoo Finance hat Rate-Limits — unter 1 Min wird nicht empfohlen.",
    )
    refresh_seconds = REFRESH_OPTIONS[refresh_label]
    if refresh_seconds > 0:
        st_autorefresh(interval=refresh_seconds * 1000, key="portfolio_autorefresh")

    st.divider()
    st.caption("Daten: Yahoo Finance · Lokal gecacht")


# ── Load data ─────────────────────────────────────────────────────────────────
has_dates = "purchase_date" in df_raw.columns
tickers_t = tuple(df_raw["ticker"])
purchases_t = tuple(df_raw["purchase_price"])
quantities_t = tuple(df_raw["quantity"])
purchase_dates_t = (
    tuple(df_raw["purchase_date"]) if has_dates else tuple(None for _ in tickers_t)
)

perf_df = build_performance(tickers_t, purchases_t, quantities_t, purchase_dates_t)
hist_df = build_history(tickers_t, purchases_t, quantities_t, purchase_dates_t, period_key)


# ══════════════════════════════════════════════════════════════════════════════
# DETAIL PAGE
# ══════════════════════════════════════════════════════════════════════════════
def show_detail_page(ticker: str) -> None:
    if st.button("← Zurück zur Übersicht"):
        st.session_state["detail_ticker"] = None
        st.rerun()

    row = perf_df[perf_df["Ticker"] == ticker]
    if row.empty:
        st.error(f"Keine Daten für {ticker} gefunden.")
        return
    r = row.iloc[0]

    info = cached_ticker_info(ticker)
    name = info.get("name", ticker)
    sector = info.get("sector", "—")
    w52h = info.get("week52_high")
    w52l = info.get("week52_low")

    st.title(f"{name}  ·  {ticker}")
    st.caption(f"Sektor: {sector}")
    st.divider()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(
        "Aktueller Kurs",
        f"${r['Aktuell ($)']:,.2f}",
        help="Letzter gehandelter Preis (Yahoo Finance).",
    )
    c2.metric(
        "Positionswert",
        f"${r['Wert ($)']:,.2f}",
        help="Aktueller Kurs × Anzahl deiner Anteile.",
    )
    c3.metric(
        "Gesamt G/V",
        f"${r['G/V ($)']:+,.2f}",
        delta=f"{r['G/V (%)']:+.2f}%",
        delta_color="normal",
        help="(Aktueller Kurs − Kaufkurs) × Stück. Zeigt ob du insgesamt im Plus oder Minus bist.",
    )
    if r["Heute (%)"] is not None:
        c4.metric(
            "Tagesänderung",
            f"{r['Heute (%)']:+.2f}%",
            delta=f"${r['Heute ($)']:+.2f}",
            delta_color="normal",
            help="Veränderung des Kurses seit dem gestrigen Börsenschluss.",
        )
    if r["Tage"] is not None:
        c5.metric(
            "Gehalten seit",
            f"{int(r['Tage'])} Tage",
            help="Wie lange du diese Position bereits hältst (ab Kaufdatum).",
        )
    if r["Ann. Rendite (%)"] is not None:
        c6.metric(
            "Ann. Rendite",
            f"{r['Ann. Rendite (%)']:+.2f}%",
            help="Hochgerechnet auf 1 Jahr: Wie viel % Rendite pro Jahr du mit dieser Position erzielst.",
        )

    st.divider()

    # ── Chart MAX ab Kaufdatum ─────────────────────────────────────────────────
    st.subheader("Kursverlauf ab Kaufdatum")
    max_hist = cached_max_history(ticker)
    if not max_hist.empty:
        pdate = r.get("_purchase_date")
        series = max_hist.copy()
        if pdate:
            series = series[series["Date"] >= pd.to_datetime(pdate)]

        cost_total = float(r["Invest ($)"])
        is_up = float(r["Wert ($)"]) >= cost_total
        lc = "#00d4aa" if is_up else "#ff4b4b"

        qty = float(r["Stück"])
        position_values = series["Close"] * qty

        # Find the data point closest to the purchase date for the buy marker
        buy_x = buy_y = None
        if pdate and not series.empty:
            buy_dt = pd.to_datetime(pdate)
            idx = (series["Date"] - buy_dt).abs().idxmin()
            buy_x = series.loc[idx, "Date"]
            buy_y = series.loc[idx, "Close"] * qty

        fig = go.Figure()
        fig.add_hline(
            y=cost_total,
            line_dash="dot",
            line_color="rgba(255,255,255,0.3)",
            annotation_text=f"Einstieg ${cost_total:,.0f}",
            annotation_position="bottom right",
        )
        fig.add_trace(go.Scatter(
            x=series["Date"],
            y=position_values,
            mode="lines",
            name="Positionswert",
            line={"color": lc, "width": 2},
            fill="tozeroy",
            fillcolor=f"{'rgba(0,212,170,0.08)' if is_up else 'rgba(255,75,75,0.08)'}",
            hovertemplate="<b>%{x|%d.%m.%Y}</b><br>$%{y:,.2f}<extra></extra>",
        ))
        # Buy marker: dot + annotation on the chart
        if buy_x is not None:
            fig.add_trace(go.Scatter(
                x=[buy_x],
                y=[buy_y],
                mode="markers+text",
                name="Kaufzeitpunkt",
                marker={"color": "#ffffff", "size": 10, "line": {"color": lc, "width": 2}},
                text=["Kauf"],
                textposition="top center",
                textfont={"color": "#ffffff", "size": 11},
                hovertemplate=f"<b>Kaufdatum</b><br>{buy_x.strftime('%d.%m.%Y')}<br>${buy_y:,.2f}<extra></extra>",
                showlegend=False,
            ))
        fig.update_layout(
            margin={"t": 10, "b": 10, "l": 0, "r": 0},
            height=340,
            showlegend=False,
            xaxis={"showgrid": False},
            yaxis={"showgrid": True, "gridcolor": "#2a2a2a", "tickprefix": "$"},
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── 52-Wochen-Spanne ───────────────────────────────────────────────────────
    if w52h and w52l:
        st.subheader("52-Wochen-Spanne")
        curr = float(r["Aktuell ($)"])
        pct_pos = max(0.0, min(1.0, (curr - w52l) / (w52h - w52l))) if w52h != w52l else 0.5

        fig_range = go.Figure(go.Indicator(
            mode="gauge+number",
            value=curr,
            number={"prefix": "$", "valueformat": ",.2f"},
            gauge={
                "axis": {"range": [w52l, w52h]},
                "bar": {"color": "#00d4aa"},
                "bgcolor": "#1a1d27",
                "steps": [{"range": [w52l, w52h], "color": "#2a2a3a"}],
                "threshold": {
                    "line": {"color": "white", "width": 2},
                    "thickness": 0.75,
                    "value": curr,
                },
            },
        ))
        fig_range.update_layout(
            height=200,
            margin={"t": 20, "b": 10, "l": 30, "r": 30},
            paper_bgcolor="rgba(0,0,0,0)",
        )
        col_l, col_g, col_r = st.columns([1, 3, 1])
        col_l.metric("52W Tief", f"${w52l:,.2f}")
        col_g.plotly_chart(fig_range, use_container_width=True)
        col_r.metric("52W Hoch", f"${w52h:,.2f}")

    # ── Periodische Renditen ───────────────────────────────────────────────────
    if not max_hist.empty:
        st.subheader("Rendite nach Zeitraum")
        periods = {"1T": 1, "1W": 7, "1M": 30, "3M": 90, "1J": 365}
        ret_cols = st.columns(len(periods))
        for col, (label, d) in zip(ret_cols, periods.items()):
            ret = period_return_from_history(max_hist, d)
            if ret is not None:
                col.metric(label, f"{ret:+.2f}%", delta_color="normal",
                           help=f"Kursveränderung der letzten {d} Tage in Prozent.")
            else:
                col.metric(label, "—")

    st.divider()

    # ── Position Details Tabelle ───────────────────────────────────────────────
    detail_data = {
        "Kaufkurs": f"${r['Kaufkurs ($)']:,.2f}",
        "Stück": r["Stück"],
        "Investiert": f"${r['Invest ($)']:,.2f}",
        "Aktueller Wert": f"${r['Wert ($)']:,.2f}",
        "Gewinn/Verlust": f"${r['G/V ($)']:+,.2f} ({r['G/V (%)']:+.2f}%)",
    }
    if r["_purchase_date"]:
        detail_data["Kaufdatum"] = r["_purchase_date"]
    st.dataframe(
        pd.DataFrame(detail_data.items(), columns=["Kennzahl", "Wert"]),
        use_container_width=True,
        hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
def show_main_page() -> None:
    st.title("📈 Portfolio Tracker")

    total_positions = perf_df["Wert ($)"].sum() if not perf_df.empty else 0.0
    total_value = round(total_positions + cash, 2)
    total_invest = perf_df["Invest ($)"].sum() if not perf_df.empty else 0.0
    total_pl = perf_df["G/V ($)"].sum() if not perf_df.empty else 0.0
    total_pl_pct = round((total_pl / total_invest) * 100, 2) if total_invest else 0.0
    today_pl = (
        perf_df["Heute ($)"].dropna().sum() if "Heute ($)" in perf_df.columns else None
    )

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Gesamtwert",
        f"${total_value:,.2f}",
        help="Aktueller Wert aller Positionen + dein eingetragenes Barvermögen.",
    )
    c2.metric(
        "Gesamt G/V",
        f"${total_pl:,.2f}",
        delta=f"{total_pl_pct:+.2f}%",
        delta_color="normal",
        help="Gesamter Gewinn oder Verlust über alle Positionen seit deinem Einstieg. Barvermögen wird nicht eingerechnet.",
    )
    c3.metric(
        "Investiert",
        f"${total_invest:,.2f}",
        help="Summe aller Kaufpreise (Einstiegskurs × Stückzahl) — dein gesamter Kapitaleinsatz.",
    )
    if today_pl is not None:
        today_pct = round((today_pl / total_invest) * 100, 2) if total_invest else 0
        c4.metric(
            "Tagesänderung",
            f"${today_pl:+,.2f}",
            delta=f"{today_pct:+.2f}%",
            delta_color="normal",
            help="Wie viel dein Portfolio heute im Vergleich zum gestrigen Börsenschluss gewonnen oder verloren hat.",
        )

    st.divider()

    # Portfolio Chart + Allocation
    left, right = st.columns([2, 1])

    with left:
        st.subheader("Portfolio-Entwicklung")
        if not hist_df.empty:
            port_series = hist_df["Portfolio"].dropna()
            is_up = port_series.iloc[-1] >= port_series.iloc[0]
            lc = "#00d4aa" if is_up else "#ff4b4b"

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=port_series.index,
                y=port_series,
                mode="lines",
                name="Portfolio",
                line={"color": lc, "width": 2},
                fill="tozeroy",
                fillcolor=f"{'rgba(0,212,170,0.08)' if is_up else 'rgba(255,75,75,0.08)'}",
                hovertemplate="<b>%{x|%d.%m.%Y}</b><br>$%{y:,.2f}<extra></extra>",
            ))
            fig.update_layout(
                margin={"t": 10, "b": 10, "l": 0, "r": 0},
                height=300,
                showlegend=False,
                xaxis={"showgrid": False},
                yaxis={"showgrid": True, "gridcolor": "#2a2a2a", "tickprefix": "$"},
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Keine Verlaufsdaten verfügbar.")

    with right:
        st.subheader("Allocation")
        if not perf_df.empty:
            alloc_df = perf_df[["Ticker", "Wert ($)"]].copy()
            if cash > 0:
                alloc_df = pd.concat(
                    [alloc_df, pd.DataFrame([{"Ticker": "Cash", "Wert ($)": cash}])],
                    ignore_index=True,
                )
            fig_pie = px.pie(
                alloc_df,
                names="Ticker",
                values="Wert ($)",
                hole=0.55,
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_pie.update_traces(
                textposition="outside",
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>$%{value:,.2f} (%{percent})<extra></extra>",
            )
            fig_pie.update_layout(
                margin={"t": 10, "b": 10, "l": 0, "r": 0},
                height=300,
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # Positions Grid
    st.subheader("Positionen")
    if not perf_df.empty:
        n_cols = min(len(perf_df), 3)
        cols = st.columns(n_cols)
        for i, (_, r) in enumerate(perf_df.iterrows()):
            ticker = r["Ticker"]
            with cols[i % n_cols]:
                pl_color = "#00c853" if r["G/V ($)"] >= 0 else "#ff1744"
                today_str = ""
                if r["Heute (%)"] is not None:
                    arrow = "▲" if r["Heute (%)"] >= 0 else "▼"
                    today_str = f"{arrow} {r['Heute (%)']:+.2f}% heute"

                st.markdown(
                    f"""
                    <div style="border:1px solid #2a2a3a; border-radius:8px; padding:14px; margin-bottom:8px;">
                        <div style="font-size:1.1rem; font-weight:700;">{ticker}</div>
                        <div style="font-size:1.4rem; font-weight:700;">${r['Aktuell ($)']:,.2f}</div>
                        <div style="color:{pl_color}; font-weight:600;">{r['G/V ($)']:+,.2f}$ &nbsp; {r['G/V (%)']:+.2f}%</div>
                        <div style="color:#888; font-size:0.85rem;">{today_str}</div>
                        <div style="color:#aaa; font-size:0.85rem;">Wert: ${r['Wert ($)']:,.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Details →", key=f"detail_{ticker}", use_container_width=True):
                    st.session_state["detail_ticker"] = ticker
                    st.rerun()

    st.divider()

    # Investiert vs. Wert Bar Chart
    st.subheader("Investiert vs. aktueller Wert")
    if not perf_df.empty:
        bar_data = perf_df[["Ticker", "Invest ($)", "Wert ($)"]].melt(
            id_vars="Ticker", var_name="Art", value_name="Betrag ($)"
        )
        fig_bar = px.bar(
            bar_data,
            x="Ticker",
            y="Betrag ($)",
            color="Art",
            barmode="group",
            color_discrete_map={"Invest ($)": "#4a4a6a", "Wert ($)": "#00d4aa"},
        )
        fig_bar.update_layout(
            margin={"t": 10, "b": 10, "l": 0, "r": 0},
            height=250,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend={"title": ""},
            yaxis={"tickprefix": "$", "gridcolor": "#2a2a2a"},
            xaxis={"showgrid": False},
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Positionen Tabelle
    st.subheader("Übersicht aller Positionen")
    if not perf_df.empty:
        display_cols = ["Ticker", "Kaufkurs ($)", "Aktuell ($)", "Stück",
                        "Invest ($)", "Wert ($)", "G/V ($)", "G/V (%)"]
        if "Heute (%)" in perf_df.columns:
            display_cols += ["Heute ($)", "Heute (%)"]
        if "Tage" in perf_df.columns:
            display_cols.append("Tage")
        if "Ann. Rendite (%)" in perf_df.columns:
            display_cols.append("Ann. Rendite (%)")

        disp = perf_df[display_cols].copy()

        green_red = ["G/V ($)", "G/V (%)"]
        if "Heute ($)" in disp.columns:
            green_red += ["Heute ($)", "Heute (%)"]
        if "Ann. Rendite (%)" in disp.columns:
            green_red.append("Ann. Rendite (%)")

        fmt = {
            "Kaufkurs ($)": "${:.2f}", "Aktuell ($)": "${:.2f}",
            "Invest ($)": "${:.2f}", "Wert ($)": "${:.2f}",
            "G/V ($)": "${:+.2f}", "G/V (%)": "{:+.2f}%",
        }
        if "Heute ($)" in disp.columns:
            fmt["Heute ($)"] = "${:+.2f}"
            fmt["Heute (%)"] = "{:+.2f}%"
        if "Ann. Rendite (%)" in disp.columns:
            fmt["Ann. Rendite (%)"] = "{:+.2f}%"

        def _color_pl(val: float) -> str:
            return f"color: {'#00c853' if val >= 0 else '#ff1744'}; font-weight: bold"

        styled = disp.style.map(_color_pl, subset=green_red).format(fmt)
        st.dataframe(styled, use_container_width=True, hide_index=True)

        if len(perf_df) > 1:
            best = perf_df.loc[perf_df["G/V (%)"].idxmax()]
            worst = perf_df.loc[perf_df["G/V (%)"].idxmin()]
            b1, b2 = st.columns(2)
            b1.success(f"🏆 Beste Position: **{best['Ticker']}** ({best['G/V (%)']:+.2f}%)")
            b2.error(f"📉 Schwächste Position: **{worst['Ticker']}** ({worst['G/V (%)']:+.2f}%)")


# ── Router ────────────────────────────────────────────────────────────────────
if st.session_state["detail_ticker"]:
    show_detail_page(st.session_state["detail_ticker"])
else:
    show_main_page()
