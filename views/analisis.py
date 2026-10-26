import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from core.data import get_eps, get_history, get_info, get_statements
from core.indicators import bollinger, macd, rsi
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


def add_derived(info: dict) -> dict:
    """Ratios que yfinance no da directo y se calculan acá."""
    d = dict(info)
    price = d.get("currentPrice") or d.get("regularMarketPrice")
    mcap, fcf, ebitda = d.get("marketCap"), d.get("freeCashflow"), d.get("ebitda")
    if mcap and isinstance(fcf, (int, float)):
        d["fcfYield"] = fcf / mcap
    if isinstance(ebitda, (int, float)) and ebitda > 0 and d.get("totalDebt") is not None and d.get("totalCash") is not None:
        d["netDebtToEbitda"] = (d["totalDebt"] - d["totalCash"]) / ebitda
    if price and d.get("dividendRate"):
        d["divYield"] = d["dividendRate"] / price
    return d


# Para sumar un ratio: agregá una tupla (label, clave de info, formateador, ayuda)
RATIOS = {
    "Valuación y Riesgo": [
        ("Trailing P/E", "trailingPE", num, "Precio/Ganancias pasadas."),
        ("Forward P/E", "forwardPE", num, "Precio/Ganancias estimadas a futuro."),
        ("PEG Ratio", "pegRatio", num, "P/E ajustado por crecimiento. <1 suele indicar subvaluación."),
        ("EPS Growth (YoY)", "earningsGrowth", pct, "Crecimiento interanual de las ganancias por acción."),
        ("EV/EBITDA", "enterpriseToEbitda", num, "Valor de la empresa (incluye deuda) sobre EBITDA. Útil para comparar empresas con distinta estructura de capital."),
        ("Price/Sales", "priceToSalesTrailing12Months", num, "Precio sobre ventas. Sirve cuando las ganancias son negativas o muy volátiles."),
        ("FCF Yield", "fcfYield", pct, "Flujo de caja libre sobre market cap. Cuánto efectivo genera el negocio por cada dólar que vale."),
        ("Beta", "beta", num, "Volatilidad respecto al mercado."),
    ],
    "Rentabilidad y Márgenes": [
        ("ROE", "returnOnEquity", pct, "Retorno sobre el patrimonio neto."),
        ("ROA", "returnOnAssets", pct, "Retorno sobre los activos."),
        ("Gross Margin", "grossMargins", pct, "Margen bruto."),
        ("Operating Margin", "operatingMargins", pct, "Margen operativo: lo que queda de cada dólar de ventas antes de intereses e impuestos."),
        ("Profit Margin", "profitMargins", pct, "Margen neto."),
        ("Revenue Growth", "revenueGrowth", pct, "Crecimiento interanual de las ventas."),
    ],
    "Salud y Dividendos": [
        ("Price to Book", "priceToBook", num, "Precio frente al valor contable."),
        ("Debt to Equity", "debtToEquity", num, "Endeudamiento sobre el patrimonio."),
        ("Net Debt/EBITDA", "netDebtToEbitda", num, "Años de EBITDA necesarios para pagar la deuda neta. Negativo = más caja que deuda."),
        ("Current Ratio", "currentRatio", num, "Cobertura de deuda corriente con activos corrientes."),
        ("Quick Ratio", "quickRatio", num, "Prueba ácida: liquidez sin inventarios."),
        ("Dividend Yield", "divYield", pct, "Dividendo anual sobre el precio."),
    ],
}

TECH_OPTIONS = ["Bandas de Bollinger", "Volumen", "RSI (14)", "MACD"]
PANEL_HEIGHT = {"price": 0.55, "Volumen": 0.15, "RSI (14)": 0.2, "MACD": 0.2}
YEARS = {"1y": 1, "2y": 2, "5y": 5, "max": None}

page_header("Análisis por ticker", "Fundamentales, técnico y estados financieros de cualquier acción.")

ticker = st.text_input("Ticker", value="ORCL", placeholder="ORCL, VIST, MSFT, NVDA…").upper().strip()
if not ticker:
    st.stop()

try:
    info = add_derived(get_info(ticker))
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

