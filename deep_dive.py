import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Deep Dive de Activo", layout="wide")
st.title("📊 Financial Deep Dive por Ticker")

ticker_input = st.text_input("Ingresá el Ticker (ej. ORCL, VIST, MSFT, TSLA, NVDA):", value="ORCL").upper().strip()

if ticker_input:
    asset = yf.Ticker(ticker_input)
    info = asset.info

    # 1. Resumen Ejecutivo
    st.header(f"{info.get('longName', ticker_input)} ({ticker_input})")
    col1, col2, col3, col4 = st.columns(4)
    
    current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    col1.metric("Precio Actual", f"${current_price:,.2f}")
    col2.metric("Market Cap", f"${info.get('marketCap', 0):,}")
    col3.metric("Sector", info.get("sector", "N/D"))
    col4.metric("Industria", info.get("industry", "N/D"))

    st.markdown("---")

    # 2. Ratios Financieros
    st.subheader("📌 Ratios Clave de Valuación y Eficiencia")
    
    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
    r_col1.metric("Trailing P/E", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/D")
    r_col1.metric("Forward P/E", f"{info.get('forwardPE', 0):.2f}" if info.get('forwardPE') else "N/D")
    
    r_col2.metric("PEG Ratio", f"{info.get('pegRatio', 0):.2f}" if info.get('pegRatio') else "N/D")
    r_col2.metric("Price to Book (P/B)", f"{info.get('priceToBook', 0):.2f}" if info.get('priceToBook') else "N/D")
    
    r_col3.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.2f}%" if info.get('returnOnEquity') else "N/D")
    r_col3.metric("ROA", f"{info.get('returnOnAsset', 0)*100:.2f}%" if info.get('returnOnAsset') else "N/D")
    
    r_col4.metric("Profit Margin", f"{info.get('profitMargins', 0)*100:.2f}%" if info.get('profitMargins') else "N/D")
    r_col4.metric("Debt to Equity", f"{info.get('debtToEquity', 0):.2f}" if info.get('debtToEquity') else "N/D")

    st.markdown("---")

    # 3. Gráfico Técnico Histórico
    st.subheader("📈 Evolución Histórica y Medias Móviles")
    
    period = st.selectbox("Seleccionar período del gráfico:", ["1y", "2y", "5y", "max"], index=0)
    df_hist = asset.history(period=period)

    if not df_hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df_hist.index,
            open=df_hist['Open'], high=df_hist['High'],
            low=df_hist['Low'], close=df_hist['Close'],
            name='Precio'
        ))
        
        df_hist['SMA50'] = df_hist['Close'].rolling(50).mean()
        df_hist['SMA200'] = df_hist['Close'].rolling(200).mean()
        
        fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['SMA50'], line=dict(color='orange', width=1.5), name='SMA 50'))
        fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['SMA200'], line=dict(color='deepskyblue', width=1.5), name='SMA 200'))

        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)

    # 4. Estados Financieros
    with st.expander("📄 Ver Estados Financieros Completos"):
        tab1, tab2 = st.tabs(["Income Statement", "Balance Sheet"])
        with tab1:
            st.dataframe(asset.financials)
        with tab2:
            st.dataframe(asset.balance_sheet)
