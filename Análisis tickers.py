import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Deep Analysis Activos", layout="wide")
st.title("📊 Financial Analysis por Ticker")

ticker_input = st.text_input("Ingresá el Ticker (ej. ORCL, VIST, MSFT, TSLA, NVDA):", value="ORCL").upper().strip()

# Cacheamos solo el diccionario de info, no el objeto Ticker entero
@st.cache_data(ttl=3600)
def get_info_data(symbol):
    return yf.Ticker(symbol).info

if ticker_input:
    try:
        info = get_info_data(ticker_input)
        asset = yf.Ticker(ticker_input) # Se instancia afuera de la caché para consultar el history()
        
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

        # 3.b Gráfico Fundamental: Precio vs EPS Trimestral
        st.subheader("📊 Evolución de Precio vs EPS Trimestral")
        
        try:
            q_fin = asset.quarterly_financials
            if not q_fin.empty and ('Diluted EPS' in q_fin.index or 'Basic EPS' in q_fin.index):
                # Extraemos el EPS trimestral
                eps_row = 'Diluted EPS' if 'Diluted EPS' in q_fin.index else 'Basic EPS'
                df_eps = q_fin.loc[eps_row].dropna().to_frame(name='EPS')
                df_eps.index = pd.to_datetime(df_eps.index)
                df_eps = df_eps.sort_index()

                # Creamos el gráfico con doble eje Y
                fig_fund = go.Figure()

                # Barras azules de EPS (Eje Y1)
                fig_fund.add_trace(go.Bar(
                    x=df_eps.index,
                    y=df_eps['EPS'],
                    name='Diluted EPS',
                    marker_color='#2962FF',
                    yaxis='y1'
                ))

                # Línea de Precio (Eje Y2)
                fig_fund.add_trace(go.Scatter(
                    x=df_hist.index,
                    y=df_hist['Close'],
                    name='Precio (USD)',
                    line=dict(color='#FF6D00', width=2),
                    yaxis='y2'
                ))

                # Configuración de ejes dobles y estilo
                fig_fund.update_layout(
                    template="plotly_dark",
                    height=450,
                    xaxis=dict(title="Fecha"),
                    yaxis=dict(title="EPS ($)", showgrid=False),
                    yaxis2=dict(title="Precio (USD)", overlaying='y', side='right', showgrid=False),
                    legend=dict(x=0.01, y=0.99)
                )

                st.plotly_chart(fig_fund, use_container_width=True)
            else:
                st.info("No hay datos suficientes de EPS trimestral para este activo.")
        except Exception:
            pass  # Si falla el scraping fundamental, simplemente no dibuja nada para evitar romper la vista

        # 4. Estados Financieros
        with st.expander("📄 Ver Estados Financieros Completos"):
            tab1, tab2 = st.tabs(["Income Statement", "Balance Sheet"])
            with tab1:
                st.dataframe(asset.financials)
            with tab2:
                st.dataframe(asset.balance_sheet)

    except Exception as e:
        st.error("Yahoo Finance limitó las peticiones desde el servidor en la nube. Intentá nuevamente en unos minutos o refrescá la página.")
