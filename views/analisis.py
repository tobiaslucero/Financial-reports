import plotly.graph_objects as go
import streamlit as st

from core.data import get_eps, get_history, get_info, get_statements
from core.style import COLORS, page_header, style_fig


def num(v, d=2):
    return f"{v:,.{d}f}" if isinstance(v, (int, float)) else "N/D"

def pct(v):
    return f"{v * 100:.2f}%" if isinstance(v, (int, float)) else "N/D"

def big(v):
    if not isinstance(v, (int, float)):
        return "N/D"
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if abs(v) >= div:
            return f"${v / div:,.2f}{suf}"
    return f"${v:,.0f}"


# Para sumar un ratio: agregá una tupla (label, clave de yfinance, formateador, ayuda)
RATIOS = {
    "Valuación y Riesgo": [
        ("Trailing P/E", "trailingPE", num, "Precio/Ganancias pasadas."),
        ("Forward P/E", "forwardPE", num, "Precio/Ganancias estimadas a futuro."),
        ("PEG Ratio", "pegRatio", num, "P/E ajustado por crecimiento. <1 suele indicar subvaluación."),
        ("EPS Growth (YoY)", "earningsGrowth", pct, "Crecimiento interanual de las ganancias por acción."),
        ("Beta", "beta", num, "Volatilidad respecto al mercado."),
    ],
    "Rentabilidad y Márgenes": [
        ("ROE", "returnOnEquity", pct, "Retorno sobre el patrimonio neto."),
        ("ROA", "returnOnAssets", pct, "Retorno sobre los activos."),
        ("Gross Margin", "grossMargins", pct, "Margen bruto."),
        ("Profit Margin", "profitMargins", pct, "Margen neto."),
    ],
    "Salud Financiera": [
        ("Price to Book", "priceToBook", num, "Precio frente al valor contable."),
        ("Debt to Equity", "debtToEquity", num, "Endeudamiento sobre el patrimonio."),
        ("Current Ratio", "currentRatio", num, "Cobertura de deuda corriente con activos corrientes."),
        ("Quick Ratio", "quickRatio", num, "Prueba ácida: liquidez sin inventarios."),
    ],
}

page_header("Análisis por ticker", "Fundamentales, técnico y estados financieros de cualquier acción.")

ticker = st.text_input("Ticker", value="ORCL", placeholder="ORCL, VIST, MSFT, NVDA…").upper().strip()
if not ticker:
    st.stop()

try:
    info = get_info(ticker)
except Exception:
    st.error("Yahoo Finance limitó las peticiones. Probá de nuevo en unos minutos.")
    st.stop()

# --- Resumen
st.header(f"{info.get('longName', ticker)} ({ticker})")
price = info.get("currentPrice") or info.get("regularMarketPrice")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Precio actual", f"${price:,.2f}" if price else "N/D")
c2.metric("Market cap", big(info.get("marketCap")))
c3.metric("Sector", info.get("sector", "N/D"))
c4.metric("Industria", info.get("industry", "N/D"))

# --- Ratios
st.subheader("Ratios clave")
for tab, (name, items) in zip(st.tabs(list(RATIOS)), RATIOS.items()):
    with tab:
        for col, (label, key, fmt, help_) in zip(st.columns(len(items)), items):
            col.metric(label, fmt(info.get(key)), help=help_)

# --- Técnico
st.subheader("Precio y medias móviles")
period = st.selectbox("Período", ["1y", "2y", "5y", "max"], index=0)
df = get_history(ticker, period)

if df.empty:
    st.info("No hay historial de precios para este activo.")
else:
    df = df.copy()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="Precio", increasing_line_color=COLORS["up"], decreasing_line_color=COLORS["down"],
    ))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50", line=dict(color=COLORS["accent"], width=1.6)))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="SMA 200", line=dict(color=COLORS["blue"], width=1.6)))
    style_fig(fig, 500).update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- Precio vs EPS
    st.subheader("Precio vs EPS trimestral")
    eps = get_eps(ticker)
    if eps is None or eps.empty:
        st.info("No hay datos de EPS disponibles para este activo.")
    else:
        eps = eps[eps.index >= df.index.min()]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=eps.index, y=eps["EPS"], name="EPS trimestral",
                              marker_color=COLORS["blue"], opacity=0.85, yaxis="y1"))
        fig2.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Precio (USD)",
                                  line=dict(color=COLORS["accent"], width=2), yaxis="y2"))
        style_fig(fig2, 450).update_layout(
            yaxis=dict(title="EPS ($)", showgrid=False),
            yaxis2=dict(title="Precio (USD)", overlaying="y", side="right", showgrid=False),
        )
        st.plotly_chart(fig2, use_container_width=True)

# --- Estados
with st.expander("Estados financieros completos"):
    fin, bs = get_statements(ticker)
    t1, t2 = st.tabs(["Income Statement", "Balance Sheet"])
    t1.dataframe(fin, use_container_width=True)
    t2.dataframe(bs, use_container_width=True)
