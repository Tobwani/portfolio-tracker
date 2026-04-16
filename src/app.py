"""
Portfolio Tracker – Streamlit Dashboard (v2)

Run with:  streamlit run src/app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_fetcher import PERIOD_MAP, get_current_price, get_price_history, load_portfolio

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Portfolio Tracker",
    page_icon="📈",
    layout="wide",
)

DATA_DIR = Path(__file__).parent.parent / "data"

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
        st.caption("Nutzt `data/example_portfolio.csv` — lade dein eigenes CSV hoch.")

    st.divider()
    period_key = st.radio("Zeitraum", list(PERIOD_MAP.keys()), index=2, horizontal=True)
    st.divider()
    st.caption("Daten: Yahoo Finance · Lokal gecacht")


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="Kurse werden geladen …")
def build_performance(tickers: tuple, purchases: tuple, quantities: tuple):
    rows = []
    for ticker, purchase_price, quantity in zip(tickers, purchases, quantities):
        price = get_current_price(ticker)
        if price is None:
            continue
        pl = round((price - purchase_price) * quantity, 2)
        pl_pct = round(((price - purchase_price) / purchase_price) * 100, 2)
        value = round(price * quantity, 2)
        cost = round(purchase_price * quantity, 2)
        rows.append({
            "Ticker": ticker,
            "Kaufkurs ($)": purchase_price,
            "Aktuell ($)": price,
            "Stück": quantity,
            "Invest ($)": cost,
            "Wert ($)": value,
            "G/V ($)": pl,
            "G/V (%)": pl_pct,
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner=False)
def build_history(tickers: tuple, purchases: tuple, quantities: tuple, period_key: str):
    """Combine individual position histories into a single portfolio value series."""
    combined: dict[str, pd.Series] = {}
    for ticker, purchase_price, quantity in zip(tickers, purchases, quantities):
        hist = get_price_history(ticker, period_key)
        if hist.empty:
            continue
        hist = hist.set_index("Date")["Close"]
        combined[ticker] = hist * quantity

    if not combined:
        return pd.DataFrame()

    port_df = pd.DataFrame(combined)
    port_df["Portfolio"] = port_df.sum(axis=1)
    return port_df


tickers_t = tuple(df_raw["ticker"])
purchases_t = tuple(df_raw["purchase_price"])
quantities_t = tuple(df_raw["quantity"])

perf_df = build_performance(tickers_t, purchases_t, quantities_t)
hist_df = build_history(tickers_t, purchases_t, quantities_t, period_key)

# ── Summary KPIs ──────────────────────────────────────────────────────────────
total_value = perf_df["Wert ($)"].sum() if not perf_df.empty else 0
total_invest = perf_df["Invest ($)"].sum() if not perf_df.empty else 0
total_pl = perf_df["G/V ($)"].sum() if not perf_df.empty else 0
total_pl_pct = round((total_pl / total_invest) * 100, 2) if total_invest else 0

# Daily change from history
day_change = None
if not hist_df.empty and len(hist_df) >= 2:
    day_change = round(hist_df["Portfolio"].iloc[-1] - hist_df["Portfolio"].iloc[-2], 2)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Gesamtwert", f"${total_value:,.2f}")
col2.metric(
    "Gesamt G/V",
    f"${total_pl:,.2f}",
    delta=f"{total_pl_pct:+.2f}%",
    delta_color="normal",
)
col3.metric("Investiert", f"${total_invest:,.2f}")
if day_change is not None:
    col4.metric("Änderung (Periode)", f"${day_change:,.2f}", delta_color="normal")

st.divider()

# ── Portfolio Chart ───────────────────────────────────────────────────────────
left, right = st.columns([2, 1])

with left:
    st.subheader("Kursverlauf")
    if not hist_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_df.index,
            y=hist_df["Portfolio"],
            mode="lines",
            name="Portfolio",
            line={"color": "#00d4aa", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(0,212,170,0.08)",
        ))
        fig.update_layout(
            margin={"t": 10, "b": 10, "l": 0, "r": 0},
            height=280,
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
        fig_pie = px.pie(
            perf_df,
            names="Ticker",
            values="Wert ($)",
            hole=0.55,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_pie.update_traces(textposition="outside", textinfo="percent+label")
        fig_pie.update_layout(
            margin={"t": 10, "b": 10, "l": 0, "r": 0},
            height=280,
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── Individual Position Charts ────────────────────────────────────────────────
st.subheader("Positionen im Detail")

if not hist_df.empty:
    position_cols = [c for c in hist_df.columns if c != "Portfolio"]
    tabs = st.tabs(position_cols)
    for tab, ticker in zip(tabs, position_cols):
        with tab:
            fig_pos = go.Figure()
            fig_pos.add_trace(go.Scatter(
                x=hist_df.index,
                y=hist_df[ticker],
                mode="lines",
                name=ticker,
                line={"width": 2},
            ))
            fig_pos.update_layout(
                margin={"t": 10, "b": 10, "l": 0, "r": 0},
                height=200,
                showlegend=False,
                xaxis={"showgrid": False},
                yaxis={"showgrid": True, "gridcolor": "#2a2a2a", "tickprefix": "$"},
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pos, use_container_width=True)

st.divider()

# ── Positions Table ───────────────────────────────────────────────────────────
st.subheader("Übersicht aller Positionen")

if not perf_df.empty:
    def color_pl(val):
        color = "#00c853" if val >= 0 else "#ff1744"
        return f"color: {color}; font-weight: bold"

    styled = (
        perf_df.style
        .applymap(color_pl, subset=["G/V ($)", "G/V (%)"])
        .format({
            "Kaufkurs ($)": "${:.2f}",
            "Aktuell ($)": "${:.2f}",
            "Invest ($)": "${:.2f}",
            "Wert ($)": "${:.2f}",
            "G/V ($)": "${:+.2f}",
            "G/V (%)": "{:+.2f}%",
        })
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.warning("Keine Positionsdaten geladen – prüfe dein CSV und Tickersymbole.")
