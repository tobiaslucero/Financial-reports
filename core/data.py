import time

import pandas as pd
import streamlit as st
import yfinance as yf


class DataUnavailable(Exception):
    """Yahoo devolvió una respuesta vacía (suele ser un límite de peticiones)."""


# Importante: Streamlit NO cachea las funciones que lanzan una excepción. Por eso las
# respuestas vacías se convierten en error: así un fallo temporal no queda guardado 1 hora.

@st.cache_data(ttl=3600, show_spinner=False)
def get_info(symbol: str) -> dict:
    last_err = DataUnavailable(f"Respuesta vacía para {symbol}")
    for attempt in range(3):
        try:
            info = yf.Ticker(symbol).info
            if info and (info.get("longName") or info.get("shortName")
                         or info.get("currentPrice") or info.get("regularMarketPrice")):
                return info
        except Exception as e:  # límite de peticiones, red, etc.
            last_err = e
        if attempt < 2:
            time.sleep(1.5 * (attempt + 1))
    raise last_err


@st.cache_data(ttl=3600, show_spinner=False)
def get_history(symbol: str, period: str) -> pd.DataFrame:
    df = yf.Ticker(symbol).history(period=period)
    if df.empty:
        raise DataUnavailable(f"Sin historial para {symbol}")
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def get_statements(symbol: str):
    t = yf.Ticker(symbol)
    return t.financials, t.balance_sheet


@st.cache_data(ttl=3600, show_spinner=False)
def get_eps(symbol: str):
    """EPS trimestral: earnings_dates primero, quarterly_financials como fallback."""
    t = yf.Ticker(symbol)
    try:
        e = t.earnings_dates
        if e is not None and not e.empty and "Reported EPS" in e.columns:
            df = e.dropna(subset=["Reported EPS"])
            df = df[df["Reported EPS"] != 0][["Reported EPS"]].rename(columns={"Reported EPS": "EPS"})
            if getattr(df.index, "tz", None) is not None:
                df.index = df.index.tz_localize(None)
            if not df.empty:
                return df.sort_index()
    except Exception:
        pass
    try:
        q = t.quarterly_financials
        row = next((r for r in ("Diluted EPS", "Basic EPS") if r in q.index), None)
        if row:
            df = q.loc[row].dropna().to_frame(name="EPS")
            df.index = pd.to_datetime(df.index)
            return df.sort_index()
    except Exception:
        pass
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def get_prices(tickers: tuple, period: str = "1y") -> pd.DataFrame:
    """Precios de cierre ajustados, una columna por ticker."""
    df = yf.download(list(tickers), period=period, auto_adjust=True, progress=False)["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame(tickers[0])
    df = df.dropna(how="all")
    if df.empty:
        raise DataUnavailable("Sin precios")
    return df
