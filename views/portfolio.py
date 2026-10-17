import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.data import get_prices
from core.style import COLORS, PALETTE, page_header, style_fig

page_header("Portfolio", "Cargá tus posiciones, seguí la cartera y mirá cómo se correlacionan.")

COLS = ["Ticker", "Cantidad", "Costo promedio (USD)"]
if "portfolio" not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(
        {"Ticker": ["AAPL", "MSFT", "NVDA"], "Cantidad": [10.0, 5.0, 8.0], "Costo promedio (USD)": [150.0, 300.0, 400.0]}
    )

# --- Carga de posiciones
st.subheader("Mis posiciones")
up = st.file_uploader("Importar CSV (Ticker, Cantidad, Costo promedio (USD))", type="csv", label_visibility="collapsed")
if up is not None and st.session_state.get("_last_upload") != up.name:
    st.session_state.portfolio = pd.read_csv(up)[COLS]
    st.session_state["_last_upload"] = up.name

edited = st.data_editor(
    st.session_state.portfolio, num_rows="dynamic", use_container_width=True,
    column_config={
        "Ticker": st.column_config.TextColumn(required=True),
        "Cantidad": st.column_config.NumberColumn(min_value=0.0, format="%.4f"),
        "Costo promedio (USD)": st.column_config.NumberColumn(min_value=0.0, format="$%.2f"),
    },
)
st.session_state.portfolio = edited
st.download_button("Descargar CSV (para guardar tu cartera)", edited.to_csv(index=False), "portfolio.csv", "text/csv")

pf = edited.dropna(subset=["Ticker", "Cantidad"]).copy()
pf["Ticker"] = pf["Ticker"].astype(str).str.upper().str.strip()
pf = pf[(pf["Ticker"] != "") & (pf["Cantidad"] > 0)].groupby("Ticker", as_index=False).agg(
    {"Cantidad": "sum", "Costo promedio (USD)": "mean"}
)
if pf.empty:
    st.info("Agregá al menos una posición para empezar.")
    st.stop()

# --- Precios
period = st.selectbox("Ventana para retornos y correlación", ["6mo", "1y", "2y", "5y"], index=1)
with st.spinner("Bajando precios…"):
    try:
        prices = get_prices(tuple(pf["Ticker"]), period)
    except Exception:
        st.error("No se pudieron bajar los precios (probablemente límite de Yahoo). Probá en unos minutos.")
        st.stop()

prices = prices.ffill()
missing = [t for t in pf["Ticker"] if t not in prices.columns or prices[t].dropna().empty]
if missing:
    st.warning(f"Sin datos para: {', '.join(missing)}. Se excluyen del análisis.")
pf = pf[~pf["Ticker"].isin(missing)].reset_index(drop=True)
if pf.empty:
    st.stop()
prices = prices[list(pf["Ticker"])]

last = prices.iloc[-1]
pf["Precio"] = pf["Ticker"].map(last)
pf["Valor"] = pf["Cantidad"] * pf["Precio"]
pf["Invertido"] = pf["Cantidad"] * pf["Costo promedio (USD)"]
pf["P&L (USD)"] = pf["Valor"] - pf["Invertido"]
pf["P&L (%)"] = np.where(pf["Invertido"] > 0, pf["P&L (USD)"] / pf["Invertido"] * 100, np.nan)
pf["Peso (%)"] = pf["Valor"] / pf["Valor"].sum() * 100

total_val, total_inv = pf["Valor"].sum(), pf["Invertido"].sum()
pnl = total_val - total_inv
returns = prices.pct_change().dropna(how="all")
w = (pf["Valor"] / total_val).values
cov = returns.cov().values * 252
vol = float(np.sqrt(w @ cov @ w)) if not np.isnan(cov).any() else np.nan

st.markdown("---")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Valor total", f"${total_val:,.0f}")
k2.metric("Invertido", f"${total_inv:,.0f}")
k3.metric("P&L", f"${pnl:,.0f}", f"{pnl / total_inv * 100:.2f}%" if total_inv else None)
k4.metric("Volatilidad anual", f"{vol * 100:.1f}%" if not np.isnan(vol) else "N/D",
          help="Calculada con la matriz de covarianza de los retornos diarios y los pesos actuales.")

tab_pos, tab_corr, tab_perf = st.tabs(["Posiciones", "Correlación", "Rendimiento"])

with tab_pos:
    left, right = st.columns([3, 2])
    left.dataframe(
        pf[["Ticker", "Cantidad", "Precio", "Valor", "P&L (USD)", "P&L (%)", "Peso (%)"]],
        use_container_width=True, hide_index=True,
        column_config={
            "Precio": st.column_config.NumberColumn(format="$%.2f"),
            "Valor": st.column_config.NumberColumn(format="$%.2f"),
            "P&L (USD)": st.column_config.NumberColumn(format="$%.2f"),
            "P&L (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Peso (%)": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )
    donut = go.Figure(go.Pie(labels=pf["Ticker"], values=pf["Valor"], hole=0.6,
                             marker=dict(colors=PALETTE, line=dict(color=COLORS["bg"], width=2)), textinfo="label+percent"))
    style_fig(donut, 320).update_layout(showlegend=False)
    right.plotly_chart(donut, use_container_width=True)

with tab_corr:
    if len(pf) < 2:
        st.info("Necesitás al menos 2 posiciones para calcular correlación.")
    else:
        corr = returns.corr()
        heat = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1,
            colorscale=[[0, COLORS["blue"]], [0.5, "#F0EEE6"], [1, COLORS["accent"]]],
            text=np.round(corr.values, 2), texttemplate="%{text}", colorbar=dict(thickness=12),
        ))
        style_fig(heat, 480).update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(heat, use_container_width=True)
        pairs = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack().sort_values(ascending=False)
        c1, c2 = st.columns(2)
        c1.metric("Par más correlacionado", " / ".join(pairs.index[0]), f"{pairs.iloc[0]:.2f}", delta_color="off")
        c2.metric("Par menos correlacionado", " / ".join(pairs.index[-1]), f"{pairs.iloc[-1]:.2f}", delta_color="off")
        st.caption("Correlación de retornos diarios. Cerca de 1 = se mueven juntas (poca diversificación); cerca de 0 o negativa = diversifican.")

with tab_perf:
    base100 = prices / prices.bfill().iloc[0] * 100
    port = (prices * pf.set_index("Ticker")["Cantidad"]).sum(axis=1)
    fig = go.Figure()
    for i, t in enumerate(base100.columns):
        fig.add_trace(go.Scatter(x=base100.index, y=base100[t], name=t,
                                 line=dict(width=1.2, color=PALETTE[i % len(PALETTE)]), opacity=0.6))
    fig.add_trace(go.Scatter(x=port.index, y=port / port.iloc[0] * 100, name="Portfolio",
                             line=dict(width=3, color=COLORS["text"])))
    style_fig(fig, 460).update_yaxes(title="Base 100")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("El portfolio se simula con las cantidades actuales sobre toda la ventana (no refleja cuándo compraste cada posición).")