# --- Ratios (filas de 4)
st.subheader("Ratios clave")
for tab, (name, items) in zip(st.tabs(list(RATIOS)), RATIOS.items()):
    with tab:
        for i in range(0, len(items), 4):
            for col, (label, key, fmt, help_) in zip(st.columns(4), items[i:i + 4]):
                col.metric(label, fmt(info.get(key)), help=help_)

# --- Técnico
st.subheader("Análisis técnico")
ca, cb = st.columns([1, 3])
period = ca.selectbox("Período", list(YEARS), index=0)
shown = cb.multiselect("Indicadores", TECH_OPTIONS, default=["Volumen", "RSI (14)"])

try:
    full = get_history(ticker, "max")
except Exception:
    full = pd.DataFrame()
if full.empty:
    st.info("No hay historial de precios para este activo (puede ser un límite temporal de Yahoo). Probá de nuevo en unos minutos.")
    st.stop()

# Los indicadores se calculan sobre todo el historial y después se recorta la ventana,
# así la SMA 200 y el RSI ya están "calentados" desde el primer día visible.
full = full.copy()
close = full["Close"]
full["SMA50"] = close.rolling(50).mean()
full["SMA200"] = close.rolling(200).mean()
full["BB_low"], _, full["BB_up"] = bollinger(close)
full["RSI"] = rsi(close)
full["MACD"], full["MACD_sig"], full["MACD_hist"] = macd(close)

years = YEARS[period]
df = full if years is None else full[full.index >= full.index.max() - pd.DateOffset(years=years)]

panels = ["price"] + [p for p in ("Volumen", "RSI (14)", "MACD") if p in shown]
heights = [PANEL_HEIGHT[p] for p in panels]
fig = make_subplots(rows=len(panels), cols=1, shared_xaxes=True, vertical_spacing=0.03,
                    row_heights=[h / sum(heights) for h in heights])
row = {p: i + 1 for i, p in enumerate(panels)}

fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
    name="Precio", increasing_line_color=COLORS["up"], decreasing_line_color=COLORS["down"],
), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50", line=dict(color=COLORS["accent"], width=1.6)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="SMA 200", line=dict(color=COLORS["blue"], width=1.6)), row=1, col=1)

if "Bandas de Bollinger" in shown:
    band = dict(color="rgba(120,140,93,0.6)", width=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_up"], name="Bollinger", line=band), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_low"], name="Bollinger inf.", line=band, showlegend=False,
                             fill="tonexty", fillcolor="rgba(120,140,93,0.08)"), row=1, col=1)

if "Volumen" in row:
    colors = [COLORS["up"] if c >= o else COLORS["down"] for o, c in zip(df["Open"], df["Close"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volumen", marker_color=colors, opacity=0.7, showlegend=False),
                  row=row["Volumen"], col=1)
    fig.update_yaxes(title_text="Volumen", row=row["Volumen"], col=1)

if "RSI (14)" in row:
    r = row["RSI (14)"]
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color=COLORS["accent"], width=1.6), showlegend=False), row=r, col=1)
    for level in (30, 70):
        fig.add_hline(y=level, line_dash="dot", line_color=COLORS["muted"], row=r, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=r, col=1)

if "MACD" in row:
    r = row["MACD"]
    hist_colors = [COLORS["up"] if v >= 0 else COLORS["down"] for v in df["MACD_hist"].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="Histograma", marker_color=hist_colors, opacity=0.6, showlegend=False), row=r, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color=COLORS["blue"], width=1.5), showlegend=False), row=r, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_sig"], name="Señal", line=dict(color=COLORS["accent"], width=1.5), showlegend=False), row=r, col=1)
    fig.update_yaxes(title_text="MACD", row=r, col=1)

style_fig(fig, 480 + 170 * (len(panels) - 1))
fig.update_xaxes(rangeslider_visible=False, rangebreaks=[dict(bounds=["sat", "mon"])])
st.plotly_chart(fig, use_container_width=True)
st.caption("RSI > 70 sugiere sobrecompra y < 30 sobreventa. MACD cruzando su señal hacia arriba marca momentum alcista. "
           "Son indicadores rezagados: dan contexto, no señales de compra por sí solos.")

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
